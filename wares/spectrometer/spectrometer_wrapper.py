from .spectrometer import Spectrometer
from wares.utils.valon_synth import Synthesizer as ValonSynthesizer, SYNTH_A, SYNTH_B
from wares.logging import logger
import spectrometer_modes as spec_modes
import time
import threading
import serial.tools.list_ports
#import logging

#logging.basicConfig(level=logging.DEBUG,
#                    format='(%(threadName)-10s) %(message)s',
#                    )

logger.name = __name__

roach_ips = {
    0: '10.0.1.97',
    1: '10.0.2.98',
    2: '10.0.3.99',
    3: '10.0.4.100',
    4: '10.0.5.101',
    5: '10.0.6.102',
    6: '10.0.7.103',
    7: '10.0.8.104' 
    }

synth_freq = {
    800: 1600,
    400: 800,
    200: 800
    }

class ConsumerWriterThread(threading.Thread):
    def __init__(self, group=None, target=None, name=None,
                 args=(), kwargs=None, verbose=None):
	super(ConsumerWriterThread,self).__init__(group=group, target=target, 
			              name=name, verbose=verbose)
	self.args = args
        self.spec = args[0]
	self.kwargs = kwargs
	return

    def run(self):
	#logging.debug('running with %s and %s', self.args, self.kwargs)
        while True:
            specdata = self.spec.queue.get()
            if specdata is None:
                break
            self.spec.nc.save_single_scan(self.spec, specdata)
            #print "Save data to NC file"
            logger.debug("Save data to NC file")
            self.spec.queue.task_done()
	return
    
class SpectrometerWrapper(object):
    def __init__(self, roach_id=0, katcp_port=7147,
                 default_ogp_file='ogp_data/ogp_chans01.npz',
                 default_inl_file='ogp_data/inl_chans01.npz'):
        self.roach_id = roach_id
        self.spec = Spectrometer(roach_ips[roach_id],
                                 katcp_port=katcp_port,
                                 default_ogp_file=default_ogp_file,
                                 default_inl_file=default_inl_file,
                                 gain=0xfffff, basefile='spectrometer')
        self.integration_active = False
        self.ObsNum = 1 # default obsnum
        
    def calc_scale(self, dump_time, mode_obj):
        """
        Given dump time in seconds, calculates scale as nearest integer
        """
        sync_period = dump_time * (mode_obj.clk*1e6)/mode_obj.ADCstreams
        scale = int((sync_period + 2) * mode_obj.FFTinputs/(mode_obj.sync_LCM*mode_obj.pfb_taps*mode_obj.FFTsize))
        return scale        
        
    def config(self, mode=800, dump_time=0.05):
        #get usb port for the right valon
        valonSN = ['A502NJ6F', 'A5Z7ZF81', 'A5Z7ZC6N', 'A51G8YDP', 'A53FKXPB', 'A53FKXOP', 'A53FKXO0', 'A53FKXQ2']
        device = None
        com = serial.tools.list_ports.comports()
        for c in com:
            if not c.device.startswith("/dev/ttyUSB"): continue
            logger.info('look at valonSN %s for %s'%(c.serial_number, valonSN[self.roach_id]))
            if c.vid == 0x0403 and c.pid == 0x6001 and valonSN[self.roach_id] == c.serial_number:
                device = c.device
                break
        logger.info('valonSN[%d] = %s, device = %s'%(self.roach_id, valonSN[self.roach_id], device))
        if device == None:
            return
        valon = ValonSynthesizer(device)
        #valon = ValonSynthesizer('/dev/ttyUSB%d' % self.roach_id)
        #print "Current Frequency: %s MHz" % valon.get_frequency(SYNTH_A)
        logger.info("Current Frequency: %s MHz" % valon.get_frequency(SYNTH_A))
        valon.set_frequency(SYNTH_A, synth_freq[mode])
        #print "Setting Frequency to: %s MHz" % valon.get_frequency(SYNTH_A)
        logger.info("Setting Frequency to: %s MHz" % valon.get_frequency(SYNTH_A))
        mode_fn = getattr(spec_modes, 'mode_%d' % mode)
        mode_obj = mode_fn()
        if dump_time < 0.040:
            logger.info("Dump time %s specified. Cannot be smaller than 0.04 seconds. Resetting to 0.04 seconds" % dump_time)
            dump_time = 0.04
        scale = self.calc_scale(dump_time, mode_obj)
        self.spec.sync_scale = scale
        self.spec.mode_setup(mode=mode)
        
    def integrate(self, inputs):
        #logging.debug('Starting ')
        #print "Starting"
        logger.info("Integration Starting")
        #throw away the current sample to guarantee timing
        acc_n = self.spec.get_acc_n()
        while True:
            acc_nn = self.spec.get_acc_n()
            if acc_nn != acc_n:
                break
            time.sleep(0.0001)
        acc_n = acc_nn
        #now collect data
        while self.integration_active:
            for inp in inputs:
                self.spec.integrate(inp, write_nc=False)
            while True:
                acc_nn = self.spec.get_acc_n()
                if acc_nn != acc_n:
                    break
                time.sleep(0.0001)
            acc_n = acc_nn
        #print "Integration halted"
        logger.info("Integrration halted")
        self.spec.queue.put(None)  # to mark end of data
        
    def open(self, obs_num, subobs_num, scan_num, source_name, obspgm):
        #self.spec.basefile = "%d_%s" % (obs_num, source_name)
        self.ObsNum = obs_num
        self.spec.open_nc_file(self.roach_id, obs_num, subobs_num, scan_num,
                               source_name, obspgm)

    def start(self):
        self.integration_active = True
        # needs to be a threaded integrate below
        self.integrate_thread = threading.Thread(name="integrate daemon",
                                                 target=self.integrate, args=([0,1,2,3],))
        self.integrate_thread.setDaemon(True)
        self.integrate_thread.start()
        self.consumer_thread = ConsumerWriterThread(args=(self.spec, ))
        self.consumer_thread.start()
        #print "Started integrate thread and consumer writer thread"
        logger.info("Started integrate thread and consumer writer thread")
        #self.integrate([0, 1, 2, 3])

    def stop(self):
        self.integration_active = False
        if hasattr(self, 'consumer_thread'):
            self.consumer_thread.join()
        if hasattr(self, 'integrate_thread'):
            self.integrate_thread.join()

    def snapshot(self):
        self.spec.snapshot_file_all(roach_num=self.roach_id, obsnum=self.ObsNum)

    def snapsend(self):
        return self.spec.snapsend()
    
    def close(self):
        #self.spec.save_all_scans()
        if self.spec.nc is not None:
            self.spec.close_scan()
        else:
            logger.info("No NC file to close")

        
