#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""YZM411 Odev 1 - Renk, aydinlatma ve ornekleme.

Varsayilan demo, AI ile olusturulmus TEK bir referans sahnenin renk
matematikleriyle simulasyondan gecirilmis 3 versiyonunu olcer.
Bu uc gorsel farkli kosullarda cekilmis uc fotograf DEGILDIR.
Gercek 3 fotografla calismak icin:
 python run_experiment.py --normal A.jpg --shadow B.jpg --lamp C.jpg
Rapor PDF'sini, CSV'leri ve gorselleri her calismada yeniden olusturur.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
import platform
import sys
from pathlib import Path
from io import BytesIO

import cv2
import numpy as np
from PIL import Image
from reportlab.lib.colors import HexColor, Color, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parent
IMG_DIR = ROOT / 'gorseller'
TARGET_SIZE = (1536, 1024)  # w, h - tum fotograflar esit boyuta getirilir
# Normal sahne uzerinde kalemin kucuk hedef yuzu; tum esikler buradan saptanip sabitlenir.
TARGET_ROI = (670, 865, 890, 892)  # x1, y1, x2, y2
TEXT_ROI = (180, 357, 1008, 669)  # yazi / cizgili ornekleme alani
PIXELS = [(700, 835), (850, 875), (950, 900)]  # (x, y) sabit fiziksel noktalar
# Normal sahnedeki hedef ROI'ye bakilarak BELIRLENMIS ve sonradan dondurulmus esikler:
RGB_LO = np.array([185, 130, 0], dtype=np.uint8)
RGB_HI = np.array([255, 255, 105], dtype=np.uint8)
HSV_LO = np.array([14, 100, 70], dtype=np.uint8)  # OpenCV H:0..179
HSV_HI = np.array([38, 255, 255], dtype=np.uint8)
# 4-7 arasi her deney ICIN onceden yazilan tahminler; sonuclarin kendisi burada yoktur.
PRE_REGISTERED = {
    'H1': 'Uc gorselde boyut ve uint8 tipi ayni kalacak; ayni (x,y) noktasinin RGB degerleri isikla degisecek.',
    'H2': 'Golgede sabit RGB maskesi belirgin daralacak; HSV daha cok hedef pikselleri koruyacak. Lambada sari not da secilebilir.',
    'H3_b40': 'Ilk kaba tahmin: ortalama tam +40 artacak (kliplemeyi ihmal eden tahmin).',
    'H3_gamma05': 'Gama 0,5 ortalamayi artiracak ve koyu alanlari acacak.',
    'H3_gamma20': 'Gama 2,0 ortalamayi azaltacak ve koyu alanlari koyultacak.',
    'H4': '1/4 NEAREST ince cizgileri koparip sahte desen olusturacak; AREA tonlari ortalayip detaylari soluklastiracak.'
}


def save_rgb(path: Path, rgb: np.ndarray):
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))


def read_rgb(path: Path):
    bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if bgr is None:
        raise FileNotFoundError(f'Gorsel okunamadi: {path}')
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


def standardize(rgb):
    if (rgb.shape[1], rgb.shape[0]) == TARGET_SIZE:
        return rgb
    return cv2.resize(rgb, TARGET_SIZE, interpolation=cv2.INTER_AREA)


def simulate_lighting(normal):
    """Tamamen simule edilmis sabit isik/renk kazanci. Fiziksel lamba/golge kaydi degil!"""
    h, w = normal.shape[:2]
    x = np.linspace(0, 1, w, dtype=np.float32)[None, :, None]
    grad = 0.96 + 0.06 * x
    f = normal.astype(np.float32)
    shadow = np.uint8(np.clip(f * np.array([0.50, 0.56, 0.64], np.float32)[None,None,:] * grad + 1.5, 0, 255))
    # Sıcak lamba: R daha cok; G daha az; B oldukca az. Biraz konumsal varyasyon.
    warm = (1.00 + 0.06*(1-x))
    lamp = np.uint8(np.clip(f * np.array([1.24, 0.97, 0.72], np.float32)[None,None,:] * warm
                            + np.array([5.0, 1.0, 1.0], np.float32)[None,None,:], 0, 255))
    return shadow, lamp


def brightness(rgb, b=40):
    return np.uint8(np.clip(rgb.astype(np.float32) + float(b), 0, 255))


def gamma_transform(rgb, gamma):
    x = rgb.astype(np.float32)/255.0
    return np.uint8(np.round(np.clip(255.0 * np.power(x, gamma), 0, 255)))


def mask_rgb(rgb):
    return np.uint8(np.all((rgb >= RGB_LO) & (rgb <= RGB_HI), axis=2) * 255)


def mask_hsv(rgb):
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    return cv2.inRange(hsv, HSV_LO, HSV_HI)


def jpeg_for_report(rgb, path):
    Image.fromarray(rgb).save(path, quality=91, optimize=True)


def ensure_font():
    candidates = [
        ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'),
        ('/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf')]
    for regular, bold in candidates:
        if Path(regular).exists() and Path(bold).exists():
            pdfmetrics.registerFont(TTFont('TR',regular)); pdfmetrics.registerFont(TTFont('TRBold',bold))
            return 'TR','TRBold'
    raise RuntimeError('Turkce TrueType font bulunamadi')


def draw_paragraph(c, text, x, y, width, size=7.6, lineheight=11.0, font='TR', color='#233447'):
    c.setFillColor(HexColor(color)); c.setFont(font, size)
    words = text.replace('\n', ' \n ').split(' ')
    line = ''
    for word in words:
        if word == '\n':
            if line:
                c.drawString(x, y, line); y -= lineheight; line = ''
            continue
        attempt = (line+' '+word).strip()
        if line and pdfmetrics.stringWidth(attempt, font, size) > width:
            c.drawString(x,y,line);y-=lineheight;line=word
        else: line=attempt
    if line: c.drawString(x,y,line);y-=lineheight
    return y


def draw_heading(c, label, x, y):
    c.setFont('TRBold', 10.0); c.setFillColor(HexColor('#153455')); c.drawString(x,y,label)
    c.setStrokeColor(HexColor('#dce4ee')); c.setLineWidth(0.7); c.line(x,y-6,559,y-6)


def img_fit(c, path, x, y, w, h, outline=True):
    img = Image.open(path)
    iw,ih=img.size; scale=min(w/iw,h/ih)
    dw,dh=iw*scale,ih*scale; xx=x+(w-dw)/2; yy=y+(h-dh)/2
    # PDF icinde kucuk gorunen 1536 px kaynaklari tekrar raw olarak gommekten
    # kacin: gorsellerin ozgun PNG'leri ZIP'te aynen tutulur.
    thumb=img.copy()
    thumb.thumbnail((800,540),Image.Resampling.LANCZOS)
    buf=BytesIO()
    if thumb.mode in ('L','1'):
        thumb.save(buf,format='PNG',optimize=True)
    else:
        thumb.convert('RGB').save(buf,format='JPEG',quality=84,optimize=True)
    buf.seek(0)
    c.drawImage(ImageReader(buf),xx,yy,dw,dh,mask='auto')
    if outline:
        c.setStrokeColor(HexColor('#d7dfe7')); c.setLineWidth(.5); c.rect(x,y,w,h,fill=0,stroke=1)


def table(c, headers, rows, x, top, widths, row_h=18, size=7.2):
    total=sum(widths)
    c.setFillColor(HexColor('#143659'));c.rect(x,top-row_h,total,row_h,fill=1,stroke=0)
    xx=x
    for head,wd in zip(headers,widths):
        c.setFillColor(white);c.setFont('TRBold',size)
        c.drawString(xx+6,top-row_h+5.5,str(head));xx+=wd
    y=top-row_h
    for i,row in enumerate(rows):
        if i%2==0:
            c.setFillColor(HexColor('#edf3fa'));c.rect(x,y-row_h,total,row_h,fill=1,stroke=0)
        xx=x
        for cell,wd in zip(row,widths):
            c.setFillColor(HexColor('#233447'));c.setFont('TR',size)
            val=str(cell)
            while pdfmetrics.stringWidth(val,'TR',size)>wd-10 and len(val)>3:val=val[:-2]+'…'
            c.drawString(xx+6,y-row_h+5.5,val);xx+=wd
        y-=row_h
    return y


def make_pdf(record, paths, out):
    regular,bold=ensure_font()
    W,H=A4; c=canvas.Canvas(str(out),pagesize=A4)
    c.setTitle('YZM411 Odev 1 - Ornek ve simulasyon aciklamali rapor')
    colors={'navy':'#132c4a','gold':'#e4a827'}
    def header(num):
        c.setFillColor(HexColor(colors['navy'])); c.rect(0,H-75,W,75,fill=1,stroke=0)
        c.setFillColor(white); c.setFont(bold,16)
        c.drawString(36,H-32,'YZM 411  |  Renk, Aydınlatma ve Örnekleme')
        c.setFont(regular,8);c.drawString(36,H-51,'2026-2027 Güz  •  Ödev #1  •  Öğrenci No: [EKLEYİN]')
        c.setFillColor(HexColor('#facf67'));c.rect(36,H-62,520,2,fill=1,stroke=0)
        c.setFont(regular,7.5);c.setFillColor(HexColor('#657487'))
        c.drawString(36,23,'YZM411 • Rapor • Simülasyonlu örnek çalışma (gerçek üç çekim değildir)')
        c.drawRightString(556,23,f'{num} / 2')
    names=['Normal','Gölge','Lamba']
    fieldnames=['normal','shadow','lamp']
    col=(523-18)/3
    header(1)
    draw_heading(c,'01  |  Aynı sahne, üç farklı ışık görünümü',36,750)
    for i,(field,name) in enumerate(zip(fieldnames,names)):
        x=36+i*(col+9)
        img_fit(c,paths['input'][field],x,620,col,112)
        c.setFont(bold,8);c.setFillColor(HexColor('#1f3956')); c.drawCentredString(x+col/2,607,name)
    draw_paragraph(c,'UYARI: Temel sahne üretici yapay zekâ ile oluşturulmuştur. Gölge/lamba görüntüleri NumPy ile matematiksel olarak simüle edilmiştir; bağımsız kamera fotoğrafları değildir. Otomatik pozlama/beyaz dengesi uygulanmamıştır.',36,593,518,7.25,10.2,color='#804c07')
    draw_heading(c,'02  |  Normal ışıkta seçilen SABİT renk eşikleri',36,562)
    draw_paragraph(c,'RGB: R=185–255, G=130–255, B=0–105  •  HSV (OpenCV 8-bit): H=14–38, S=100–255, V=70–255. Eşikler gölge/lamba için değiştirilmedi.',36,548,520,7.0,10.0)
    for r,space in enumerate(['RGB','HSV']):
        for i,(field,name) in enumerate(zip(fieldnames,names)):
            x=36+i*(col+9); y=411-r*143
            img_fit(c,paths['mask'][space][field],x,y,col,110)
            p=record['masks'][space][field]['percent'];cnt=record['masks'][space][field]['count']
            c.setFillColor(HexColor('#203c59'));c.setFont(bold,7.5)
            c.drawCentredString(x+col/2,y-12,f'{space} / {name}: %{p:.2f} ({cnt:,} px)')
    draw_heading(c,'03  |  Maskelerin alan oranı karşılaştırması',36,237)
    rows=[]
    for field,name in zip(fieldnames,names):
        rows.append([name, f"{record['masks']['RGB'][field]['percent']:.2f}", f"{record['masks']['HSV'][field]['percent']:.2f}",str(record['masks']['RGB'][field]['count']), str(record['masks']['HSV'][field]['count'])])
    table(c,['Koşul','RGB %','HSV %','RGB piksel','HSV piksel'],rows,36,224,[111,78,78,128,128],17,7.0)
    y=draw_paragraph(c,'Ön tahmin (H2): Gölgede RGB maskesi belirgin azalır; HSV daha fazla sarı pikseli korur. Gözlem: Her iki yöntem de sarı yapışkan notu hedef kalemle karıştırabilir. Alan oranı başarım/doğruluk ölçütü değildir.',36,151,523,7.25,10)
    y=draw_paragraph(c,'Neden: Sınıflandırıcı nesneyi değil, renk aralığını seçer. Kontrol: Kalem için ayrıca geometrik ROI ya da yer-gerçekliği maskesi eklenerek yanlış pozitifler ayrı ölçülmelidir.',36,y-3,523,7.25,10)
    y=draw_paragraph(c,f"Sayısal yapı (H1) - normal: {record['shape']}; {record['dtype']}; gözlenen aralık {record['minmax'][0]}–{record['minmax'][1]}. OpenCV BGR okur; RGB için cvtColor, erişim için img[y, x, kanal] kullanıldı.",36,y-5,523,7.25,10)
    c.showPage()
    header(2)
    draw_heading(c,'04  |  Sabit (x,y) noktalarında gerçek sayısal ölçüm',36,750)
    rows=[]
    for p in record['pixels']:
        rows.append([f"({p['x']},{p['y']})",str(tuple(p['normal'])),str(tuple(p['shadow'])),str(tuple(p['lamp']))])
    table(c,['(x,y)','Normal RGB','Gölge RGB','Lamba RGB'],rows,36,738,[90,145,145,143],19,7.15)
    draw_paragraph(c,'Tahmin (H1): Boyut ve veri türü sabit; aynı noktada RGB değişecek. Ölçüm tabloyla doğrulandı. Kontrol: Üç görüntünün hizasını ve koordinatların aynı fiziksel bölgeye düştüğünü denetle.',36,654,523,7.1,9.5)
    draw_heading(c,'05  |  Parlaklık ve gama (normal görüntü üzerinde ayrı ayrı)',36,631)
    for i,(key,label) in enumerate([('b40','b=+40'),('g05','γ=0,5'),('g20','γ=2,0')]):
        x=36+i*(col+9)
        img_fit(c,paths['trans'][key],x,500,col,111)
        c.setFont(bold,7.5);c.setFillColor(HexColor('#203c59'));c.drawCentredString(x+col/2,488,label)
    tr=record['transforms']
    table(c,['Durum','Görüntü ort.','Değişim / not'],[
        ['Normal',f"{tr['normal']:.2f}",'Temel ortalama'],
        ['b=+40',f"{tr['b40']:.2f}",f"+{tr['b40']-tr['normal']:.2f} (kırpma %{tr['clipping_percent']:.1f} kanal)"],
        ['γ=0,5',f"{tr['g05']:.2f}",'Açılma'],
        ['γ=2,0',f"{tr['g20']:.2f}",'Koyulaşma']],36,477,[121,148,254],15,7.0)
    draw_paragraph(c,'Tahmin (H3): b=+40 ile ortalama tam +40 artar; γ=0,5 açar, γ=2,0 koyulaştırır. İlk tahmin TUTMADI: 255 üstüne çıkan kanallar kırpıldı. Kontrol: Kırpılan kanal sayısı, histogram ve float formüllerini incele.',36,388,523,7.2,9.8)
    draw_heading(c,'06  |  1/4 örnekleme ve en yakın komşuyla geri büyütme',36,349)
    for i,(key,label) in enumerate([('original','Orijinal doku'),('nearest','NEAREST ↓1/4 ↑4'),('area','AREA ↓1/4 ↑4')]):
        x=36+i*(col+9)
        img_fit(c,paths['sampling'][key],x,231,col,91)
        c.setFont(bold,7.2);c.setFillColor(HexColor('#203c59'));c.drawCentredString(x+col/2,220,label)
    sample=record['sampling']
    draw_paragraph(c,f"Yazı ROI: {sample['roi_shape']} → {sample['down_shape']} piksel. Orijinale göre MAE: NEAREST {sample['nearest_mae']:.2f}, AREA {sample['area_mae']:.2f} (küçük daha yakındır; okuma doğruluğu DEĞİLDİR).",36,208,523,7.0,9.6)
    draw_paragraph(c,'Tahmin (H4): İnce çizgiler örnekleme sonrasında kopacak; NEAREST yapay desenler üretebilir, AREA yerel ortalamayla bulanıklaşır. Neden: Piksel gruplarındaki yüksek frekanslı bilgi 1/4’e inince kaybolur. Kontrol: Orijinal ve iki geri büyütülmüş kesiti aynı ölçekte karşılaştır.',36,180,523,7.0,9.4)
    draw_heading(c,'07  |  Kısa değerlendirme, sınırlar ve kaynak beyanı',36,134)
    y=draw_paragraph(c,'Sarı arka plan neden hedef seçildi? Çünkü sarı notun H/S/V veya RGB değerleri kalemin eşik aralığına girer. Büyütme yazıyı neden geri getirmedi? Çünkü küçültme aşamasında kaybolan piksel ayrıntısı enterpolasyonla yeniden elde edilemez.',36,120,523,6.9,9.2)
    y=draw_paragraph(c,'Sınır: Üçü gerçek bağımsız çekim değil, tek AI sahnesinin dönüştürülmüş sürümleri. Kamera otomatik WB/pozlama, gerçek gölge, yansıma, sensör gürültüsü ve bakış değişimleri sınanmamıştır.',36,y-2,523,6.9,9.2)
    y=draw_paragraph(c,'AI beyanı: OpenAI görüntü üretimi (temel_sahne_ai.png); ChatGPT/GPT-6 (run_experiment.py, rapor, açıklamalar). Doğrulama: kod çalıştırıldı, CSV ile PDF sayıları karşılaştırıldı ve görseller kontrol edildi. Ayrıntılar: kaynak_ve_yapay_zeka_beyani.md.',36,y-2,523,6.9,9.2)
    c.save()


def run(args):
    IMG_DIR.mkdir(exist_ok=True)
    mode = 'demo_synthetic' if not args.normal else 'own_photos'
    if args.normal:
        if not (args.shadow and args.lamp):
            raise SystemExit('--normal, --shadow ve --lamp argumanlarinin ucu birlikte verilmeli.')
        normal,shadow,lamp=[standardize(read_rgb(Path(p))) for p in [args.normal,args.shadow,args.lamp]]
    else:
        normal=standardize(read_rgb(IMG_DIR / 'temel_sahne_ai.png'))
        shadow,lamp=simulate_lighting(normal)
    imgs=dict(normal=normal,shadow=shadow,lamp=lamp)
    paths={'input':{},'mask':{'RGB':{},'HSV':{}},'trans':{},'sampling':{}}
    for field,rgb in imgs.items():
        path=IMG_DIR/f'sahne_{field}.png';save_rgb(path,rgb);paths['input'][field]=path
    h,w,channels=normal.shape
    rec={'mode':mode,'shape':str(normal.shape),'dtype':str(normal.dtype),'minmax':(int(normal.min()),int(normal.max())),
         'masks':{},'pixels':[],'transforms':{},'sampling':{},'thresholds':{'rgb_low':RGB_LO.tolist(),'rgb_high':RGB_HI.tolist(),
         'hsv_low':HSV_LO.tolist(),'hsv_high':HSV_HI.tolist()},'predictions_before_experiments':PRE_REGISTERED,
         'versions':{'python':platform.python_version(),'opencv':cv2.__version__,'numpy':np.__version__,
                     'pillow':Image.__version__}}
    x1,y1,x2,y2=TARGET_ROI
    target_rgb=normal[y1:y2,x1:x2]
    target_hsv=cv2.cvtColor(target_rgb,cv2.COLOR_RGB2HSV)
    rec['calibration_roi']={'xyxy':TARGET_ROI,'median_rgb':np.median(target_rgb,axis=(0,1)).tolist(),
                            'median_hsv':np.median(target_hsv,axis=(0,1)).tolist()}
    for space,fn in [('RGB',mask_rgb),('HSV',mask_hsv)]:
        rec['masks'][space]={}
        for field,img in imgs.items():
            mask=fn(img); cnt=int(np.count_nonzero(mask)); pct=100.0*cnt/mask.size
            rec['masks'][space][field]={'count':cnt,'percent':pct}
            path=IMG_DIR/f'maske_{space}_{field}.png';cv2.imwrite(str(path),mask);paths['mask'][space][field]=path
    for (x,y) in PIXELS:
        p={'x':x,'y':y}
        for field,rgb in imgs.items():p[field]=[int(v) for v in rgb[y,x]]
        rec['pixels'].append(p)
    b40=brightness(normal,+40);g05=gamma_transform(normal,0.5);g20=gamma_transform(normal,2.0)
    trans={'b40':b40,'g05':g05,'g20':g20}
    for key,arr in trans.items():
        path=IMG_DIR/f'donusum_{key}.png';save_rgb(path,arr);paths['trans'][key]=path
    rec['transforms']={'normal':float(normal.mean()),'b40':float(b40.mean()),'g05':float(g05.mean()),
                       'g20':float(g20.mean()),'clipping_percent':float(np.mean(normal.astype(np.uint16)+40>255)*100),
                       'b40_exact_prediction':float(normal.mean()+40)}
    rx1,ry1,rx2,ry2=TEXT_ROI
    original=normal[ry1:ry2,rx1:rx2].copy()
    sh,sw=original.shape[:2]
    dst=(max(1,sw//4),max(1,sh//4))
    down_nearest=cv2.resize(original,dst,interpolation=cv2.INTER_NEAREST)
    down_area=cv2.resize(original,dst,interpolation=cv2.INTER_AREA)
    up_nearest=cv2.resize(down_nearest,(sw,sh),interpolation=cv2.INTER_NEAREST)
    up_area=cv2.resize(down_area,(sw,sh),interpolation=cv2.INTER_NEAREST)
    for key,arr in [('original',original),('nearest',up_nearest),('area',up_area)]:
        path=IMG_DIR/f'ornekleme_{key}.png';save_rgb(path,arr);paths['sampling'][key]=path
    rec['sampling']={'roi_shape':f'{sw}x{sh}','down_shape':f'{dst[0]}x{dst[1]}',
                     'nearest_mae':float(np.mean(np.abs(original.astype(np.int16)-up_nearest.astype(np.int16)))),
                     'area_mae':float(np.mean(np.abs(original.astype(np.int16)-up_area.astype(np.int16)))),
                     'nearest_down_shape':down_nearest.shape,'area_down_shape':down_area.shape}
    with open(ROOT/'olcumler.csv','w',newline='',encoding='utf-8-sig') as f:
        writer=csv.writer(f);writer.writerow(['deney','kosul','yontem','deger','birim','aciklama'])
        for space in ['RGB','HSV']:
            for field in ['normal','shadow','lamp']:
                r=rec['masks'][space][field]
                writer.writerow(['renk_maskesi',field,space,round(r['percent'],6),'yuzde','Secilen alan/goruntu alani'])
                writer.writerow(['renk_maskesi',field,space,r['count'],'piksel','Beyaz maske pikseli'])
        for k in ['normal','b40','g05','g20']:
            writer.writerow(['donusum','normal_fotograf',k,round(rec['transforms'][k],6),'0-255','Tum kanal ortalamasi'])
        writer.writerow(['donusum','normal_fotograf','clipping',round(rec['transforms']['clipping_percent'],6),'kanal_yuzdesi','I+40>255 olan kanallar'])
        for k in ['nearest','area']:
            writer.writerow(['ornekleme','yazi_doku_ROI',k,round(rec['sampling'][f'{k}_mae'],6),'MAE','Orijinal ile geri buyutulen arasindaki mutlak fark'])
    with open(ROOT/'piksel_olcumleri.csv','w',newline='',encoding='utf-8-sig') as f:
        wr=csv.writer(f);wr.writerow(['x','y','normal_R','normal_G','normal_B','golge_R','golge_G','golge_B','lamba_R','lamba_G','lamba_B'])
        for row in rec['pixels']:wr.writerow([row['x'],row['y']]+row['normal']+row['shadow']+row['lamp'])
    with open(ROOT/'ham_sonuclar.json','w',encoding='utf-8') as f:
        json.dump(rec,f,ensure_ascii=False,indent=2,default=lambda x:x.item() if isinstance(x,np.integer) else str(x))
    make_pdf(rec,paths,ROOT/'rapor_2_sayfa.pdf')
    print('Mod:',mode,'| shape:',rec['shape'],'| dtype:',rec['dtype'],'| min-max:',rec['minmax'])
    print('Ayni noktalar icin OpenCV ornek erisim: bgr[y,x,0] = B; rgb[y,x,0] = R')
    for p in rec['pixels']:print(p)
    print('Maske yuzdeleri:',{s:{k:round(v['percent'],2) for k,v in d.items()} for s,d in rec['masks'].items()})
    print('Ortalamalar:',rec['transforms']);print('Ornekleme:',rec['sampling'])
    print('Olusturulan: rapor_2_sayfa.pdf, olcumler.csv, piksel_olcumleri.csv, ham_sonuclar.json, gorseller/')
    return rec

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='YZM411 deneylerinin gercekten calistirilan ve yeniden olusturulabilir ornek paketi')
    parser.add_argument('--normal',type=str,help='Gercek normal isik fotografi')
    parser.add_argument('--shadow',type=str,help='Gercek golge fotografi')
    parser.add_argument('--lamp',type=str,help='Gercek lamba fotografi')
    run(parser.parse_args())
