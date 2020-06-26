import bob
from matplotlib import pyplot

def plot_det_and_save_fig_as(negatives, positives, filename, save=True):
    npoints = 100
    fig = pyplot.figure(figsize=(10,5))
    bob.measure.plot.det(negatives, positives, npoints, color=(0,0,0), linestyle='-', label='test') 
    bob.measure.plot.det_axis([1, 99.9, 1, 99.9]) 
    pyplot.xlabel('FAR (%)') 
    pyplot.ylabel('FRR (%)') 
    pyplot.grid(True)
    pyplot.show()
    if save:
        fig.savefig(filename)
