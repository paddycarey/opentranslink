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
from .routes import fetch_routes
from .utils import make_get_request

# public objects (well, as public as it gets in pythonland)
__all__ = ['parse_timetable_page', 'get_timetable', 'get_timetable_by_url']


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


def get_timetable_by_url(url):
    """
    Convenience function to return a timetable for a single route given a url
    """

    timetable = parse_timetable_page(make_get_request(url))
    return timetable
