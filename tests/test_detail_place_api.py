"""
Script pour voir  la strucutre de Json de Place Detail api
sur un resteraut exemple "Dakawa"  son id"510ecb55e2f008034059631faee64a6c4840f00103f90144d9ccff0000000092030644616b617761"

"""

import requests
import json

API_KEY = "132c437924d24298b7c5b3fc7ee703df"

place_id = "510ecb55e2f008034059631faee64a6c4840f00103f90144d9ccff0000000092030644616b617761"
 
url = (
    "https://api.geoapify.com/v2/place-details"
    f"?id={place_id}"
    f"&apiKey={API_KEY}"
)

response = requests.get(url)
print("status code", response.status_code)
 
if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("Erreur :", response.text)
