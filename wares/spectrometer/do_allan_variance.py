import telnetlib
import time

def do_allan_variance(host, port, start_obs_num=10000,
                      numobs=1000, int_time=1.0,
                      dump_time=0.05, spec_mode=2,
                      sleep_time=0.0):
    """
    Do an allan variance by sending commands to
    running socket server
    spec_mode: 2 - 800; 1 - 400; 0 - 200
    """
    telnet = telnetlib.Telnet(host, port=port)
    # config
    telnet.write('config %d %s\n' % (spec_mode, dump_time))
    time.sleep(2.0)
    print telnet.read_some()
    for obsnum in range(start_obs_num, start_obs_num+numobs):
        telnet.write("open %d 0 0 allantest on\n" %  obsnum)
        print telnet.read_some()
        telnet.write("start\n")
        print telnet.read_some()
        time.sleep(int_time)
        telnet.write("stop\n")
        print telnet.read_some()
        telnet.write("close\n")
        print telnet.read_some()
        time.sleep(sleep_time)
        print "Done with Obsnum: %d" % obsnum

        
    
