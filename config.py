"""
ReçeteGöz - Konfigürasyon Yönetim Modülü
Çevre değişkenleri, varsayılan ayarlar ve kullanıcı tercihlerini yönetir.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Temel Dizinler
BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
SETTINGS_FILE = BASE_DIR / "settings.json"

# .env dosyasını yükle
load_dotenv(dotenv_path=ENV_FILE)


class Config:
    """Uygulama genel yapılandırma sınıfı."""

    def __init__(self):
        self.load()

    def load(self):
        """Ayarları .env ve settings.json dosyalarından yükler."""
        # Varsayılanlar & .env
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
        self.capture_interval: float = float(os.getenv("CAPTURE_INTERVAL", "5.0"))
        self.hash_threshold: int = int(os.getenv("HASH_THRESHOLD", "6"))
        self.flash_duration_ms: int = int(os.getenv("FLASH_DURATION_MS", "1000"))
        self.flash_alpha: float = float(os.getenv("FLASH_ALPHA", "0.38"))
        self.sound_alert: bool = True
        self.auto_start: bool = True

        # Kullanıcı kayıtlı ayarları varsa üzerine yaz
        if SETTINGS_FILE.exists():
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if "gemini_api_key" in data and data["gemini_api_key"]:
                        self.gemini_api_key = data["gemini_api_key"].strip()
                    if "gemini_model" in data:
                        self.gemini_model = data["gemini_model"].strip()
                    if "capture_interval" in data:
                        self.capture_interval = float(data["capture_interval"])
                    if "hash_threshold" in data:
                        self.hash_threshold = int(data["hash_threshold"])
                    if "flash_duration_ms" in data:
                        self.flash_duration_ms = int(data["flash_duration_ms"])
                    if "flash_alpha" in data:
                        self.flash_alpha = float(data["flash_alpha"])
                    if "sound_alert" in data:
                        self.sound_alert = bool(data["sound_alert"])
            except Exception as e:
                print(f"[Config] Ayarlar dosyası yüklenirken hata: {e}")

    def save(self):
        """Mevcut ayarları settings.json ve .env dosyasına kaydeder."""
        data = {
            "gemini_api_key": self.gemini_api_key,
            "gemini_model": self.gemini_model,
            "capture_interval": self.capture_interval,
            "hash_threshold": self.hash_threshold,
            "flash_duration_ms": self.flash_duration_ms,
            "flash_alpha": self.flash_alpha,
            "sound_alert": self.sound_alert,
        }
        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[Config] Ayarlar kaydedilirken hata: {e}")

        # .env dosyasını da güncelle
        try:
            with open(ENV_FILE, "w", encoding="utf-8") as f:
                f.write(f"GEMINI_API_KEY={self.gemini_api_key}\n")
                f.write(f"GEMINI_MODEL={self.gemini_model}\n")
                f.write(f"CAPTURE_INTERVAL={self.capture_interval}\n")
                f.write(f"HASH_THRESHOLD={self.hash_threshold}\n")
                f.write(f"FLASH_DURATION_MS={self.flash_duration_ms}\n")
                f.write(f"FLASH_ALPHA={self.flash_alpha}\n")
        except Exception as e:
            print(f"[Config] .env kaydedilirken hata: {e}")

    def is_api_key_set(self) -> bool:
        """API anahtarının tanımlı olup olmadığını döner."""
        return bool(self.gemini_api_key and len(self.gemini_api_key) > 10)


# Global tekil yapılandırma örneği
config = Config()
