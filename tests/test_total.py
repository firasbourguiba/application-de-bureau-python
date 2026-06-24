"""scripte de teste uniquement (a supprimer /ignorer pour le code apres)
objet: tester l'api (Place API) et voir la structure de reelle retournee par Geoapify Places API

"""

import requests
import json

API_KEY = "132c437924d24298b7c5b3fc7ee703df"

url = (
    "https://api.geoapify.com/v2/places"
    "?categories=catering.restaurant"
    "&filter=rect:2.30,48.88,2.38,48.84"
    "&limit=5"
    f"&apiKey={API_KEY}"
)

response = requests.get(url)

print("status code", response.status_code)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2, ensure_ascii=False))
else:
    print("Error:", response.text)