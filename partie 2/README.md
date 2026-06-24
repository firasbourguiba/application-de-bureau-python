# Partie 2 — Rapport Word généré à partir d'un livre

Application **Tkinter** qui analyse le premier chapitre d'un livre et génère
automatiquement un rapport Word illustré.

## Logique des sources de données

| Élément          | Source                                   |
|-------------------|-------------------------------------------|
| Livre             | Fichier **.txt local** (sélectionné via "Parcourir...") |
| Logo (image n°2)  | Fichier image **local** (sélectionné via "Parcourir...") |
| Image n°1         | **Téléchargée depuis une URL** (champ modifiable, valeur par défaut fournie) |

Cette logique est volontaire et correspond aux exigences du sujet : le livre
et le logo doivent être fournis localement par l'utilisateur, alors que
l'image liée au contenu du livre est récupérée sur Internet pendant
l'exécution.

## Structure du projet

```
part2/
├── app/
│   └── gui.py                 # Interface Tkinter (point d'orchestration)
├── book/
│   ├── gutenberg_client.py    # Chargement .txt local + extraction titre/auteur/chapitre 1
│   └── text_analyzer.py       # Comptage de mots par paragraphe, arrondi, distribution
├── images/
│   ├── image_processor.py     # Téléchargement URL + recadrage/redimensionnement (image n°1)
│   └── image_merger.py        # Chargement logo local (N&B) + rotation + collage
├── charts/
│   └── paragraph_chart.py     # Graphique de distribution des longueurs de paragraphes
├── report/
│   └── word_generator.py      # Génération du document Word (page de titre + page graphique)
├── tests/
│   └── test_part2.py          # 44 tests unitaires
├── resources/
│   └── logo.png                # Logo de démonstration (noir et blanc)
├── output/                     # Fichiers générés (image fusionnée, graphique, rapport .docx)
├── main.py                     # Point d'entrée : lance l'interface Tkinter
└── requirements.txt
```

## Installation

```bash
cd part2
pip install -r requirements.txt
```

Dépendances : `requests`, `Pillow`, `matplotlib`, `python-docx` (Tkinter fait
partie de la bibliothèque standard de Python).

## Lancement

```bash
python main.py
```

## Utilisation (dans l'ordre)

1. **Sélectionner le livre** : cliquer sur "Parcourir..." en face de "Livre
   (.txt local)" et choisir un fichier texte Project Gutenberg
   (ex : `pg12949.txt`, fourni à titre d'exemple).
2. **Sélectionner le logo** : cliquer sur "Parcourir..." en face de "Logo
   (image locale)" et choisir une image (idéalement en noir et blanc).
   Un logo de démonstration est fourni dans `resources/logo.png`.
3. **Vérifier/modifier l'URL de l'image** du livre (un exemple par défaut
   est pré-rempli).
4. **Saisir votre nom** dans le champ "Votre nom (rapport)".
5. Cliquer sur **"Charger et analyser le livre"** : extrait le titre,
   l'auteur, le premier chapitre, calcule les statistiques par paragraphe,
   et **affiche immédiatement le graphique de distribution directement dans
   la fenêtre principale** (section 3, à droite).
6. Cliquer sur **"Télécharger et fusionner l'image"** : télécharge l'image
   n°1, la recadre/redimensionne, charge le logo local, le pivote, puis le
   colle sur l'image. Un aperçu s'affiche dans l'interface (section 3, à
   gauche).
7. Cliquer sur **"Générer le rapport Word"** : régénère le graphique pour
   l'export PNG, puis génère `output/rapport_livre.docx`.

Le journal en bas de fenêtre affiche le détail de chaque étape (y compris
la taille du fichier livre, le nombre de caractères lus, la longueur du
chapitre extrait — utile pour diagnostiquer un fichier incomplet ou mal
sélectionné), et la barre de statut résume l'opération en cours.

## Gestion des erreurs

Chaque module définit ses propres exceptions (`BookLoadError`,
`TextAnalysisError`, `ImageProcessingError`, `ImageMergeError`,
`ChartGenerationError`, `WordGenerationError`). L'interface les intercepte
toutes et affiche un message clair à l'utilisateur (boîte de dialogue +
journal), sans jamais faire planter l'application : fichier introuvable,
URL invalide, pas de connexion réseau, image corrompue, etc.

Le téléchargement de l'image se fait dans un thread séparé pour ne pas
geler l'interface pendant l'attente réseau.

## Tests unitaires

```bash
cd part2
python -m unittest tests.test_part2 -v
```

44 tests couvrant tous les modules : chargement et parsing du livre,
analyse de texte, téléchargement et traitement d'image (avec mock réseau),
fusion de logo, génération de graphique, génération du document Word.

## Notes techniques

- **Arrondi à la dizaine** : utilise `round()` natif de Python, qui suit la
  convention IEEE 754 "round half to even" (125 → 120, car 12 est pair ;
  135 → 140, car 14 est pair). Ce n'est pas une erreur, c'est documenté
  dans `text_analyzer.py`.
- **Détection du premier chapitre** : gère à la fois les romans classiques
  (marqueurs `CHAPTER I` / `CHAPITRE I`) et les recueils de nouvelles (le
  premier titre de conte apparaissant deux fois — une fois dans la table
  des matières, une fois en tête du texte réel).
- **Logo en noir et blanc** : converti automatiquement en niveaux de gris ;
  le fond blanc est rendu transparent pour un collage propre sur l'image.
