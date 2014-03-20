# marty mcfly imports
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# stdlib imports
import urllib
from urlparse import parse_qsl
from urlparse import urlparse

# local imports
from .routes import Route
from .utils import make_request


class InvalidServiceError(Exception):
    pass


class Service(object):

    base_url = 'http://www.translink.co.uk/Routes-and-Timetables/{0}/'
    valid_services = ['metro', 'ulsterbus', 'goldline', 'nir', 'enterprise']

    def __init__(self, service_name):
        if service_name not in self.valid_services:
            raise InvalidServiceError('{0} is not a valid service name.'.format(service_name))
        self.service_name = service_name
        self.service_url = self.base_url.format(service_name)
        self._routes = None

    def route(self, code):
        """returns the route that matches the given code or None if not found
        """
        for route in self.routes():
            if route.code.lower() == code.lower():
                return route
        return None

    def routes(self):
        """
        Given a service URL, fetch it's contents and scrape any routes we can find,
        paging through the route lists if necessary
        """

        if self._routes is not None:
            return self._routes

        # fetch the first page of results, pagination's done with POST requests so
        # we'll do any subsequent pages in a loop after parsing
        soup = make_request('get', self.service_url)

        # if this is a train service the call a different parser (for some reason
        # the page has a different layout)
        if self.service_name in ['nir', 'enterprise']:
            self._routes = self._parse_train_routes_page(soup)
            return self._routes

        # loop until we hit the last page, adding all possible routes
        routes, last_page = self._parse_routes_page(soup)
        while not last_page:
            soup = make_request('post', self.service_url, data=self._parse_next_page_data(soup))
            new_routes, last_page = self._parse_routes_page(soup)
            routes.extend(new_routes)

        self._routes = routes
        return routes

    def _fix_url_format(self, url):
        """
        Simple method to create a query string changing only
        one parameter in the request
        """

        # we can't modify the request params in place so
        # we need to make a copy of the dict
        qs = urlparse(url).query
        temp = dict(parse_qsl(qs))
        temp['outputFormat'] = 0

        # return encoded query string
        return url.replace(qs, urllib.urlencode(temp))

    def _parse_routes_page(self, soup):
        """
        Parse routes from a given service page
        """

        routes = []

        # check if this is the last page of results
        try:
            page_nums = soup.find('div', attrs={'class': 'rgWrap rgNumPart'}).find_all('a')
        except AttributeError:
            last_page = True
        else:
            last_page = [x.get('class') for x in page_nums][-1] is not None

        # build dict containg details of routes on page
        # table = route_soup.find(id='ctl00_MainRegion_rptPageList_ctl00')
        table = soup.find('table', attrs={'class': 'rgMasterTable'})
        for row in table.find('tbody').find_all('tr'):
            # get columns, discarding any that are empty
            columns = row.find_all('td')
            # skip empty or malformed rows
            if not columns or len(columns) < 3:
                continue
            # parse route and add to dict
            code = columns[0].get_text().strip()
            name = columns[1].get_text().strip()
            url = self._fix_url_format(columns[1].a['href'])
            route = Route(code, name, url)
            routes.append(route)
        return routes, last_page

    def _parse_train_routes_page(self, soup):
        """
        Parse routes from a given service page
        """
        raise NotImplementedError('Still can\'t find anything but PDF links for train times :(')

    def _parse_next_page_data(self, soup):
        """
        Scrape a routes list page to get the formdata we need to POST to retrieve
        the next page of results
        """

        form_data = {}
        submit_buttons = {}

        # find the form in the fetched page
        form = soup.find(id='aspnetForm')
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
