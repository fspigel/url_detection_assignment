from cv2 import imread
import numpy as np
import matplotlib.pyplot as plt
from time import time
import pytesseract
import re
from progressbar import progressbar as pb
from sys import argv


def get_address_bar(img):
    """Grabs the FQDN (fully-qualified domain name) from a screenshot of a web browser.
    img is an (m x n x 3) numpy.array representing the screenshot. 
    The function begins by segmenting the image into rectangular blocks, one of 
    which will represent the address bar. It then uses the tesseract OCR engine
    (https://pypi.org/project/pytesseract/) to look for strings of text in each block. 
    Once it comes across a block that contains a FQDN, it parses it and returns. 

    Input:
    - img - (m x n x 3) RGB screenshot of a browser, including its full address bar

    Return:
    - string - the FQDN found in the address bar. If none are found, returns None

    """

    # First, segment image into blocks
    blocks = segment_img(img)
    # print('looking for address bar block...')
    # Look for the address bar
    for block in blocks:
        if block[2][0] - block[0][0] > 10 and \
                block[2][1] - block[0][1] > 10:    # ignore blocks that are too small
            # extract block from the image
            slice = img[block[0][0]:block[2][0],
                        block[0][1]:block[2][1], :]
            # if the browser is running a dark theme, invert the image
            slice = dark_theme_inverter(slice)
            # save to disk in order to run the tesseract engine on it
            plt.imsave('bar_color.png', slice)
            # run tesseract
            text = pytesseract.image_to_string(
                'bar_color.png', config='--psm 7')
            # detect FQDN in the resulting strings
            result = grab_URL(text)
            if result != None:
                return result
            # if none detected, continue on to the next block
    return None


def dark_theme_inverter(img):
    """Tesseract doesn't work if the text color is lighter than the background,
    so we have to invert any images extracted from a dark mode browser

    Input:
    - img - (m x n) or (m x n x 3) numpy.array representing a (part of) a screenshot

    Return:
    - the same image, or the negative of that image, whichever is lighter
    """
    if len(img.shape) > 2:
        flat = np.sum(img, axis=2).flatten()
    else:
        flat = img.flatten()
    n = len(flat)
    avg = np.sum(flat)/n
    # if most of the pixels are dark (below-average brightness), invert image
    if np.sum(flat < avg) > n/2:
        return 1-img
    else:
        return img


def grab_URL(text):
    """Performs a regular expression search in order to determine if the given text
    contains an FQDN or not. If so, it returns the FQDN in question. Otherwise, return None.

    Input:
    - text - string, possibly containing FQDN

    Return:
    - sub-string of text which matches the definition of an FQDN. If none found, returns None.
    """
    domain_extensions = [
        'com', 'org', 'hr', 'ru', 'net', 'ir', 'in', 'uk', 'au', 'de', 'ua', 'us', 'gov'
    ]
    domain_selector = '('
    for domain in domain_extensions:
        domain_selector += domain+'|'
    domain_selector = domain_selector[:-1]
    domain_selector += ')'
    expr = r'\bhttps?://\S+\.'+domain_selector+r'\b'
    search = re.compile(expr).search(text)
    if search == None:
        return None
    else:
        return text[search.start():search.end()]


def segment_img(img):
    """Segments an image into rectangular blocks. Each block is relatively monochrome
    (blocks may have text or icons inside of them). One of these blocks should represent
    the address bar. 

    Input:
    - img - input screenshot

    Return:
    - a list of blocks, where each block is a list of 4 points representing its corners
    (starting with the lower left and going clockwise), where each point is a list of two
    pixel coordinates
    """

    # print('image segmentation...\n')
    start = time()
    blocks = []
    # project a mech grid of points on the image (each 10 pixels vertically, and
    # each 100 pixels horiyontally)
    # the only important thing here is that at least one of these points be inside
    # the bounds of the address bar
    for i in range(0, img.shape[0], 10):
        for j in range(0, img.shape[1], 100):
            accounted_flag = False
            # check if the point is inside another block and, if so, ignore it
            for block in blocks:
                if block[0][0] <= i and block[2][0] >= i \
                        and block[0][1] <= j and block[2][1] >= j:
                    accounted_flag = True
                    continue
            if accounted_flag:
                continue
            # define a new block around the point
            new_block = get_block(img, [i, j])
            blocks.append(new_block)
    # print('segmentation complete: ', time()-start)
    return blocks


def get_block(img, point):
    """Find the block that a given point belongs to. A block is defined rougly as a 
    rectangular shape with a monochrome background, for example a colored rectangle 
    with text or a symbol inside it.

    Input:
    - img - the image containing the block
    - point - a point inside the block
    """
    points = [point]
    target = img[point[0], point[1]]  # the color of the block
    # semi-recursive loop: this loop takes points assumed to be inside the block, then
    # projects perpendicular rays in each of four directions (up, down, left, right),
    # for as long as the ray stays the same color as the block. The end of each ray,
    # and everything in between them is assumed to still be inside the block.
    # At the end of each iteration, the ends of the rays are added to the list of points,
    # then new projections are started from them.
    for i in range(3):
        points_new = []
        for point in points:  # this is inefficient, the same point will be projected from in each successive iteration
            points_new += project(img, point, target)
        points += points_new

    # the end result is a number of points, some of which should be at the extremes
    # of the rectangular block. We need only look at the furthest points in each
    # direction to establish the four boundaries.
    points_x = [point[0] for point in points]
    points_y = [point[1] for point in points]
    i_min = min(points_x)
    i_max = max(points_x)
    j_min = min(points_y)
    j_max = max(points_y)
    return [[i_min, j_min], [i_max, j_min], [i_max, j_max], [i_min, j_max]]


def project(img, point, target):
    """Projet rays from a given point in four directions for as long as they remain
    monochrome, then return the end points. 

    Input:
    - img - screenshot
    - point - origin of the projections
    - target - target color

    Return:
    - a list of four points, representing the edges of the projections
    """
    i, j = point
    i_min, i_max, j_min, j_max = point[0], point[0], point[1], point[1]

    # project to the left
    where = np.where(np.linalg.norm(
        img[point[0]:, point[1]]-target, axis=1) > 1e-6)
    if len(where[0]) == 0:
        i_max = i
    else:
        i_max = i+where[0][0]-1

    # project to the right
    where = np.where(np.linalg.norm(
        img[point[0]::-1, point[1]]-target, axis=1) > 1e-6)
    if len(where[0]) == 0:
        i_min = i
    else:
        i_min = i-where[0][0]+1

    # project down
    where = np.where(np.linalg.norm(
        img[point[0], point[1]:]-target, axis=1) > 1e-6)
    if len(where[0]) == 0:
        j_max = j
    else:
        j_max = j+where[0][0]-1

    # project up
    where = np.where(np.linalg.norm(
        img[point[0], point[1]::-1]-target, axis=1) > 1e-6)
    if len(where[0]) == 0:
        j_min = j
    else:
        j_min = j-where[0][0]+1

    # lots of repeated code, can this be abstracted?
    return [[i, j_min], [i, j_max], [i_min, j], [i_max, j]]


if __name__ == "__main__":
    if len(argv) == 0:
        img = imread("Screenshot from 2021-10-22 15-53-19.png")
    else:
        img = imread(argv[1])
    result = get_address_bar(img)
    # print(flush=True)
    print(result, flush=True)
