"""
Module pour charger un logo (image n°2, en noir et blanc) depuis le disque
local, le faire pivoter, et le coller sur l'image n°1.
"""

import logging
from pathlib import Path

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


class ImageMergeError(Exception):
    """Exception levée en cas d'erreur lors du chargement ou de la fusion d'images."""
    pass


class ImageMerger:
    """Charge un logo local, le pivote, et le colle sur une image de fond."""

    def load_logo_from_file(self, filepath: str) -> Image.Image:
        """
        Charge le logo (image n°2) depuis un fichier local et le convertit
        en niveaux de gris (noir et blanc) tel que demandé par le sujet.

        Args:
            filepath: Chemin vers le fichier image du logo.

        Returns:
            Image PIL en mode "L" (niveaux de gris), puis reconvertie en
            RGBA pour permettre un collage avec transparence.

        Raises:
            ImageMergeError: si le fichier n'existe pas ou n'est pas une image valide.
        """
        path = Path(filepath)
        if not path.exists():
            raise ImageMergeError(f"Le fichier logo '{filepath}' n'existe pas.")
        if not path.is_file():
            raise ImageMergeError(f"'{filepath}' n'est pas un fichier valide.")

        try:
            image = Image.open(filepath)
            image.load()
        except UnidentifiedImageError:
            raise ImageMergeError(f"'{filepath}' n'est pas un fichier image valide.")
        except Exception as e:
            logger.error(f"Erreur lors du chargement du logo : {e}")
            raise ImageMergeError(f"Impossible de charger le logo '{filepath}' : {e}")

        # Conversion en noir et blanc (niveaux de gris), comme exigé par le sujet
        grayscale = image.convert("L")

        # Reconversion en RGBA pour pouvoir gérer la transparence lors du collage :
        # les pixels blancs (fond) deviennent transparents, le reste reste opaque.
        rgba = grayscale.convert("RGBA")
        pixels = rgba.getdata()
        new_pixels = []
        for r, g, b, a in pixels:
            if r > 240 and g > 240 and b > 240:
                new_pixels.append((r, g, b, 0))  # fond blanc -> transparent
            else:
                new_pixels.append((r, g, b, 255))
        rgba.putdata(new_pixels)

        logger.info(f"Logo chargé depuis {filepath} ({image.size[0]}x{image.size[1]}), converti en N&B")
        return rgba

    def rotate_image(self, image: Image.Image, angle: float) -> Image.Image:
        """
        Fait pivoter une image d'un angle donné (en degrés).

        Args:
            image: Image PIL à pivoter.
            angle: Angle de rotation en degrés (sens anti-horaire positif).

        Returns:
            Image pivotée (la zone hors image d'origine devient transparente
            si l'image source a un canal alpha).

        Raises:
            ImageMergeError: en cas d'erreur lors de la rotation.
        """
        try:
            if image.mode != "RGBA":
                image = image.convert("RGBA")
            rotated = image.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)
        except Exception as e:
            logger.error(f"Erreur lors de la rotation : {e}")
            raise ImageMergeError(f"Erreur lors de la rotation de l'image : {e}")

        logger.info(f"Logo pivoté de {angle}° -> nouvelle taille {rotated.size}")
        return rotated

    def paste_logo(self, background: Image.Image, logo: Image.Image,
                    position: str = "bottom-right", margin: int = 15,
                    scale_ratio: float = 0.18) -> Image.Image:
        """
        Colle le logo (déjà pivoté) sur l'image de fond (image n°1).

        Args:
            background: Image de fond (image n°1, déjà traitée).
            logo: Logo à coller (idéalement déjà pivoté, en RGBA).
            position: Coin de placement : 'top-left', 'top-right',
                      'bottom-left' ou 'bottom-right'.
            margin: Marge en pixels par rapport au bord choisi.
            scale_ratio: Largeur du logo en proportion de la largeur du fond.

        Returns:
            Nouvelle image (copie du fond) avec le logo collé.

        Raises:
            ImageMergeError: si la position demandée est invalide.
        """
        valid_positions = {"top-left", "top-right", "bottom-left", "bottom-right"}
        if position not in valid_positions:
            raise ImageMergeError(
                f"Position '{position}' invalide. Valeurs possibles : {sorted(valid_positions)}"
            )
        if not (0 < scale_ratio <= 1):
            raise ImageMergeError("scale_ratio doit être compris entre 0 (exclu) et 1.")

        bg_width, bg_height = background.size

        target_width = max(1, int(bg_width * scale_ratio))
        aspect_ratio = logo.size[1] / logo.size[0] if logo.size[0] else 1
        target_height = max(1, int(target_width * aspect_ratio))

        try:
            logo_resized = logo.resize((target_width, target_height), Image.Resampling.LANCZOS)
        except Exception as e:
            raise ImageMergeError(f"Erreur lors du redimensionnement du logo : {e}")

        if position == "top-left":
            pos = (margin, margin)
        elif position == "top-right":
            pos = (bg_width - target_width - margin, margin)
        elif position == "bottom-left":
            pos = (margin, bg_height - target_height - margin)
        else:  # bottom-right
            pos = (bg_width - target_width - margin, bg_height - target_height - margin)

        result = background.convert("RGBA").copy()

        try:
            if logo_resized.mode == "RGBA":
                result.paste(logo_resized, pos, logo_resized)
            else:
                result.paste(logo_resized, pos)
        except Exception as e:
            logger.error(f"Erreur lors du collage du logo : {e}")
            raise ImageMergeError(f"Erreur lors du collage du logo : {e}")

        logger.info(f"Logo collé en position '{position}' à {pos}, taille {logo_resized.size}")
        return result.convert("RGB")
