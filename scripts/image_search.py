from apiclient.discovery import build
import os
from random import choice


# Set Google Developer API and CSE ID
google_apikey = os.environ["GOOGLE_API"]
cse_id = os.environ["CSE_ID"]

# Set up CSE (Custom Search Engine)
service = build("customsearch", "v1", developerKey=google_apikey)


# Search image url with given keyword
def search_image(keyword):
    # Search image results with CSE
    results = service.cse().list(q=keyword, cx=cse_id, searchType="image").execute()

    # If images exist return random choice from list of urls
    if "items" in results:
        return choice([result["link"] for result in results["items"]])
    else:
        return None
