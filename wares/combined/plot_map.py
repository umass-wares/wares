import numpy
from matplotlib import pyplot as plt
from matplotlib import cm
def nanmean(array):
    """Returns the mean of an array after ignoring the
    nan numbers"""
    return array[numpy.isfinite(array)].mean()

def plot_map(self, comb, 
             pixel=2,
             average=False,
             limits = None,
             stepsize = 15.0,
             nlevels = 10,
             cmap = cm.spectral,
             subtract=False, 
):
        if limits is None:
            limits = [comb.xi.min(), comb.xi.max(), comb.yi.min(), comb.yi.max()]
        zi = comb.BeamMap[pixel]
        if subtract:
            tmparr = zi.flatten()
            baseline =numpy.median(tmparr[numpy.isfinite(tmparr)])
            zi = zi - baseline
        cs = plt.contour(comb.xi, comb.yi, zi, nlevels, linewidths=0.5, colors='k')
        cs = plt.contourf(comb.xi, comb.yi, zi, nlevels, cmap=cmap)
        plt.colorbar()
        X, Y = numpy.meshgrid(comb.xi, comb.yi)
        def format_coord(x, y):
            ind = numpy.logical_and(numpy.abs(X-x)<stepsize,
                                    numpy.abs(Y-y)<stepsize)
            zzz = nanmean(zi[ind])
            return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, zzz)
        plt.xlim(limits[0], limits[1])
        plt.ylim(limits[2], limits[3])
