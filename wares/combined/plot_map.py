import numpy
from matplotlib import pyplot as plt
from matplotlib import cm
def nanmean(array):
    """Returns the mean of an array after ignoring the
    nan numbers"""
    return array[numpy.isfinite(array)].mean()

def plot_map(comb, 
             pixel=2,
             average=False,
             limits = None,
             stepsize = 15.0,
             nlevels = 10,
             cmap = cm.spectral,
             subtract=False,
             clear_plot=True):
    if clear_plot:
        plt.clf()
    if limits is None:
        limits = [comb.xi[pixel].min(), comb.xi[pixel].max(), comb.yi[pixel].min(), comb.yi[pixel].max()]
    zi = comb.BeamMap[pixel]
    if subtract:
        tmparr = zi.flatten()
        baseline =numpy.median(tmparr[numpy.isfinite(tmparr)])
        zi = zi - baseline
    cs = plt.contour(comb.xi[pixel], comb.yi[pixel], zi, nlevels, linewidths=0.5, colors='k')
    cs = plt.contourf(comb.xi[pixel], comb.yi[pixel], zi, nlevels, cmap=cmap)
    plt.colorbar()
    X, Y = numpy.meshgrid(comb.xi[pixel], comb.yi[pixel])
    def format_coord(x, y):
        ind = numpy.logical_and(numpy.abs(X-x)<stepsize,
                                numpy.abs(Y-y)<stepsize)
        zzz = nanmean(zi[ind])
        return 'x=%1.4f, y=%1.4f, z=%1.4f' % (x, y, zzz)
    ax = plt.gca()
    ax.format_coord = format_coord
    plt.xlim(limits[0], limits[1])
    plt.ylim(limits[2], limits[3])
    plt.title('%d: Source %s' % (comb.obsnum, comb.telnc.hdu.header.get('Source.SourceName')))
    plt.draw()
