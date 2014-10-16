import logging
import sys


class FilterLevel(object):
    """ Process only messages with/without given values. """

    def __init__(self, is_good=True, values=[]):
        self.is_good = is_good
        self.values = values

    def filter(self, record):
        if record.levelno in self.values:
            return self.is_good
        return not self.is_good


def getLogger(name):
    """
    Custom format for different log levels.
    """
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    log.propagate = False
    hnd2 = logging.StreamHandler(sys.stdout)
    fmt2 = logging.Formatter(fmt='%(name)-20s %(levelname)-8s %(message)s')
    hnd2.setLevel(logging.NOTSET)
    hnd2.addFilter(FilterLevel(True, [logging.INFO]))
    hnd2.setFormatter(fmt2)
    log.addHandler(hnd2)
    hnd1 = logging.StreamHandler(sys.stdout)
    fmt1 = logging.Formatter(fmt=('%(name)-20s %(levelname)-8s' +
                                  '%(filename)s:%(lineno)s %(message)s'))
    hnd1.setLevel(logging.NOTSET)
    hnd1.addFilter(FilterLevel(False, [logging.INFO]))
    hnd1.setFormatter(fmt1)
    log.addHandler(hnd1)
    return log
