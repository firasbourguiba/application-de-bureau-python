"""
Module pour charger et extraire les métadonnées d'un livre Project Gutenberg
à partir d'un fichier texte local (.txt).
"""

import re
import logging

logger = logging.getLogger(__name__)


class BookLoadError(Exception):
    """Exception levée en cas d'erreur lors du chargement du livre."""
    pass


class GutenbergClient:
    """
    Client pour charger et parser un livre Project Gutenberg
    à partir d'un fichier texte présent sur le disque local.
    """

    def load_book_from_file(self, filepath: str) -> str:
        """
        Charge le contenu complet d'un livre depuis un fichier .txt local.

        Args:
            filepath: Chemin vers le fichier texte (.txt)

        Returns:
            Le contenu textuel complet du fichier.

        Raises:
            BookLoadError: si le fichier n'existe pas, n'est pas lisible,
                           ou n'est pas un texte valide.
        """
        if not filepath.lower().endswith(".txt"):
            logger.warning(f"Le fichier {filepath} n'a pas l'extension .txt")

        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()
        except FileNotFoundError:
            logger.error(f"Fichier non trouvé : {filepath}")
            raise BookLoadError(f"Le fichier '{filepath}' n'existe pas.")
        except PermissionError:
            logger.error(f"Permission refusée : {filepath}")
            raise BookLoadError(f"Permission refusée pour lire '{filepath}'.")
        except UnicodeDecodeError:
            logger.error(f"Erreur d'encodage : {filepath}")
            raise BookLoadError(f"Le fichier '{filepath}' a un encodage non supporté.")
        except Exception as e:
            logger.error(f"Erreur inattendue lors du chargement : {e}")
            raise BookLoadError(f"Erreur lors de la lecture du fichier : {e}")

        if not text.strip():
            raise BookLoadError("Le fichier est vide.")

        logger.info(f"Livre chargé depuis {filepath} ({len(text)} caractères)")
        return text

    def extract_book_metadata(self, text: str) -> tuple[str, str, str]:
        """
        Extrait le titre, l'auteur et le contenu principal d'un livre
        au format Project Gutenberg.

        Args:
            text: Texte brut complet du livre (avec en-tête Gutenberg)

        Returns:
            Tuple (titre, auteur, contenu_principal)

        Raises:
            BookLoadError: si le texte est vide ou totalement non exploitable.
        """
        if not text or not text.strip():
            raise BookLoadError("Texte vide, impossible d'extraire les métadonnées.")

        start_marker_patterns = [
            r"\*\*\*\s*START OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*",
            r"\*\*\*\s*START OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*",
        ]
        end_marker_patterns = [
            r"\*\*\*\s*END OF THE PROJECT GUTENBERG EBOOK.*?\*\*\*",
            r"\*\*\*\s*END OF THIS PROJECT GUTENBERG EBOOK.*?\*\*\*",
        ]

        start_idx = 0
        header = text
        for pattern in start_marker_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                start_idx = match.end()
                header = text[:match.start()]
                break

        end_idx = len(text)
        for pattern in end_marker_patterns:
            match = re.search(pattern, text[start_idx:], re.IGNORECASE | re.DOTALL)
            if match:
                end_idx = start_idx + match.start()
                break

        main_content = text[start_idx:end_idx].strip()

        if not main_content:
            raise BookLoadError("Impossible d'isoler le contenu principal du livre.")

        title = self._extract_field(header, r"Title:\s*(.+)")
        author = self._extract_field(header, r"Author:\s*(.+)")

        if not author:
            # Certains recueils n'ont pas de champ "Author" mais un champ
            # "Contributor:" ou "Editor:" avec plusieurs noms listés.
            author = self._extract_field(header, r"Contributor:\s*(.+)")

        if not title:
            title = "Titre inconnu"
        if not author:
            author = "Auteur inconnu"

        logger.info(f"Métadonnées extraites - Titre: {title} | Auteur: {author}")
        return title.strip(), author.strip(), main_content

    @staticmethod
    def _extract_field(text: str, pattern: str) -> str:
        """Extrait un champ via regex, retourne '' si non trouvé."""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def extract_first_chapter(self, content: str, book_title: str = "") -> str:
        """
        Extrait le premier chapitre / premier texte narratif du contenu principal.

        Gère deux cas :
        - Roman classique avec marqueurs "CHAPTER I" / "CHAPITRE I"
        - Recueil de nouvelles : la première occurrence d'un titre en
          MAJUSCULES correspond généralement à la table des matières ;
          la deuxième occurrence du même titre marque le vrai début du texte.

        Args:
            content: Contenu principal du livre (sans en-tête/pied Gutenberg)
            book_title: Titre du livre (pour l'exclure des candidats de titre
                        de chapitre/conte, car il apparaît souvent en en-tête)

        Returns:
            Texte correspondant au premier chapitre/conte.

        Raises:
            BookLoadError: si le contenu est vide.
        """
        if not content or not content.strip():
            raise BookLoadError("Contenu vide, impossible d'extraire un chapitre.")

        content = content.strip()

        # --- Cas 1 : marqueurs de chapitre classiques (CHAPTER I, CHAPITRE I) ---
        chapter_pattern = r"^[ \t]*(CHAPTER|CHAPITRE)\s+[IVXLC0-9]+\b.*$"
        matches = list(re.finditer(chapter_pattern, content, re.MULTILINE | re.IGNORECASE))

        start_pos = None
        end_pos = len(content)

        if matches:
            # On prend la DERNIÈRE occurrence du même numéro de chapitre que
            # la première trouvée (ex: "CHAPTER I"), car les occurrences
            # précédentes sont souvent dans la table des matières.
            # Comparaison stricte sur le numéro exact (pas de endswith, qui
            # confondrait par exemple "I" et "II").
            first_match_text = matches[0].group(0).strip()
            first_number = first_match_text.split()[1] if len(first_match_text.split()) > 1 else None

            same_label_matches = matches
            if first_number:
                same_label_matches = [
                    m for m in matches
                    if m.group(0).strip().split()[1] == first_number
                ]

            start_match = same_label_matches[-1]
            start_pos = start_match.start()

            # Chercher le prochain marqueur de chapitre après celui-ci pour borner la fin
            for m in matches:
                if m.start() > start_pos:
                    end_pos = m.start()
                    break

        # Cas 2 : recueil de nouvelles (titres en MAJUSCULES répétés : TOC puis texte) ---
        if start_pos is None:
            start_pos, end_pos = self._locate_first_story(content, book_title)

        if start_pos is None:
            # Dernier recours : on prend le premier tiers du texte
            start_pos = 0
            end_pos = min(len(content) // 3, 12000)

        chapter = content[start_pos:end_pos].strip()

        if not chapter:
            raise BookLoadError("Le premier chapitre extrait est vide.")

        logger.info(f"Premier chapitre extrait ({len(chapter)} caractères)")
        return chapter

    @staticmethod
    def detect_story_author(chapter_text: str, fallback_author: str) -> str:
        """
        Pour un recueil de nouvelles, la première ligne du chapitre extrait
        est souvent le nom de l'auteur du conte (ex: "MÉRIMÉE"), plus précis
        que le champ générique "Contributor" de l'en-tête Gutenberg.

        Args:
            chapter_text: Texte du premier chapitre/conte extrait
            fallback_author: Auteur à utiliser si rien de mieux n'est détecté

        Returns:
            Le nom d'auteur le plus pertinent trouvé.
        """
        lines = chapter_text.strip().split("\n")
        if not lines:
            return fallback_author

        first_line = lines[0].strip()
        if (
            first_line
            and first_line.isupper()
            and 3 <= len(first_line) <= 40
            and re.match(r"^[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ' .\-]+$", first_line)
        ):
            return first_line.title()

        return fallback_author

    @staticmethod
    def _locate_first_story(content: str, book_title: str = "") -> tuple:
        """
        Repère le début du premier texte narratif dans un recueil de nouvelles.

        Heuristique : on cherche les lignes entièrement en MAJUSCULES (titres
        potentiels) apparaissant au moins deux fois (une fois dans la table
        des matières, une fois en tête du vrai texte). On retient la DEUXIÈME
        occurrence du premier titre répété rencontré, en se plaçant après les
        sections de préface/notes/vocabulaire. Le titre du livre lui-même est
        exclu des candidats (il apparaît souvent en en-tête de page).

        Returns:
            Tuple (start_pos, end_pos) ou (None, None) si rien trouvé.
        """
        lines = content.split("\n")
        candidate_titles = {}
        normalized_book_title = book_title.strip().upper()

        for idx, line in enumerate(lines):
            stripped = line.strip()
            if (
                stripped
                and stripped.isupper()
                and 3 <= len(stripped) <= 60
                and not stripped.startswith("[")
                and stripped != normalized_book_title
                and re.match(r"^[A-ZÀÂÉÈÊËÎÏÔÙÛÜÇ' .\-]+$", stripped)
            ):
                candidate_titles.setdefault(stripped, []).append(idx)

        # On cherche un titre apparaissant au moins 2 fois, le plus tôt possible
        # dans le texte (donc le premier conte/chapitre de la table des matières).
        repeated = {t: positions for t, positions in candidate_titles.items() if len(positions) >= 2}

        if not repeated:
            return None, None

        # Trier par position de la PREMIÈRE apparition (ordre dans la table des matières)
        sorted_titles = sorted(repeated.items(), key=lambda kv: kv[1][0])
        first_title, positions = sorted_titles[0]

        # La deuxième occurrence = le vrai début du texte
        start_line = positions[1]
        start_pos = sum(len(l) + 1 for l in lines[:start_line])

        # Chercher la fin : prochain titre candidat (de n'importe quelle liste)
        # qui apparaît après cette position, en ignorant les sous-titres trop proches.
        all_other_positions = sorted(
            pos for t, plist in candidate_titles.items()
            for pos in plist if pos > start_line + 5
        )
        end_pos = len(content)
        if all_other_positions:
            end_line = all_other_positions[0]
            end_pos = sum(len(l) + 1 for l in lines[:end_line])

        return start_pos, end_pos
