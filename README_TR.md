# YZM411 Bilgisayarlı Görü — Ödev 1
## Renk, aydınlatma ve örnekleme — çalıştırılmış örnek çalışma

**ÖNEMLİ AKADEMİK UYARI:** Bu klasördeki `temel_sahne_ai.png` üretici yapay zekâ ile hazırlanmış bir *örnek sahnedir*. `sahne_shadow.png` ve `sahne_lamp.png`, bu tek görüntünün **NumPy ile matematiksel olarak simüle edilmiş** varyasyonlarıdır. Bunlar kamerayla farklı ışıklarda çekilmiş üç bağımsız fotoğraf **değildir**. Ödev yönergesi kendi masaüstü sahnenizin gerçek üç çekimini istiyor; dolayısıyla bu paket gerçek fotoğraf koşulunu mevcut hâliyle sağlamaz. Çalışma veri kaynağını saklamaz, ölçüm uydurmaz, kendine ait fotoğraf çekildiği iddiasında bulunmaz.

### Klasör içeriği

| Dosya | İçerik |
|---|---|
| `run_experiment.py` | Tüm deneyleri yeniden çalıştıran Python programı; kaynakta deney öncesi tahminler de bulunur. |
| `rapor_2_sayfa.pdf` | İki sayfalık, üç ışık koşulu, altı maske, ölçümler, yeniden örnekleme ve AI beyanı içeren rapor. |
| `olcumler.csv` | RGB/HSV maskeleri, parlaklık/gama, görüntü ortalamaları ve MAE ham sayıları. |
| `piksel_olcumleri.csv` | Üç sabit `(x,y)` noktasında üç koşul için RGB değerleri. |
| `ham_sonuclar.json` | Boyut, parametre, tüm ham ölçümler, ön tahminler, paket sürümleri. |
| `deney_aciklamalari.md` | 4–7. adımlar için tahmin–ölçüm–gözlem–neden–kontrol, açıklamalı değerlendirmeler. |
| `kaynak_ve_yapay_zeka_beyani.md` | Görsel kaynağı, AI kullanım kapsamı, doğrulama ve sınırlar. |
| `gorseller/` | AI temel sahne, 3 koşul, 6 maske, 3 dönüşüm, 3 örnekleme görseli. |
| `requirements.txt` | Gerekli Python paketleri. |

## Yeniden çalıştırma sırası

Python 3.10+ ile, bu klasörün içindeyken:

```bash
python -m pip install -r requirements.txt
python run_experiment.py
```

Program `gorseller/` altındaki temel AI sahneyle aynı parametrelerde *demo simülasyonunu* oluşturur; PNG, CSV, JSON ve PDF çıktıları **gerçekten hesaplayarak** yeniler. Ekrana ölçüm özetlerini basar. Ağ bağlantısı gerektirmez.

### Hocanın istediği gerçek fotoğraflarla kullanma

1. Aynı düzeneğe sarı veya renkli nesne, beyaz/gri kâğıt ve küçük yazılı/çizgili doku yerleştirin.
2. Telefonu ve nesneyi oynatmadan **normal**, **gölge**, **farklı lamba** altında gerçek üç fotoğraf çekin; kişiler görünmesin.
3. Kameranın otomatik pozlama ve beyaz denge ayarlarını not edin; açıksa yalnızca ışığın değiştiğini ileri sürmeyin.
4. Bu üç fotoğrafı klasöre kopyalayın; şu komutu çalıştırın:

```bash
python run_experiment.py --normal kendi_normal.jpg --shadow kendi_golge.jpg --lamp kendi_lamba.jpg
```

**DİKKAT:** Programa gerçek fotoğraflar verildiğinde çıktı istatistikleri yeniden hesaplanır; fakat örnek sahneye göre sabitlenmiş `RGB_LO`, `RGB_HI`, `HSV_LO`, `HSV_HI`, `TARGET_ROI`, `TEXT_ROI` ve `PIXELS` değerleri artık uygun olmayabilir. Bunları **yalnızca ilk normal fotoğrafa bakıp** bir kere ayarlayın; sonraki iki fotoğraf için değiştirmeyin. Fotoğrafınızın boyutu 1536×1024'e yeniden ölçeklenir; ROI ve piksel koordinatlarını buna göre seçin. `PRE_REGISTERED` başlığındaki tahminleri deneyleri çalıştırmadan **önce** kendinize göre yenileyin. Gerçek fotoğraflarla yeniden üretilen raporun AI/görsel kaynağı açıklamalarını da gerçeğe uygun şekilde düzenleyin: PDF rapor metni şu anda açıkça *demo veri* için yazılmıştır. Gerçek fotoğraflarla kullanımda bu sabit kaynak ifadesini kaynak kodundaki `make_pdf()` fonksiyonunda ve kaynak beyanında güncelleyin.

**Öğrenci numarası:** `rapor_2_sayfa.pdf` içindeki `[EKLEYİN]` ve ZIP dosyasındaki `OgrenciNo` yer tutucularını kendi öğrenci numaranızla değiştirin.

## Algoritma ve sabitler

- OpenCV ile okuma: `cv2.imread()` **BGR** döndürür; `cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)` ile **RGB** olur; `rgb[y, x, kanal]` sırası kullanılır.
- Normal görüntüden seçilen hedef ROI: `[670:890] x [865:892]` (gerçek NumPy dilimleri `normal[865:892,670:890]`).
- RGB sabit aralığı (R,G,B): alt `[185,130,0]`, üst `[255,255,105]`.
- HSV sabit aralığı (H,S,V): alt `[14,100,70]`, üst `[38,255,255]`; OpenCV 8-bit HSV: H∈[0,179], S/V∈[0,255].
- Parlaklık: `clip(I.astype(float32)+40, 0,255)`.
- Gama: `clip(255*(I/255)**gamma,0,255)`; `gamma = 0.5` ve `2.0` ayrı uygulanır (1/gamma **kullanılmaz**).
- Yazı ROI: `normal[357:669,180:1008]` (828×312 piksel), sonra genişlik ve yükseklikte tam sayı `//4` küçültme; iki sonuç da `INTER_NEAREST` ile özgün ROI boyutuna geri büyütülür.
- MAE: ROI orijinali ve geri büyütülen ROI'nin RGB değerleri arasındaki kanal başına ortalama mutlak fark. MAE okuma doğruluğu değildir.
- Tüm yüzdeler *tüm görüntü alanına göre* beyaz maske piksellerinin yüzdesidir; sınıflandırma doğruluğu olarak kullanılmaz.
- Simülasyon sabitleri `simulate_lighting()` fonksiyonunda yer alır. Gerçek ışık fiziğinin tam modeli değildir.

## GitHub / teslim öncesi kontrol

Ödev yönergesine göre en geç **10 Kasım 2026** teslim ve GitHub yüklemesi isteniyor. Öğrenci numarasını düzeltin, **kendi üç fotoğrafınız** ile deneyi yeniden çalıştırıp sonuçları yorumlayın; sonrasında `.py`, iki sayfalık PDF, CSV sonuçları ve kaynak beyanını tek ZIP olarak yükleyin. `.py` betiğini PDF rapor yerine göndermeyin; ayrı PDF vardır.
