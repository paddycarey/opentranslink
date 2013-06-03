#!/usr/bin/env python
"""
Python module to handle scraping and parsing of timetable data from
translink.co.uk
"""
# marty mcfly imports
from __future__ import absolute_import

# stdlib imports
import copy

# third-party imports
from bs4 import BeautifulSoup

# local imports
from .utils import OrderedDefaultdict
from .utils import make_get_request
from .utils import make_post_request


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
        "ulsterbus": "http://www.translink.co.uk/Services/Ulsterbus-Service-Page/Routes--Timetables/All-Timetables1/",
        "goldline": "http://www.translink.co.uk/Services/Goldline/Routes--Timetables/All-Timetables/",
        "rail": "http://www.translink.co.uk/Services/NI-Railways/",
        "enterprise": "http://www.translink.co.uk/Services/Enterprise/"
    }

    if service == 'metro':
        routes = {}
        for base_url in fetch_metro_base_urls("http://www.translink.co.uk/Services/Metro-Service-Page/"):
            routes.update(fetch_routes_for_base_url(base_url))
        return routes
    else:
        return fetch_routes_for_base_url(base_urls[service])


def fetch_metro_base_urls(url):

    soup = BeautifulSoup(make_get_request(url))
    table = soup.find('table', attrs={'summary': 'Metro Routes'})
    for row in table.find_all('tr'):
        try:
            yield "http://www.translink.co.uk" + row.find_all('td')[0].a['href']
        except TypeError:
            pass


def fetch_routes_for_base_url(base_url):

    # fetch the first page of results, pagination's done with POST requests so
    # we'll do any subsequent pages in a loop after parsing
    soup = BeautifulSoup(make_get_request(base_url))
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
        soup = BeautifulSoup(make_post_request(base_url, formdata=get_next_page(soup)))
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
    timetable = parse_timetable_page(make_get_request(route[direction.lower()]['url']))
    return timetable
