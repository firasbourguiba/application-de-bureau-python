""""
teste qui couvre :xtraction de données, affichage site web
- data (CRUD, agrégations SQL)

"""


import unittest
import os
import sys
 
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
from data.api_client import _extraire_restaurant, afficher_site_web
from data.database import (
    create_table,
    insert_restaurants,
    clear_database,
    get_all_restaurants,
    count_restaurants,
    count_with_website,
    count_without_website,
    count_by_postcode,
    stats_resume,
)
from chats.chart_builder import (
    create_pie_website,
    create_bar_by_postcode,
    create_bar_by_category,
)

# des fake donnees 
FAKE_PROPERTIES_WITH_SITE = {
    "place_id": "abc123",
    "name": "Chez Test",
    "formatted": "1 Rue de Test, 75001 Paris",
    "city": "Paris",
    "postcode": "75001",
    "categories": ["catering", "catering.restaurant", "catering.restaurant.french"],
    "website": "https://cheztest.fr",
    "opening_hours": "Mo-Fr 12:00-14:00",
    "lat": 48.86,
    "lon": 2.34,
}
 
FAKE_PROPERTIES_WITHOUT_SITE = {
    "place_id": "def456",
    "name": "Sans Site",
    "formatted": "2 Rue du Vide, 75012 Paris",
    "city": "Paris",
    "postcode": "75012",
    "categories": ["catering", "catering.restaurant"],
    "opening_hours": None,
    "lat": 48.84,
    "lon": 2.38,
}
 
FAKE_PROPERTIES_MINIMAL = {
    "place_id": "ghi789",
}
 
TEST_DB = os.path.join(os.path.dirname(__file__), "test_temp.db")
 
 
def _fake_restaurants():
    """Retourne une liste de restaurants comme api_client les retournerait"""
    return [
        _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE),
        _extraire_restaurant(FAKE_PROPERTIES_WITHOUT_SITE),
    ]



# test api 


class TestExtraireRestaurant(unittest.TestCase):
    """Tests pour la fonction _extraire_restaurant."""
 
    def test_extraction_complete(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertEqual(result["name"], "Chez Test")
        self.assertEqual(result["place_id"], "abc123")
        self.assertEqual(result["formatted_address"], "1 Rue de Test, 75001 Paris")
        self.assertEqual(result["city"], "Paris")
        self.assertEqual(result["postcode"], "75001")
        self.assertEqual(result["website"], "https://cheztest.fr")
        self.assertEqual(result["opening_hours"], "Mo-Fr 12:00-14:00")
        self.assertEqual(result["lat"], 48.86)
        self.assertEqual(result["lon"], 2.34)
 
    def test_extraction_sans_site_web(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITHOUT_SITE)
        self.assertIsNone(result["website"])
 
    def test_extraction_donnees_minimales(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_MINIMAL)
        self.assertEqual(result["name"], "Nom inconnu")
        self.assertIsNone(result["city"])
        self.assertIsNone(result["website"])
        self.assertEqual(result["categories"], [])
 
    def test_extraction_retourne_dict(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertIsInstance(result, dict)
 
    def test_categories_est_une_liste(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertIsInstance(result["categories"], list)
        self.assertIn("catering.restaurant.french", result["categories"])
 
 
class TestAfficherSiteWeb(unittest.TestCase):
    """Tests pour la fonction afficher_site_web."""
 
    def test_avec_site(self):
        r = {"website": "https://example.com"}
        self.assertEqual(afficher_site_web(r), "https://example.com")
 
    def test_sans_site_none(self):
        r = {"website": None}
        self.assertEqual(afficher_site_web(r), "Pas de site web")
 
    def test_sans_cle_website(self):
        r = {}
        self.assertEqual(afficher_site_web(r), "Pas de site web")
 
    def test_site_vide(self):
        r = {"website": ""}
        self.assertEqual(afficher_site_web(r), "Pas de site web")
 

 # test pour les database 
 
class TestExtraireRestaurant(unittest.TestCase):
    """Tests pour la fonction _extraire_restaurant."""
 
    def test_extraction_complete(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertEqual(result["name"], "Chez Test")
        self.assertEqual(result["place_id"], "abc123")
        self.assertEqual(result["formatted_address"], "1 Rue de Test, 75001 Paris")
        self.assertEqual(result["city"], "Paris")
        self.assertEqual(result["postcode"], "75001")
        self.assertEqual(result["website"], "https://cheztest.fr")
        self.assertEqual(result["opening_hours"], "Mo-Fr 12:00-14:00")
        self.assertEqual(result["lat"], 48.86)
        self.assertEqual(result["lon"], 2.34)
 
    def test_extraction_sans_site_web(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITHOUT_SITE)
        self.assertIsNone(result["website"])
 
    def test_extraction_donnees_minimales(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_MINIMAL)
        self.assertEqual(result["name"], "Nom inconnu")
        self.assertIsNone(result["city"])
        self.assertIsNone(result["website"])
        self.assertEqual(result["categories"], [])
 
    def test_extraction_retourne_dict(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertIsInstance(result, dict)
 
    def test_categories_est_une_liste(self):
        result = _extraire_restaurant(FAKE_PROPERTIES_WITH_SITE)
        self.assertIsInstance(result["categories"], list)
        self.assertIn("catering.restaurant.french", result["categories"])
 
 
class TestAfficherSiteWeb(unittest.TestCase):
    """Tests pour la fonction afficher_site_web."""
 
    def test_avec_site(self):
        r = {"website": "https://example.com"}
        self.assertEqual(afficher_site_web(r), "https://example.com")
 
    def test_sans_site_none(self):
        r = {"website": None}
        self.assertEqual(afficher_site_web(r), "Pas de site web")
 
    def test_sans_cle_website(self):
        r = {}
        self.assertEqual(afficher_site_web(r), "Pas de site web")
 
    def test_site_vide(self):
        r = {"website": ""}
        self.assertEqual(afficher_site_web(r), "Pas de site web")


        #  Tests chart
        
class TestChartBuilder(unittest.TestCase):
    """Tests pour le module chart_builder.py."""
 
    def test_pie_website_retourne_figure(self):
        from matplotlib.figure import Figure
        stats = {"avec_site_web": 5, "sans_site_web": 10}
        fig = create_pie_website(stats)
        self.assertIsInstance(fig, Figure)
 
    def test_pie_website_base_vide(self):
        from matplotlib.figure import Figure
        stats = {"avec_site_web": 0, "sans_site_web": 0}
        fig = create_pie_website(stats)
        self.assertIsInstance(fig, Figure)
 
    def test_bar_postcode_retourne_figure(self):
        from matplotlib.figure import Figure
        data = [{"postcode": "75001", "count": 3}]
        fig = create_bar_by_postcode(data)
        self.assertIsInstance(fig, Figure)
 
    def test_bar_postcode_liste_vide(self):
        from matplotlib.figure import Figure
        fig = create_bar_by_postcode([])
        self.assertIsInstance(fig, Figure)
 
    def test_bar_category_retourne_figure(self):
        from matplotlib.figure import Figure
        restaurants = [
            {"categories": "catering, catering.restaurant, catering.restaurant.french"},
            {"categories": "catering, catering.restaurant, catering.restaurant.italian"},
        ]
        fig = create_bar_by_category(restaurants)
        self.assertIsInstance(fig, Figure)
 
    def test_bar_category_liste_vide(self):
        from matplotlib.figure import Figure
        fig = create_bar_by_category([])
        self.assertIsInstance(fig, Figure)

        # lancement 
 
if __name__ == "__main__":
    unittest.main(verbosity=2)