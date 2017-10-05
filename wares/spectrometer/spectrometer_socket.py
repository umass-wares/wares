#!/usr/bin/python
"""A class for receiving WARES spectrometer commands from
TCP/IP sockets"""


#import socket
#import struct
#import sys
#import traceback
import time
#import syslog

import SocketServer
#LOG_SYSLOG=0
#LOG_STDOUT=1

#msgtype = {syslog.LOG_INFO: 'LOG_INFO',
#           syslog.LOG_ERR: 'LOG_ERR'
#}

class SpecTCPHandler(SocketServer.BaseRequestHandler):
    '''Base class for WARES tcpip socket communications'''

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(1024).strip()
        print "{} wrote:".format(self.client_address[0])
        print self.data
        # just send back the same data, but upper-cased
        self.request.sendall(self.data.upper())

    
    # debug = 0
    # status_bytes = []
    # status_dict = {}

    # def __init__(self, HOST=None, PORT=None, log=LOG_SYSLOG):
    #     self.log = log
    #     if self.log == LOG_SYSLOG:
    #         syslog.openlog('SpectrometerSockServer')
    #     try:
    #         self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         if HOST:
    #             #self.s.connect((HOST, PORT))
    #             self.sock.bind((HOST, PORT))
    #         else:
    #             self.sock.bind((socket.gethostname(),PORT))
    #         self.conn = None
    #         self.addr = None
    #         self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #     except:
    #         self.printlog(syslog.LOG_ERR, str(self.formatExceptionInfo()))
            
    # def formatExceptionInfo(self, maxTBlevel=5):
    #     """copied from Linux Journal article 5821"""
    #     cla, exc, trbk = sys.exc_info()
    #     excName = cla.__name__
    #     try:
    #         excArgs = exc.__dict__["args"]
    #     except KeyError:
    #         excArgs = "<no args>"
    #     excTb = traceback.format_tb(trbk, maxTBlevel)
    #     return (excName, excArgs, excTb)

    # def printlog(self, *arguments):
    #     if len(arguments) == 1:
    #         type=syslog.LOG_INFO
    #         msg = arguments[0]
    #     else:
    #         type=arguments[0]
    #         msg=arguments[1]
    #     if self.log == LOG_STDOUT:
    #         print msgtype[type], msg
    #     else:
    #         syslog.syslog(type, msg)

    # def listen(self, numconnections=10):
    #     self.sock.listen(numconnections)

    # def accept(self):
    #     self.conn, self.addr = self.sock.accept()
    #     self.printlog("Connected by %s" % repr(self.addr))
    #     return True

    # def recv(self, maxlen=1024):
    #     if self.conn:
    #         try:
    #             data = self.conn.recv(maxlen)
    #             return data
    #         except:
    #             self.printlog(syslog.LOG_ERR, "No data")
    #             self.conn=None
    #             return None
    #     else:
    #         self.printlog(syslog.LOG_ERR,"No connection")
    
    # def process_spectrometer_command(self):
    #     data = self.recv(1024)
    #     if not data:
    #         return False
    #     else:
    #         msg = data.split()
    #         print data
    #         return True

    # def conn_close(self):
    #     if self.conn:
    #         self.conn.close()

    # def receive_with_size(self, msglen):
    #     msg = ''
    #     while len(msg) < msglen:
    #         chunk = self.sock.recv(msglen-len(msg))
    #         if chunk == '':
    #             raise RuntimeError, "socket connection broken"
    #         msg = msg + chunk
    #     return msg


    # def close(self):
    #     self.sock.close()
          

                         
