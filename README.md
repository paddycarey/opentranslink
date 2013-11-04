Translink Extractor 0.0.1
=========================

### Note: Translink's refusal to offer any sort of real API means this project is currently broken due to a site update. Unfortunately I don't have time to fix it currently, but if you're so inclined, please feel free.


Python module to handle scraping and parsing of timetable data from translink.co.uk

Thanks to [@Tyndyll](https://twitter.com/tyndyll) for https://github.com/tyndyll/translink-extraction which
was the inspiration for this script and a big help in parts

Command-line usage:
-------------------
    Usage:
      translink.py --routes <service>
      translink.py <service> <route_number> <direction>
      translink.py (-h | --help)
      translink.py --version

    Options:
      -h --help     Show this screen.
      --version     Show version.

API usage:
----------
```python
>>> from translink_extractor import get_timetable
>>> timetable = get_timetable('rail', 4, 'inbound')
>>> print json.dumps([x for x in timetable][-1])
{
  "days_of_operation": "Su",
  "operator": "NIR",
  "service": "4",
  "stops": [
    {
      "stop_name": "Portrush, (NIR) Rail Station",
      "time": "2110"
    },
    {
      "stop_name": "Dhu Varren, (NIR) Rail Station",
      "time": "2112"
    },
    {
      "stop_name": "Coleraine Univ, (NIR) Rail Station",
      "time": "2118"
    },
    {
      "stop_name": "Coleraine, (NIR) Rail Station",
      "time": "2122"
    }
  ]
}

```



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
