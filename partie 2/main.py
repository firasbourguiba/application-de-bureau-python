"""
Point d'entrée principal de la Partie 2.

Lance l'interface Tkinter permettant de :
1. Charger un livre depuis un fichier .txt local et l'analyser
2. Télécharger une image depuis une URL et la fusionner avec un logo local
3. Générer un rapport Word complet (page de titre + page d'analyse/graphique)

Usage :
    python main.py
"""

import logging
import sys
from pathlib import Path

# Permet d'exécuter "python main.py" depuis le dossier part2/ en trouvant
# les modules book/, images/, charts/, report/, app/.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tkinter import Tk
from app.gui import Part2App


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    root = Tk()
    Part2App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
