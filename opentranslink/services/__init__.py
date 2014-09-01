# marty mcfly imports
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# stdlib imports
import urllib
try:
    # python 3+
    from urllib.parse import parse_qsl
    from urllib.parse import urlparse
except ImportError:
    # python 2+
    from urlparse import parse_qsl
    from urlparse import urlparse

# local imports
from ..routes import Route
from ..utils import make_request

from . import nir

class InvalidServiceError(Exception):
    pass

class ServiceRegistry(object):
    def __init__(self):
        self._service_name_to_provider_map = {}
        self._uri_prefix_to_provider_map = {}

    def register(self, service_name, service_info_provider):
        assert service_name not in self._service_name_to_class_map

        self._service_name_to_provider_map[service_name] = service_info_provider
        self._uri_prefix_to_provider_map[uri_prefix] = service_info_provider

    def deregister(self, service_name):
        assert service_name in self._service_name_to_class_map
        del self._service_name_to_provider_map[service_name]
        del self._uri_prefix_to_provider_map[service_name]

    def all_services_for_uri_prefix(self, uri_prefix):
        raise NotImplementedError()

    def preferred_service_for_uri_prefix(self, uri_prefix):
        return all_services_for_uri_prefix(self, uri_prefix)[0]

class TransportServiceInfoProvider(object):
    def __init__(self, service_name, loc_uri_provided):
        """
        Creates a new TransportService object, with the given service_name.
        For each loc_uri in loc_uris_provided dictionary's keys, the
        value is considered the score (relative to 0) at which this
        ServiceInfoProvider should be scored.
        """

        if service_name not in self.valid_services:
            raise InvalidServiceError('{0} is not a valid service name.'.format(service_name))
        self.service_name = service_name
        self.loc_uris_provided = loc_uris_provided
 
class TransportServiceTimetableProvider(TransportServiceInfoProvider):
   def route(self, code):
        """
        Returns the route that matches the given service code or None if not found
        """
        raise NotImplementedError()

    def routes(self):
        """
        Return a list of routes supported by this service.
        """
        raise NotImplementedError()

class TransportLiveInfoService(TransportServiceInfoProvider):
    def next_journeys_between(self, src_loc_uri, dst_loc_uri):
        """
        Returns a list of upcoming journeys which serve the given dst_loc_uri,
        from the given src_loc_uri.  Status information, such as depature times
        and delays, is included.
        """
        raise NotImplementedError()

class TranslinkServiceOfficialTimeTableProvider(TransportServiceTimetableProvider):
    base_url = 'http://www.translink.co.uk/Routes-and-Timetables/{0}/'
    valid_services = ['metro', 'ulsterbus', 'goldline', 'nir', 'enterprise']

    def __init__(self, *args, subservice, **kwargs):
        super(TranslinkServiceOfficialTimeTableProvider, self).__init__(*args, **kwargs)

        assert subservice in self.__class__.valid_services

        self.subservice = subservice
        self.service_url = self.base_url.format(subservice)
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
        form_data['__EVENTTARGET'] = ''
        form_data['__EVENTARGUMENT'] = ''
        form_data['ctl00$MainRegion$rptPageListCurrent$ctl00$ctl03$ctl01$ctl12'] = ''
        return form_data

def register_services(service_registry):
    # register main timetable services by creating them in a loop based on service names
    for subservice in TranslinkServiceOfficialTimeTableProvider.valid_services:
        tt_service_info_provider = TranslinkServiceOfficialTimeTableProvider("official_translink_" + subservice + "_timetable_provider", subservice)
        service_registry.register("translink-northern-ireland:/" + subservice, tt_service_info_provider)

    # register nir next trains service directly
    nir_live_info_provider = NotImplementedError()
    raise nir_live_info_provider
    service_registry.register("translink-northern-ireland:/nir", nir_live_info_provider)

