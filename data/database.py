"""
database.py

objectif;  gere les gere les base de données sqlite pour stocker les restaurents 
recuperés via l'api Geoapify Places API

- stocker les restaurents dans une base de données sqlite
- gere le cas ou la base n'est pas vide lors d'un nouveau telechargement 
 solution : insert or ignore si le resterant existe deja 
 - effacer le continu de la base de donnees "menu"
 - agregation sql (somme ou moyenne) via requete sql 

 table 'restaurants' :
    place_id : TEXT PRIMARY KEY  (identifiant unique Geoapify)
    name : TEXT
    formatted_address : TEXT
    city : TEXT
    postcode : TEXT
    categories : TEXT  
    website : TEXT  (NULL si absent)
    opening_hours : TEXT
    lat : REAL
    lon : REAL

"""

import sqlite3
import os

# 1 chemain de la base de données SQLite
DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "restaurants.db")

# 2 connection et creation de table
def get_connection(db_path=DEFAULT_DB_PATH):
    """
    ouvre une connecxion sqlite ver le ficher db_path
    cree le fichier si il n'existe pas

  """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # pour accéder aux colonnes par nom
    return conn

def create_table(db_path=DEFAULT_DB_PATH):
    """"
    cree la table 'restaurants' si elle n'existe pas deja
    appelee une fois au demarage de l'application
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS restaurants (
            place_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            formatted_address TEXT,
            city TEXT,
            postcode TEXT,
            categories TEXT,
            website TEXT,
            opening_hours TEXT,
            lat REAL,
            lon REAL
        )
        """
    )
    conn.commit()
    conn.close()

# 3 insertion de restaurants dans la base de données

def insert_restaurants(restaurants, db_path=DEFAULT_DB_PATH):
    """
    Gestion du cas "base non vide" (exigence du sujet) :
     INSERT OR IGNORE : si un restaurant avec le même place_id
      existe déjà, il est simplement ignoré (pas de doublon,
      pas d'erreur, pas d'écrasement).
      """
    
    conn = get_connection(db_path)
    cursor = conn.cursor()

    # compter avant insertion
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    avant = cursor.fetchone()[0]

    for r in restaurants:
        categories_texte = ", ".join(r.get("categories", []))

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO restaurants
                (place_id, name, formatted_address, city, postcode,
                 categories, website, opening_hours, lat, lon)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                r.get("place_id"),
                r.get("name"),
                r.get("formatted_address"),
                r.get("city"),
                r.get("postcode"),
                categories_texte,
                r.get("website"),
                r.get("opening_hours"),
                r.get("lat"),
                r.get("lon"),
            ))
        except sqlite3.Error as e:
            print(f"Erreur insertion {r.get('name')} : {e}")

    conn.commit()

    # compter après insertion
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    apres = cursor.fetchone()[0]

    conn.close()
    return apres - avant

# 4 effacer le contenu de la table restaurants
def clear_database(db_path=DEFAULT_DB_PATH):
    """
    Supprime TOUS les restaurants de la table.
    Appelée depuis le menu "Effacer la base de données".
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM restaurants")
    conn.commit()
    conn.close()

# 5 lecture les donner

def get_all_restaurants(db_path=DEFAULT_DB_PATH):
    """"
    retourne une liste de dictionnaires representant tous les restaurants
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM restaurants")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def count_restaurants(db_path=DEFAULT_DB_PATH):
    """
    retourne le nombre de restaurants dans la base de données
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM restaurants")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# 6 agregation SQL (somme ou moyenne)

def count_with_website(db_path=DEFAULT_DB_PATH):
    """
    retourne le nombre de restaurants avec un site web (website non NULL)
    sql: count(*)where website is not null
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM restaurants WHERE website IS NOT NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def count_without_website(db_path=DEFAULT_DB_PATH):
    """
    retourne le nombre de restaurants sans site web (website NULL)
    sql: count(*)where website is null
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM restaurants WHERE website IS NULL")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def count_by_postcode(db_path=DEFAULT_DB_PATH):
    """
    compte le nombre de restaurent par code postal
    utile pour le graphique (barres par quartier).
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT postcode, COUNT(*) as count
        FROM restaurants
        WHERE postcode IS NOT NULL
        GROUP BY postcode
                
        """)
    rows = cursor.fetchall()
    conn.close()
    return [{"postcode": row["postcode"], "count": row["count"]} for row in rows]

def stats_resume(db_path=DEFAULT_DB_PATH):
    """
    retourne un dictionnaire resume pour le bouton Agregation
    de la fenetre principale

    """
    total = count_restaurants(db_path)
    avec_site = count_with_website(db_path)
    sans_site = count_without_website(db_path)
 
    pourcentage_avec_site = round((avec_site / total) * 100, 1) if total > 0 else 0
 
    return {
        "total_restaurants": total,
        "avec_site_web": avec_site,
        "sans_site_web": sans_site,
        "pourcentage_avec_site": pourcentage_avec_site,
    }

"""
# test 
if __name__ == "__main__":
    # Chemin de test (pas le vrai fichier de l'app)
    TEST_DB = os.path.join(os.path.dirname(__file__), "test_restaurants.db")
 
    # Nettoyage
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
 
    # 1. Créer la table
    create_table(TEST_DB)
    print("Table créée.")
 
    # 2. Insérer des données de test (simulent ce que retourne api_client.py)
    faux_restaurants = [
        {
            "place_id": "abc123",
            "name": "Chez Test",
            "formatted_address": "1 Rue de Test, 75001 Paris",
            "city": "Paris",
            "postcode": "75001",
            "categories": ["catering", "catering.restaurant"],
            "website": "https://cheztest.fr",
            "opening_hours": "Mo-Fr 12:00-14:00",
            "lat": 48.86,
            "lon": 2.34,
        },
        {
            "place_id": "def456",
            "name": "Sans Site",
            "formatted_address": "2 Rue du Vide, 75012 Paris",
            "city": "Paris",
            "postcode": "75012",
            "categories": ["catering", "catering.restaurant"],
            "website": None,
            "opening_hours": None,
            "lat": 48.84,
            "lon": 2.38,
        },
        {
            "place_id": "ghi789",
            "name": "Autre Resto",
            "formatted_address": "3 Rue de Lyon, 69001 Lyon",
            "city": "Lyon",
            "postcode": "69001",
            "categories": ["catering", "catering.restaurant"],
            "website": None,
            "opening_hours": "Mo-Su 11:00-22:00",
            "lat": 45.76,
            "lon": 4.83,
        },
    ]
 
    inseres = insert_restaurants(faux_restaurants, TEST_DB)
    print(f"Restaurants insérés : {inseres}")
 
    # 3. Tester le cas "base non vide" (re-insertion des mêmes données)
    inseres_2 = insert_restaurants(faux_restaurants, TEST_DB)
    print(f"Re-insertion (doublons ignorés) : {inseres_2} nouveaux")
 
    # 4. Lire les données
    tous = get_all_restaurants(TEST_DB)
    print(f"\nRestaurants en base : {len(tous)}")
    for r in tous:
        site = r["website"] if r["website"] else "Pas de site web"
        print(f"  {r['name']} — {site}")
 
    # 5. Agrégations
    print(f"\nStats résumé :")
    stats = stats_resume(TEST_DB)
    print(f"  Total          : {stats['total_restaurants']}")
    print(f"  Avec site web  : {stats['avec_site_web']}")
    print(f"  Sans site web  : {stats['sans_site_web']}")
    print(f"  % avec site    : {stats['pourcentage_avec_site']}%")
 
    # 6. Par code postal
    print(f"\nPar code postal :")
    for p in count_by_postcode(TEST_DB):
        print(f"  {p['postcode']} : {p['count']} restaurants")
 
    # 7. Effacer
    clear_database(TEST_DB)
    print(f"\nAprès effacement : {count_restaurants(TEST_DB)} restaurants")
 
    # Nettoyage fichier de test
    os.remove(TEST_DB)
    print("Fichier de test supprimé.")

    """