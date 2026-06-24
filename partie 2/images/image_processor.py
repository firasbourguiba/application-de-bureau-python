"""
Module pour télécharger une image depuis une URL (image n°1 du livre)
et la traiter : recadrage et redimensionnement.
"""

import logging
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class ImageProcessingError(Exception):
    """Exception levée en cas d'erreur de téléchargement ou de traitement d'image."""
    pass


class ImageProcessor:
    """Télécharge depuis une URL et traite (recadre/redimensionne) une image."""

    def __init__(self, timeout: int = 10):
        """
        Args:
            timeout: Délai d'attente maximal pour la requête HTTP (secondes).
        """
        self.timeout = timeout

    def download_image(self, url: str) -> Image.Image:
        """
        Télécharge une image depuis une URL (Image n°1, liée au livre).

        Args:
            url: URL de l'image à télécharger.

        Returns:
            Image PIL en mode RGB.

        Raises:
            ImageProcessingError: en cas d'échec réseau ou de contenu invalide.
        """
        if not url or not url.strip():
            raise ImageProcessingError("L'URL de l'image est vide.")

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Projet Python Avance)"}
            response = requests.get(url, timeout=self.timeout, headers=headers)
            response.raise_for_status()
        except requests.Timeout:
            logger.error(f"Timeout lors du téléchargement de {url}")
            raise ImageProcessingError(f"Délai dépassé pour télécharger l'image depuis : {url}")
        except requests.ConnectionError:
            logger.error(f"Erreur de connexion pour {url}")
            raise ImageProcessingError(f"Impossible de se connecter pour télécharger : {url}")
        except requests.HTTPError as e:
            logger.error(f"Erreur HTTP pour {url} : {e}")
            raise ImageProcessingError(f"Erreur HTTP ({response.status_code}) lors du téléchargement de l'image.")
        except requests.RequestException as e:
            logger.error(f"Erreur réseau pour {url} : {e}")
            raise ImageProcessingError(f"Erreur réseau lors du téléchargement de l'image : {e}")

        try:
            image = Image.open(BytesIO(response.content))
            image.load()
            image = image.convert("RGB")
        except UnidentifiedImageError:
            logger.error(f"Contenu non reconnu comme image : {url}")
            raise ImageProcessingError("Le contenu téléchargé n'est pas une image valide.")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture de l'image téléchargée : {e}")
            raise ImageProcessingError(f"Impossible de traiter l'image téléchargée : {e}")

        logger.info(f"Image téléchargée depuis {url} ({image.size[0]}x{image.size[1]})")
        return image

    def crop_image(self, image: Image.Image, box: tuple) -> Image.Image:
        """
        Recadre une image selon une boîte (left, top, right, bottom).

        Args:
            image: Image PIL source.
            box: Tuple (left, top, right, bottom) en pixels.

        Returns:
            Image recadrée.

        Raises:
            ImageProcessingError: si la boîte est invalide.
        """
        left, top, right, bottom = box
        width, height = image.size

        if left < 0 or top < 0 or right > width or bottom > height or left >= right or top >= bottom:
            raise ImageProcessingError(
                f"Boîte de recadrage invalide {box} pour une image de taille {image.size}."
            )

        try:
            cropped = image.crop(box)
        except Exception as e:
            logger.error(f"Erreur lors du recadrage : {e}")
            raise ImageProcessingError(f"Erreur lors du recadrage de l'image : {e}")

        logger.info(f"Image recadrée à {box} -> {cropped.size}")
        return cropped

    def crop_center(self, image: Image.Image, ratio: float = 0.85) -> Image.Image:
        """
        Recadre l'image en gardant une zone centrale proportionnelle.

        Args:
            image: Image PIL source.
            ratio: Proportion de l'image d'origine à conserver (0 < ratio <= 1).

        Returns:
            Image recadrée centrée.
        """
        if not (0 < ratio <= 1):
            raise ImageProcessingError("Le ratio de recadrage doit être compris entre 0 (exclu) et 1.")

        width, height = image.size
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        left = (width - new_width) // 2
        top = (height - new_height) // 2
        right = left + new_width
        bottom = top + new_height

        return self.crop_image(image, (left, top, right, bottom))

    def resize_image(self, image: Image.Image, size: tuple, keep_aspect: bool = True) -> Image.Image:
        """
        Redimensionne une image.

        Args:
            image: Image PIL source.
            size: Tuple (largeur, hauteur) cible en pixels.
            keep_aspect: Si True, conserve les proportions (ajout de marges blanches
                         si nécessaire) ; si False, étire l'image à la taille exacte.

        Returns:
            Image redimensionnée.

        Raises:
            ImageProcessingError: si la taille demandée est invalide.
        """
        width, height = size
        if width <= 0 or height <= 0:
            raise ImageProcessingError(f"Dimensions de redimensionnement invalides : {size}")

        try:
            if keep_aspect:
                working = image.copy()
                working.thumbnail(size, Image.Resampling.LANCZOS)
                canvas = Image.new("RGB", size, (255, 255, 255))
                offset = ((size[0] - working.size[0]) // 2, (size[1] - working.size[1]) // 2)
                canvas.paste(working, offset)
                result = canvas
            else:
                result = image.resize(size, Image.Resampling.LANCZOS)
        except Exception as e:
            logger.error(f"Erreur lors du redimensionnement : {e}")
            raise ImageProcessingError(f"Erreur lors du redimensionnement de l'image : {e}")

        logger.info(f"Image redimensionnée à {result.size} (keep_aspect={keep_aspect})")
        return result

    def process_image(self, image: Image.Image, target_width: int = 600,
                       target_height: int = 800, crop_ratio: float = 0.9) -> Image.Image:
        """
        Traitement complet de l'image n°1 : recadrage centré puis redimensionnement.

        Args:
            image: Image PIL source.
            target_width: Largeur cible finale.
            target_height: Hauteur cible finale.
            crop_ratio: Ratio de recadrage central appliqué avant redimensionnement.

        Returns:
            Image traitée (recadrée + redimensionnée).
        """
        cropped = self.crop_center(image, ratio=crop_ratio)
        resized = self.resize_image(cropped, (target_width, target_height), keep_aspect=True)
        logger.info("Traitement complet de l'image n°1 terminé (recadrage + redimensionnement)")
        return resized

    def save_image(self, image: Image.Image, filepath: str) -> None:
        """
        Sauvegarde une image sur le disque.

        Args:
            image: Image PIL à sauvegarder.
            filepath: Chemin de destination.

        Raises:
            ImageProcessingError: en cas d'échec de sauvegarde.
        """
        try:
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            image.save(filepath, quality=95)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de l'image : {e}")
            raise ImageProcessingError(f"Impossible de sauvegarder l'image dans '{filepath}' : {e}")

        logger.info(f"Image sauvegardée dans {filepath}")
