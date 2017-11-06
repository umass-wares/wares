import os
import glob

def get_nc_file(obsnum, basepat='/data_lmt/spectrometer', roach_id=0):
    basepath = os.path.join(basepat, "roach%1d"%  roach_id)
    fnames = glob.glob(os.path.join(basepath, "roach%1d_%d_*.nc" % (roach_id, obsnum)))
    if fnames:
        return fnames[0]

def get_telnc_file(obsnum, basepath='/data_lmt/ifproc'):
    fnames = glob.glob(os.path.join(basepath, "ifproc_*_%d_*.nc" % obsnum))
    if fnames:
        return fnames[0]

    

