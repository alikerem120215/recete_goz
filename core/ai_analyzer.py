"""
ReçeteGöz - AI Analiz Modülü (Google GenAI SDK)
Google GenAI SDK (gemini-2.5-flash) ve Pydantic Structured Output kullanarak
ekran görüntüsündeki reçete kayıtlarını SGK SUT ve tıbbi kurallara göre denetler.
"""

from typing import Optional
from pydantic import BaseModel, Field
from PIL import Image
from google import genai
from google.genai import types


class PrescriptionAnalysisResult(BaseModel):
    """Reçete analiz sonucunu temsil eden Pydantic veri modeli."""

    prescription_found: bool = Field(
        default=False,
        description="Ekran görüntüsünde bir eczane reçete giriş/kontrol ekranı (Medula, Botanik, E-Reçete vb.) tespit edildi mi?",
    )
    has_error: bool = Field(
        default=False,
        description="Reçetede SGK SUT kesinti riski, doz aşımı, periyot veya rapor uyumsuzluğu gibi herhangi bir hata var mı?",
    )
    error_row: Optional[int] = Field(
        default=None,
        description="Hatalı veya uyarı gerektiren ilacın satır/sıra numarası (örn: 1, 2, 3...)",
    )
    field_name: Optional[str] = Field(
        default=None,
        description="Hatalı alanın adı (Örn: 'Doz', 'Periyot', 'Kutu Adedi', 'ICD-10 / Teşhis', 'Rapor Dozu', 'Kullanım Süresi')",
    )
    short_message: str = Field(
        default="",
        description="Kısa, net ve dikkat çekici hata uyarısı (Örn: 'Doz Aşımı: Günde 2x1 yerine 3x1 girilmiş')",
    )
    detailed_explanation: str = Field(
        default="",
        description="SGK Sağlık Uygulama Tebliği (SUT) kuralı, kesinti riski veya tıbbi doz aşımı gerekçesiyle ilgili detaylı açıklama",
    )
    suggested_fix: Optional[str] = Field(
        default=None,
        description="Eczacı veya teknisyenin reçeteyi düzeltmesi için önerilen somut adım (Örn: 'Dozu 2x1 olarak düzeltin veya rapor teşhisini güncelleyin')",
    )


SYSTEM_INSTRUCTION = """
Sen Türkiye'deki eczanelerde kullanılan reçete kayıt ve provizyon yazılımlarını (Medula Eczane, Botanik Eczane, TEBEOS, Byte Eczane, E-Reçete vb.) denetleyen uzman bir "Eczacı Asistanı ve SGK SUT Müfettişi" yapay zekasısın (ReçeteGöz).

GÖREVİN:
Sana sağlanan ekran görüntüsünü dikkatle taramak; reçetedeki doz, periyot, kutu adedi, teşhis ve rapor kurallarını denetleyerek eczacının SGK kesintisine uğramasını veya hatalı ilaç verilmesini önlemektir.

KONTROL KRİTERLERİ:
1. **Doz ve Periyot Uyumu**:
   - İlacın maksimum günlük dozu aşılmış mı? (Örn: Günlük maksimum 1000mg olan bir ilaç için 2x1000mg veya 3x1 girilmiş mi?)
   - Periyot ile kullanım adedi tutarlı mı? (Örn: Günde 1x1 yerine haftada 1x1 girilmesi gerekirken yanlış periyot seçilmiş mi?)
2. **Teşhis (ICD-10) ve İlaç Grubu Uyumu**:
   - Reçetedeki veya rapordaki teşhis kodu (ICD-10), reçete edilen ilacın SGK SUT geri ödeme endikasyonuna uygun mu?
   - Teşhis uyumsuzluğu nedeniyle SGK kesintisi riski var mı?
3. **Rapor Süresi ve Maksimum Kutu Adedi**:
   - Raporlu ilaçlarda rapor dozu aşılmış mı?
   - Raporun geçerlilik süresi dolmuş mu?
   - SUT kurallarına göre verilebilecek maksimum kutu adedi aşılmış mı? (Örn: raporsuz 1 kutu limiti, 3 aylık doz sınırı vb.)
4. **Mükerrer veya Etkileşen İlaçlar**:
   - Aynı etken maddeye veya benzer terapötik gruba ait mükerrer ilaç girilmiş mi?

ÖNEMLİ KURALLAR:
- Eğer ekranda herhangi bir reçete/medula/botanik kayıt ekranı YOKSA: `prescription_found = False`, `has_error = False` döndür.
- Eğer ekranda reçete VAR ve tüm girişler SUT/tıbbi kurallara tamamen UYGUNSA: `prescription_found = True`, `has_error = False`, `short_message = "Reçete kurallara uygun"` döndür.
- Eğer hata varsa: `has_error = True` yap; `error_row`, `field_name`, `short_message`, `detailed_explanation` ve `suggested_fix` alanlarını eksiksiz, Türkçe ve profesyonel bir dille doldur.
"""


class PrescriptionAnalyzer:
    """Google GenAI SDK ile reçete ekran görüntülerini analiz eder."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model_name = model_name
        self.client: Optional[genai.Client] = None
        self._init_client()

    def _init_client(self):
        """API anahtarı mevcutsa Google GenAI client'ını ilklendirir."""
        if self.api_key and len(self.api_key.strip()) > 10:
            try:
                self.client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                print(f"[AIAnalyzer] Client başlatma hatası: {e}")
                self.client = None
        else:
            self.client = None

    def update_api_key(self, new_api_key: str, model_name: Optional[str] = None):
        """API anahtarını veya model adını günceller."""
        self.api_key = new_api_key
        if model_name:
            self.model_name = model_name
        self._init_client()

    def analyze_prescription(
        self, image: Image.Image
    ) -> PrescriptionAnalysisResult:
        """
        Verilen PIL Image görüntüsünü gemini-2.5-flash modeline gönderip yapılandırılmış JSON çıktısı alır.

        Args:
            image: Reçete ekran görüntüsü (PIL.Image)

        Returns:
            PrescriptionAnalysisResult pydantic nesnesi
        """
        if not self.client:
            return PrescriptionAnalysisResult(
                prescription_found=False,
                has_error=False,
                short_message="Gemini API Anahtarı Tanımlanmamış",
                detailed_explanation="Lütfen ayarlar menüsünden geçerli bir Google Gemini API anahtarı giriniz.",
            )

        try:
            # Görüntüyü ve promptu model API'sine gönder
            prompt = "Lütfen bu ekrandaki reçete kayıtlarını SUT kuralları, doz aşımı, periyot ve teşhis uyumu açısından incele ve yapılandırılmış JSON formatında raporla."

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=PrescriptionAnalysisResult,
                    temperature=0.1,  # Tutarlı ve katı kural kontrolü için düşük sıcaklık
                ),
            )

            if response.parsed and isinstance(
                response.parsed, PrescriptionAnalysisResult
            ):
                return response.parsed

            # Eğer parsed otomatik oluşmadıysa metinden parse et
            if response.text:
                return PrescriptionAnalysisResult.model_validate_json(
                    response.text
                )

            return PrescriptionAnalysisResult(
                prescription_found=False,
                has_error=False,
                short_message="Modelden boş yanıt alındı",
                detailed_explanation="AI modeli herhangi bir analiz metni üretmedi.",
            )

        except Exception as e:
            error_str = str(e)
            print(f"[AIAnalyzer] Analiz sırasında hata: {error_str}")

            if "RESOURCE_EXHAUSTED" in error_str or "429" in error_str:
                msg = "API Kota Sınırı Aşıldı (429)"
                det = "Gemini API istek kotası doldu. Lütfen birkaç saniye bekleyin veya yeni bir API anahtarı girin."
            elif "API_KEY_INVALID" in error_str or "401" in error_str:
                msg = "Geçersiz API Anahtarı"
                det = "Belirtilen Gemini API anahtarı geçersiz veya yetkisiz. Ayarları kontrol ediniz."
            else:
                msg = "Analiz Bağlantı Hatası"
                det = f"Reçete analiz edilirken bir hata oluştu: {error_str[:150]}"

            return PrescriptionAnalysisResult(
                prescription_found=False,
                has_error=False,
                short_message=msg,
                detailed_explanation=det,
            )
