"""
ReçeteGöz - Kırmızı Flaş Uyarı Katmanı (Flash Overlay)
Hata tespit edildiğinde ekranı 1 saniyeliğine şeffaf kırmızı renkle kaplayıp
kullanıcıyı anında görsel olarak uyarır.
"""

import tkinter as tk
from typing import Optional
from config import config


class FlashOverlay:
    """Tam ekran şeffaf kırmızı uyarı katmanı."""

    @classmethod
    def trigger(
        cls,
        parent: Optional[tk.Misc] = None,
        duration_ms: Optional[int] = None,
        alpha: Optional[float] = None,
    ):
        """
        1 saniyelik kırmızı uyarı penceresini başlatır.

        Args:
            parent: Tkinter ana penceresi
            duration_ms: Flaş süresi (varsayılan: config.flash_duration_ms)
            alpha: Şeffaflık (varsayılan: config.flash_alpha)
        """
        duration = duration_ms or config.flash_duration_ms
        opacity = alpha or config.flash_alpha

        try:
            overlay = tk.Toplevel(parent)
            overlay.overrideredirect(True)

            # Ekran çözünürlüğünü al
            screen_w = overlay.winfo_screenwidth()
            screen_h = overlay.winfo_screenheight()
            overlay.geometry(f"{screen_w}x{screen_h}+0+0")

            # Kırmızı arka plan ve saydamlık
            overlay.configure(bg="#DC2626")  # Canlı uyarı kırmızısı (Tailwind Red 600)
            overlay.attributes("-topmost", True)

            try:
                overlay.attributes("-alpha", opacity)
            except Exception as e:
                print(f"[FlashOverlay] Alpha ayarı uygulanamadı: {e}")

            # Tıklamaları geçirmesi veya tıklanınca hemen kapanması için
            overlay.bind("<Button-1>", lambda e: overlay.destroy())

            # Belirtilen süre sonra otomatik kapat
            overlay.after(duration, lambda: cls._safe_destroy(overlay))

            # Sesli uyarı aktifse sistem sesi çıkar
            if config.sound_alert:
                try:
                    overlay.bell()
                except Exception:
                    pass

        except Exception as e:
            print(f"[FlashOverlay] Flaş overlay başlatılırken hata: {e}")

    @staticmethod
    def _safe_destroy(window: tk.Toplevel):
        try:
            if window and window.winfo_exists():
                window.destroy()
        except Exception:
            pass
