from matplotlib import pyplot as plt
from matplotlib import mlab
import numpy as np

def levels_hist(raw):
    bins = np.arange(-128.5, 128.5, 1)
	
    th = 32
    lim1 = -th-0.5
    lim2 = -0.5
    lim3 = th-0.5
    
    ideal_gauss = mlab.normpdf(bins, 0, th)

    plt.subplot(111)
    plt.plot((lim1,lim1), (0,1), 'k--')
    plt.plot((lim2,lim2), (0,1), 'k--')
    plt.plot((lim3,lim3), (0,1), 'k--')
    plt.plot(bins, ideal_gauss, 'gray', linewidth=1)
    
    plt.hist(raw, bins, normed=1, facecolor='blue', 
             alpha=0.9, histtype='stepfilled')
    
    plt.xlim(-129, 128)
    plt.ylim(0, 0.06)
    plt.xlabel('ADC Value')
    plt.ylabel('Normalized Count')
    plt.title('zdok0 levels')
    plt.grid()
    
    plt.show()
