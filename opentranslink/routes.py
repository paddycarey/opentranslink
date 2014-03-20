# marty mcfly imports
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# third-party imports
import tablib

# local imports
from .utils import make_request


class Timetable(object):

    def __init__(self, url):
        self.url = url
        self.soup = make_request('get', self.url)
        self._times = None

    def _parse_timetable(self):

        times = []

        weekday_tds = self.soup.find_all('td', attrs={'class': 'weekdayTable'})
        header_tables = self.soup.find_all('table', attrs={'class': 'ttbM'})
        body_tables = self.soup.find_all('table', attrs={'class': 'ttbCo'})

        for weekday_td, header_table, body_table in zip(weekday_tds, header_tables, body_tables):
            weekday = weekday_td.text
            dataset = tablib.Dataset()
            columns = [[x.text for x in col.find_all('td')] for col in body_table.find_all('tr')[0:-1]]
            for column in columns:
                dataset.append_col(column)
            dataset.headers = [x.text.strip() for x in header_table.find_all('tr')[0:-1]]
            times.append((weekday, dataset))
        return times

    @property
    def times(self):
        if self._times is not None:
            return self._times
        self._times = self._parse_timetable()
        return self._times


class Route(object):

    def __init__(self, code, name, url):
        self.code = code
        self.name = name
        self.url = url
        self._timetable = None

    @property
    def timetable(self):
        if self._timetable is not None:
            return self._timetable.times
        self._timetable = Timetable(self.url)
        return self._timetable.times

    def __repr__(self):
        return '<opentranslink.Route-{0}>'.format(self.code)
