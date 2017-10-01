import sys
import signal

class ProcessStopper(object):
    def __init__(self):
        self.process_list = []
        self.keep_running = True
        signal.signal(signal.SIGTERM, self.hup)

    def add_process(self, process):
        self.process_list.append(process)

    def hup(self, signum, frame):
        self.stop()

    def stop(self):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        self.keep_running=False
        print "Gracefully stopping processes"
        for p in self.process_list:
            os.kill(p.pid, signal.SIGTERM)
            p.join()
        print "Processes gracefully stopped"

    def terminate(self):
        signal.signal(signal.SIGTERM, signal.SIG_DFL)
        self.keep_running=False
        for p in self.process_list:
            p.terminate()
            p.join()
