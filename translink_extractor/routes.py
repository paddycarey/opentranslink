"""
Functions to facilitate scraping and parsing of routes from translink.co.uk
"""
# third-party imports
from bs4 import BeautifulSoup

# local imports
from .utils import OrderedDefaultDict
from .utils import make_get_request
from .utils import make_post_request

# public objects (well, as public as it gets in pythonland)
__all__ = ['fetch_all_routes', 'fetch_routes', 'service_urls']

# dict containing base urls for each of the services we can parse routes from
service_urls = {
    "metro": "http://www.translink.co.uk/Services/Metro-Service-Page/",
    "ulsterbus": "http://www.translink.co.uk/Services/Ulsterbus-Service-Page/Routes--Timetables/All-Timetables1/",
    "goldline": "http://www.translink.co.uk/Services/Goldline/Routes--Timetables/All-Timetables/",
    "rail": "http://www.translink.co.uk/Services/NI-Railways/",
    "enterprise": "http://www.translink.co.uk/Services/Enterprise/"
}


def fetch_all_routes():
    """
    Fetch routes for all available services
    """

    services = {}
    for service in service_urls:
        services[service] = fetch_routes(service)
    return services


def fetch_routes(service):
    """
    Given a service name, fetch a list of routes, their names, ids and urls
    from which we can parse the timetable data we need
    """

    def fetch_metro_base_urls():
        """
        Metro routes are a special case because there's an extra listing page
        which we need to parse to get to the route pages, other services don't
        have this intermediate step
        """

        soup = BeautifulSoup(make_get_request(service_urls['metro']))
        table = soup.find('table', attrs={'summary': 'Metro Routes'})
        for row in table.find_all('tr'):
            try:
                yield "http://www.translink.co.uk" + row.find_all('td')[0].a['href']
            except TypeError:
                pass

    if service == 'metro':
        routes = {}
        for base_url in fetch_metro_base_urls():
            routes.update(fetch_routes_for_base_url(base_url))
        return routes
    else:
        return fetch_routes_for_base_url(service_urls[service])


def fetch_routes_for_base_url(base_url):
    """
    Given a service URL, fetch it's contents and scrape any routes we can find,
    paging through the route lists if necessary
    """

    # fetch the first page of results, pagination's done with POST requests so
    # we'll do any subsequent pages in a loop after parsing
    soup = BeautifulSoup(make_get_request(base_url))
    routes, last_page = parse_routes(soup)

    # loop until we hit the last page, adding all possible routes
    while not last_page:
        soup = BeautifulSoup(make_post_request(base_url, formdata=get_next_page(soup)))
        new_routes, last_page = parse_routes(soup)
        routes.update(new_routes)

    return routes


def get_next_page(page_soup):
    """
    Scrape a routes list page to get the formdata we need to POST to retrieve
    the next page of results
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


def parse_routes(route_soup):
    """
    Parse routes from a given service page
    """

    routes = OrderedDefaultDict(dict)

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
