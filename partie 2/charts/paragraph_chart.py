"""
Module pour créer le graphique de distribution des longueurs de paragraphes
du premier chapitre (matplotlib, sauvegardé en PNG).
"""

import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Backend sans interface graphique (génération de fichiers)
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)


class ChartGenerationError(Exception):
    """Exception levée en cas d'erreur lors de la génération du graphique."""
    pass


class ParagraphDistributionChart:
    """Crée et sauvegarde le graphique en barres de la distribution des paragraphes."""

    def __init__(self, figsize: tuple = (10, 5.5), dpi: int = 110):
        """
        Args:
            figsize: Taille de la figure (largeur, hauteur) en pouces.
            dpi: Résolution de l'image générée.
        """
        self.figsize = figsize
        self.dpi = dpi
        self.fig = None
        self.ax = None

    def create_bar_chart(self, distribution: dict,
                          title: str = "Distribution des longueurs de paragraphes",
                          xlabel: str = "Nombre de mots (arrondi à la dizaine)",
                          ylabel: str = "Nombre de paragraphes") -> None:
        """
        Crée un graphique en barres à partir de la distribution.

        Args:
            distribution: Dictionnaire {longueur_arrondie: nombre_de_paragraphes},
                          trié du plus court au plus long.
            title: Titre du graphique.
            xlabel: Étiquette de l'axe des X.
            ylabel: Étiquette de l'axe des Y.

        Raises:
            ChartGenerationError: si la distribution est vide.
        """
        if not distribution:
            raise ChartGenerationError("La distribution est vide, impossible de créer le graphique.")

        try:
            lengths = list(distribution.keys())
            counts = list(distribution.values())

            self.fig, self.ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

            bars = self.ax.bar(
                range(len(lengths)), counts,
                color="#4472C4", alpha=0.9, edgecolor="#1F3864", linewidth=1
            )

            for bar, count in zip(bars, counts):
                self.ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    str(count), ha="center", va="bottom", fontsize=9, fontweight="bold"
                )

            self.ax.set_xticks(range(len(lengths)))
            self.ax.set_xticklabels(lengths, rotation=0)
            self.ax.set_xlabel(xlabel, fontsize=11, fontweight="bold")
            self.ax.set_ylabel(ylabel, fontsize=11, fontweight="bold")
            self.ax.set_title(title, fontsize=13, fontweight="bold", pad=15)
            self.ax.grid(axis="y", linestyle="--", alpha=0.4)
            self.ax.set_axisbelow(True)

            self.fig.tight_layout()

        except Exception as e:
            logger.error(f"Erreur lors de la création du graphique : {e}")
            raise ChartGenerationError(f"Erreur lors de la création du graphique : {e}")

        logger.info(f"Graphique créé avec {len(lengths)} catégories")

    def save_chart(self, filepath: str) -> None:
        """
        Sauvegarde le graphique courant en PNG.

        Args:
            filepath: Chemin de destination du fichier PNG.

        Raises:
            ChartGenerationError: si aucun graphique n'a été créé, ou en cas
                                   d'échec de sauvegarde.
        """
        if self.fig is None:
            raise ChartGenerationError("Aucun graphique à sauvegarder. Appelez create_bar_chart d'abord.")

        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            self.fig.savefig(filepath, format="png", dpi=self.dpi, bbox_inches="tight")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du graphique : {e}")
            raise ChartGenerationError(f"Impossible de sauvegarder le graphique dans '{filepath}' : {e}")

        logger.info(f"Graphique sauvegardé dans {filepath}")

    def close(self) -> None:
        """Ferme la figure matplotlib pour libérer la mémoire."""
        if self.fig is not None:
            plt.close(self.fig)
            self.fig = None
            self.ax = None

    def generate_and_save(self, distribution: dict, output_path: str,
                           title: str = "Distribution des longueurs de paragraphes") -> str:
        """
        Crée puis sauvegarde le graphique en une seule étape.

        Args:
            distribution: Dictionnaire {longueur_arrondie: nombre_de_paragraphes}.
            output_path: Chemin du fichier PNG de sortie.
            title: Titre du graphique.

        Returns:
            Le chemin du fichier sauvegardé.
        """
        try:
            self.create_bar_chart(distribution, title=title)
            self.save_chart(output_path)
        finally:
            self.close()

        return output_path
