from app import geolocator
from geopy.exc import GeocoderTimedOut
from PIL import Image
import requests
from io import BytesIO


def geocode(address, attempt=1, max_attempts=5):
    try:
        return geolocator.geocode(address)
    except GeocoderTimedOut:
        if attempt <= max_attempts:
            return geocode(address, attempt=attempt + 1)
        raise


def get_image_from(src):
    return Image.open(BytesIO(requests.get(src).content))
