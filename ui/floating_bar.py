"""
ReçeteGöz - Sürüklenebilir Kayan Araç Çubuğu (Floating Toolbar)
Ekranda daima en üstte duran, modern cam efektli/karanlık temalı,
durum bildirimlerini ve kontrol butonlarını içeren mini kontrol paneli.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional
from PIL import Image

from core.ai_analyzer import PrescriptionAnalysisResult, PrescriptionAnalyzer
from core.screen_capture import ScreenCaptureManager
from core.worker import PrescriptionWorker
from ui.flash_overlay import FlashOverlay
from ui.explanation_dialog import ExplanationDialog
from ui.settings_dialog import SettingsDialog
from config import config


class FloatingBar(ctk.CTk):
    """Her zaman en üstte duran sürüklenebilir mini araç çubuğu."""

    def __init__(self):
        super().__init__()

        # Pencere Özellikleri
        self.overrideredirect(True)  # Kenarlıksız pencere
        self.attributes("-topmost", True)  # Daima en üstte
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")  # Arka plan slate 900

        # Varsayılan Konum (Ekranın sağ üst köşesi)
        self.bar_width = 380
        self.bar_height = 54
        self._initial_position()

        # Sürükleme (Drag & Drop) koordinatları
        self._drag_start_x = 0
        self._drag_start_y = 0

        # Çekirdek Nesneler
        self.capture_manager = ScreenCaptureManager()
        self.analyzer = PrescriptionAnalyzer(
            api_key=config.gemini_api_key, model_name=config.gemini_model
        )
        self.last_error_result: Optional[PrescriptionAnalysisResult] = None
        self.last_error_image: Optional[Image.Image] = None

        # Arka Plan Worker'ı
        self.worker = PrescriptionWorker(
            capture_manager=self.capture_manager,
            analyzer=self.analyzer,
            on_status_change=self._on_worker_status_change,
            on_error_detected=self._on_worker_error_detected,
            on_clean_detected=self._on_worker_clean_detected,
        )

        # UI Bileşenlerini Kur
        self._build_ui()
        self._bind_drag_events()

        # Otomatik Başlatma
        if config.auto_start:
            self.worker.start()

    def _initial_position(self):
        """Pencereyi ekranın sağ üst tarafına hizalar."""
        try:
            screen_w = self.winfo_screenwidth()
            x = screen_w - self.bar_width - 24
            y = 36
            self.geometry(f"{self.bar_width}x{self.bar_height}+{x}+{y}")
        except Exception:
            self.geometry(f"{self.bar_width}x{self.bar_height}+800+50")

    def _bind_drag_events(self):
        """Pencerenin herhangi bir yerinden fare ile tutulup taşınmasını sağlar."""
        self.bind("<ButtonPress-1>", self._on_drag_start)
        self.bind("<B1-Motion>", self._on_drag_motion)
        self.main_container.bind("<ButtonPress-1>", self._on_drag_start)
        self.main_container.bind("<B1-Motion>", self._on_drag_motion)
        self.title_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.title_label.bind("<B1-Motion>", self._on_drag_motion)
        self.status_label.bind("<ButtonPress-1>", self._on_drag_start)
        self.status_label.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event):
        self._drag_start_x = event.x
        self._drag_start_y = event.y

    def _on_drag_motion(self, event):
        x = self.winfo_x() + (event.x - self._drag_start_x)
        y = self.winfo_y() + (event.y - self._drag_start_y)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        # Ana Çerçeve (Pill / Kapsül Tasarım)
        self.main_container = ctk.CTkFrame(
            self,
            fg_color="#1E293B",
            corner_radius=20,
            border_width=1.5,
            border_color="#334155",
        )
        self.main_container.pack(fill="both", expand=True, padx=2, pady=2)

        # 1. Sol: Logo ve İsim
        left_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        left_frame.pack(side="left", padx=(10, 6), pady=6)

        self.status_dot = ctk.CTkLabel(
            left_frame,
            text="●",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#10B981",  # Yeşil
            width=14,
        )
        self.status_dot.pack(side="left", padx=(0, 4))

        self.title_label = ctk.CTkLabel(
            left_frame,
            text="ReçeteGöz",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color="#F8FAFC",
        )
        self.title_label.pack(side="left", padx=(0, 6))

        # 2. Orta: Durum Metni
        self.status_label = ctk.CTkLabel(
            self.main_container,
            text="Dinleniyor...",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            width=110,
            anchor="w",
        )
        self.status_label.pack(side="left", padx=(0, 4), fill="x", expand=True)

        # 3. Sağ: Aksiyon Butonları
        right_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        right_frame.pack(side="right", padx=(4, 8), pady=6)

        # Hatayı Açıkla Butonu (Hata tespit edildiğinde canlılaşır)
        self.explain_btn = ctk.CTkButton(
            right_frame,
            text="🚨 Hatayı Açıkla",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="#FFFFFF",
            corner_radius=12,
            height=28,
            width=100,
            command=self._open_explanation_modal,
        )
        # Başlangıçta gizli tut veya pasif yap
        self.explain_btn.pack_forget()

        # Duraklat / Başlat Butonu
        self.pause_btn = ctk.CTkButton(
            right_frame,
            text="⏸",
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            corner_radius=12,
            height=28,
            width=28,
            command=self._toggle_pause,
        )
        self.pause_btn.pack(side="left", padx=2)

        # Ayarlar Butonu
        self.settings_btn = ctk.CTkButton(
            right_frame,
            text="⚙",
            font=ctk.CTkFont(size=12),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            corner_radius=12,
            height=28,
            width=28,
            command=self._open_settings_modal,
        )
        self.settings_btn.pack(side="left", padx=2)

        # Kapat Butonu
        self.close_btn = ctk.CTkButton(
            right_frame,
            text="✕",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="transparent",
            hover_color="#EF4444",
            text_color="#94A3B8",
            corner_radius=12,
            height=28,
            width=24,
            command=self._on_close,
        )
        self.close_btn.pack(side="left", padx=(2, 0))

    # --- Thread-Safe Worker Callbacks ---

    def _on_worker_status_change(self, code: str, message: str):
        """Worker'dan gelen durum güncellemelerini ana UI döngüsüne iletir."""
        self.after(0, lambda: self._apply_status_update(code, message))

    def _apply_status_update(self, code: str, message: str):
        if code == "LISTENING":
            self.status_dot.configure(text_color="#10B981")  # Yeşil
            self.status_label.configure(text="Dinleniyor...", text_color="#94A3B8")
            self.main_container.configure(border_color="#334155")
        elif code == "ANALYZING":
            self.status_dot.configure(text_color="#F59E0B")  # Sarı / Turuncu
            self.status_label.configure(text="Analiz Ediliyor...", text_color="#FCD34D")
            self.main_container.configure(border_color="#F59E0B")
        elif code == "CLEAN":
            self.status_dot.configure(text_color="#10B981")  # Yeşil
            self.status_label.configure(text="Reçete Uygun", text_color="#6EE7B7")
            self.main_container.configure(border_color="#059669")
            self.explain_btn.pack_forget()
        elif code == "ERROR_FOUND":
            self.status_dot.configure(text_color="#EF4444")  # Kırmızı
            self.status_label.configure(text="Hata Bulundu!", text_color="#FCA5A5")
            self.main_container.configure(border_color="#EF4444")
            self.explain_btn.pack(side="left", padx=2, before=self.pause_btn)
        elif code == "PAUSED":
            self.status_dot.configure(text_color="#64748B")  # Gri
            self.status_label.configure(text="Duraklatıldı", text_color="#94A3B8")
            self.main_container.configure(border_color="#334155")
        elif code == "NO_KEY":
            self.status_dot.configure(text_color="#EAB308")  # Sarı
            self.status_label.configure(text="API Key Gerekli", text_color="#FDE047")
            self.main_container.configure(border_color="#EAB308")
        else:
            self.status_label.configure(text=message[:18], text_color="#94A3B8")

    def _on_worker_error_detected(
        self, result: PrescriptionAnalysisResult, image: Image.Image
    ):
        """Hata tespit edildiğinde UI döngüsünde flaş patlatır ve hata kartını hazırlar."""
        self.after(0, lambda: self._apply_error_detected(result, image))

    def _apply_error_detected(
        self, result: PrescriptionAnalysisResult, image: Image.Image
    ):
        self.last_error_result = result
        self.last_error_image = image

        # 1. Kırmızı Tam Ekran Flaş Uyarısı
        FlashOverlay.trigger(
            self,
            duration_ms=config.flash_duration_ms,
            alpha=config.flash_alpha,
        )

        # 2. Butonu görünür yap ve genişliği güncelle
        self.explain_btn.pack(side="left", padx=2, before=self.pause_btn)

    def _on_worker_clean_detected(self, result: PrescriptionAnalysisResult):
        """Reçete temiz olduğunda UI döngüsünde günceller."""
        self.after(0, lambda: self._apply_clean_detected(result))

    def _apply_clean_detected(self, result: PrescriptionAnalysisResult):
        self.last_error_result = None
        self.explain_btn.pack_forget()

    # --- UI Etkileşimleri ---

    def _toggle_pause(self):
        """Analizi duraklatır veya devam ettirir."""
        if self.worker.is_paused():
            self.worker.resume()
            self.pause_btn.configure(text="⏸", fg_color="#334155")
        else:
            self.worker.pause()
            self.pause_btn.configure(text="▶", fg_color="#0284C7")

    def _open_explanation_modal(self):
        """Son hata için detay kartını açar."""
        if self.last_error_result:
            dialog = ExplanationDialog(self, self.last_error_result)
            dialog.focus()

    def _open_settings_modal(self):
        """Ayarlar penceresini açar."""
        dialog = SettingsDialog(
            self,
            on_save_callback=self._on_settings_saved,
            on_test_callback=self._on_test_triggered,
        )
        dialog.focus()

    def _on_settings_saved(self):
        """Ayarlar kaydedildiğinde analyzer ve worker'ı günceller."""
        self.analyzer.update_api_key(
            new_api_key=config.gemini_api_key,
            model_name=config.gemini_model,
        )
        if config.is_api_key_set():
            self._apply_status_update("LISTENING", "Dinleniyor...")
            self.worker.trigger_immediate_analysis()

    def _on_test_triggered(self):
        """Ayarlar modalından anlık test analizi tetikler."""
        self.worker.trigger_immediate_analysis()

    def _on_close(self):
        """Uygulamayı güvenli şekilde kapatır."""
        self.worker.stop()
        self.destroy()
