"""
Tests unitaires pour la Partie 2 :
- book.gutenberg_client (chargement et parsing du livre depuis un .txt local)
- book.text_analyzer (analyse des paragraphes)
- images.image_processor (téléchargement URL + traitement image n°1)
- images.image_merger (logo local, rotation, collage)
- charts.paragraph_chart (graphique de distribution)
- report.word_generator (génération du document Word)
"""

import unittest
import tempfile
import shutil
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from PIL import Image

from book.gutenberg_client import GutenbergClient, BookLoadError
from book.text_analyzer import TextAnalyzer, TextAnalysisError
from images.image_processor import ImageProcessor, ImageProcessingError
from images.image_merger import ImageMerger, ImageMergeError
from charts.paragraph_chart import ParagraphDistributionChart, ChartGenerationError
from report.word_generator import WordReportGenerator, WordGenerationError


SAMPLE_GUTENBERG_TEXT = """The Project Gutenberg eBook of Test Book

Title: Test Book

Author: Jane Doe

*** START OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***

CHAPTER I

This is the first paragraph of the first chapter. It has enough words
to be counted as a real paragraph for the analysis we want to perform.

This is the second paragraph. It is shorter than the first one.

This third paragraph is intentionally a bit longer than the others so
that the distribution of paragraph lengths shows some real variation
across the whole chapter content that we are analyzing here today.

CHAPTER II

This is the second chapter and should not be included in the analysis
of the first chapter at all.

*** END OF THE PROJECT GUTENBERG EBOOK TEST BOOK ***
"""


class TestGutenbergClient(unittest.TestCase):
    """Tests pour le chargement et le parsing du livre."""

    def setUp(self):
        self.client = GutenbergClient()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _write_temp_file(self, content: str, name: str = "book.txt") -> str:
        path = os.path.join(self.temp_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_load_book_from_file_success(self):
        path = self._write_temp_file(SAMPLE_GUTENBERG_TEXT)
        text = self.client.load_book_from_file(path)
        self.assertIn("CHAPTER I", text)

    def test_load_book_from_file_not_found(self):
        with self.assertRaises(BookLoadError):
            self.client.load_book_from_file(os.path.join(self.temp_dir, "missing.txt"))

    def test_load_book_from_file_empty(self):
        path = self._write_temp_file("   ")
        with self.assertRaises(BookLoadError):
            self.client.load_book_from_file(path)

    def test_extract_book_metadata(self):
        title, author, content = self.client.extract_book_metadata(SAMPLE_GUTENBERG_TEXT)
        self.assertEqual(title, "Test Book")
        self.assertEqual(author, "Jane Doe")
        self.assertIn("CHAPTER I", content)
        self.assertNotIn("START OF THE PROJECT GUTENBERG", content)

    def test_extract_book_metadata_empty_text(self):
        with self.assertRaises(BookLoadError):
            self.client.extract_book_metadata("")

    def test_extract_first_chapter_classic_markers(self):
        _, _, content = self.client.extract_book_metadata(SAMPLE_GUTENBERG_TEXT)
        chapter = self.client.extract_first_chapter(content)
        self.assertIn("first paragraph", chapter)
        self.assertNotIn("second chapter", chapter)

    def test_extract_first_chapter_empty_content(self):
        with self.assertRaises(BookLoadError):
            self.client.extract_first_chapter("")

    def test_detect_story_author_fallback(self):
        result = self.client.detect_story_author("Just a normal paragraph.", "Fallback Author")
        self.assertEqual(result, "Fallback Author")

    def test_detect_story_author_detected(self):
        result = self.client.detect_story_author("MERIMEE\n\nSome text here.", "Fallback Author")
        self.assertEqual(result, "Merimee")


class TestTextAnalyzer(unittest.TestCase):
    """Tests pour l'analyse des paragraphes."""

    def setUp(self):
        self.analyzer = TextAnalyzer()
        self.sample_chapter = (
            "This is paragraph one with several words in it for testing.\n\n"
            "This is paragraph two, a bit shorter.\n\n"
            "This third paragraph is intentionally longer than the two "
            "paragraphs that came before it, to test variation in length.\n\n"
            "Short one here too."
        )

    def test_extract_paragraphs(self):
        paragraphs = self.analyzer.extract_paragraphs(self.sample_chapter)
        self.assertEqual(len(paragraphs), 4)

    def test_extract_paragraphs_excludes_uppercase_titles(self):
        text = "TITLE HEADING\n\nThis is a real paragraph with enough words in it."
        paragraphs = self.analyzer.extract_paragraphs(text)
        self.assertEqual(len(paragraphs), 1)
        self.assertNotIn("TITLE HEADING", paragraphs)

    def test_extract_paragraphs_empty_raises(self):
        with self.assertRaises(TextAnalysisError):
            self.analyzer.extract_paragraphs("   ")

    def test_count_words_per_paragraph(self):
        self.analyzer.extract_paragraphs(self.sample_chapter)
        counts = self.analyzer.count_words_per_paragraph()
        self.assertEqual(len(counts), len(self.analyzer.paragraphs))
        self.assertTrue(all(c > 0 for c in counts))

    def test_count_words_without_extraction_raises(self):
        with self.assertRaises(TextAnalysisError):
            self.analyzer.count_words_per_paragraph([])

    def test_round_to_nearest_ten(self):
        # Note : round() en Python arrondit les .5 au pair le plus proche
        # (125 -> 12.5 dizaines -> 120, car 12 est pair).
        rounded = self.analyzer.round_to_nearest_ten([123, 127, 129, 125, 95])
        self.assertEqual(rounded, [120, 130, 130, 120, 100])

    def test_get_distribution_sorted(self):
        distribution = self.analyzer.get_distribution([20, 10, 20, 30, 10, 10])
        self.assertEqual(distribution, {10: 3, 20: 2, 30: 1})
        self.assertEqual(list(distribution.keys()), sorted(distribution.keys()))

    def test_calculate_statistics(self):
        stats = self.analyzer.calculate_statistics([10, 20, 30, 40])
        self.assertEqual(stats["total_paragraphs"], 4)
        self.assertEqual(stats["total_words"], 100)
        self.assertEqual(stats["min_words"], 10)
        self.assertEqual(stats["max_words"], 40)
        self.assertEqual(stats["avg_words"], 25.0)

    def test_calculate_statistics_empty_raises(self):
        with self.assertRaises(TextAnalysisError):
            self.analyzer.calculate_statistics([])

    def test_analyze_full_chapter(self):
        distribution, stats = self.analyzer.analyze_full_chapter(self.sample_chapter)
        self.assertIsInstance(distribution, dict)
        self.assertIn("total_paragraphs", stats)


class TestImageProcessor(unittest.TestCase):
    """Tests pour le téléchargement (URL) et le traitement de l'image n°1."""

    def setUp(self):
        self.processor = ImageProcessor()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @staticmethod
    def _make_image(width=400, height=300, color="red") -> Image.Image:
        return Image.new("RGB", (width, height), color=color)

    def test_download_image_empty_url_raises(self):
        with self.assertRaises(ImageProcessingError):
            self.processor.download_image("")

    @patch("images.image_processor.requests.get")
    def test_download_image_success(self, mock_get):
        from io import BytesIO
        img = self._make_image()
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        mock_response = MagicMock()
        mock_response.content = buffer.getvalue()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = self.processor.download_image("https://example.com/fake.png")
        self.assertEqual(result.size, (400, 300))

    @patch("images.image_processor.requests.get")
    def test_download_image_connection_error(self, mock_get):
        import requests
        mock_get.side_effect = requests.ConnectionError()
        with self.assertRaises(ImageProcessingError):
            self.processor.download_image("https://example.com/fake.png")

    def test_crop_image_valid(self):
        img = self._make_image(200, 200)
        cropped = self.processor.crop_image(img, (10, 10, 100, 100))
        self.assertEqual(cropped.size, (90, 90))

    def test_crop_image_invalid_box_raises(self):
        img = self._make_image(100, 100)
        with self.assertRaises(ImageProcessingError):
            self.processor.crop_image(img, (50, 50, 10, 10))

    def test_crop_center(self):
        img = self._make_image(200, 100)
        cropped = self.processor.crop_center(img, ratio=0.5)
        self.assertEqual(cropped.size, (100, 50))

    def test_resize_image_keep_aspect(self):
        img = self._make_image(400, 200)
        resized = self.processor.resize_image(img, (200, 200), keep_aspect=True)
        self.assertEqual(resized.size, (200, 200))

    def test_resize_image_invalid_size_raises(self):
        img = self._make_image()
        with self.assertRaises(ImageProcessingError):
            self.processor.resize_image(img, (0, 100))

    def test_process_image_full_pipeline(self):
        img = self._make_image(800, 600)
        result = self.processor.process_image(img, target_width=300, target_height=400)
        self.assertEqual(result.size, (300, 400))

    def test_save_image(self):
        img = self._make_image()
        path = os.path.join(self.temp_dir, "out.png")
        self.processor.save_image(img, path)
        self.assertTrue(os.path.exists(path))


class TestImageMerger(unittest.TestCase):
    """Tests pour le chargement du logo, la rotation et le collage."""

    def setUp(self):
        self.merger = ImageMerger()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_logo_file(self) -> str:
        img = Image.new("RGB", (100, 100), "white")
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 80, 80], fill="black")
        path = os.path.join(self.temp_dir, "logo.png")
        img.save(path)
        return path

    def test_load_logo_from_file_success(self):
        path = self._make_logo_file()
        logo = self.merger.load_logo_from_file(path)
        self.assertEqual(logo.mode, "RGBA")

    def test_load_logo_from_file_not_found(self):
        with self.assertRaises(ImageMergeError):
            self.merger.load_logo_from_file(os.path.join(self.temp_dir, "missing.png"))

    def test_rotate_image(self):
        img = Image.new("RGBA", (100, 50), (0, 0, 0, 255))
        rotated = self.merger.rotate_image(img, 90)
        # Une rotation de 90° avec expand=True échange largeur et hauteur
        self.assertEqual(rotated.size, (50, 100))

    def test_paste_logo_valid_position(self):
        background = Image.new("RGB", (300, 300), "white")
        logo = Image.new("RGBA", (50, 50), (0, 0, 0, 255))
        result = self.merger.paste_logo(background, logo, position="bottom-right")
        self.assertEqual(result.size, (300, 300))

    def test_paste_logo_invalid_position_raises(self):
        background = Image.new("RGB", (300, 300), "white")
        logo = Image.new("RGBA", (50, 50), (0, 0, 0, 255))
        with self.assertRaises(ImageMergeError):
            self.merger.paste_logo(background, logo, position="middle")

    def test_paste_logo_invalid_ratio_raises(self):
        background = Image.new("RGB", (300, 300), "white")
        logo = Image.new("RGBA", (50, 50), (0, 0, 0, 255))
        with self.assertRaises(ImageMergeError):
            self.merger.paste_logo(background, logo, scale_ratio=1.5)


class TestParagraphDistributionChart(unittest.TestCase):
    """Tests pour la génération du graphique de distribution."""

    def setUp(self):
        self.chart = ParagraphDistributionChart()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.chart.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_bar_chart_success(self):
        self.chart.create_bar_chart({10: 3, 20: 5, 30: 2})
        self.assertIsNotNone(self.chart.fig)

    def test_create_bar_chart_empty_raises(self):
        with self.assertRaises(ChartGenerationError):
            self.chart.create_bar_chart({})

    def test_save_chart_without_creation_raises(self):
        with self.assertRaises(ChartGenerationError):
            self.chart.save_chart(os.path.join(self.temp_dir, "out.png"))

    def test_generate_and_save(self):
        path = os.path.join(self.temp_dir, "chart.png")
        result = self.chart.generate_and_save({10: 2, 20: 4}, path)
        self.assertEqual(result, path)
        self.assertTrue(os.path.exists(path))
        self.assertGreater(os.path.getsize(path), 0)


class TestWordReportGenerator(unittest.TestCase):
    """Tests pour la génération du document Word final."""

    def setUp(self):
        self.generator = WordReportGenerator()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _make_test_image(self, name="img.png") -> str:
        img = Image.new("RGB", (100, 100), "blue")
        path = os.path.join(self.temp_dir, name)
        img.save(path)
        return path

    def test_create_document(self):
        doc = self.generator.create_document()
        self.assertIsNotNone(doc)

    def test_add_title_page(self):
        self.generator.create_document()
        image_path = self._make_test_image()
        self.generator.add_title_page("Mon Livre", "Auteur X", "Rapport Y", image_path)
        texts = [p.text for p in self.generator.doc.paragraphs]
        self.assertTrue(any("Auteur X" in t for t in texts))

    def test_add_graph_page(self):
        self.generator.create_document()
        chart_path = self._make_test_image("chart.png")
        self.generator.add_graph_page(
            chart_path,
            description="Une description de test.",
            statistics={"total_paragraphs": 10, "total_words": 200,
                        "min_words": 5, "max_words": 50, "avg_words": 20.0},
            source_text="Source de test"
        )
        self.assertEqual(len(self.generator.doc.tables), 1)

    def test_save_document_without_creation_raises(self):
        with self.assertRaises(WordGenerationError):
            self.generator.save_document(os.path.join(self.temp_dir, "out.docx"))

    def test_save_document_success(self):
        self.generator.create_document()
        self.generator.add_title_page("Titre", "Auteur", "Rapport")
        path = os.path.join(self.temp_dir, "rapport.docx")
        self.generator.save_document(path)
        self.assertTrue(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
