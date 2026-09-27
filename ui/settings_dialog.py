"""
ReçeteGöz - Ayarlar Modalı (Settings Dialog)
API Anahtarı, model seçimi, tarama frekansı ve hassasiyet ayarlarını yönetir.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Callable, Optional
from config import config


class SettingsDialog(ctk.CTkToplevel):
    """Kullanıcı tercihleri ve API konfigürasyonu penceresi."""

    def __init__(
        self,
        parent: tk.Misc,
        on_save_callback: Optional[Callable[[], None]] = None,
        on_test_callback: Optional[Callable[[], None]] = None,
    ):
        super().__init__(parent)

        self.on_save_callback = on_save_callback
        self.on_test_callback = on_test_callback

        self.title("ReçeteGöz - Ayarlar")
        self.geometry("520x480")
        self.minsize(460, 420)
        self.attributes("-topmost", True)

        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")

        self._center_window(parent)
        self._build_ui()

    def _center_window(self, parent: tk.Misc):
        try:
            self.update_idletasks()
            w = 520
            h = 480
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self):
        # Ana Çerçeve
        main_frame = ctk.CTkFrame(
            self, fg_color="#1E293B", corner_radius=16, border_width=1, border_color="#334155"
        )
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # Başlık
        title_label = ctk.CTkLabel(
            main_frame,
            text="⚙️ ReçeteGöz Asistan Ayarları",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color="#38BDF8",
        )
        title_label.pack(anchor="w", padx=20, pady=(18, 14))

        # 1. API Anahtarı
        api_label = ctk.CTkLabel(
            main_frame,
            text="Google Gemini API Anahtarı:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0",
        )
        api_label.pack(anchor="w", padx=20, pady=(0, 4))

        self.api_entry = ctk.CTkEntry(
            main_frame,
            placeholder_text="AIzaSy...",
            show="*",
            fg_color="#0F172A",
            border_color="#475569",
            text_color="#F8FAFC",
            height=36,
            corner_radius=8,
        )
        self.api_entry.pack(fill="x", padx=20, pady=(0, 12))
        if config.gemini_api_key:
            self.api_entry.insert(0, config.gemini_api_key)

        # 2. Model Seçimi
        model_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        model_frame.pack(fill="x", padx=20, pady=(0, 12))

        model_label = ctk.CTkLabel(
            model_frame,
            text="Model:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0",
        )
        model_label.pack(side="left", padx=(0, 10))

        self.model_combo = ctk.CTkComboBox(
            model_frame,
            values=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"],
            fg_color="#0F172A",
            button_color="#38BDF8",
            border_color="#475569",
            dropdown_fg_color="#1E293B",
            corner_radius=8,
            width=200,
        )
        self.model_combo.pack(side="left")
        self.model_combo.set(config.gemini_model)

        # 3. Tarama Sıklığı (Saniye)
        interval_label = ctk.CTkLabel(
            main_frame,
            text=f"Ekran Tarama Sıklığı: {config.capture_interval:.1f} sn",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0",
        )
        interval_label.pack(anchor="w", padx=20, pady=(0, 2))

        self.interval_slider = ctk.CTkSlider(
            main_frame,
            from_=2.0,
            to=15.0,
            number_of_steps=26,
            button_color="#38BDF8",
            progress_color="#0284C7",
            command=lambda val: interval_label.configure(
                text=f"Ekran Tarama Sıklığı: {val:.1f} sn"
            ),
        )
        self.interval_slider.pack(fill="x", padx=20, pady=(0, 12))
        self.interval_slider.set(config.capture_interval)

        # 4. Hash Değişim Hassasiyeti
        hash_label = ctk.CTkLabel(
            main_frame,
            text=f"Değişim Algılama Hassasiyeti (Eşik): {config.hash_threshold}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#E2E8F0",
        )
        hash_label.pack(anchor="w", padx=20, pady=(0, 2))

        self.hash_slider = ctk.CTkSlider(
            main_frame,
            from_=2,
            to=20,
            number_of_steps=18,
            button_color="#38BDF8",
            progress_color="#0284C7",
            command=lambda val: hash_label.configure(
                text=f"Değişim Algılama Hassasiyeti (Eşik): {int(val)}"
            ),
        )
        self.hash_slider.pack(fill="x", padx=20, pady=(0, 14))
        self.hash_slider.set(config.hash_threshold)

        # 5. Sesli Uyarı Onay Kutusu
        self.sound_checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Hata anında sesli uyarı ver",
            font=ctk.CTkFont(size=13),
            text_color="#E2E8F0",
            checkmark_color="#FFFFFF",
            fg_color="#38BDF8",
            hover_color="#0284C7",
        )
        self.sound_checkbox.pack(anchor="w", padx=20, pady=(0, 16))
        if config.sound_alert:
            self.sound_checkbox.select()
        else:
            self.sound_checkbox.deselect()

        # Alt Butonlar
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 16), side="bottom")

        if self.on_test_callback:
            test_btn = ctk.CTkButton(
                bottom_frame,
                text="⚡ Şimdi Test Et",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#334155",
                hover_color="#475569",
                text_color="#F8FAFC",
                corner_radius=8,
                width=120,
                command=self._on_test_clicked,
            )
            test_btn.pack(side="left")

        save_btn = ctk.CTkButton(
            bottom_frame,
            text="Kaydet & Uygula",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284C7",
            hover_color="#0369A1",
            text_color="#FFFFFF",
            corner_radius=8,
            width=130,
            command=self._on_save_clicked,
        )
        save_btn.pack(side="right")

    def _on_test_clicked(self):
        """Test taraması tetikler."""
        if self.on_test_callback:
            self.on_test_callback()

    def _on_save_clicked(self):
        """Ayarları config nesnesine aktarır ve kaydeder."""
        config.gemini_api_key = self.api_entry.get().strip()
        config.gemini_model = self.model_combo.get().strip()
        config.capture_interval = float(self.interval_slider.get())
        config.hash_threshold = int(self.hash_slider.get())
        config.sound_alert = bool(self.sound_checkbox.get())
        config.save()

        if self.on_save_callback:
            self.on_save_callback()

        self.destroy()
