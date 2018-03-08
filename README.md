# prism
An animated wrapping of [Dan Foreman-Mackey](https://github.com/dfm)'s
[corner.py](https://github.com/dfm/corner.py).

## Usage
``prism`` is handy for watching ensembles burn in.  Pretend below that
``samples`` are samples in 5 dimensions collected by 5000 walkers in 100 steps.
```python
import numpy as np
import prism

nsteps, nwalkers, ndim  = 100, 5000, 5
samples = np.random.randn(nsteps * nwalkers * ndim).reshape([nsteps, nwalkers, ndim])

# Make-believe burn in
samples[:nsteps/10] *= np.arange(1, nsteps/10+1)[::-1, np.newaxis, np.newaxis]

anim = prism.corner(samples)
anim.save("prism.mp4", fps=30)
```

and you get something like

![Demo](https://raw.github.com/bfarr/prism/master/prism.gif)
