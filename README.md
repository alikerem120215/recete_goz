# 🩺 ReçeteGöz - Eczane Botanik / Medula Reçete Kontrol Asistanı

Türkiye'deki eczanelerde kullanılan reçete kayıt/kontrol yazılımlarında (Botanik, Medula, TEBEOS, E-Reçete vb.) reçete girilirken yapılan **doz aşımı, rapor-teşhis uyumsuzluğu, periyot ve kutu adedi hatalarını** gerçek zamanlı tespit eden akıllı bir masaüstü asistanıdır.

---

## 🌟 Temel Özellikler

1. **Sürüklenebilir Kayan Araç Çubuğu (Floating Toolbar):**
   - Ekranda daima en üstte (`topmost`) duran, kenarlıksız (`overrideredirect`), mouse ile istenilen yere taşınabilen şık mini panel.
   - Canlı durum göstergeleri (🟢 Dinleniyor, 🟡 Analiz Ediliyor, 🔴 Hata Bulundu, ⚪ Duraklatıldı).
   - Duraklat/Devam Et (⏯️) ve Ayarlar (⚙️) butonları.
   - Hata tespit edildiğinde canlı kırmızı renkte beliren **"🚨 Hatayı Açıkla"** butonu.

2. **Periyodik Ekran Yakalama & Akıllı Hash Filtreleme:**
   - Arka planda ekranı periyodik olarak yakalama (`mss`).
   - *Sıfır Gereksiz API Maliyeti:* Önceki kare ile yeni kare arasında kayda değer piksel/hash farkı yoksa (`imagehash`) API çağrısı yapılmaz.

3. **Google GenAI SDK Tabanlı Yapay Zeka Analizi (`google-genai`):**
   - En güncel `from google import genai` kütüphanesi ve `gemini-2.5-flash` modeli.
   - Pydantic şeması ile yapılandırılmış JSON çıktısı (`PrescriptionAnalysisResult`):
     - `has_error`: Hata/kesinti riski var mı?
     - `error_row`: Hatalı ilaç/satır sıra numarası.
     - `field_name`: Doz, Periyot, Teşhis Kodu (ICD-10), Rapor Süresi vb.
     - `short_message`: Kısa ve net hata başlığı.
     - `detailed_explanation`: SGK Sağlık Uygulama Tebliği (SUT) kuralı ve kesinti gerekçesi.
     - `suggested_fix`: Eczacının yapması gereken düzeltme adımı.

4. **1 Saniyelik Kırmızı Flaş Uyarısı (Overlay Flash):**
   - Hata tespit edildiğinde ekran boyutunda şeffaf kırmızı pencere (`alpha=0.38`) 1 saniye yanıp söner ve otomatik kapanır.

5. **"Hatayı Açıkla" Modal Bilgi Kartı:**
   - Hatanın bulunduğu satırı, alanı, SUT maddesini ve somut çözüm önerisini gösteren şık karanlık tema bilgi kartı.

---

## 📁 Proje Dizin Yapısı

```text
recete_goz/
├── .env.example              # Örnek çevre değişkenleri
├── .env                      # API anahtarı ve yerel ayarlar
├── requirements.txt          # Python bağımlılıkları
├── config.py                 # Konfigürasyon yönetimi (.env & settings.json)
├── main.py                   # Canlı uygulama başlatıcı
├── simulate_demo.py          # Görsel test & demo simülasyonu
├── tests/
│   └── test_recete_goz.py    # Otomatik birim testleri
├── core/
│   ├── __init__.py
│   ├── screen_capture.py     # MSS ile ekran alma ve hash karşılaştırma
│   ├── ai_analyzer.py        # google-genai structured output entegrasyonu
│   └── worker.py             # Thread-safe arka plan analiz döngüsü
└── ui/
    ├── __init__.py
    ├── floating_bar.py       # Sürüklenebilir mini araç çubuğu
    ├── flash_overlay.py      # 1 saniyelik tam ekran kırmızı uyarı
    ├── explanation_dialog.py # Detaylı hata açıklaması modalı
    └── settings_dialog.py    # API Anahtarı ve hassasiyet ayarları modalı
```

---

## 🚀 Kurulum ve Çalıştırma

### 1. Bağımlılıkları Yükleme
```bash
pip install -r requirements.txt
```

### 2. API Anahtarını Tanımlama
`.env` dosyasını açıp Google Gemini API anahtarınızı ekleyin veya uygulama açıldığında araç çubuğundaki **⚙️ (Ayarlar)** butonundan girin:
```env
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-2.5-flash
```

### 3. Uygulamayı Başlatma
```bash
python main.py
```

### 4. Simülasyon / Demo Modu (API Anahtarsız Test)
Arayüzü ve flaş uyarısını test etmek için:
```bash
python simulate_demo.py
```

### 5. Birim Testlerini Çalıştırma
```bash
python tests/test_recete_goz.py
```
