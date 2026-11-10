# YZM411 — Ödev 1 / Deney raporu için ayrıntılı çalışma notları

> **Veri türü:** Bir üretici yapay zekâ masaüstü sahnesi ve ondan matematiksel olarak simüle edilen gölge/lamba sürümleri. Aşağıdaki tüm sayılar **gerçek program çalıştırmasından alınan hesaplama sonuçlarıdır**, ancak **gerçek farklı ışık fotoğraflarının ölçümleri değildir**. Hocanın çekim koşulu için gerçek sahne fotoğrafları gerekir.

## 1. Konuyu okuma — tanımlar

- Kamera nesnenin kimliğini değil, yüzeyden gelen ışığın kanallara düşen şiddetlerini ölçer. Nesne aynı kalsa bile aydınlatma, yüzey yansıması ve kamera işleme zinciri piksel değerini değiştirebilir.
- Sayısal renkli görüntüde üç eksen vardır: **Yükseklik × genişlik × kanal**. OpenCV ile okunan bir `uint8` renkli görüntü genellikle **BGR** kanalları içerir. NumPy dizisinde `[y,x,kanal]` kullanılır. Gerçek RGB için `cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB)` gerekir.
- RGB parlaklık ve rengin bileşik değerlerini tutar; HSV'de H kabaca tonu, S doygunluğu ve V parlaklığı temsil eder. HSV'nin her koşulda sabit kalacağı varsayılmaz; kamera ve spektral ışık değişimleri H/S/V'yi değiştirebilir.
- Örnekleme, bir resmi daha az pikselde temsil etmektir. 1/4 küçültme iki boyutta uygulanırsa piksel sayısı yaklaşık **1/16** olur. Tekrar büyütme yeni sensör bilgisi yaratmaz.

## 2. Veriyi hazırlama — hangi değişkenler kontrol edildi?

Temel görüntü: `gorseller/temel_sahne_ai.png` (1536 × 1024 RGB). Sarı kalem ana hedeftir. Sağdaki sarı yapışkan not, renkçe benzer ama **hedef olmayan** dikkat dağıtıcıdır. Sol üstte beyaz kağıt, küçük punto yazı ve ince çizgiler bulunur. Tanınabilir insan yoktur.

- **Sabit:** Görüntü geometrisi, görüntü boyutu, kalem ve notun konumu, üç `(x,y)` noktası, RGB/HSV eşikleri, örnekleme ROI'si.
- **Değişken:** Gölge için RGB kanallarına yaklaşık `(0.50,0.56,0.64)` çarpanları; lamba için yaklaşık `(1.24,0.97,0.72)` çarpanları ve düşük konumsal kazanç farkı. Kesin uygulama `simulate_lighting()` fonksiyonundadır.
- **Kamera otomatik pozlama/beyaz dengesi:** Uygulanmadı. Bu görüntüler fiziksel bir kameradan alınmadığından bir kameranın AE/AWB davranışına ilişkin sonuç çıkarılamaz.
- **Sınırlama:** Lamba/gölge 3 farklı gerçek çekim **değildir**. Işık değişiminin kontrollü *dijital taklididir*. Bu deney fiziksel ışık, gölge kenarı, yansıma ve pozlama etkilerini bütünüyle genellemez.

## 3. Deneyden ÖNCE belirlenmiş tahminler ve gerçek ölçümler

### Deney 4: Görüntünün sayısal yapısı (H1)

**Ön tahmin — 2 cümle:** Üç görüntünün boyutunun `(1024,1536,3)` ve veri türünün `uint8` kalacağını bekliyorum. Aynı kalem noktalarındaki RGB değerleri gölge/lamba dönüşümünden sonra değişecek; çünkü kanal kazançları farklıdır.

**Ölçüm:** Normal görüntünün şekli `(1024,1536,3)`, tipi `uint8` ve gözlenen asgari–azami kanal değerleri `0–255`'tir. Üç noktada RGB ölçümleri:

| (x,y) | Normal RGB | Gölge RGB | Lamba RGB |
|---|---|---|---|
| (700,835) | (252,203,4) | (125,113,4) | (255,204,3) |
| (850,875) | (240,190,2) | (120,107,2) | (255,190,2) |
| (950,900) | (193,137,2) | (97,78,2) | (249,136,2) |

**Ne gördüm?** Aynı kalem bölgesinde kanal değerleri farklı, dizinin koordinat yapısı sabittir. **Neden olabilir?** Fiziksel hedefin yeri değişmemişken dijital ışık kazançları RGB kanallarını farklı ölçekler; bazı değerler 255'e dayanır. **Nasıl kontrol ederim?** Her görüntü için `shape`, `dtype`, `min/max` yazdırır, `rgb[y,x,0]` ve BGR karşılığını elle karşılaştırır, aynı koordinatların gerçekten kalemin üzerinde olduğunu kontrol ederim.

**Kısa kod:** `bgr=cv2.imread(dosya); rgb=cv2.cvtColor(bgr,cv2.COLOR_BGR2RGB); print(rgb.shape,rgb.dtype,rgb[y,x,:])`.

### Deney 5: Sabit RGB ve HSV maskeleri (H2)

**Ön tahmin — 2 cümle:** Gölge karardığı için sabit minimum kanallar kullanan RGB maskesi ciddi daralacaktır. HSV ton seçimi daha fazla sarı alanı koruyabilir; sarı yapışkan not hedef olmadığı hâlde yanlış seçilerek maskeyi büyütebilir.

**Normalden bir kez seçilen kalem ROI'si:** `normal[865:892,670:890]`. Çıktı `ham_sonuclar.json` içinde ROI'nin medyan RGB/HSV'si de kaydedilir. Yalnızca normal görüntüdeki renkler temel alınarak dondurulmuş eşikler:

- RGB: `R∈[185,255], G∈[130,255], B∈[0,105]`
- HSV: `H∈[14,38], S∈[100,255], V∈[70,255]`

**Ölçüm:**

| Işık | RGB seçilen piksel | RGB alan oranı | HSV seçilen piksel | HSV alan oranı |
|---|---:|---:|---:|---:|
| Normal | 203.113 | %12,91 | 362.983 | %23,08 |
| Gölge | 0 | %0,00 | 221.381 | %14,08 |
| Lamba | 431.266 | %27,42 | 246.073 | %15,64 |

**Ne gördüm?** Gölge altında RGB hiç piksel seçmezken HSV bazı sarı bölgeleri seçmiştir. Lamba simülasyonunda RGB alanı %12,91'den %27,42'ye çıkmış; kalem dışındaki ısınmış masa renkleri de seçilmeye başlamıştır. **Neden olabilir?** RGB eşikleri mutlak kanal büyüklüğüne duyarlıdır; HSV de renk değişimlerine tamamen bağışık değildir. Bir yapışkan notun sarısı ile fosforlu kalemin sarısı, aynı eşik aralığına gelebilir. **Nasıl kontrol ederim?** Eşikleri **üç görüntüde aynı** tutup hem maske sayılarını hem de maskelerin kalem/not/masa üstünde nerelere yayıldığını görsel olarak karşılaştırırım. Gerekirse yalnızca hedefin konumunu belirleyen bağımsız bir ROI veya ayrı bir yer-gerçekliği etiketiyle **yanlış seçilmiş alanları** sayarım.

**Önemli:** `%12,91` bir doğruluk oranı değildir. Yalnızca beyaz maske piksellerinin toplam görüntü alanına yüzdesidir. Nesne sınıfını bildiğini kanıtlamaz.

**Sarı arka plan neden hedef gibi seçildi?** Çünkü renk maskesi nesnenin nesne olduğunu bilmez. Hedefle benzer RGB/HSV aralığındaki sarı not ve lamba altında sarımsı görünen başka yüzeyler de maskeye dahil olabilir; bu **yanlış pozitif** durumunu gösterir.

### Deney 6: Parlaklık ve gama (H3)

**Dönüşümleri uygulamadan önce iki cümlelik tahminler:**

- **b=+40:** Önceki en basit tahmin, her kanalın +40 artacağı ve dolayısıyla tüm görüntünün ortalamasının **148,49+40=188,49** olacağıdır. Ancak 255 sınırına dayanan pikseller varsa bu tahmin gerçek değerle uyuşmayabilir.
- **γ=0,5:** Üs 1'den küçük olduğundan `0<I<255` pikselleri büyür; ortalamanın artmasını bekliyorum. Koyu yazı/masa ayrıntıları açılırken beyaz bölgelerde fark nispeten azalabilir.
- **γ=2,0:** Üs 1'den büyük olduğundan `0<I<255` pikselleri küçülür; ortalamanın düşmesini bekliyorum. Özellikle orta/koyu tonlarda kararma belirgin olur.

**NumPy formülleri:**

```python
J_b = np.uint8(np.clip(I.astype(np.float32) + 40, 0, 255))
J_05 = np.uint8(np.round(np.clip(255*(I.astype(np.float32)/255)**0.5, 0, 255)))
J_20 = np.uint8(np.round(np.clip(255*(I.astype(np.float32)/255)**2.0, 0, 255)))
```

| Koşul | Kanal başına genel ortalama (0–255) |
|---|---:|
| Normal | 148,49 |
| Parlaklık b=+40 | **186,31** |
| Gamma 0,5 | **187,57** |
| Gamma 2,0 | **103,28** |

**En az bir tutmayan tahmin:** Parlaklık için **188,49** tahmin edilmişti, **186,31** ölçüldü. Tahmin **2,18 puan yüksek** kaldı, çünkü `I+40 >255` olan kanalların **%16,46'sı** 255'e kırpılmıştır. Başlangıçta tam +40 beklentisi **tutmamıştır**. Gama yön tahminleri doğru çıktı.

**Ne gördüm?** +40 ile tüm görüntü açıldı ama beklenen ortalama artışı gerçekleşmedi; γ=0,5 açtı, γ=2,0 koyulaştırdı. **Neden olabilir?** `clip()` üst sınıra yaklaşan değerleri 255'e sabitler; gama eğrisinin eğimi orta tonları farklı etkiler. **Nasıl kontrol ederim?** `np.mean(I.astype(float32)+40>255)` ile kırpılan kanal yüzdesini sayar, işlem öncesi/sonrası histogram ve ortalamayı karşılaştırırım. `uint8` üzerinde doğrudan toplama yapmayıp önce float'a çeviririm (taşmayı engellerim).

### Deney 7: 1/4 küçültme ve geri büyütme (H4)

**Ön tahmin — 2 cümle:** En yakın komşuyla 1/4 küçültmede dar çizgi ve küçük harfler kopacak veya çizgi kalınlıkları düzensiz görünecektir. `INTER_AREA` yerel pikselleri ortalayarak sahte yüksek frekansları azaltabilir ama kaybolan küçük harf detaylarını geri getiremez.

**Uygulama:** Orijinal yazı/çizgi kesiti `normal[357:669,180:1008] = 828×312` pikseldir. Genişlik/yükseklik 1/4 olunca **207×78** piksele iner (alan tam **1/16**). Hem `INTER_NEAREST` hem `INTER_AREA` ayrı ayrı 1/4'e küçültüldü, her iki küçük kesit **yalnızca görüntülemek için** `INTER_NEAREST` ile 828×312'ye büyütüldü.

**Sayısal kontrol:** Orijinal RGB kesite göre geri büyütülmüş piksellerin MAE'si yaklaşık **NEAREST 33,75**, **AREA 25,76**. MAE görüntü farkının basit büyüklüğüdür; okunabilirliğin veya nesne tanıma başarısının metriği değildir.

**Ne gördüm?** Orijinal küçük harfler ve paralel çizgiler büyütülmüş panellerde bozulmuştur. `NEAREST` bazı çizgileri kopuk/bloklu; `AREA` ise daha yumuşak fakat incelmiş/solmuş gösterebilir. **Neden olabilir?** Orijinalde birkaç piksel genişliğindeki yüksek frekans bilgisi örnekleme sırasında atılır/ortalaması alınır; büyütme yalnızca kalan sayıları çoğaltır. **Nasıl kontrol ederim?** Üç sonucu **aynı kesit, aynı ekran boyutu** ile yan yana gösterir, çizgilerin sürekliliğini inceler ve MAE'yi yan destek olarak kaydederim.

**Büyütme kaybolan yazıyı neden geri getirmedi?** Çünkü küçültme, orijinalin birçok pikselini tek piksele indirger. Harfin iç açıklığı, ince kenarı veya çizgi aralığı tek sayıya dönüştüğünde kaybolan eski değerleri `INTER_NEAREST` tahmin edemez; büyütülmüş görüntüye sadece tekrar eden blok pikseller ekler.

## 4. Önceden tahmin yapılmasının anlamı

Tahminler `run_experiment.py` dosyasının üst bölümündeki `PRE_REGISTERED` sözlüğünde, ölçümleri hesaplayan döngülerden önce kayıtlıdır. Rapor, tahminlerin tutup tutmadığını **gerçek program sonuçlarıyla** karşılaştırır. Sayılar daha sonra bu çalıştırmanın CSV/JSON'undan okunabilir; sonuçlar ayrı tutulmuştur.

## 5. Teknik değerlendirme ve ileriye yönelik iyileştirme

- **Renk alanı güvenilirliği:** Sabit eşik kullanmak değişken kontrolü açısından doğrudur ama hedef/arka plan renginin benzemesi yanlış pozitif üretir. Bu, sarı not ile görünür hale gelir.
- **Beyaz denge/pozlama:** Gerçek dünyada kamera değişkenlerini kontrol etmek gerekir. Sadece yapay kanal çarpanları ile gerçek kamera davranışı hakkında kesin yorum yapılamaz.
- **Maskelerin başarıya dönüştürülmesi:** Başarı için kalemin sınırları elle etiketlenip gerçek pozitif, yanlış pozitif ve yanlış negatif pikseller ayrılmalı; ancak o zaman IoU/precision/recall gibi ölçütler kullanılabilir.
- **Düşük örnekleme:** `INTER_AREA` yöntemi aliasing riskini azaltabilir, fakat örnekleme öncesi gerçek bilgiyi korumaz.
- **Yeniden üretim:** Kod, kaynak AI görsel, sabit ROI/parametreler, paket sürümleri, tüm maske/CSV çıktıları ve rapor aynı ZIP içindedir.

## 6. Teslim için yapılacak en önemli şey

Bu çalışma **yapay örnek veri** ile tamamlanmıştır. Ödevin gerçek deney niteliğini kazanması için kendi çektiğin üç fotoğrafı programa ver, normal fotoğraftaki objeye göre sabit eşikleri seç, tahminleri fotoğraflardan önce yaz, otomatik kamera ayarlarını açıkça not et ve rapordaki beyanı buna uygun güncelle. Gerçek fotoğraf çekilmiş gibi yazmak etik açıdan uygun değildir.
