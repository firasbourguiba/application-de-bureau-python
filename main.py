"""
main.py — Point d'entrée de l'application Restaurant Finder.

Lance l'interface graphique Tkinter.
Exécuter depuis la racine du projet :
    python main.py
"""

import tkinter as tk
from app.gui import RestaurantApp


def main():
    root = tk.Tk()
    app = RestaurantApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()