"""
Module d'analyse de texte : extraction des paragraphes, comptage de mots,
arrondi à la dizaine et calcul de la distribution des longueurs.
"""

import re
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class TextAnalysisError(Exception):
    """Exception levée en cas d'erreur lors de l'analyse du texte."""
    pass


class TextAnalyzer:
    """Analyse un chapitre pour en extraire des statistiques par paragraphe."""

    def __init__(self):
        self.paragraphs: list[str] = []
        self.word_counts: list[int] = []
        self.rounded_counts: list[int] = []
        self.stats: dict = {}

    def extract_paragraphs(self, text: str) -> list[str]:
        """
        Extrait les paragraphes d'un texte (blocs séparés par une ou
        plusieurs lignes vides), en filtrant les lignes trop courtes
        (titres, numéros de page, etc.).

        Args:
            text: Texte brut à analyser

        Returns:
            Liste des paragraphes non vides.

        Raises:
            TextAnalysisError: si aucun paragraphe exploitable n'est trouvé.
        """
        if not text or not text.strip():
            raise TextAnalysisError("Le texte fourni est vide.")

        raw_paragraphs = re.split(r"\n\s*\n+", text)

        cleaned = []
        for para in raw_paragraphs:
            # Remettre les retours à la ligne internes en espaces (un paragraphe = une ligne logique)
            normalized = " ".join(para.split())

            # Ignorer les lignes-titres (entièrement en majuscules, ex: nom
            # de l'auteur du conte ou titre du conte/chapitre lui-même).
            if normalized and normalized.isupper() and len(normalized) <= 60:
                continue

            # On ignore aussi les lignes très courtes : probablement des
            # numéros de page ("Page 8") ou artefacts de mise en page.
            if normalized and len(normalized.split()) >= 4:
                cleaned.append(normalized)

        if not cleaned:
            raise TextAnalysisError("Aucun paragraphe exploitable trouvé dans le texte.")

        self.paragraphs = cleaned
        logger.info(f"Extraction de {len(cleaned)} paragraphes")
        return cleaned

    def count_words_per_paragraph(self, paragraphs: list[str] = None) -> list[int]:
        """
        Compte le nombre de mots de chaque paragraphe.

        Args:
            paragraphs: Liste de paragraphes. Si None, utilise self.paragraphs.

        Returns:
            Liste du nombre de mots par paragraphe.

        Raises:
            TextAnalysisError: si la liste de paragraphes est vide.
        """
        if paragraphs is None:
            paragraphs = self.paragraphs

        if not paragraphs:
            raise TextAnalysisError("Aucun paragraphe à analyser. Appelez extract_paragraphs d'abord.")

        counts = [len(p.split()) for p in paragraphs]
        self.word_counts = counts

        logger.info(
            f"Comptage des mots : min={min(counts)}, max={max(counts)}, "
            f"moyenne={sum(counts) / len(counts):.1f}"
        )
        return counts

    def round_to_nearest_ten(self, counts: list[int] = None) -> list[int]:
        """
        Arrondit chaque valeur à la dizaine la plus proche.
        Exemple : 123 -> 120, 127 -> 130.

        Note : Python utilise l'arrondi "au pair le plus proche" pour les
        cas exactement à mi-chemin (ex: 125 -> 12.5 dizaines). Avec round(),
        125 est arrondi à 120 (12 est pair), et 135 est arrondi à 140
        (14 est pair). C'est le comportement standard de la fonction
        round() de Python (IEEE 754) et non une erreur.

        Args:
            counts: Liste d'entiers. Si None, utilise self.word_counts.

        Returns:
            Liste des valeurs arrondies à la dizaine.
        """
        if counts is None:
            counts = self.word_counts

        if not counts:
            raise TextAnalysisError("Aucune valeur à arrondir.")

        rounded = [round(c / 10) * 10 for c in counts]
        self.rounded_counts = rounded
        logger.info("Arrondissement à la dizaine effectué")
        return rounded

    def get_distribution(self, rounded_counts: list[int] = None) -> dict:
        """
        Construit la distribution : pour chaque longueur arrondie, combien
        de paragraphes ont cette longueur. Triée du plus court au plus long.

        Args:
            rounded_counts: Liste d'entiers arrondis. Si None, utilise self.rounded_counts.

        Returns:
            Dictionnaire {longueur_arrondie: nombre_de_paragraphes}, trié par clé.
        """
        if rounded_counts is None:
            rounded_counts = self.rounded_counts

        if not rounded_counts:
            raise TextAnalysisError("Aucune donnée arrondie disponible pour la distribution.")

        distribution = dict(sorted(Counter(rounded_counts).items()))
        logger.info(f"Distribution calculée sur {len(distribution)} catégories")
        return distribution

    def calculate_statistics(self, word_counts: list[int] = None) -> dict:
        """
        Calcule les statistiques globales sur les paragraphes.

        Args:
            word_counts: Liste du nombre de mots par paragraphe.
                         Si None, utilise self.word_counts.

        Returns:
            Dictionnaire contenant :
            - total_paragraphs
            - total_words
            - min_words
            - max_words
            - avg_words
        """
        if word_counts is None:
            word_counts = self.word_counts

        if not word_counts:
            raise TextAnalysisError("Aucune donnée disponible pour calculer les statistiques.")

        stats = {
            "total_paragraphs": len(word_counts),
            "total_words": sum(word_counts),
            "min_words": min(word_counts),
            "max_words": max(word_counts),
            "avg_words": round(sum(word_counts) / len(word_counts), 2),
        }

        self.stats = stats
        logger.info(f"Statistiques calculées : {stats}")
        return stats

    def analyze_full_chapter(self, chapter_text: str) -> tuple[dict, dict]:
        """
        Exécute l'analyse complète d'un chapitre en une seule méthode :
        extraction des paragraphes, comptage, arrondi, distribution, stats.

        Args:
            chapter_text: Texte du premier chapitre.

        Returns:
            Tuple (distribution, statistiques).
        """
        logger.info("Démarrage de l'analyse complète du chapitre")

        self.extract_paragraphs(chapter_text)
        self.count_words_per_paragraph()
        self.round_to_nearest_ten()
        stats = self.calculate_statistics()
        distribution = self.get_distribution()

        logger.info("Analyse complète du chapitre terminée")
        return distribution, stats
