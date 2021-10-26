from cv2 import imread
from getaddressbar import get_address_bar
from os import listdir

image_folder = 'test_images_assigned/'
images = listdir(image_folder)
for image_name in images:
    img = imread(image_folder+image_name)
    result = get_address_bar(img)
    print(image_name, result)
