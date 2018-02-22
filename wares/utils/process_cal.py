from .file_utils import get_telnc_file, get_nc_file
from wares.netcdf.wares_netcdf import WaresNetCDFFile

def do_Tsys_cal(obsnum, roach_id=0):
    telnc = WaresNetCDFFile(get_telnc_file(obsnum))
    hotind = telnc.hdu.data.BufPos == 3
    skyind = telnc.hdu.data.BufPos == 2
    hottime = telnc.hdu.data.TelTime[hotind]
    skytime = telnc.hdu.data.TelTime[skyind]

    nc = WaresNetCDFFile(get_nc_file(obsbum, roach_id=roach_id))
    spechotind = numpy.logical_and(nc.hdu.data.time > hottime[0],
                                   nc.hdu.data.time < hottime[-1])
    speccoldind = numpy.logical_and(nc.hdu.data.time > coldtime[0],
                                    nc.hdu.data.time < coldtime[-1])
    hots = numpy.zeros((4, nc.hdu.data.Data.shape[1]))
    colds = numpy.zeros((4, nc.hdu.data.Data.shape[1]))
    yfac = numpy.zeros((4, nc.hdu.data.Data.shape[1]))
    for inp in range(4):
        ind = nc.hdu.data.Inputs == inp
        indexh = numpy.logical_and(spechotind, ind)
        indexc = numpy.logical_and(speccoldind, ind)
        hotspec = nc.hdu.data.Data[indexh, :].mean(axis=0)
        coldspec = nc.hdu.data.Data[indexc, :][5:, :].mean(axis=0)
        hots[inp, :] = hotspec
        colds[inp, :] = coldspec
        yfac[inp, :] = hotspec/coldspec
    return hots, colds
