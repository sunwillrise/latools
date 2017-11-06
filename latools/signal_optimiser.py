"""
Functions for automatic selection optimisation.
"""
import warnings
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import bayes_mvs
from scipy.stats.kde import gaussian_kde
from .helpers import Bunch, rolling_window, nominal_values
from .plots import tplot

def calc_windows(fn, s, min_points):
    """
    Apply fn to all contiguous regions in s that have at least min_points.
    """
    max_points = np.sum(~np.isnan(s))
    n_points = max_points - min_points

    out = np.full((n_points, s.size), np.nan)

    # skip nans, for speed
    ind = ~np.isnan(s)
    s = s[ind]

    for i, w in enumerate(range(min_points, s.size)):
        r = rolling_window(s, w, pad=np.nan)
        out[i, ind] = np.apply_along_axis(fn, 1, r)

    return out

def calc_window_mean_std(s, min_points):
    """
    Apply fn to all contiguous regions in s that have at least min_points.
    """
    max_points = np.sum(~np.isnan(s))
    n_points = max_points - min_points

    mean = np.full((n_points, s.size), np.nan)
    std = np.full((n_points, s.size), np.nan)

    # skip nans, for speed
    ind = ~np.isnan(s)
    s = s[ind]

    for i, w in enumerate(range(min_points, s.size)):
        r = rolling_window(s, w, pad=np.nan)
        mean[i, ind] = np.apply_along_axis(np.nanmean, 1, r)
        std[i, ind] = np.apply_along_axis(np.nanstd, 1, r)

    return mean, std

def scale(s):
    """
    Remove the mean, and divide by the standard deviation.
    """
    return (s - np.nanmean(s)) / np.nanstd(s)

def bayes_scale(s):
    """
    Remove mean and divide by standard deviation, using bayes_kvm statistics.
    """
    if sum(~np.isnan(s)) > 1:
        bm, bv, bs = bayes_mvs(s[~np.isnan(s)])
        return (s - bm.statistic) / bs.statistic
    else:
        return np.full(s.shape, np.nan)

def signal_optimiser(d, analytes, min_points=5,
                     threshold_mode='kde_first_max',
                     weights=None):
    """
    Optimise data selection based on specified analytes.

    Identifies the longest possible contiguous data region in
    the signal where the relative standard deviation (std) and 
    concentration of all analytes is minimised.

    Optimisation is performed via a grid search of all possible
    contiguous data regions. For each region, the mean std and
    mean scaled analyte concentration ('amplitude') are calculated. 
    
    The size and position of the optimal data region are identified 
    using threshold std and amplitude values. Thresholds are derived
    from all calculated stds and amplitudes using the method specified
    by `threshold_mode`. For example, using the 'kde_max' method, a
    probability density function (PDF) is calculated for std and
    amplitude values, and the threshold is set as the maximum of the
    PDF. These thresholds are then used to identify the size and position
    of the longest contiguous region where the std is below the threshold, 
    and the amplitude is either below the threshold.

    All possible regions of the data that have at least
    `min_points` are considered.

    For a graphical demonstration of the action of signal_optimiser, 
    use `optimisation_plot`. 

    Parameters
    ----------
    d : latools.D object
        An latools data object.
    analytes : str or array-like
        Which analytes to consider.
    min_points : int
        The minimum number of contiguous points to
        consider.
    threshold_mode : str
        The method used to calculate the optimisation
        thresholds. Can be 'mean', 'median', 'kde_max'
        or 'bayes_mvs', or a custom function. If a
        function, must take a 1D array, and return a
        single, real number.
    weights : array-like of length len(analytes)
        An array of numbers specifying the importance of
        each analyte considered. Larger number makes the
        analyte have a greater effect on the optimisation.
        Default is None.

    Returns
    -------
    optimisation result : dict
    """    
    if isinstance(analytes, str):
        analytes = [analytes]

    # calculate statistics
    stds = []
    means = []
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for a in analytes:
            m, s = calc_window_mean_std(nominal_values(d.focus[a]), min_points)
            # stds.append(calc_windows(np.nanstd, nominal_values(d.focus[a]), min_points))
            # means.append(calc_windows(np.nanmean, nominal_values(d.focus[a]), min_points))
            means.append(m)
            stds.append(s)
        # compile stats
    stds = np.array(stds)
    means = np.array(means)

    # sstds = stds / means

    # scale means and standard deviations
    smeans = np.apply_along_axis(bayes_scale, 1, means)
    sstds = np.apply_along_axis(bayes_scale, 1, stds)

    # apply weights
    if weights is not None:
        sstds *= np.reshape(weights, (len(analytes), 1, 1))
        smeans *= np.reshape(weights, (len(analytes), 1, 1))

    # average of all means and standard deviations
    msstds = sstds.mean(0)
    msmeans = smeans.mean(0)

    # define thresholds
    valid = ['median', 'mean', 'kde_max', 'kde_first_max', 'bayes_mvs']
    if threshold_mode == 'median':
        # median - OK, but best?
        std_threshold = np.nanmedian(msstds)
        mean_threshold = np.nanmedian(msmeans)
    elif threshold_mode == 'mean':
        # mean
        std_threshold = np.nanmean(msstds)
        mean_threshold = np.nanmean(msmeans)
    elif threshold_mode == 'kde_max':
        # maximum of gaussian kernel density estimator
        mkd = gaussian_kde(msmeans[~np.isnan(msmeans)])
        xm = np.linspace(*np.percentile(msmeans.flatten()[~np.isnan(msmeans.flatten())], (1, 99)), 100)
        mdf = mkd.pdf(xm)
        mean_threshold = xm[np.argmax(mdf)]

        rkd = gaussian_kde(msstds[~np.isnan(msstds)])
        xr = np.linspace(*np.percentile(msstds.flatten()[~np.isnan(msstds.flatten())], (1, 99)), 100)
        rdf = rkd.pdf(xr)
        std_threshold = xr[np.argmax(rdf)]
    elif threshold_mode == 'kde_first_max':
        # first local maximum of gaussian kernel density estimator
        mkd = gaussian_kde(msmeans[~np.isnan(msmeans)])
        xm = np.linspace(*np.percentile(msmeans.flatten()[~np.isnan(msmeans.flatten())], (1, 99)), 100)
        mdf = mkd.pdf(xm)
        inds = np.argwhere(np.r_[False, mdf[1:] > mdf[:-1]] & 
                           np.r_[mdf[:-1] > mdf[1:], False] & 
                           (mdf > 0.25 * mdf.max()))
        mean_threshold = xm[np.min(inds)]

        rkd = gaussian_kde(msstds[~np.isnan(msstds)])
        xr = np.linspace(*np.percentile(msstds.flatten()[~np.isnan(msstds.flatten())], (1, 99)), 100)
        rdf = rkd.pdf(xr)
        inds = np.argwhere(np.r_[False, rdf[1:] > rdf[:-1]] & 
                           np.r_[rdf[:-1] > rdf[1:], False] & 
                           (rdf > 0.25 * rdf.max()))
        std_threshold = xr[np.min(inds)]
    elif threshold_mode == 'bayes_mvs':
        # bayesian mvs.
        bm, _, bs = bayes_mvs(msstds[~np.isnan(msstds)])
        std_threshold = bm.statistic

        bm, _, bs = bayes_mvs(msmeans[~np.isnan(msmeans)])
        mean_threshold = bm.statistic
    elif callable(threshold_mode):
        std_threshold = threshold_mode(msstds[~np.isnan(msstds)].flatten())
        mean_threshold = threshold_mode(msmeans[~np.isnan(msmeans)].flatten())
    else:
        try:
            mean_threshold, std_threshold = threshold_mode
        except:
            raise ValueError('\nthreshold_mode must be one of:\n   ' + ', '.join(valid) + ',\na custom function, or a \n(mean_threshold, std_threshold) tuple.')

    # identify max number of points within thresholds
    centres, npoints = np.meshgrid(np.arange(msmeans.shape[1]),
                                   np.arange(min_points, min_points + msmeans.shape[0]))
    rind = (msstds < std_threshold - 0.01)
    mind = (msmeans < mean_threshold - 0.01)

    ind = rind & mind
    opt_n_points = npoints[ind].max()
    # plus/minus one point to allow some freedom to shift selection window.
    cind = ind & ((npoints <= opt_n_points + 1) | (npoints >= opt_n_points - 1))
    opt_centre = centres[cind].min()
    # opt_centre = opt_centres[msmeans[cind] == np.nanmin(msmeans[cind])][0]

    if opt_n_points % 2 == 0:
        lims = (opt_centre - opt_n_points // 2,
                opt_centre + opt_n_points // 2 + 1)
    else:
        lims = (opt_centre - opt_n_points // 2 - 1,
                opt_centre + opt_n_points // 2 - 1)

    filt = np.zeros(d.Time.shape, dtype=bool)
    filt[lims[0]:lims[1]] = True

    return Bunch({'means': msmeans,
                  'stds': msstds,
                  'mean_threshold': mean_threshold,
                  'std_threshold': std_threshold,
                  'lims': lims,
                  'filt': filt,
                  'threshold_mode': threshold_mode,
                  'min_points': min_points,
                  'analytes': analytes,
                  'opt_centre': opt_centre,
                  'opt_n_points': opt_n_points,
                  'weights': weights})


def optimisation_plot(d, overlay_alpha=0.5, **kwargs):
    """
    Plot the result of signal_optimise.

    `signal_optimiser` must be run first, and the output
    stored in the `opt` attribute of the latools.D object.

    Parameters
    ----------
    d : latools.D object
        A latools data object.
    overlay_alpha : float
        The opacity of the threshold overlays. Between 0 and 1.
    **kwargs
        Passed to `tplot`
    """
    if not hasattr(d, 'opt'):
        raise ValueError('Please run `signal_optimiser` before trying to plot its results.')

    # unpack variables
    means = d.opt['means']
    stds = d.opt['stds']
    min_points = d.opt['min_points']
    mean_threshold = d.opt['mean_threshold']
    std_threshold = d.opt['std_threshold']
    opt_centre = d.opt['opt_centre']
    opt_n_points = d.opt['opt_n_points']
    
    centres, npoints = np.meshgrid(np.arange(means.shape[1]), np.arange(min_points, min_points + means.shape[0]))
    rind = (stds < std_threshold)
    mind = (means < mean_threshold)

    cmr = plt.cm.Blues
    cmr.set_bad((0,0,0,0.3))

    cmm = plt.cm.Reds
    cmm.set_bad((0,0,0,0.3))
    
    # create figure
    fig = plt.figure(figsize=[10,7])

    ma = fig.add_subplot(3, 2, 1)
    ra = fig.add_subplot(3, 2, 2)

    mm = ma.imshow(means, origin='bottomleft', cmap=cmm,
                   extent=(centres.min(), centres.max(), npoints.min(), npoints.max()))

    ma.set_ylabel('N points')
    ma.set_xlabel('Center')
    fig.colorbar(mm, ax=ma, label='Amplitude')

    mr = ra.imshow(stds, origin='bottomleft', cmap=cmr,
                   extent=(centres.min(), centres.max(), npoints.min(), npoints.max()))

    # ra.set_ylabel('N points')
    ra.set_xlabel('Center')
    fig.colorbar(mr, ax=ra, label='std')

    # view limits
    ra.imshow(~rind, origin='bottomleft', cmap=plt.cm.Greys, alpha=overlay_alpha,
              extent=(centres.min(), centres.max(), npoints.min(), npoints.max()))
    ma.imshow(~mind, origin='bottomleft', cmap=plt.cm.Greys, alpha=overlay_alpha,
              extent=(centres.min(), centres.max(), npoints.min(), npoints.max()))

    ma.scatter(opt_centre, opt_n_points, c=(1,1,1,0.7), edgecolor='k',marker='o')
    ra.scatter(opt_centre, opt_n_points, c=(1,1,1,0.7), edgecolor='k', marker='o')

    # draw histograms
    mah = fig.add_subplot(3, 2, 3)
    rah = fig.add_subplot(3, 2, 4)

    mah.set_xlim(*np.percentile(means.flatten()[~np.isnan(means.flatten())], (0, 99)))
    mbin = np.linspace(*mah.get_xlim(), 50)
    mah.hist(means.flatten()[~np.isnan(means.flatten())], mbin)
    mah.axvspan(mean_threshold, mah.get_xlim()[1], color=(0,0,0,overlay_alpha))

    mah.axvline(mean_threshold, c='r')
    mah.set_xlabel('Scaled Mean Analyte Conc')
    mah.set_ylabel('N')

    rah.set_xlim(np.percentile(stds.flatten()[~np.isnan(stds.flatten())], (0, 99)))
    rbin = np.linspace(*rah.get_xlim(), 50)
    rah.hist(stds.flatten()[~np.isnan(stds.flatten())], rbin)
    rah.axvspan(std_threshold, rah.get_xlim()[1], color=(0,0,0,0.4))
    rah.axvline(std_threshold, c='r')
    rah.set_xlabel('std')
    
    tax = fig.add_subplot(3,1,3)
    tplot(d, d.opt.analytes, ax=tax, **kwargs)
    tax.axvspan(*d.Time[[d.opt.lims[0], d.opt.lims[1]]], alpha=0.2)
    
    fig.tight_layout()

    return fig, (ma, ra, mah, rah, tax)
