"""
ReçeteGöz - Hata Açıklama Modalı (Explanation Dialog)
Tespit edilen reçete hatasını, SGK SUT gerekçesini ve çözüm önerisini
modern bir kart arayüzünde kullanıcıya sunar.
"""

import tkinter as tk
import customtkinter as ctk
from typing import Optional
from core.ai_analyzer import PrescriptionAnalysisResult


class ExplanationDialog(ctk.CTkToplevel):
    """Modern ve şık hata açıklama penceresi."""

    def __init__(
        self,
        parent: tk.Misc,
        result: PrescriptionAnalysisResult,
    ):
        super().__init__(parent)

        self.result = result
        self.title("ReçeteGöz - Hata Analiz Detayı")
        self.geometry("560x520")
        self.minsize(480, 420)
        self.attributes("-topmost", True)

        # Arka plan ve stil ayarları
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#0F172A")  # Slate 900

        # Pencereyi ekranın ortasında konumlandır
        self._center_window(parent)

        # Sürüklenebilirlik
        self._offset_x = 0
        self._offset_y = 0

        self._build_ui()

    def _center_window(self, parent: tk.Misc):
        try:
            self.update_idletasks()
            w = 560
            h = 520
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            x = (sw - w) // 2
            y = (sh - h) // 2
            self.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def _build_ui(self):
        # Ana Konteyner
        main_frame = ctk.CTkFrame(
            self, fg_color="#1E293B", corner_radius=16, border_width=1, border_color="#EF4444"
        )
        main_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # Başlık ve Rozetler
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(18, 10))

        title_label = ctk.CTkLabel(
            header_frame,
            text="🚨 Reçete Hatası ve SUT Uyarısı",
            font=ctk.CTkFont(family="Inter", size=18, weight="bold"),
            text_color="#F87171",
        )
        title_label.pack(side="left")

        # Rozetler Satırı (Satır No & Alan)
        badges_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        badges_frame.pack(fill="x", padx=20, pady=(0, 10))

        if self.result.error_row is not None:
            row_badge = ctk.CTkLabel(
                badges_frame,
                text=f"📌 Satır #{self.result.error_row}",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#7F1D1D",
                text_color="#FECACA",
                corner_radius=8,
                padx=10,
                pady=4,
            )
            row_badge.pack(side="left", padx=(0, 8))

        if self.result.field_name:
            field_badge = ctk.CTkLabel(
                badges_frame,
                text=f"🏷️ Alan: {self.result.field_name}",
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color="#374151",
                text_color="#E5E7EB",
                corner_radius=8,
                padx=10,
                pady=4,
            )
            field_badge.pack(side="left")

        # Kısa Hata Özeti Kutusu
        short_msg = self.result.short_message or "Reçete kuralı ihlali tespit edildi."
        summary_card = ctk.CTkFrame(
            main_frame, fg_color="#450A0A", corner_radius=10, border_width=1, border_color="#991B1B"
        )
        summary_card.pack(fill="x", padx=20, pady=(0, 12))

        summary_label = ctk.CTkLabel(
            summary_card,
            text=f"⚠️ {short_msg}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FCA5A5",
            wraplength=480,
            justify="left",
            padx=12,
            pady=10,
        )
        summary_label.pack(fill="x")

        # Detaylı SUT / Tıbbi Açıklama (Scrollable Text)
        desc_label = ctk.CTkLabel(
            main_frame,
            text="📖 SGK SUT & Tıbbi Kesinti Gerekçesi:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#CBD5E1",
        )
        desc_label.pack(anchor="w", padx=20, pady=(0, 4))

        desc_box = ctk.CTkTextbox(
            main_frame,
            fg_color="#0F172A",
            text_color="#E2E8F0",
            font=ctk.CTkFont(size=13),
            corner_radius=8,
            border_width=1,
            border_color="#334155",
            wrap="word",
            height=110,
        )
        desc_box.pack(fill="x", padx=20, pady=(0, 12))
        desc_box.insert(
            "1.0",
            self.result.detailed_explanation
            or "Bu reçete kaydı mevcut SGK Sağlık Uygulama Tebliği kurallarına veya maksimum doz sınırlarına aykırılık içermektedir.",
        )
        desc_box.configure(state="disabled")

        # Çözüm / Düzeltme Önerisi Kutusu
        if self.result.suggested_fix:
            fix_label = ctk.CTkLabel(
                main_frame,
                text="💡 Önerilen Düzeltme Adımı:",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#34D399",
            )
            fix_label.pack(anchor="w", padx=20, pady=(0, 4))

            fix_card = ctk.CTkFrame(
                main_frame, fg_color="#064E3B", corner_radius=8, border_width=1, border_color="#059669"
            )
            fix_card.pack(fill="x", padx=20, pady=(0, 14))

            fix_text = ctk.CTkLabel(
                fix_card,
                text=f"✓ {self.result.suggested_fix}",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color="#A7F3D0",
                wraplength=480,
                justify="left",
                padx=12,
                pady=8,
            )
            fix_text.pack(fill="x")

        # Alt Butonlar
        bottom_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=(0, 16), side="bottom")

        copy_btn = ctk.CTkButton(
            bottom_frame,
            text="📋 Raporu Kopyala",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#334155",
            hover_color="#475569",
            text_color="#F8FAFC",
            corner_radius=8,
            width=140,
            command=self._copy_to_clipboard,
        )
        copy_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            bottom_frame,
            text="Kapat",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="#FFFFFF",
            corner_radius=8,
            width=100,
            command=self.destroy,
        )
        close_btn.pack(side="right")

    def _copy_to_clipboard(self):
        """Hata özetini panoya kopyalar."""
        text = (
            f"--- ReçeteGöz Hata Bildirimi ---\n"
            f"Satır: {self.result.error_row or 'Belirtilmemiş'}\n"
            f"Alan: {self.result.field_name or 'Belirtilmemiş'}\n"
            f"Uyarı: {self.result.short_message}\n"
            f"Açıklama: {self.result.detailed_explanation}\n"
            f"Öneri: {self.result.suggested_fix or 'Belirtilmemiş'}\n"
        )
        try:
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except Exception as e:
            print(f"[ExplanationDialog] Kopyalama hatası: {e}")
