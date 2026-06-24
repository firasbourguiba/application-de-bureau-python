"""
Api client module.

Role : interroget l'API Geoapify (Place Api ) pour recuperer les details d'un lieu (restaurant, bar, etc..)
sous forme une liste de dictionnaire (json) avec les informations suivantes:
-name   :str
- formatted :str ( tout l'addresse en meme ligne)
- city :str ou none 
- postcode :str ou none
-categories :list ( liste des categories du lieu)
- website :str ou none
- opening_hours :str ou none
- place_id :str (identifiant unique Geoapify)
-lat, lon : float (coordonnees geographiques du lieu)

Rmarque : le champ " website" n'est pas toujours present 
dans la reponse de l'api , est c'est ca que on cherche apres des restaurant sans site web
pour faire des appelles d'offres 
"""



import requests

GEOAPIFY_PLACES_URL = "https://api.geoapify.com/v2/places"
GEOAPIFY_GEOCODE_URL = "https://api.geoapify.com/v1/geocode/search"

class GeoapifyAPIError(Exception):
    """levee quand l'appel a api est echouee (erreur de reseau, ou reponse non 200)"""

    pass

def geocode_city(api_key, city_name):
    """"
    convertir le nom d'une ville en coordonnees geographiques (lat, lon) en utilisant l'API Geoapify Geocoding.
    Utilise Geoapify Geocoding API avec le paramètre type=city
    pour ne retourner que des villes/villages
    exemple 
    api_key : str
        Cle API Geoapify.
    city_name : str
        Nom de la ville (ex: "Paris").

    Returns
    -------
       - "lat": float
         - "lon": float
        - "formatted": str(nom complete retourné par api)
    """

    params = {
        "text": city_name,
        "type": "city",
        "limit": 1,
        "format": "json",
        "apiKey": api_key,
    }

    try:
        response = requests.get(GEOAPIFY_GEOCODE_URL, params=params, timeout=10)
    except requests.RequestException as e:
        raise GeoapifyAPIError(f"Erreur lors de l'appel à l'API Geoapify Geocoding: {e}") from e
    
    if response.status_code != 200:
        raise GeoapifyAPIError(f"Geocoding API code {response.status_code} : {response.text}")
    
    data = response.json()
    results = data.get("results", [])

    if not results:
        raise GeoapifyAPIError(f"Aucun résultat trouvé pour la ville '{city_name}'.")
    

    premier = results[0]

    return {
        "lat": premier.get("lat"),
        "lon": premier.get("lon"),
        "formatted": premier.get("formatted", city_name),
    }

#  2 on commence la partie de cherche les restaurent par cercle ( pour clic sur carte directement)

def search_restaurants_by_radius(api_key, lon, lat, radius_meters=2000, limit=20):
    """
    Cherche des restaurants dans un rayon spécifié autour d'un point
      géographique donné en utilisant l'API Geoapify Places.
      "filter=circle:LON,LAT,RAYON_EN_METRES"
    
    """

    params = {
        "categories": "catering.restaurant",
        "filter": f"circle:{lon},{lat},{radius_meters}",
        "bias": f"proximity:{lon},{lat}",
        "limit": limit,
        "apiKey": api_key,
    }
    return  _appeler_places_api(params) 

#3 recherche  les restaurents par les noms des villes  *

def search_restaurants_by_city(api_key, city_name, radius_meters=2000, limit=20):
    """"
     Recherche "tout-en-un" : l'utilisateur tape un nom de ville,
    on géocode d'abord, puis on cherche les restaurants autour.
    
    """

    city_info = geocode_city(api_key, city_name)

    restaurants = search_restaurants_by_radius(
        api_key=api_key,
        lon=city_info["lon"],
        lat=city_info["lat"],
        radius_meters=radius_meters,
        limit=limit,
    )

    return {
        "city_info": city_info,
        "restaurants": restaurants
    }

# 4 fonction interne pour appeler l'API Geoapify Places avec les paramètres donnés
def _appeler_places_api(params):
    """
    Appelle Geoapify Places API avec les parametres donnés
    et retourne une liste de dictionnaires propres.
    """
    try:
        response = requests.get(GEOAPIFY_PLACES_URL, params=params, timeout=10)
    except requests.exceptions.RequestException as e:
        raise GeoapifyAPIError(f"Erreur réseau (Places) : {e}") from e
 
    if response.status_code != 200:
        raise GeoapifyAPIError(
            f"Places API code {response.status_code} : {response.text}"
        )
 
    data = response.json()
    features = data.get("features", [])
 
    restaurants = []
    for feature in features:
        proprietes = feature.get("properties", {})
        restaurants.append(_extraire_restaurant(proprietes))
 
    return restaurants
 
def _extraire_restaurant(proprietes):
    """"
    construit un dictionnaire propre à partir du bloc "properties"
    d'un résultat Places API.
[name , formatted, city, postcode, categories, website, opening_hours, place_id, lat, lon]

    """
    return {
        "place_id": proprietes.get("place_id"),
        "name": proprietes.get("name", "Nom inconnu"),
        "formatted_address": proprietes.get("formatted"),
        "city": proprietes.get("city"),
        "postcode": proprietes.get("postcode"),
        "categories": proprietes.get("categories", []),
        "website": proprietes.get("website"),       # None si absent
        "opening_hours": proprietes.get("opening_hours"),
        "lat": proprietes.get("lat"),
        "lon": proprietes.get("lon"),
    }

#5  afficeher le site web d'un restaurant ou "Pas de site web" si absent
def afficher_site_web(restaurant):
    """
    Retourne "Pas de site web" si website est None,
    sinon retourne l'URL.
    """
    site = restaurant.get("website")
    return site if site else "Pas de site web"
"""
#teste manuel de la fonction afficher_site_web
if __name__ == "__main__":
    MA_CLE_API = "mettre key  #  remplacez par votre clé
 
    
    print("TEST 1 : Recherche par nom de ville (Paris)")
    
    try:
        resultat = search_restaurants_by_city(
            api_key=MA_CLE_API,
            city_name="Paris",
            radius_meters=2000,
            limit=5,
        )
        print(f"Ville trouvée : {resultat['city_info']['formatted']}")
        print(f"Coordonnées   : {resultat['city_info']['lat']}, {resultat['city_info']['lon']}")
        print(f"Restaurants trouvés : {len(resultat['restaurants'])}")
        print()
        for r in resultat["restaurants"]:
            print(f"  {r['name']}")
            print(f"    Adresse  : {r['formatted_address']}")
            print(f"    Site web : {afficher_site_web(r)}")
            print(f"    Horaires : {r['opening_hours'] or 'Non renseigné'}")
            print()
    except GeoapifyAPIError as e:
        print(f"ERREUR : {e}")
 
    print("=" * 60)
    print("TEST 2 : Recherche par cercle (Tour Eiffel, rayon 500m)")
    print("=" * 60)
 
    try:
        restaurants = search_restaurants_by_radius(
            api_key=MA_CLE_API,
            lon=2.2945,
            lat=48.8584,
            radius_meters=500,
            limit=5,
        )
        print(f"Restaurants trouvés : {len(restaurants)}")
        for r in restaurants:
            print(f"  {r['name']} — {afficher_site_web(r)}")
    except GeoapifyAPIError as e:
        print(f"ERREUR : {e}")
        """