from .spectrometer import Spectrometer
from wares.utils.valon_synth import Synthesizer as ValonSynthesizer, SYNTH_A, SYNTH_B
import spectrometer_modes as spec_modes
import time
import threading
#import logging

#logging.basicConfig(level=logging.DEBUG,
#                    format='(%(threadName)-10s) %(message)s',
#                    )


roach_ips = {
    0: '10.0.0.97',
    1: '10.0.0.98',
    2: '10.0.0.99',
    3: '10.0.0.100'
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
            print "Save data to NC file"
            self.spec.queue.task_done()
	return
    
class SpectrometerWrapper(object):
    def __init__(self, roach_id=0, katcp_port=7147,
                 default_ogp_file='ogp_data/ogp_chans01.npz',
                 default_inl_file='ogp_data/inl_chans01.npz'):
        self.spec = Spectrometer(roach_ips[roach_id],
                                 katcp_port=katcp_port,
                                 default_ogp_file=default_ogp_file,
                                 default_inl_file=default_inl_file,
                                 gain=0xfffff, basefile='spectrometer')
        self.integration_active = False
        
    def calc_scale(self, dump_time, mode_obj):
        """
        Given dump time in seconds, calculates scale as nearest integer
        """
        sync_period = dump_time * (mode_obj.clk*1e6)/mode_obj.ADCstreams
        scale = int((sync_period + 2) * mode_obj.FFTinputs/(mode_obj.sync_LCM*mode_obj.pfb_taps*mode_obj.FFTsize))
        return scale        
        
    def config(self, mode=800, dump_time=0.05):
        valon = ValonSynthesizer('/dev/ttyUSB0')
        print "Current Frequency: %s MHz" % valon.get_frequency(SYNTH_A)
        valon.set_frequency(SYNTH_A, synth_freq[mode])
        print "Setting Frequency to: %s MHz" % valon.get_frequency(SYNTH_A)
        mode_fn = getattr(spec_modes, 'mode_%d' % mode)
        mode_obj = mode_fn()
        scale = self.calc_scale(dump_time, mode_obj)
        self.spec.sync_scale = scale
        self.spec.mode_setup(mode=mode)
        
    def integrate(self, inputs):
        #logging.debug('Starting ')
        print "Starting"
        while self.integration_active:
            #t1 = time.time()
            #acc_n = self.spec.get_acc_n()
            for inp in inputs:
                self.spec.integrate(inp, plt=False, write_nc=False)
            #while self.spec.get_acc_n() == acc_n:
            #    time.sleep(0.001)
            #while time.time() - t1 < self.spec.sync_time:
            #    time.sleep(0.001)
        print "Integration halted"
        self.spec.queue.put(None)  # to mark end of data
        
    def open(self, obs_num, source_name, obspgm):
        self.spec.basefile = "%d_%s" % (obs_num, source_name)
        self.spec.open_nc_file()

    def start(self):
        self.integration_active = True
        # needs to be a threaded integrate below
        self.integrate_thread = threading.Thread(name="integrate daemon",
                                                 target=self.integrate, args=([0,1,2,3],))
        self.integrate_thread.setDaemon(True)
        self.integrate_thread.start()
        self.consumer_thread = ConsumerWriterThread(args=(self.spec, ))
        self.consumer_thread.start()
        #self.integrate([0, 1, 2, 3])

    def stop(self):
        self.integration_active = False
        self.consumer_thread.join()
        self.integrate_thread.join()
    
    def close(self):
        self.spec.save_all_scans()
        self.spec.close_scan()


        
