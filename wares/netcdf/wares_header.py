from lmtheader import LMTHeader
#from utils.coordinates import sixty

import numpy
from netCDF4 import num2date, date2num
import datetime
from wares.utils.coordinates import sixty
class WaresHeader(LMTHeader):

    def __init__(self, ncvariables=None, dimensions=None):
        LMTHeader.__init__(self, ncvariables=ncvariables,
                           dimensions=dimensions,
                           fromold=False)
        if self.has_key('Dcs'):
            self.calculate_attributes() # this is a IFProc file

    def calculate_attributes(self):
       """Given a conventional LMTHeader object,
        creates onemm specific header attributes"""
       self.SourceName = self.get('Source.SourceName', None)
       self.Epoch = self.get('Source.Epoch', None)
       self.Az = self.get('Source.Az', None)
       self.El = self.get('Source.El', None)
       AzReq = self.get('Sky.AzReq', None)
       ElReq = self.get('Sky.ElReq', None)
       if AzReq is not None:
           if AzReq.any():
               self.AzReq = numpy.degrees(AzReq[0])
       else:
           self.AzReq = None
       if ElReq is not None:
           if ElReq.any():
               self.ElReq = numpy.degrees(ElReq[0])
       else:
           self.ElReq = None
       self.Ra = self.get('Source.Ra', None)
       self.Dec = self.get('Source.Dec', None)
       if self.Ra is not None:
           if self.Ra.any():
               self.RA = sixty(self.Ra[0], ra=True)
       if self.Dec is not None:
           if self.Dec.any():
               self.DEC = sixty(self.Dec[0])
       self.L = self.get('Source.L', None)
       self.B = self.get('Source.B', None)
       self.CoordSys = self.get('Source.CoordSys', None)
       self.Velocity = self.get('Source.Velocity', None)
       self.VelSys = self.get('Source.VelSys', None)
       self.AzOff = self.get('Sky.AzOff', None)
       self.ElOff = self.get('Sky.ElOff', None)
       self.RaOff = self.get('Sky.RaOff', None)
       self.DecOff = self.get('Sky.DecOff', None)
       self.LOff = self.get('Sky.LOff', None)
       self.BOff = self.get('Sky.BOff', None)
       self.ObsVel = self.get('Sky.ObsVel', None)
       self.BaryVel = self.get('Sky.BaryVel', None)
       self.ParAng = self.get('Sky.ParAng', None)
       self.Operator = self.get('Telescope.Operator', None)
       self.AzTotalPoff = self.get('Telescope.AzTotalPoff', None)
       self.ElTotalPoff = self.get('Telescope.ElTotalPoff', None)
       self.AzPcor = self.get('Telescope.AzPcor', None)
       self.ElPcor = self.get('Telescope.ElPcor', None)
       self.XAct = self.get('M2.XAct', None)
       self.YAct = self.get('M2.YAct', None)
       self.ZAct = self.get('M2.ZAct', None)
       self.TipAct = self.get('M2.TipAct', None)
       self.TiltAct = self.get('M2.TiltAct', None)
       self.Wvp = self.get('Environment.Wvp', None)
       self.Temp = self.get('Environment.Temp', None)
       self.Pressure = self.get('Environment.Pressure', None)
       self.LST = self.get('TimePlace.LST', None)
       self.UTDate = self.get('TimePlace.UTDate', None)
       self.UT1 = self.get('TimePlace.UT1', None)
       self.ModRev = self.get('PointModel.ModRev', None)
       self.ObsPgm = self.get('Dcs.ObsPgm', None)
       self.Receiver = self.get('Dcs.Receiver', None)
       self.ObsNum = self.get('Dcs.ObsNum', None)
       self.SubObsNum = self.get('Dcs.SubObsNum', None)
       self.ScanNum = self.get('Dcs.ScanNum', None)
       self.ObsType = self.get('Dcs.ObsType', None)
       self.ObsMode = self.get('Dcs.ObsMode', None)
       self.CalMode = self.get('Dcs.CalMode', None)
       self.Timer = self.get('Dcs.Timer', None)
       self.Valid = self.get('ScanFile.Valid',None)
        
        
