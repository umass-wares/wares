import numpy

class SpectrometerIntegration(object):

    def __init__(self, inp, numchannels, acc_n,
                 sync_n, read_time, data):
        self.inp = inp
        self.numchannels = numchannels
        self.data = data
        self.acc_n = acc_n
        self.sync_n = sync_n
        self.read_time = read_time
