#!/usr/bin/python
"""A class for receiving WARES spectrometer commands from
TCP/IP sockets"""


import socket
#import struct
import sys
import traceback
import time
import logging

#import syslog

import SocketServer
from .spectrometer_wrapper import SpectrometerWrapper
# LOG_SYSLOG=0
# LOG_STDOUT=1

# msgtype = {syslog.LOG_INFO: 'LOG_INFO',
#            syslog.LOG_ERR: 'LOG_ERR'
# }
# logging.basicConfig(level=logging.DEBUG,
#                    format='%(name)s: %(message)s',
#                    )

class SpecTCPHandler(SocketServer.BaseRequestHandler):
    '''Base class for WARES tcpip socket communications.
    Do not use this use the SpectrometerSocketServer class instead
    '''
    def __init__(self, request, client_address, server):
        #self.logger = logging.getLogger('SpecRequestHandler')
        #self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return

    def setup(self):
        #self.logger.debug('setup')
        self.specw = SpectrometerWrapper(default_ogp_file='/home/oper/wares/ogp_data/ogp_chans01.npz',
                                         default_inl_file='/home/oper/wares/ogp_data/inl_chans01.npz')
        return SocketServer.BaseRequestHandler.setup(self)
    
    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())
        msg = self.data.split()
        if not msg[0] in ('open', 'config', 'start', 'stop',  'close'):
            print "Request has to be one of 'open', 'config', 'start', 'stop',  'close'"
        if msg[0] == 'open':
            self.open(msg[1], msg[2], msg[3])
        elif msg[0] == 'config':
            self.config(msg[1], msg[2])
        elif msg[0] == 'start':
            self.start()
        elif msg[0] == 'stop':
            self.stop()
        elif msg[0] == 'close':
            self.close()
            
    def config(self, mode, dump_time):
        self.specw.config(mode=int(mode), dump_time=float(dump_time))
        self.specw.spec.start_queue(1000)
        
    def open(self, obs_num, source_name, obspgm):
        self.specw.open(int(obs_num), source_name, obspgm)
        
    def start(self):
        self.specw.start()

    def stop(self):
        self.specw.stop()

    def close(self):
        self.specw.close()


class SpectrometerSocketServer():
    debug = 0
    status_bytes = []
    status_dict = {}

    def __init__(self, HOST=None, PORT=None, roach_id=0,
                 katcp_port=7147):
        #self.log = log
        #if self.log == LOG_SYSLOG:
        #    syslog.openlog('SpectrometerSockServer')
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if HOST:
                #self.s.connect((HOST, PORT))
                self.sock.bind((HOST, PORT))
            else:
                self.sock.bind((socket.gethostname(),PORT))
            self.conn = None
            self.addr = None
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.specw = SpectrometerWrapper(roach_id=roach_id,
                                             katcp_port=katcp_port,
                                             default_ogp_file='/home/oper/wares/ogp_data/ogp_chans01.npz',
                                             default_inl_file='/home/oper/wares/ogp_data/inl_chans01.npz')            
        except:
            self.printlog(str(self.formatExceptionInfo()))
            
    def formatExceptionInfo(self, maxTBlevel=5):
        """copied from Linux Journal article 5821"""
        cla, exc, trbk = sys.exc_info()
        excName = cla.__name__
        try:
            excArgs = exc.__dict__["args"]
        except KeyError:
            excArgs = "<no args>"
        excTb = traceback.format_tb(trbk, maxTBlevel)
        return (excName, excArgs, excTb)

    def printlog(self, *arguments):
        # if len(arguments) == 1:
        #     type=syslog.LOG_INFO
        #     msg = arguments[0]
        # else:
        #     type=arguments[0]
        #     msg=arguments[1]
        # if self.log == LOG_STDOUT:
        #     print msgtype[type], msg
        # else:
        #     syslog.syslog(type, msg)
        print arguments

    def listen(self, numconnections=10):
        self.sock.listen(numconnections)

    def accept(self):
        self.conn, self.addr = self.sock.accept()
        self.printlog("Connected by %s" % repr(self.addr))
        return True

    def recv(self, maxlen=1024):
        if self.conn:
            try:
                data = self.conn.recv(maxlen)
                return data
            except:
                self.printlog("No data")
                self.conn=None
                return None
        else:
            self.printlog("No connection")
    
    def process_spectrometer_command(self):
        self.data = self.recv(1024)
        if not self.data:
            return False
        else:
            msg = self.data.strip().split()
            if not msg[0] in ('open', 'config', 'start', 'stop',  'close'):
                print "Request has to be one of 'open', 'config', 'start', 'stop',  'close'"
            if msg[0] == 'open':
                self.open(msg[1], msg[2], msg[3])
            elif msg[0] == 'config':
                self.config(msg[1], msg[2])
            elif msg[0] == 'start':
                self.start()
            elif msg[0] == 'stop':
                self.stop()
            elif msg[0] == 'close':
                self.spec_close()
            print self.data
            self.send("%s DONE\n" % self.data.strip())
            return True

    def config(self, mode, dump_time):
        self.specw.config(mode=int(mode), dump_time=float(dump_time))
        self.specw.spec.start_queue(1000)
        
        
    def open(self, obs_num, source_name, obspgm):
        self.specw.open(int(obs_num), source_name, obspgm)
        
    def start(self):
        self.specw.start()

    def stop(self):
        self.specw.stop()

    def spec_close(self):
        self.specw.close()
        
    def conn_close(self):
        if self.conn:
            self.conn.close()

    def send(self, msg):
        if self.conn:
            self.conn.send(msg)

    def receive_with_size(self, msglen):
        msg = ''
        while len(msg) < msglen:
            chunk = self.sock.recv(msglen-len(msg))
            if chunk == '':
                raise RuntimeError, "socket connection broken"
            msg = msg + chunk
        return msg


    def close(self):
        self.sock.close()
          

                         
