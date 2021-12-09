import os
from random import choice
from ..utils import get
from ...logger import logging


logger = logging.getLogger(__name__)


class ImageSearch:
    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    CSE_ID = os.environ["CSE_ID"]
    REGION = os.environ["REGION"]

    def __init__(self):
        pass

    # Search image url with given keyword
    def get_random_image(self, keyword):
        try:
            data = self._get_data(keyword)
            if "items" in data:
                image = choice([result["link"] for result in data["items"]])
                return image
        except Exception:
            logger.exception(f"Error getting image with keyword: {keyword}")

    # Get image data
    def _get_data(self, keyword):
        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": self.GOOGLE_API_KEY,
            "cx": self.CSE_ID,
            "searchType": "image",
            "hl": self.REGION.lower(),
            "q": keyword,
        }
        data = get(url, params).json()
        return data
