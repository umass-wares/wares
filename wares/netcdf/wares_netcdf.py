from collections import OrderedDict
from .lmtnetcdffile import LMTNetCDFFile
from .waresdata import WaresData
from .wares_header import WaresHeader
#from wares_header import WaresHeader
#from wares_data import WaresData
from .wares_scan import WaresScan
from netCDF4 import Dataset,Variable
import numpy
#from lmtnetcdf import LMTNetCDFFile
import netCDF4
import os
import time

dimensions = {
    #'Header.Mode.Bitcode': ('Header.Mode.Bitcode_slen', 100),
    'time': ('time', None),
    'numinputs': ('numinputs', 4),
}

variables = {
    #'Header.Mode.Bitcode': (numpy.dtype('S1'), ('Header.Mode.Bitcode_slen',),
    #                        {'long_name': 'BOF File name'}),
    'Header.Mode.Clock': (numpy.dtype('float64'), (),
                          {'long_name': 'Clock Frequency in MHz',
                           'units': 'MHz'}),
    'Header.Mode.Bandwidth': (numpy.dtype('float64'), (),
                          {'long_name': 'Bandwidth of Mode in MHz',
                           'units': 'MHz'}),
    'Header.Mode.ADCStreams': (numpy.dtype('int32'), (),
                               {'long_name': 'Number of ADC Time streams'}),
    'Header.Mode.numchannels': (numpy.dtype('int32'), (),
                                {'long_name': 'Number of channels in mode'}),
    'Header.Mode.Gain': (numpy.dtype('int64'), (),
                         {'long_name': 'Gain setting for accumulation'}),
    'Header.Mode.Shift': (numpy.dtype('int64'), (),
                          {'long_name': 'Shift Schedule for FFT'}),
    'Header.Mode.sync_LCM': (numpy.dtype('int32'), (),
                             {'long_name': 'Lowest Common Multiple in FFTs'}),
    'Header.Mode.PFBTaps': (numpy.dtype('int32'), (),
                            {'long_name': 'Number of taps in PFB'}),
    'Header.Mode.FFTSize': (numpy.dtype('int32'), (), 
                            {'long_name': 'Size of FFT'}),
    'Header.Mode.FFTInputs': (numpy.dtype('int32'), (),
                            {'long_name': 'Number of FFT Inputs'}),
    'Header.Mode.roach_id': (numpy.dtype('int32'), (),
                            {'long_name': 'ROACH ID of roach2 board'}),
    'Header.Mode.nbram': (numpy.dtype('int32'), (), 
                            {'long_name': 'Number of BRAMs in design'}),
    'Header.Telescope.ObsNum': (numpy.dtype('int64'), (),
                                 {'long_name': 'Observation Number'}),
    'Header.Telescope.SubObsNum': (numpy.dtype('int64'), (),
                                 {'long_name': 'Sub Observation Number'}),
    'Header.Telescope.ScanNum': (numpy.dtype('int64'), (),
                                 {'long_name': 'Scan Number'}),        
    'Data.Integrate.Inputs': (numpy.dtype('int'), ('time', ),
                              {'long_name': 'Array of Inputs to spectrometer'}),
    'Data.Integrate.acc_n': (numpy.dtype(int), ('time', ),
                             {'long_name': 'Accumulation Number'}),
    'Data.Integrate.sync_n': (numpy.dtype(int), ('time', ),
                              {'long_name': 'Sync count'}),
    'Data.Integrate.sync_scale': (numpy.dtype(int), ('time', ),
                                  {'long_name': 'Sync Scale'}),
    'Data.Integrate.sync_period': (numpy.dtype(int), ('time', ),
                                  {'long_name': 'Sync Period'}),
    'Data.Integrate.sync_time': (numpy.dtype('float'), ('time', ),
                                  {'long_name': 'Sync Time'}),    
    'Data.Integrate.read_time': (numpy.dtype('float'), ('time', ),
                                 {'long_name': 'Read time',
                                  'units': 'seconds'}),
    'Data.Integrate.time': (numpy.dtype('float'), ('time', ),
                                 {'long_name': 'Epoch time',
                                  }),
    }

header_variables = {
    'Header.Mode.Bitcode': 'bitcode',
    'Header.Telescope.source_name': 'source_name',
    'Header.Telescope.ObsNum': 'ObsNum',
    'Header.Telescope.SubObsNum': 'SubObsNum',
    'Header.Telescope.ScanNum': 'ScanNum',
    'Header.Telescope.obspgm': 'obspgm',
    'Header.Mode.Clock': 'clk',
    'Header.Mode.Bandwidth': 'bandwidth',
    'Header.Mode.ADCStreams': 'ADCstreams',
    'Header.Mode.numchannels': 'numchannels',
    'Header.Mode.Gain': 'gain',
    'Header.Mode.Shift': 'shift',
    'Header.Mode.sync_LCM': 'sync_LCM',
    'Header.Mode.PFBTaps': 'pfb_taps',
    'Header.Mode.FFTSize': 'FFTsize',
    'Header.Mode.FFTInputs': 'FFTinputs', 
    'Header.Mode.nbram': 'nbram',
    'Header.Mode.roach_id': 'roach_id'
    }

                            
    

class WaresNetCDFFile(LMTNetCDFFile):

    def __init__(self, filename, mode='r'):
        if mode in ('r', 'a') and not os.path.exists(filename):
            raise Error('NetCDF Error', 'File %s not found' % filename)
        LMTNetCDFFile.__init__(self, filename, mode)
        self.filename = filename
        self.hdus = OrderedDict()
        if mode in ('r', 'a'):
            self._make_hdus()
        self.data_index = 0

#    def _populate_headers(self, variables, dimensions):

#        return WaresHeader(variables, dimensions)

#    def _populate_data(self, variables):

#        return WaresData(variables)

    def _populate_headers(self, variables,
                          dimensions):
        return WaresHeader(ncvariables=variables,
                              dimensions=dimensions)

    def _populate_data(self, variables):
        return WaresData(variables)

    def _make_hdus(self):
        # if len(self.nc.groups) > 0:
        #     #more than one group available,
        #     #but don't open everything just the first one
        #     #so you don't run out of memory
        #     i = 0
        #     for key, group in self.nc.groups.items():
        #         if i == 0:
        #             data = self._populate_data(group.variables)
        #             header = self._populate_headers(group.variables, group.dimensions)
        #             self.hdus[key] = WaresScan(data=data, header=header,
        #                                        filename=self.filename)
        #         else:
        #             self.hdus[key] = None
        #         i += 1
        # else:
        #only one single root group
        data = self._populate_data(self.nc.variables)
        header = self._populate_headers(self.nc.variables, self.nc.dimensions)
        self.hdus['rootgrp'] = WaresScan(data=data, header=header,
                                         filename=self.filename)
        self.hdu = self.hdus.values()[0]

    #sdef make_hdu(self, spectrometer, 

    def create_dimensions(self, specobj):
        for (dimname, dimlen) in dimensions.values():
            self.nc.createDimension(dimname, dimlen)
        self.nc.createDimension('Header.Mode.Bitcode_slen', len(specobj.mode.bitcode))
        if specobj.source_name is None:
            specobj.source_name = 'None'
        self.nc.createDimension('Header.Telescope.source_name_slen', len(specobj.source_name))
        if specobj.obspgm is None:
            specobj.obspgm = 'None'
        self.nc.createDimension('Header.Telescope.obspgm_slen', len(specobj.obspgm)) 
        self.nc.createDimension('numchannels', specobj.mode.numchannels)
        
    def create_variables(self, specobj):
        for varname, (dtype, dims, ncattrs) in variables.items():
            var = self.nc.createVariable(varname, dtype, dims)
            for attrname, attrval in ncattrs.items():
                var.setncattr(attrname, attrval)
        #var = self.nc.createVariable('Header.Mode.Bitcode', numpy.dtype('S%d' % len(specobj.mode.bitcode)), ('Header.Mode.Bitcode_slen', ))
        var = self.nc.createVariable('Header.Mode.Bitcode', numpy.dtype('S1'), ('Header.Mode.Bitcode_slen', ))
        var = self.nc.createVariable('Header.Telescope.source_name', numpy.dtype('S1'), ('Header.Telescope.source_name_slen', ))
        var = self.nc.createVariable('Header.Telescope.obspgm', numpy.dtype('S1'), ('Header.Telescope.obspgm_slen', ))        
        var = self.nc.createVariable('Data.Integrate.Data', numpy.dtype('float'), ('time', 'numchannels'))
        var.setncattr('long_name', 'Spectrum')
        
    def create_header(self, specobj):
        for varname, attrname in header_variables.items():
            print varname
            if varname == 'Header.Mode.Bitcode':
                bcode = getattr(specobj.mode,  attrname)
                self.nc.variables['Header.Mode.Bitcode'][:len(bcode)] = netCDF4.stringtochar(numpy.array([bcode]))
            elif varname == 'Header.Mode.roach_id':
                self.nc.variables[varname][:] = getattr(specobj, 'roach_id')
            elif varname == 'Header.Telescope.source_name':
                sname = specobj.source_name
                self.nc.variables['Header.Telescope.source_name'][:len(sname)] = netCDF4.stringtochar(numpy.array([sname]))
            elif varname == 'Header.Telescope.obspgm':
                obspgm = specobj.obspgm
                self.nc.variables['Header.Telescope.obspgm'][:len(obspgm)] = netCDF4.stringtochar(numpy.array([obspgm]))
            elif varname in ('Header.Telescope.ObsNum', 'Header.Telescope.SubObsNum', 'Header.Telescope.ScanNum'):
                self.nc.variables[varname][:] = getattr(specobj, attrname)
            else:
                self.nc.variables[varname][:] = getattr(specobj.mode, attrname)

    def create_data(self, specobj, inp):
        specdata = specobj.inputs[inp]
        self.nc.variables['Data.Integrate.Inputs'][self.data_index] = specdata.inp
        self.nc.variables['Data.Integrate.acc_n'][self.data_index] = specdata.acc_n
        self.nc.variables['Data.Integrate.sync_n'][self.data_index] = specdata.sync_n
        self.nc.variables['Data.Integrate.read_time'][self.data_index] = specdata.read_time
        self.nc.variables['Data.Integrate.Data'][self.data_index, :] = specdata.data
        self.nc.variables['Data.Integrate.sync_scale'][self.data_index] = specobj.sync_scale
        self.nc.variables['Data.Integrate.sync_period'][self.data_index] = specobj.sync_period
        self.nc.variables['Data.Integrate.sync_time'][self.data_index] = specobj.sync_time
        self.nc.variables['Data.Integrate.time'][self.data_index] = time.time()
        self.data_index += 1
        
    def setup_scan(self, specobj):
        groupName = "Spectrometer"
        self.nc.createGroup(groupName)
        self.create_dimensions(specobj)
        self.create_variables(specobj)
        self.create_header(specobj)

    def save_scan(self, specobj, inp):
        self.create_data(specobj, inp)

    def save_single_scan(self, specobj, specdata):
        self.nc.variables['Data.Integrate.Inputs'][self.data_index] = specdata.inp
        self.nc.variables['Data.Integrate.acc_n'][self.data_index] = specdata.acc_n
        self.nc.variables['Data.Integrate.sync_n'][self.data_index] = specdata.sync_n
        self.nc.variables['Data.Integrate.read_time'][self.data_index] = specdata.read_time
        self.nc.variables['Data.Integrate.Data'][self.data_index, :] = specdata.data
        self.nc.variables['Data.Integrate.sync_scale'][self.data_index] = specobj.sync_scale
        self.nc.variables['Data.Integrate.sync_period'][self.data_index] = specobj.sync_period
        self.nc.variables['Data.Integrate.sync_time'][self.data_index] = specobj.sync_time
        self.nc.variables['Data.Integrate.time'][self.data_index] = specdata.time
        self.data_index += 1
            
    def save_all_scans(self, specobj):
        specdatas = specobj.spec_dumps
        self.data_index = 0
        for i, specdata in enumerate(specdatas):
            self.nc.variables['Data.Integrate.Inputs'][self.data_index] = specdata.inp
            self.nc.variables['Data.Integrate.acc_n'][self.data_index] = specdata.acc_n
            self.nc.variables['Data.Integrate.sync_n'][self.data_index] = specdata.sync_n
            self.nc.variables['Data.Integrate.read_time'][self.data_index] = specdata.read_time
            self.nc.variables['Data.Integrate.Data'][self.data_index, :] = specdata.data
            self.nc.variables['Data.Integrate.sync_scale'][self.data_index] = specobj.sync_scale
            self.nc.variables['Data.Integrate.sync_period'][self.data_index] = specobj.sync_period
            self.nc.variables['Data.Integrate.sync_time'][self.data_index] = specobj.sync_time
            self.nc.variables['Data.Integrate.time'][self.data_index] = specdata.time
            self.data_index += 1
            
        
    def close_scan(self):
        self.nc.sync()
        self.nc.close()
        
    # def _make_hdu(self):

    #     #data = self._populate_data(self.variables)
    #     #header = self._populate_headers(self.variables, self.dimensions)

    #     self.ds.createDimension('numchannels', self.dimensions['numchannels'])
    #     self.ds.createVariable('spectrum', numpy.dtype(numpy.float32), 'numchannels')
    #     self.ds.variables['spectrum'] = self.variables['spectrum']
    #     #self.nc.variables['spectrum'].__setattr__('test', 0)

    #     self.ds.close()
