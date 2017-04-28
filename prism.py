#!/usr/bin/env python

from __future__ import division

import numpy as np
from matplotlib import animation
from matplotlib.pyplot import close

try:
    import corner as triangle
except ImportError:
    # Try to import corner under its old name
    import triangle


def inline_ipynb():
    """
    Inline animations in ipython notebooks.
    """
    from matplotlib import animation
    from IPython.display import HTML

    animation.Animation._repr_html_ = anim_to_html


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
        try:
            anim._encoded_video = video.encode("base64")
        except AttributeError:
            # Handle encoding differently if using python3
            import base64
            anim._encoded_video = base64.b64encode(video).decode('utf-8')

    return VIDEO_TAG.format(anim._encoded_video)


def corner(data_cube, color='k', ms=2.0,
           labels=None, truths=None,
           samps_per_frame=10, fps=30,
           rough_length=10.0, outname='corner.mp4',
           hist_kwargs=None, **kwargs):
    """
    Animate a triangle corner plot.  All kwargs are
    passed to ``triangle.corner()``.

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

    :param outname: (optional)
    The name to use for saving the animation.

    :param hist_kwargs: (optional)
    Keyword arguments to be passed to ``hist()``.

    """
    if hist_kwargs is None:
        hist_kwargs = dict()

    hist_kwargs["color"] = hist_kwargs.get("color", color)
    hist_kwargs["histtype"] = hist_kwargs.get("histtype", "step")
    hist_kwargs["normed"] = hist_kwargs.get("normed", True)

    nframes, nwalkers, ndim = data_cube.shape

    final_bins = 50  # number of bins covering final posterior

    # Determine the extent of each parameter, and the final height of the bins
    bins = []
    ymaxs = []
    extremes = []
    for x in range(ndim):
        extremes.append((data_cube[..., x].min(), data_cube[..., x].max()))
        dx = (data_cube[-1, :, x].max() - data_cube[-1, :, x].min())/final_bins
        nbins = np.diff(extremes[x])[0]//dx
        these_bins = np.linspace(extremes[x][0],
                                 extremes[x][1], nbins + 1)[:-1]
        bins.append(these_bins)
        hist, _ = np.histogram(data_cube[-1, :, x], bins=bins[-1], normed=True)
        ymaxs.append(1.1*max(hist))

    # Use the first time sample as the initial frame
    fig = triangle.corner(data_cube[0], color=color, labels=labels,
                          plot_contours=False, plot_density=False,
                          plot_datapoints=True,
                          truths=truths, range=extremes,
                          hist_kwargs=hist_kwargs, **kwargs)
    axes = np.array(fig.axes).reshape((ndim, ndim))
    for x in range(ndim):
        axes[x, x].set_ylim(top=ymaxs[x])

        # Set marker sizes
        for y in range(x):
            ax = axes[x, y]
            line = ax.get_lines()[0]
            line.set_markersize(ms)

    # Determine number of frames
    thin_factor = (nframes//rough_length)//fps
    if thin_factor > 1:
        data_cube = data_cube[::thin_factor]
        samps_per_frame *= thin_factor
    samps_per_sec = fps * samps_per_frame

    # Make the movie
    anim = animation.FuncAnimation(fig, iterate_corner,
                                   frames=range(len(data_cube)), blit=True,
                                   fargs=(data_cube, fig, bins,
                                          truths, ymaxs, hist_kwargs))

    # Close the window and return just the animation
    close(fig)

    return anim


def update_corner(data, fig, bins=50, truths=None, ymaxs=None, **kwargs):
    """
    Update a corner plot with the given `data`.
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

        try:
            n, _, _ = ax.hist(data[:, x], range=xlim, bins=bins[x], **kwargs)
        except TypeError:
            n, _, _ = ax.hist(data[:, x], range=xlim, bins=bins, **kwargs)

        if ymaxs is None:
            ax.set_ylim(ymax=n.max())
        else:
            ax.set_ylim(ymax=ymaxs[x])

        if truths is not None:
            ax.axvline(truths[x], color="#4682b4")

    # Update scatter plots
    for x in range(1, ndim):
        for y in range(x):
            ax = axes[x, y]
            line = ax.get_lines()[0]
            line.set_data(data[:, y], data[:, x])

    return fig,


def iterate_corner(i, data_cube, fig, bins=50, truths=None,
                   ymaxs=None, hist_kwargs=None):
    """
    Update a corner plot for frame ``i`` of animation.
    """
    return update_corner(data_cube[i], fig, bins, truths, ymaxs, **hist_kwargs)
