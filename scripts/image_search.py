import os
import requests
from random import choice


# Set Google Developer API and CSE ID
GOOGLE_API_KEY = os.environ["GOOGLE_API"]
CSE_ID = os.environ["CSE_ID"]


# Search image url with given keyword
def search_image(keyword):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": CSE_ID,
        "searchType": "image",
        "lr": "lang_fi",
        "q": keyword
    }
    try:
        res = requests.get(url=url, params=params)
        data = res.json()

        if "items" in data:
            return choice([result["link"] for result in data["items"]])
            # return [result["link"] for result in data["items"]][0]

    except Exception:
        return None
