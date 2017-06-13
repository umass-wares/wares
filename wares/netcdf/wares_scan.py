"""
The WaresScan class is a simple extension to the
LMThdu class"""

import numpy
from .lmtnetcdffile import LMThdu

class WaresScan(LMThdu):
    def __init__(self, data=None, header=None,
                 filename=None, groupname=None):
        LMThdu.__init__(self, data=data, header=header,
                        filename=filename)
        self.groupname = groupname
         
