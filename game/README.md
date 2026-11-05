# Kurtarıcı: Kayıp Pati

Kurtarma ekibi karakteriyle oynanan, tek bölümlük, tarayıcıda çalışan 2D platform oyunu.
Enkaz bölgesinde mahsur kalan kediciği bulup kurtarmak gerekiyor.

## Çalıştırma

`index.html` dosyasını tarayıcıda açın (ya da klasörü herhangi bir statik sunucuyla sunun).
Kurulum gerekmez; `sprites.png` aynı klasörde olmalı.

## Kontroller

| Tuş | İşlev |
| --- | --- |
| ← → / A D | Yürü |
| Boşluk / ↑ / W | Zıpla (basılı tut = daha yüksek) |
| Shift / X | Koş |
| P / Esc | Duraklat |
| M | Ses aç/kapa |

Dokunmatik ekranlarda ekran üstü butonlar çıkar.

## Oyun

- **Altın sandıklar (!)**: Alttan vurunca altın verir; bazıları **baret** çıkarır (bir darbeyi karşılar).
- **Tuğlalar**: Alttan vurunca kırılır.
- **Moloz** ve **Alev** düşmanları: Üstlerine zıplayarak etkisiz hale getirin.
- **Dikenler** ve çukurlardan kaçının; hareketli platformları kullanın.
- Yarı yoldaki **kontrol noktası** bayrağı yeniden doğma yerini kaydeder.
- 50 altın = +1 can. Süre bonusu ve kurtarma bonusu bölüm sonunda eklenir.

`sprites.png`: verilen 4 GIF animasyonundan (bekleme, kutlama, zıplama, koşu) üretilen 8×4 kare sprite sayfası.
