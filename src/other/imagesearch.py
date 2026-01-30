import os
import random
from ..common.logger import logging
from ..common.utils import get

logger = logging.getLogger(__name__)


class ImageSearch:
    GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
    CSE_ID = os.environ["CSE_ID_SECRET"]
    REGION = os.getenv("REGION", "FI")

    def __init__(self):
        pass

    # Search image url with given keyword
    def get_random_image(self, keyword):
        url = "https://customsearch.googleapis.com/customsearch/v1"
        params = {
            "key": self.GOOGLE_API_KEY,
            "cx": self.CSE_ID,
            "searchType": "image",
            "fileType": "jpg",
            "hl": self.REGION.lower(),
            "gl": self.REGION.lower(),
            "q": keyword,
        }
        try:
            data = get(url, params).json()
            if "items" in data:
                images = [result["link"] for result in data["items"]]
                image = random.choice(images)
                return image
        except Exception:
            logger.exception(f"Error getting image with keyword {keyword}")
