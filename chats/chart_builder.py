""""
chart_builder.py
objectif : generer des graphiques (matplotlib) à partir des données
stockées dans la base SQLite (database.py).

- ajouter un bouton pour afficher les do,,es sous forme  de graphique
- le graphe doit etre place dans la fenetre principale
"""


import matplotlib
matplotlib.use("Agg")  # backend sans interface, compatible Tkinter
from matplotlib.figure import Figure

#graphique  1 : les restaurnet avec site web vs sans site web (camembert)
def create_pie_website(stats):
    """
    cree un graphique camember (pie chart) montrant la proportion
    de restaurant avec et sans site web.
    stats : dict
        Dictionnaire retourné par database.stats_resume(), contenant :
        - "avec_site_web" : int
        - "sans_site_web" : int
    """

    avec = stats.get("avec_site_web", 0)
    sans = stats.get("sans_site_web", 0)

    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)

    if avec + sans == 0:
        ax.text(0.5, 0.5, "Aucune donnée en base",
                ha="center", va="center", fontsize=14)
        return fig
 
    labels = [f"Avec site web ({avec})", f"Sans site web ({sans})"]
    values = [avec, sans]
    colors = ["#4CAF50", "#F44336"]
 
    ax.pie(values, labels=labels, colors=colors,
           autopct="%1.1f%%", startangle=90)
    ax.set_title("Restaurants : site web ou non ?")
 
    return fig

# 2 graphique barres : nombre de restaurants par code postal
def create_bar_by_postcode(data_postcode):
    """
    Crée un graphique en barres montrant le nombre de restaurants
    par code postal.
 
    Parametres : 
    
    data_postcode : list[dict]
        Liste retournée par database.count_by_postcode(),
        chaque dict contient : {"postcode": str, "count": int}
    """
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
 
    if not data_postcode:
        ax.text(0.5, 0.5, "Aucune donnée en base",
                ha="center", va="center", fontsize=14)
        return fig
 
    postcodes = [d["postcode"] for d in data_postcode]
    counts = [d["count"] for d in data_postcode]
 
    bars = ax.bar(postcodes, counts, color="#2196F3")
 
    # afficher le nombre au dessus de chaque barre
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
                str(count), ha="center", va="bottom", fontsize=9)
 
    ax.set_xlabel("Code postal")
    ax.set_ylabel("Nombre de restaurants")
    ax.set_title("Restaurants par code postal")
 
    # rotation des labels si il y en a beaucoup
    if len(postcodes) > 5:
        ax.tick_params(axis="x", rotation=45)
 
    fig.tight_layout()
    return fig
 #3 graphique barres : top restaurants par catégorie

def create_bar_by_category(restaurants):
    """
    Cree un graphique en barres des catégories de cuisine
    les plus fréquentes.
 
    Paramètres
    ----------
    restaurants : list[dict]
        Liste retournée par database.get_all_restaurants()
    """
    fig = Figure(figsize=(6, 4), dpi=100)
    ax = fig.add_subplot(111)
 
    if not restaurants:
        ax.text(0.5, 0.5, "Aucune donnée en base",
                ha="center", va="center", fontsize=14)
        return fig
 
    # compter les catégories (on garde seulement celles qui contiennent "catering.restaurant.")
    compteur = {}
    for r in restaurants:
        categories = r.get("categories", "")
        if isinstance(categories, str):
            categories = categories.split(", ")
        for cat in categories:
            # garder seulement les sous-catégories spécifiques
            if cat.startswith("catering.restaurant."):
                nom_court = cat.replace("catering.restaurant.", "")
                compteur[nom_court] = compteur.get(nom_court, 0) + 1
 
    if not compteur:
        ax.text(0.5, 0.5, "Pas de catégories spécifiques",
                ha="center", va="center", fontsize=14)
        return fig
 
    # trier par fréquence et garder le top 10
    tri = sorted(compteur.items(), key=lambda x: x[1], reverse=True)[:10]
    noms = [item[0] for item in tri]
    valeurs = [item[1] for item in tri]
 
    bars = ax.barh(noms, valeurs, color="#FF9800")
 
    for bar, val in zip(bars, valeurs):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), ha="left", va="center", fontsize=9)
 
    ax.set_xlabel("Nombre de restaurants")
    ax.set_title("Types de cuisine les plus fréquents")
    ax.invert_yaxis()
 
    fig.tight_layout()
    return fig
"""
# test 
if __name__ == "__main__":
    # Test avec des fausses données (pas besoin de la vraie base)
 
    # Test 1 : camembert
    faux_stats = {"avec_site_web": 8, "sans_site_web": 12}
    fig1 = create_pie_website(faux_stats)
    fig1.savefig("test_pie.png")
    print("test_pie.png créé ")
 
    # Test 2 : barres par code postal
    faux_postcodes = [
        {"postcode": "75001", "count": 5},
        {"postcode": "75012", "count": 8},
        {"postcode": "75011", "count": 3},
        {"postcode": "69001", "count": 6},
    ]
    fig2 = create_bar_by_postcode(faux_postcodes)
    fig2.savefig("test_bar_postcode.png")
    print("test_bar_postcode.png créé ")
 
    # Test 3 : barres par catégorie
    faux_restaurants = [
        {"categories": "catering, catering.restaurant, catering.restaurant.french"},
        {"categories": "catering, catering.restaurant, catering.restaurant.french"},
        {"categories": "catering, catering.restaurant, catering.restaurant.asian"},
        {"categories": "catering, catering.restaurant, catering.restaurant.italian"},
        {"categories": "catering, catering.restaurant, catering.restaurant.italian"},
        {"categories": "catering, catering.restaurant, catering.restaurant.italian"},
        {"categories": "catering, catering.restaurant"},
    ]
    fig3 = create_bar_by_category(faux_restaurants)
    fig3.savefig("test_bar_category.png")
    print("test_bar_category.png créé ")
 
    print("\nOuvrez les 3 images .png pour vérifier visuellement.")
    """