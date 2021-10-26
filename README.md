### URL Detection Assignment

A simple python API that takes a screenshot of a browser as input, and outputs the address currently in the address bar.

The process first divides the screenshot into rectangular, monocolor blocks. One of the blocks will always represent the address bar. It then employs google's Tesseract OCR engine to read the text in each block. If the text matches a fixed definition of a URL (starts with http and ends with .com or one of a dozen other domain extensions), then that block is parsed and returned.

`getaddressbar.py` contains the code that analyzes the screenshots. It is usable on its own with `python3 getaddressbar.py <path-to-image>`

`getaddressbar_api.py` is the Flask-based web API that serves as the backend for the web app (found at http://fspigel-assignment.sytes.net/)

`test.py` is used to automatically process a folder of screenshots. Simply point it to a folder with `python3 test.py <path-to-folder>`. It will output the parsed address for each image, along with the image name. For example, `python3 test.py test_images_assigned/`

