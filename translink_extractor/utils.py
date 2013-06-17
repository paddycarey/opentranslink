# stdlib imports
import time
import urllib
import urllib2
from collections import OrderedDict, Callable


def retry(ExceptionToCheck, tries=4, delay=0.5, backoff=2, logger=None):

    """
    Ye olde retry decorator

    Catches exceptions in wrapped funcs and retries them using an exponential
    backoff until a maximum number of retries has been reached, at which point
    it raises the original exception if the func is still failing
    """

    def deco_retry(f):
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            try_one_last_time = True
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                    try_one_last_time = False
                    break
                except ExceptionToCheck, e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print msg
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            if try_one_last_time:
                return f(*args, **kwargs)
            return
        return f_retry  # true decorator
    return deco_retry


class OrderedDefaultDict(OrderedDict):

    def __init__(self, default_factory=None, *a, **kw):
        if (default_factory is not None and not isinstance(default_factory, Callable)):
            raise TypeError('first argument must be callable')
        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __getitem__(self, key):
        try:
            return OrderedDict.__getitem__(self, key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = self.default_factory,
        return type(self), args, None, None, (x for x in self.items())

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        import copy
        return type(self)(self.default_factory, copy.deepcopy(self.items()))

    def __repr__(self):
        return 'OrderedDefaultDict(%s, %s)' % (self.default_factory, OrderedDict.__repr__(self))


# http related functions

@retry(urllib2.HTTPError)
def make_get_request(url):
    """
    Fetch the given url, returning its contents as a string
    """
    return urllib2.urlopen(url).read()


def make_post_request(url, formdata):
    """
    Make a post request to the given url, encoding formdata as the body of the
    request
    """
    return urllib2.urlopen(url, urllib.urlencode(formdata)).read()
