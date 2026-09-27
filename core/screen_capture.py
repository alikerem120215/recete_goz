"""
ReçeteGöz - Ekran Yakalama ve Değişim Algılama Modülü
MSS ve Pillow ile yüksek performanslı ekran yakalama ve perceptual/difference hashing ile akıllı filtreleme sağlar.
"""

import io
from typing import Optional, Tuple
from PIL import Image
import mss
import imagehash


class ScreenCaptureManager:
    """Ekran görüntüsü alma, hash hesaplama ve optimizasyon işlemlerini yönetir."""

    def __init__(self, monitor_index: int = 1):
        """
        Args:
            monitor_index: Yakalanacak ekran indeksi.
                          1: Birincil monitör, 0: Tüm monitörler birleşik.
        """
        self.monitor_index = monitor_index
        self._last_hash: Optional[imagehash.ImageHash] = None
        self._last_image: Optional[Image.Image] = None

    def capture_screen(self) -> Image.Image:
        """
        MSS kullanarak ekran görüntüsü yakalar ve PIL Image nesnesine dönüştürür.
        """
        with mss.mss() as sct:
            monitors = sct.monitors
            # Eğer belirtilen indeks yoksa birincil veya ilk ekranı al
            target_monitor = (
                monitors[self.monitor_index]
                if 0 <= self.monitor_index < len(monitors)
                else monitors[0]
            )

            sct_img = sct.grab(target_monitor)
            # MSS raw formatından PIL RGB formatına dönüştür
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
            return img

    def compute_hash(self, image: Image.Image) -> imagehash.ImageHash:
        """
        Görüntünün difference hash (dhash) değerini hesaplar.
        dhash metin ve arayüz değişikliklerinde oldukça hızlı ve etkilidir.
        """
        return imagehash.dhash(image)

    def has_screen_changed(
        self, new_image: Image.Image, threshold: int = 6
    ) -> Tuple[bool, int]:
        """
        Yeni alınan ekran görüntüsünün önceki görüntüden anlamlı derecede farklı olup olmadığını kontrol eder.

        Args:
            new_image: Yeni yakalanan PIL Image
            threshold: Hash fark eşiği (0-64 arası). Eşik aşıldığında ekran değişti sayılır.

        Returns:
            (changed: bool, diff: int)
        """
        current_hash = self.compute_hash(new_image)

        if self._last_hash is None:
            self._last_hash = current_hash
            self._last_image = new_image
            return True, 999

        diff = int(current_hash - self._last_hash)
        is_changed = bool(diff >= threshold)

        if is_changed:
            self._last_hash = current_hash
            self._last_image = new_image

        return is_changed, diff

    def optimize_for_ai(
        self, image: Image.Image, max_dimension: int = 1600
    ) -> Tuple[bytes, Image.Image]:
        """
        Görüntüyü AI modeline göndermek üzere optimize eder.
        Metin okunaklılığını korurken token maliyetini ve yanıt süresini düşürür.

        Args:
            image: Kaynak PIL Image
            max_dimension: Maksimum genişlik veya yükseklik (px)

        Returns:
            (png_bytes, resized_image)
        """
        w, h = image.size
        if max(w, h) > max_dimension:
            scale = max_dimension / max(w, h)
            new_w = int(w * scale)
            new_h = int(h * scale)
            optimized_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        else:
            optimized_img = image.copy()

        buf = io.BytesIO()
        optimized_img.save(buf, format="PNG", optimize=True)
        return buf.getvalue(), optimized_img

    def reset_hash(self):
        """Son hash hafızasını sıfırlar, böylece bir sonraki kare mutlaka analiz edilir."""
        self._last_hash = None
        self._last_image = None
