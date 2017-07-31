"""
A set of routines to analyze the spectra from the spectrometer
for Allan deviation stability
"""
from wares.netcdf.wares_netcdf import WaresNetCDFFile

import numpy
import math

def load_allan_scans(filename, startscan=0, numscans=5000,
                     inputpix=0):
    nc = WaresNetCDFFile(filename)
    ind = nc.hdu.data.Inputs == inputpix
    data = nc.hdu.data.Data[ind, :]
    nscans, nchans = data.shape
    if nscans < numscans:
        print "Number of scans in file less than numscans requested"
        numscans = nscans
    return data[startscan:startscan+numscans]

def find_sample_interval(filename):
    nc = WaresNetCDFFile(filename)
    return numpy.diff(nc.hdu.data.time).mean()

def allan_analysis(filename, startscan=0, numscans=5000,
                   inputpix=0, max_allan=None,
                   lochan=500, hichan=1000,
                   indices=None,
                   sampleint=None,
                   freqres=390.625e3,
                   return_spectra=True):
    rmsvals = load_allan_scans(filename, startscan=startscan,
                               numscans=numscans, inputpix=inputpix)
    nscans, nchans = rmsvals.shape
    Nout = numscans - startscan + 1
    if max_allan is not None:
        maxk = max_allan
    else:
        maxk = Nout/4
    print maxk
    alanvar = []
    for k in range(1, maxk+1):
        M = Nout/k
        print M
        for n in range(M):
            tmpR = rmsvals[(n*k):(n+1)*k, :].sum(axis=0)/k
            if n == 0:
                R = tmpR
            else:
                R = numpy.column_stack((R, tmpR))
        print R.shape
        sigmak = 0.0
        avgspec = numpy.zeros((nchans,), dtype='float')
        for n in range(M-1):
            spec = (R[:, n+1] - R[:, n])/R[:, n+1]
            avgspec += spec
            if type(indices) == numpy.ndarray and indices.any():
                #print "indices"
                sigmak += spec[indices].var()
            else:
                sigmak += spec[lochan:hichan].var()
        avgspec = avgspec*math.sqrt(k) #*k/math.sqrt(M-1.)  #/(k*(M-1))
        if k == 1:
            avgspectra = avgspec
        else:
            avgspectra = numpy.column_stack((avgspectra, avgspec))
        sigmak = sigmak/(M-1)
        alanvar.append(math.sqrt(sigmak))
            
    alanvar = numpy.array(alanvar)
    if sampleint is None:
        sampleint = find_sample_interval(filename)
    time = sampleint + numpy.arange(maxk)*sampleint
    theory = math.sqrt(2)/(math.sqrt(freqres)*numpy.sqrt(time))
    if return_spectra:
        return (time, theory, alanvar, rmsvals, avgspectra)
    else:
        return (time, theory, alanvar, rmsvals)    
