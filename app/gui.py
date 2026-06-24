"""
gui.py
objet : interface graphique principale de l'application (Tkinter).
Connecte tous les autres modules ensemble
- api_client.py => recherche les restaurants via Geoapify Places API
- database.py => stocke / lecture/ agregation


"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import sys
import os
 
# Ajouter le dossier parent au path pour les imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
 
from data.api_client import (
    search_restaurants_by_city,
    search_restaurants_by_radius,
    afficher_site_web,
    GeoapifyAPIError,
)
from data.database import (
    create_table,
    insert_restaurants,
    clear_database,
    get_all_restaurants,
    count_restaurants,
    stats_resume,
    count_by_postcode,
)
from chats.chart_builder import (
    create_pie_website,
    create_bar_by_postcode,
    create_bar_by_category,
)
 
import tkintermapview
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
 
 

#  Cle API (a remplacer par votre vraie cle)

API_KEY = "votre key de api"
 
 

#  Classe principale

 
class RestaurantApp:
    """Application principale de recherche de restaurants."""
 
    def __init__(self, root):
        self.root = root
        self.root.title("🍽️ Restaurant Finder — Projet Python Avancé")
        self.root.geometry("1200x700")
 
        # liste des marqueurs actuels sur la carte
        self.markers = []
        # widget graphique actuellement affiché (pour pouvoir le supprimer)
        self.current_chart_widget = None
 
        # initialiser la base de données
        create_table()
 
        # construire l'interface
        self._create_menu()
        self._create_search_bar()
        self._create_main_area()
        
        self._create_status_bar()
 
        # message de bienvenue
        self.update_status("Prêt. Tapez un nom de ville ou faites clic droit sur la carte.")
 
    #  Menu

 
    def _create_menu(self):
        menu_bar = tk.Menu(self.root)
 
        # Menu Fichier
        menu_fichier = tk.Menu(menu_bar, tearoff=0)
        menu_fichier.add_command(label="Effacer la base de données", command=self.clear_db)
        menu_fichier.add_separator()
        menu_fichier.add_command(label="Quitter", command=self.root.quit)
        menu_bar.add_cascade(label="Fichier", menu=menu_fichier)
 
        # Menu Données
        menu_donnees = tk.Menu(menu_bar, tearoff=0)
        menu_donnees.add_command(label="Charger depuis la base", command=self.load_from_db)
        menu_bar.add_cascade(label="Données", menu=menu_donnees)
 
        # Menu Options
        menu_options = tk.Menu(menu_bar, tearoff=0)
        menu_options.add_command(label="Couleur de fond", command=self.change_bg_color)
        menu_options.add_command(label="Taille de police", command=self.change_font_size)
        menu_bar.add_cascade(label="Options", menu=menu_options)
 
        self.root.config(menu=menu_bar)
 
    #  Barre de recherche

 
    def _create_search_bar(self):
        frame_search = tk.Frame(self.root, pady=5, padx=10)
        frame_search.pack(fill=tk.X)
 
        # champ ville
        tk.Label(frame_search, text="Ville :").pack(side=tk.LEFT)
        self.entry_city = tk.Entry(frame_search, width=25)
        self.entry_city.pack(side=tk.LEFT, padx=5)
        self.entry_city.insert(0, "Paris")
        # appuyer sur Entrée = chercher
        self.entry_city.bind("<Return>", lambda e: self.search_by_city())
 
        # bouton chercher
        btn_search = tk.Button(frame_search, text="🔍 Chercher",
                               command=self.search_by_city)
        btn_search.pack(side=tk.LEFT, padx=5)
 
        # champ rayon
        tk.Label(frame_search, text="Rayon (m) :").pack(side=tk.LEFT, padx=(20, 0))
        self.entry_radius = tk.Entry(frame_search, width=8)
        self.entry_radius.pack(side=tk.LEFT, padx=5)
        self.entry_radius.insert(0, "2000")
 
        # champ limite
        tk.Label(frame_search, text="Limite :").pack(side=tk.LEFT, padx=(20, 0))
        self.entry_limit = tk.Entry(frame_search, width=5)
        self.entry_limit.pack(side=tk.LEFT, padx=5)
        self.entry_limit.insert(0, "20")
 
    #  Zone principale : carte + liste

 
    def _create_main_area(self):
        frame_main = tk.Frame(self.root)
        frame_main.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # --- Colonne gauche : carte ---
        frame_map = tk.LabelFrame(frame_main, text="Carte (clic droit = chercher ici)")
        frame_map.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.map_widget = tkintermapview.TkinterMapView(
            frame_map, width=550, height=500, corner_radius=0
        )
        self.map_widget.pack(fill=tk.BOTH, expand=True)
        self.map_widget.set_position(48.8566, 2.3522)
        self.map_widget.set_zoom(13)

        self.map_widget.add_right_click_menu_command(
            label="Chercher les restaurants ici",
            command=self.search_at_coords,
            pass_coords=True,
        )

        # --- Colonne droite ---
        self.frame_right = tk.Frame(frame_main, width=500)
        self.frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # Treeview (liste des restaurants)
        frame_list = tk.LabelFrame(self.frame_right, text="Restaurants")
        frame_list.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "address", "website", "hours")
        self.tree = ttk.Treeview(frame_list, columns=columns, show="headings", height=12)
        self.tree.heading("name", text="Nom")
        self.tree.heading("address", text="Adresse")
        self.tree.heading("website", text="Site web")
        self.tree.heading("hours", text="Horaires")

        self.tree.column("name", width=120)
        self.tree.column("address", width=180)
        self.tree.column("website", width=120)
        self.tree.column("hours", width=100)

        scrollbar = ttk.Scrollbar(frame_list, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Boutons (toujours visibles entre la liste et le graphique)
        frame_btn = tk.Frame(self.frame_right)
        frame_btn.pack(fill=tk.X, pady=5)

        tk.Button(frame_btn, text="Stats (SQL)",
                command=self.show_stats).pack(side=tk.LEFT, padx=3)
        tk.Button(frame_btn, text="Site web (camembert)",
                command=self.show_pie_chart).pack(side=tk.LEFT, padx=3)
        tk.Button(frame_btn, text="Par code postal",
                command=self.show_bar_chart).pack(side=tk.LEFT, padx=3)
        tk.Button(frame_btn, text="Types de cuisine",
                command=self.show_category_chart).pack(side=tk.LEFT, padx=3)

        # Zone graphique (sous les boutons)
        self.frame_chart = tk.Frame(self.frame_right)
        self.frame_chart.pack(fill=tk.BOTH, expand=True)

    #  Boutons Stats et Graphique

 
    def _create_buttons(self):
        frame_btn = tk.Frame(self.root, pady=5)
        frame_btn.pack(fill=tk.X, padx=10)
 
        tk.Button(frame_btn, text="📊 Statistiques (agrégation SQL)",
                  command=self.show_stats).pack(side=tk.LEFT, padx=5)
 
        tk.Button(frame_btn, text="🥧 Graphique : site web",
                  command=self.show_pie_chart).pack(side=tk.LEFT, padx=5)
 
        tk.Button(frame_btn, text="📈 Graphique : par code postal",
                  command=self.show_bar_chart).pack(side=tk.LEFT, padx=5)
 
        tk.Button(frame_btn, text="🍽️ Graphique : types de cuisine",
                  command=self.show_category_chart).pack(side=tk.LEFT, padx=5)
 
   
    #  Barre d'état

 
    def _create_status_bar(self):
        self.status_var = tk.StringVar()
        status_bar = tk.Label(
            self.root, textvariable=self.status_var,
            bd=1, relief=tk.SUNKEN, anchor=tk.W, padx=10
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
 
    def update_status(self, message):
        """Met à jour le texte de la barre d'état."""
        self.status_var.set(message)
        self.root.update_idletasks()
 
    
    #  Recherche par nom de ville

 
    def search_by_city(self):
        city = self.entry_city.get().strip()
        if not city:
            messagebox.showwarning("Attention", "Veuillez entrer un nom de ville.")
            return
 
        radius = self._get_radius()
        limit = self._get_limit()
 
        self.update_status(f"Recherche des restaurants autour de '{city}'...")
 
        try:
            result = search_restaurants_by_city(
                api_key=API_KEY,
                city_name=city,
                radius_meters=radius,
                limit=limit,
            )
        except GeoapifyAPIError as e:
            messagebox.showerror("Erreur API", str(e))
            self.update_status(f"Erreur : {e}")
            return
 
        restaurants = result["restaurants"]
        city_info = result["city_info"]
 
        # centrer la carte sur la ville trouvée
        self.map_widget.set_position(city_info["lat"], city_info["lon"])
        self.map_widget.set_zoom(14)
 
        self._process_results(restaurants)
 
    
    #  Recherche par clic droit sur la carte
  
 
    def search_at_coords(self, coords):
        """Appelée quand l'utilisateur fait clic droit → 'Chercher ici'."""
        lat, lon = coords
        radius = self._get_radius()
        limit = self._get_limit()
 
        self.update_status(f"Recherche autour de ({lat:.4f}, {lon:.4f})...")
 
        try:
            restaurants = search_restaurants_by_radius(
                api_key=API_KEY,
                lon=lon,
                lat=lat,
                radius_meters=radius,
                limit=limit,
            )
        except GeoapifyAPIError as e:
            messagebox.showerror("Erreur API", str(e))
            self.update_status(f"Erreur : {e}")
            return
 
        self._process_results(restaurants)
 
    #  Traitement des résultats (commun aux deux modes de recherche)
  
 
    def _process_results(self, restaurants):
        """Affiche les résultats dans la liste et sur la carte, et les sauvegarde en base."""
        if not restaurants:
            messagebox.showinfo("Résultat", "Aucun restaurant trouvé dans cette zone.")
            self.update_status("Aucun restaurant trouvé.")
            return
 
        # sauvegarder en base
        nb_new = insert_restaurants(restaurants)
        total = count_restaurants()
 
        # afficher dans le Treeview
        self._update_treeview(restaurants)
 
        # afficher les marqueurs sur la carte
        self._update_markers(restaurants)
 
        self.update_status(
            f"{len(restaurants)} restaurants trouvés, {nb_new} nouveaux en base "
            f"(total en base : {total}). Données © OpenStreetMap contributors."
        )
 
    def _update_treeview(self, restaurants):
        """Remplit le Treeview avec la liste de restaurants."""
        # vider l'ancien contenu
        for item in self.tree.get_children():
            self.tree.delete(item)
 
        for r in restaurants:
            self.tree.insert("", tk.END, values=(
                r.get("name", ""),
                r.get("formatted_address", ""),
                afficher_site_web(r),
                r.get("opening_hours") or "Non renseigné",
            ))
 
    def _update_markers(self, restaurants):
        """Place des marqueurs sur la carte pour chaque restaurant."""
        # supprimer les anciens marqueurs
        for marker in self.markers:
            marker.delete()
        self.markers.clear()
 
        for r in restaurants:
            lat = r.get("lat")
            lon = r.get("lon")
            name = r.get("name", "")
            if lat and lon:
                marker = self.map_widget.set_marker(lat, lon, text=name)
                self.markers.append(marker)
 
    
    #  Charger depuis la base (menu Données)
 
 
    def load_from_db(self):
        """Charge et affiche les restaurants déjà en base."""
        restaurants = get_all_restaurants()
        if not restaurants:
            messagebox.showinfo("Base vide", "Aucun restaurant en base de données.")
            return
 
        self._update_treeview(restaurants)
        self._update_markers(restaurants)
        self.update_status(f"{len(restaurants)} restaurants chargés depuis la base.")
 

    #  Effacer la base (menu Fichier)

 
    def clear_db(self):
        """Efface la base avec confirmation."""
        reponse = messagebox.askyesno(
            "Confirmation",
            "Voulez-vous vraiment supprimer TOUS les restaurants ?\n"
            "Cette action est irréversible."
        )
        if reponse:
            clear_database()
            # vider le Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
            # supprimer les marqueurs
            for marker in self.markers:
                marker.delete()
            self.markers.clear()
            self.update_status("Base de données vidée.")
 

    #  statistiques / agregation SQL (bouton)

 
    def show_stats(self):
        """Affiche un résumé des statistiques (agrégation SQL)."""
        total = count_restaurants()
        if total == 0:
            messagebox.showinfo("Stats", "Aucune donnée en base.")
            return
 
        stats = stats_resume()
        message = (
            f"📊 Statistiques (requêtes SQL d'agrégation)\n"
            f"{'─' * 40}\n"
            f"Total restaurants en base : {stats['total_restaurants']}\n"
            f"Avec site web : {stats['avec_site_web']}\n"
            f"Sans site web : {stats['sans_site_web']}\n"
            f"% avec site web : {stats['pourcentage_avec_site']}%\n"
        )
        messagebox.showinfo("Statistiques", message)
        self.update_status("Statistiques affichées.")
 

    #  Graphiques (boutons)

 
    def _display_chart(self, fig):
        """Affiche un graphique matplotlib dans la zone dédiée, avec un bouton pour le fermer."""
        # supprimer le graphique précédent si il existe
        self.close_chart()

        # bouton pour fermer le graphique
        self.btn_close_chart = tk.Button(
            self.frame_chart,
            text="❌ Fermer le graphique",
            command=self.close_chart,
            bg="#F44336",
            fg="white",
        )
        self.btn_close_chart.pack(pady=2)

        # afficher le graphique
        canvas = FigureCanvasTkAgg(fig, master=self.frame_chart)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.current_chart_widget = canvas
        
    def close_chart(self):
        """Ferme le graphique et libère l'espace."""
        if self.current_chart_widget:
            self.current_chart_widget.get_tk_widget().destroy()
            self.current_chart_widget = None
        if hasattr(self, "btn_close_chart") and self.btn_close_chart:
            self.btn_close_chart.destroy()
            self.btn_close_chart = None


    def show_pie_chart(self):
        """Graphique camembert : avec site web vs sans."""
        if count_restaurants() == 0:
            messagebox.showinfo("Graphique", "Aucune donnée en base.")
            return
        stats = stats_resume()
        fig = create_pie_website(stats)
        self._display_chart(fig)
        self.update_status("Graphique camembert affiché.")
 
    def show_bar_chart(self):
        """Graphique barres : restaurants par code postal."""
        if count_restaurants() == 0:
            messagebox.showinfo("Graphique", "Aucune donnée en base.")
            return
        data = count_by_postcode()
        fig = create_bar_by_postcode(data)
        self._display_chart(fig)
        self.update_status("Graphique par code postal affiché.")
 
    def show_category_chart(self):
        """Graphique barres : types de cuisine."""
        restaurants = get_all_restaurants()
        if not restaurants:
            messagebox.showinfo("Graphique", "Aucune donnée en base.")
            return
        fig = create_bar_by_category(restaurants)
        self._display_chart(fig)
        self.update_status("Graphique par catégorie affiché.")
 

    #  Options (menu)

 
    def change_bg_color(self):
        """Permet de changer la couleur de fond de la fenêtre."""
        color = colorchooser.askcolor(title="Couleur de fond")
        if color[1]:
            self.root.configure(bg=color[1])
            self.update_status(f"Couleur de fond changée en {color[1]}")
 
    def change_font_size(self):
        """Permet de changer la taille de police du Treeview."""
        popup = tk.Toplevel(self.root)
        popup.title("Taille de police")
        popup.geometry("250x100")
 
        tk.Label(popup, text="Nouvelle taille :").pack(pady=5)
        entry = tk.Entry(popup, width=5)
        entry.insert(0, "10")
        entry.pack()
 
        def apply():
            try:
                size = int(entry.get())
                style = ttk.Style()
                style.configure("Treeview", font=("Arial", size))
                style.configure("Treeview.Heading", font=("Arial", size, "bold"))
                self.update_status(f"Taille de police changée à {size}")
                popup.destroy()
            except ValueError:
                messagebox.showerror("Erreur", "Entrez un nombre valide.")
 
        tk.Button(popup, text="Appliquer", command=apply).pack(pady=5)
 

    #  Utilitaires

 
    def _get_radius(self):
        """Lit le rayon depuis le champ de saisie."""
        try:
            return int(self.entry_radius.get())
        except ValueError:
            return 2000
 
    def _get_limit(self):
        """Lit la limite depuis le champ de saisie."""
        try:
            return int(self.entry_limit.get())
        except ValueError:
            return 20
 

#  Lancement direct (pour tester)

 
if __name__ == "__main__":
    root = tk.Tk()
    app = RestaurantApp(root)
    root.mainloop()