from __future__ import print_function

import sys
import os
import shelve
import datetime
import time

import bs4

nir_stations_url = "http://www.journeycheck.com/nirailways/route?from=GVA&to=CLA&action=search&savedRoute="
nir_departures_url_template = "http://www.journeycheck.com/nirailways/route?from=%(src)s&to=%(dst)s&action=search&savedRoute="

MAX_STATION_ID_LEN = 3
MIN_STATION_ID_LEN = 3

MAX_CACHE_TIME = datetime.timedelta(hours=12)


class InvalidStationExcept(KeyError):
    pass

class InvalidStationIdExcept(InvalidStationExcept):
    pass

class InvalidStationNameExcept(InvalidStationExcept):
    pass


def datetime_from_nir_time(nir_time):
    dt = datetime.datetime.strptime(nir_time, "%H:%M")
    return dt

class StationMapper(object):
    def __init__(self):
        self._ids_to_names = {}
        self._names_to_ids = {}

    def add_mapping(self, station_id, station_name):
        assert station_name != "All Stations"

        assert isinstance(station_id, unicode)
        assert isinstance(station_name, unicode)
        assert len(station_id) <= MAX_STATION_ID_LEN # if this happens, you may have given a name instead of an id
        assert len(station_id) >= MIN_STATION_ID_LEN
        assert station_id not in self._ids_to_names
        assert station_name not in self._names_to_ids

        self._ids_to_names[station_id] = station_name
        self._names_to_ids[station_name] = station_id

        assert station_name in self._names_to_ids
        assert station_id in self._ids_to_names

        assert self._ids_to_names[station_id] == station_name
        assert self._names_to_ids[station_name] == station_id

    def remove_mapping(self, station_id, station_name):
        assert len(station_id) <= MAX_STATION_ID_LEN # if this happens, you may have given a name instead of an id
        assert len(station_id) >= MIN_STATION_ID_LEN
        assert station_id in self._ids_to_names
        assert station_name in self._names_to_ids

        del self._ids_to_names[station_id]
        del self._names_to_ids[station_name]

    def name_for_id(self, station_id):
        if len(station_id) > MAX_STATION_ID_LEN or len(station_id) < MIN_STATION_ID_LEN:
            raise InvalidStationId(station_id)

        try:
            return self._ids_to_names[station_id]
        except KeyError as e:
            raise InvalidStationId(station_id)

    def id_for_name(self, station_name):
        assert isinstance(station_name, unicode)

        try:
            return self._names_to_ids[station_name]
        except KeyError, e:
            raise InvalidStationNameExcept(station_name)

    def all_ids(self):
        for station_id in self._ids_to_names.keys():
            yield station_id

    def all_names(self):
        for station_name in self._names_to_ids.keys():
            yield station_name

    def id_is_valid(self, station_id):
        assert isinstance(station_id, unicode)

        if len(station_id) < MIN_STATION_ID_LEN or len(station_id) > MAX_STATION_ID_LEN:
            return False

        return station_id in self._ids_to_names

    def name_is_valid(self, station_name):
        assert isinstance(station_name, unicode)
        return station_name in self._names_to_ids

    def ids_and_names(self):
        for k,v in self._ids_to_names.items():
            yield (k,v)

def build_browser():
    import mechanize
    from functools import partial

    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    br.addheaders = [ ('User-Agent', 'Firefox') ]

    def get_raw_page(br, url):
        br.open(url)
        res = br.response()
        return res.read()

    def cached_get_page(br, url):
        escaped_url = escape_url(url)
        cache_path = os.path.join("/tmp", escaped_url)

        now = datetime.datetime.now()

        page_dat = None
        need_new_page_dat = True

        if os.path.exists(cache_path):
            page_shelf = shelve.open(cache_path)
            cache_date = page_shelf["page_retrieval_date"]

            assert page_shelf["page_url"] == url # TODO: treat this as a runtime error, not an assertion

            if cache_date - now > MAX_CACHE_TIME:
                need_new_page_dat = True
            else:
                page_dat = page_shelf["page_dat"]
                need_new_page_dat = False

        if need_new_page_dat:
            page_dat = get_raw_page(br, url)
            shelf = shelve.open(cache_path)
            shelf["page_url"] = url
            shelf["page_dat"] = page_dat
            shelf["page_retrieval_date"] = now

        return bs4.BeautifulSoup(page_dat)

    br.cached_get_page = partial(cached_get_page, br)

    return br

def escape_url(url):
    import urllib
    return urllib.quote_plus(url)

def unescape_url(url):
    import urllib
    return urllib.unquote_plus(url)


def get_station_mapper():
    """
    Returns a StationMapper, which provides a mapping of all station ids and names
    """

    br = build_browser()
    page = br.cached_get_page(nir_stations_url)
    stationSelect = page.find('select', id='fromSelectBox')

    station_mapper = StationMapper()

    for station in stationSelect.findChildren():
        station_name = unicode(station.contents[0].strip())
        if station_name == "All Stations":
            continue
        station_id = unicode(station.attrs["value"]).strip()
        station_mapper.add_mapping(station_id, station_name)

    return station_mapper

def get_departures_by_station_ids(src_station_id, dst_station_id, station_mapper):
    """
    Yields upcoming departures from the given src_station_name, to the given dst_station_name
    """

    br = build_browser()

    station_departures_url = nir_departures_url_template % { 'src': src_station_id, 'dst': dst_station_id }
    page = br.cached_get_page(station_departures_url)

    departuresList = page.find('div', id='portletDivBodyliveDepartures')
    assert departuresList is not None

    table_rows = departuresList.find('tbody').findAll('tr')

    waypoints = []
    train = None

    for row in table_rows:
        if 'onclick' in row.attrs:
            # new train
            if train != None:
                yield (train, waypoints)

            train = row.findAll('td')

            train_departure_time = train[1].contents[0].strip()
            train_departure_time = datetime_from_nir_time(train_departure_time)

            # TODO: parse this into the actual time, or the adjusted time [don't know if these actually have adjusted times, but the waypoint status does]
            train_departure_status = "".join(train[2].contents).strip()

            train_dst_name = "".join(train[3].contents).strip()
            train_dst_id = station_mapper.id_for_name(train_dst_name)

            train = (src_station_id, train_dst_id, train_departure_time, train_departure_status)

            waypoints = []

        else:
            for subrow in row.findAll('tr', attrs={'class': 'callingPatternRow'}):
                subrow_els = list(subrow.children)

                waypoint_time = subrow_els[1].contents[2]
                waypoint_time = waypoint_time[:len(u" Dep.")]
                waypoint_time = datetime_from_nir_time(waypoint_time)

                # TODO: parse this into the actual time or the adjusted time
                waypoint_status = subrow_els[3].string

                waypoint_station_name = subrow_els[5].contents[0].replace(u"\xa0", u" ").strip()
                waypoint_station_id = station_mapper.id_for_name(waypoint_station_name)

                waypoints.append( (waypoint_time, waypoint_station_id, waypoint_status) )

    if train is not None:
        yield (train, waypoints)

def get_departures_by_station_names(src_station_name, dst_station_name, station_mapper):
    """
    Yields upcoming departures from the given src_station_id, to the given dst_station_id
    """
    assert station_mapper.name_is_valid(src_station_name)
    assert station_mapper.name_is_valid(dst_station_name)

    return get_departures_by_station_names(station_mapper.id_for_name(src_station_id), station_mapper.id_for_name(dst_station_id), station_mapper)


def pretty_print_departure(dep, station_mapper):
    dep_info, waypoint_info = dep

    train_src_id, train_dst_id, train_departure_time, train_departure_status = dep_info

    train_src_name = station_mapper.name_for_id(train_src_id)
    train_dst_name = station_mapper.name_for_id(train_dst_id)

    print("")
    print("#" * 78)
    print("\n")
    print("%s: %s to %s" % (train_departure_time.strftime("%H:%M"), train_src_name, train_dst_name))
    print("=" * 78)
    print("")
    print("    Departure status: %s" % (train_departure_status,))
    print("")

    print("        Time    Station                                    Status")
    print("    " + "-" * 67)
    for wp_time, wp_station_id, wp_status in waypoint_info:
        wp_time_str = wp_time.strftime("%H:%M")
        print("        %-7s %-42s %s" % (wp_time_str, station_mapper.name_for_id(wp_station_id), wp_status))

    print("")

