"""
A class that joins the WARES and 
IFProc files and is able to derive spectra 
with positional information
"""
from wares.utils.file_utils import get_telnc_file, get_nc_file
from wares.netcdf.wares_netcdf import WaresNetCDFFile
import numpy
from scipy.interpolate import interp1d
from matplotlib.mlab import griddata

class SpectrumIFProc():
    def __init__(self, obsnum):
        self.nc = WaresNetCDFFile(get_nc_file(obsnum))
        self.telnc = WaresNetCDFFile(get_telnc_file(obsnum))
        self.obsnum = obsnum
        if self.telnc.hdu.header.SourceName != self.nc.hdu.header.get('Telescope.source_name'):
            print "Source Name not same in IFProc and WARES files"
        if self.telnc.hdu.header.ObsPgm != self.nc.hdu.header.get('Telescope.obspgm'):
            print "ObsPgm not same in IFProc and WARES files"
        self.antTime = self.telnc.hdu.data.BasebandTime - self.telnc.hdu.data.BasebandTime[0]
        self.specTime = self.nc.hdu.data.time - self.nc.hdu.data.time[0]
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
        return interp1d(self.antTime, quantity, fill_value='extrapolate')(self.specTime)
        
    def combine_files(self):
        self.BufPos = self.interpolate(self.telnc.hdu.data.BufPos).astype(numpy.int)
        self.TelAzMap = self.interpolate(self.telnc.hdu.data.TelAzMap)
        self.TelElMap = self.interpolate(self.telnc.hdu.data.TelElMap)
        
    def process_ps(self):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') != 'Ps':
            print "Not a PS scan"
            return
        num_repeats = self.telnc.hdu.header.get('Ps.NumRepeats')
        bufind_edges = list(numpy.where(numpy.diff(self.BufPos) != 0)[0])
        bufind_edges.insert(0, 0)
        bufind_edges.append(bufind_edges[-1] + 50000)
        #refind = self.BufPos == 1
        #onind = self.BufPos == 0

        
        self.spectra = numpy.zeros((num_repeats, 4, self.numchannels))
        self.refspec = numpy.zeros((num_repeats, 4, self.numchannels))
        self.onspec = numpy.zeros((num_repeats, 4, self.numchannels))
        self.combined_spectra = numpy.zeros((4, self.numchannels))
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
                                      linewindows=[(-10, 10),]):
        if self.telnc.hdu.header.get('Dcs.ObsPgm') not in ('Map', 'Lissajous'):
            print "Not a Map scan"
            return            
        else:
            maptype = self.telnc.hdu.header.get('Dcs.ObsPgm')
        numpixels = self.telnc.hdu.data.BasebandLevel.shape[1]
        self.bias = numpy.zeros((numpixels, self.numchannels))
        numdumps = self.BufPos.size/numpixels
        self.all_spectra = numpy.zeros((numpixels, numdumps, self.numchannels))
        self.xpos = numpy.zeros((numpixels, numdumps))
        self.ypos = numpy.zeros((numpixels, numdumps))
        for inp in range(numpixels):
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
        
            
