import os
import glob

def most_recent_file(glob_pattern):
    return max(glob.iglob(glob_pattern), key=os.path.getctime)

def get_nc_file(obsnum, basepat='/data_lmt/spectrometer', roach_id=0,
                most_recent=True):
    basepath = os.path.join(basepat, "roach%1d"%  roach_id)
    glob_pattern = os.path.join(basepath, "roach%1d_%d_*.nc" % (roach_id, obsnum))
    if most_recent:
        return most_recent_file(glob_pattern)
    fnames = glob.glob(glob_pattern)
    if fnames:
        return fnames[0]

def get_telnc_file(obsnum, basepath='/data_lmt/ifproc',
                   most_recent=True):
    glob_pattern = os.path.join(basepath, "ifproc_*_%06d_*.nc" % obsnum)
    if most_recent:
        return most_recent_file(glob_pattern)
    fnames = glob.glob(glob_pattern)
    if fnames:
        return fnames[0]

    

