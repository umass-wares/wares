from wares.spectrometer.spectrometer_wrapper import SpectrometerWrapper
import time

specw = SpectrometerWrapper(default_ogp_file='/home/oper/wares/ogp_data/ogp_chans01.npz',
                            default_inl_file='/home/oper/wares/ogp_data/inl_chans01.npz')

specw.config(mode=200, dump_time=0.070)
specw.open(10022, 'orionkl', 'otfmap')
specw.spec.start_queue(1000)
specw.start()
time.sleep(20)
specw.stop()
#specw.close()
#print "Waiting for a while for consumer to catch up"
#while not specw.spec.queue.empty():
#   time.sleep(1)
specw.close()
print specw.spec.numscans
