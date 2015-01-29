#!/usr/bin/env python
import numpy as np
from matplotlib import animation

import triangle


def anim_to_html(anim):
    """
    Function to help with inline animations in ipython notebooks:

    >>> import prism
    >>> from matplotlib import animation
    >>> from IPython.display import HTML

    >>> animation.Animation._repr_html_ = prism.anim_to_html

    This first appeared as a blog post on Pythonic Perambulations:
    https://jakevdp.github.io/blog/2013/05/12/embedding-matplotlib-animations/
    """
    from tempfile import NamedTemporaryFile

    VIDEO_TAG = """<video controls>
     <source src="data:video/x-m4v;base64,{0}" type="video/mp4">
     Your browser does not support the video tag.
    </video>"""

    if not hasattr(anim, '_encoded_video'):
        with NamedTemporaryFile(suffix='.mp4') as f:
            anim.save(f.name, fps=30, extra_args=['-vcodec', 'libx264'])
            video = open(f.name, "rb").read()
        anim._encoded_video = video.encode("base64")

    return VIDEO_TAG.format(anim._encoded_video)


def corner(data_cube, labels=None, truths=None,
           samps_per_frame=10, fps=30,
           rough_length=10.0, outname='corner.mp4'):
    """
    Animate a triangle corner plot.

    :param data_cube:
    A ``T x N x dim`` array, containing ``T`` timesteps of ``N`` evolving
    samples of a ``dim`` dimensional distribution.

    :param labels: (optional)
    A ``dim``-long list of parameter labels.

    :param truths: (optional)
    A ``dim``-long list of true parameters.

    :param samps_per_frame: (optional)
    A rough number of timesteps per frame.

    :param fps: (optional)
    The frame rate for the animation.

    :param rough_length: (optional)
    A rough request for the duration (in seconds) of the animation.

    : param outname: (optional)
    The name to use for saving the animation.

    """
    nframes, nwalkers, ndim = data_cube.shape

    final_bins = 50  # number of bins covering final posterior

    # Determine the extent of each parameter, and the final height of the bins
    bins = []
    ymaxs = []
    extremes = []
    for x in range(ndim):
        extremes.append((data_cube[..., x].min(), data_cube[..., x].max()))
        dx = (data_cube[-1, :, x].max() - data_cube[-1, :, x].min())/final_bins
        nbins = int(np.diff(extremes[x])[0]/dx)
        these_bins = np.linspace(extremes[x][0],
                                 extremes[x][1], nbins + 1)[:-1]
        bins.append(these_bins)
        hist, _ = np.histogram(data_cube[-1, :, x], bins=bins[-1], normed=True)
        ymaxs.append(1.1*max(hist))

    # Use the first time sample as the initial frame
    fig = triangle.corner(data_cube[0], labels=labels,
                          plot_contours=False, truths=truths, extents=extremes)
    axes = np.array(fig.axes).reshape((ndim, ndim))
    for x in range(ndim):
        axes[x, x].set_ylim(top=ymaxs[x])

    # Determine number of frames
    thin_factor = int(nframes/rough_length)/fps
    if thin_factor > 1:
        data_cube = data_cube[::thin_factor]
        samps_per_frame *= thin_factor
    samps_per_sec = fps * samps_per_frame

    # Make the movie
    anim = animation.FuncAnimation(fig, update_corner,
                                   frames=xrange(len(data_cube)), blit=True,
                                   fargs=(data_cube, fig, bins, truths))
    return anim


def update_corner(i, data, fig, bins, truths=None):
    """
    Update a corner plot for frame ``i`` of animation.
    """
    ndim = data.shape[-1]
    axes = np.array(fig.axes).reshape((ndim, ndim))

    # Update histograms along diagonal
    for x in range(ndim):
        ax = axes[x, x]

        # Save bins and y-limits
        xlim = ax.get_xlim()
        ylim = ax.get_ylim()

        # Clean current histrogram while keeping ticks
        while len(ax.patches) > 0:
            ax.patches[0].remove()

        ax.hist(data[i, :, x], range=xlim,
                bins=bins[x], histtype='step', normed=True, color='k')
        ax.set_ylim(*ylim)
        if truths is not None:
                ax.axvline(truths[x], color="#4682b4")

    # Update scatter plots
    for x in range(1, ndim):
        for y in range(x):
            ax = axes[x, y]
            line = ax.get_lines()[0]
            line.set_data(data[i, :, y], data[i, :, x])

    return fig,
