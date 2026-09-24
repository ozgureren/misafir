# TKİ Misafirhane – Dış Kabuk 3D Modeli

Kaynak: `source/BLK-15.01_tki misafirhane -mevcut mimari_2015.05.05.dwg` (TKİ Genel Müdürlüğü – Mimari Rölöve Projesi, Mevcut Durum, AutoCAD 2013 / AC1027).

| Dosya | İçerik |
|---|---|
| `model/tki_misafirhane_exterior.blend` | Blender 5.0 sahnesi (koleksiyonlar, malzemeler, instance'lı pencereler) |
| `model/tki_misafirhane_exterior.glb` | glTF 2.0 binary (Y-up, metre) |
| `model/tki_misafirhane_exterior.fbx` | FBX (metre) |
| `model/dwg_transform.json` | DWG → yerel koordinat dönüşümleri, orijin tanımı, yön bilgisi |
| `model/model_data.json` | Modelin üretildiği ara veri (poligonlar, kotlar, açıklıklar) |
| `qc/COMPARE_*.png` | DWG görünüşü (üst) ↔ model ortografik render (alt), aynı ölçek ve orijin |
| `qc/FRONT…/BACK…/LEFT…/RIGHT…`, `qc/AERIAL_*` | Dört ana cephe + iki kuşbakışı |
| `model/textures/` | Fotoğraflara göre üretilmiş döşenebilir PBR dokular (renk `.jpg` + normal `.png`) |
| `qc/photo_views/` | Saha fotoğraflarıyla aynı açılardan Cycles render'ları ve fotoğraf ↔ model karşılaştırmaları |
| `source/photos/` | Referans saha fotoğrafları (1–4) |
| `tools/` | Tam üretim hattı (`tools/run_all.sh`): DWG → model, tekrar üretilebilir |

Model yalnızca **dış kabuk**tur; iç mekân (bölmeler, iç kapılar, mobilya, tesisat, asma tavan, iç merdivenler, galeri korkulukları, iç kolonlar) modellenmemiştir.

---

## 1. DWG'de tespit edilen çizimler

DWG model uzayı bir pafta dizilimidir (tüm çizimler yan yana, ~845 m genişlikte; koordinatlar harita koordinatı değildir). LibreDWG 0.13.3 ile okundu, 1 051 blok tanımı açıldı; 54 layer (46'sı model uzayında kullanılıyor). Anlamlı layer'lar: `A-Duvar`, `A-Betonarme`, `A-Cam`, `A-Kapı`, `A-Merdiven`, `A-Gör 2/3/4/5` (görünüş çizgileri), `A-Kot`, `A-Aks *`, `A-Olcu *`, `A-Yazı *`, `AHSAP`.

| Blok | Çizim | Ölçek |
|---|---|---|
| A Blok | Bodrum Kat Planı, Zemin Kat Planı, Tip Kat Planı, +16.00 Kotu Planı (çatı çekirdeği), Çatı Planı | 1/50 |
| B + C Blok | Bodrum Kat Planı, Zemin Kat Planı, Çatı Planı | 1/50 |
| Kesitler | A-A Kesiti (A + B/C boyunca), B-B Kesiti | 1/50 |
| Görünüşler | Doğu Cephesi, Kuzey Batı Cephesi, Güney Batı Cephesi | 1/50 |
| Detay | Teras korkuluk/parapet detay kesitleri (Rölöve / Uygulama, 1/20) | 1/20 |
| Diğer | Antet, lejant, logo | – |

**Kilit bulgu:** A bloğu ile B/C blokları aynı aks sistemini paylaşır (A–O ve 8–9 aksları). B/C zemin planında A–O aksları 45° eğik çizilmiştir, yani **A bloğu sahada B/C'ye göre +45° dönüktür.** Tüm planlar ortak aks kesişimleri üzerinden tek koordinat sistemine oturtuldu; A bloğunun B/C ile ortak duvarı üst üste çakışmaktadır (doğrulandı).

## 2. Kat sayısı

- **A Blok (misafirhane kulesi):** bodrum + zemin + 4 tip kat = **zemin üstü 5 kat**, ayrıca çatıda asansör makine dairesi/merdiven çekirdeği.
- **B/C Blok (sosyal tesis):** bodrum + zemin = **zemin üstü 1 kat**; büyük salon çift yükseklikli (kırma çatı).

## 3. Kat yükseklikleri (kesit A-A ve görünüş kotlarından)

| Seviye | Kot | Kat yüksekliği |
|---|---|---|
| Doğal zemin (görünüşler) | −1.00 | – |
| A / B-C bodrum döşemesi | −4.00 (plan: −4.15) | A bodrum 5.00 m (−4.00 → +1.00) |
| B/C zemin kat, teraslar | ±0.00 | 4.00 m (±0.00 → +4.00 kiriş üstü) |
| A zemin kat | +1.00 | 3.00 m |
| A 1.–4. tip katlar | +4.00 / +7.00 / +10.00 / +13.00 | 3.00 m |
| A çatı döşemesi | +16.00 | – |
| A parapet üstü | +17.60 (harpuşta +17.40–17.60) | 1.60 m parapet |
| A çatı çekirdeği | +19.20 döşeme / +19.80 parapet | – |

Pencere kotları (görünüşler): A zemin +1.60/+3.20, tip katlar +4.60/+6.20 … +13.60/+15.20; B/C +0.90, +2.20, +2.85, +3.40 (her açıklık kendi görünüş dikdörtgeninden alındı).

## 4. Toplam bina yüksekliği

- A Blok: ±0.00'dan parapet **+17.60 m**, doğal zeminden (−1.00) **18.60 m**; çatı çekirdeği dahil +19.80 (zeminden **20.80 m**).
- B/C Blok: parapet +4.60 / +5.60, salon kırma çatı mahyası **+7.65** (zeminden 8.65 m).

## 5. Yaklaşık dış ölçüler

- Tüm kompleks (teras ve merdivenler dahil): **96.1 m × 47.4 m** (yerel X × Y).
- B/C gövdesi: **78.1 m × 34.3 m**, oturum ≈ 1 400 m².
- A Blok (45° dönük): tip katlar **22.5 m × 27.7 m** (≈ 524 m²), zemin kat giriş kulesi dahil 22.8 m × 29.1 m.
- Dış duvar kalınlığı: planlardan ölçülen baskın değer **29 cm**.

## 6. Modellenen dış cephe elemanları

| Koleksiyon | İçerik |
|---|---|
| `BUILDING_SHELL` | A/B-C subasman kütleleri (−1.00 → +1.00 / ±0.00), ara döşeme, çatı çekirdeği, havuzlu avlu tabanı (−4.15) |
| `EXTERIOR_WALLS` | A zemin kat (traverten), A tip katlar (sıva), B/C duvarları (sıva) – 29 cm; avluya bakan bodrum cepheleri (−4.15'e kadar) |
| `WINDOWS` / `WINDOW_GLASS` | 124 pencere birimi: 6 cm × 7 cm alüminyum çerçeve, cam, traverten denizlik, söve (görünüşlerde "Söve" yazan yerlerde). Aynı ölçüdekiler **ortak mesh (linked instance)** kullanır; toplam 366 mesh / 679 obje. Eğik giydirme cephe (atrium, +5.00 → +15.90, 1.0 m içe eğik) + kayıt/dikmeler |
| `EXTERIOR_DOORS` / `ENTRANCE` | 55 kapı parçası (alüminyum + cam, orta kayıt, çift kanatta orta kayıt); A kavisli giriş kulesi ve B/C ışıklık altı girişi `ENTRANCE`'ta |
| `ROOF` | A +16.00 düz çatı, atrium eğik metal çatısı (+16.95 → +16.00), salon kırma çatısı (saçak +5.60, mahya +7.65), batı kanadı beşik çatısı (+4.15 → +5.50), A–B arası cam ışıklık (+4.80/+5.20), GD ışıklık (+4.00/+4.60), B/C düz çatı tabliyesi |
| `PARAPETS` | A parapeti +17.60, B/C parapetleri +4.60 / +4.80 / +5.60, harpuştalı taş denizlik (4 cm taşkın), GD terası 95 cm duvar (+0.95) |
| `EXTERIOR_STAIRS` | BM1, BM2 (6R × 16.66, −1.00 → ±0.00), BM4 (6 basamak), BM5 ve BM7 (18R × 17.50, −1.00 → −4.15, şaft duvarları −0.70), BM6 kavisli çift kollu avlu merdiveni (2 × 18R), avlu istinat duvarı (−0.70) |
| `CANOPIES` | Güney pergola kirişleri (üst +4.00, GD'de +4.70) |
| `COLUMNS` | 14 serbest kolon (pergola sırası y≈−11 ve avlu kolonları) |
| `ENTRANCE` | Teraslar: ±0.00 pergola/teras döşemesi, −0.70 basamak teras, −0.40 giriş sahanlığı, 272 m² GD açık terası |
| `RAILINGS` | Teras kenarı paslanmaz boru korkuluk (fotoğraf + DWG notu) |
| `BALCONIES`, `RAMPS` | Boş – DWG'de ve fotoğraflarda balkon/rampa yok |

**Malzemeler (görünüş notlarından):** *Silikon esaslı dış cephe sıvası* (duvarlar), *Traverten kaplama* (A zemin kat, denizlikler), *Taş kaplama + 2 sıra bisküvi tuğla* (subasman bandı), *Harpuştalı taş kaplama alınlı* (parapet denizlikleri), *Renkli eloksal alüminyum doğrama + ısıcam*, *Renkli metal yaprak çatı örtüsü*. Renk bilgisi olmayan malzemeler (sıva, doğrama, çatı metali) nötr tonda bırakıldı; her malzemede DWG açıklaması `dwg_description` özelliğinde duruyor.

**Yöntem:** Dış konturlar planlardan otomatik çıkarıldı. Pencere ve kapılar **görünüşlerden geri izdüşüm** ile yerleştirildi: her görünüşün bakış yönü ve ölçeği aks balonlarından hesaplandı, görünüşteki her açıklık dikdörtgeni izleyiciye en yakın cepheye oturtuldu. Kavisli cephelerde açıklık cephe poligonu boyunca parçalandı.

**Doğrulama:** Üç görünüşteki 162 açıklık dikdörtgeninin tamamı bir cepheye oturdu (Doğu 61/61, KB 56/56, GB 45/45). Plan kontrolünde A zemin 14/15, A tip 14/14, B/C 36/47 plan penceresi görünüşten gelen bir açıklıkla eşleşti. Eşleşmeyenler, hiçbir görünüşte görünmeyen cephelerde (avlu, KB çapraz kanadı).

## Kalite kontrol

| Kontrol | DWG | Model | Durum |
|---|---|---|---|
| A tip kat ölçüsü (aks 1–9 × A–O) | 22.37 m aks + duvar / 28.80 m aks | 22.54 m × 27.65 m (dış kontur) | ✔ |
| B/C uzunluk / genişlik | aks 14–30: 68.2 m; dış kontur | 78.1 m × 34.3 m | ✔ |
| Kat sayısı | 5 (A), 1 (B/C) | 5, 1 | ✔ |
| A parapet / çatı / çekirdek | +17.60 / +16.00 / +19.80 | aynı | ✔ |
| Pencere adedi/hizası | Doğu: A 4 sıra × 4 + zemin; KB: 6 × 5 kat; GB: 4 × 5 kat | aynı (bkz. `qc/COMPARE_*.png`) | ✔ |
| Kapı/giriş konumları | görünüş dikdörtgenleri | geri izdüşüm | ✔ |
| Cephe çıkıntıları | plan konturu | plan konturu | ✔ |
| Balkon | yok | yok | ✔ |
| Çatı formu | kırma (salon), beşik (batı), ışıklıklar, düz (A) | aynı | ✔ (madde 7'deki farklarla) |
| Giriş | A kavisli giriş kulesi, B/C ışıklık altı | aynı | ✔ |

Dört ana cephe ortografik olarak render edildi (FRONT = batı/teras tarafı, BACK = doğu, LEFT = kuzey/A blok ucu, RIGHT = güney/doğu kanadı ucu), üç DWG görünüşü de aynı ölçekte üst üste karşılaştırıldı.

## 7. DWG'de belirsiz kalan noktalar

1. **Kuzey oku / harita koordinatı yok.** Yön, görünüş adlarından çıkarıldı (yerel −X ≈ Kuzey, +Y ≈ Doğu). DWG koordinatları pafta dizilimi olduğu için model yerel orijinde (aks 8 × aks A, Z=0 = ±0.00). Yerleşke modeline oturtmak için bir saha ölçü noktası gerekir.
2. **Çatı çekirdeği (+19.80)** kesit A-A'da ve +16.00 kotu planında var, ama hiçbir görünüşte çizilmemiş. Kesite göre modellendi.
3. **Salon kırma çatısı:** çatı planında taban 20.8 m, mahya 5.05 m. Doğu görünüşünde taban ≈26 m, mahya ≈10 m çizilmiş. Model çatı planını esas aldı.
4. **Doğu kanadı çatısı:** çatı planında mahya/mahya dönüş çizgileri var, ama mahya kotu yok. Model +5.60 parapet arkasında düz çatı.
5. Batı kanadı çatısında, kuzey ek bina ile mahya arasındaki üçgen yüzeyin eğimi belirsiz; kuzey yüzeyin devamı olarak alındı. Kavisli güney çıkıntısı üzerindeki küçük çatı ve ışıklık yanındaki iki küçük "+4.80 mahya" parçası +4.60 parapet altında kaldığı için düz modellendi.
6. **Parapet bölgeleri:** +4.60 / +4.80 / +5.40 / +5.60 etiketleri noktasal. Bölge sınırları plandan yorumlandı; tek noktadaki +5.40 ayrıca modellenmedi. GB görünüşünde A için +17.90/+18.10 kotları var, çatı planında +17.60 → +17.60 kullanıldı.
7. **Pergola kiriş yüksekliği** verilmemiş; 30 cm alındı (üst kot +4.00 çizimden). Kolonlar kiriş altına kadar.
8. **Atrium çatısının eğimi** (+16.95 → +16.00) kesitten grafik olarak okundu; kot yazılmamış.
9. Görünüşlerde görünmeyen cephelerdeki (avlu, KB çapraz kanadı) 6 pencere birimi plan konumundan alındı. Denizlik/lento kotu aynı cephedeki en yakın görünüş penceresinden aktarıldı.
10. BM4 merdiveninin kot/rıht bilgisi yok (6 basamak numaralı); −1.00 → ±0.00 kabul edildi. Teras kotlarının (−0.40 / −0.70 / ±0.00) sınırları plan çizgilerinden yorumlandı.
11. A tip kat planında atrium cephesi ve kavisli merdiven kulesi kapalı duvar çizgisiyle çizilmemiş. Cephe çizgisi eğik cam alt kenarına göre, kule ise zemin kat konturu ve KB görünüşüne göre tamamlandı.
12. A kavisli giriş kulesinde −1.00 zeminden +1.00 zemin katına çıkan dış basamak çizilmemiş (M1 bina içinde).
13. Doğrama rengi ("renkli eloksal"), çatı metali rengi ve sıva rengi belirtilmemiş.
14. Doğu görünüşünde GD pergola/ışıklık çizilmemiş, planda var; plana göre modellendi.

## 8. Özellikle modellenmeyen detaylar

- Tüm iç mekân: bölmeler, iç kapılar, mobilya, tesisat, asma tavan, iç merdivenler (M1–M4), asansörler, atrium galeri korkulukları, uzay kafes (atrium içi), çatı ahşap/çelik taşıyıcıları, iç kolonlar.
- Doğrama profil detayları (yalnızca çerçeve + cam + ana kayıtlar), görünüşlerdeki pencere kanat bölüntüleri ve açılım çizgileri.
- Kat hizası "fuga" derz çizgileri ve cephe bantları (yalnızca çizgi olarak çizilmiş, derinlik yok).
- Yağmur olukları, iniş boruları, çatı drenajı.
- Korkuluklar, fotoğraflar geldikten sonra teras kenarlarına eklendi (bkz. "Gerçekçi kaplama"). Hat, DWG teras sınırından otomatik alındı; tek tek fotoğrafla doğrulanmadı.
- Havuzlar (avluda "HAVUZ", −4.60/−1.20 kotları). Yalnızca avlu tabanı −4.15.
- Arazi/peyzaj, 1/20 teras detayları, tesisat kapakları, logo/antet.
- Zemin altında kalan bodrum duvarları (avlu ve merdiven şaftları dışında). Subasman kütlesi dolu blok olarak bırakıldı.

## Gerçekçi kaplama (saha fotoğraflarına göre)

Malzemeler dört saha fotoğrafına göre ayarlandı ve dokulu PBR malzemeye dönüştürüldü (renk + normal haritası, metre ölçekli UV). Dokular `tools/make_textures.py` ile prosedürel üretildi; döşenebilir, fotoğraf kopyası değil.

| Malzeme | Nerede | Kaynak |
|---|---|---|
| `PLASTER_A`: krem, granüllü sıva, 1.5 m aralıklı yatay derz | A blok tip katlar, saçak, konsollar, çatı çekirdeği | Foto 2, 4 + DWG "Silikon esaslı dış cephe sıvası", "Fuga" |
| `TRAVERTINE`: krem traverten, 1.20 × 0.60 m plaka | A zemin kat, B/C duvarları, kolonlar, pergola kirişleri, basamaklar | Foto 1, 3 + DWG "Traverten kaplama" |
| `ASHLAR`: bej kesme taş, 40 × 20 cm, şaşırtmalı | Subasman (zeminden ≈1.1 m, +0.10'a kadar) | Foto 2, 4 + DWG "Taş kaplama" |
| `RED_MARBLE`: koyu kırmızı damarlı mermer | B/C parapet harpuşta/alın bandı (30 cm), giriş portalı | Foto 1, 3 |
| `OCHRE`: hardal sarı sıva | Pergola/kolonat arkasındaki cephe (0 → +3.70) | Foto 1, 3 |
| `COPING_A`: oker | A blok parapet harpuştası | Foto 2, 4 |
| `RED_ALU`: kırmızı eloksal alüminyum | Tüm pencere/kapı doğramaları (çift kanatlı pencerelerde orta dikme) | Foto 1–4 + DWG "Renkli eloksal alü." |
| `SOVE`: açık traverten | Pencere söveleri ve denizlikleri | Foto 4 + DWG "Söve", "Traverten denizlik" |
| `CURTAIN`: bej tül perde paneli | A blok oda pencerelerinin 12 cm arkası (iç mekân modellenmedi, yalnız cam arkası panel) | Foto 1–4 |
| `BLUE_GLASS` + `RED_PAINT` | Atrium eğik giydirme cephesi, kırmızı üst alın | Foto 3 |
| `GRANITE`: açık gri granit plak, 60 cm | Teraslar, avlu tabanı | Foto 3 |
| `STAINLESS` | Teras kenarı boru korkuluk (h 0.90, 3 ara çubuk, 1.5 m dikme aralığı) | Foto 1, 3 + DWG "Alü. boru korkuluk h: 90 cm" |
| `ROOF_METAL`, `ROOF_FLAT`, `CONCRETE` | Kırma/beşik çatılar, düz çatılar, şaft duvarları | Fotoğraflarda görünmüyor → nötr gri |

**Fotoğraflarla eklenen/düzeltilen geometri:**
- **A blok konsollu saçak:** DWG çatı planındaki parapet konturu, NB ve GD cephelerindeki girintili pencere nişlerinin üzerinden düz geçiyor (68.7 m² saçak). Parapet artık bu konturdan üretiliyor. Altında soffit ve fotoğraflardaki üçgen konsollar var (14 adet, üst kat pencerelerinin arasında).
- **Giriş portalı:** DWG'deki portalı kullandım (GB görünüşünde alınlık: saçak +4.65, tepe +5.40; planda iki ayak). Kırmızı mermer ayaklar, +3.00 üstü panel, alınlık ve "TKİ MİSAFİRHANE" yazısı eklendi.
- B/C parapet harpuştası 15 cm'den 30 cm yüksekliğe çıkarıldı (fotoğraftaki mermer alın bandı).
- Kesme taş kaide +1.00 yerine +0.10'da bitiyor (fotoğrafta zeminden ≈1.1 m).
- GD açık terasındaki 95 cm duvar kaldırıldı. Fotoğrafta teras kenarında yalnızca korkuluk var; DWG notu teras kenarı istinat yüksekliği (−1.00 → ±0.00) olarak yorumlandı.
- Teras kenarlarına toplam ≈250 m paslanmaz boru korkuluk eklendi (merdiven ağızları ve bina önü hariç).

Fotoğraf ↔ model karşılaştırmaları `qc/photo_views/COMPARE_PHOTO*.jpg` içinde. GLB, dokuları gömülü (JPEG) olarak taşıyor (≈9 MB). `.blend` dosyası `model/textures/` klasörüne göreli yol kullanıyor.

## Koordinat ve ölçek

- 1:1, metre. DWG cm'dir (100 birim = 1 m, kot işaretleriyle doğrulandı).
- Orijin: aks 8 × aks A kesişimi. Z=0 = ±0.00. Dönüşümler `model/dwg_transform.json` ve Blender'daki `TKI_MISAFIRHANE_ORIGIN` boş objesinin özelliklerinde.
- Poligon: ≈122 000 üçgen (orta seviye).

## Yeniden üretim

```bash
# gereksinim: LibreDWG ≥ 0.13 (dwgread), Python 3.11 + bpy==5.0.1, numpy, shapely, matplotlib, pillow
bash tools/run_all.sh            # ara dosyalar _work/ içine, çıktılar model/ ve qc/ içine
```
