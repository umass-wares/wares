import math
import numpy

def sixty(valrad, ra=False):
    """returns a pretty string version of the RA or Dec value. Input
    is in radians. If ra is needed, set ra=True.
    >>> sixty(numpy.radians(63.3233))
    '63:19:23'
    >>> sixty(numpy.radians(4.344*360/24.), ra=True)
    '04:20:38'
    """
    if valrad < 0.0:
        neg = "-"
    else:
        neg = ""
    valdeg = numpy.degrees(valrad)
    if ra:
        valdeg *= 24./360.0
    degs = int(valdeg)
    absdegs = abs(degs)
    valmins = (abs(valdeg)-absdegs)*60.0
    mins = int(valmins)
    secs = int((valmins-mins)*60.0)
    return "%s%02d:%02d:%02d" % (neg, degs, mins, secs)
