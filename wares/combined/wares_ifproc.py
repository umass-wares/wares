"""
A class that joins the WARES and 
IFProc files and is able to derive spectra 
with positional information
"""
from wares.utils.file_utils import get_telnc_file, get_nc_file
from wares.netcdf.wares_netcdf import WaresNetCDFFile
import numpy

class SpectrumIFProc():
    def __init__(self, obsnum):
        self.nc = WaresNetCDFFile(get_nc_file(obsnum))
        self.telnc = WaresNetCDFFile(get_telnc_file(obsnum))
        if self.telnc.hdu.header.SourceName != self.nc.hdu.header.get('Telescope.source_name'):
            print "Source Name not same in IFProc and WARES files"
        if self.telnc.hdu.header.ObsPgm != self.nc.hdu.header.get('Telescope.obspgm'):
            print "ObsPgm not same in IFProc and WARES files"
        self.antTime = self.telnc.hdu.data.BasebandTime
        self.specTime = self.nc.hdu.data.time
        self.combine_files()

    def interpolate(self, quantity):
        return numpy.interp(self.specTime, self.antTime, quantity)
        
    def combine_files(self):
        self.BufPos = self.interpolate(self.telnc.hdu.data.BufPos)
        self.TelAzMap = self.interpolate(self.telnc.hdu.data.TelAzMap)
        self.TelElMap = self.interpolate(self.telnc.hdu.data.TelElMap)
        
