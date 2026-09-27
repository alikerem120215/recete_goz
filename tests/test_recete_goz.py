"""
ReçeteGöz - Doğrulama ve Birim Testleri
"""

import sys
import unittest
from pathlib import Path
from PIL import Image, ImageDraw

# Proje dizinini ekle
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from core.screen_capture import ScreenCaptureManager
from core.ai_analyzer import PrescriptionAnalysisResult, PrescriptionAnalyzer, SYSTEM_INSTRUCTION
from config import config


class TestReceteGoz(unittest.TestCase):
    """ReçeteGöz temel modül testleri."""

    def test_pydantic_schema_validation(self):
        """Pydantic PrescriptionAnalysisResult şemasının doğrulanması."""
        sample_json = """{
            "prescription_found": true,
            "has_error": true,
            "error_row": 2,
            "field_name": "Doz",
            "short_message": "Doz aşımı: Günde 2x1 yerine 3x1 girilmiş",
            "detailed_explanation": "SGK SUT kuralına göre maksimum günlük doz 2 adettir.",
            "suggested_fix": "Günde 2x1 olarak güncelleyiniz."
        }"""
        result = PrescriptionAnalysisResult.model_validate_json(sample_json)
        self.assertTrue(result.prescription_found)
        self.assertTrue(result.has_error)
        self.assertEqual(result.error_row, 2)
        self.assertEqual(result.field_name, "Doz")
        self.assertIn("Doz aşımı", result.short_message)
        self.assertIn("SUT", result.detailed_explanation)
        self.assertEqual(result.suggested_fix, "Günde 2x1 olarak güncelleyiniz.")

    def test_pydantic_clean_case(self):
        """Temiz reçete çıktısının doğrulanması."""
        sample_json = """{
            "prescription_found": true,
            "has_error": false,
            "short_message": "Reçete kurallara uygun",
            "detailed_explanation": "Herhangi bir doz aşımı veya kural ihlali bulunamadı."
        }"""
        result = PrescriptionAnalysisResult.model_validate_json(sample_json)
        self.assertTrue(result.prescription_found)
        self.assertFalse(result.has_error)
        self.assertIsNone(result.error_row)

    def test_screen_capture_and_hashing(self):
        """ScreenCaptureManager hash ve görüntü optimizasyonu testi."""
        manager = ScreenCaptureManager()

        # Sahte iki görüntü oluştur (biri aynı, biri farklı)
        img1 = Image.new("RGB", (400, 300), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        draw1.rectangle([0, 0, 200, 300], fill=(0, 0, 0))  # Sol yarı siyah, sağ yarı beyaz

        img2 = img1.copy()

        img3 = Image.new("RGB", (400, 300), color=(255, 255, 255))
        draw3 = ImageDraw.Draw(img3)
        draw3.rectangle([0, 0, 400, 150], fill=(0, 0, 0))  # Üst yarı siyah, alt yarı beyaz (tamamen farklı gradyan)

        # İlk kare her zaman changed sayılır
        changed1, _ = manager.has_screen_changed(img1, threshold=4)
        self.assertTrue(changed1)

        # Aynı kare changed sayılmamalı
        changed2, diff2 = manager.has_screen_changed(img2, threshold=4)
        self.assertFalse(changed2)
        self.assertEqual(diff2, 0)

        # Tamamen farklı kare changed sayılmalı
        changed3, diff3 = manager.has_screen_changed(img3, threshold=4)
        self.assertTrue(changed3)
        self.assertGreaterEqual(diff3, 4)

    def test_config_operations(self):
        """Konfigürasyon okuma ve kaydetme testleri."""
        self.assertIsNotNone(config.gemini_model)
        self.assertGreater(config.capture_interval, 0)
        self.assertGreater(config.hash_threshold, 0)

    def test_worker_lifecycle(self):
        """Worker thread başlatma, duraklatma ve durdurma testi."""
        from core.worker import PrescriptionWorker
        manager = ScreenCaptureManager()
        analyzer = PrescriptionAnalyzer(api_key="test_dummy_key_1234567890123")

        worker = PrescriptionWorker(
            capture_manager=manager,
            analyzer=analyzer,
        )

        self.assertFalse(worker.is_running())
        self.assertFalse(worker.is_paused())

        worker.start()
        self.assertTrue(worker.is_running())

        worker.pause()
        self.assertTrue(worker.is_paused())

        worker.resume()
        self.assertFalse(worker.is_paused())

        worker.stop()
        self.assertFalse(worker.is_running())


if __name__ == "__main__":
    unittest.main()
