# marty mcfly imports
from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals

# third-party imports
import requests
from bs4 import BeautifulSoup


def make_request(method, url, **kwargs):
    """Make HTTP request, raising an exception if it fails.
    """
    request_func = getattr(requests, method)
    response = request_func(url, **kwargs)
    # raise an exception if request is not successful
    if not response.status_code == requests.codes.ok:
        response.raise_for_status()
    return BeautifulSoup(response.text)
