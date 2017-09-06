from __future__ import division

import numpy as np

from bokeh.layouts import gridplot
from bokeh.plotting import figure, output_file, show

# create an array of RGBA data
N = 20
img = np.empty((N, N), dtype=np.uint32)
view = img.view(dtype=np.uint8).reshape((N, N, 4))
for i in range(N):
    for j in range(N):
        view[i, j, 0] = int(255 * i / N)
        view[i, j, 1] = 158
        view[i, j, 2] = int(255 * j / N)
        view[i, j, 3] = 255

output_file("image_rgba.html")

#p1 = figure(plot_width=472, plot_height=295, x_range=(0, 4727), y_range=(0, 2950))

p1 = figure(x_range=(0, 4727), y_range=(0, 2950))
p2 = figure(plot_width=p1.plot_width, plot_height=p1.plot_height, x_range=p1.x_range, y_range=p1.y_range)


#p2 = figure(plot_width=472, plot_height=295, x_range=p1.x_range, y_range=p1.y_range)

#p.image_rgba(image=[img], x=[0], y=[0], dw=[10], dh=[10])
p1.image_url(["file:///Users/avi/developer/python/web/uploads/a02775df-9b6b-451d-8b94-f86ad49c9059/L1006443.jpg"],  x=[0], y=[2950], w=[4727], h=[2950])
p2.image_url(["file:///Users/avi/developer/python/web/uploads/a02775df-9b6b-451d-8b94-f86ad49c9059/L1006443.jpg"],  x=[0], y=[2950], w=[4727], h=[2950])

p = gridplot([[p1,p2]])
show(p)

