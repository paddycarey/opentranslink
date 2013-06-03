#!/usr/bin/env python
"""Translink Extractor 0.0.1

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

# local imports
from translink_extractor import fetch_routes
from translink_extractor import get_timetable


if __name__ == '__main__':

    # parse the command line args with docopt
    arguments = docopt(__doc__, version='Translink Extractor 0.0.1')

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
