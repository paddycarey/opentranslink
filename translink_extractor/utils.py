# stdlib imports
import collections
# third-party imports
import requests


class OrderedDefaultdict(collections.OrderedDict):
    """
    Simple implementation of an ordered, defaultdict
    """

    def __init__(self, *args, **kwargs):
        if not args:
            self.default_factory = None
        else:
            if not (args[0] is None or callable(args[0])):
                raise TypeError('first argument must be callable or None')
            self.default_factory = args[0]
            args = args[1:]
        super(self.__class__, self).__init__(*args, **kwargs)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = default = self.default_factory()
        return default


# http related functions

def make_get_request(url):
    """
    Fetch the given url, returning its contents as a string
    """
    return requests.get(url).text


def make_post_request(url, formdata):
    """
    Make a post request to the given url, encoding formdata as the body of the
    request
    """
    return requests.post(url, data=formdata).text
