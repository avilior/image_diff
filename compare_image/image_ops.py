import logging
import os

import cv2
import numpy as np

logger = logging.getLogger(__name__)

import utils
import imutils

from bokeh.models import (FactorRange, LinearAxis, Grid,
                          Range1d)
from bokeh.models.glyphs import VBar
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.models.sources import ColumnDataSource
from bokeh.layouts import gridplot

def create_hover_tool():
    # we'll code this function in a moment
    return None


def create_bar_chart(data, title, x_name, y_name, hover_tool=None, width=1200, height=300):
    """
    Creates a bar chart plot with the exact styling for the centcom
       dashboard. Pass in data as a dictionary, desired plot title,
       name of x axis, y axis and the hover tool HTML.
    """
    source = ColumnDataSource(data)

    xdr = FactorRange(factors=data[x_name])   # xdr = FactorRange(factors=data[x_name])

    ydr = Range1d(start=0,end=max(data[y_name]))

    tools = []
    if hover_tool:
        tools = [hover_tool,]

    plot = figure(title=title, x_range=xdr, y_range=ydr, plot_width=width,
                  plot_height=height, h_symmetry=False, v_symmetry=False,
                  min_border=0, toolbar_location="above", tools=tools,
                  responsive=True, outline_line_color="#666666")

    glyph = VBar(x=x_name, top=y_name, bottom=0, width=.8,
                 fill_color="#e12127")
    plot.add_glyph(source, glyph)

    xaxis = LinearAxis()
    yaxis = LinearAxis()

    plot.add_layout(Grid(dimension=0, ticker=xaxis.ticker))
    plot.add_layout(Grid(dimension=1, ticker=yaxis.ticker))
    plot.toolbar.logo = None
    plot.min_border_top = 0
    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = "#999999"
    plot.yaxis.axis_label = "Count"
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = "Bins"
    plot.xaxis.major_label_orientation = 1
    plot.xaxis.minor_tick_line_color = "orange"
    return plot


# Not used
def plot_histogram(data):

    hover = create_hover_tool()
    plot = create_bar_chart(data, "Histogram", "x", "y", hover)
    script, div = components(plot)
    return script, div


def histogram_data(image):
    h = None
    h_b = None
    h_g = None
    h_r = None


    h, e = np.histogram(image, bins=[x for x in range(257)])


    if image.shape[2] == 3:
        h_b, e = np.histogram(image[:, :, 0], bins=[x for x in range(257)])
        h_g, e = np.histogram(image[:, :, 1], bins=[x for x in range(257)])
        h_r, e = np.histogram(image[:, :, 2], bins=[x for x in range(257)])

    return {"h":h, "h_b":h_b, "h_g":h_g, "h_r":h_r, "bins": e[:-1]}


def make_histogram_plot(data):

    x = data['bins'].tolist()

    h = data['h'].tolist()
    h_b = None
    h_g = None
    h_r = None
    if 'h_b' in data:
        h_b = data['h_b'].tolist()
    if 'h_g' in data:
        h_g = data['h_g'].tolist()
    if 'h_r' in data:
        h_r = data['h_r'].tolist()

    # data contains histograms and bins all in numpy
    xdr = Range1d(start=min(x), end=max(x))
    ydr = Range1d(start=min(h), end=max(h))

    plot = figure( x_range=xdr, y_range=ydr,
                   h_symmetry=False, v_symmetry=False,
                  min_border=0, toolbar_location="above",
                  responsive=True, outline_line_color="#666666")

    plot.vbar(x=x,  width=0.8, bottom=0, top=h, color="gray", fill_alpha=0.1)

    if h_b:
        # plot.vbar(x=x, width=0.8, bottom=0, top=h_b, color="blue", fill_alpha=0.3)
        plot.line(x, h_b, line_width=1, color="blue")
    if h_g:
        # plot.vbar(x=x, width=0.8, bottom=0, top=h_g, color="green", fill_alpha=0.3)
        plot.line(x, h_g, line_width=1, color="green")
    if h_r:
        # plot.vbar(x=x, width=0.8, bottom=0, top=h_r, color="red", fill_alpha=0.3)
        plot.line(x, h_r, line_width=1, color="red")

    plot.yaxis.axis_label = "Count"
    plot.ygrid.grid_line_alpha = 0.1
    plot.xaxis.axis_label = "Bins"
    plot.xaxis.major_label_orientation = 1
    return plot


def make_side_by_side_histogram_plot(ldata,rdata):

    p1 = make_histogram_plot(ldata)
    p1.title.text = "left image"
    p2 = make_histogram_plot(rdata)
    p2.title.text = "right image"
    p2.x_range = p1.x_range
    p2.y_range = p1.y_range
    p = gridplot([[p1, p2]])
    return p

def make_histogram_diff_plot(ldata, rdata):

    delta_h = (ldata['h'] - rdata['h'])
    delta_h_b = None
    delta_h_g = None
    delta_h_r = None
    if 'h_b' in ldata and 'h_b' in rdata:
        delta_h_b = ldata['h_b'] - rdata['h_b']
    if 'h_g' in ldata and 'h_g' in rdata:
        delta_h_g = ldata['h_g'] - rdata['h_g']
    if 'h_r' in ldata and 'h_r' in rdata:
        delta_h_r = ldata['h_r'] - rdata['h_r']

    p = make_histogram_plot({'bins':ldata['bins'], 'h':delta_h, 'h_b': delta_h_b, 'h_g': delta_h_g, 'h_r': delta_h_r})
    p.title.text = "left - right"
    return p

def compare(img1, img2):
    """

    :param img1:
    :param img2:
    :return: ssim score, marked up image1, marked up image2, diff image and threshold image
    """

    ssim, diff = utils.compute_SSIM(img1, img2)


    diff = (diff * 255).astype("uint8")

    thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    cnts = cnts[0] if imutils.is_cv2() else cnts[1]

    for c in cnts:
        (x, y, w, h) = cv2.boundingRect(c)
        cv2.rectangle(img1, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.rectangle(img2, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return ssim, img1, img2, diff, thresh

def _fname(p):
    return os.path.splitext(os.path.basename(p))[0]

def workon_images(left, right, upload_dir):
    """

    :param left:
    :param right:
    :param upload_dir:
    :return:
        { "ssim_score":
            "diff":    <diff image name> optional
            "thresh"   <thresh image name> optional
            "marked_l" <marked left image name> optional
            "marked_r"  <marked right iamge name> optional
            "histogram" <dual histogram plot {"div","script"} for left image and right image>
            "diff_histogram" {"div","script"} <single histogram plot
        }

    """

    if not os.path.isfile(left) or not os.path.isfile(right):
        return 1, "Files were not found"

    l = cv2.imread(left)
    r = cv2.imread(right)


    if l is None or r is None:
        return 1, "Images could not be loaded into opencv"

    minus_filename = None

    # get thes sizes of the image
    # size
    # lstat["rows"] = l.shape[0]
    # lstat["cols"] = l.shape[1]
    # rstat["rows"] = r.shape[0]
    # rstat["cols"] = r.shape[1]

    result = {}

    logger.debug("left image w: {} h: {}  right image w:{} h: {}".format(l.shape[1], l.shape[0], r.shape[1], r.shape[0]))

    # if the images are the same size then we can do certain compare operations
    if l.shape[0] == r.shape[0] and l.shape[1] == r.shape[1]:
        # detect shift
        sr, er, sc, ec = utils.detect_shift_using_correlation(l, r)

        if sr != 0 or er != 0 or sc != 0 or ec != 0:
            # shift detection using black bars  -- since we know the input pattern otherwise need to use fft method

            logger.debug("Shift detected sr: {} er: {} sc: {} ec: {}".format(sr, er, sc, ec))

            r = utils.capture_remove_shift(r, sr, er, sc, ec)
            l = utils.golden_remove_shift(l, sr, er, sc, ec)


        # straight forward image subtraction
        #save the diff image in the upload_dir using <left_filename>_minus_<right_filename>
        minus_filename = os.path.join(upload_dir, "{}_minus_{}.png".format(_fname(left), _fname(right)))
        cv2.imwrite(minus_filename, l - r)
        result["minus"] = minus_filename

        # compute diff using SSIM
        marked_l = np.copy(l)
        marked_r = np.copy(r)

        ssim, marked_l, marked_r, diff, thresh = compare(marked_l, marked_r)

        diff_filename = os.path.join(upload_dir, "{}_diff_{}.png".format(_fname(left), _fname(right)))
        thresh_filename = os.path.join(upload_dir, "{}_thresh_{}.png".format(_fname(left), _fname(right)))
        marked_l_filename = os.path.join(upload_dir, "{}_lmarked.png".format(_fname(left)))
        marked_r_filename = os.path.join(upload_dir, "{}_rmarked.png".format(_fname(right)))
        cv2.imwrite(diff_filename, diff)
        cv2.imwrite(thresh_filename, thresh)
        cv2.imwrite(marked_l_filename, marked_l)
        cv2.imwrite(marked_r_filename, marked_r)

        result["ssim_score"] = ssim
        result["diff"]   = os.path.basename(diff_filename)
        result["thresh"] = os.path.basename(thresh_filename)
        result["marked_l"] = os.path.basename(marked_l_filename)
        result["marked_r"] = os.path.basename(marked_r_filename)

        logger.info(f"Computed SSIM {ssim}")


    # histograms of the left and right images
    histogram = {}
    diff_histogram = {}
    histogram["script"], histogram["div"] = components(make_side_by_side_histogram_plot(histogram_data(l),histogram_data(r)))
    diff_histogram["script"], diff_histogram["div"] = components(make_histogram_diff_plot(histogram_data(l), histogram_data(r)))


    result["histogram"] = histogram
    result["diff_histogram"] = diff_histogram

    return 0, result
