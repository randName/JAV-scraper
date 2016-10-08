import requests
from io import BytesIO
from PIL import Image

def imagesize(url):
    r = requests.get(url, headers={"Range": "bytes=0-500"}, stream=True)
    try:
        return Image.open(BytesIO(r.content)).size
    except AttributeError:
        return (0, 0)
