"""
A class that joins the WARES and 
IFProc files and is able to derive spectra 
with positional information
"""
from wares.utils.file_utils import get_telnc_file, get_nc_file
from wares.netcdf.wares_netcdf import WaresNetCDFFile
from wares.logging import logger
import numpy
from scipy.interpolate import interp1d
from matplotlib.mlab import griddata
from scipy.signal import medfilt
from scipy import __version__ as scipy_version
logger.name = __name__

class SpectrumIFProc():
    def __init__(self, obsnum, roach_id=0,
                 spec_basepat='/data_lmt/spectrometer'):

        # Spectrometer NetCDF (wares spectra)
        self.nc = WaresNetCDFFile(get_nc_file(obsnum, basepat=spec_basepat,
                                              roach_id=roach_id))

        # Telescope NetCDF (Total Power, Telescope information)
        self.telnc = WaresNetCDFFile(get_telnc_file(obsnum))

        if self.telnc.hdu.header.SourceName != self.nc.hdu.header.get('Telescope.source_name'):
            print "Source Name not same in IFProc and WARES files"
        if self.telnc.hdu.header.ObsPgm != self.nc.hdu.header.get('Telescope.obspgm'):
            print "ObsPgm not same in IFProc and WARES files"

        self.obsnum = obsnum
        self.obspgm = self.telnc.hdu.header.ObsPgm
        #self.antTime = self.telnc.hdu.data.BasebandTime - self.telnc.hdu.data.BasebandTime[0]
        self.antTime = self.telnc.hdu.data.TelTime - self.telnc.hdu.data.TelTime[0] # Antenna Time [s]
        self.specTime = self.nc.hdu.data.time - self.nc.hdu.data.time[0] # Wares Time [s]
        self.numchannels = self.nc.hdu.header.get('Mode.numchannels') # no. of bins in Wares mode spectrum
        self.numpixels = self.telnc.hdu.data.BasebandLevel.shape[1] 
        self.populate_spectral_xaxis() #??
        self.combine_files() #see below

    def populate_spectral_xaxis(self):
        """
        Adds "x-axis" arrays to the class variables.
        
        """
        self.chans = numpy.arange(self.numchannels)
        receiver = self.telnc.hdu.header.get('Dcs.Receiver')
        center_freq = self.telnc.hdu.header.get('%s.LineFreq' % receiver)[0]
        bandwidth = self.nc.hdu.header.get('Mode.Bandwidth')/1000.
        self.frequencies = center_freq + (self.chans - self.numchannels/2) * bandwidth/self.numchannels
        self.velocities = ((self.frequencies - center_freq)/center_freq)*3e5
        
    def interpolate(self, quantity):
        """
        Uses 'scipy.interp1d'

        Interpolating function: quantity(antTime)
        Where 'quantity' is a telescope position time series (BufPos, TelAzMap, TelElMap)
        and 'antTime' is the Antenna Time

        Abscissa: specTime
        
        returns: quantitiy(specTime)
        """

        if scipy_version >= '0.17.0':
            return interp1d(self.antTime, quantity, fill_value='extrapolate')(self.specTime)
        else:
            return interp1d(self.antTime, quantity)(self.specTime)
        
    def combine_files(self):
        """
        Calls 'self.interpolate' to set telescope position time series (BufPos, TelAzMap,
        TelElMap) from Antenna Time to Wares Time
        """

        self.BufPos = self.interpolate(self.telnc.hdu.data.BufPos).astype(numpy.int)
        self.TelAzMap = self.interpolate(self.telnc.hdu.data.TelAzMap)
        self.TelElMap = self.interpolate(self.telnc.hdu.data.TelElMap)
        
    def process_ps(self):
        """
        Process spectra if ObsPgm is Position Switch ('Ps')
        """
        
        if self.telnc.hdu.header.get('Dcs.ObsPgm') != 'Ps':
            print "Not a PS scan"
            return
        num_repeats = self.telnc.hdu.header.get('Ps.NumRepeats')
        
        # Finds indices that match a switching BufPos
        bufind_edges = list(numpy.where(numpy.diff(self.BufPos) != 0)[0])
        bufind_edges.insert(0, 0)
        bufind_edges.append(bufind_edges[-1] + 50000) # Adding 50,000*t_res [s] ?
        #refind = self.BufPos == 1
        #onind = self.BufPos == 0

        self.spectra = numpy.zeros((num_repeats, self.numpixels, self.numchannels))
        self.refspec = numpy.zeros((num_repeats, self.numpixels, self.numchannels))
        self.onspec = numpy.zeros((num_repeats, self.numpixels, self.numchannels))
        self.combined_spectra = numpy.zeros((self.numpixels, self.numchannels))
        
        for rpt in range(num_repeats):
            refind_start = bufind_edges[2*rpt] + 2 
            refind_end = bufind_edges[2*rpt + 1] - 2 
            onind_start = bufind_edges[2*rpt+1] + 2
            onind_end = bufind_edges[2*(rpt+1)] - 2
            refind = numpy.zeros(self.BufPos.size, dtype=numpy.bool)
            onind = numpy.zeros(self.BufPos.size, dtype=numpy.bool)
            refind[refind_start:refind_end] = True
            onind[onind_start:onind_end] = True
            for inp in range(4):
                pixind = self.nc.hdu.data.Inputs == inp
                refpixind = numpy.logical_and(refind, pixind)
                onpixind = numpy.logical_and(onind, pixind)
                self.refspec[rpt, inp, :] = self.nc.hdu.data.Data[refpixind, :].mean(axis=0)
                self.onspec[rpt, inp, :] = self.nc.hdu.data.Data[onpixind, :].mean(axis=0)
                self.spectra[rpt, inp, :] = (self.onspec[rpt, inp, :] - self.refspec[rpt, inp, :])/self.refspec[rpt, inp, :]
        
        for inp in range(4):
            self.combined_spectra[inp, :] = self.spectra[:, inp, :].mean(axis=0)

        

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

    def process_ifproc_map(self, remove_offset=False, numoff=20,
                           scigrid=False,
                           **kwargs):
        """
        processes Map Obspgm that has been made in IFProc
        continuum mode. Uses a regridding algorithm
        and uses some kwargs arguments to derive output
        grid size and sampling
        """
        if self.telnc.hdu.header.ObsPgm not in ('Map', 'Lissajous'):
            logger.error("Not a Map datafile")
            return
        else:
            maptype = self.telnc.hdu.header.ObsPgm
        logger.info("Processing MSIP 1mm Continuum Map data and regridding for Observation with ObsNum %d" % int(self.telnc.hdu.header.ObsNum))
        self.numpixels = self.telnc.hdu.data.BasebandLevel.shape[1]
        xlength = numpy.degrees(self.telnc.hdu.header.get('%s.XLength' % maptype))*3600.0
        ylength = numpy.degrees(self.telnc.hdu.header.get('%s.YLength' % maptype))*3600.0
        if maptype == 'Lissajous':
            xlength = xlength/numpy.cos(numpy.radians(45))
            xlength = ylength/numpy.cos(numpy.radians(45))
        ind = numpy.where(self.telnc.hdu.data.BufPos == 0)
        xpos = numpy.degrees(self.telnc.hdu.data.TelAzMap[ind])*3600.
        ypos = numpy.degrees(self.telnc.hdu.data.TelElMap[ind])*3600.
        rows = self.telnc.hdu.header.get('Map.RowsPerScan')
        z = {}
        self.off_source = {}
        for chan in range(self.numpixels):
            z[chan] = self.telnc.hdu.data.BasebandLevel[ind, chan].flatten()
            self.off_source[chan] = numpy.histogram(self.telnc.hdu.data.BasebandLevel[ind, chan].flatten())[1][:4].mean()
            if remove_offset:
                z[chan] = z[chan] - self.off_source[chan]
            print z[chan].shape
        ramp = kwargs.get('ramp', 5.)
        numpoints = kwargs.get('numpoints', 100)
        numypoints = kwargs.get('numypoints', 100)
        xlength = xlength * (1.-ramp/100.)
        ylength = ylength * (1.-ramp/100.)
        ind = numpy.logical_and(xpos > -xlength/2., xpos < xlength/2.)
        xpos, ypos = xpos[ind], ypos[ind]
        # add a tiny random number to stop griddata from crashing when two pixels are same
        xpos = xpos + numpy.random.random(xpos.size)*1e-6
        ypos = ypos + numpy.random.random(ypos.size)*1e-6
        for chan in range(self.numpixels):
            z[chan] = z[chan][ind]
        ind = numpy.logical_and(ypos > -ylength/2., ypos < ylength/2.)
        xpos, ypos = xpos[ind], ypos[ind]
        for chan in range(self.numpixels):
            z[chan] = z[chan][ind]
        self.xi = numpy.linspace(-xlength/2, xlength/2, numpoints)
        self.yi = numpy.linspace(-ylength/2, ylength/2, numypoints)
        print "Making %d x %d map" % (numpoints, numypoints)
        #self.z = z
        #self.xpos = xpos
        #self.ypos = ypos
        self.BeamMap = numpy.zeros((self.yi.size, self.xi.size, self.numpixels))
        for chan in range(self.numpixels):
            #self.BeamMap[chan] = numpy.zeros((self.yi.size, self.xi.size),
            #                                 dtype='float')
            if scigrid:
                self.BeamMap[:, :, chan] = scipy.interpolate.griddata(xpos, ypos, z[chan], (self.xi, self.yi),
                                                                      method='cubic')
            else:
                self.BeamMap[:, :, chan] = griddata(xpos, ypos, z[chan], self.xi, self.yi)
            
    def baseline(self, windows=[(-100, -50), (50, 100)], order=0,
                 subtract=False):
        self.windows = windows
        for i, win in enumerate(self.windows):
            c1, c2 = win
            c1, c2 = sorted([c1, c2])
            ind = numpy.logical_and(self.velocities >= c1, self.velocities <=c2)
            if i == 0:
                finalind = numpy.logical_or(ind, ind)
            else:
                finalind = numpy.logical_or(finalind, ind)
        num_repeats = self.telnc.hdu.header.get('Ps.NumRepeats')
        self.sigma = numpy.zeros((num_repeats, 4))
        self.combined_sigma = numpy.zeros(4)
        ind = numpy.where(finalind)
        for rpt in range(num_repeats):
            for inp in range(4):
                p = numpy.polyfit(self.velocities[ind], self.spectra[rpt, inp, :][ind], order)
                self.spectra[rpt, inp, :] = self.spectra[rpt, inp, :] - numpy.polyval(p, self.velocities)
                self.sigma[rpt, inp] = self.spectra[rpt, inp, :][ind].std()
                if not subtract:
                    self.spectra[rpt, inp, :] = self.spectra[rpt, inp, :] + numpy.polyval(p, self.velocities)

        #for inp in range(4):
        #    self.combined_spectra[inp, :] = self.spectra[:, inp, :].mean(axis=0)
        # need to do a better job of combined sigma
        
        for inp in range(4):
            #self.combined_spectra[inp, :] = self.spectra[:, inp, :].mean(axis=0)
            p = numpy.polyfit(self.velocities[ind], self.combined_spectra[inp, :][ind], order)
            self.combined_spectra[inp, :] = self.combined_spectra[inp, :] - numpy.polyval(p, self.velocities)
            self.combined_sigma[inp] = self.combined_spectra[inp, :][ind].std()
            if not subtract:
                self.combined_spectra[inp, :] = self.combined_spectra[inp, :] + numpy.polyval(p, self.velocities)
                              
    def get_area(self, windows=[(-25, 25)]):
        if not hasattr(self, 'combined_sigma'):
            print "First obtain baseline"
            return
        for i, win in enumerate(windows):
            c1, c2 = win
            c1, c2 = sorted([c1, c2])
            ind = numpy.logical_and(self.velocities >= c1, self.velocities <=c2)
            if i == 0:
                finalind = numpy.logical_or(ind, ind)
            else:
                finalind = numpy.logical_or(finalind, ind)
        deltav = numpy.abs(self.velocities[1] - self.velocities[0])
        self.area = numpy.zeros(4)
        self.area_uncertainty = numpy.zeros(4)
        ind = numpy.where(finalind)
        N = ind[0].size
        for inp in range(4):
            self.area[inp] = self.combined_spectra[inp, :][ind].sum() * deltav
            self.area_uncertainty[inp] = self.combined_sigma[inp] * deltav * numpy.sqrt(N)

    def process_spectral_map(self, channels=[500, 1500]):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') not in ('Map', 'Lissajous'):
            print "Not a Map scan"
            return            
        else:
            maptype = self.telnc.hdu.header.get('Dcs.ObsPgm')
        numpixels = self.telnc.hdu.data.BasebandLevel.shape[1]             
        xlength = numpy.degrees(self.telnc.hdu.header.get('%s.XLength' % maptype))*3600.0
        ylength = numpy.degrees(self.telnc.hdu.header.get('%s.YLength' % maptype))*3600.0
        if maptype == 'Lissajous':
            xlength = xlength/numpy.cos(numpy.radians(45))
            xlength = ylength/numpy.cos(numpy.radians(45))
        xpos = numpy.degrees(self.TelAzMap)*3600.
        ypos = numpy.degrees(self.TelElMap)*3600.
        rows = self.telnc.hdu.header.get('Map.RowsPerScan')                             
        outsideind = numpy.zeros(self.TelAzMap.size, dtype=numpy.bool)
        outsideind[:100] = True
        outsideind[-100:] = True # take outer region
        offspectra = numpy.zeros((numpixels, self.numchannels))
        for inp in range(numpixels):
            pixind = self.nc.hdu.data.Inputs == inp
            offind = numpy.logical_and(outsideind, pixind)
            offspectra[inp, :] = self.nc.hdu.data.Data[offind, :].mean(axis=0)
        chan_start, chan_end = channels
        onspectra = numpy.zeros((numpixels, self.TelAzMap.size/4, self.numchannels))
        self.onoffspectra = numpy.zeros((numpixels, self.TelAzMap.size/4, self.numchannels))
        for inp in range(numpixels):
            pixind = self.nc.hdu.data.Inputs == inp
            onspectra[inp, :, :] = self.nc.hdu.data.Data[pixind, :]
            self.xpos = xpos[pixind]
            self.ypos = ypos[pixind]
            offspec = offspectra[inp, :]
            offspec.shape = (1, 1, self.numchannels)
            self.onoffspectra[inp, :, :] = onspectra[inp, :, :] - offspec

    def process_pointing_spectral_map(self, windows=[(-100, -50), (50, 100)],
                                      order=1,
                                      subtract=True,
                                      num_imagepixels=200,
                                      linewindows=[(-10, 10),],
                                      ignore_reference=False,
                                      median_filter=True):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') not in ('Map', 'Lissajous'):
            print "Not a Map scan"

            return            
        else:
            maptype = self.telnc.hdu.header.get('Dcs.ObsPgm')
        numpixels = self.telnc.hdu.data.BasebandLevel.shape[1]
        self.bias = numpy.zeros((numpixels, self.numchannels))
        onind = self.BufPos == 0
        numdumps = numpy.where(onind)[0].size/4
        self.all_spectra = numpy.zeros((numpixels, numdumps, self.numchannels))
        print self.all_spectra.shape
        self.xpos = numpy.zeros((numpixels, numdumps))
        self.ypos = numpy.zeros((numpixels, numdumps))            
        if not ignore_reference and (self.BufPos == 1).any():
            # Map with separate reference position in
            print "Processing line map with reference pos observations"
            onind = self.BufPos == 0
            refind = self.BufPos == 1
            for inp in range(4):
                pixind = self.nc.hdu.data.Inputs == inp
                onpixind = numpy.logical_and(onind, pixind)
                pixspectra = self.nc.hdu.data.Data[onpixind, :][:numdumps, :] # need this to ensure right sizes
                print pixspectra.shape
                refpixind = numpy.logical_and(refind, pixind)
                self.bias[inp, :] = self.nc.hdu.data.Data[refpixind, :].mean(axis=0)
                self.bias[inp, :].shape = (1, self.numchannels)
                pixspectra = (pixspectra - self.bias[inp, :])/self.bias[inp, :]
                self.xpos[inp, :] = self.TelAzMap[onpixind][:numdumps]
                self.ypos[inp, :] = self.TelElMap[onpixind][:numdumps]
                self.all_spectra[inp, :, :] = pixspectra            
        else:
            for inp in range(4):
                pixind = self.nc.hdu.data.Inputs == inp
                pixspectra = self.nc.hdu.data.Data[pixind, :]
                self.bias[inp, :] = numpy.median(pixspectra, axis=0)
                self.bias[inp, :].shape = (1, self.numchannels)
                pixspectra = (pixspectra - self.bias[inp, :])/self.bias[inp, :]
                self.xpos[inp, :] = self.TelAzMap[pixind]
                self.ypos[inp, :] = self.TelElMap[pixind]
                self.all_spectra[inp, :, :] = pixspectra
        self.windows = windows
        for i, win in enumerate(self.windows):
            c1, c2 = win
            c1, c2 = sorted([c1, c2])
            ind = numpy.logical_and(self.velocities >= c1, self.velocities <=c2)
            if i == 0:
                finalind = numpy.logical_or(ind, ind)
            else:
                finalind = numpy.logical_or(finalind, ind)
        ind = numpy.where(finalind)
        for inp in range(4):
            for ipos in range(numdumps):
                p = numpy.polyfit(self.velocities[ind], self.all_spectra[inp, ipos, :][ind], order)
                self.all_spectra[inp, ipos, :] = self.all_spectra[inp, ipos, :] - numpy.polyval(p, self.velocities)
                
        for i, win in enumerate(linewindows):
            c1, c2 = win
            c1, c2 = sorted([c1, c2])
            ind = numpy.logical_and(self.velocities >= c1, self.velocities <=c2)
            if i == 0:
                finalind = numpy.logical_or(ind, ind)
            else:
                finalind = numpy.logical_or(finalind, ind)

        deltav = numpy.abs(self.velocities[1] - self.velocities[0])
        self.specarea = numpy.zeros((numpixels, numdumps))
        ind = numpy.where(finalind)
        for inp in range(4):
            self.specarea[inp] = self.all_spectra[inp, :, ind].sum(axis=1) * deltav
            if median_filter:
                self.specarea[inp] = medfilt(self.specarea[inp])
            
        self.xi = numpy.zeros((4, num_imagepixels))
        self.yi = numpy.zeros((4, num_imagepixels))
        self.BeamMap = numpy.zeros((4, num_imagepixels, num_imagepixels))
        for inp in range(4):
            xpos = numpy.degrees(self.xpos[inp, :])*3600
            ypos = numpy.degrees(self.ypos[inp, :])*3600
            xmin, xmax = xpos.min(), xpos.max()
            ymin, ymax = ypos.min(), ypos.max()
            self.xi[inp, :] = numpy.linspace(xmin, xmax, num_imagepixels)
            self.yi[inp, :] = numpy.linspace(ymin, ymax, num_imagepixels)
            self.BeamMap[inp, :, :] = griddata(xpos, ypos, self.specarea[inp], self.xi[inp], self.yi[inp])
        
    def process_spectral_cal(self, Tamb=280):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') not in ('Cal'):
            print "Not a Map scan"
            return
        numpixels = self.telnc.hdu.data.BasebandLevel.shape[1]
        self.tsys_spec = numpy.zeros((numpixels, self.numchannels))
        self.tsys = numpy.zeros(numpixels)
        hotind = self.BufPos == 3
        skyind = self.BufPos == 2
        for inp in range(numpixels):
            pixind = self.nc.hdu.data.Inputs == inp
            indexh = numpy.logical_and(hotind, pixind)
            indexs = numpy.logical_and(skyind, pixind)
            hotspec = medfilt(self.nc.hdu.data.Data[indexh, :].mean(axis=0))
            skyspec = medfilt(self.nc.hdu.data.Data[indexs, :].mean(axis=0))
            self.tsys_spec[inp, :] = Tamb * skyspec/(hotspec - skyspec)
            self.tsys[inp] = self.tsys_spec[inp, 100: self.numchannels-100].mean()
            print "Pixel: %d, Tsys: %.3f K" % (inp, self.tsys[inp])
