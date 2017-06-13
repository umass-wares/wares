from lmtheader import LMTHeader
#from utils.coordinates import sixty

import numpy
from netCDF4 import num2date, date2num
import datetime

class WaresHeader(LMTHeader):

    def __init__(self, ncvariables=None, dimensions=None):
        LMTHeader.__init__(self, ncvariables=ncvariables,
                           dimensions=dimensions,
                           fromold=False)
        
