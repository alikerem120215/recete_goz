"""
ReçeteGöz - Simülasyon ve Demo Testi
Canlı API çağrısı yapmadan arayüzün (Floating Bar, Flash Overlay, Explanation Dialog)
tüm görsel ve interaktif özelliklerini simüle eder.
"""

import sys
import time
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from ui.floating_bar import FloatingBar
from core.ai_analyzer import PrescriptionAnalysisResult
from PIL import Image


def simulate_scenario(app: FloatingBar):
    """3 saniye sonra simüle edilmiş bir reçete hatası tetikler."""
    time.sleep(3)

    print("\n[Simülasyon] 1. Aşama: Ekran taranıyor (Analiz Ediliyor)...")
    app._apply_status_update("ANALYZING", "Ekran Değişti, Analiz Ediliyor...")

    time.sleep(2)

    print("[Simülasyon] 2. Aşama: SGK SUT Doz Aşımı Hatası Tespit Edildi!")
    mock_result = PrescriptionAnalysisResult(
        prescription_found=True,
        has_error=True,
        error_row=2,
        field_name="Doz ve Periyot",
        short_message="Doz Aşımı: Günde 2x1 yerine 3x1 girilmiş",
        detailed_explanation="SGK Sağlık Uygulama Tebliği (SUT) Ek-4/D Listesi ve ilgili prospektüs kuralına göre bu etken maddenin günlük maksimum dozu 2 adettir. 3x1 dozajı kesinti sebebidir.",
        suggested_fix="İlaç dozunu günde 2x1 (veya 1x2) olarak düzeltiniz ve kutu adedini yeniden hesaplayınız.",
    )

    dummy_img = Image.new("RGB", (800, 600), color=(240, 240, 240))
    app._apply_error_detected(mock_result, dummy_img)
    app._apply_status_update("ERROR_FOUND", f"Hata: {mock_result.short_message}")
    print("[Simülasyon] Flaş uyarısı tetiklendi ve 'Hatayı Açıkla' butonu aktifleşti.")


def main():
    print("=" * 60)
    print("  ReçeteGöz - Demo & Arayüz Simülasyonu")
    print("  3 saniye sonra otomatik olarak örnek bir SUT doz aşımı simüle edilecektir.")
    print("=" * 60)

    app = FloatingBar()

    # Simülasyonu ayrı bir thread'de başlat
    sim_thread = threading.Thread(target=simulate_scenario, args=(app,), daemon=True)
    sim_thread.start()

    app.mainloop()


if __name__ == "__main__":
    main()
