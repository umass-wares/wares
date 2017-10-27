import numpy as np
import struct, datetime, time
#from pylab import plot,xlabel,ylabel
from wares import adc5g
#from wares.tools.adc5g_cal import ADC5g_Calibration_Tools
from wares.tools.adc5g_ogp_inl_tools import ADC5g_Load
from corr import katcp_wrapper
from wares.spectrometer.spectrometer_modes import mode_800, mode_400, mode_200
from wares.spectrometer.spectrometer_integration import SpectrometerIntegration
from wares.netcdf.wares_netcdf import WaresNetCDFFile
from wares.utils.process_stopper import ProcessStopper
from wares.logging import logger
import datetime
import multiprocessing
import Queue
import os

logger.name = __name__

class Spectrometer(object):
    def __init__(self, roach_id='172.30.51.101', katcp_port=7147, mode=800, scale=1024,
                 default_ogp_file='ogp_data/ogp_chans01.npz',
                 default_inl_file='ogp_data/inl_chans01.npz',
                 gain=None, basefile='spectrometer'):

        self.default_ogp_file = default_ogp_file
        self.default_inl_file = default_inl_file        
        self.roach_id = roach_id
        self.katcp_port = katcp_port 

        self.roach = katcp_wrapper.FpgaClient(roach_id)
        self.roach.wait_connected()

        #self.roach = roach

        self.sync_scale = scale
        self.sync_period = None
        self.sync_time = None
        self.acc_len = None
        self.inputs = {}  # a dictionary of spectral classes
        self.spec_dumps = []  # a list of all spectrometer dumps
        self.gain = gain
        # if (mode==800):
        #     if gain is not None:
        #         self.mode = mode_800(gain=gain)
        #     else:
        #         self.mode = mode_800()

        # if (mode==400):
        #     if gain is not None:
        #         self.mode = mode_400(gain=gain)
        #     else:
        #         self.mode = mode_400()

        # if (mode==200):
        #     if gain is not None:
        #         self.mode = mode_200(gain=gain)
        #     else:
        #         self.mode = mode_200()

        self.adc_cal_tools = ADC5g_Load(self.roach, program=False)

        # self.set_sync_period()
        # self.set_acc_len()

        # self.program_device()
        # self.configure()
        self.calADC()
        self.mode_setup(mode=mode)
        self.nc = None
        self.basefile = basefile
        logger.info("Spectrometer class inititated with roach_id: %s" % self.roach_id)
        
    def mode_setup(self, mode=800):
        if (mode==800):
            if self.gain is not None:
                self.mode = mode_800(gain=self.gain)
            else:
                self.mode = mode_800()

        if (mode==400):
            if self.gain is not None:
                self.mode = mode_400(gain=self.gain)
            else:
                self.mode = mode_400()

        if (mode==200):
            if self.gain is not None:
                self.mode = mode_200(gain=self.gain)
            else:
                self.mode = mode_200()

        #self.adc_cal_tools = ADC5g_Load(self.roach, program=False)

        self.set_sync_period()
        self.set_acc_len()

        self.program_device()
        self.configure()
        self.calADC()
        self.start_queue(1000)
        
    def calc_sync_period(self, scale):

        period = ((scale*self.mode.sync_LCM*self.mode.pfb_taps*self.mode.FFTsize)/self.mode.FFTinputs)-2
        return period

    def set_sync_period(self):
    
        self.sync_period = self.calc_sync_period(self.sync_scale)
        self.sync_time = self.sync_period/((self.mode.clk*1e6)/self.mode.ADCstreams)
    
    def set_acc_len(self):

        self.acc_len = self.sync_period/(self.mode.numchannels/self.mode.nbram)

    def calc_scale(self, dump_time):
        """
        Given dump time in seconds, calculates scale as nearest integer
        """
        sync_period = dump_time * (self.mode.clk*1e6)/self.mode.ADCstreams
        scale = int((sync_period + 2) * self.mode.FFTinputs/(self.mode.sync_LCM*self.mode.pfb_taps*self.mode.FFTsize))
        return scale
        
    def program_device(self):

        bitcode = self.mode.bitcode
        self.roach.progdev(bitcode)

        #print 'Programming bitcode %s' %(bitcode)
        logger.info('Programming bitcode %s' %(bitcode))

    def configure(self):

        #print 'Configuring accumulation period to %d...' %self.acc_len,
        logger.info('Configuring accumulation period to %d...' % self.acc_len)
        self.roach.write_int('acc_len', self.acc_len)
        #print 'done'
        logger.info('done')
                                                                                       
        #print 'Setting digital gain of all channels to %i...' %self.mode.gain,
        logger.info('Setting digital gain of all channels to %i...' %self.mode.gain)
        self.roach.write_int('gain', self.mode.gain)
        #print 'done'
        logger.info('done')
        
        #print 'Setting fft shift schedule to %i...' %self.mode.shift,
        logger.info('Setting fft shift schedule to %i...' %self.mode.shift )
        self.roach.write_int('fftshift', self.mode.shift)
        #print 'done'
        logger.info('done')
        
        #print 'Setting sync period to %i...' %self.sync_period,
        logger.info('Setting sync period to %i...' %self.sync_period)
        self.roach.write_int('sync_constant', self.sync_period)
        #print 'done'
        logger.info('done')
        
        self.reset()
        time.sleep(0.1)
    
    def calADC(self):

        #print '------------------------'
        logger.info( '------------------------')
        #print 'Loading default OGP/INL corrections to ADCs'
        logger.info('Loading default OGP/INL corrections to ADCs')
        #self.adc_cal_tools.update_ogp(fname=self.default_ogp_file)
        #self.adc_cal_tools.update_inl(fname=self.default_inl_file)
	for inp in range(4):
		self.adc_cal_tools.fit_og(inp)

    def reset(self):

        #print 'Resetting counters...',
        logger.info('Resetting counters...')
        self.roach.write_int('cnt_rst',1)
        self.roach.write_int('cnt_rst',0)
        #print 'done'
        logger.info('done')

    def get_acc_n(self):

        acc_n = self.roach.read_uint('acc_cnt')
        return acc_n

    def get_sync_cnt(self):

        sync_n = self.roach.read_uint('sync_cnt')
        return sync_n

    def read_bram(self, inp, bramNo):                                                                                                                                                    

        bram_array = np.array(struct.unpack('>%dl' %(self.mode.numchannels/self.mode.nbram),
                                     self.roach.read('bram%i%i' %(inp,bramNo),
                                     4.*(self.mode.numchannels/self.mode.nbram), 0)),
                                     dtype='float')

        return bram_array

    def read_bram_par(self, inp, bramNo):
        print "Inp: %d, bramNo: %d" % (inp, bramNo)
        self.interleave[bramNo::self.mode.nbram] = np.array(struct.unpack('>%dl' %(self.mode.numchannels/self.mode.nbram),
                                     self.roach.read('bram%i%i' %(inp,bramNo),
                                     4.*(self.mode.numchannels/self.mode.nbram), 0)),
                                     dtype='float')

    def integrate_by_input(self, inp):
        print "Integrating on input %d" % inp
        t1 = time.time()
        acc_n = self.get_acc_n()
        sync_n = self.get_sync_cnt()

        interleave = np.empty((self.mode.numchannels,), dtype=float)

        for bramNo in range(self.mode.nbram):

            interleave[bramNo::self.mode.nbram] = self.read_bram(inp, bramNo)

        read_time = time.time() - t1

        print 'Done with integration'
        print 'acc_n = %i, sync_n = %i' %(acc_n, sync_n)

        self.inputs[inp] = SpectrometerIntegration(inp, self.mode.numchannels,
                                                   acc_n, sync_n, read_time,
                                                   interleave)
        if self.nc is None:
            #filename ="%s_%s.nc" % (self.basefile, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
            #self.nc = WaresNetCDFFile(filename, 'w')
            #self.nc.setup_scan(self, inp)
            self.open_nc_file()    
        self.nc.save_scan(self, inp)

    def open_nc_file(self, roach_num=0, obs_num=None, subobs_num=None, scan_num=None,
                     source_name=None, obspgm=None):
        basedir = os.path.join("/data_lmt/spectrometer", "roach%d" % roach_num)
        self.ObsNum, self.SubObsNum, self.ScanNum, self.source_name, self.obspgm = obs_num, subobs_num, scan_num, source_name, obspgm
        self.roach_num = roach_num # roach_num is integer; roach_id is IP address
        if self.ObsNum is not None and self.SubObsNum is not None and self.ScanNum is not None and self.source_name is not None:
            self.basefile = "roach%d_%d_%d_%d_%s" % (self.roach_num, self.ObsNum, self.SubObsNum, self.ScanNum, self.source_name)
        filename ="%s_%s.nc" % (self.basefile, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
        fullpath = os.path.join(basedir, filename)
        #print "Opening filename: %s" % fullpath
        logger.info("Opening filename: %s" % fullpath)
        self.nc = WaresNetCDFFile(fullpath, 'w')
        self.nc.setup_scan(self)
        
    def start_queue(self, numdumps=500):
        self.queue = Queue.Queue(numdumps)
        self.numscans = 0
        
    def integrate(self, inp, write_nc=True, queue_enable=True):

        t1 = time.time()

        acc_n = self.get_acc_n()
        # test code here
        # while len(self.spec_dumps) > 0 and acc_n - self.spec_dumps[-1].acc_n == 0:
        #     time.sleep(0.001)
        #     acc_n = self.get_acc_n()
        # test code finish
        sync_n = self.get_sync_cnt()

        interleave = np.empty((self.mode.numchannels,), dtype=float)

        for bramNo in range(self.mode.nbram):

            interleave[bramNo::self.mode.nbram] = self.read_bram(inp, bramNo)

        read_time = time.time() - t1

        #print 'Done with integration'
        #print 'acc_n = %i, sync_n = %i' %(acc_n, sync_n)
        logger.info('Done with integration')
        logger.info('acc_n = %i, sync_n = %i' % (acc_n, sync_n))

        #if plt:
        #        plot(10.*np.log10(interleave[10:]))
        #        xlabel('FFT Channel')
        #        ylabel('dB')

        self.inputs[inp] = SpectrometerIntegration(inp, self.mode.numchannels,
                                                   acc_n, sync_n, read_time,
                                                   interleave)
        if not queue_enable:
            self.spec_dumps.append(self.inputs[inp])
        if queue_enable and self.queue:
            self.queue.put(self.inputs[inp])
            self.numscans += 1
        if write_nc:
            if self.nc is None:
                self.open_nc_file()
                #filename ="%s_%s.nc" % (self.basefile, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
                #self.nc = WaresNetCDFFile(filename, 'w')
                #self.nc.setup_scan(self, inp)
                
            self.nc.save_scan(self, inp)
            #nc.close_scan()
            
        return acc_n, sync_n, interleave, read_time

    def integrate_all_inputs(self):
        for input in range(4):
            process = multiprocessing.Process(target=self.integrate_by_input, args=(input,))
            process.start()
            time.sleep(0.001)

    def integrate_par(self, inp, write_nc=True):

        t1 = time.time()

        acc_n = self.get_acc_n()
        sync_n = self.get_sync_cnt()

        self.interleave = np.empty((self.mode.numchannels,), dtype=float)
        ncpu = multiprocessing.cpu_count()
        
        #self.pstop = ProcessStopper()
        self.process = {}
        for bramNo in range(self.mode.nbram):
            self.process[bramNo] = multiprocessing.Process(target=self.read_bram_par, args=(inp, bramNo))
            self.process[bramNo].start()
            #self.pstop.add_process(process)
            time.sleep(0.001)
            #interleave[bramNo::self.mode.nbram] = self.read_bram(inp, bramNo)

        
        read_time = time.time() - t1
        #print 'Done with integration'
        #print 'acc_n = %i, sync_n = %i' %(acc_n, sync_n)
        logger.info( 'Done with integration')
        logger.info('acc_n = %i, sync_n = %i' %(acc_n, sync_n))

        #if plt:
        #        plot(10.*np.log10(self.interleave[10:]))
        #        xlabel('FFT Channel')
        #        ylabel('dB')

        self.inputs[inp] = SpectrometerIntegration(inp, self.mode.numchannels,
                                                   acc_n, sync_n, read_time,
                                                   self.interleave)
        if write_nc:
            if self.nc is None:
                self.open_nc_file()
            self.nc.save_scan(self, inp)
            #nc.close_scan()
        # while self.pstop.keep_running:
        #     try:
        #         time.sleep(1)
        #     except KeyboardInterrupt:
        #         self.pstop.terminate()
        #         break
        return acc_n, sync_n, self.interleave, read_time
    
    def save_all_scans(self):
        if self.nc is not None:
            self.nc.save_all_scans(self)

    def close_scan(self):
        self.nc.close_scan()
        self.nc = None
        
    def snap(self, inp):
                                                                                                                                     
        raw = adc5g.get_snapshot(self.roach, 'snap%i' %(inp))

        # removed hist plots from spectrometer by GN Oct 15, 2017
        # to remove X dependency on plots
        # if you separately want to plot
        # from wares.tools.snap_tools import levels_hist
        # levels_hist(raw)
        
        #if hist:
        #        self.adc_cal_tools.levels_hist(raw)

        return np.array(raw)

    def snap_file(self, inp, filename):
        raw = self.snap(inp)
        np.savetxt(filename, raw)

    def snapshot_file_all(self, roach_num=0, obsnum=None):
        basedir = os.path.join("/data_lmt/spectrometer/snapshots", "roach%d" % roach_num)
        basefile = "roach%d_%d" % (roach_num, obsnum)
        for inp in range(4):
            filename ="%s_inp%d_%s.txt" % (basefile, inp, datetime.datetime.now().strftime('%Y-%m-%d_%H%M%S'))
            fullpath = os.path.join(basedir, filename)
            self.snap_file(inp, fullpath)
            logger.info("Wrote snapshot file %s" % fullpath)
            time.sleep(0.010)
        logger.info("Done with Snapshots")

    def snapsend(self):
        sdev = []
        for inp in range(4):
            raw = self.snap(inp)
            time.sleep(0.010)
            sdev.append(raw.std())
        return sdev
        
    def snap_bad(self):

        raw = adc5g.get_snapshot(self.roach, 'snap')

        #if hist:
        #    self.adc_cal_tools.levels_hist(raw)
        
        return raw
