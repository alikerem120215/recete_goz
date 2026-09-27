"""
ReçeteGöz - Eczane Botanik / Medula Reçete Kontrol Asistanı
Ana Uygulama Giriş Noktası (Entry Point)
"""

import sys
import os
import signal
from pathlib import Path

# Proje kök dizinini sys.path'e ekle
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from config import config
from ui.floating_bar import FloatingBar


def main():
    print("=" * 60)
    print("  ReçeteGöz - Eczane Reçete ve SUT Kontrol Asistanı")
    print("  Google GenAI (gemini-2.5-flash) Tabanlı Gerçek Zamanlı Denetçi")
    print("=" * 60)

    if not config.is_api_key_set():
        print("[Uyarı] GEMINI_API_KEY tanımlı değil. Lütfen araç çubuğundaki '⚙' ayarlar butonundan giriniz.")
    else:
        print(f"[Bilgi] Aktif Model: {config.gemini_model}")
        print(f"[Bilgi] Tarama Aralığı: {config.capture_interval} sn | Hash Eşiği: {config.hash_threshold}")

    app = FloatingBar()

    # Terminalden Ctrl+C ile temiz çıkış yönetimi
    def signal_handler(sig, frame):
        print("\n[Bilgi] ReçeteGöz kapatılıyor...")
        try:
            app.worker.stop()
            app.destroy()
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    print("[Hazır] Araç çubuğu başlatıldı. Ekranın sağ üst köşesinden sürükleyebilirsiniz.")
    app.mainloop()


if __name__ == "__main__":
    main()
