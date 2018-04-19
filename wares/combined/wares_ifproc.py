"""
A class that joins the WARES and 
IFProc files and is able to derive spectra 
with positional information
"""
from wares.utils.file_utils import get_telnc_file, get_nc_file
from wares.netcdf.wares_netcdf import WaresNetCDFFile
import numpy
from scipy.interpolate import interp1d

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
        self.numchannels = self.nc.hdu.header.get('Mode.numchannels')
        self.populate_spectral_xaxis()
        self.combine_files()

    def populate_spectral_xaxis(self):
        self.chans = numpy.arange(self.numchannels)
        center_freq = self.telnc.hdu.header.get('Msip1mm.LineFreq')[0]
        bandwidth = self.nc.hdu.header.get('Mode.Bandwidth')/1000.
        self.frequencies = center_freq + (self.chans - self.numchannels/2) * bandwidth/self.numchannels
        self.velocities = ((self.frequencies - center_freq)/center_freq)*3e5
        
    def interpolate(self, quantity):
        return interp1d(self.antTime, quantity, bounds_error=False, fill_value='extrapolate')(self.specTime)
        
    def combine_files(self):
        self.BufPos = self.interpolate(self.telnc.hdu.data.BufPos).astype(numpy.int)
        self.TelAzMap = self.interpolate(self.telnc.hdu.data.TelAzMap)
        self.TelElMap = self.interpolate(self.telnc.hdu.data.TelElMap)
        
    def process_ps(self):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') != 'Ps':
            print "Not a PS scan"
            return
        refind = self.BufPos == 1
        onind = self.BufPos == 0
        
        self.spectra = numpy.zeros((4, self.numchannels))
        self.refspec = numpy.zeros((4, self.numchannels))
        self.onspec = numpy.zeros((4, self.numchannels))
        for inp in range(4):
            pixind = self.nc.hdu.data.Inputs == inp
            refpixind = numpy.logical_and(refind, pixind)
            onpixind = numpy.logical_and(onind, pixind)

            self.refspec[inp, :] = self.nc.hdu.data.Data[refpixind, :].mean(axis=0)
            self.onspec[inp, :] = self.nc.hdu.data.Data[onpixind, :].mean(axis=0)
            self.spectra[inp, :] = (self.onspec[inp, :] - self.refspec[inp, :])/self.refspec[inp, :]

    def process_on(self):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') != 'On':
            print "Not a ON scan"
            return
        onind = self.BufPos == 0
        
        self.onspec = numpy.zeros((4, self.numchannels))
        for inp in range(4):
            pixind = self.nc.hdu.data.Inputs == inp
            onpixind = numpy.logical_and(onind, pixind)

            self.onspec[inp, :] = self.nc.hdu.data.Data[onpixind, :].mean(axis=0)
            
            
