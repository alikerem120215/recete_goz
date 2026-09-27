"""
ReçeteGöz - Arka Plan Analiz İş Parçacığı (Worker Thread)
Ekranı periyodik olarak yakalar, görüntü hash farkını denetler,
AI analizini çalıştırır ve thread-safe arayüz bildirimleri üretir.
"""

import time
import threading
from typing import Callable, Optional
from PIL import Image

from .screen_capture import ScreenCaptureManager
from .ai_analyzer import PrescriptionAnalyzer, PrescriptionAnalysisResult
from config import config


class PrescriptionWorker:
    """Arka plan tarama ve analiz döngüsünü yöneten iş parçacığı sınıfı."""

    def __init__(
        self,
        capture_manager: ScreenCaptureManager,
        analyzer: PrescriptionAnalyzer,
        on_status_change: Optional[Callable[[str, str], None]] = None,
        on_error_detected: Optional[
            Callable[[PrescriptionAnalysisResult, Image.Image], None]
        ] = None,
        on_clean_detected: Optional[
            Callable[[PrescriptionAnalysisResult], None]
        ] = None,
    ):
        self.capture_manager = capture_manager
        self.analyzer = analyzer

        # Callback fonksiyonları (Thread-safe arayüz bildirimleri için)
        self.on_status_change = on_status_change
        self.on_error_detected = on_error_detected
        self.on_clean_detected = on_clean_detected

        self._running = False
        self._paused = False
        self._thread: Optional[threading.Thread] = None
        self._wake_event = threading.Event()
        self._lock = threading.Lock()

        self.last_result: Optional[PrescriptionAnalysisResult] = None
        self.last_image: Optional[Image.Image] = None

    def start(self):
        """Worker iş parçacığını başlatır."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._paused = False
            self._wake_event.clear()
            self._thread = threading.Thread(
                target=self._run_loop, name="PrescriptionWorkerThread", daemon=True
            )
            self._thread.start()

    def pause(self):
        """Analiz döngüsünü geçici olarak duraklatır."""
        self._paused = True
        self._notify_status("PAUSED", "Analiz Duraklatıldı")

    def resume(self):
        """Duraklatılan analiz döngüsünü devam ettirir."""
        self._paused = False
        self._notify_status("LISTENING", "Dinleniyor...")
        self._wake_event.set()

    def is_paused(self) -> bool:
        """İş parçacığının duraklatılıp duraklatılmadığını döner."""
        return self._paused

    def is_running(self) -> bool:
        """İş parçacığının aktif olup olmadığını döner."""
        return self._running

    def stop(self):
        """İş parçacığını güvenli şekilde sonlandırır."""
        with self._lock:
            self._running = False
            self._wake_event.set()

    def trigger_immediate_analysis(self):
        """Bekleme süresini atlayıp anında ekran görüntüsü alıp analiz eder."""
        self.capture_manager.reset_hash()
        self._wake_event.set()

    def _notify_status(self, code: str, message: str):
        if self.on_status_change:
            try:
                self.on_status_change(code, message)
            except Exception as e:
                print(f"[Worker] on_status_change callback hatası: {e}")

    def _run_loop(self):
        """Ana arka plan çalışma döngüsü."""
        self._notify_status("LISTENING", "Dinleniyor (Reçete Ekranı Bekleniyor)...")

        while self._running:
            try:
                if self._paused:
                    time.sleep(0.5)
                    continue

                # API anahtarı kontrolü
                if not config.is_api_key_set():
                    self._notify_status(
                        "NO_KEY", "Gemini API Anahtarı Eksik (Ayarlardan Giriniz)"
                    )
                    time.sleep(2.0)
                    continue

                # 1. Ekran görüntüsü yakala
                img = self.capture_manager.capture_screen()

                # 2. Hash farkı kontrolü (Gereksiz API maliyetini önleme)
                changed, diff = self.capture_manager.has_screen_changed(
                    img, threshold=config.hash_threshold
                )

                if not changed:
                    # Ekran değişmedi, bekle
                    self._wake_event.wait(timeout=config.capture_interval)
                    self._wake_event.clear()
                    continue

                # 3. Ekran değişti, analiz başlat
                self._notify_status("ANALYZING", "Ekran Değişti, Analiz Ediliyor...")

                # Görüntüyü AI için optimize et
                _, optimized_img = self.capture_manager.optimize_for_ai(img)

                # GenAI API çağrısı
                result = self.analyzer.analyze_prescription(optimized_img)
                self.last_result = result
                self.last_image = optimized_img

                # 4. Sonuç değerlendirme
                if result.has_error:
                    # HATA TESPİT EDİLDİ
                    self._notify_status(
                        "ERROR_FOUND",
                        f"Hata: {result.short_message or 'Reçete Uyumsuzluğu'}",
                    )
                    if self.on_error_detected:
                        try:
                            self.on_error_detected(result, optimized_img)
                        except Exception as e:
                            print(f"[Worker] on_error_detected hatası: {e}")

                elif result.prescription_found:
                    # REÇETE BULUNDU VE TEMİZ
                    self._notify_status(
                        "CLEAN",
                        result.short_message or "Reçete Kurallara Uygun",
                    )
                    if self.on_clean_detected:
                        try:
                            self.on_clean_detected(result)
                        except Exception as e:
                            print(f"[Worker] on_clean_detected hatası: {e}")

                else:
                    # Reçete ekranı yok veya tespit edilmedi
                    self._notify_status("LISTENING", "Dinleniyor (Reçete Ekranı Aranıyor)...")

            except Exception as e:
                print(f"[Worker] Döngü hatası: {e}")
                self._notify_status("ERROR", f"Hata: {str(e)[:50]}")

            # Bir sonraki periyoda kadar bekle (veya manuel tetikleme gelirse uyan)
            self._wake_event.wait(timeout=config.capture_interval)
            self._wake_event.clear()
