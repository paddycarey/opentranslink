#!/usr/bin/env python
"""
Python script that fetches Translink NI timetable data and processes it into
something that can be easily worked with in python. Could be used as the basis
for building a simple timetable API.

Thanks to @Tyndyll for https://github.com/tyndyll/translink-extraction which
was the inspiration for this script and a bug help for parts

Copyright (c) 2013 Patrick Carey

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
"""
# stdlib imports
import collections
import copy

# third-party imports
import requests
from bs4 import BeautifulSoup


# utility classes/functions

class OrderedDefaultdict(collections.OrderedDict):
    """
    Simple implementation of an ordered, defaultdict
    """

    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(self.__class__, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default


def fetch_page(url):
    """
    Fetch the given url, returning its contents as a string
    """
    return requests.get(url).text


# translink functions


def parse_routes(route_soup):
    """
    Parse routes from a given timetable page
    """

    routes = OrderedDefaultdict(dict)

    # check if this is the last page of results
    try:
        page_nums = route_soup.find('div', attrs={'class': 'rgWrap rgNumPart'}).find_all('a')
    except AttributeError:
        last_page = True
    else:
        last_page = [x.get('class') for x in page_nums][-1] is not None

    # build dict containg details of routes on page
    # table = route_soup.find(id='ctl00_MainRegion_rptPageList_ctl00')
    table = route_soup.find_all('a', attrs={'class': 'timetable-ico'})[1].parent.parent.parent.parent
    for row in table.find('tbody').find_all('tr'):
        # get columns, discarding any that are empty
        columns = [x for x in row.find_all('td') if x.get_text().strip()]
        # skip empty or malformed rows
        if not columns or len(columns) < 3:
            continue
        # parse route and add to dict
        routes[columns[0].get_text().strip()][columns[2].get_text().strip().lower()] = {
            'name': columns[1].get_text().strip(),
            'url': "http://www.translink.co.uk" + columns[1].a['href'],
        }
    return routes, last_page


def fetch_routes(service):
    """
    Given a service name, fetch a list of routes, their names, ids and urls
    from which we can parse the timetable data we need
    """

    # dict containing base urls for each of the services we need
    base_urls = {
        "metro": "http://www.translink.co.uk/Services/Metro-Service-Page/",
        "ulsterbus": "http://www.translink.co.uk/Services/Ulsterbus-Service-Page/Routes--Timetables/All-Timetables1/",
        "goldline": "http://www.translink.co.uk/Services/Goldline/Routes--Timetables/All-Timetables/",
        "rail": "http://www.translink.co.uk/Services/NI-Railways/",
        "enterprise": "http://www.translink.co.uk/Services/Enterprise/"
    }

    base_url = base_urls[service]
    # fetch the first page of results, pagination's done with POST requests so
    # we'll do any subsequent pages in a loop after parsing
    soup = BeautifulSoup(fetch_page(base_url))
    routes, last_page = parse_routes(soup)

    def get_next_page(page_soup):
        """
        Scrape the page to get the formdata we need to POST to retrieve the
        next set of results
        """

        form_data = {}
        submit_buttons = {}

        # find the form in the fetched page
        form = page_soup.find(id='aspnetForm')
        # get all inputs from the form
        for input_field in form.find_all('input'):
            # store any submit buttons in a seperate array so we can use only
            # the one we need
            if input_field['type'] == 'submit':
                try:
                    submit_buttons[input_field['class'][0]] = input_field
                except KeyError:
                    pass
                continue
            # store the value of the input field in our dict
            try:
                form_data[input_field['name']] = input_field['value']
            except KeyError:
                pass
        # add the correct submit button to the formdata and return
        form_data[submit_buttons['rgPageNext']['name']] = ''
        return form_data

    # loop until we hit the last page, adding all possible routes
    while not last_page:
        soup = BeautifulSoup(requests.post(base_url, data=get_next_page(soup)).text)
        new_routes, last_page = parse_routes(soup)
        routes.update(new_routes)

    return routes


def parse_timetable_fragment(table):
    """
    Parses a <table> fragment of a timetable page, returning a list of dicts
    """

    # template for a journey parsed from the table
    journey_template = {
        'days_of_operation': None,
        'service': None,
        'operator': None,
        'stops': [],
    }

    # get number of journeys in this table fragment
    journey_count = len(table.find('tr').find_all("th"))
    journeys = [copy.deepcopy(journey_template) for j in xrange(journey_count)]

    # loop over all table rows and extract timetable data
    for row in table.find_all("tr")[1:]:

        # parse name of the stop from the table, skipping the row if we're not
        # able to parse it
        try:
            stop_name = row.find("th").get_text()
        except AttributeError:
            continue

        for idx, column in enumerate(row.find_all("td")):

            # parse text from column
            text = column.get_text().lstrip().rstrip()

            # populate journey dict as required
            if stop_name == 'Operator:':
                journeys[idx]['operator'] = text
            elif stop_name == 'Service:':
                journeys[idx]['service'] = text
            elif stop_name == 'Days of operation:':
                journeys[idx]['days_of_operation'] = text
            elif stop_name == 'Bank Holidays:':
                journeys[idx]['bank_holidays'] = text
            elif stop_name == 'Calling points:':
                continue
            else:
                journeys[idx]['stops'].append({
                    'stop_name': stop_name,
                    'time': text,
                })

    # return the list of parsed journeys
    return journeys


def parse_timetable_page(timetable_data):
    """
    Parse timetable data fetched from a valid timetable URL using BeautifulSoup
    """

    # parse url content as soup object
    soup = BeautifulSoup(timetable_data)
    # find the timetable
    for table in soup.find(id="timetableContainer").find_all('table'):
        for journey in parse_timetable_fragment(table):
            yield journey


def get_timetable(service, route_number, direction):
    """
    Convenience function to return a timetable for a single route
    """

    routes = fetch_routes(service)
    route = routes[route_number]
    timetable = parse_timetable_page(fetch_page(route[direction.lower()]['url']))
    return timetable

if __name__ == '__main__':

    help_text = """Translink Extractor 0.0.1

    Usage:
      translink.py --routes <service>
      translink.py <service> <route_number> <direction>
      translink.py (-h | --help)
      translink.py --version

    Options:
      -h --help     Show this screen.
      --version     Show version.

    """
    # stdlib imports
    import json
    # third-party imports
    from docopt import docopt

    # parse the command line args with docopt
    arguments = docopt(help_text, version='Translink Extractor 0.0.1')

    if arguments['--routes']:
        routes = fetch_routes(arguments['<service>'])
        for key, value in routes.items():
            print key
            for inner_key, inner_value in value.items():
                print '  ' + inner_key.capitalize() + ': ' + inner_value['name']
                print '    ' + inner_value['url']
            print
    else:
        # get command line arguments
        service = arguments['<service>']
        route_number = arguments['<route_number>']
        direction = arguments['<direction>']
        # get timetable data
        timetable = get_timetable(service, route_number, direction)
        # timetable is a generator, so listify it and dump to json for pretty printing
        print json.dumps(list(timetable), indent=2)
