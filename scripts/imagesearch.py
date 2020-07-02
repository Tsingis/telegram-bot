import os
import requests
from random import choice


class ImageSearch:

    # Set Google Developer API and CSE ID
    GOOGLE_API_KEY = os.environ["GOOGLE_API"]
    CSE_ID = os.environ["CSE_ID"]

    def __init__(self):
        pass

    # Search image url with given keyword
    def search_random_image(self, keyword):
        try:
            data = self._get_data(keyword)
            if "items" in data:
                return choice([result["link"] for result in data["items"]])
        except Exception as ex:
            print(f"Error getting random Google image with keyword {keyword}: " + str(ex))
            return None

    # Get image data
    def _get_data(self, keyword):
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": self.GOOGLE_API_KEY,
            "cx": self.CSE_ID,
            "searchType": "image",
            "lr": "lang_fi",
            "q": keyword
        }
        try:
            res = requests.get(url=url, params=params)
            if res.status_code == 200:
                return res.json()
            res.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            print("Error getting search data: " + str(ex))
