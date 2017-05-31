"""This module implements the NetCDF-4 read/write capabilities.
It is a wrapper around python-netCDF4 which in turn depends on
libhdf5 and libnetcdf4
Gopal Narayanan <gopal@astro.umass.edu>
"""
# import netCDF4

# if netCDF4.__version__ <= '0.9.2':
#     # needs _private_atts
#     oldNETCDF4 = True
#     from netCDF4 import Dataset, Variable, _private_atts
# else:
#     oldNETCDF4 = False
#     from netCDF4 import Dataset, Variable
from netCDF4 import Dataset, Variable

#from netCDF4 import Dataset, Variable, _private_atts
import numpy


class NetCDFFile(Dataset, object):
    #if oldNETCDF4:
     #   _private_atts.extend(['filename', 'hdu', 'hdus'])
    def __init__(self, filename, mode='r', 
                 clobber=True, format='NETCDF4'):
        #self.__dict__['filename'] = filename
        #self.__dict__['hdu'] = None
        #self.__dict__['hdus'] = None
        super(NetCDFFile, self).__init__(filename, mode=mode,
                                         clobber=clobber, format=format)
        #self.__dict__['filename'] = filename
        #self.filename = filename
        

def Variable_repr(self):
    if self.dtype == numpy.dtype('c'):
        return "%s" % self.tostring().strip()
    else:
        return "%s" % self[:]

NetCDFVariable = Variable

#Variable.__str__ = Variable_repr

