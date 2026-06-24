"""
Interface graphique Tkinter pour la Partie 2 du projet.

Logique des sources de données (telle que demandée) :
- Livre        -> chargé depuis un fichier .txt LOCAL (sélection via Parcourir)
- Logo         -> chargé depuis un fichier image LOCAL (sélection via Parcourir)
- Image n°1    -> téléchargée depuis une URL (saisie dans un champ texte)
"""

import logging
import threading
from pathlib import Path
from tkinter import (
    Tk, Frame, Label, Button, Entry, StringVar, Text, END, DISABLED, NORMAL,
    filedialog, messagebox, BOTH, X, Y, LEFT, RIGHT, TOP, BOTTOM, W, E,
)
from tkinter import ttk

from PIL import Image, ImageTk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from book.gutenberg_client import GutenbergClient, BookLoadError
from book.text_analyzer import TextAnalyzer, TextAnalysisError
from images.image_processor import ImageProcessor, ImageProcessingError
from images.image_merger import ImageMerger, ImageMergeError
from charts.paragraph_chart import ParagraphDistributionChart, ChartGenerationError
from report.word_generator import WordReportGenerator, WordGenerationError

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_URL = "https://raw.githubusercontent.com/github/explore/main/topics/python/python.png"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


class Part2App:
    """Application Tkinter pour generer le rapport Word à partir d'un livre."""

    def __init__(self, root: Tk):
        self.root = root
        self.root.title("Partie 2 - Rapport Word à partir d'un livre")
        self.root.geometry("1020x900")
        self.root.minsize(900, 760)

        # etat interne
        self.book_path_var = StringVar()
        self.logo_path_var = StringVar()
        self.image_url_var = StringVar(value=DEFAULT_IMAGE_URL)
        self.report_author_var = StringVar()

        self.book_title = None
        self.book_author = None
        self.first_chapter = None
        self.distribution = None
        self.stats = None
        self.merged_image = None
        self.merged_image_preview = None  # référence Tkinter pour éviter le garbage collection

        self._build_ui()
        self._set_status("Prêt. Sélectionnez un livre (.txt) et un logo pour commencer.")


    # construction de l'interface
    def _build_ui(self):
        container = Frame(self.root, padx=15, pady=15)
        container.pack(fill=BOTH, expand=True)

        self._build_inputs_section(container)
        self._build_actions_section(container)
        self._build_preview_section(container)
        self._build_log_section(container)
        self._build_status_bar()

    def _build_inputs_section(self, parent):
        frame = ttk.LabelFrame(parent, text="1. Sources de données", padding=10)
        frame.pack(fill=X, pady=(0, 10))

        # Livre (.txt local) 
        Label(frame, text="Livre (.txt local) :", width=18, anchor=W).grid(row=0, column=0, sticky=W, pady=4)
        Entry(frame, textvariable=self.book_path_var, width=60).grid(row=0, column=1, sticky=W, padx=5)
        Button(frame, text="Parcourir...", command=self._browse_book).grid(row=0, column=2, padx=5)

        # Logo (image locale)
        Label(frame, text="Logo (image locale) :", width=18, anchor=W).grid(row=1, column=0, sticky=W, pady=4)
        Entry(frame, textvariable=self.logo_path_var, width=60).grid(row=1, column=1, sticky=W, padx=5)
        Button(frame, text="Parcourir...", command=self._browse_logo).grid(row=1, column=2, padx=5)

        #  Image n°1 (URL) 
        Label(frame, text="Image du livre (URL) :", width=18, anchor=W).grid(row=2, column=0, sticky=W, pady=4)
        Entry(frame, textvariable=self.image_url_var, width=60).grid(row=2, column=1, sticky=W, padx=5)
        Label(frame, text="(téléchargée à l'exécution)", fg="gray").grid(row=2, column=2, sticky=W, padx=5)

        # Auteur du rapport 
        Label(frame, text="Votre nom (rapport) :", width=18, anchor=W).grid(row=3, column=0, sticky=W, pady=4)
        Entry(frame, textvariable=self.report_author_var, width=40).grid(row=3, column=1, sticky=W, padx=5)

    def _build_actions_section(self, parent):
        frame = ttk.LabelFrame(parent, text="2. Génération", padding=10)
        frame.pack(fill=X, pady=(0, 10))

        Button(
            frame, text="Charger et analyser le livre",
            command=self._on_load_book, width=28
        ).grid(row=0, column=0, padx=5, pady=5)

        Button(
            frame, text="Télécharger et fusionner l'image",
            command=self._on_process_image, width=28
        ).grid(row=0, column=1, padx=5, pady=5)

        Button(
            frame, text="Générer le rapport Word",
            command=self._on_generate_report, width=28
        ).grid(row=0, column=2, padx=5, pady=5)

    def _build_preview_section(self, parent):
        frame = ttk.LabelFrame(parent, text="3. Aperçus (image fusionnée et graphique)", padding=10)
        frame.pack(fill=BOTH, pady=(0, 10))

        columns = Frame(frame)
        columns.pack(fill=BOTH, expand=True)

        #  Colonne gauche : image fusionnée
        left_col = Frame(columns)
        left_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 8))

        Label(left_col, text="Image n°1 + logo", font=("", 9, "bold")).pack(anchor=W)
        self.preview_label = Label(left_col, text="(aucune image générée pour le moment)", fg="gray")
        self.preview_label.pack(pady=5)

        #  Colonne droite : graphique de distribution embarqué (matplotlib + Tkinter)
        right_col = Frame(columns)
        right_col.pack(side=LEFT, fill=BOTH, expand=True, padx=(8, 0))

        Label(right_col, text="Distribution des paragraphes", font=("", 9, "bold")).pack(anchor=W)

        self.chart_figure = Figure(figsize=(4.6, 2.6), dpi=90)
        self.chart_ax = self.chart_figure.add_subplot(111)
        self.chart_ax.text(
            0.5, 0.5, "(en attente de l'analyse du livre)",
            ha="center", va="center", color="gray", transform=self.chart_ax.transAxes,
        )
        self.chart_ax.set_xticks([])
        self.chart_ax.set_yticks([])

        self.chart_canvas = FigureCanvasTkAgg(self.chart_figure, master=right_col)
        self.chart_canvas.get_tk_widget().pack(fill=BOTH, expand=True)
        self.chart_canvas.draw()

    def _build_log_section(self, parent):
        frame = ttk.LabelFrame(parent, text="4. Journal des opérations", padding=10)
        frame.pack(fill=BOTH, expand=True, pady=(0, 10))

        self.log_text = Text(frame, height=10, state=DISABLED, wrap="word")
        self.log_text.pack(fill=BOTH, expand=True)

    def _build_status_bar(self):
        self.status_var = StringVar()
        status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor=W)
        status_bar.pack(side=BOTTOM, fill=X)

   
    # Utilitaires d'affichage
    def _set_status(self, message: str):
        self.status_var.set(message)

    def _log(self, message: str):
        self.log_text.config(state=NORMAL)
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)
        self.log_text.config(state=DISABLED)
        logger.info(message)

    def _show_error(self, title: str, message: str):
        self._log(f"ERREUR : {message}")
        self._set_status(f"Erreur : {message}")
        messagebox.showerror(title, message)

    # Sélection de fichiers locaux
    def _browse_book(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner le livre (fichier .txt)",
            filetypes=[("Fichiers texte", "*.txt"), ("Tous les fichiers", "*.*")],
        )
        if filepath:
            self.book_path_var.set(filepath)
            self._log(f"Livre sélectionné : {filepath}")

    def _browse_logo(self):
        filepath = filedialog.askopenfilename(
            title="Sélectionner le logo (image locale)",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.bmp *.gif"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if filepath:
            self.logo_path_var.set(filepath)
            self._log(f"Logo sélectionné : {filepath}")


    # Action 1 : Charger et analyser le livre
    def _on_load_book(self):
        book_path = self.book_path_var.get().strip()
        if not book_path:
            self._show_error("Livre manquant", "Veuillez sélectionner un fichier .txt pour le livre.")
            return

        self._set_status("Chargement et analyse du livre en cours...")
        self._log(f"Chargement du livre depuis : {book_path}")

        try:
            file_size = Path(book_path).stat().st_size
            self._log(f"Taille du fichier : {file_size:,} octets".replace(",", " "))
            if file_size < 1000:
                self._log(
                    "ATTENTION : ce fichier semble très petit pour un livre complet "
                    "(moins de 1 Ko). Vérifiez que c'est bien le bon fichier."
                )

            client = GutenbergClient()
            text = client.load_book_from_file(book_path)
            self._log(f"Contenu lu : {len(text):,} caractères".replace(",", " "))

            title, author, content = client.extract_book_metadata(text)
            self._log(f"Contenu principal (hors en-tête Gutenberg) : {len(content):,} caractères".replace(",", " "))

            chapter = client.extract_first_chapter(content, book_title=title)
            self._log(f"Premier chapitre extrait : {len(chapter):,} caractères".replace(",", " "))

            real_author = client.detect_story_author(chapter, author)

            analyzer = TextAnalyzer()
            distribution, stats = analyzer.analyze_full_chapter(chapter)

            if stats["total_paragraphs"] < 3 or stats["total_words"] < 50:
                self._log(
                    "ATTENTION : très peu de texte détecté dans le premier chapitre "
                    f"({stats['total_paragraphs']} paragraphe(s), {stats['total_words']} mot(s)). "
                    "Le fichier sélectionné est peut-être incomplet, mal encodé, ou ne "
                    "correspond pas au format attendu (vérifiez le bon fichier .txt)."
                )

            self.book_title = title
            self.book_author = real_author
            self.first_chapter = chapter
            self.distribution = distribution
            self.stats = stats

            self._log(f"Titre détecté : {title}")
            self._log(f"Auteur détecté : {real_author}")
            self._log(
                f"Analyse terminée : {stats['total_paragraphs']} paragraphes, "
                f"{stats['total_words']} mots (min={stats['min_words']}, "
                f"max={stats['max_words']}, moyenne={stats['avg_words']})"
            )
            self._update_chart_preview(distribution, title)
            self._set_status("Livre chargé et analysé avec succès.")

        except BookLoadError as e:
            self._show_error("Erreur de chargement du livre", str(e))
        except TextAnalysisError as e:
            self._show_error("Erreur d'analyse du texte", str(e))
        except Exception as e:
            self._show_error("Erreur inattendue", f"Une erreur inattendue est survenue : {e}")


    # Action 2 : Télécharger l'image (URL) et fusionner avec le logo (local)
    def _on_process_image(self):
        url = self.image_url_var.get().strip()
        logo_path = self.logo_path_var.get().strip()

        if not url:
            self._show_error("URL manquante", "Veuillez saisir une URL pour l'image du livre.")
            return
        if not logo_path:
            self._show_error("Logo manquant", "Veuillez sélectionner un fichier image local pour le logo.")
            return

        self._set_status("Téléchargement de l'image en cours...")
        self._log(f"Téléchargement de l'image depuis : {url}")

        # Le téléchargement réseau se fait dans un thread pour ne pas geler l'interface.
        threading.Thread(target=self._process_image_worker, args=(url, logo_path), daemon=True).start()

    def _process_image_worker(self, url: str, logo_path: str):
        try:
            processor = ImageProcessor()
            image1 = processor.download_image(url)
            self.root.after(0, lambda: self._log(f"Image téléchargée ({image1.size[0]}x{image1.size[1]})"))

            processed = processor.process_image(image1, target_width=600, target_height=800, crop_ratio=0.9)
            self.root.after(0, lambda: self._log("Image n°1 recadrée et redimensionnée (600x800)."))

            merger = ImageMerger()
            logo = merger.load_logo_from_file(logo_path)
            self.root.after(0, lambda: self._log(f"Logo chargé depuis : {logo_path} (converti en N&B)"))

            rotated_logo = merger.rotate_image(logo, angle=20)
            self.root.after(0, lambda: self._log("Logo pivoté de 20°."))

            final_image = merger.paste_logo(
                processed, rotated_logo, position="bottom-right", margin=15, scale_ratio=0.22
            )
            self.root.after(0, lambda: self._log("Logo collé sur l'image n°1 (bas-droite)."))

            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_path = OUTPUT_DIR / "image_fusionnee.png"
            processor.save_image(final_image, str(output_path))

            self.merged_image = str(output_path)
            self.root.after(0, lambda: self._on_image_ready(str(output_path)))

        except (ImageProcessingError, ImageMergeError) as e:
            self.root.after(0, lambda: self._show_error("Erreur de traitement d'image", str(e)))
        except Exception as e:
            self.root.after(0, lambda: self._show_error("Erreur inattendue", f"Une erreur inattendue est survenue : {e}"))

    def _on_image_ready(self, image_path: str):
        self._log(f"Image fusionnée sauvegardée : {image_path}")
        self._set_status("Image téléchargée, traitée et fusionnée avec succès.")
        self._show_preview(image_path)

    def _show_preview(self, image_path: str):
        try:
            img = Image.open(image_path)
            img.thumbnail((220, 280))
            self.merged_image_preview = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.merged_image_preview, text="")
        except Exception as e:
            logger.warning(f"Impossible d'afficher l'aperçu de l'image : {e}")

    def _update_chart_preview(self, distribution: dict, book_title: str):
        """
        Dessine le graphique de distribution des paragraphes directement dans
        la fenêtre principale (canvas Tkinter intégré via matplotlib), sans
        attendre la génération du fichier Word.
        """
        try:
            self.chart_ax.clear()

            lengths = list(distribution.keys())
            counts = list(distribution.values())

            bars = self.chart_ax.bar(
                range(len(lengths)), counts,
                color="#4472C4", edgecolor="#1F3864", linewidth=1,
            )
            for bar, count in zip(bars, counts):
                self.chart_ax.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height(),
                    str(count), ha="center", va="bottom", fontsize=8, fontweight="bold",
                )

            self.chart_ax.set_xticks(range(len(lengths)))
            self.chart_ax.set_xticklabels(lengths, fontsize=8)
            self.chart_ax.set_xlabel("Mots / paragraphe (dizaine)", fontsize=8)
            self.chart_ax.set_ylabel("Nb. paragraphes", fontsize=8)
            self.chart_ax.set_title(book_title, fontsize=9, fontweight="bold")
            self.chart_ax.grid(axis="y", linestyle="--", alpha=0.4)
            self.chart_ax.tick_params(axis="y", labelsize=8)

            self.chart_figure.tight_layout()
            self.chart_canvas.draw()

            self._log("Graphique de distribution affiché dans la fenêtre principale.")

        except Exception as e:
            logger.warning(f"Impossible d'afficher le graphique dans l'interface : {e}")

    # Action 3 : Générer le rapport Word
    def _on_generate_report(self):
        if not self.book_title or not self.stats:
            self._show_error(
                "Livre non chargé",
                "Veuillez d'abord charger et analyser un livre (étape 1).",
            )
            return

        if not self.merged_image:
            self._show_error(
                "Image non prête",
                "Veuillez d'abord télécharger et fusionner l'image (étape 2).",
            )
            return

        report_author = self.report_author_var.get().strip() or "Auteur du rapport"

        self._set_status("Génération du graphique et du document Word...")
        self._log("Génération du graphique de distribution des paragraphes...")

        try:
            OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            chart_path = OUTPUT_DIR / "distribution_paragraphes.png"

            chart = ParagraphDistributionChart()
            chart.generate_and_save(
                self.distribution, str(chart_path),
                title=f"Distribution des paragraphes - {self.book_title}",
            )
            self._log(f"Graphique sauvegardé : {chart_path}")

            description = (
                f"Cette analyse porte sur le premier chapitre du livre « {self.book_title} » "
                f"de {self.book_author}. Le texte a été découpé en paragraphes ; pour chacun, "
                f"le nombre de mots a été compté puis arrondi à la dizaine la plus proche. "
                f"Le graphique ci-dessus présente la distribution de ces longueurs, du plus "
                f"court au plus long, et permet d'observer le rythme d'écriture de l'auteur."
            )
            source_text = (
                f"Premier chapitre extrait du fichier texte local '{Path(self.book_path_var.get()).name}' "
                f"(édition Project Gutenberg)."
            )

            generator = WordReportGenerator()
            generator.create_document()
            generator.add_title_page(
                book_title=self.book_title,
                book_author=self.book_author,
                report_author=report_author,
                image_path=self.merged_image,
            )
            generator.add_graph_page(
                chart_path=str(chart_path),
                description=description,
                statistics=self.stats,
                source_text=source_text,
            )

            report_path = OUTPUT_DIR / "rapport_livre.docx"
            generator.save_document(str(report_path))

            self._log(f"Rapport Word généré avec succès : {report_path}")
            self._set_status(f"Rapport généré : {report_path}")
            messagebox.showinfo("Succès", f"Le rapport Word a été généré avec succès :\n{report_path}")

        except ChartGenerationError as e:
            self._show_error("Erreur de génération du graphique", str(e))
        except WordGenerationError as e:
            self._show_error("Erreur de génération du document Word", str(e))
        except Exception as e:
            self._show_error("Erreur inattendue", f"Une erreur inattendue est survenue : {e}")


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
