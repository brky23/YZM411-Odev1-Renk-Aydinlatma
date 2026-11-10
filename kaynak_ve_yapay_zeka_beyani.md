# Kaynak ve üretici yapay zekâ beyanı

## Görsel kaynağı ve dürüstlük açıklaması

- **Temel sahne:** `gorseller/temel_sahne_ai.png`; **OpenAI görüntü üretimi** tarafından bu çalışma için yapay olarak oluşturuldu. Gerçek bir kişinin çektiği fotoğraf değildir. Sarı fosforlu kalem, sarı not, beyaz yazı/çizgi kâğıdı içeren masaüstü görünümüdür. Görseldeki basılı harfler yapay olarak oluşturulmuştur ve gerçek yazılı metin olarak hata içerebilir.
- **Normal koşul:** `gorseller/sahne_normal.png`; temel görüntünün RGB olarak okunmuş biçimi.
- **Gölge ve lamba koşulları:** `gorseller/sahne_shadow.png`, `gorseller/sahne_lamp.png`; `run_experiment.py / simulate_lighting()` içindeki sabit kanal kazançları ve mekânsal çarpanlarla **hesaplanmış** varyasyonlar. Fiziksel gölge veya lambayla çekilmiş fotoğraf değillerdir.
- **Tüm diğer PNG'ler:** `run_experiment.py` dosyası tarafından bu üç girdi üzerinden matematiksel olarak hesaplanmıştır.
- **Kişi:** Görüntülerde tanınabilir kişi bulunmamaktadır.
- **Gerçek fotoğraf şartı:** YZM411 yönergesindeki aynı sahnenin telefon/kamera ile üç kere fotoğraflanması şartı burada sağlanmamıştır. Bu nedenle paket, ilgili bölüm için **yerine geçecek gerçek saha verisi içermez**.

## Kullanılan üretici yapay zekâ

| Araç | Amaç | Etkilenen dosya/bölüm | Doğrulama |
|---|---|---|---|
| OpenAI görüntü üretimi | Tek bir açıklamalı masaüstü örnek sahnesi oluşturma | `gorseller/temel_sahne_ai.png` ve buna bağlı bütün demo görüntüleri | RGB görüntü dosyası açıldı ve sahne nesneleri/alanları görsel olarak kontrol edildi. |
| ChatGPT (OpenAI GPT-6) | Python analizi ve rapor metnini hazırlamada yardımcı olma | `run_experiment.py`, `README_TR.md`, `deney_aciklamalari.md`, `rapor_2_sayfa.pdf`, `kaynak_ve_yapay_zeka_beyani.md` | Python kodu gerçekten çalıştırıldı; maskelerin alanı `count_nonzero/size`, görüntü ortalamaları ve örnekleme MAE'si programatik ölçüldü. CSV/JSON'daki değerler PDF tablolarına aktarıldı. PDF iki sayfa olarak render edilip okunabilirliği incelendi. |

## Kullanılan teknik kaynaklar

1. Ders yönergesi: Kullanıcının sağladığı `YZM411_Odev1_Renk_Aydinlatma_Ornekleme.pdf` (2026–2027 Güz Dönemi, Ödev 1). Özellikle adımlar 2–8 ve etik/teslim uyarıları.
2. NumPy resmi dokümantasyonu: https://numpy.org/doc/stable/ (`ndarray` erişimi, `clip`, temel aritmetik).
3. OpenCV resmi dokümantasyonu: https://docs.opencv.org/4.x/ (BGR/RGB/HSV ve `cv2.resize` enterpolasyonları).
4. Pillow / Python Imaging Library: https://pillow.readthedocs.io/ (rapor görselinin açılması).
5. ReportLab: https://docs.reportlab.com/ (PDF yazımı).

Buradaki dış bağlantılar **teknik başvuru adresleridir**; deneysel veri kaynağı değildir. Örnek için Wikimedia vb. sitelerden indirilmiş üçüncü taraf fotoğraf **kullanılmadı**.

## Fotoğraf çekimi ve ölçümlerin sınırlılığı

Görselde otomatik kamera pozlaması veya beyaz dengesi **uygulanmadı**; matematiksel katsayılar seçildi. Bu yüzden gerçek kameradaki beyaz dengesi, gölgede renk kayması, çevresel yansıma, fiziksel ışık spektrumu, hareket ve JPEG gürültüsü tam olarak modellenmez. Tablo değerleri uydurulmuş değildir: sağlanan görsellerden kodla hesaplanmış **simüle edilmiş veriye ait gerçek ölçümler**dir. Gerçek çekim gözlemi olarak sunulmamalıdır.

## Yeniden üretilebilirlik

`requirements.txt` bağımlılıklarıyla `python run_experiment.py` komutu çalıştırılır. Sürüm/parametreler `ham_sonuclar.json` içinde saklanır. Temel sahne ZIP'te bulunduğundan işlem ağ bağlantısı gerektirmeden yeniden üretilebilir.
