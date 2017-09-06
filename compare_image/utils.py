import cv2
import numpy as np
from skimage.measure import compare_ssim
import scipy.signal
import logging
logger = logging.getLogger(__name__)


def compute_shift_row_col_parameters(rows, cols, shift_row, shift_col):
    # note 0,0 is the top left corner
    # mask for shifted image
    # pos col means the mask must start 0+col and end at width
    # neg col means the mast must start at 0 and end at  width+col
    # pos row means the mask must start at 0 + row and end at width
    # neg row means the mask must start at 0 and endt at height+row

    start_row = 0
    stop_row = rows
    start_col = 0
    stop_col = cols

    if shift_row > 0:
        start_row = shift_row
        # stop_row  -= shift_row
    elif shift_row < 0:
        stop_row += shift_row  # 1080 + (-shift_row)

    if shift_col > 0:
        start_col = shift_col
    elif shift_col < 0:
        stop_col += shift_col

    return start_row, stop_row, start_col, stop_col

def detect_shift_using_correlation(im1, im2):
   # get rid of the color channels by performing a grayscale transform
   # the type cast into 'float' is to avoid overflows
   im1_gray = np.sum(im1.astype('float'), axis=2)
   im2_gray = np.sum(im2.astype('float'), axis=2)

   # get rid of the averages, otherwise the results are not good
   im1_gray -= np.mean(im1_gray)
   im2_gray -= np.mean(im2_gray)

   # calculate the correlation image; note the flipping of onw of the images
   im1xim2 = scipy.signal.fftconvolve(im1_gray, im2_gray[::-1,::-1], mode='same')

   center = np.unravel_index(np.argmax(im1xim2), im1xim2.shape)

   shift_row = int(im1.shape[0] / 2.0 - center[0])
   shift_col = int(im1.shape[1] / 2.0 - center[1])

   start_row, stop_row, start_col, stop_col = compute_shift_row_col_parameters(im1.shape[0], im1.shape[1], shift_row, shift_col)

   return start_row, im1.shape[0] - stop_row, start_col, im1.shape[1] - stop_col



def detect_shift(image, black=(20,20,20)):
    """
    When an image is shifted vertically/horizontally a "black" col/row is inserted into the image.
    given an image with the below known characteristics. This algorithm will detect the shift
    the image must guarantee that in any given row or col there is at least one pixel that is not BLACK.
    :param image: 
    :return: a tuple: top row shift, bottom row shift, start col shift, end col shift
    """
    # when an image is shifted, one or more black row and or cols are inserted
    # assume that there are no "black" rows of pixels

    def compare(srow,erow,scol,ecol, black):
        b_slice = image[srow:erow, scol:ecol, 0]
        if np.max(b_slice) > black[0]:
            return True
        g_slice = image[srow:erow, scol:ecol, 1]
        if np.max(g_slice) > black[1]:
            return True
        r_slice = image[srow:erow, scol:ecol, 2]
        if np.max(r_slice) > black[2]:
            return True
        return False

    max_col = image.shape[1]
    max_row = image.shape[0]


    # look for left and right shifts
    srow =  0
    erow =  -1

    # left side
    left_col = 0 # no shift
    for scol in range (300):
        ecol = scol + 1
        if compare(srow,erow,scol,ecol,black):
            break
        left_col += 1

    # right side
    right_col = 0 # no shift
    for ecol in range (max_col, max_col-300, -1):
        scol = ecol - 1
        if compare(srow,erow,scol,ecol, black):
            break
        right_col += 1

    # top down shifts
    scol = 0
    ecol = -1

    #top row
    top_row = 0
    for srow in range(300):
        erow = srow+1
        if compare(srow,erow,scol,ecol, black):
            break
        top_row += 1

    # bottom row
    bottom_row = 0  # no shift
    for erow in range(max_row, max_row - 300, -1):
        srow = erow - 1
        if compare(srow, erow, scol, ecol, black):
            break
        bottom_row += 1

    return top_row, bottom_row, left_col, right_col

def align_images(golden_img, captured_img, black_threshold):
    """
    Utility function that given 2 images that are relatively shifted returns images that are now aligned. if the images
    do not require alignment the images are returned as is.
    Method uses the fftconvolve procedure to compare two images and detect shifts.  Assumes that the images are just shifted but not stretched
    Both images must have the same dimension as well
    :param golden_img: golden image
    :param captured_img: capture
    :return: golden_image, capture_image that are aligned - this are "views" into the passed in images
    """

    # detect how much image2 the captured image is shifted

    top_row, bottom_row, left_col, right_col = detect_shift(captured_img, black=black_threshold)

    if top_row == 0 and bottom_row == 0 and left_col == 0 and right_col == 0:
        logger.info("No shift detected")
        return golden_img, captured_img


    logger.info("Shift detected top: {}  bottom: {} left: {} right: {}".format(top_row, bottom_row, left_col, right_col))

    # apply shift parameter to remove the black borders
    cropped_capture_img = captured_img[top_row:captured_img.shape[0]-bottom_row, left_col:captured_img.shape[1]-right_col]

    # crop the golden image (image1) to align with the cropped image
    cropped_golden_img = golden_img[bottom_row:golden_img.shape[0]-top_row, right_col:golden_img.shape[1]-left_col]

    return cropped_golden_img, cropped_capture_img

def capture_remove_shift(captured, top_row, bottom_row, left_col, right_col):
    return captured[top_row:captured.shape[0] - bottom_row, left_col:captured.shape[1] - right_col]

def golden_remove_shift(golden, top_row, bottom_row, left_col, right_col):
    return  golden[bottom_row:golden.shape[0]-top_row, right_col:golden.shape[1]-left_col]

def compute_SSIM(image1, image2):

    score, diff = compare_ssim(cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY), cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY), full=True)
    return score, diff
