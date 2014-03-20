===============================
OpenTranslink
===============================


The OpenTranslink project aims to provide a simple pythonic interface to public data on translink.co.uk e.g. timetables

* Free software: MIT license
* Documentation: http://github.com/paddycarey/opentranslink.

Features
~~~~~~~~

* Route/Service listings
* Bus Timetables

Future Features
~~~~~~~~~~~~~~~

* A better/nicer API.
* Train timetables
* Train status
* Journey Planner
* Route Maps


Usage
-----

Getting started
~~~~~~~~~~~~~~~

Once the library's a bit more mature, it'll be installable from pypi, but for now, just clone repo repo and run `python setup.py install`.

The top-level object in opentranslink (for now) is the `Service`, you should initialise the service you need after importing the module::

    import opentranslink

    # initialise a client for each available service
    goldline = opentranslink.Service('goldline')
    metro = opentranslink.Service('metro')
    ulsterbus = opentranslink.Service('ulsterbus')

Retrieving route listings
~~~~~~~~~~~~~~~~~~~~~~~~~

You can retrieve a full list of routes for a given service using its `route()` method::

    >>> print metro.routes()
    [<opentranslink.Route-1A>, <opentranslink.Route-1B>, <opentranslink.Route-1C>, ...]

You can also retrieve a specific route using its code::

    >>> print metro.route('1A')
    <opentranslink.Route-1A>

Working with timetables
~~~~~~~~~~~~~~~~~~~~~~~

Route objects contain a `timetable` property which is used to interact with any available timetable for the route::

    >>> route = goldline.route('273')
    >>> print route.timetable
    [
        (u'Mondays to Fridays', <dataset object>),
        (u'Saturdays', <dataset object>),
        (u'Sundays', <dataset object>),
        (u'Mondays to Fridays', <dataset object>),
        (u'Saturdays', <dataset object>),
        (u'Sundays', <dataset object>)
    ]

`timetable` returns a list of tuples. Each tuple returned contains a label for the corresponding dataset (better labels will be added soon, including inbound/outbound direction). the dataset objects shown are tablib.Dataset objects, you can read more about these in the `tablib documentation <http://docs.python-tablib.org>`_

Interacting with the dataset objects is simple::

    >>> dataset = route.timetable[0][1]

    >>> # show list of stops on this route
    >>> print dataset.headers
    [u'Belfast City Centre, Europa Buscentre', u'Lurgan, Loughview Park and Ride Lough Road', ...]

    >>> # show the timetable for the fifth bus of the day
    >>> print zip(dataset.headers, dataset[4])
    [(u'Belfast City Centre, Europa Buscentre', u'0835'), (u'Lurgan, Loughview Park and Ride Lough Road', u'0900'), ...]

You can dump the timetable to a whole host of formats using tablib's export features::

    >>> print dataset.json
    >>> print dataset.csv
    >>> print dataset.yaml
    >>> print dataset.xls


Reporting Bugs
~~~~~~~~~~~~~~

Report bugs (there are lots, I know) at https://github.com/paddycarey/opentranslink/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.
