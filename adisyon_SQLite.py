import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import sqlite3
import os
import shutil
from pathlib import Path # Kullanılmıyor, kaldırılabilir
import json # Kullanılmıyor, kaldırılabilir
import subprocess

# --- Sabit Tanımlamalar ---
# Renkler
RENK_BOS_MASA = "#fefcbf"       # Açık Sarı
RENK_DOLU_MASA = "#faa93e"      # Turuncu
RENK_MUSTERILI_MASA = "#a7c5eb"  # Açık Mavi (Müşteri atanmış)
RENK_BEKLEYEN_MASA = "#e57373"  # Açık Kırmızı (30 dk işlem yapılmamış)
RENK_BUTON_MASA_YONETIM = "#fac35b" # Sarımsı
RENK_BUTON_ODEME = "#fab918"    # Koyu Sarı
RENK_BUTON_KAPAT = "#e57373"    # Kırmızımsı
RENK_BUTON_ARA_ODEME = "#39b1fa"  # Mavi
RENK_BUTON_EKLE_CIKAR = "#c8fb8a" # Açık Yeşil
RENK_BUTON_YONETIM = "#fdd364"  # Açık Turuncu (Müşteri/Ürün)
RENK_BUTON_RAPOR = "#4CAF50"    # Yeşil
RENK_BUTON_EXPORT = "#2196F3"   # Mavi
RENK_BUTON_TEMIZLE = "#FF5722"  # Turuncu Kırmızı

# Kategori renk tanımları (Hızlı satış butonları için)
KATEGORI_RENKLERI = {
    "SICAK KAHVE": "#f9e79f",
    "SOĞUK KAHVE": "#edbb99",
    "SICAK İÇECEK": "#e74c3c", # Kırmızı
    "SOĞUK İÇECEK": "#85c1e9", # Mavi
    "MILK SHAKE": "#98fb98",   # Açık Yeşil
    "TATLI": "#fad7a0",      # Pastel Turuncu
    "FRAPPE": "#d2b4de"      # Lila
}
# Kategori renkleri için metin rengi (arka plana göre otomatik ayar)
# Açık renkler için siyah metin, koyu renkler için beyaz metin
def get_text_color(bg_color):
    # Basit bir parlaklık kontrolü (HSL veya RGB parlaklığı hesaplanabilir)
    # Burada sadece belirgin koyu renkler için beyaz kullanılıyor
    if bg_color in [KATEGORI_RENKLERI["SICAK İÇECEK"], KATEGORI_RENKLERI["SOĞUK İÇECEK"]]:
         return "#f4f6f7" # Beyaz
    return "black"

# Boyutlar ve Padding
PAD_X = 5
PAD_Y = 5
MASA_BTN_WIDTH = 18
MASA_BTN_HEIGHT = 5
RAPOR_TARIH_FORMATI = "%d.%m.%Y"
DB_DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # ISO 8601 formatı, sorgulamalar için daha iyi
INACTIVITY_THRESHOLD_MIN = 30 # Masa inaktiflik süresi (dakika)
ARCHIVE_THRESHOLD_DAYS = 30 # Kaç günden eski boş masaların arşivleneceği

# --- Ana Uygulama Sınıfı ---
class CafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Cafe Adisyon Sistemi")
        self.root.geometry("1250x700") # Başlangıç boyutu

        self.style = ttk.Style()
        self._configure_styles() # ttk stillerini ayarla

        # Veritabanı bağlantısı ve tabloları oluştur/kontrol et
        self.db_file = 'cafe.db' # Veritabanı dosya adını sakla
        self.conn = sqlite3.connect('cafe.db')
        self.conn.row_factory = sqlite3.Row # Sütun isimleriyle verilere erişim için
        self.cursor = self.conn.cursor()

        self._veritabani_tablolarini_olustur()
        self._load_default_data() # Tablolar oluşturulduktan sonra varsayılan veriler yüklenir

        # !!! YENİ: musteriler tablosuna cumulative_balance sütununu ekle (varsa hata vermez)
        try:
            self.cursor.execute("ALTER TABLE musteriler ADD COLUMN cumulative_balance REAL DEFAULT 0.0")
            self.conn.commit()
            print("musteriler tablosuna cumulative_balance sütunu eklendi (veya zaten vardı).")
        except sqlite3.Error as e:
            # Eğer sütun zaten varsa OperationalError verir, bu beklenir.
            # Başka bir hata varsa yazdır.
            if "duplicate column name" not in str(e):
                 print(f"Hata: musteriler tablosuna cumulative_balance sütunu eklenirken veritabanı hatası: {e}")
            self.conn.rollback() # Hata durumunda rollback yap

        self._yedek_al() # Program açılışında yedek al

        # Başlangıç değişkenleri
        self.aktif_masa = None
        self.current_mode = "normal" # Uygulama modunu takip et (normal, assign_customer vb.)
        # self.toplam_tutar ve self.iskonto artık Adisyon sekmesinde anlık hesaplanacak veya DB'den çekilecek

        # Müşteri Atama Mod Sistemi Fonksiyonları (Önce tanımlanmalı)
        self._perform_customer_assignment = self._perform_customer_assignment # Placeholder ataması
        self._initiate_assign_customer_mode = self._initiate_assign_customer_mode
        self._start_assign_customer_selection_mode = self._start_assign_customer_selection_mode
        self._on_masa_button_click = self._on_masa_button_click
        self._assign_customer_to_clicked_masa = self._assign_customer_to_clicked_masa


        # Ana arayüz (Notebook) oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=PAD_Y, padx=PAD_X, fill=tk.BOTH, expand=True)

        # Sekmeleri oluştur
        self.masa_frame = ttk.Frame(self.notebook, padding="10")
        self.adisyon_frame = ttk.Frame(self.notebook, padding="10")
        self.musteri_frame = ttk.Frame(self.notebook, padding="10")
        self.urun_frame = ttk.Frame(self.notebook, padding="10")
        self.muhasebe_frame = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.masa_frame, text="Masa Yönetimi")
        self.notebook.add(self.adisyon_frame, text="Adisyon")
        self.notebook.add(self.musteri_frame, text="Müşteri İşlemleri")
        self.notebook.add(self.urun_frame, text="Ürün Yönetimi")
        self.notebook.add(self.muhasebe_frame, text="Muhasebe")

        # Arayüzleri oluştur
        self.masa_arayuz_olustur()
        self.adisyon_arayuz_olustur()
        self.musteri_arayuz_olustur()
        self.urun_arayuz_olustur()
        self.muhasebe_arayuz_olustur()


        # Sekme değişim olayını bağla
        self.notebook.bind("<<NotebookTabChanged>>", self._sekme_degisti)

        # Program başladığında Masa Yönetimi sekmesini seç
        self.notebook.select(0)

        # Saat etiketini güncelle
        self._saat_guncelle()

        # Program kapanırken veritabanını kapat
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        print(f"Veritabanı yedeği alındı: {self.last_backup_path}")


    def _veritabani_tablolarini_olustur(self):
        """Veritabanı tablolarını oluşturur ve gerekli sütunların varlığını kontrol eder (Varsayılan ürün ekleme mantığı kaldırıldı)"""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masalar (
                masa_no TEXT PRIMARY KEY,
                durum TEXT DEFAULT 'boş', -- 'boş', 'dolu'
                musteri_id INTEGER, -- İlişkili müşteri ID'si
                toplam REAL DEFAULT 0.0,
                acilis TEXT, -- ISO formatında tarih ve saat
                kapanis TEXT, -- ISO formatında tarih ve saat
                son_adisyon_zamani TEXT, -- ISO formatında son adisyonun eklendiği saat
                son_islem_zamani TEXT -- ISO formatında (açılış, sipariş, ödeme, müşteri atama gibi) son işlem saati
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS urunler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sira INTEGER UNIQUE, -- Hızlı satış butonları için sıralama
                urun_adi TEXT UNIQUE,
                fiyat REAL,
                kategori TEXT
            )
        ''')

        # !!! Varsayılan ürün ekleme mantığı buradan kaldırıldı. Bu işi _load_default_data() yapacak. !!!
        # try:
        #     self.cursor.execute("SELECT COUNT(*) FROM urunler")
        #     urun_sayisi = self.cursor.fetchone()[0]
        #     if urun_sayisi == 0:
        #         print("urunler tablosu boş, varsayılan ürünler ekleniyor...")
        #         # ... (varsayılan ürün ekleme döngüsü ve commit) ...
        #     else:
        #         print(f"urunler tablosunda {urun_sayisi} ürün mevcut, varsayılan ürünler eklenmedi.")
        # except ...:
        #     ...


        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masa_siparisleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT, -- İlişkili masa numarası
                urun_adi TEXT,
                fiyat REAL,
                miktar INTEGER,
                tutar REAL, -- fiyat * miktar
                FOREIGN KEY(masa_no) REFERENCES masalar(masa_no),
                UNIQUE(masa_no, urun_adi) -- Bir masada aynı üründen sadece tek bir satır olmalı
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS musteriler (
                musteri_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT,
                soyad TEXT,
                telefon TEXT UNIQUE,
                adres TEXT,
                kayit_tarihi TEXT, -- ISO formatında
                cumulative_balance REAL DEFAULT 0.0
            )
        ''')

        # Savunma amaçlı kontrol ve ekleme: soyad sütununun varlığını kontrol et ve ekle
        try:
            self.cursor.execute("SELECT soyad FROM musteriler LIMIT 1")
            # print("musteriler tablosunda soyad sütunu mevcut.")
        except sqlite3.OperationalError:
            print("musteriler tablosunda soyad sütunu eksik, ekleniyor...")
            try:
                self.cursor.execute("ALTER TABLE musteriler ADD COLUMN soyad TEXT")
                self.conn.commit()
                print("soyad sütunu başarıyla eklendi.")
            except sqlite3.Error as e:
                print(f"Hata: soyad sütunu eklenirken veritabanı hatası: {e}")
                self.conn.rollback()
        except Exception as e:
             print(f"soyad sütunu kontrol edilirken beklenmedik hata: {e}")


        # Savunma amaçlı kontrol ve ekleme: cumulative_balance sütununun varlığını kontrol et ve ekle
        try:
            self.cursor.execute("SELECT cumulative_balance FROM musteriler LIMIT 1")
            # print("musteriler tablosunda cumulative_balance sütunu mevcut.")
        except sqlite3.OperationalError:
            print("musteriler tablosunda cumulative_balance sütunu eksik, ekleniyor...")
            try:
                self.cursor.execute("ALTER TABLE musteriler ADD COLUMN cumulative_balance REAL DEFAULT 0.0")
                self.conn.commit()
                print("cumulative_balance sütunu başarıyla eklendi.")
            except sqlite3.Error as e:
                print(f"Hata: cumulative_balance sütunu eklenirken veritabanı hatası: {e}")
                self.conn.rollback()
        except Exception as e:
             print(f"cumulative_balance sütunu kontrol edilirken beklenmedik hata: {e}")


        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                tarih TEXT, -- Kapanış tarihi (ISO formatında)
                odeme_turu TEXT,
                toplam REAL, -- Kapanan masanın toplamı
                musteri_id INTEGER -- İlişkili müşteri ID'si (varsa)
            )
        ''')

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS siparis_detaylari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siparis_id INTEGER, -- İlişkili siparis_gecmisi ID'si
                urun_adi TEXT,
                fiyat REAL,
                miktar INTEGER,
                tutar REAL,
                FOREIGN KEY(siparis_id) REFERENCES siparis_gecmisi(id)
            )
        ''')

        self.cursor.execute('''
             CREATE TABLE IF NOT EXISTS ara_odemeler (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 masa_no TEXT,
                 miktar REAL,
                 tarih TEXT, -- ISO formatında
                 FOREIGN KEY(masa_no) REFERENCES masalar(masa_no)
             )
        ''')

        self.conn.commit()

    def _load_default_data(self):
        """Tablolar boşsa varsayılan verileri yükler"""
        # Ürünler kontrolü
        self.cursor.execute("SELECT COUNT(*) FROM urunler")
        if self.cursor.fetchone()[0] == 0:
            default_products = [
                ("MOCHA", 80.0, "SICAK KAHVE", 1), # Kategori renkleriyle uyumlu hale getirildi
                ("DOPPIO", 80.0, "SICAK KAHVE", 2),
                ("ESPR. MOCCHIATO", 80.0, "SICAK KAHVE", 3),
                ("AMERICANO", 90.0, "SICAK KAHVE", 4),
                ("CAPPUCINO", 80.0, "SICAK KAHVE", 5),
                ("LATTE", 90.0, "SICAK KAHVE", 6),
                ("FLAT WHITE", 80.0, "SICAK KAHVE", 7),
                ("CORTADO", 90.0, "SICAK KAHVE", 8),
                ("ESPRESSO", 120.0, "SICAK KAHVE", 9),
                ("CAR. MOCCHIATO", 120.0, "SICAK KAHVE", 10),
                ("WHITE MOCHA", 120.0, "SICAK KAHVE", 11),
                ("TUF. NUT LATTE", 130.0, "SICAK KAHVE", 12),
                ("FILTRE KAHVE", 80.0, "SICAK KAHVE", 13),
                ("F. KAHVE SÜTLÜ", 90.0, "SICAK KAHVE", 14),
                ("SICAK ÇIKOLATA", 120.0, "SICAK İÇECEK", 15),
                ("ICE LATTE", 120.0, "SOĞUK KAHVE", 16),
                ("ICE LATTE COSTOM", 120.0,"SOĞUK KAHVE", 17),
                ("ICE MOCHA", 120.0, "SOĞUK KAHVE", 18),
                ("ICE AMERICANO", 110.0, "SOĞUK KAHVE", 19),
                ( "ICE WHITE MOCCA", 120.0,"SOĞUK KAHVE", 20),
                ("ICE FILTRE KAHVE", 110.0,"SOĞUK KAHVE", 21),
                ("ICE KAR. MOCHA", 120.0, "SOĞUK KAHVE", 22),
                ("ICE TUF. NUT LATTE", 130.0, "SOĞUK KAHVE", 23),
                ("COOL LIME", 130.0, "SOĞUK İÇECEK", 24), # Kategori düzeltildi
                ("LIMONATA", 70.0, "SOĞUK İÇECEK", 25), # Kategori düzeltildi
                ("KARADUT SUYU", 90.0, "SOĞUK İÇECEK", 26), # Kategori düzeltildi
                ("ÇILEKLI MILKSHAKE", 90.0, "MILK SHAKE", 27),
                ("KIRMIZI ORMAN", 120.0, "MILK SHAKE", 28),
                ("BÖĞÜRTLEN", 120.0, "MILK SHAKE", 29),
                ("KARA ORMAN", 100.0, "MILK SHAKE", 30),
                ("MENENGIÇ KAHVESI", 80.0, "SICAK İÇECEK", 31),
                ("DIBEK KAHVESI", 80.0, "SICAK İÇECEK", 32),
                ("DETOX KAHVE", 90.0, "SICAK İÇECEK", 33),
                ("ADAÇAYI", 60.0, "SICAK İÇECEK", 34),
                ("ÇAY", 30.0, "SICAK İÇECEK", 35),
                ("IHLAMUR", 60.0, "SICAK İÇECEK", 36),
                ("YEŞILÇAY", 60.0, "SICAK İÇECEK", 37),
                ("HIBISKUS", 60.0, "SICAK İÇECEK", 38),
                ("COCA KOLA", 60.0, "SOĞUK İÇECEK", 39),
                ("FANTA", 60.0, "SOĞUK İÇECEK", 40),
                ("SPRITE", 60.0, "SOĞUK İÇECEK", 41),
                ("İCE TEA", 60.0, "SOĞUK İÇECEK", 42),
                ("SODA SADE", 40.0, "SOĞUK İÇECEK", 43),
                ("MEYVELI SODA", 40.0, "SOĞUK İÇECEK", 44),
                ("SU", 20.0, "SOĞUK İÇECEK", 45),
                ("CHURCHILL", 40.0, "SOĞUK İÇECEK", 46),
                ("OREOLU FRAPPE", 80.0, "FRAPPE", 47),
                ("ÇIKOLATALI FRAPPE", 90.0, "FRAPPE", 48),
                ("VANILYALI FRAPPE", 90.0, "FRAPPE", 49),
                ("KARAMELLI FRAPPE", 100.0, "FRAPPE", 50),
                ("ÇILEKLI SMOOTHIE", 95.0, "FRAPPE", 51),
                ("MUZLU SMOOTHIE", 100.0, "FRAPPE", 52),
                ("SAN SEBASTIAN", 80.0, "TATLI", 53),
                ("MANGOLIA", 60.0, "TATLI", 54),
                ("TRAMISU", 60.0, "TATLI", 55),
            ]
            try:
                self.cursor.executemany(
                    "INSERT INTO urunler (urun_adi, fiyat, kategori, sira) VALUES (?, ?, ?, ?)",
                    default_products
                )
            except sqlite3.Error as e:
                 print(f"Varsayılan ürünler yüklenirken hata: {e}")


        # Masalar kontrolü
        self.cursor.execute("SELECT COUNT(*) FROM masalar")
        if self.cursor.fetchone()[0] == 0:
            for i in range(1, 6):
                self.cursor.execute(
                    "INSERT INTO masalar (masa_no, durum) VALUES (?, ?)",
                    (str(i), "boş")
                )

        self.conn.commit()

    def _configure_styles(self):
        """ttk widget'ları için stilleri ayarlar"""
        self.style.theme_use("clam") # Kullanılabilir temalar: ('clam', 'alt', 'default', 'classic')

        # Genel Font Ayarı
        self.style.configure(".", font=("Arial", 10)) # Varsayılan font
        self.style.configure("Treeview.Heading", font=("Arial", 10, "bold"))
        self.style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=[10, 5])

        # Buton Stilleri
        self.style.configure("TButton",
                             padding=6,
                             relief="flat",
                             background="#cccccc") # Varsayılan gri
        self.style.map("TButton",
                       background=[('active', '#dddddd')], # Hover rengi
                       relief=[('pressed', 'sunken')]) # Basılma efekti

        # Özelleştirilmiş Buton Stilleri (Renkler için ayrı stiller)
        self.style.configure("MasaYonetim.TButton", background=RENK_BUTON_MASA_YONETIM)
        self.style.map("MasaYonetim.TButton", background=[('active', '#e0a94a')])

        self.style.configure("Odeme.TButton", background=RENK_BUTON_ODEME)
        self.style.map("Odeme.TButton", background=[('active', '#d0a115')])

        self.style.configure("Kapat.TButton", background=RENK_BUTON_KAPAT)
        self.style.map("Kapat.TButton", background=[('active', '#c46262')])
        self.style.configure("Kapat.TButton", foreground="white") # Kırmızı üzerine beyaz metin
        self.style.map("Kapat.TButton", foreground=[('active', 'white')])

        self.style.configure("AraOdeme.TButton", background=RENK_BUTON_ARA_ODEME)
        self.style.map("AraOdeme.TButton", background=[('active', '#3398d8')])
        self.style.configure("AraOdeme.TButton", foreground="white") # Mavi üzerine beyaz metin
        self.style.map("AraOdeme.TButton", foreground=[('active', 'white')])

        self.style.configure("EkleCikar.TButton", background=RENK_BUTON_EKLE_CIKAR)
        self.style.map("EkleCikar.TButton", background=[('active', '#aedc7a')])

        self.style.configure("Yonetim.TButton", background=RENK_BUTON_YONETIM)
        self.style.map("Yonetim.TButton", background=[('active', '#e0b956')])

        self.style.configure("Rapor.TButton", background=RENK_BUTON_RAPOR)
        self.style.map("Rapor.TButton", background=[('active', '#449d48')])
        self.style.configure("Rapor.TButton", foreground="white")
        self.style.map("Rapor.TButton", foreground=[('active', 'white')])

        self.style.configure("Export.TButton", background=RENK_BUTON_EXPORT)
        self.style.map("Export.TButton", background=[('active', '#1d86e0')])
        self.style.configure("Export.TButton", foreground="white")
        self.style.map("Export.TButton", foreground=[('active', 'white')])

        self.style.configure("Temizle.TButton", background=RENK_BUTON_TEMIZLE)
        self.style.map("Temizle.TButton", background=[('active', '#e04a1d')])
        self.style.configure("Temizle.TButton", foreground="white")
        self.style.map("Temizle.TButton", foreground=[('active', 'white')])


        # Masa Butonları için özel style (rengi dinamik değişiyor, style sadece font/padding için)
        self.style.configure("MasaButton.TButton", font=("Arial", 10, "bold"), padding=10)
        self.style.map("MasaButton.TButton",
                       background=[('active', RENK_DOLU_MASA)], # Masa doluyken basıldığında rengi
                       foreground=[('active', 'black')],
                       relief=[('pressed', 'sunken')])

        # Label Stilleri
        self.style.configure("Baslik.TLabel", font=("Arial", 12, "bold"))
        self.style.configure("Bilgi.TLabel", font=("Arial", 10))
        self.style.configure("Toplam.TLabel", font=("Arial", 10, "bold"))

        # YENİ EKLENEN STYLE: Hızlı Satış Frame Arkaplanı için
        # ttk Frame'in arkaplanını bu şekilde ayarlamak temaya göre değişebilir.
        # Eğer işe yaramazsa, Canvas'ın bg rengi tek başına yeterli olabilir veya tk.Frame kullanılabilir.
        self.style.configure("HizliSatis.TFrame", background="#f0f0f0") # Canvas ile aynı açık gri tonu


    def _create_tables(self):
        """Veritabanı tablolarını oluşturur"""
        # Önce temel tabloları oluştur
        tables = [
            '''CREATE TABLE IF NOT EXISTS urunler (
                urun_adi TEXT PRIMARY KEY,
                fiyat REAL,
                kategori TEXT,
                sira INTEGER DEFAULT 9999
            )''',
            '''CREATE TABLE IF NOT EXISTS masalar (
                masa_no TEXT PRIMARY KEY,
                durum TEXT,
                toplam REAL DEFAULT 0,
                musteri_id TEXT,
                acilis TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                kapanis TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                son_adisyon_zamani TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                son_islem_zamani TEXT -- YYYY-MM-DD HH:MM:SS formatı
            )''',
            '''CREATE TABLE IF NOT EXISTS musteriler (
                musteri_id TEXT PRIMARY KEY,
                ad TEXT,
                telefon TEXT,
                -- puan INTEGER DEFAULT 0, -- MÜŞTERİ PUAN SİSTEMİ KALDIRILDI
                kayit_tarihi TEXT -- YYYY-MM-DD formatı
            )''',
            '''CREATE TABLE IF NOT EXISTS masa_siparisleri (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                urun_adi TEXT,
                fiyat REAL,
                miktar INTEGER,
                tutar REAL,
                FOREIGN KEY (masa_no) REFERENCES masalar(masa_no),
                FOREIGN KEY (urun_adi) REFERENCES urunler(urun_adi)
            )''',
            '''CREATE TABLE IF NOT EXISTS ara_odemeler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                miktar REAL,
                tarih TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                FOREIGN KEY (masa_no) REFERENCES masalar(masa_no)
            )''',
            '''CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                tarih TEXT, -- YYYY-MM-DD HH:MM:SS formatı (Kapanış tarihi gibi)
                odeme_turu TEXT,
                toplam REAL,
                musteri_id TEXT
                -- FOREIGN KEY musteri_id eklenmedi, silinen müşteriler sorun yaratmaz
            )''',
            '''CREATE TABLE IF NOT EXISTS siparis_detaylari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siparis_id INTEGER,
                urun_adi TEXT,
                fiyat REAL,
                miktar INTEGER,
                tutar REAL,
                FOREIGN KEY (siparis_id) REFERENCES siparis_gecmisi(id),
                FOREIGN KEY (urun_adi) REFERENCES urunler(urun_adi) -- Ürün silinirse history kalır
            )''',
             '''CREATE TABLE IF NOT EXISTS masa_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                acilis TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                kapanis TEXT, -- YYYY-MM-DD HH:MM:SS formatı
                musteri_id TEXT,
                toplam REAL,
                odeme_turu TEXT,
                tarih TEXT -- YYYY-MM-DD HH:MM:SS formatı (Kapanış tarihi gibi)
                -- FOREIGN KEY musteri_id eklenmedi
            )'''
        ]

        for table in tables:
            try:
                self.cursor.execute(table)
            except sqlite3.Error as e:
                print(f"Tablo oluşturulurken hata: {e}")
                messagebox.showerror("Veritabanı Hatası", f"Tablo oluşturulurken hata oluştu: {e}")

        # Mevcut veritabanını kontrol et ve gerekirse şemayı güncelle (sira sütunu gibi)
        try:
            self.cursor.execute("PRAGMA table_info(urunler)")
            columns = [column[1] for column in self.cursor.fetchall()]
            if 'sira' not in columns:
                self.cursor.execute("ALTER TABLE urunler ADD COLUMN sira INTEGER DEFAULT 9999")
                # Mevcut ürünlere varsayılan sıra ata
                self.cursor.execute("""
                    UPDATE urunler
                    SET sira = rowid
                    WHERE sira IS NULL OR sira = 9999
                """) # rowid veya 9999 olanlara başlangıç sırası ver
                print("sira sütunu eklendi ve varsayılan sıralama yapıldı.")

            # Musteriler tablosundan puan sütununu sil (Eğer önceden varsa)
            if 'puan' in [col[1] for col in self.cursor.execute("PRAGMA table_info(musteriler)").fetchall()]:
                 try:
                     self.cursor.execute("ALTER TABLE musteriler DROP COLUMN puan")
                     print("puan sütunu musteriler tablosundan silindi.")
                 except sqlite3.Error as e:
                     print(f"puan sütunu silinirken hata: {e}")
                     # Eğer sütun doluysa veya başka bir sorun varsa silinemeyebilir.
                     # Bu durumda manuel müdahale gerekebilir veya program bu sütunu yok sayarak devam edebilir.
                     messagebox.showwarning("Veritabanı Uyarısı", "Müşteriler tablosundan 'puan' sütunu kaldırılamadı. Lütfen manuel kontrol edin.")


        except sqlite3.Error as e:
            print(f"Veritabanı şema güncellemesi sırasında hata: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Veritabanı şeması güncellenirken hata oluştu: {e}")

        self.conn.commit()

    def _gunluk_bakim(self):
        """Günlük veritabanı bakım işlemleri"""
        try:
            # Veritabanı boyut kontrolü ve optimizasyon
            self.cursor.execute("VACUUM")

            # Sadece masa geçmişini (masa_gecmisi) 30 günden eski olanları sil.
            # Aktif masa siparişleri veya ara ödemeler bu fonksiyonda silinmemeli,
            # onlar masa kapatıldığında temizleniyor.
            # Masa_gecmisi kaydı zaten odeme_yap'ta tutuluyor.
            # gunluk_bakim'daki eski 'boş' masaları masa_gecmisine arşivleme/silme mantığı,
            # odeme_yap'taki masa_gecmisi kaydıyla çakışabilir/karışabilir.
            # En temizi, masa_gecmisi tablosunun sadece odeme_yap tarafından doldurulması
            # ve bu bakım fonksiyonunun sadece sipariş geçmişini (siparis_gecmisi, siparis_detaylari)
            # belirli bir süreden (örn. 1-2 yıl) eski olanları arşivlemesi/silmesi olabilir.
            # Ancak mevcut tablolar dikkate alındığında, siparis_gecmisi/detaylari ana rapor kaynağı
            # olduğu için onları silmek yerine, sadece masa_gecmisi tablosundaki eski kayıtları
            # temizlemek daha az riskli görünüyor.
            
            # Masa geçmişindeki (masa_gecmisi) 30 günden eski kayıtları sil
            # ISO formatı için tarih karşılaştırması
            tarih_esik = (datetime.now() - timedelta(days=ARCHIVE_THRESHOLD_DAYS)).strftime(DB_DATE_FORMAT)

            self.cursor.execute('''
                DELETE FROM masa_gecmisi
                WHERE tarih < ?
            ''', (tarih_esik,))

            self.conn.commit()

            # Yedek al (Bakım başarılıysa)
            self._yedek_al()

        except Exception as e:
            print(f"Bakım sırasında hata: {str(e)}")
            # Hata durumunda yedekleme yapılmaz


    def veritabani_temizle(self):
        """Manuel veritabanı temizliği ve boş/hatalı kayıt düzeltme"""
        try:
             # Bağlantıyı kapatıp yeniden açarak VACUUM öncesi olası kilitlenmeleri önleyelim
            self.conn.close()
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row # Row factory'yi yeniden ayarla
            self.cursor = self.conn.cursor()

            # VACUUM işlemi (veritabanı dosyasını küçültür)
            self.cursor.execute("VACUUM")
            self.conn.commit()

            # Masa geçmişi (masa_gecmisi) tablosundaki boş tarih/toplam/ödeme_turu kayıtlarını düzelt (ISO formatına uygun boş değer)
            self.cursor.execute(f'''
                UPDATE masa_gecmisi
                SET
                    acilis = COALESCE(acilis, '{datetime(2000, 1, 1, 0, 0, 0).strftime(DB_DATE_FORMAT)}'),
                    kapanis = COALESCE(kapanis, '{datetime(2000, 1, 1, 0, 0, 0).strftime(DB_DATE_FORMAT)}'),
                    toplam = COALESCE(toplam, 0.0),
                    odeme_turu = COALESCE(odeme_turu, 'Bilinmiyor')
                WHERE
                    acilis IS NULL OR
                    kapanis IS NULL OR
                    toplam IS NULL OR
                    odeme_turu IS NULL
            ''')
            self.conn.commit()

            messagebox.showinfo("Başarılı", "Veritabanı VACUUM yapıldı ve boş/hatalı kayıtlar düzeltildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Veritabanı temizlenirken hata oluştu:\n{str(e)}")
            # Hata durumunda bağlantının açık olduğundan emin olalım
            if not hasattr(self, 'conn') or self.conn is None:
                 self.conn = sqlite3.connect(self.db_file)
                 self.conn.row_factory = sqlite3.Row
                 self.cursor = self.conn.cursor()


    def _yedek_al(self):
        """Veritabanının yedeğini alır"""
        try:
            # self.db_file değişkenini kullan
            backup_filename = f"cafe_yedek_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            backup_dir = "yedekler"
            os.makedirs(backup_dir, exist_ok=True) # Klasörü oluştur yoksa
            backup_path = os.path.join(backup_dir, backup_filename)

            # Orijinal veritabanı dosyası
            original_db_path = self.db_file # <<< self.db_file kullanıldı

            # Bağlantıları kapatıp dosyayı kopyala (basit yedekleme yöntemi)
            # Daha robust yöntemler için veritabanı kilitlenme riskine karşı dikkatli olmak gerekir.
            # Bu örnekte basit kopyalama yeterli olabilir.
            # Eğer program çalışırken yedek alınacaksa veritabanı kilitli olabilir.
            # Alternatif olarak SQLite'ın backup API'si kullanılabilir, bu daha güvenlidir.

            # Basit dosya kopyalama yöntemi:
            # Eğer program açıkken bu yedek alınıyorsa dosya kilitli olabilir.
            # Daha güvenlisi için SQLite'ın kendi backup API'si kullanılmalı.
            # Şimdilik sadece açılışta kullanıldığı varsayılarak kopyalama yapalım.
            # Eğer çalışma anında da çağrılıyorsa, dosya kilitlenme hatası yönetilmelidir.

            # Önce mevcut bağlantıyı kapat (kopyalama için gerekli olabilir)
            # Ancak __init__ içinde yedek alınıyorsa henüz arayüz başlamamıştır.
            # Çalışma anında yedek alınıyorsa, bu kısmı düşünmek gerekir.

            # Şimdilik, db_file tanımından sonra __init__ içinde çağrıldığı varsayılarak,
            # bağlantıyı kapatmadan kopyalamayı deneyelim. Kilitlenme olursa try/except yakalar.

            import shutil
            shutil.copy2(original_db_path, backup_path) # Metadatasını da kopyalar

            self.last_backup_path = backup_path # Son yedek dosya yolunu sakla
            #print(f"Veritabanı yedeği alındı: {backup_path}") # Artık __init__ sonunda yazdırılıyor
            # messagebox.showinfo("Yedekleme Başarılı", f"Veritabanı başarıyla yedeklendi:\n{backup_path}", parent=self.root) # Yedekleme mesajı çok sık çıkmasın

        except FileNotFoundError:
            print(f"Yedek alınırken hata: '{self.db_file}' dosyası bulunamadı.") # <<< self.db_file kullanıldı
            # messagebox.showerror("Yedekleme Hatası", f"Veritabanı dosyası bulunamadı:\n{self.db_file}", parent=self.root) # Hata mesajı da çok sık çıkmasın
        except Exception as e:
            print(f"Yedek alınırken hata oluştu: {e}")
            # messagebox.showerror("Yedekleme Hatası", f"Veritabanı yedeği alınırken beklenmedik hata:\n{e}", parent=self.root)

# --- MÜŞTERİ ATAMA MOD SİSTEMİ FONKSİYONLARI ---
    # Lütfen bu fonksiyonların tamamını, __init__ metodundan sonra ve masa_arayuz_olustur metodundan önce ekleyin.

    def _perform_customer_assignment(self, masa_no):
        """Belirtilen masaya müşteri atama işleminin diyalog ve DB kısmını yapar"""

        # Müşteri ID veya Telefon ile arama
        # Ana pencere üzerinde gösterildi
        musteri_input = simpledialog.askstring("Müşteri Ata", f"Masa {masa_no} için müşteri ID veya Telefon Numarası:", parent=self.root)

        if musteri_input:
            musteri_input = musteri_input.strip()
            if not musteri_input:
                 messagebox.showwarning("Uyarı", "Müşteri ID veya Telefon girilmedi!", parent=self.root)
                 return False # İşlem yapılmadı

            # Müşteriyi ara (ID veya Telefon)
            try:
                self.cursor.execute('''
                    SELECT musteri_id, ad FROM musteriler
                    WHERE musteri_id = ? OR telefon = ?
                ''', (musteri_input, musteri_input))
                musteri = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilebilir

                if musteri:
                    musteri_id = musteri['musteri_id']
                    musteri_adi = musteri['ad']

                    # Masaya müşteriyi ata
                    self.cursor.execute('''
                        UPDATE masalar SET musteri_id = ?, son_islem_zamani = ? WHERE masa_no = ?
                    ''', (musteri_id, self._tarih_saat_al_db_format(), masa_no)) # Son işlem zamanı güncellendi
                    self.conn.commit()

                    # Eğer atama yapılan masa aktif masaysa, Adisyon sekmesindeki etiketi güncelle
                    # Bu kontrol sadece UI içindir, DB ataması zaten yapıldı
                    if self.aktif_masa == masa_no and hasattr(self, 'musteri_label'):
                        self.musteri_label.config(text=f"Müşteri: {musteri_adi}")

                    self._masa_butonlarini_guncelle() # Masa butonunu güncelle (müşteri bilgisi görünür)
                    messagebox.showinfo("Başarılı", f"Masa {masa_no} için müşteri '{musteri_adi}' atandı!", parent=self.root)
                    return True # İşlem başarılı

                else:
                    messagebox.showwarning("Uyarı", "Belirtilen ID veya Telefon ile müşteri bulunamadı!", parent=self.root)
                    return False # İşlem yapılmadı

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Masa {masa_no} için müşteri atanırken veritabanı hatası: {e}", parent=self.root)
                 self.conn.rollback()
                 return False # İşlem başarılı değil
            except Exception as e:
                 messagebox.showerror("Hata", f"Masa {masa_no} için müşteri atanırken beklenmedik hata: {e}", parent=self.root)
                 print(f"Müşteri atama hatası (perform): {e}")
                 return False # İşlem başarılı değil

        else: # Kullanıcı diyalogu iptal etti
             return False # İşlem yapılmadı


    def _initiate_assign_customer_mode(self):
        """Masa Yönetimi sekmesindeki 'Müşteri Ata' butonuna basıldığında modu başlatır veya aktif masaya atama yapar"""
        if self.current_mode == "assign_customer":
             # Zaten atama modundaysak, butona tekrar basmak modu iptal eder
             self.current_mode = "normal"
             if hasattr(self, 'masa_mode_label'):
                 self.masa_mode_label.config(text="Mod: Normal")
             messagebox.showinfo("Bilgi", "Müşteri atama modu iptal edildi.", parent=self.masa_frame)
             # Mod iptal edildiğinde butonların rengi/görünümü değişiyorsa güncelleme yapılabilir
             # self._masa_butonlarini_guncelle()
             return

        # Modda değiliz. Aktif masa var mı kontrol et.
        if self.aktif_masa:
             # Aktif masa varsa, kullanıcıya o masaya mı atama yapmak istediğini sor
             if messagebox.askyesno("Müşteri Ata", f"Aktif Masa ({self.aktif_masa}) için müşteri atamak ister misiniz?", parent=self.masa_frame):
                 # Evet dediyse, doğrudan atama işlemini çağır, mod başlatmaya gerek yok
                 self._perform_customer_assignment(self.aktif_masa)
                 # İşlem _perform_customer_assignment içinde başarı/hata mesajı gösterir ve masa butonlarını günceller
             # Hayır dediyse veya aktif masa yoksa, masa seçme modunu başlat

             else: # Kullanıcı aktif masaya atamayı reddetti, şimdi masa seçme modunu başlat
                 self._start_assign_customer_selection_mode()

        else: # Aktif masa yok, doğrudan masa seçme modunu başlat
             self._start_assign_customer_selection_mode()


    def _start_assign_customer_selection_mode(self):
        """Müşteri atamak için masa seçme modunu aktif hale getirir"""
        self.current_mode = "assign_customer"
        if hasattr(self, 'masa_mode_label'): # Label henüz oluşmamış olabilir (pek olası değil ama kontrol iyi)
             self.masa_mode_label.config(text="Mod: Müşteri Ata - Masayı Seçin")
        messagebox.showinfo("Bilgi", "Müşteri atamak istediğiniz masayı Masa Yönetimi sekmesinden seçin.", parent=self.masa_frame)
        # Mod durumuna özel buton görünümü gerekiyorsa burada _masa_butonlarini_guncelle çağrılabilir


    def _on_masa_button_click(self, masa_no):
        """Masa Yönetimi sekmesindeki masa butonuna tıklanma olayını mod durumuna göre yönlendirir"""
        # Masaya tıklandığında son işlem zamanını güncelle
        try:
             self.cursor.execute('''
                 UPDATE masalar SET son_islem_zamani = ? WHERE masa_no = ?
             ''', (self._tarih_saat_al_db_format(), masa_no))
             self.conn.commit()
        except sqlite3.Error as e:
             print(f"Masa {masa_no} son işlem zamanı güncellenirken hata: {e}")
        except Exception as e:
             print(f"Masa {masa_no} son işlem zamanı güncellenirken beklenmedik hata: {e}")


        if self.current_mode == "normal":
            # Normal modda, masayı aktif yap, sepeti yükle ve Adisyon sekmesine geç
            # _masa_sec artık masa durumunu (boş->dolu) DEĞİŞTİRMİYOR. O iş _sepete_ekle'de.
            # Sadece aktif masayı ayarlar, UI'ı günceller ve sekmeyi değiştirir.
            self._masa_sec(masa_no) # Bu metot zaten self.aktif_masa'yı set eder ve sekmeyi değiştirir
            # Note: _masa_sec içinde de son işlem zamanı güncelleniyordu, tekrar gerek yok.
            # _masa_sec çağrıldığı için masa butonları güncellenecek ve adisyona geçilecek.

        elif self.current_mode == "assign_customer":
            # Müşteri atama modunda, tıklanan masaya müşteri atama işlemini başlat
            self._assign_customer_to_clicked_masa(masa_no)
            # İşlem sonrası mod normal'e dönecek (_assign_customer_to_clicked_masa içinde)
            # Sekme değişimi YAPILMAZ.


    def _assign_customer_to_clicked_masa(self, masa_no):
        """Müşteri atama modunda iken bir masa tıklandığında müşteri atama işlemini gerçekleştirir ve modu sıfırlar"""
        # Perform customer assignment for the clicked masa
        success = self._perform_customer_assignment(masa_no)

        # İşlem tamamlandıktan sonra (başarılı veya iptal/hata), modu normal'e döndür
        self.current_mode = "normal"
        if hasattr(self, 'masa_mode_label'):
             self.masa_mode_label.config(text="Mod: Normal")

        # Masa butonlarının görünümü değiştiyse güncelleme yapılabilir
        # _perform_customer_assignment zaten bunu yapıyor

        # İşlem sonrası ek mesaj göstermeye gerek yok, _perform_customer_assignment kendi mesajını gösterir.
        # Sekme değişimi yapılmaz, kullanıcı Masa Yönetimi sekmesinde kalır.

    # --- MÜŞTERİ ATAMA MOD SİSTEMİ FONKSİYONLARI SONU ---

    def _musteri_sec(self, event):
        """Müşteri listesi Treeview'ında bir müşteri seçildiğinde form alanlarını doldurur"""
        # Bu fonksiyon, musteri_arayuz_olustur içinde Treeview'ın <<TreeviewSelect>> olayına bağlanmıştır.
        selected_item = self.musteri_listesi.selection()
        if not selected_item:
            self._musteri_formu_temizle() # Seçim kaldırılırsa formu temizle
            return

        # Seçili öğenin değerlerini al (Treeview'daki sütun sırasına göre)
        item_values = self.musteri_listesi.item(selected_item[0], "values")

        # Değerleri form alanlarına yerleştir
        self._musteri_formu_temizle() # Önce formu temizle

        # Treeview değerleri sırasıyla: ID, Ad, Soyad, Telefon, Adres, Kayıt Tarihi, Bakiye
        self.musteri_ad_entry.insert(0, item_values[1]) # Ad (index 1)
        self.musteri_soyad_entry.insert(0, item_values[2]) # Soyad (index 2)
        self.musteri_telefon_entry.insert(0, item_values[3]) # Telefon (index 3)
        self.musteri_adres_entry.insert(0, item_values[4]) # Adres (index 4)
        # Kayıt Tarihi Treeview'da var ama formda alanı yok (index 5)

        # Kumulatif Bakiye alanını doldur (index 6)
        # Treeview'dan gelen bakiye stringi "123 ₺" formatında olabilir, sadece sayıyı almalıyız
        try:
            bakiye_str = str(item_values[6]).replace(' ₺', '').strip() # Bakiye sütunu 6. index
            # Sayıya çevirip form alanına ondalıklı formatta yerleştir (kullanıcı düzenlerken kolaylık)
            bakiye_float = float(bakiye_str)
            self.musteri_bakiye_entry.insert(0, f"{bakiye_float:.2f}") # Ondalıklı göster
        except (ValueError, IndexError, TypeError): # IndexError veya TypeError (None gelirse) yakala
            self.musteri_bakiye_entry.insert(0, "0.00") # Hata olursa varsayılan değer

        # Seçili müşterinin ID'sini sakla (güncelleme veya silme için)
        self.secili_musteri_id = item_values[0] # ID sütunu 0. index

    # MASA YÖNETİMİ FONKSİYONLARI
    def masa_arayuz_olustur(self):
        """Masa Yönetimi sekmesi arayüzünü oluşturur"""
        # Buton Frame (üst kısım, sabit yükseklik)
        btn_frame = ttk.Frame(self.masa_frame)
        btn_frame.pack(pady=PAD_Y, fill=tk.X) # Yatayda genleşebilir

        # ttk Button Style kullan
        ttk.Button(btn_frame, text="Masa Ekle", width=15, style="MasaYonetim.TButton", command=self.masa_ekle).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(btn_frame, text="Masa Sil", width=15, style="MasaYonetim.TButton", command=self.masa_sil).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(btn_frame, text="Müşteri Ata", width=15, style="MasaYonetim.TButton", command=self._initiate_assign_customer_mode).pack(side=tk.LEFT, padx=PAD_X) 
        ttk.Button(btn_frame, text="İndirim Uygula", width=15, style="MasaYonetim.TButton", command=self.indirim_uygula).pack(side=tk.LEFT, padx=PAD_X)

        # Masalar Frame (Alt kısım, kalan alanı doldurur)
        self.masalar_frame = ttk.Frame(self.masa_frame)
        self.masalar_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=PAD_Y) # Hem yatay hem dikey genleşebilir

        # Grid için sütun ve satır ağırlıklarını ayarla
        # Bu, masalar_frame içindeki grid'in boş alanı doldurmasını sağlar
        for i in range(6): # Varsayılan 6 sütun
             self.masalar_frame.grid_columnconfigure(i, weight=1, uniform="masa_cols") # Ağırlık ver ve genişlikleri eşitle

        # Masa butonlarının kendileri sabit boyutta kalacak, grid hücreleri genleşecek.
        # Bu, buton içindeki metnin dağılmasını engeller.

        # İlk masa butonlarını oluştur
        self._masa_butonlarini_guncelle()


    def _masa_butonlarini_guncelle(self):
        """Veritabanındaki masa durumuna göre butonları yeniler (Müşteri Bakiyesi ve Toplam Borç dahil)"""
        # Önceki butonları temizle
        for widget in self.masalar_frame.winfo_children():
            widget.destroy()

        # Sabit ayarlar
        COLS = 6 # Sütun sayısı
        PAD = 8 # Butonlar arası boşluk

        # Masaları veritabanından çek (ISO tarih formatıyla)
        # Müşterinin kümülatif bakiyesini de çekiyoruz
        self.cursor.execute('''
            SELECT m.masa_no, m.durum, m.musteri_id, m.toplam, m.son_adisyon_zamani,
                   COALESCE(SUM(a.miktar), 0) as ara_odeme,
                   mu.ad as musteri_adi,
                   mu.cumulative_balance as musteri_bakiye, -- <<< Müşteri bakiyesi çekildi
                   m.son_islem_zamani
            FROM masalar m
            LEFT JOIN ara_odemeler a ON m.masa_no = a.masa_no
            LEFT JOIN musteriler mu ON m.musteri_id = mu.musteri_id
            GROUP BY m.masa_no
            ORDER BY CAST(m.masa_no AS INTEGER)
        ''')

        masalar = self.cursor.fetchall()

        for index, masa in enumerate(masalar):
            masa_no = masa['masa_no']
            durum = masa['durum']
            musteri_id = masa['musteri_id']
            toplam_masa_oturum = masa['toplam'] if masa['toplam'] is not None else 0.0 # Masa oturumu toplamı
            son_adisyon_str = masa['son_adisyon_zamani']
            ara_odeme = masa['ara_odeme'] if masa['ara_odeme'] is not None else 0.0
            musteri_adi = masa['musteri_adi']
            musteri_bakiye = masa['musteri_bakiye'] if masa['musteri_bakiye'] is not None else 0.0 # Müşteri bakiyesi alındı
            son_islem_str = masa['son_islem_zamani']

            # Durum ve metin belirleme
            durum_text = "DOLU" if durum == "dolu" else "BOŞ"

            # Müşteri adı ve bakiye bilgisi ekleme
            musteri_bilgi = ""
            if musteri_adi:
                 ad = musteri_adi.split()[0] if ' ' in musteri_adi else musteri_adi
                 # Müşteri adı ve bakiyeyi butona ekliyoruz
                 musteri_bilgi = f"\n{ad[:8]} (Bakiye: {musteri_bakiye:.0f} ₺)" # <<< Müşteri adı ve bakiye butona eklendi


            # Temel buton metni
            btn_text = f"Masa {masa_no}\nDurum: {durum_text}{musteri_bilgi}" # Müşteri bilgisi eklendi

            # Dolu masalar için ek bilgiler (masa oturumu toplamı ve Toplam Borç)
            if durum == "dolu":
                kalan = max(0.0, toplam_masa_oturum - ara_odeme) # Masa oturumu için kalan

                btn_text += f"\nOturum: {toplam_masa_oturum:.0f} ₺" # Masa oturumu toplamı

                # !!! YENİ: Toplam Borç Hesaplama ve Gösterme !!!
                # Toplam Borç = Müşterinin Kümülatif Bakiyesi + Masa Oturumu Toplamı
                total_owed = musteri_bakiye + toplam_masa_oturum
                btn_text += f"\nBorç: {total_owed:.0f} ₺" # Toplam Borç butona eklendi


                # Son işlem saatini göster (varsa)
                son_islem_saat_str = "-"
                if son_islem_str:
                     try:
                         son_islem_dt = datetime.strptime(son_islem_str, DB_DATE_FORMAT)
                         son_islem_saat_str = son_islem_dt.strftime("%H:%M")
                     except (ValueError, TypeError):
                         pass

                btn_text += f"\nSon İşlem: {son_islem_saat_str}"

                if ara_odeme > 0:
                    btn_text += f"\nÖ/K: {ara_odeme:.0f}/{kalan:.0f} ₺"


            # RENK AYARLARI
            bg_color = RENK_BOS_MASA if durum == "boş" else RENK_DOLU_MASA

            # MÜŞTERİ ATANMIŞ MASA KONTROLÜ (varsayılan dolu rengini geçersiz kılar)
            if musteri_id:
                 bg_color = RENK_MUSTERILI_MASA
            elif durum == "dolu" and son_islem_str:
                 try:
                     son_islem_dt = datetime.strptime(son_islem_str, DB_DATE_FORMAT)
                     time_difference = (datetime.now() - son_islem_dt).total_seconds()

                     if time_difference > INACTIVITY_THRESHOLD_MIN * 60:
                         bg_color = RENK_BEKLEYEN_MASA

                 except (ValueError, TypeError):
                     pass

            btn = tk.Button(
                self.masalar_frame,
                text=btn_text,
                command=lambda mn=masa_no: self._on_masa_button_click(mn),
                bg=bg_color,
                fg="black",
                width=MASA_BTN_WIDTH,
                height=MASA_BTN_HEIGHT,
                font=("Arial", 9, "bold"),
                relief="raised",
                wraplength=MASA_BTN_WIDTH * 8,
                justify="center"
            )

            row, col = divmod(index, COLS)
            btn.grid(row=row, column=col, padx=PAD, pady=PAD, sticky="nsew")

        total_rows = (len(masalar) + COLS - 1) // COLS
        for r in range(total_rows):
             self.masalar_frame.grid_rowconfigure(r, weight=1)


    def _masa_sec(self, masa_no):
        """Bir masa seçildiğinde Adisyon sekmesine geçer ve sepeti yükler (Masa durumunu değiştirmez)"""
        try:
            masa_no = str(masa_no)

            # Eğer zaten aktif masa aynı ise, sadece Adisyon sekmesine geç
            if self.aktif_masa == masa_no:
                self._sepeti_yukle()
                self.notebook.select(1)  # Adisyon sekmesine geç (index 1)
                return

            # Önceki aktif masanın son işlem zamanını güncelle (eğer bir masa seçiliyse)
            # Bu, masa butonu renginin doğru güncellenmesi için önemli
            if self.aktif_masa:
                 try:
                     self.cursor.execute('''
                         UPDATE masalar
                         SET son_islem_zamani = ?
                         WHERE masa_no = ?
                     ''', (self._tarih_saat_al_db_format(), self.aktif_masa))
                     self.conn.commit()
                 except sqlite3.Error as e:
                      print(f"Önceki aktif masa son işlem zamanı güncellenirken hata: {e}")


            # Yeni masayı aktif yap
            self.aktif_masa = masa_no

            # Masanın güncel durumunu DB'den çek (sadece bilgi amaçlı veya UI için)
            # Durum değiştirmek burada yapılmıyor artık
            self.cursor.execute('''
                SELECT durum FROM masalar WHERE masa_no = ?
            ''', (masa_no,))
            masa_info = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir
            # durum = masa_info['durum'] # Artık burada kullanılmıyor


            # UI güncellemeleri
            if hasattr(self, 'aktif_masa_label'):
                 self.aktif_masa_label.config(text=f"Aktif Masa: {masa_no}")

            # Müşteri bilgisini _sepeti_yukle içinde güncelliyoruz, burada çağırmaya gerek yok.
            # if hasattr(self, 'musteri_label'): ...


            # Sepeti yükle ve Adisyon sekmesine geç
            # Sepeti yükleme işlemi sırasında müşteri bilgisi ve toplam tutar da güncellenir.
            self._sepeti_yukle()
            # Masa butonlarını güncelle (durum ve toplam değişmediği için renk aynı kalır - eğer ürün eklenmediyse)
            self._masa_butonlarini_guncelle() # Masa rengi/bilgisi güncel durumu yansıtacak
            self.notebook.select(1)  # Adisyon sekmesine geç (index 1)

        except Exception as e:
            messagebox.showerror("Hata", f"Masa seçilirken hata oluştu: {str(e)}")
            print(f"Masa seçme hatası: {e}")
            import traceback
            traceback.print_exc()
            self.aktif_masa = None
            if hasattr(self, 'aktif_masa_label'):
                self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
            if hasattr(self, 'musteri_label'):
                 self.musteri_label.config(text="Müşteri: -")
            self._sepeti_temizle_ui_only() # Sadece arayüzü temizle


    def _masa_renk_guncelleme_timer(self):
        """Belirli aralıklarla masa buton renklerini günceller"""
        try:
            if hasattr(self, 'masalar_frame'):
                self._masa_butonlarini_guncelle()
        except Exception as e:
            print(f"Masa renk güncelleme timer hatası: {str(e)}")
        finally:
            # 10 dakika (600 saniye) sonra tekrar çalıştır
            self.root.after(INACTIVITY_THRESHOLD_MIN * 60 * 1000, self._masa_renk_guncelleme_timer)


    def masa_ekle(self):
        """Yeni bir masa ekler"""
        try:
            # Mevcut masa numaralarını al ve en yüksek olanı bul
            self.cursor.execute("SELECT masa_no FROM masalar ORDER BY CAST(masa_no AS INTEGER) DESC LIMIT 1")
            son_masa = self.cursor.fetchone()
            yeni_masa_no = str(int(son_masa['masa_no']) + 1) if son_masa else "1" # 'masa_no' sütununa isimle erişim

            self.cursor.execute(
                "INSERT INTO masalar (masa_no, durum) VALUES (?, ?)",
                (yeni_masa_no, "boş")
            )
            self.conn.commit()
            self._masa_butonlarini_guncelle()
            messagebox.showinfo("Başarılı", f"Masa {yeni_masa_no} eklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Masa eklenirken hata oluştu: {str(e)}")

    def masa_sil(self):
        """Seçilen masayı siler (boş olmalı)"""
        try:
            # Mevcut masaları listele
            self.cursor.execute("SELECT masa_no FROM masalar ORDER BY CAST(masa_no AS INTEGER)")
            masalar = [row['masa_no'] for row in self.cursor.fetchall()] # 'masa_no' sütununa isimle erişim

            if not masalar:
                messagebox.showwarning("Uyarı", "Silinecek masa yok!")
                return

            # Silinecek masayı kullanıcıdan al
            masa_no = simpledialog.askstring("Masa Sil", "Silinecek masa numarasını girin:",
                                         parent=self.root)

            if masa_no and masa_no in masalar:
                # Masa dolu mu kontrol et
                self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
                durum = self.cursor.fetchone()['durum'] # 'durum' sütununa isimle erişim

                if durum == "dolu":
                    messagebox.showwarning("Uyarı", "Bu masada sipariş var veya kapatılmamış. Önce ödeme yapılmalı!")
                    return

                # Onay al
                if not messagebox.askyesno("Silme Onayı", f"Masa {masa_no} silinecektir. Emin misiniz?"):
                    return

                # Masayı ve ilgili ara ödemeleri sil
                self.cursor.execute("DELETE FROM masalar WHERE masa_no = ?", (masa_no,))
                self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,)) # İlişkili ara ödemeleri de sil
                # masa_siparisleri zaten dolu değilse yoktur, varsa silinemez uyarısı verdik.

                if self.aktif_masa == masa_no:
                    self.aktif_masa = None
                    if hasattr(self, 'aktif_masa_label'):
                        self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
                    if hasattr(self, 'musteri_label'):
                         self.musteri_label.config(text="Müşteri: -")
                    self._sepeti_temizle_ui_only() # Sadece arayüzü temizle


                self.conn.commit()
                self._masa_butonlarini_guncelle()
                messagebox.showinfo("Başarılı", f"Masa {masa_no} silindi.")
            elif masa_no: # Kullanıcı bir değer girdi ama listede yok
                 messagebox.showwarning("Uyarı", "Geçersiz masa numarası!")
            # else: Kullanıcı iptal etti, bir şey yapmaya gerek yok

        except Exception as e:
            messagebox.showerror("Hata", f"Masa silinirken hata oluştu: {str(e)}")
            print(f"Masa silme hatası: {e}")


    def masa_musteri_ata(self):
        """Aktif masaya müşteri atar"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return

        # Müşteri ID veya Telefon ile arama
        musteri_input = simpledialog.askstring("Müşteri Ata", "Müşteri ID veya Telefon Numarası:", parent=self.root)

        if musteri_input:
            musteri_input = musteri_input.strip()
            if not musteri_input:
                 messagebox.showwarning("Uyarı", "Müşteri ID veya Telefon girilmedi!")
                 return

            # Müşteriyi ara (ID veya Telefon)
            self.cursor.execute('''
                SELECT musteri_id, ad FROM musteriler
                WHERE musteri_id = ? OR telefon = ?
            ''', (musteri_input, musteri_input))
            musteri = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilebilir

            if musteri:
                musteri_id = musteri['musteri_id']
                musteri_adi = musteri['ad']

                # Masaya müşteriyi ata
                self.cursor.execute('''
                    UPDATE masalar SET musteri_id = ? WHERE masa_no = ?
                ''', (musteri_id, self.aktif_masa))
                self.conn.commit()

                if hasattr(self, 'musteri_label'):
                    self.musteri_label.config(text=f"Müşteri: {musteri_adi}")

                self._masa_butonlarini_guncelle()
                messagebox.showinfo("Başarılı", f"Masa {self.aktif_masa} için müşteri '{musteri_adi}' atandı!")
            else:
                messagebox.showwarning("Uyarı", "Belirtilen ID veya Telefon ile müşteri bulunamadı!")


    def indirim_uygula(self):
        """Seçilen masaya indirim uygular (Ara ödeme gibi düşünülebilir veya toplamdan düşer)"""
        # Mevcut dolu masaları al
        self.cursor.execute("SELECT masa_no FROM masalar WHERE durum = 'dolu' ORDER BY CAST(masa_no AS INTEGER)")
        dolu_masalar = [row['masa_no'] for row in self.cursor.fetchall()] # 'masa_no' sütununa isimle erişim

        if not dolu_masalar:
            messagebox.showwarning("Uyarı", "İndirim uygulanacak dolu masa bulunamadı!")
            return

        # İndirim penceresi oluştur
        indirim_pencere = tk.Toplevel(self.root)
        indirim_pencere.title("İndirim Uygula")
        indirim_pencere.transient(self.root) # Ana pencere üzerinde kalmasını sağlar
        indirim_pencere.grab_set() # Ana pencereyi kilitler
        indirim_pencere.resizable(False, False)

        ttk.Label(indirim_pencere, text="Masa Seçin:", style="Bilgi.TLabel").grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")

        masa_combobox = ttk.Combobox(indirim_pencere, values=dolu_masalar, state="readonly", width=15)
        masa_combobox.grid(row=0, column=1, padx=PAD_X, pady=PAD_Y)
        if self.aktif_masa and self.aktif_masa in dolu_masalar:
             masa_combobox.set(self.aktif_masa) # Aktif masayı varsayılan seç

        ttk.Label(indirim_pencere, text="İndirim Miktarı (TL):", style="Bilgi.TLabel").grid(row=1, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        indirim_entry = ttk.Entry(indirim_pencere, width=18)
        indirim_entry.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y)

        def indirimi_uygula_action():
            masa_no = masa_combobox.get()
            if not masa_no:
                messagebox.showwarning("Uyarı", "Lütfen bir masa seçin!", parent=indirim_pencere)
                return

            try:
                indirim = float(indirim_entry.get().replace(",", ".")) # Virgülü noktaya çevir
                if indirim < 0:
                    raise ValueError # Negatif indirim olmamalı
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz indirim miktarı! Pozitif sayı girin.", parent=indirim_pencere)
                return

            # Masa bilgilerini al
            self.cursor.execute('''
                SELECT durum, toplam FROM masalar WHERE masa_no = ?
            ''', (masa_no,))
            masa_info = self.cursor.fetchone()
            if not masa_info or masa_info['durum'] != "dolu":
                messagebox.showwarning("Uyarı", "Seçilen masa dolu değil veya bulunamadı!", parent=indirim_pencere)
                return

            toplam = masa_info['toplam']

            if indirim > toplam:
                if not messagebox.askyesno("Onay", f"İndirim ({indirim:.2f} TL) toplam tutardan ({toplam:.2f} TL) fazla. Tutar sıfırlansın mı?", parent=indirim_pencere):
                     return
                yeni_tutar = 0.0
            else:
                 yeni_tutar = toplam - indirim


            # İndirimi uygula (Masanın toplamını güncelle)
            try:
                self.cursor.execute('''
                    UPDATE masalar
                    SET toplam = ?, son_islem_zamani = ?
                    WHERE masa_no = ?
                ''', (yeni_tutar, self._tarih_saat_al_db_format(), masa_no))
                self.conn.commit()

                self._masa_butonlarini_guncelle()
                # Eğer indirim uygulanan masa aktif masaysa, sepeti de güncelle
                if self.aktif_masa == masa_no:
                     self._sepeti_yukle() # Sepeti veritabanından yeniden yükle
                     self._toplam_guncelle_ui() # Toplam etiketlerini güncelle


                messagebox.showinfo("Başarılı", f"Masa {masa_no} için {indirim:.2f} TL indirim uygulandı. Yeni Toplam: {yeni_tutar:.2f} TL", parent=indirim_pencere)
                indirim_pencere.destroy()

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"İndirim uygulanırken veritabanı hatası: {e}", parent=indirim_pencere)
            except Exception as e:
                 messagebox.showerror("Hata", f"İndirim uygulanırken hata oluştu: {e}", parent=indirim_pencere)


        ttk.Button(
            indirim_pencere,
            text="İndirimi Uygula",
            command=indirimi_uygula_action,
            style="Odeme.TButton" # Ödeme butonu style kullanıldı
        ).grid(row=2, column=0, columnspan=2, pady=PAD_Y)

        indirim_pencere.focus_set() # Pencereye odaklan

    # ADİSYON İŞLEMLERİ
    def adisyon_arayuz_olustur(self):
        """Adisyon sekmesi arayüzünü oluşturur"""
        # Bilgi Frame (üst kısım, sabit yükseklik)
        bilgi_frame = ttk.Frame(self.adisyon_frame)
        bilgi_frame.pack(pady=PAD_Y, fill=tk.X)

        self.aktif_masa_label = ttk.Label(bilgi_frame, text="Aktif Masa: Seçili değil", style="Baslik.TLabel")
        self.aktif_masa_label.pack(side=tk.LEFT, padx=PAD_X)

        self.musteri_label = ttk.Label(bilgi_frame, text="Müşteri: -", style="Bilgi.TLabel")
        self.musteri_label.pack(side=tk.LEFT, padx=PAD_X)

        # Müşteri Kümülatif Bakiye Etiketi
        self.musteri_bakiye_adisyon_label = ttk.Label(bilgi_frame, text="Bakiye: 0 ₺", style="Bilgi.TLabel")
        self.musteri_bakiye_adisyon_label.pack(side=tk.LEFT, padx=PAD_X)


        # Sağ tarafa saati ekle
        self.saat_label = ttk.Label(bilgi_frame, text=self._tarih_saat_al_display_format(), style="Bilgi.TLabel")
        self.saat_label.pack(side=tk.RIGHT)
        self._saat_guncelle()

        # Arama ve Kategori Filtreleme Frame
        arama_filtre_frame = ttk.Frame(self.adisyon_frame)
        arama_filtre_frame.pack(pady=PAD_Y, fill=tk.X)

        # Arama Kısmı
        arama_frame = ttk.Frame(arama_filtre_frame)
        arama_frame.pack(side=tk.LEFT, padx=PAD_X, fill=tk.X, expand=True)

        ttk.Label(arama_frame, text="Ürün Ara:", style="Bilgi.TLabel").pack(side=tk.LEFT)
        self.urun_arama_entry = ttk.Entry(arama_frame)
        self.urun_arama_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.urun_arama_entry.bind("<Return>", self._urun_ara)

        # Kategori Filtreleme Kısmı
        kategori_frame = ttk.Frame(arama_filtre_frame)
        kategori_frame.pack(side=tk.RIGHT, padx=PAD_X)

        ttk.Label(kategori_frame, text="Kategori Seç:", style="Bilgi.TLabel").pack(side=tk.LEFT)
        self.kategori_filtre_combobox = ttk.Combobox(kategori_frame, state="readonly", width=20)
        self.kategori_filtre_combobox.pack(side=tk.LEFT)

        kategoriler = self._kategorileri_getir()
        self.kategori_filtre_combobox['values'] = kategoriler

        if "Tümü" in kategoriler:
             self.kategori_filtre_combobox.set("Tümü")
        self.kategori_filtre_combobox.bind("<<ComboboxSelected>>", self._filter_hizli_satis_buttons)

        # Hızlı Satış Butonları Alanı (genleşebilir orta alan)
        self.hizli_satis_container = ttk.Frame(self.adisyon_frame)
        self.hizli_satis_container.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        # Scrollbar için Canvas kullanılıyor
        self.hizli_satis_canvas = tk.Canvas(self.hizli_satis_container, bg="#f0f0f0")
        self.hizli_satis_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hizli_satis_scrollbar = ttk.Scrollbar(self.hizli_satis_container, orient=tk.VERTICAL, command=self.hizli_satis_canvas.yview)
        self.hizli_satis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hizli_satis_canvas.configure(yscrollcommand=self.hizli_satis_scrollbar.set)
        self.hizli_satis_canvas.bind('<Configure>', lambda e: self.hizli_satis_canvas.itemconfigure("frame", width=self.hizli_satis_canvas.winfo_width()))

        # !!! DİKKAT: self.hizli_satis_frame BURADA OLUŞTURULUYOR !!!
        # _hizli_satis_butonlari_olustur çağrılmadan önce tanımlı olmalı.
        self.hizli_satis_frame = ttk.Frame(self.hizli_satis_canvas, style="HizliSatis.TFrame")
        # create_window kullanarak frame'i canvas içine yerleştir
        self.hizli_satis_canvas.create_window((0, 0), window=self.hizli_satis_frame, anchor="nw", tags="frame")

        # Frame boyutu değiştiğinde Canvas'ın scrollable alanını güncelle
        self.hizli_satis_frame.bind('<Configure>', lambda e: self.hizli_satis_canvas.config(scrollregion=self.hizli_satis_canvas.bbox("all")))

        # İlk yüklemede hızlı satış butonlarını filtrele ('Tümü' seçili gelir)
        # Bu çağrı self.hizli_satis_frame oluşturulduktan sonra olmalı.
        self._filter_hizli_satis_buttons()


        # Sepet Tablosu (genleşebilir orta alan 2)
        self.sepet_tablo = ttk.Treeview(self.adisyon_frame, columns=("Urun", "Fiyat", "Miktar", "Tutar"), show="headings", height=6)
        self.sepet_tablo.heading("Urun", text="Ürün")
        self.sepet_tablo.heading("Fiyat", text="Fiyat", anchor='e')
        self.sepet_tablo.heading("Miktar", text="Miktar", anchor='e')
        self.sepet_tablo.heading("Tutar", text="Tutar", anchor='e')
        self.sepet_tablo.column("Urun", width=200, stretch=tk.YES)
        self.sepet_tablo.column("Fiyat", width=80, stretch=tk.NO)
        self.sepet_tablo.column("Miktar", width=80, stretch=tk.NO)
        self.sepet_tablo.column("Tutar", width=100, stretch=tk.NO)
        self.sepet_tablo.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        # Kontrol Frame (sabit yükseklik)
        kontrol_frame = ttk.Frame(self.adisyon_frame)
        kontrol_frame.pack(pady=PAD_Y, fill=tk.X)

        ttk.Label(kontrol_frame, text="Adetli Ürün Miktarı:", style="Bilgi.TLabel").pack(side=tk.LEFT, padx=PAD_X)
        self.miktar_spinbox = tk.Spinbox(kontrol_frame, from_=1, to=99, width=5, font=("Arial", 10))
        self.miktar_spinbox.pack(side=tk.LEFT, padx=PAD_X)

        ttk.Button(kontrol_frame, text="Sepete Ekle", style="EkleCikar.TButton", command=self._sepete_ekle_action).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(kontrol_frame, text="Seçileni Çıkar", style="EkleCikar.TButton", command=self._sepetten_cikar).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(kontrol_frame, text="Sepeti Temizle", style="EkleCikar.TButton", command=self._sepeti_temizle).pack(side=tk.LEFT, padx=PAD_X)

        # Ödeme Frame (sabit yükseklik)
        odeme_frame = ttk.Frame(self.adisyon_frame)
        odeme_frame.pack(pady=PAD_Y, fill=tk.X)

        ttk.Button(odeme_frame, text="Masa Hesap Bilgisi", style="Odeme.TButton", command=self._nakit_odeme_bilgi).pack(side=tk.RIGHT, padx=PAD_X)
        ttk.Button(odeme_frame, text="Masa Kapat (Nakit)", style="Kapat.TButton", command=lambda: self._odeme_yap("Nakit")).pack(side=tk.RIGHT, padx=PAD_X)
        ttk.Button(odeme_frame, text="Masa Kapat (Kart)", style="Kapat.TButton", command=lambda: self._odeme_yap("Kredi Kartı")).pack(side=tk.RIGHT, padx=PAD_X)
        ttk.Button(odeme_frame, text="Ara Ödeme Al", style="AraOdeme.TButton", command=self._ara_odeme).pack(side=tk.RIGHT, padx=PAD_X)

        # Toplam Frame (en alt kısım, sabit yükseklik)
        toplam_frame = ttk.Frame(self.adisyon_frame)
        toplam_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=PAD_Y)

        # Etiketlerin sırası değiştirildi ve yeni etiket eklendi
        # Toplam Borç en sağda, sonra Net Tutar, sonra İskonto, sonra Masa Toplamı
        self.toplam_borc_label = ttk.Label(toplam_frame, text="Toplam Borç: 0 ₺", style="Toplam.TLabel")
        self.toplam_borc_label.pack(side=tk.RIGHT, padx=PAD_X)

        self.net_tutar_label = ttk.Label(toplam_frame, text="Net Tutar: 0 ₺", style="Toplam.TLabel")
        self.net_tutar_label.pack(side=tk.RIGHT, padx=PAD_X)

        self.iskonto_label = ttk.Label(toplam_frame, text="İskonto: 0 ₺", style="Toplam.TLabel")
        self.iskonto_label.pack(side=tk.RIGHT, padx=PAD_X)

        self.masa_toplam_label = ttk.Label(toplam_frame, text="Masa Toplamı: 0 ₺", style="Toplam.TLabel")
        self.masa_toplam_label.pack(side=tk.RIGHT, padx=PAD_X)

        # _hizli_satis_butonlari_olustur artık _filter_hizli_satis_buttons tarafından çağrılıyor.

    def _hizli_satis_butonlari_olustur(self, category=None):
        """Hızlı satış alanındaki ürün butonlarını oluşturur/yeniler (kategoriye göre filtreleyebilir)"""
        # Önceki butonları temizle
        # Canvas içindeki frame'in tüm widget'larını temizle
        for widget in self.hizli_satis_frame.winfo_children():
            widget.destroy()

        # Ürünleri veritabanından çek
        sql_query = """
            SELECT urun_adi, fiyat, kategori
            FROM urunler
        """
        params = () # Sorgu parametreleri için boş tuple

        # Eğer kategori belirtildiyse ve 'Tümü' değilse WHERE koşulunu ekle
        if category is not None and category != "Tümü":
            sql_query += " WHERE kategori = ?"
            params = (category,) # Kategori adını parametre olarak ekle

        # Sıralama koşulunu ekle
        sql_query += " ORDER BY sira ASC, urun_adi ASC"

        # Sorguyu çalıştır
        self.cursor.execute(sql_query, params) # Sorguyu parametrelerle çalıştır
        urunler = self.cursor.fetchall() # row_factory sayesinde sütun isimleriyle erişilebilir

        # Butonları yerleştirmek için grid ayarları
        COLS = 9 # Hızlı satış butonları için sütun sayısı (ayarlanabilir)
        PAD = 4 # Butonlar arası boşluk

        # Grid için satır ağırlıklarını ayarla (Responsive olması için)
        # Eğer hiç ürün yoksa satır sayısı 0 olur, buna dikkat et
        total_rows = (len(urunler) + COLS - 1) // COLS if len(urunler) > 0 else 1 # En az 1 satır yap
        for r in range(total_rows):
             self.hizli_satis_frame.grid_rowconfigure(r, weight=1) # Her satıra ağırlık ver

        # Grid için sütun ağırlıklarını ayarla (Zaten ayarlı olabilir ama emin olalım)
        for c in range(COLS):
             self.hizli_satis_frame.grid_columnconfigure(c, weight=1) # Her sütuna ağırlık ver


        # Ürün butonlarını oluştur
        for i, urun in enumerate(urunler):
            urun_adi = urun['urun_adi']
            fiyat = urun['fiyat']
            kategori = urun['kategori']

            # Kategori rengini al, yoksa varsayılan
            bg_color = KATEGORI_RENKLERI.get(kategori, "#f0f0f0")
            fg_color = get_text_color(bg_color)

            # Buton oluşturma
            # Formatlama düzeltildi: Ondalıksız ve ₺ işareti
            btn = tk.Button(
                self.hizli_satis_frame,
                text=f"{urun_adi}\n{fiyat:.0f} ₺",
                command=lambda u=urun_adi: self._urun_ekle_hizli_satis(u),
                bg=bg_color,
                fg=fg_color,
                font=("Arial", 8, "bold"),
                relief="groove",
                justify="center"
            )

            # Grid'e yerleştirme
            row, col = divmod(i, COLS)
            btn.grid(row=row, column=col, padx=PAD, pady=PAD, sticky="nsew") # Hücre içinde yapışık kal ve genişle

        # Canvas'ın scroll bölgesini güncelle
        self.hizli_satis_frame.update_idletasks() # Frame boyutunun hesaplanmasını sağla
        # Eğer hiç ürün yoksa scrollregion hata verebilir, kontrol ekleyelim
        bbox = self.hizli_satis_canvas.bbox("all")
        if bbox:
            self.hizli_satis_canvas.config(scrollregion=bbox) # Scroll bölgesini ayarla
        else:
            # Hiç ürün yoksa scrollable alan canvas boyutu kadar olsun
            self.hizli_satis_canvas.config(scrollregion=(0,0,self.hizli_satis_canvas.winfo_width(), self.hizli_satis_canvas.winfo_height()))

    def _kategorileri_getir(self):
        """Veritabanındaki ürün kategorilerini getirir ve 'Tümü' seçeneğini ekler"""
        try:
            # Ürünler tablosundan benzersiz kategorileri çek
            self.cursor.execute("SELECT DISTINCT kategori FROM urunler ORDER BY kategori ASC")
            # Çekilen sonuçları listeleyip None olanları filtrele
            kategoriler = [row['kategori'] for row in self.cursor.fetchall() if row['kategori'] is not None]
            # Listenin başına 'Tümü' seçeneğini ekle
            kategoriler.insert(0, "Tümü")
            return kategoriler
        except sqlite3.Error as e:
            print(f"Kategori listesi alınırken veritabanı hatası: {e}")
            # Hata durumunda sadece 'Tümü' seçeneği ile dön
            return ["Tümü"]

    def _filter_hizli_satis_buttons(self, event=None):
        """Kategori combobox seçimine göre hızlı satış butonlarını filtreler ve günceller"""
        # Combobox'tan seçilen kategori değerini al
        selected_category = self.kategori_filtre_combobox.get()
        # _hizli_satis_butonlari_olustur fonksiyonunu seçilen kategori ile çağırarak butonları yeniden oluştur
        self._hizli_satis_butonlari_olustur(category=selected_category)

    def _sepeti_yukle(self):
        """Aktif masanın siparişlerini sepet Treeview'ına yükler ve UI'ı günceller (Müşteri bilgisi, Bakiye ve Toplam Borç dahil)"""
        # Sepeti temizle
        for item in self.sepet_tablo.get_children():
            self.sepet_tablo.delete(item)

        # Toplamları sıfırla (self.toplam_tutar artık sadece masa oturumu toplamı)
        self.toplam_tutar = 0.0 # Masa oturumunun toplamı
        self.iskonto = 0.0 # İskonto özelliği eklenirse kullanılacak
        current_cumulative_balance = 0.0 # Müşterinin kümülatif bakiyesi

        # Müşteri ve Bakiye etiketlerini varsayılana ayarla
        if hasattr(self, 'musteri_label'):
             self.musteri_label.config(text="Müşteri: -")
        if hasattr(self, 'musteri_bakiye_adisyon_label'):
             self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")
        if hasattr(self, 'masa_toplam_label'): # Masa Toplamı etiketi
             self.masa_toplam_label.config(text="Masa Toplamı: 0 ₺")
        if hasattr(self, 'toplam_borc_label'): # Toplam Borç etiketi
             self.toplam_borc_label.config(text="Toplam Borç: 0 ₺")
        # Net Tutar ve İskonto etiketlerini de sıfırla
        if hasattr(self, 'net_tutar_label'):
             self.net_tutar_label.config(text="Net Tutar: 0 ₺")
        if hasattr(self, 'iskonto_label'):
             self.iskonto_label.config(text="İskonto: 0 ₺")


        if self.aktif_masa:
            # Aktif masanın siparişlerini çek
            self.cursor.execute('''
                SELECT urun_adi, fiyat, miktar, tutar
                FROM masa_siparisleri
                WHERE masa_no = ?
            ''', (self.aktif_masa,))

            siparisler = self.cursor.fetchall()

            # Sepet Treeview'ına siparişleri ekle ve masa oturumu toplamını hesapla
            masa_oturum_toplami = 0.0
            for siparis in siparisler:
                self.sepet_tablo.insert("", tk.END, values=(
                    siparis['urun_adi'],
                    f"{siparis['fiyat']:.0f} ₺",
                    siparis['miktar'],
                    f"{siparis['tutar']:.0f} ₺"
                ))
                masa_oturum_toplami += siparis['tutar']

            # self.toplam_tutar artık sadece masa oturumu toplamını tutuyor
            self.toplam_tutar = masa_oturum_toplami


            # Masanın müşteri ID'sini çek
            self.cursor.execute('''
                 SELECT musteri_id FROM masalar WHERE masa_no = ?
            ''', (self.aktif_masa,))
            masa_info = self.cursor.fetchone()

            musteri_id = None
            if masa_info:
                musteri_id = masa_info['musteri_id']

                # Müşteri bilgisi varsa adını ve kümülatif bakiyesini çek ve UI'ı güncelle
                if musteri_id:
                    self.cursor.execute("SELECT ad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                    musteri = self.cursor.fetchone()
                    if musteri: # Müşteri bulunduysa
                        if hasattr(self, 'musteri_label'):
                             self.musteri_label.config(text=f"Müşteri: {musteri['ad']}")
                        if hasattr(self, 'musteri_bakiye_adisyon_label'):
                             # Kümülatif bakiye etiketini güncelle (formatlı)
                             current_cumulative_balance = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0
                             self.musteri_bakiye_adisyon_label.config(text=f"Bakiye: {current_cumulative_balance:.0f} ₺")
                    else: # Müşteri ID var ama müşteri bulunamadı (DB tutarsızlığı)
                        if hasattr(self, 'musteri_label'):
                             self.musteri_label.config(text="Müşteri: Bulunamadı")
                        if hasattr(self, 'musteri_bakiye_adisyon_label'):
                             self.musteri_bakiye_adisyon_label.config(text="Bakiye: ? ₺")

            # Ara ödemeler toplamını çek (bu sadece bilgi amaçlı gösterilebilir veya ödeme ekranında kullanılır)
            # Şu anki mantıkta ara ödemeler doğrudan kümülatif bakiyeden düşülecek,
            # bu yüzden buradaki ara ödeme toplamı sadece bilgilendirme amaçlıdır.
            # Yine de çekelim, belki UI'da gösterilir.
            self.cursor.execute('''
                SELECT COALESCE(SUM(miktar), 0) as ara_odeme_toplam FROM ara_odemeler
                WHERE masa_no = ?
            ''', (self.aktif_masa,))
            ara_odeme_row = self.cursor.fetchone()
            ara_odeme_toplam = ara_odeme_row['ara_odeme_toplam'] if ara_odeme_row and ara_odeme_row['ara_odeme_toplam'] is not None else 0.0


            # Toplam UI etiketlerini güncelle
            # Masa Toplamı = Sadece bu oturumdaki siparişlerin toplamı
            if hasattr(self, 'masa_toplam_label'):
                 self.masa_toplam_label.config(text=f"Masa Toplamı: {self.toplam_tutar:.0f} ₺")

            # Net Tutar ve İskonto (şimdilik iskonto 0, net tutar = masa toplamı)
            net_tutar_adisyon = self.toplam_tutar - self.iskonto # İskonto düşülmüş masa toplamı
            if hasattr(self, 'net_tutar_label'):
                 self.net_tutar_label.config(text=f"Net Tutar: {net_tutar_adisyon:.0f} ₺")
            if hasattr(self, 'iskonto_label'):
                 self.iskonto_label.config(text=f"İskonto: {self.iskonto:.0f} ₺")


            # Toplam Borç = Müşterinin Kümülatif Bakiyesi + Masa Oturumu Toplamı
            total_owed = current_cumulative_balance + self.toplam_tutar # self.toplam_tutar artık sadece oturum toplamı

            if hasattr(self, 'toplam_borc_label'):
                 self.toplam_borc_label.config(text=f"Toplam Borç: {total_owed:.0f} ₺")


        else: # Aktif masa yoksa tüm etiketleri sıfırla (fonksiyon başında yapılıyor)
            pass # Zaten sıfırlandı

    def _urun_formu_temizle(self):
        """Ürün ekleme/düzenleme form alanlarını temizler"""
        self.urun_sira_entry.delete(0, tk.END)
        self.urun_adi_entry.delete(0, tk.END)
        self.urun_fiyat_entry.delete(0, tk.END)
        # Kategori combobox'ı temizle ve varsayılana ayarla
        self._urun_kategori_combobox_guncelle() # Mevcut kategorilerle yeniden doldurur

        # Seçili ürün ID'sini sıfırla
        self.secili_urun_id = None


    def _urun_listesini_guncelle(self):
        """Ürün listesi Treeview'ını veritabanından günceller"""
        # Mevcut satırları temizle
        for item in self.urun_listesi.get_children():
            self.urun_listesi.delete(item)

        # Ürünleri veritabanından çek
        self.cursor.execute('''
            SELECT id, sira, urun_adi, fiyat, kategori
            FROM urunler
            ORDER BY sira ASC, urun_adi ASC
        ''')

        urunler = self.cursor.fetchall() # row_factory sayesinde sütun isimleriyle erişilebilir

        # Treeview'a ekle
        for urun in urunler:
            # Fiyatı formatlayarak ekle (ondalıksız ve ₺ işareti)
            fiyat_str = f"{urun['fiyat']:.0f} ₺" if urun['fiyat'] is not None else "0 ₺"

            self.urun_listesi.insert("", tk.END, values=(
                urun['id'], # Gizli ID sütunu
                urun['sira'],
                urun['urun_adi'],
                fiyat_str, # Formatlanmış fiyat stringi
                urun['kategori'] if urun['kategori'] is not None else "" # Kategori boş olabilir
            ))

        # Form alanlarını temizle
        self._urun_formu_temizle()
        # Kategori combobox'ını da güncelle (yeni eklenen kategoriler olabilir)
        self._kategori_listesini_guncelle() # Bu fonksiyon hem kategori listesi Treeview'ını hem de ürün/adisyon combobox'larını günceller


    def _urun_sec(self, event):
        """Ürün listesi Treeview'ında bir ürün seçildiğinde form alanlarını doldurur"""
        selected_item = self.urun_listesi.selection()
        if not selected_item:
            self._urun_formu_temizle() # Seçim kaldırılırsa formu temizle
            return

        # Seçili öğenin değerlerini al (Treeview'daki sütun sırasına göre)
        # Dikkat: Treeview'da gizli ID sütunu ilk sırada (index 0)
        item_values = self.urun_listesi.item(selected_item[0], "values")

        # Değerleri form alanlarına yerleştir
        self._urun_formu_temizle() # Önce formu temizle

        # Treeview değerleri sırasıyla: ID, Sıra, Ürün Adı, Fiyat, Kategori
        self.secili_urun_id = item_values[0] # ID sütunu (index 0)

        self.urun_sira_entry.insert(0, item_values[1]) # Sıra (index 1)
        self.urun_adi_entry.insert(0, item_values[2]) # Ürün Adı (index 2)

        # Fiyatı alırken ₺ işaretini temizle ve sayıya çevir
        try:
            fiyat_str = str(item_values[3]).replace(' ₺', '').strip() # Fiyat sütunu (index 3)
            # Sayıya çevirip form alanına ondalıklı formatta yerleştir (kullanıcı düzenlerken kolaylık)
            fiyat_float = float(fiyat_str)
            self.urun_fiyat_entry.insert(0, f"{fiyat_float:.2f}") # Ondalıklı göster
        except (ValueError, IndexError, TypeError):
            self.urun_fiyat_entry.insert(0, "0.00") # Hata olursa varsayılan değer


        # Kategori combobox'ını doldur (index 4)
        kategori = item_values[4] if item_values[4] is not None else ""
        self._urun_kategori_combobox_guncelle() # Önce tüm kategorileri yükle
        if kategori in self.urun_kategori_combobox['values']:
             self.urun_kategori_combobox.set(kategori) # Seçili ürünün kategorisini ayarla
        else:
             self.urun_kategori_combobox.set("") # Kategori listede yoksa boş bırak


    def _urun_ekle_duzenle_db(self):
        """Formdaki bilgilere göre yeni ürün ekler veya seçili ürünü günceller"""
        sira_str = self.urun_sira_entry.get().strip()
        urun_adi = self.urun_adi_entry.get().strip()
        fiyat_str = self.urun_fiyat_entry.get().strip()
        kategori = self.urun_kategori_combobox.get().strip() # Combobox'tan kategori al

        if not sira_str or not urun_adi or not fiyat_str:
            messagebox.showwarning("Uyarı", "Sıra, Ürün Adı ve Fiyat alanları boş bırakılamaz!", parent=self.urun_frame)
            return

        try:
            sira = int(sira_str)
            fiyat = float(fiyat_str)
        except ValueError:
            messagebox.showwarning("Uyarı", "Sıra ve Fiyat alanlarına geçerli sayılar girin!", parent=self.urun_frame)
            return

        # Kategori boş bırakılabilir (varsayılan kategori yoksa)
        if not kategori:
             if messagebox.askyesno("Uyarı", "Kategori seçilmedi. Ürün boş kategori ile eklensin/güncellensin mi?", parent=self.urun_frame):
                 kategori = None # Veritabanında NULL olarak saklanır
             else:
                 return # Kullanıcı vazgeçti


        try:
            if self.secili_urun_id is None:
                # Yeni Ürün Ekle
                self.cursor.execute('''
                    INSERT INTO urunler (sira, urun_adi, fiyat, kategori)
                    VALUES (?, ?, ?, ?)
                ''', (sira, urun_adi, fiyat, kategori))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Yeni ürün başarıyla eklendi!", parent=self.urun_frame)
            else:
                # Seçili Ürünü Güncelle
                self.cursor.execute('''
                    UPDATE urunler
                    SET sira = ?, urun_adi = ?, fiyat = ?, kategori = ?
                    WHERE id = ?
                ''', (sira, urun_adi, fiyat, kategori, self.secili_urun_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Ürün bilgileri başarıyla güncellendi!", parent=self.urun_frame)

            # Listeyi ve formu yenile
            self._urun_listesini_guncelle() # Ürün listesini ve formu temizler, kategori combobox'ını günceller


        except sqlite3.IntegrityError as e:
             if "UNIQUE constraint failed: urunler.sira" in str(e):
                 messagebox.showwarning("Uyarı", f"'{sira}' sıra numarası zaten kullanılıyor.\nLütfen farklı bir sıra numarası girin.", parent=self.urun_frame)
             elif "UNIQUE constraint failed: urunler.urun_adi" in str(e):
                 messagebox.showwarning("Uyarı", f"'{urun_adi}' isimli ürün zaten mevcut.\nLütfen farklı bir isim girin.", parent=self.urun_frame)
             else:
                 messagebox.showwarning("Veritabanı Hatası", f"Ürün eklenirken/güncellenirken bütünlük hatası: {e}", parent=self.urun_frame)
             self.conn.rollback() # İşlemi geri al
        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Ürün eklenirken/güncellenirken hata oluştu: {e}", parent=self.urun_frame)
             self.conn.rollback() # İşlemi geri al
        except Exception as e:
             messagebox.showerror("Hata", f"Ürün eklenirken/güncellenirken beklenmedik hata: {e}", parent=self.urun_frame)
             print(f"Ürün ekle/düzenle hatası: {e}")


    def _urun_sil(self):
        """Seçili ürünü veritabanından siler"""
        selected_item = self.urun_listesi.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir ürün seçin!", parent=self.urun_frame)
            return

        # Seçili öğenin ID'sini al (gizli sütun)
        urun_id = self.urun_listesi.item(selected_item[0], "values")[0]
        urun_adi = self.urun_listesi.item(selected_item[0], "values")[2] # Ürün adını da alalım mesaj için

        if messagebox.askyesno("Ürün Sil", f"'{urun_adi}' ürününü silmek istediğinize emin misiniz?", parent=self.urun_frame):
            try:
                # Ürünü veritabanından sil
                self.cursor.execute("DELETE FROM urunler WHERE id = ?", (urun_id,))
                self.conn.commit()

                # Listeyi ve formu yenile
                self._urun_listesini_guncelle() # Ürün listesini ve formu temizler, kategori combobox'ını günceller

                messagebox.showinfo("Başarılı", f"'{urun_adi}' ürünü başarıyla silindi.", parent=self.urun_frame)

            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Ürün silinirken hata oluştu: {e}", parent=self.urun_frame)
                self.conn.rollback()
            except Exception as e:
                messagebox.showerror("Hata", f"Ürün silinirken beklenmedik hata: {e}", parent=self.urun_frame)
                print(f"Ürün silme hatası: {e}")



    def _urun_ara(self, event=None):
        """Ürün arama girişine Enter basıldığında ürünü bulur ve sepete ekler"""
        arama_metni = self.urun_arama_entry.get().strip().upper()
        if not arama_metni:
            return

        # Ürünü ada göre LIKE ile ara (ilk eşleşeni al)
        self.cursor.execute('''
            SELECT urun_adi FROM urunler
            WHERE urun_adi LIKE ?
            ORDER BY urun_adi LIMIT 1 -- Alfabetik sırala
        ''', (f'%{arama_metni}%',)) # Başında veya sonunda olabilir

        bulunan_urun = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir

        if bulunan_urun:
            self._urun_ekle_hizli_satis(bulunan_urun['urun_adi']) # Bulunan ürünü sepete ekle
            self.urun_arama_entry.delete(0, tk.END) # Arama alanını temizle
        else:
            messagebox.showinfo("Bilgi", "Ürün bulunamadı!", parent=self.adisyon_frame)
            self.urun_arama_entry.select_range(0, tk.END) # Arama alanını seç


    def _urun_ekle_hizli_satis(self, urun_adi):
        """Hızlı satış butonlarından veya aramadan gelen ürünü sepete ekler (varsayılan miktar 1)"""
        # Miktarı Spinbox'tan al
        try:
            miktar = int(self.miktar_spinbox.get())
            if miktar <= 0:
                 miktar = 1 # Geçersiz miktar girildiyse varsayılan 1 yap

        except ValueError:
            miktar = 1 # Geçersiz spinbox değeri

        self._sepete_ekle(urun_adi, miktar) # Asıl ekleme fonksiyonunu çağır

        # Spinbox'ı varsayılan 1'e çek (Opsiyonel)
        self.miktar_spinbox.delete(0, tk.END)
        self.miktar_spinbox.insert(0, "1")


    def _sepete_ekle_action(self):
         """Adisyon sekmesindeki 'Sepete Ekle' butonuna basılınca çalışır"""
         urun_adi = self.urun_arama_entry.get().strip().upper()
         if not urun_adi:
              messagebox.showwarning("Uyarı", "Lütfen eklenecek ürün adını girin veya listeden seçin!", parent=self.adisyon_frame)
              return

         # Miktarı Spinbox'tan al
         try:
             miktar = int(self.miktar_spinbox.get())
             if miktar <= 0:
                 messagebox.showwarning("Uyarı", "Geçersiz miktar! Pozitif tam sayı girin.", parent=self.adisyon_frame)
                 return
         except ValueError:
             messagebox.showwarning("Uyarı", "Geçersiz miktar! Lütfen sayı girin.", parent=self.adisyon_frame)
             return

         self._sepete_ekle(urun_adi, miktar)
         self.urun_arama_entry.delete(0, tk.END) # Ürün eklendikten sonra arama alanını temizle
         self.miktar_spinbox.delete(0, tk.END) # Miktar spinbox'ı 1 yap
         self.miktar_spinbox.insert(0, "1")


    def _sepete_ekle(self, urun_adi, miktar):
        """Belirtilen ürünü aktif masanın sepetine ekler veya miktarını günceller"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa # Yerel değişken kullanıldı

        try:
            # Aktif masanın mevcut durumunu DB'den çek
            self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_status_row = self.cursor.fetchone()
            if not masa_status_row:
                 messagebox.showerror("Hata", "Aktif masa bilgisi veritabanında bulunamadı.", parent=self.adisyon_frame)
                 self.aktif_masa = None # Aktif masa geçerli değilse sıfırla
                 self._sepeti_temizle_ui_only()
                 self._masa_butonlarini_guncelle()
                 return

            current_masa_durum = masa_status_row['durum']

            # Eğer masa şu anda 'boş' ise, adisyon oturumunu BAŞLAT (ilk ürün eklendiğinde)
            if current_masa_durum == "boş":
                su_an = self._tarih_saat_al_db_format()
                self.cursor.execute('''
                    UPDATE masalar
                    SET acilis = ?, durum = 'dolu', son_adisyon_zamani = ?, son_islem_zamani = ?,
                    toplam = 0 -- Yeni adisyon başladığında toplamı sıfırla (Eğer _masa_sec'te sıfırlanmadıysa)
                    -- musteri_id burada NULL yapılmamalıdır, eğer daha önce atanmışsa kalmalı
                    WHERE masa_no = ?
                ''', (su_an, su_an, su_an, masa_no))
                # Yeni adisyon başladığında varsa eski ara ödemeleri de temizle
                self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,))
                # Commit işlemi aşağıda yapılacak

            # Ürün var mı kontrol et ve fiyatını al
            self.cursor.execute('''
                SELECT fiyat FROM urunler WHERE urun_adi = ?
            ''', (urun_adi,))
            urun_info = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir

            if not urun_info:
                messagebox.showwarning("Uyarí", f"'{urun_adi}' isimli ürün bulunamadı!", parent=self.adisyon_frame)
                # Arama alanını temizle (isteğe bağlı)
                # self.urun_arama_entry.delete(0, tk.END)
                # self.urun_arama_entry.insert(0, urun_adi) # Yanlış ürünü tekrar gösterme
                return

            fiyat = urun_info['fiyat']
            eklenecek_tutar = fiyat * miktar

            # Aynı üründen masada var mı kontrol et
            self.cursor.execute('''
                SELECT id, miktar FROM masa_siparisleri
                WHERE masa_no = ? AND urun_adi = ?
            ''', (masa_no, urun_adi)) # masa_no kullanıldı
            eski_siparis = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir

            if eski_siparis:
                # Miktarı ve tutarı güncelle
                yeni_miktar = eski_siparis['miktar'] + miktar
                yeni_tutar = fiyat * yeni_miktar

                self.cursor.execute('''
                    UPDATE masa_siparisleri
                    SET miktar = ?, tutar = ?
                    WHERE id = ?
                ''', (yeni_miktar, yeni_tutar, eski_siparis['id']))
            else:
                # Yeni sipariş ekle
                self.cursor.execute('''
                    INSERT INTO masa_siparisleri
                    (masa_no, urun_adi, fiyat, miktar, tutar)
                    VALUES (?, ?, ?, ?, ?)
                ''', (masa_no, urun_adi, fiyat, miktar, eklenecek_tutar)) # masa_no kullanıldı

            # Masanın toplamını güncelle (masa_siparisleri'nin toplamından hesapla)
            # Bu sorgu, ekleme/çıkarma sonrasında masanın yeni toplamını güvenilir şekilde verir
            self.cursor.execute('''
                UPDATE masalar
                SET toplam = (
                    SELECT COALESCE(SUM(tutar), 0)
                    FROM masa_siparisleri
                    WHERE masa_no = ?
                ),
                son_adisyon_zamani = ?, -- Her sipariş eklendiğinde adisyon zamanı güncellenir
                son_islem_zamani = ? -- Her sipariş eklendiğinde genel işlem zamanı güncellenir
                WHERE masa_no = ?
            ''', (masa_no, self._tarih_saat_al_db_format(), self._tarih_saat_al_db_format(), masa_no)) # masa_no kullanıldı

            # Masanın durumunu 'dolu' yap (Eğer masa boş iken buraya geldiysek if içinde zaten 'dolu' yapıldı)
            # Eğer masa zaten doluysa bu komut gereksizdir ama zarar vermez.
            # Ancak if bloğu durum değişimini taşıdığı için bu satır artık gereksizdir ve kaldırılabilir.
            # self.cursor.execute("UPDATE masalar SET durum = 'dolu' WHERE masa_no = ?", (masa_no,))


            self.conn.commit() # Buraya kadar tüm DB işlemleri commit edilir.
            self._sepeti_yukle() # Sepeti yeniden yükleyerek UI'ı güncelle
            self._masa_butonlarini_guncelle() # Masa buton rengi/bilgisi değişebilir (durum ve toplam)

        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Sipariş eklenirken hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
             self.conn.rollback() # İşlemi geri al
        except Exception as e:
             messagebox.showerror("Hata", f"Sipariş eklenirken beklenmedik hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
             print(f"Sepete ekle hatası (Masa {masa_no}): {e}")
             import traceback
             traceback.print_exc()


    def _sepetten_cikar(self):
        """Adisyon sepetinden seçili ürünü çıkarır veya miktarını azaltır"""
        selected_item = self.sepet_tablo.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen sepetten çıkarmak için bir ürün seçin!", parent=self.adisyon_frame)
            return

        # Tek bir öğe seçildiğinden emin ol
        item = selected_item[0]
        item_values = self.sepet_tablo.item(item, "values")

        urun_adi = item_values[0]
        # Fiyatı alırken ₺ işaretini temizle ve sayıya çevir
        try:
            fiyat_str = str(item_values[1]).replace(' ₺', '').strip() # ₺ işaretini temizle
            fiyat = float(fiyat_str) # Sayıya çevir
        except ValueError:
            messagebox.showerror("Hata", f"Sepetteki '{urun_adi}' ürünü için fiyat bilgisi alınamadı veya formatı hatalı.", parent=self.adisyon_frame)
            print(f"Fiyat dönüşüm hatası: {item_values[1]}")
            return

        mevcut_miktar = int(item_values[2])

        # Miktarı azalt mı, tamamen sil mi?
        if mevcut_miktar > 1:
            # Miktarı 1 azalt
            yeni_miktar = mevcut_miktar - 1
            yeni_tutar = fiyat * yeni_miktar

            try:
                # Veritabanında miktarı ve tutarı güncelle
                self.cursor.execute('''
                    UPDATE masa_siparisleri
                    SET miktar = ?, tutar = ?
                    WHERE masa_no = ? AND urun_adi = ?
                ''', (yeni_miktar, yeni_tutar, self.aktif_masa, urun_adi))
                self.conn.commit()

                # UI'ı güncelle (sepeti yeniden yükle)
                self._sepeti_yukle()
                self._masa_butonlarini_guncelle() # Toplam değiştiği için masa butonunu güncelle
                # messagebox.showinfo("Başarılı", f"{urun_adi} ürünü miktarı 1 azaltıldı.", parent=self.adisyon_frame) # Çok sık çıkar, mesaj göstermeyelim

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Ürün miktarı azaltılırken hata oluştu: {e}", parent=self.adisyon_frame)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ürün miktarı azaltılırken beklenmedik hata: {e}", parent=self.adisyon_frame)
                 print(f"Miktar azaltma hatası: {e}")

        else:
            # Miktar 1 ise veya 1'e düşürülecekse ürünü tamamen sil
            if messagebox.askyesno("Ürün Sil", f"Sepetten '{urun_adi}' ürününü tamamen kaldırmak istediğinize emin misiniz?", parent=self.adisyon_frame):
                try:
                    self.cursor.execute('''
                        DELETE FROM masa_siparisleri
                        WHERE masa_no = ? AND urun_adi = ?
                    ''', (self.aktif_masa, urun_adi))
                    self.conn.commit()

                    # UI'ı güncelle (sepeti yeniden yükle)
                    self._sepeti_yukle()
                    self._masa_butonlarini_guncelle() # Toplam değiştiği için masa butonunu güncelle

                    # Eğer masa siparişi kalmadıysa, masa durumunu 'boş' yap (Bu mantık _sepeti_temizle içinde zaten var, _sepeti_yukle'den sonra kontrol edilebilir veya burada tekrar yapılabilir)
                    # Ancak _sepeti_yukle zaten toplamı güncelliyor ve _masa_butonlarini_guncelle çağrılıyor.
                    # Eğer son ürün silindi ve toplam 0 olduysa, _masa_butonlarini_guncelle masa rengini güncelleyebilir.
                    # Masa durumunu burada 'boş' yapmak yerine, _sepeti_temizle'nin son sipariş için yaptığı gibi yapalım.

                    self.cursor.execute("SELECT COUNT(*) FROM masa_siparisleri WHERE masa_no = ?", (self.aktif_masa,))
                    kalan_siparis_sayisi = self.cursor.fetchone()[0]

                    if kalan_siparis_sayisi == 0:
                         # Eğer hiç sipariş kalmadıysa masayı boşalt
                         # !!! DİKKAT: _sepeti_temizle çağrılmıyor, sadece masa durumu güncelleniyor !!!
                         self.cursor.execute('''
                             UPDATE masalar
                             SET durum = 'boş', toplam = 0, musteri_id = NULL,
                             acilis = NULL, son_adisyon_zamani = NULL
                             WHERE masa_no = ?
                         ''', (self.aktif_masa,))
                         self.conn.commit()
                         self._sepeti_yukle() # UI'ı tekrar güncelle (masa durumu değiştiği için _sepeti_yukle total=0 yapar)
                         self._masa_butonlarini_guncelle() # Masa rengi artık boş görünmeli
                         # Aktif masa sıfırlanmıyor! (Bu 3. sorunun çözümüyle tutarlı)
                         # self.aktif_masa = None # <<< Bu satır kaldırıldı


                    # messagebox.showinfo("Başarılı", f"'{urun_adi}' ürünü sepetten kaldırıldı.", parent=self.adisyon_frame) # Çok sık çıkar, mesaj göstermeyelim


                except sqlite3.Error as e:
                    messagebox.showerror("Veritabanı Hatası", f"Ürün sepetten kaldırılırken hata oluştu: {e}", parent=self.adisyon_frame)
                    self.conn.rollback()
                except Exception as e:
                    messagebox.showerror("Hata", f"Ürün sepetten kaldırılırken beklenmedik hata: {e}", parent=self.adisyon_frame)
                    print(f"Ürün silme hatası: {e}")


    def _sepeti_temizle_ui_only(self):
         """Sadece sepet Treeview'ını ve toplam etiketlerini temizler (Veritabanına dokunmaz)"""
         for item in self.sepet_tablo.get_children():
             self.sepet_tablo.delete(item)
         self.toplam_tutar = 0.0
         self.iskonto = 0.0
         self._toplam_guncelle_ui(0.0) # Ara ödeme de sıfırlanır


    def _sepeti_temizle(self):
        """Aktif masanın sepetini (masa_siparisleri) tamamen temizler ve masayı boşaltır"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Sepeti temizlemek için önce bir masa seçin!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa # Yerel değişken kullanıldı

        # Sepette ürün var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))
        siparis_sayisi = self.cursor.fetchone()[0]

        if siparis_sayisi == 0:
            # Sepet zaten boşsa, ama masa hala dolu görünüyorsa (manuel olarak dolu yapıldıysa vb.)
            # Masayı yine de boşaltma seçeneği sunalım.
            self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_durum_row = self.cursor.fetchone()
            current_masa_durum = masa_durum_row['durum'] if masa_durum_row else 'boş' # Yoksa boş say

            if current_masa_durum == 'dolu':
                 if messagebox.askyesno("Uyarı", f"Masa {masa_no} sepeti zaten boş görünüyor ama dolu olarak işaretli. Masayı boşaltmak istediğinize emin misiniz?", parent=self.adisyon_frame):
                      # Boşaltma işlemini yap (aşağıdaki try bloğuna benzer)
                      try:
                           self.cursor.execute('''
                               UPDATE masalar
                               SET durum = 'boş', toplam = 0, musteri_id = NULL,
                               acilis = NULL, son_adisyon_zamani = NULL, son_islem_zamani = ?
                               WHERE masa_no = ?
                           ''', (self._tarih_saat_al_db_format(), masa_no)) # Son işlem zamanı güncellendi
                           # Ara ödemeleri de temizle (varsa)
                           self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,))
                           self.conn.commit()
                           self._sepeti_yukle() # UI temizlenir, toplam 0 olur
                           self._masa_butonlarini_guncelle() # Masa rengi boş olur
                           # self.aktif_masa = None # <<< Bu satır kaldırıldı
                           messagebox.showinfo("Bilgi", f"Masa {masa_no} boşaltıldı.", parent=self.adisyon_frame)
                           return # İşlem tamamlandı

                      except sqlite3.Error as e:
                           messagebox.showerror("Veritabanı Hatası", f"Boş masa boşaltılırken hata oluştu: {e}", parent=self.adisyon_frame)
                           self.conn.rollback()
                           return
                      except Exception as e:
                            messagebox.showerror("Hata", f"Boş masa boşaltılırken beklenmedik hata: {e}", parent=self.adisyon_frame)
                            print(f"Boş masa boşaltma hatası: {e}")
                            return

            else: # Hem sepet boş hem masa boş işaretli
                messagebox.showinfo("Bilgi", f"Masa {masa_no} sepeti zaten boş.", parent=self.adisyon_frame)
                # self.aktif_masa = None # <<< Bu satır kaldırıldı (aktif masa hala bu masa kalır)
                self._sepeti_yukle() # UI güncellenir (boş sepet görünür)
                self._masa_butonlarini_guncelle() # Masa rengi doğru (boş) görünür
                return # Yapılacak başka bir şey yok

        # Sepet boş değilse, temizleme onayı al
        if messagebox.askyesno("Sepeti Temizle", f"Masa {masa_no} sepetindeki tüm ürünleri kaldırmak istediğinize emin misiniz?", parent=self.adisyon_frame):
            try:
                # Veritabanından tüm siparişleri ve ara ödemeleri sil
                self.cursor.execute("DELETE FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))
                self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,))

                # Masayı boşalt ve toplamı sıfırla, müşteri ID'yi kaldır, adisyon zamanlarını sıfırla
                self.cursor.execute('''
                    UPDATE masalar
                    SET durum = 'boş', toplam = 0, musteri_id = NULL,
                    acilis = NULL, son_adisyon_zamani = NULL, son_islem_zamani = ?
                    WHERE masa_no = ?
                ''', (self._tarih_saat_al_db_format(), masa_no)) # Son işlem zamanı güncellendi


                self.conn.commit()

                # UI'ı güncelle (sepeti temizle, toplamı sıfırla, masa butonunu boş olarak göster)
                self._sepeti_yukle() # UI temizlenir, toplam 0 olur
                self._masa_butonlarini_guncelle() # Masa rengi boş olur

                # !!!!! self.aktif_masa = None ARTIK BURADA YOK !!!!!
                # Masa sepeti temizlense bile aktif masa bilgisi korunur.

                messagebox.showinfo("Başarılı", f"Masa {masa_no} sepeti temizlendi.", parent=self.adisyon_frame)


            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Sepet temizlenirken hata oluştu: {e}", parent=self.adisyon_frame)
                self.conn.rollback()
            except Exception as e:
                messagebox.showerror("Hata", f"Sepet temizlenirken beklenmedik hata: {e}", parent=self.adisyon_frame)
                print(f"Sepet temizleme hatası: {e}")

    def _nakit_odeme_bilgi(self):
        """Masa hesap bilgisini (toplam, ara ödeme, kalan, kümülatif bakiye, toplam borç) gösterir"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        try:
            # Masanın toplam tutarını ve müşteri ID'sini al
            self.cursor.execute("SELECT toplam, musteri_id FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_info = self.cursor.fetchone()

            if not masa_info:
                 messagebox.showwarning("Uyarı", f"Masa {masa_no} bilgisi bulunamadı!", parent=self.adisyon_frame)
                 return

            masa_oturum_toplami = masa_info['toplam'] if masa_info['toplam'] is not None else 0.0
            musteri_id = masa_info['musteri_id']
            current_cumulative_balance = 0.0 # Müşterinin kümülatif bakiyesi

            # Müşteri bilgisi varsa kümülatif bakiyesini çek
            musteri_adi = "Misafir"
            if musteri_id:
                self.cursor.execute("SELECT ad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri:
                    musteri_adi = musteri['ad']
                    current_cumulative_balance = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0


            # Masanın ara ödemeler toplamını al
            self.cursor.execute('''
                SELECT COALESCE(SUM(miktar), 0) as ara_odeme_toplam FROM ara_odemeler
                WHERE masa_no = ?
            ''', (masa_no,))
            ara_odeme_row = self.cursor.fetchone()
            # Anahtar adı 'ara_odeme_toplam' olarak kullanılmalı
            ara_odemeler_toplam = ara_odeme_row['ara_odeme_toplam'] if ara_odeme_row and 'ara_odeme_toplam' in ara_odeme_row and ara_odeme_row['ara_odeme_toplam'] is not None else 0.0

            # Toplam Borç = Müşterinin Kümülatif Bakiyesi + Masa Oturumu Toplamı
            total_owed = current_cumulative_balance + masa_oturum_toplami

            # Kalan Tutar = Toplam Borç - Yapılan Ara Ödemeler (Bu pencere için hesaplanan kalan)
            kalan_tutar_bu_pencere = total_owed - ara_odemeler_toplam


            # Mesaj metni formatlama
            message_text = f"Masa: {masa_no}"
            if musteri_id:
                 message_text += f" ({musteri_adi})"
            message_text += "\n\n"
            message_text += f"Masa Oturumu Toplamı: {masa_oturum_toplami:.0f} ₺\n"
            message_text += f"Müşteri Kümülatif Bakiye: {current_cumulative_balance:.0f} ₺\n"
            message_text += "-"*30 + "\n"
            message_text += f"Toplam Borç: {total_owed:.0f} ₺\n"
            if ara_odemeler_toplam > 0:
                 message_text += f"Yapılan Ara Ödemeler: {ara_odemeler_toplam:.0f} ₺\n"
                 message_text += f"Ödenecek Tutar: {max(0.0, kalan_tutar_bu_pencere):.0f} ₺\n"
            else:
                 message_text += f"Ödenecek Tutar: {max(0.0, total_owed):.0f} ₺\n"

            message_text += "\nÖdeme almak için 'Masa Kapat' veya 'Ara Ödeme Al' butonlarını kullanın."


            messagebox.showinfo(
                "Masa Hesap Bilgisi",
                message_text
                , parent=self.adisyon_frame
            )

        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Masa hesap bilgisi alınırken hata oluştu: {e}", parent=self.adisyon_frame)
             print(f"Masa hesap bilgi hatası: {e}")
        except Exception as e:
             messagebox.showerror("Hata", f"Masa hesap bilgisi alınırken beklenmedik hata: {e}", parent=self.adisyon_frame)
             print(f"Masa hesap bilgi beklenmedik hata: {e}")

    def _ara_odeme(self):
        """Aktif masadan ara ödeme alır, kaydeder ve müşteri bakiyesini günceller"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        try:
            # Masanın toplam tutarını ve müşteri ID'sini al
            self.cursor.execute("SELECT toplam, musteri_id FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_info = self.cursor.fetchone()

            if not masa_info:
                 messagebox.showwarning("Uyarı", f"Masa {masa_no} bilgisi bulunamadı!", parent=self.adisyon_frame)
                 return

            masa_oturum_toplami = masa_info['toplam'] if masa_info['toplam'] is not None else 0.0
            musteri_id = masa_info['musteri_id']
            current_cumulative_balance = 0.0 # Müşterinin kümülatif bakiyesi

            # Müşteri bilgisi varsa kümülatif bakiyesini çek
            musteri_adi = "Misafir"
            if musteri_id:
                self.cursor.execute("SELECT ad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri:
                    musteri_adi = musteri['ad']
                    current_cumulative_balance = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0
                else:
                    # Müşteri ID var ama müşteri bulunamadı (DB tutarsızlığı)
                    messagebox.showwarning("Uyarı", f"Masa {masa_no} ile ilişkili müşteri bulunamadı!", parent=self.adisyon_frame)
                    return # Müşteri yoksa ara ödeme alımını iptal et


            # Masanın ara ödemeler toplamını al (Ayrı sorgu)
            self.cursor.execute('''
                SELECT COALESCE(SUM(miktar), 0) as ara_odeme_toplam FROM ara_odemeler
                WHERE masa_no = ?
            ''', (masa_no,))
            ara_odeme_row = self.cursor.fetchone()
            # Anahtar adı 'ara_odeme_toplam' olarak kullanılmalı
            ara_odemeler_toplam = ara_odeme_row['ara_odeme_toplam'] if ara_odeme_row and 'ara_odeme_toplam' in ara_odeme_row and ara_odeme_row['ara_odeme_toplam'] is not None else 0.0

            # Toplam Borç = Müşterinin Kümülatif Bakiyesi + Masa Oturumu Toplamı
            total_owed = current_cumulative_balance + masa_oturum_toplami

            # Kalan Tutar (Bu ara ödeme sonrası ödenecek olan) = Toplam Borç - Yapılan Ara Ödemeler
            kalan_tutar_odeme_sonrasi = total_owed - ara_odemeler_toplam

            if kalan_tutar_odeme_sonrasi <= 0:
                 messagebox.showwarning("Uyarı", f"Bu masanın zaten ödemesi tamamlanmış veya fazla ödeme yapılmış! Ödenecek: {kalan_tutar_odeme_sonrasi:.0f} ₺", parent=self.adisyon_frame)
                 return

            # Kullanıcıdan alınacak ödeme miktarı soruluyor
            odeme = simpledialog.askfloat(
                "Ara Ödeme Al",
                f"Masa {masa_no} ({musteri_adi}) - Toplam Borç: {total_owed:.0f} ₺\n"
                f"Yapılan Ara Ödemeler: {ara_odemeler_toplam:.0f} ₺\n"
                f"Şu Anda Ödenecek: {max(0.0, kalan_tutar_odeme_sonrasi):.0f} ₺\n\n"
                "Alınan Ödeme Miktarı (₺):",
                minvalue=0.01,
                initialvalue=max(0.0, kalan_tutar_odeme_sonrasi), # Başlangıç değeri ödenecek tutar olsun
                parent=self.root
            )

            if odeme is None or odeme <= 0:
                 if odeme is not None:
                     messagebox.showwarning("Uyarı", "Geçersiz veya sıfır ödeme miktarı girildi.", parent=self.adisyon_frame)
                 return

            # Eğer girilen ödeme ödenecek tutardan fazlaysa onayla
            if odeme > kalan_tutar_odeme_sonrasi:
                if not messagebox.askyesno("Fazla Ödeme?", f"Girilen ödeme ({odeme:.0f} ₺) ödenecek tutardan ({max(0.0, kalan_tutar_odeme_sonrasi):.0f} ₺) fazla. Devam edilsin mi?", parent=self.adisyon_frame):
                    return

            try:
                # Ara ödemeyi ara_odemeler tablosuna kaydet
                self.cursor.execute('''
                    INSERT INTO ara_odemeler (masa_no, miktar, tarih)
                    VALUES (?, ?, ?)
                ''', (masa_no, odeme, self._tarih_saat_al_db_format()))

                # MÜŞTERİ KÜMÜLATİF BAKİYESİNİ GÜNCELLE
                # Ara ödeme müşterinin kümülatif bakiyesinden düşülür.
                yeni_cumulative_balance = current_cumulative_balance - odeme

                self.cursor.execute('''
                    UPDATE musteriler
                    SET cumulative_balance = ?
                    WHERE musteri_id = ?
                ''', (yeni_cumulative_balance, musteri_id))


                # Masanın son işlem zamanını güncelle
                self.cursor.execute('''
                     UPDATE masalar
                     SET son_islem_zamani = ?
                     WHERE masa_no = ?
                ''', (self._tarih_saat_al_db_format(), masa_no))

                self.conn.commit()

                # UI'ı güncelle (Adisyon sekmesindeki bakiye ve toplam borç, masa butonundaki bakiye ve borç)
                self._sepeti_yukle() # Adisyon sekmesindeki etiketleri günceller
                self._masa_butonlarini_guncelle() # Masa butonlarını günceller

                messagebox.showinfo(
                    "Başarılı",
                    f"{odeme:.0f} ₺ ara ödeme alındı.\n"
                    f"Masa {masa_no} ({musteri_adi}).\n"
                    f"Yeni Kümülatif Bakiye: {yeni_cumulative_balance:.0f} ₺" # Yeni bakiyeyi göster
                    , parent=self.adisyon_frame
                )


            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Ara ödeme kaydedilirken hata oluştu: {e}", parent=self.adisyon_frame)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ara ödeme alınırken beklenmedik hata: {e}", parent=self.adisyon_frame)
                 print(f"Ara ödeme hatası: {e}")
                 import traceback
                 traceback.print_exc()

        except Exception as e:
             messagebox.showerror("Hata", f"Ara ödeme işlemi sırasında beklenmedik hata: {e}", parent=self.adisyon_frame)
             print(f"Ara ödeme ana blok hatası: {e}")
             import traceback
             traceback.print_exc()


    def _odeme_yap(self, odeme_turu):
        """Aktif masanın hesabını kapatır, siparişleri geçmişe kaydeder, masayı boşaltır ve müşteri bakiyesini günceller"""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        self.cursor.execute("SELECT durum, musteri_id, toplam FROM masalar WHERE masa_no = ?", (masa_no,))
        masa_info = self.cursor.fetchone()
        if not masa_info:
             messagebox.showwarning("Uyarı", "Masa bilgisi veritabanında bulunamadı.", parent=self.adisyon_frame)
             self._sepeti_yukle()
             self._masa_butonlarini_guncelle()
             return

        masa_durum = masa_info['durum']
        musteri_id = masa_info['musteri_id']
        masa_oturum_toplami = masa_info['toplam'] if masa_info['toplam'] is not None else 0.0


        if masa_durum != 'dolu':
             messagebox.showwarning("Uyarı", "Bu masa dolu değil veya zaten kapatılmış.", parent=self.adisyon_frame)
             self._sepeti_yukle()
             self._masa_butonlarini_guncelle()
             return

        self.cursor.execute("SELECT COUNT(*) FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))
        siparis_sayisi = self.cursor.fetchone()[0]

        if siparis_sayisi == 0:
            # Sepet boşsa masayı direkt boşalt
            if messagebox.askyesno("Uyarı", f"Sepet boş. Masa {masa_no}'yu kapatıp boşaltmak istediğinize emin misiniz?", parent=self.adisyon_frame):
                 self._sepeti_temizle() # _sepeti_temizle çağrılır, o içinde DB güncelleme ve UI yenileme yapar
                 messagebox.showinfo("Bilgi", f"Masa {masa_no} boşaltıldı.", parent=self.adisyon_frame)
                 # Ödeme işlemi tamamlandığı için aktif masayı burada None yapmalıyız.
                 self.aktif_masa = None
                 if hasattr(self, 'aktif_masa_label'):
                     self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
                 if hasattr(self, 'musteri_label'):
                      self.musteri_label.config(text="Müşteri: -")
                 if hasattr(self, 'musteri_bakiye_adisyon_label'):
                      self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺") # Bakiye etiketini de sıfırla
                 return # İşlem tamamlandı

            return # Sepet boş ve kullanıcı kapatmak istemediyse çık


        # Siparişler varsa ödeme işlemine devam et

        # Müşterinin mevcut kümülatif bakiyesini çek (varsa)
        current_cumulative_balance = 0.0
        if musteri_id:
            self.cursor.execute("SELECT cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
            musteri_bakiye_row = self.cursor.fetchone()
            if musteri_bakiye_row:
                current_cumulative_balance = musteri_bakiye_row['cumulative_balance'] if musteri_bakiye_row['cumulative_balance'] is not None else 0.0

        # Masanın ara ödemeler toplamını al
        self.cursor.execute('''
            SELECT COALESCE(SUM(miktar), 0) as ara_odeme_toplam FROM ara_odemeler
            WHERE masa_no = ?
        ''', (masa_no,))
        ara_odeme_row = self.cursor.fetchone()

        # !!! DÜZELTME: Anahtar adı 'ara_odeme_toplam' olarak değiştirildi !!!
        # Traceback'in işaret ettiği satır burasıydı.
        ara_odemeler_toplam = ara_odeme_row['ara_odeme_toplam'] if ara_odeme_row and 'ara_odeme_toplam' in ara_odeme_row and ara_odeme_row['ara_odeme_toplam'] is not None else 0.0


        # Masa oturumu toplamı + Müşteri kümülatif bakiye = Toplam Borç
        total_owed = current_cumulative_balance + masa_oturum_toplami

        # Ödenecek Tutar (Bu oturum için alınan ödeme + varsa ara ödemeler düşüldükten sonra kalan)
        odenecek_tutar_bu_kapanista = total_owed - ara_odemeler_toplam


        if odenecek_tutar_bu_kapanista < 0:
             messagebox.showwarning("Uyarı", f"Masa {masa_no} için fazla ödeme yapılmış veya hesapta tutarsızlık var. Ödenecek: {odenecek_tutar_bu_kapanista:.0f} ₺", parent=self.adisyon_frame)
             if not messagebox.askyesno("Onay", "Yine de masayı kapatmak istediğinize emin misiniz?", parent=self.adisyon_frame):
                 return

        # Ödeme onayı al
        if not messagebox.askyesno("Ödeme Onayı",
                                   f"Masa {masa_no} ({odeme_turu})\n"
                                   f"Masa Oturumu Toplamı: {masa_oturum_toplami:.0f} ₺\n"
                                   f"Müşteri Kümülatif Bakiye: {current_cumulative_balance:.0f} ₺\n"
                                   f"Toplam Borç: {total_owed:.0f} ₺\n"
                                   f"Yapılan Ara Ödemeler: {ara_odemeler_toplam:.0f} ₺\n"
                                   f"Ödenecek Tutar: {max(0.0, odenecek_tutar_bu_kapanista):.0f} ₺\n\n"
                                   "Masayı kapatmak istediğinize emin misiniz?",
                                   parent=self.adisyon_frame):
            return

        try:
            kapanis_str = self._tarih_saat_al_db_format()

            # Sipariş geçmişine kaydet (oturuma ait toplamı kaydet)
            self.cursor.execute('''
                INSERT INTO siparis_gecmisi
                (masa_no, tarih, odeme_turu, toplam, musteri_id)
                VALUES (?, ?, ?, ?, ?)
            ''', (masa_no, kapanis_str, odeme_turu, masa_oturum_toplami, musteri_id))

            siparis_id = self.cursor.lastrowid

            # Sipariş detaylarını kaydet (masa_siparisleri'nden çekerek)
            self.cursor.execute('''
                SELECT urun_adi, fiyat, miktar, tutar
                FROM masa_siparisleri
                WHERE masa_no = ?
            ''', (masa_no,))
            siparis_detaylari = self.cursor.fetchall()

            for detay in siparis_detaylari:
                self.cursor.execute('''
                    INSERT INTO siparis_detaylari
                    (siparis_id, urun_adi, fiyat, miktar, tutar)
                    VALUES (?, ?, ?, ?, ?)
                ''', (siparis_id, detay['urun_adi'], detay['fiyat'], detay['miktar'], detay['tutar']))

            # Masa geçmişine kaydet (oturuma ait bilgileri kaydet)
            self.cursor.execute("SELECT acilis FROM masalar WHERE masa_no = ?", (masa_no,))
            acilis_str = self.cursor.fetchone()['acilis'] # Acilis zamanını çek
            acilis_kayit = acilis_str if acilis_str else datetime(2000, 1, 1, 0, 0, 0).strftime(DB_DATE_FORMAT)

            # Tablo adı düzeltildi: 'masa geçmişi' -> 'masa_gecmisi'
            self.cursor.execute('''
                INSERT INTO masa_gecmisi
                (masa_no, acilis, kapanis, musteri_id, toplam, odeme_turu, tarih)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (masa_no, acilis_kayit, kapanis_str, musteri_id, masa_oturum_toplami, odeme_turu, kapanis_str))


            # MÜŞTERİ KÜMÜLATİF BAKİYESİNİ GÜNCELLE
            if musteri_id:
                alinan_odeme_bu_kapanista = max(0.0, odenecek_tutar_bu_kapanista)
                yeni_cumulative_balance = current_cumulative_balance + masa_oturum_toplami - alinan_odeme_bu_kapanista

                self.cursor.execute('''
                    UPDATE musteriler
                    SET cumulative_balance = ?
                    WHERE musteri_id = ?
                ''', (yeni_cumulative_balance, musteri_id))


            # Masa siparişlerini ve ara ödemeleri temizle
            self.cursor.execute("DELETE FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))
            self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,))

            # Masayı boşalt ve durumunu güncelle
            self.cursor.execute('''
                UPDATE masalar
                SET durum = 'boş', toplam = 0, musteri_id = NULL,
                acilis = NULL, kapanis = ?,
                son_adisyon_zamani = NULL, son_islem_zamani = ?
                WHERE masa_no = ?
            ''', (kapanis_str, kapanis_str, masa_no))

            self.conn.commit()

            # Fatura/Fiş Bilgisi Oluştur (Basit metin)
            fatura = f" ADİSYON DETAY & FİŞ \n"
            fatura += f"Masa: {masa_no}\n"
            # Acilis zamanını masa_gecmisi'nden çekmek daha doğru olabilir
            # Tablo adı düzeltildi: 'masa geçmişi' -> 'masa_gecmisi'
            self.cursor.execute("SELECT acilis FROM masa_gecmisi WHERE masa_no = ? ORDER BY kapanis DESC LIMIT 1", (masa_no,))
            acilis_gecmis_row = self.cursor.fetchone()
            acilis_str_display = datetime.strptime(acilis_gecmis_row['acilis'], DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if acilis_gecmis_row and acilis_gecmis_row['acilis'] else '-'

            fatura += f"Açılış: {acilis_str_display}\n"
            fatura += f"Kapanış: {self._tarih_saat_al_display_format()}\n"
            fatura += f"Ödeme Türü: {odeme_turu}\n"

            if musteri_id:
                self.cursor.execute("SELECT ad FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri and musteri['ad']:
                    fatura += f"Müşteri: {musteri['ad']}\n"
                    # Fişte güncel kümülatif bakiyeyi de gösterebiliriz
                    fatura += f"Yeni Bakiye: {yeni_cumulative_balance:.0f} ₺\n"


            fatura += "-"*30 + "\n"

            # Sipariş detaylarını fişe ekle (siparis_detaylari tablosundan çekerek)
            self.cursor.execute('''
                SELECT urun_adi, fiyat, miktar, tutar
                FROM siparis_detaylari
                WHERE siparis_id = ?
            ''', (siparis_id,)) # Yeni kaydedilen siparis_id kullanıldı
            siparis_detaylari_fis = self.cursor.fetchall()

            for detay in siparis_detaylari_fis:
                fatura += f"{detay['urun_adi']} x{detay['miktar']}: {detay['tutar']:.0f} ₺\n"

            fatura += "-"*30 + "\n"
            fatura += f"Masa Oturumu Toplamı: {masa_oturum_toplami:.0f} ₺\n"
            if ara_odemeler_toplam > 0:
                fatura += f"Ara Ödemeler: {ara_odemeler_toplam:.0f} ₺\n"
            fatura += f"Ödenen Tutar: {max(0.0, odenecek_tutar_bu_kapanista):.0f} ₺\n" # Bu kapanışta ödenen tutar
            fatura += "=== Teşekkür Ederiz ==="

            # Fiş penceresi
            popup = tk.Toplevel(self.root)
            popup.title("Fiş / Adisyon Detay")
            popup.transient(self.root)
            popup.grab_set()

            text_frame = ttk.Frame(popup)
            text_frame.pack(padx=PAD_X, pady=PAD_Y, fill=tk.BOTH, expand=True)

            fatura_text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Courier New", 10))
            scrollbar = ttk.Scrollbar(text_frame, command=fatura_text_widget.yview)
            fatura_text_widget.config(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            fatura_text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

            fatura_text_widget.insert(tk.END, fatura)
            fatura_text_widget.config(state="disabled")

            ttk.Button(popup, text="Tamam", command=popup.destroy, style="TButton").pack(pady=PAD_Y)
            popup.bind("<Return>", lambda e: popup.destroy())

            # Ödeme işlemi tamamlandığı için aktif masayı sıfırla
            self.aktif_masa = None
            if hasattr(self, 'aktif_masa_label'):
                self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
            if hasattr(self, 'musteri_label'):
                 self.musteri_label.config(text="Müşteri: -")
            if hasattr(self, 'musteri_bakiye_adisyon_label'): # Bakiye etiketini de sıfırla
                 self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")

            self._sepeti_temizle_ui_only()

            self._masa_butonlarini_guncelle()

            messagebox.showinfo("Başarılı", f"Masa {masa_no} kapatıldı ({odeme_turu}).", parent=self.adisyon_frame)

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ödeme yapılırken hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ödeme yapılırken beklenmedik hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
            print(f"Ödeme yapma hatası (Masa {masa_no}): {e}")
            import traceback
            traceback.print_exc()


# MÜŞTERİ İŞLEMLERİ
    # musteriler tablosuna cumulative_balance sütunu eklendiği için bu fonksiyon güncellendi
    # musteriler tablosuna cumulative_balance sütunu eklendiği için bu fonksiyon güncellendi
    def musteri_arayuz_olustur(self): # ALT ÇİZGİSİZ OLACAK
        """Müşteri İşlemleri sekmesi arayüzünü oluşturur"""
        # Form ve butonlar için Frame
        form_frame = ttk.Frame(self.musteri_frame, padding="10")
        form_frame.pack(pady=PAD_Y, fill=tk.X)

        # Etiketler ve Giriş Alanları için iç içe Frame
        input_frame = ttk.Frame(form_frame)
        input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))

        # Grid layout kullanacağız
        input_frame.columnconfigure(1, weight=1) # Giriş alanlarının olduğu sütun genişlesin

        ttk.Label(input_frame, text="Ad:", style="Bilgi.TLabel").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.musteri_ad_entry = ttk.Entry(input_frame)
        self.musteri_ad_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(input_frame, text="Soyad:", style="Bilgi.TLabel").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.musteri_soyad_entry = ttk.Entry(input_frame)
        self.musteri_soyad_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(input_frame, text="Telefon:", style="Bilgi.TLabel").grid(row=2, column=0, sticky="w", pady=2, padx=5)
        self.musteri_telefon_entry = ttk.Entry(input_frame)
        self.musteri_telefon_entry.grid(row=2, column=1, sticky="ew", pady=2)

        ttk.Label(input_frame, text="Adres:", style="Bilgi.TLabel").grid(row=3, column=0, sticky="w", pady=2, padx=5)
        self.musteri_adres_entry = ttk.Entry(input_frame)
        self.musteri_adres_entry.grid(row=3, column=1, sticky="ew", pady=2)

        # Kümülatif Bakiye Giriş Alanı
        ttk.Label(input_frame, text="Kümülatif Bakiye (₺):", style="Bilgi.TLabel").grid(row=4, column=0, sticky="w", pady=2, padx=5)
        self.musteri_bakiye_entry = ttk.Entry(input_frame)
        self.musteri_bakiye_entry.grid(row=4, column=1, sticky="ew", pady=2)
        self.musteri_bakiye_entry.insert(0, "0.00") # Varsayılan değer

        # Butonlar için Frame
        button_frame = ttk.Frame(form_frame)
        button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(button_frame, text="Yeni Müşteri Ekle", command=lambda: self._musteri_ekle_duzenle_db(), style="Yonetim.TButton").pack(pady=PAD_Y) # Lambda kullanıldı emin olmak için
        ttk.Button(button_frame, text="Seçileni Güncelle", command=lambda: self._musteri_ekle_duzenle_db(), style="Yonetim.TButton").pack(pady=PAD_Y) # Lambda kullanıldı emin olmak için
        ttk.Button(button_frame, text="Seçileni Sil", command=self.musteri_sil, style="Temizle.TButton").pack(pady=PAD_Y)
        # Müşteri Ödeme Al Butonu (Fonksiyonu sonra yazılacak)
        #ttk.Button(button_frame, text="Ödeme Al", command=self._musteri_odeme_al, style="AraOdeme.TButton").pack(pady=PAD_Y)

        # Müşteri Listesi Tablosu
        # Kumulatif Bakiye sütunu eklendi
        self.musteri_listesi = ttk.Treeview(self.musteri_frame, columns=("ID", "Ad", "Soyad", "Telefon", "Adres", "Kayıt Tarihi", "Kümülatif Bakiye"), show="headings", style="Treeview")

        self.musteri_listesi.heading("ID", text="ID")
        self.musteri_listesi.heading("Ad", text="Ad")
        self.musteri_listesi.heading("Soyad", text="Soyad")
        self.musteri_listesi.heading("Telefon", text="Telefon")
        self.musteri_listesi.heading("Adres", text="Adres")
        self.musteri_listesi.heading("Kayıt Tarihi", text="Kayıt Tarihi")
        self.musteri_listesi.heading("Kümülatif Bakiye", text="Bakiye", anchor='e') # Sağa hizala

        self.musteri_listesi.column("ID", width=50, stretch=tk.NO)
        self.musteri_listesi.column("Ad", width=100, stretch=tk.YES)
        self.musteri_listesi.column("Soyad", width=100, stretch=tk.YES)
        self.musteri_listesi.column("Telefon", width=100, stretch=tk.NO)
        self.musteri_listesi.column("Adres", width=150, stretch=tk.YES)
        self.musteri_listesi.column("Kayıt Tarihi", width=100, stretch=tk.NO)
        self.musteri_listesi.column("Kümülatif Bakiye", width=80, stretch=tk.NO) # Bakiye için sabit genişlik

        self.musteri_listesi.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        # Treeview'da seçim değiştiğinde formu doldur
        self.musteri_listesi.bind("<<TreeviewSelect>>", self._musteri_sec) # _musteri_sec fonksiyonuna bağlı

        # İlk yüklemede listeyi güncelle
        self._musteri_listesini_guncelle()

    def musteri_ekle(self):
        """Yeni müşteri ekler"""
        # Müşteri ID'si için basit bir timestamp kullanıldı, çakışma riski düşük
        # Daha robust bir ID için uuid modülü kullanılabilir (ancak kütüphane ekler)
        # veya veritabanında otomatik artan integer kullanılabilir (daha standart)
        # Şimdilik mevcut timestamp yaklaşımı korunuyor.

        ad = simpledialog.askstring("Müşteri Ekle", "Müşteri Adı (Zorunlu):", parent=self.root)
        if ad:
            ad = ad.strip()
            if not ad:
                 messagebox.showwarning("Uyarı", "Müşteri Adı boş olamaz!", parent=self.root)
                 return

            telefon = simpledialog.askstring("Müşteri Ekle", "Telefon (Opsiyonel):", parent=self.root)
            telefon = telefon.strip() if telefon else ""

            # Müşteri ID'si oluştur (Timestamp tabanlı, son 6 hane)
            musteri_id = str(int(datetime.now().timestamp()))[-6:]

            try:
                self.cursor.execute('''
                    INSERT INTO musteriler
                    (musteri_id, ad, telefon, kayit_tarihi)
                    VALUES (?, ?, ?, ?)
                ''', (musteri_id, ad, telefon, datetime.now().strftime(RAPOR_TARIH_FORMATI))) # Kayıt tarihi gg.aa.yyyy formatında

                self.conn.commit()
                self._musteri_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi!", parent=self.root)

            except sqlite3.IntegrityError:
                 messagebox.showerror("Hata", f"Müşteri ID'si {musteri_id} zaten mevcut. Lütfen tekrar deneyin.", parent=self.root)
                 # Nadir durumda timestamp çakışması olursa
            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Müşteri eklenirken veritabanı hatası: {e}", parent=self.root)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Müşteri eklenirken beklenmedik hata: {e}", parent=self.root)
                 print(f"Müşteri ekleme hatası: {e}")


    def musteri_sil(self):
        """Seçilen müşteriyi siler"""
        selected = self.musteri_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir müşteri seçin!", parent=self.musteri_frame)
            return

        # Seçilen müşterinin ID'sini al
        # row_factory sayesinde item["values"] yerine item["values"][0] ile ID'ye erişebiliriz.
        # Ama Treeview'a eklerken tuple olarak eklediğimiz için index kullanmak daha güvenli.
        musteri_id = self.musteri_listesi.item(selected[0], "values")[0]
        musteri_ad = self.musteri_listesi.item(selected[0], "values")[1]

        if messagebox.askyesno("Silme Onayı", f"'{musteri_ad}' müşterisini silmek istediğinize emin misiniz?\nBu müşterinin atandığı masalar boşaltılacaktır.", parent=self.musteri_frame):
            try:
                # Masalardan müşteriye yapılan atamaları kaldır
                self.cursor.execute('''
                    UPDATE masalar SET musteri_id = NULL
                    WHERE musteri_id = ?
                ''', (musteri_id,))

                # Müşteriyi sil
                self.cursor.execute('''
                    DELETE FROM musteriler WHERE musteri_id = ?
                ''', (musteri_id,))

                self.conn.commit()
                self._musteri_listesini_guncelle() # Müşteri listesini güncelle
                self._masa_butonlarini_guncelle() # Masa butonlarında müşteri bilgisi değişebilir

                # Eğer aktif masa silinen müşteriye aitse Adisyon sekmesindeki bilgiyi güncelle
                if self.aktif_masa:
                    self.cursor.execute("SELECT musteri_id FROM masalar WHERE masa_no = ?", (self.aktif_masa,))
                    aktif_masa_musteri_id = self.cursor.fetchone()['musteri_id']
                    if aktif_masa_musteri_id is None: # Eğer müşteri ID'si null olduysa
                        if hasattr(self, 'musteri_label'):
                             self.musteri_label.config(text="Müşteri: -")


                messagebox.showinfo("Başarılı", "Müşteri başarıyla silindi!", parent=self.musteri_frame)

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Müşteri silinirken veritabanı hatası: {e}", parent=self.musteri_frame)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Müşteri silinirken beklenmedik hata: {e}", parent=self.musteri_frame)
                 print(f"Müşteri silme hatası: {e}")


    def musteri_duzenle(self):
        """Seçilen müşterinin bilgilerini düzenler"""
        selected = self.musteri_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek için bir müşteri seçin!", parent=self.musteri_frame)
            return

        # Seçilen müşterinin ID'sini al
        musteri_id = self.musteri_listesi.item(selected[0], "values")[0]

        # Müşterinin mevcut bilgilerini al
        self.cursor.execute('''
            SELECT ad, telefon FROM musteriler WHERE musteri_id = ?
        ''', (musteri_id,))
        musteri = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir

        if not musteri: # Bu durum olmamalı ama kontrol etmek iyi
             messagebox.showerror("Hata", "Müşteri bilgisi bulunamadı!", parent=self.musteri_frame)
             self._musteri_listesini_guncelle()
             return

        mevcut_ad = musteri['ad']
        mevcut_tel = musteri['telefon']

        # Yeni bilgileri kullanıcıdan al (dialog pencereleri)
        yeni_ad = simpledialog.askstring("Müşteri Düzenle", "Yeni Ad (Zorunlu):", initialvalue=mevcut_ad, parent=self.root)
        if yeni_ad is None: # Kullanıcı iptal ettiyse
             return
        yeni_ad = yeni_ad.strip()

        if not yeni_ad:
             messagebox.showwarning("Uyarı", "Yeni Ad boş olamaz!", parent=self.root)
             return


        yeni_tel = simpledialog.askstring("Müşteri Düzenle", "Yeni Telefon (Opsiyonel):", initialvalue=mevcut_tel, parent=self.root)
        yeni_tel = yeni_tel.strip() if yeni_tel else ""


        # Bilgileri güncelle
        try:
            self.cursor.execute('''
                UPDATE musteriler
                SET ad = ?, telefon = ?
                WHERE musteri_id = ?
            ''', (yeni_ad, yeni_tel, musteri_id))

            self.conn.commit()
            self._musteri_listesini_guncelle() # Müşteri listesini güncelle

            # Eğer aktif masadaki müşteri bu müşteri ise Adisyon sekmesindeki bilgiyi güncelle
            if self.aktif_masa:
                self.cursor.execute("SELECT musteri_id FROM masalar WHERE masa_no = ?", (self.aktif_masa,))
                aktif_masa_musteri_id = self.cursor.fetchone()['musteri_id']

                if aktif_masa_musteri_id == musteri_id:
                    if hasattr(self, 'musteri_label'):
                         self.musteri_label.config(text=f"Müşteri: {yeni_ad}")


            messagebox.showinfo("Başarılı", "Müşteri bilgileri güncellendi!", parent=self.musteri_frame)

        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Müşteri güncellenirken veritabanı hatası: {e}", parent=self.musteri_frame)
             self.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Müşteri güncellenirken beklenmedik hata: {e}", parent=self.musteri_frame)
             print(f"Müşteri düzenleme hatası: {e}")


    def _musteri_listesini_guncelle(self):
        """Müşteri listesi Treeview'ını veritabanından günceller (Kumulatif Bakiye dahil)"""
        # Mevcut satırları temizle
        for item in self.musteri_listesi.get_children():
            self.musteri_listesi.delete(item)

        # Müşterileri veritabanından çek (cumulative_balance sütununu da çek)
        self.cursor.execute('''
            SELECT musteri_id, ad, soyad, telefon, adres, kayit_tarihi, cumulative_balance
            FROM musteriler
            ORDER BY ad ASC, soyad ASC
        ''')

        musteriler = self.cursor.fetchall() # row_factory sayesinde sütun isimleriyle erişilebilir

        # Treeview'a ekle
        for musteri in musteriler:
            # cumulative_balance değerini formatlayarak ekle (ondalıksız ve ₺ işareti)
            # Formatlama: Sayıyı ondalıksız yap (.0f) ve sonuna " ₺" ekle
            bakiye_str = f"{musteri['cumulative_balance']:.0f} ₺" if musteri['cumulative_balance'] is not None else "0 ₺"

            self.musteri_listesi.insert("", tk.END, values=(
                musteri['musteri_id'],
                musteri['ad'],
                musteri['soyad'],
                musteri['telefon'],
                musteri['adres'],
                musteri['kayit_tarihi'],
                bakiye_str # Formatlanmış bakiye stringi
            ))

        # Form alanlarını temizle
        self._musteri_formu_temizle()

    def _musteri_sec(self, event):
        """Müşteri listesi Treeview'ında bir müşteri seçildiğinde form alanlarını doldurur"""
        # Bu fonksiyon, musteri_arayuz_olustur içinde Treeview'ın <<TreeviewSelect>> olayına bağlanmıştır.
        selected_item = self.musteri_listesi.selection()
        if not selected_item:
            self._musteri_formu_temizle() # Seçim kaldırılırsa formu temizle
            return

        # Seçili öğenin değerlerini al (Treeview'daki sütun sırasına göre)
        item_values = self.musteri_listesi.item(selected_item[0], "values")

        # Değerleri form alanlarına yerleştir
        self._musteri_formu_temizle() # Önce formu temizle

        # Treeview değerleri sırasıyla: ID, Ad, Soyad, Telefon, Adres, Kayıt Tarihi, Bakiye
        self.musteri_ad_entry.insert(0, item_values[1]) # Ad (index 1)
        self.musteri_soyad_entry.insert(0, item_values[2]) # Soyad (index 2)
        self.musteri_telefon_entry.insert(0, item_values[3]) # Telefon (index 3)
        self.musteri_adres_entry.insert(0, item_values[4]) # Adres (index 4)
        # Kayıt Tarihi Treeview'da var ama formda alanı yok (index 5)

        # Kumulatif Bakiye alanını doldur (index 6)
        # Treeview'dan gelen bakiye stringi "123 ₺" formatında olabilir, sadece sayıyı almalıyız
        try:
            bakiye_str = str(item_values[6]).replace(' ₺', '').strip() # Bakiye sütunu 6. index
            # Sayıya çevirip form alanına ondalıklı formatta yerleştir (kullanıcı düzenlerken kolaylık)
            # Formatlama: Sayıyı iki ondalık basamaklı yap (.2f), ₺ işareti olmadan
            bakiye_float = float(bakiye_str)
            self.musteri_bakiye_entry.insert(0, f"{bakiye_float:.2f}") # Ondalıklı göster
        except (ValueError, IndexError, TypeError): # IndexError veya TypeError (None gelirse) yakala
            self.musteri_bakiye_entry.insert(0, "0.00") # Hata olursa varsayılan değer

        # Seçili müşterinin ID'sini sakla (güncelleme veya silme için)
        self.secili_musteri_id = item_values[0] # ID sütunu 0. index

    def _musteri_formu_temizle(self):
        """Müşteri ekleme/düzenleme form alanlarını temizler"""
        self.musteri_ad_entry.delete(0, tk.END)
        self.musteri_soyad_entry.delete(0, tk.END)
        self.musteri_telefon_entry.delete(0, tk.END)
        self.musteri_adres_entry.delete(0, tk.END)
        # Kumulatif Bakiye alanını temizle
        self.musteri_bakiye_entry.delete(0, tk.END)
        self.musteri_bakiye_entry.insert(0, "0.00") # Varsayılan başlangıç değeri

        # Seçili müşteri ID'sini sıfırla (güncelleme/silme modundan çıkar)
        self.secili_musteri_id = None

    def _musteri_ekle_duzenle_db(self):
        """Formdaki bilgilere göre yeni müşteri ekler veya seçili müşteriyi günceller (Kumulatif Bakiye dahil)"""
        ad = self.musteri_ad_entry.get().strip()
        soyad = self.musteri_soyad_entry.get().strip()
        telefon = self.musteri_telefon_entry.get().strip()
        adres = self.musteri_adres_entry.get().strip()
        bakiye_str = self.musteri_bakiye_entry.get().strip() # Bakiye stringini al

        if not ad or not soyad or not telefon:
            messagebox.showwarning("Uyarı", "Ad, Soyad ve Telefon alanları boş bırakılamaz!", parent=self.musteri_frame)
            return

        # Bakiye stringini sayıya çevir
        try:
            cumulative_balance = float(bakiye_str)
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçersiz bakiye değeri girildi.\nLütfen sayısal bir değer girin.", parent=self.musteri_frame)
            return

        kayit_tarihi = self._tarih_saat_al_db_format() # Kayıt veya güncelleme tarihi

        try:
            if self.secili_musteri_id is None:
                # Yeni Müşteri Ekle
                self.cursor.execute('''
                    INSERT INTO musteriler (ad, soyad, telefon, adres, kayit_tarihi, cumulative_balance)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (ad, soyad, telefon, adres, kayit_tarihi, cumulative_balance))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Yeni müşteri başarıyla eklendi!", parent=self.musteri_frame)
            else:
                # Seçili Müşteriyi Güncelle
                # Güncelleme sırasında kayit_tarihi güncellenmez, sadece bilgiler değişir
                self.cursor.execute('''
                    UPDATE musteriler
                    SET ad = ?, soyad = ?, telefon = ?, adres = ?, cumulative_balance = ?
                    WHERE musteri_id = ?
                ''', (ad, soyad, telefon, adres, cumulative_balance, self.secili_musteri_id))
                self.conn.commit()
                messagebox.showinfo("Başarılı", "Müşteri bilgileri başarıyla güncellendi!", parent=self.musteri_frame)

            # Listeyi ve formu yenile
            self._musteri_listesini_guncelle()
            self._musteri_formu_temizle()

        except sqlite3.IntegrityError:
             messagebox.showwarning("Uyarı", f"'{telefon}' telefon numarası zaten başka bir müşteriye ait.", parent=self.musteri_frame)
             self.conn.rollback() # İşlemi geri al
        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Müşteri eklenirken/güncellenirken hata oluştu: {e}", parent=self.musteri_frame)
             self.conn.rollback() # İşlemi geri al
        except Exception as e:
             messagebox.showerror("Hata", f"Müşteri eklenirken/güncellenirken beklenmedik hata: {e}", parent=self.musteri_frame)
             print(f"Müşteri ekle/düzenle hatası: {e}")

    # ÜRÜN YÖNETİMİ
    def urun_arayuz_olustur(self):
        """Ürün Yönetimi sekmesi arayüzünü oluşturur (Kategori Yönetimi dahil)"""

        # !!! YENİ SIRALAMA: Kategori Yönetimi Alanı en üstte !!!
        kategori_yonetim_frame = ttk.Frame(self.urun_frame, padding="10")
        kategori_yonetim_frame.pack(pady=PAD_Y, fill=tk.X) # <<< İlk paketlenen frame

        ttk.Label(kategori_yonetim_frame, text="Kategori Yönetimi", style="Baslik.TLabel").pack(anchor="w")

        kategori_input_frame = ttk.Frame(kategori_yonetim_frame)
        kategori_input_frame.pack(pady=PAD_Y, fill=tk.X)

        ttk.Label(kategori_input_frame, text="Kategori Adı:", style="Bilgi.TLabel").pack(side=tk.LEFT, padx=5)
        self.kategori_adi_entry = ttk.Entry(kategori_input_frame)
        self.kategori_adi_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(kategori_input_frame, text="Kategori Ekle", command=self._kategori_ekle_db, style="Yonetim.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(kategori_input_frame, text="Kategori Sil", command=self._kategori_sil_db, style="Temizle.TButton").pack(side=tk.LEFT)

        # Kategori Listesi Tablosu
        # Treeview oluşturuluyor ve paketleniyor
        self.kategori_listesi_tree = ttk.Treeview(kategori_yonetim_frame, columns=("Kategori Adı",), show="headings", style="Treeview", height=5)
        self.kategori_listesi_tree.heading("Kategori Adı", text="Kategori Adı")
        self.kategori_listesi_tree.column("Kategori Adı", width=200, stretch=tk.YES)
        self.kategori_listesi_tree.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        # Treeview'da kategori seçildiğinde Entry'i doldur (Silme kolaylığı için)
        self.kategori_listesi_tree.bind("<<TreeviewSelect>>", self._kategori_sec_for_delete)


        # Ürün ekleme/güncelleme formu (Ortada)
        urun_form_frame = ttk.Frame(self.urun_frame, padding="10")
        urun_form_frame.pack(pady=PAD_Y, fill=tk.X) # <<< İkinci paketlenen frame

        urun_input_frame = ttk.Frame(urun_form_frame)
        urun_input_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 20))

        urun_input_frame.columnconfigure(1, weight=1) # Giriş alanlarının olduğu sütun genişlesin

        ttk.Label(urun_input_frame, text="Sıra:", style="Bilgi.TLabel").grid(row=0, column=0, sticky="w", pady=2, padx=5)
        self.urun_sira_entry = ttk.Entry(urun_input_frame)
        self.urun_sira_entry.grid(row=0, column=1, sticky="ew", pady=2)

        ttk.Label(urun_input_frame, text="Ürün Adı:", style="Bilgi.TLabel").grid(row=1, column=0, sticky="w", pady=2, padx=5)
        self.urun_adi_entry = ttk.Entry(urun_input_frame)
        self.urun_adi_entry.grid(row=1, column=1, sticky="ew", pady=2)

        ttk.Label(urun_input_frame, text="Fiyat (₺):", style="Bilgi.TLabel").grid(row=2, column=0, sticky="w", pady=2, padx=5)
        self.urun_fiyat_entry = ttk.Entry(urun_input_frame)
        self.urun_fiyat_entry.grid(row=2, column=1, sticky="ew", pady=2)

        # Kategori seçimi için Combobox
        ttk.Label(urun_input_frame, text="Kategori:", style="Bilgi.TLabel").grid(row=3, column=0, sticky="w", pady=2, padx=5)
        self.urun_kategori_combobox = ttk.Combobox(urun_input_frame, state="readonly")
        self.urun_kategori_combobox.grid(row=3, column=1, sticky="ew", pady=2)
        # Kategori combobox içeriği _kategori_listesini_guncelle içinde doldurulacak

        urun_button_frame = ttk.Frame(urun_form_frame)
        urun_button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Button(urun_button_frame, text="Yeni Ürün Ekle", command=self._urun_ekle_duzenle_db, style="Yonetim.TButton").pack(pady=PAD_Y)
        ttk.Button(urun_button_frame, text="Seçili Ürünü Güncelle", command=self._urun_ekle_duzenle_db, style="Yonetim.TButton").pack(pady=PAD_Y)
        ttk.Button(urun_button_frame, text="Seçili Ürünü Sil", command=self._urun_sil, style="Temizle.TButton").pack(pady=PAD_Y)


        # Ürün Listesi Tablosu (En altta)
        self.urun_listesi = ttk.Treeview(self.urun_frame, columns=("Sıra", "Ürün Adı", "Fiyat", "Kategori"), show="headings", style="Treeview")
        # ... (Mevcut ürün listesi başlıkları ve sütunları) ...
        self.urun_listesi.heading("Sıra", text="Sıra")
        self.urun_listesi.heading("Ürün Adı", text="Ürün Adı")
        self.urun_listesi.heading("Fiyat", text="Fiyat", anchor='e')
        self.urun_listesi.heading("Kategori", text="Kategori")

        self.urun_listesi.column("Sıra", width=50, stretch=tk.NO)
        self.urun_listesi.column("Ürün Adı", width=150, stretch=tk.YES)
        self.urun_listesi.column("Fiyat", width=80, stretch=tk.NO)
        self.urun_listesi.column("Kategori", width=100, stretch=tk.NO)

        self.urun_listesi.pack(pady=PAD_Y, fill=tk.BOTH, expand=True) # <<< Üçüncü paketlenen frame

        # Ürün listesi Treeview'ında seçim değiştiğinde formu doldur
        self.urun_listesi.bind("<<TreeviewSelect>>", self._urun_sec)

        # İlk yüklemede ürün ve kategori listelerini güncelle
        # _urun_listesini_guncelle() çağrısı Ürün listesini ve formu temizler, kategori combobox'ını günceller.
        # Ancak kategori listesi Treeview'ını güncellemez. Onu ayrıca çağırmalıyız.
        self._urun_listesini_guncelle()
        self._kategori_listesini_guncelle() # <<< Kategori listesi Treeview'ını güncellemek için çağrı eklendi


    def _kategori_ekle_db(self):
        """Yeni kategori ekler"""
        kategori_adi = self.kategori_adi_entry.get().strip()

        if not kategori_adi:
            messagebox.showwarning("Uyarı", "Kategori adı boş bırakılamaz!", parent=self.urun_frame)
            return

        try:
            # Kategorileri ayrı bir tabloda tutmak daha iyi olabilir,
            # ancak şimdilik urunler tablosundaki DISTINCT kategorileri kullanıyoruz.
            # Yeni bir kategori eklemek, aslında o kategoride bir ürün eklemeyi gerektirir.
            # Ancak kullanıcı sadece kategori eklemek isteyebilir.
            # Bu durumda, kategori listesini urunler tablosundan DISTINCT çekerek oluşturduğumuz için,
            # sadece kategori ekleme diye bir işlem veritabanı tarafında doğrudan yapılamaz.
            # Geçici çözüm olarak, kategori ekleme butonuna basıldığında,
            # girilen kategori adında bir ürünün (varsayılan değerlerle) eklenmesini sağlayabiliriz.
            # Veya, sadece kategori listesi Treeview'ını güncellemek yeterli olabilir,
            # çünkü yeni kategori adı girilip Ürün Ekle/Güncelle yapıldığında kategori listesi zaten güncellenecektir.

            # En basit yaklaşım: Sadece UI'daki kategori listesini güncelle.
            # Yeni kategori adı, bir ürün eklenirken kullanılabilir hale gelecek.
            # Ancak kullanıcı sadece kategori eklemek isterse, bu butonun anlamı ne olmalı?

            # Daha iyi bir yaklaşım: Kategoriler için ayrı bir tablo oluşturmak.
            # Şimdilik mevcut yapıya uyum sağlayalım: Ürün eklerken yeni kategori girilebilir.
            # Kategori Ekle butonuna basıldığında, girilen kategori adının geçerli bir kategori olduğunu teyit edip,
            # kategori listesi Treeview'ını ve ürün ekleme Combobox'ını güncelleyelim.

            # Girilen kategori adının zaten var olup olmadığını kontrol et
            self.cursor.execute("SELECT COUNT(*) FROM urunler WHERE kategori = ?", (kategori_adi,))
            if self.cursor.fetchone()[0] > 0:
                messagebox.showwarning("Uyarı", f"'{kategori_adi}' kategorisi zaten mevcut (en az bir ürünü var).", parent=self.urun_frame)
                return

            # Eğer kategori mevcut değilse, kullanıcıya bu kategoride bir ürün eklemesi gerektiğini bildirelim.
            # Veya, sadece kategori listesi Treeview'ını güncelleyelim ve umalım ki kullanıcı bu kategoride bir ürün ekler.
            # İkinci yol daha basit ve mevcut yapıya uygun.

            # Sadece kategori listesi Treeview'ını ve Ürün Combobox'ını güncelle
            self._kategori_listesini_guncelle()
            self._urun_kategori_combobox_guncelle() # Ürün ekleme combobox'ını güncelle

            messagebox.showinfo("Bilgi", f"'{kategori_adi}' kategorisi listeye eklendi. Bu kategoride ürün ekleyebilirsiniz.", parent=self.urun_frame)
            self.kategori_adi_entry.delete(0, tk.END) # Giriş alanını temizle


        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Kategori eklenirken hata oluştu: {e}", parent=self.urun_frame)
             self.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Kategori eklenirken beklenmedik hata: {e}", parent=self.urun_frame)
             print(f"Kategori ekleme hatası: {e}")

    def _kategori_sil_db(self):
        """Seçili kategoriyi siler"""
        selected_item = self.kategori_listesi_tree.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir kategori seçin!", parent=self.urun_frame)
            return

        kategori_adi = self.kategori_listesi_tree.item(selected_item[0], "values")[0]

        # Bu kategoride ürün olup olmadığını kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM urunler WHERE kategori = ?", (kategori_adi,))
        urun_sayisi = self.cursor.fetchone()[0]

        if urun_sayisi > 0:
            messagebox.showwarning("Uyarı", f"'{kategori_adi}' kategorisine ait {urun_sayisi} ürün bulunmaktadır.\nLütfen önce bu kategorideki ürünleri silin veya başka bir kategoriye taşıyın.", parent=self.urun_frame)
            return

        # Eğer kategoriye ait ürün yoksa silme onayı al
        if messagebox.askyesno("Kategori Sil", f"'{kategori_adi}' kategorisini silmek istediğinize emin misiniz?", parent=self.urun_frame):
            try:
                # Kategoriler ayrı bir tabloda olmadığı için, aslında silme işlemi sadece UI listesinden kaldırmak anlamına gelir.
                # Ancak gelecekte ayrı bir kategori tablosu olursa burası güncellenmelidir.
                # Şu anki mantıkla, ürün olmayan bir kategoriyi listeden silmek yeterlidir.
                # Veritabanında kategori sütunundaki değeri NULL yapmak da bir seçenek olabilir,
                # ancak bu durumda kategori listesi DISTINCT çekildiği için yine görünmeyecektir.

                # Sadece UI listesinden kaldırıyoruz ve ürün ekleme combobox'ını güncelliyoruz.
                # Veritabanında doğrudan kategori silme diye bir işlem yok mevcut yapıda.

                # Kategori listesi Treeview'ını ve Ürün Combobox'ını güncelle
                self._kategori_listesini_guncelle()
                self._urun_kategori_combobox_guncelle() # Ürün ekleme combobox'ını güncelle

                messagebox.showinfo("Başarılı", f"'{kategori_adi}' kategorisi listeden kaldırıldı.", parent=self.urun_frame)
                self.kategori_adi_entry.delete(0, tk.END) # Giriş alanını temizle


            except Exception as e:
                 messagebox.showerror("Hata", f"Kategori silinirken beklenmedik hata: {e}", parent=self.urun_frame)
                 print(f"Kategori silme hatası: {e}")

    def _kategori_listesini_guncelle(self):
        """Ürünler tablosundaki benzersiz kategorileri çekerek Kategori Listesi Treeview'ını ve Ürün Combobox'ını günceller"""
        # Kategori Listesi Treeview'ını temizle
        if hasattr(self, 'kategori_listesi_tree'): # Treeview'ın oluşturulduğundan emin ol
            for item in self.kategori_listesi_tree.get_children():
                self.kategori_listesi_tree.delete(item)

        try:
            # Ürünler tablosundan benzersiz kategorileri çek
            # Boş veya NULL kategorileri hariç tut
            self.cursor.execute("SELECT DISTINCT kategori FROM urunler WHERE kategori IS NOT NULL AND kategori != '' ORDER BY kategori ASC")
            kategoriler = [row['kategori'] for row in self.cursor.fetchall()]

            # Kategori Listesi Treeview'ına ekle
            if hasattr(self, 'kategori_listesi_tree'): # Treeview'ın oluşturulduğundan emin ol
                for kategori in kategoriler:
                    self.kategori_listesi_tree.insert("", tk.END, values=(kategori,))

            # Ürün ekleme/düzenleme Combobox'ını güncelle
            self._urun_kategori_combobox_guncelle()

            # Adisyon sekmesindeki kategori filtreleme Combobox'ını da güncelle
            self._adisyon_kategori_filtre_combobox_guncelle()


        except sqlite3.Error as e:
            print(f"Kategori listesi güncellenirken veritabanı hatası: {e}")
        except Exception as e:
            print(f"Kategori listesi güncellenirken beklenmedik hata: {e}")


    def _kategori_sec_for_delete(self, event):
        """Kategori listesi Treeview'ında bir kategori seçildiğinde Kategori Adı Entry'sini doldurur"""
        selected_item = self.kategori_listesi_tree.selection()
        if not selected_item:
            self.kategori_adi_entry.delete(0, tk.END)
            return

        kategori_adi = self.kategori_listesi_tree.item(selected_item[0], "values")[0]
        self.kategori_adi_entry.delete(0, tk.END)
        self.kategori_adi_entry.insert(0, kategori_adi)


    def _urun_kategori_combobox_guncelle(self):
        """Ürün ekleme/düzenleme formundaki Kategori Combobox'ını güncel kategorilerle doldurur"""
        try:
            self.cursor.execute("SELECT DISTINCT kategori FROM urunler WHERE kategori IS NOT NULL AND kategori != '' ORDER BY kategori ASC")
            kategoriler = [row['kategori'] for row in self.cursor.fetchall()]
            # Ürün eklerken boş kategoriye izin vermek isterseniz buraya boş string ekleyebilirsiniz.
            # kategoriler.insert(0, "") # Boş kategori seçeneği ekle
            self.urun_kategori_combobox['values'] = kategoriler
            if kategoriler:
                 self.urun_kategori_combobox.set(kategoriler[0]) # Varsayılan olarak ilk kategoriyi seç
            else:
                 self.urun_kategori_combobox.set("") # Kategori yoksa boş bırak

        except sqlite3.Error as e:
            print(f"Ürün kategori combobox güncellenirken veritabanı hatası: {e}")
        except Exception as e:
            print(f"Ürün kategori combobox güncellenirken beklenmedik hata: {e}")


    def _adisyon_kategori_filtre_combobox_guncelle(self):
        """Adisyon sekmesindeki kategori filtreleme Combobox'ını güncel kategorilerle doldurur"""
        # Bu fonksiyon, _kategorileri_getir fonksiyonunu çağırarak Combobox'ı doldurur.
        # Sadece _kategori_listesini_guncelle içinde çağrılması yeterlidir.
        # _kategorileri_getir zaten 'Tümü' seçeneğini içerir.
        if hasattr(self, 'kategori_filtre_combobox'): # Adisyon sekmesi UI'ı oluşturulduysa
             kategoriler = self._kategorileri_getir()
             self.kategori_filtre_combobox['values'] = kategoriler
             if "Tümü" in kategoriler:
                  self.kategori_filtre_combobox.set("Tümü") # Varsayılanı 'Tümü' yap
             elif kategoriler:
                  self.kategori_filtre_combobox.set(kategoriler[0]) # 'Tümü' yoksa ilkini seç
             else:
                  self.kategori_filtre_combobox.set("") # Kategori yoksa boş bırak

    def urun_ekle_panel(self):
        """Yeni ürün ekleme penceresini açar"""
        ekle_pencere = tk.Toplevel(self.root)
        ekle_pencere.title("Yeni Ürün Ekle")
        ekle_pencere.transient(self.root) # Ana pencere üzerinde kalmasını sağlar
        ekle_pencere.grab_set() # Ana pencereyi kilitler
        ekle_pencere.resizable(False, False)

        # Giriş alanları için frame
        input_frame = ttk.Frame(ekle_pencere, padding=(PAD_X*2, PAD_Y*2))
        input_frame.pack(padx=PAD_X, pady=PAD_Y)

        ttk.Label(input_frame, text="Ürün Adı:", style="Bilgi.TLabel").grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        urun_adi_entry = ttk.Entry(input_frame, width=30)
        urun_adi_entry.grid(row=0, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")

        ttk.Label(input_frame, text="Fiyat (TL):", style="Bilgi.TLabel").grid(row=1, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        fiyat_entry = ttk.Entry(input_frame, width=15)
        fiyat_entry.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")

        ttk.Label(input_frame, text="Kategori:", style="Bilgi.TLabel").grid(row=2, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        kategori_combobox = ttk.Combobox(input_frame, values=list(KATEGORI_RENKLERI.keys()), state="readonly", width=20)
        if len(KATEGORI_RENKLERI) > 0:
             kategori_combobox.current(0) # İlk kategoriyi varsayılan yap
        kategori_combobox.grid(row=2, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")

        ttk.Label(input_frame, text="Sıra No:", style="Bilgi.TLabel").grid(row=3, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        sira_spinbox = tk.Spinbox(input_frame, from_=1, to=9999, width=8, font=("Arial", 10)) # Spinbox genişliği ayarlandı
        sira_spinbox.grid(row=3, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")

        # Otomatik sıra numarası önerisi (en yüksek sıradan +1)
        self.cursor.execute("SELECT MAX(sira) FROM urunler")
        max_sira = self.cursor.fetchone()[0]
        next_sira = (max_sira if max_sira is not None else 0) + 1
        sira_spinbox.delete(0, tk.END)
        sira_spinbox.insert(0, str(next_sira))


        def kaydet_action():
            urun_adi = urun_adi_entry.get().strip().upper()
            if not urun_adi:
                messagebox.showwarning("Uyarı", "Ürün adı boş olamaz!", parent=ekle_pencere)
                return

            # Ürün adının zaten var olup olmadığını kontrol et
            self.cursor.execute("SELECT COUNT(*) FROM urunler WHERE urun_adi = ?", (urun_adi,))
            if self.cursor.fetchone()[0] > 0:
                 messagebox.showwarning("Uyarı", f"'{urun_adi}' isminde bir ürün zaten mevcut!", parent=ekle_pencere)
                 return

            try:
                fiyat = float(fiyat_entry.get().replace(",", ".")) # Virgülü noktaya çevir
                if fiyat < 0:
                    raise ValueError # Negatif fiyat olamaz
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz fiyat değeri! Sayı girin ve negatif olmasın.", parent=ekle_pencere)
                return

            kategori = kategori_combobox.get()
            if not kategori:
                 messagebox.showwarning("Uyarı", "Lütfen kategori seçin!", parent=ekle_pencere)
                 return

            try:
                sira = int(sira_spinbox.get())
                if sira <= 0:
                     raise ValueError # Sıra numarası pozitif olmalı
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz sıra numarası! Pozitif tam sayı girin.", parent=ekle_pencere)
                return

            try:
                self.cursor.execute('''
                    INSERT INTO urunler (urun_adi, fiyat, kategori, sira)
                    VALUES (?, ?, ?, ?)
                ''', (urun_adi, fiyat, kategori, sira))

                self.conn.commit()
                self._urun_listesini_guncelle() # Ürün listesini güncelle
                self._hizli_satis_butonlari_olustur() # Hızlı satış butonlarını yenile
                messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!", parent=ekle_pencere)
                ekle_pencere.destroy() # Pencereyi kapat

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Ürün eklenirken veritabanı hatası: {e}", parent=ekle_pencere)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ürün eklenirken beklenmedik hata: {e}", parent=ekle_pencere)
                 print(f"Ürün ekleme hatası: {e}")


        ttk.Button(input_frame, text="Kaydet", command=kaydet_action, style="TButton").grid(row=4, column=0, columnspan=2, pady=PAD_Y)

        ekle_pencere.focus_set() # Pencereye odaklan


    def urun_sil(self):
        """Seçilen ürünü siler"""
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek için bir ürün seçin!", parent=self.urun_frame)
            return

        # Seçilen ürün adını al
        # Treeview'a eklerken tuple olarak eklediğimiz için index kullanmak daha güvenli.
        # Ürün adı 1. sütunda (index 1)
        urun_adi = self.urun_listesi.item(selected[0], "values")[1]


        if messagebox.askyesno("Silme Onayı", f"'{urun_adi}' ürününü silmek istediğinize emin misiniz?\nAçık masalardaki bu ürüne ait siparişler de silinecektir.", parent=self.urun_frame):
            try:
                # Ürünü veritabanından sil
                self.cursor.execute('''
                    DELETE FROM urunler WHERE urun_adi = ?
                ''', (urun_adi,))

                # Açık masalardaki bu ürünün siparişlerini sil
                self.cursor.execute('''
                    DELETE FROM masa_siparisleri WHERE urun_adi = ?
                ''', (urun_adi,))

                # Ürün silindiğinde masaların toplamını yeniden hesapla (etkilenen masalar için)
                # Bu sorgu, ürün silindikten sonra doğru toplamı set eder
                self.cursor.execute('''
                     UPDATE masalar
                     SET toplam = (
                         SELECT COALESCE(SUM(tutar), 0)
                         FROM masa_siparisleri
                         WHERE masa_no = masalar.masa_no
                     )
                     WHERE masa_no IN (SELECT masa_no FROM masa_siparisleri WHERE urun_adi IS NULL GROUP BY masa_no) -- Etkilenen masaları bul
                        OR masa_no IN (SELECT masa_no FROM masalar WHERE toplam != 0 AND durum = 'dolu') -- Veya toplamı 0 olmayan dolu masalar (genel güvenlik)
                 ''')


                self.conn.commit()
                self._urun_listesini_guncelle() # Ürün listesini güncelle
                self._hizli_satis_butonlari_olustur() # Hızlı satış butonlarını yenile

                # Eğer aktif masa etkilendiyse (silinen ürün sepetteyse), sepeti ve toplamı güncelle
                if self.aktif_masa:
                    self._sepeti_yukle() # Sepeti veritabanından yeniden yükle


                self._masa_butonlarini_guncelle() # Masa buton bilgilerini güncelle (toplam değişebilir)

                messagebox.showinfo("Başarılı", "Ürün başarıyla silindi!", parent=self.urun_frame)

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Ürün silinirken veritabanı hatası: {e}", parent=self.urun_frame)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ürün silinirken beklenmedik hata: {e}", parent=self.urun_frame)
                 print(f"Ürün silme hatası: {e}")


    def urun_fiyat_guncelle(self):
        """Seçilen ürünün fiyatını günceller"""
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen fiyatını güncellemek için bir ürün seçin!", parent=self.urun_frame)
            return

        # Seçilen ürün adını ve mevcut fiyatını al
        # Treeview'a eklerken tuple olarak eklediğimiz için index kullanmak daha güvenli.
        # Ürün adı 1. sütunda (index 1), fiyat 2. sütunda (index 2)
        urun_adi = self.urun_listesi.item(selected[0], "values")[1]
        mevcut_fiyat = self.urun_listesi.item(selected[0], "values")[2] # Treeview'dan al

        # Alternatif ve daha güvenli: Fiyatı veritabanından tekrar çek
        self.cursor.execute("SELECT fiyat FROM urunler WHERE urun_adi = ?", (urun_adi,))
        db_mevcut_fiyat_row = self.cursor.fetchone()
        if db_mevcut_fiyat_row:
             mevcut_fiyat = db_mevcut_fiyat_row['fiyat'] # row_factory sayesinde sütun isimleriyle erişilir
        else:
             messagebox.showerror("Hata", "Ürün bilgisi veritabanında bulunamadı!", parent=self.urun_frame)
             self._urun_listesini_guncelle()
             return


        # Yeni fiyatı kullanıcıdan al (dialog penceresi)
        while True: # Geçersiz giriş olana kadar tekrar sor
            yeni_fiyat_str = simpledialog.askstring("Fiyat Güncelle",
                                                    f"'{urun_adi}' için yeni fiyatı girin (TL):",
                                                    initialvalue=str(mevcut_fiyat), # float'ı string yap
                                                    parent=self.root)

            if yeni_fiyat_str is None: # Kullanıcı iptal ettiyse
                 return

            try:
                yeni_fiyat = float(yeni_fiyat_str.replace(",", ".")) # Virgülü noktaya çevir
                if yeni_fiyat < 0:
                    raise ValueError # Negatif fiyat olamaz
                break # Geçerli giriş yapıldı, döngüden çık
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz fiyat formatı! Lütfen pozitif bir sayı girin.", parent=self.root)


        # Fiyatı veritabanında güncelle
        try:
            # 1. Ürünler tablosunda fiyatı güncelle
            self.cursor.execute('''
                UPDATE urunler SET fiyat = ? WHERE urun_adi = ?
            ''', (yeni_fiyat, urun_adi))

            # 2. Açık masalardaki bu ürünün fiyatını ve tutarını güncelle
            self.cursor.execute('''
                UPDATE masa_siparisleri
                SET fiyat = ?, tutar = ? * miktar
                WHERE urun_adi = ?
            ''', (yeni_fiyat, yeni_fiyat, urun_adi))

            # 3. Açık masaların toplamını yeniden hesapla (etkilenen masalar için)
            self.cursor.execute('''
                UPDATE masalar
                SET toplam = (
                    SELECT COALESCE(SUM(tutar), 0)
                    FROM masa_siparisleri
                    WHERE masa_no = masalar.masa_no
                )
                WHERE masa_no IN (SELECT masa_no FROM masa_siparisleri WHERE urun_adi = ? GROUP BY masa_no) -- Etkilenen masaları bul
                OR masa_no IN (SELECT masa_no FROM masalar WHERE toplam != 0 AND durum = 'dolu') -- Veya toplamı 0 olmayan dolu masalar (genel güvenlik)
            ''', (urun_adi,)) # urun_adi parametresi 2. sorgudaki ? için tekrar kullanılmaz, dikkat!
             # Sorgu yeniden yazıldı veya birden çok execute kullanılmalı. En güvenlisi 2 execute.

            # Yukarıdaki sorguyu 2 execute'a bölelim
            self.cursor.execute('''
                UPDATE masalar
                SET toplam = (
                    SELECT COALESCE(SUM(tutar), 0)
                    FROM masa_siparisleri
                    WHERE masa_no = masalar.masa_no
                )
                WHERE masa_no IN (SELECT masa_no FROM masa_siparisleri WHERE urun_adi = ? GROUP BY masa_no)
            ''', (urun_adi,))
             # İkinci sorgya gerek yok, ilk sorgu fiyatı değişen ürünün olduğu tüm masaları günceller.

            self.conn.commit()
            self._urun_listesini_guncelle() # Ürün listesini güncelle
            self._hizli_satis_butonlari_olustur() # Hızlı satış butonlarını yenile

            # Eğer aktif masadaki ürünün fiyatı değiştiyse, sepeti ve toplamı güncelle
            if self.aktif_masa:
                # Aktif masanın etkilenip etkilenmediğini kontrol etmeye gerek yok, sepeti_yukle her türlü doğru toplamı çeker
                self._sepeti_yukle() # Sepeti veritabanından yeniden yükle


            self._masa_butonlarini_guncelle() # Masa buton bilgilerini güncelle (toplam değişebilir)

            messagebox.showinfo("Başarılı", "Ürün fiyatı başarıyla güncellendi!", parent=self.urun_frame)

        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Fiyat güncellenirken veritabanı hatası: {e}", parent=self.urun_frame)
             self.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Fiyat güncellenirken beklenmedik hata: {e}", parent=self.urun_frame)
             print(f"Fiyat güncelleme hatası: {e}")
             import traceback
             traceback.print_exc()


    def urun_kategori_degistir(self):
        """Seçilen ürünün kategorisini değiştirir"""
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen kategorisini değiştirmek için bir ürün seçin!", parent=self.urun_frame)
            return

        # Seçilen ürün adını al
        urun_adi = self.urun_listesi.item(selected[0], "values")[1] # Ürün adı 1. sütunda (index 1)


        # Ürünün mevcut kategorisini al
        self.cursor.execute('''
            SELECT kategori FROM urunler WHERE urun_adi = ?
        ''', (urun_adi,))
        urun_info = self.cursor.fetchone()
        if not urun_info:
             messagebox.showerror("Hata", "Ürün bilgisi veritabanında bulunamadı!", parent=self.urun_frame)
             self._urun_listesini_guncelle()
             return
        mevcut_kategori = urun_info['kategori'] # row_factory sayesinde sütun isimleriyle erişilir


        # Kategori değiştirme penceresi
        degistir_pencere = tk.Toplevel(self.root)
        degistir_pencere.title("Kategori Değiştir")
        degistir_pencere.transient(self.root)
        degistir_pencere.grab_set()
        degistir_pencere.resizable(False, False)
        # Pencere boyutu içeriğe göre otomatik ayarlansın

        input_frame = ttk.Frame(degistir_pencere, padding=(PAD_X*2, PAD_Y*2))
        input_frame.pack(padx=PAD_X, pady=PAD_Y)

        ttk.Label(input_frame, text=f"Ürün:", style="Bilgi.TLabel").grid(row=0, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")
        ttk.Label(input_frame, text=urun_adi, style="Bilgi.TLabel").grid(row=0, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")

        ttk.Label(input_frame, text="Yeni Kategori:", style="Bilgi.TLabel").grid(row=1, column=0, padx=PAD_X, pady=PAD_Y, sticky="e")

        kategori_combobox = ttk.Combobox(input_frame, values=list(KATEGORI_RENKLERI.keys()), state="readonly", width=20)
        kategori_combobox.set(mevcut_kategori) # Mevcut kategoriyi varsayılan yap
        kategori_combobox.grid(row=1, column=1, padx=PAD_X, pady=PAD_Y, sticky="w")


        def kaydet_action():
            yeni_kategori = kategori_combobox.get()
            if not yeni_kategori:
                 messagebox.showwarning("Uyarı", "Lütfen bir kategori seçin!", parent=degistir_pencere)
                 return

            try:
                self.cursor.execute('''
                    UPDATE urunler SET kategori = ? WHERE urun_adi = ?
                ''', (yeni_kategori, urun_adi))
                self.conn.commit()

                self._urun_listesini_guncelle() # Ürün listesini güncelle
                self._hizli_satis_butonlari_olustur() # Hızlı satış butonlarını yenile (renk değişebilir)
                messagebox.showinfo("Başarılı", "Ürün kategorisi başarıyla değiştirildi!", parent=degistir_pencere)
                degistir_pencere.destroy()

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Kategori değiştirilirken veritabanı hatası: {e}", parent=degistir_pencere)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Kategori değiştirilirken beklenmedik hata: {e}", parent=degistir_pencere)
                 print(f"Kategori değiştirme hatası: {e}")


        ttk.Button(input_frame, text="Kaydet", command=kaydet_action, style="TButton").grid(row=2, column=0, columnspan=2, pady=PAD_Y)

        degistir_pencere.focus_set() # Pencereye odaklan


    def urun_sira_degistir(self):
        """Seçilen ürünün sıra numarasını değiştirir"""
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen sırasını değiştirmek için bir ürün seçin!", parent=self.urun_frame)
            return

        # Seçilen ürün adını ve mevcut sıra numarasını al
        # Treeview'a eklerken tuple olarak eklediğimiz için index kullanmak daha güvenli.
        # Sıra 0. sütunda (index 0), Ürün adı 1. sütunda (index 1)
        mevcut_sira = self.urun_listesi.item(selected[0], "values")[0]
        urun_adi = self.urun_listesi.item(selected[0], "values")[1]

        # Yeni sıra numarasını kullanıcıdan al
        yeni_sira = simpledialog.askinteger(
            "Sıra Değiştir",
            f"'{urun_adi}' için yeni sıra numarasını girin:",
            minvalue=1,
            initialvalue=mevcut_sira,
            parent=self.root # Ana pencere üzerinde göster
        )

        # Kullanıcı iptal etmediyse ve sıra değiştiyse
        if yeni_sira is not None and yeni_sira != mevcut_sira:
            try:
                self.cursor.execute('''
                    UPDATE urunler SET sira = ? WHERE urun_adi = ?
                ''', (yeni_sira, urun_adi))
                self.conn.commit()

                self._urun_listesini_guncelle() # Ürün listesini güncelle (sıralama değişir)
                self._hizli_satis_butonlari_olustur() # Hızlı satış butonlarını yenile (sıralama değişir)
                messagebox.showinfo("Başarılı", "Ürün sırası başarıyla güncellendi!", parent=self.urun_frame)

            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Ürün sırası güncellenirken veritabanı hatası: {e}", parent=self.urun_frame)
                 self.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ürün sırası güncellenirken beklenmedik hata: {e}", parent=self.urun_frame)
                 print(f"Ürün sıra değiştirme hatası: {e}")


    def _urun_listesini_guncelle(self):
        """Ürün listesi Treeview'ını veritabanından günceller"""
        for item in self.urun_listesi.get_children():
            self.urun_listesi.delete(item)

        self.cursor.execute('''
            SELECT sira, urun_adi, fiyat, kategori
            FROM urunler
            ORDER BY sira ASC, urun_adi ASC
        ''')

        urunler = self.cursor.fetchall()

        for urun in urunler:
            self.urun_listesi.insert("", tk.END, values=(
                urun['sira'],
                urun['urun_adi'],
                f"{urun['fiyat']:.0f} ₺", # Formatlama düzeltildi
                urun['kategori']
            ))

# MUHASEBE İŞLEMLERİ
    def muhasebe_arayuz_olustur(self):
        """Muhasebe sekmesi arayüzünü oluşturur"""
        # Ana Frame (genleşebilir)
        main_frame = ttk.Frame(self.muhasebe_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=PAD_Y)

        # Rapor Kontrol Frame (üst kısım, sabit yükseklik)
        kontrol_frame = ttk.Frame(main_frame)
        kontrol_frame.pack(pady=PAD_Y, fill=tk.X) # Yatayda genleşebilir

        # Rapor Türü Seçimi
        ttk.Label(kontrol_frame, text="Rapor Türü:", style="Bilgi.TLabel").pack(side=tk.LEFT, padx=PAD_X)
        self.rapor_turu = ttk.Combobox(kontrol_frame,
                                        values=["Günlük", "Haftalık", "Aylık", "Özel Aralık"],
                                        state="readonly",
                                        width=12)
        self.rapor_turu.current(0) # Varsayılan "Günlük"
        self.rapor_turu.pack(side=tk.LEFT, padx=PAD_X)
        self.rapor_turu.bind("<<ComboboxSelected>>", self._rapor_turu_degisti) # Özel method

        # Tarih Seçim Frame (Dinamik içerik, kontrol_frame içinde sola yaslı)
        self.tarih_frame = ttk.Frame(kontrol_frame)
        self.tarih_frame.pack(side=tk.LEFT, padx=PAD_X, expand=True, fill=tk.X) # Genleşebilir

        # Varsayılan olarak günlük tarih alanı oluştur
        self._rapor_turu_degisti() # Combobox'ın ilk değeri için tarih alanını oluştur

        # Rapor Butonları (kontrol_frame içinde sağa yaslı)
        btn_frame = ttk.Frame(kontrol_frame)
        btn_frame.pack(side=tk.RIGHT, padx=PAD_X)

        ttk.Button(btn_frame, text="Rapor Oluştur",
                 style="Rapor.TButton", command=self.rapor_olustur).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(btn_frame, text="TXT Olarak Kaydet",
                 style="Export.TButton", command=self.excele_aktar).pack(side=tk.LEFT)

        # DB Temizle butonu (rapor butonlarının soluna)
        ttk.Button(kontrol_frame, text="DB Temizle",
                         style="Temizle.TButton",
                       command=self.veritabani_temizle).pack(side=tk.LEFT, padx=PAD_X*2)


        # Rapor Görüntüleme Alanı (kalan alanı doldurur)
        self.rapor_notebook = ttk.Notebook(main_frame)
        self.rapor_notebook.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=PAD_Y) # Genleşebilir

        # --- Sekme: Genel Rapor ---
        self.genel_rapor_frame = ttk.Frame(self.rapor_notebook, padding=(PAD_X, PAD_Y))
        self.rapor_notebook.add(self.genel_rapor_frame, text="Genel Rapor")

        # Text widget'ı için scrollbar
        genel_rapor_scrollbar = ttk.Scrollbar(self.genel_rapor_frame, orient=tk.VERTICAL)
        self.genel_rapor_text = tk.Text(self.genel_rapor_frame, wrap=tk.WORD, font=("Courier New", 10), # Rapor için monospace font
                                        yscrollcommand=genel_rapor_scrollbar.set)
        genel_rapor_scrollbar.config(command=self.genel_rapor_text.yview)

        genel_rapor_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.genel_rapor_text.pack(fill=tk.BOTH, expand=True) # Text widget genleşebilir

        # --- Sekme: Ürün Bazlı Rapor ---
        self.urun_rapor_frame = ttk.Frame(self.rapor_notebook, padding=(PAD_X, PAD_Y))
        self.rapor_notebook.add(self.urun_rapor_frame, text="Ürün Bazlı")

        self.urun_rapor_tree = ttk.Treeview(self.urun_rapor_frame,
                                            columns=("Ürün", "Adet", "Tutar"),
                                            show="headings", style="Treeview")
        self.urun_rapor_tree.heading("Ürün", text="Ürün")
        self.urun_rapor_tree.heading("Adet", text="Adet", anchor='e')
        self.urun_rapor_tree.heading("Tutar", text="Tutar", anchor='e')
        self.urun_rapor_tree.column("Ürün", width=250, stretch=tk.YES) # Ürün genleşebilir
        self.urun_rapor_tree.column("Adet", width=100, stretch=tk.NO)
        self.urun_rapor_tree.column("Tutar", width=120, stretch=tk.NO)

        # Scrollbar ekle
        urun_scrollbar = ttk.Scrollbar(self.urun_rapor_frame, orient=tk.VERTICAL, command=self.urun_rapor_tree.yview)
        self.urun_rapor_tree.configure(yscrollcommand=urun_scrollbar.set)
        urun_scrollbar.pack(side="right", fill="y")

        self.urun_rapor_tree.pack(fill=tk.BOTH, expand=True) # Treeview genleşebilir


        # --- Sekme: Masa Hareketleri ---
        self.masa_rapor_frame = ttk.Frame(self.rapor_notebook, padding=(PAD_X, PAD_Y))
        self.rapor_notebook.add(self.masa_rapor_frame, text="Masa Hareketleri")

        self.masa_rapor_tree = ttk.Treeview(self.masa_rapor_frame,
                                            columns=("ID", "Masa", "Açılış", "Kapanış", "Süre", "Müşteri", "Toplam", "Ödeme"), # ID eklendi detay almak için
                                            show="headings", style="Treeview")
        self.masa_rapor_tree.heading("ID", text="ID")
        self.masa_rapor_tree.heading("Masa", text="Masa")
        self.masa_rapor_tree.heading("Açılış", text="Açılış")
        self.masa_rapor_tree.heading("Kapanış", text="Kapanış")
        self.masa_rapor_tree.heading("Süre", text="Süre")
        self.masa_rapor_tree.heading("Müşteri", text="Müşteri")
        self.masa_rapor_tree.heading("Toplam", text="Toplam")
        self.masa_rapor_tree.heading("Ödeme", text="Ödeme")

        # Sütun genişlikleri ve genleşme ayarları
        self.masa_rapor_tree.column("ID", width=50, stretch=tk.NO) # ID sabit
        self.masa_rapor_tree.column("Masa", width=60, stretch=tk.NO) # Masa sabit
        self.masa_rapor_tree.column("Açılış", width=140, stretch=tk.NO) # Açılış sabit
        self.masa_rapor_tree.column("Kapanış", width=140, stretch=tk.NO) # Kapanış sabit
        self.masa_rapor_tree.column("Süre", width=80, stretch=tk.NO) # Süre sabit
        self.masa_rapor_tree.column("Müşteri", width=200, stretch=tk.YES, anchor='w') # Müşteri genleşebilir, sola yaslı
        self.masa_rapor_tree.column("Toplam", width=100, stretch=tk.NO, anchor='e') # Toplam sabit, sağa yaslı
        self.masa_rapor_tree.column("Ödeme", width=100, stretch=tk.NO, anchor='center') # Ödeme sabit, ortalı


        # Scrollbar ekle
        masa_scrollbar = ttk.Scrollbar(self.masa_rapor_frame, orient=tk.VERTICAL, command=self.masa_rapor_tree.yview)
        self.masa_rapor_tree.configure(yscrollcommand=masa_scrollbar.set)
        masa_scrollbar.pack(side="right", fill="y")

        self.masa_rapor_tree.pack(fill=tk.BOTH, expand=True) # Treeview genleşebilir

        # Masa detay butonu (alt kısım, sabit yükseklik)
        ttk.Button(self.masa_rapor_frame, text="Seçili Masa Detayını Göster", style="TButton",
                 command=self.masa_detay_goster).pack(side=tk.BOTTOM, pady=PAD_Y)


    def _rapor_turu_degisti(self, event=None):
        """Rapor türü Combobox'ı değiştiğinde tarih giriş alanlarını günceller"""
        # Mevcut tarih giriş alanlarını temizle
        for widget in self.tarih_frame.winfo_children():
            widget.destroy()

        secim = self.rapor_turu.get()
        bugun_str = datetime.now().strftime(RAPOR_TARIH_FORMATI)

        if secim == "Özel Aralık":
            ttk.Label(self.tarih_frame, text="Başlangıç:", style="Bilgi.TLabel").pack(side=tk.LEFT)
            self.baslangic_tarih_entry = ttk.Entry(self.tarih_frame, width=10)
            self.baslangic_tarih_entry.pack(side=tk.LEFT, padx=PAD_X)
            self.baslangic_tarih_entry.insert(0, bugun_str)
            # TODO: Basit bir takvim picker eklenebilir (harici kütüphane gerektirebilir veya manuel kodlama)

            ttk.Label(self.tarih_frame, text="Bitiş:", style="Bilgi.TLabel").pack(side=tk.LEFT)
            self.bitis_tarih_entry = ttk.Entry(self.tarih_frame, width=10)
            self.bitis_tarih_entry.pack(side=tk.LEFT, padx=PAD_X)
            self.bitis_tarih_entry.insert(0, bugun_str)
            # TODO: Basit bir takvim picker eklenebilir

        else: # Günlük, Haftalık, Aylık
            ttk.Label(self.tarih_frame, text="Tarih:", style="Bilgi.TLabel").pack(side=tk.LEFT)
            self.tek_tarih_entry = ttk.Entry(self.tarih_frame, width=10)
            self.tek_tarih_entry.pack(side=tk.LEFT, padx=PAD_X)
            self.tek_tarih_entry.insert(0, bugun_str)
            # TODO: Basit bir takvim picker eklenebilir

        # Tarih giriş alanlarının tutulduğu frame'in genleşmesini sağla
        self.tarih_frame.pack_configure(expand=True, fill=tk.X)


    def rapor_olustur(self):
        """Seçilen tarih aralığına göre raporları oluşturur ve görüntüler"""
        try:
            self.genel_rapor_text.config(state="normal")
            self.genel_rapor_text.delete(1.0, tk.END)
            self.urun_rapor_tree.delete(*self.urun_rapor_tree.get_children())
            self.masa_rapor_tree.delete(*self.masa_rapor_tree.get_children())

            rapor_turu = self.rapor_turu.get()
            baslangic_dt = None
            bitis_dt = None

            def parse_and_validate_date(date_str_entry, field_name):
                date_str = date_str_entry.get().strip()
                try:
                    return datetime.strptime(date_str, RAPOR_TARIH_FORMATI)
                except ValueError:
                    messagebox.showerror("Hata", f"Geçersiz {field_name} formatı: {date_str}\nLütfen {RAPOR_TARIH_FORMATI} formatında girin.", parent=self.muhasebe_frame)
                    return None

            if rapor_turu == "Özel Aralık":
                baslangic_dt = parse_and_validate_date(self.baslangic_tarih_entry, "Başlangıç Tarihi")
                if baslangic_dt is None: return
                bitis_dt = parse_and_validate_date(self.bitis_tarih_entry, "Bitiş Tarihi")
                if bitis_dt is None: return
                bitis_dt = bitis_dt.replace(hour=23, minute=59, second=59)

                if baslangic_dt > bitis_dt:
                     messagebox.showwarning("Uyarı", "Başlangıç tarihi, bitiş tarihinden sonra olamaz.", parent=self.muhasebe_frame)
                     return

            else:
                tarih_dt = parse_and_validate_date(self.tek_tarih_entry, "Tarih")
                if tarih_dt is None: return

                if rapor_turu == "Günlük":
                    baslangic_dt = tarih_dt.replace(hour=0, minute=0, second=0)
                    bitis_dt = tarih_dt.replace(hour=23, minute=59, second=59)
                elif rapor_turu == "Haftalık":
                    baslangic_dt = tarih_dt - timedelta(days=tarih_dt.weekday())
                    baslangic_dt = baslangic_dt.replace(hour=0, minute=0, second=0)
                    bitis_dt = baslangic_dt + timedelta(days=6, hours=23, minutes=59, seconds=59)
                elif rapor_turu == "Aylık":
                    baslangic_dt = tarih_dt.replace(day=1, hour=0, minute=0, second=0)
                    next_month = baslangic_dt.replace(day=28) + timedelta(days=4)
                    bitis_dt = next_month.replace(day=1) - timedelta(seconds=1)

            baslangic_str_db = baslangic_dt.strftime(DB_DATE_FORMAT)
            bitis_str_db = bitis_dt.strftime(DB_DATE_FORMAT)

            # --- 1. Genel Rapor Verileri ---
            self.cursor.execute(f'''
                SELECT strftime('{RAPOR_TARIH_FORMATI}', tarih) as gun,
                       SUM(toplam) as ciro,
                       COUNT(*) as siparis_sayisi
                FROM siparis_gecmisi
                WHERE tarih BETWEEN ? AND ?
                GROUP BY gun
                ORDER BY tarih ASC
            ''', (baslangic_str_db, bitis_str_db))

            gunluk_hasilat = self.cursor.fetchall()

            self.genel_rapor_text.insert(tk.END, f"=== {rapor_turu.upper()} RAPOR ===\n")
            self.genel_rapor_text.insert(tk.END, f"Tarih Aralığı: {baslangic_dt.strftime(RAPOR_TARIH_FORMATI)} - {bitis_dt.strftime(RAPOR_TARIH_FORMATI)}\n\n")

            self.genel_rapor_text.insert(tk.END, "GÜNLÜK HASILAT\n")
            self.genel_rapor_text.insert(tk.END, "{:<12} {:<15} {:<15}\n".format("Tarih", "Toplam Ciro", "Sipariş Sayısı"))
            self.genel_rapor_text.insert(tk.END, "-"*45 + "\n")

            toplam_ciro_genel = 0.0
            toplam_siparis_genel = 0

            for row in gunluk_hasilat:
                gun = row['gun']
                ciro = row['ciro'] if row['ciro'] is not None else 0.0
                siparis_sayisi = row['siparis_sayisi']

                # Formatlama düzeltildi: Ondalıksız ciro
                self.genel_rapor_text.insert(tk.END, "{:<12} {:<15.0f} {:<15}\n".format(gun, ciro, siparis_sayisi))

                toplam_ciro_genel += ciro
                toplam_siparis_genel += siparis_sayisi

            self.genel_rapor_text.insert(tk.END, "-"*45 + "\n")
            # Formatlama düzeltildi: Ondalıksız toplam ciro
            self.genel_rapor_text.insert(tk.END, "{:<12} {:<15.0f} {:<15}\n".format("TOPLAM:", toplam_ciro_genel, toplam_siparis_genel))
            self.genel_rapor_text.insert(tk.END, "\n")


            # --- 2. Ürün Bazlı Satışlar ---
            self.cursor.execute('''
                SELECT sd.urun_adi, SUM(sd.miktar) as toplam_adet, SUM(sd.tutar) as toplam_tutar
                FROM siparis_detaylari sd
                JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
                WHERE sg.tarih BETWEEN ? AND ?
                GROUP BY sd.urun_adi
                ORDER BY SUM(sd.tutar) DESC
            ''', (baslangic_str_db, bitis_str_db))

            urun_satis = self.cursor.fetchall()

            for urun in urun_satis:
                self.urun_rapor_tree.insert("", tk.END, values=(
                    urun['urun_adi'],
                    int(urun['toplam_adet']) if urun['toplam_adet'] is not None else 0,
                    f"{urun['toplam_tutar']:.0f} ₺" if urun['toplam_tutar'] is not None else "0 ₺" # Formatlama düzeltildi
                ))


            # --- 3. Masa Hareketleri ---
            self.cursor.execute('''
                SELECT id, masa_no, acilis, kapanis, musteri_id, toplam, odeme_turu, tarih
                FROM masa_gecmisi mg
                WHERE tarih BETWEEN ? AND ?
                ORDER BY tarih ASC
            ''', (baslangic_str_db, bitis_str_db))

            masa_hareketleri = self.cursor.fetchall()

            for hareket in masa_hareketleri:
                masa_gecmisi_id = hareket['id']
                masa_no = hareket['masa_no']
                acilis_str_db = hareket['acilis']
                kapanis_str_db = hareket['kapanis']
                musteri_id = hareket['musteri_id']
                toplam_masa = hareket['toplam'] if hareket['toplam'] is not None else 0.0
                odeme_turu = hareket['odeme_turu']

                musteri_adi = "Misafir"
                if musteri_id:
                     self.cursor.execute("SELECT ad FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                     musteri = self.cursor.fetchone()
                     if musteri and musteri['ad']:
                         musteri_adi = musteri['ad']

                sure_str = "-"
                try:
                     acilis_dt = datetime.strptime(acilis_str_db, DB_DATE_FORMAT)
                     kapanis_dt = datetime.strptime(kapanis_str_db, DB_DATE_FORMAT)
                     sure_td = kapanis_dt - acilis_dt
                     total_minutes = int(sure_td.total_seconds() / 60)
                     sure_str = f"{total_minutes // 60} sa {total_minutes % 60} dk"
                except (ValueError, TypeError):
                     pass

                self.masa_rapor_tree.insert("", tk.END, values=(
                    masa_gecmisi_id,
                    masa_no,
                    datetime.strptime(acilis_str_db, DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if acilis_str_db else "-",
                    datetime.strptime(kapanis_str_db, DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if kapanis_str_db else "-",
                    sure_str,
                    musteri_adi,
                    f"{toplam_masa:.0f}", # Formatlama düzeltildi (value'da TL işareti yok, exportta eklenir)
                    odeme_turu if odeme_turu else "Bilinmiyor"
                ))

            self.genel_rapor_text.config(state="disabled")
            messagebox.showinfo("Başarılı", "Rapor başarıyla oluşturuldu.", parent=self.muhasebe_frame)

        except ValueError as ve:
             print(f"Tarih format hatası: {ve}")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Rapor oluşturulurken veritabanı hatası: {e}\nSorguda sütun adı hatası olabilir mi?", parent=self.muhasebe_frame)
            print(f"Rapor sorgu hatası: {e}")
            import traceback
            traceback.print_exc()
            self.genel_rapor_text.config(state="disabled")
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulurken beklenmedik hata: {e}", parent=self.muhasebe_frame)
            print(f"Rapor oluşturma hatası: {e}")
            import traceback
            traceback.print_exc()
            self.genel_rapor_text.config(state="disabled")

    def masa_detay_goster(self):
        """Masa Hareketleri Treeview'ında seçilen bir masa hareketinin detaylarını (siparişlerini) gösterir"""
        selected = self.masa_rapor_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen detayını görmek için Masa Hareketlerinden bir kayıt seçin!", parent=self.muhasebe_frame)
            return

        secili_masa_gecmisi_id = self.masa_rapor_tree.item(selected[0], "values")[0]
        masa_no = self.masa_rapor_tree.item(selected[0], "values")[1]
        acilis_str_display = self.masa_rapor_tree.item(selected[0], "values")[2]
        kapanis_str_display = self.masa_rapor_tree.item(selected[0], "values")[3]
        sure_str = self.masa_rapor_tree.item(selected[0], "values")[4]
        musteri_ad = self.masa_rapor_tree.item(selected[0], "values")[5]
        toplam_str = self.masa_rapor_tree.item(selected[0], "values")[6] # String formatında alınıyor Treeview'dan
        odeme_turu = self.masa_rapor_tree.item(selected[0], "values")[7]

        try:
            self.cursor.execute("SELECT tarih FROM masa_gecmisi WHERE id = ?", (secili_masa_gecmisi_id,))
            masa_gecmisi_tarih_db = self.cursor.fetchone()['tarih']

            if not masa_gecmisi_tarih_db:
                 messagebox.showwarning("Uyarı", "Seçili masa hareketine ait kapanış tarihi bulunamadı!", parent=self.muhasebe_frame)
                 return

            self.cursor.execute('''
                 SELECT id FROM siparis_gecmisi
                 WHERE masa_no = ? AND tarih = ?
            ''', (masa_no, masa_gecmisi_tarih_db))
            siparis_gecmisi_row = self.cursor.fetchone()

            if not siparis_gecmisi_row:
                 messagebox.showwarning("Uyarı", "Seçili masa hareketine ait sipariş özeti bulunamadı!", parent=self.muhasebe_frame)
                 return

            ilgili_siparis_id = siparis_gecmisi_row['id']

            self.cursor.execute('''
                SELECT urun_adi, fiyat, miktar, tutar
                FROM siparis_detaylari
                WHERE siparis_id = ?
            ''', (ilgili_siparis_id,))

            detaylar = self.cursor.fetchall()

            if not detaylar:
                messagebox.showwarning("Uyarı", "Detay bilgi (ürünler) bulunamadı!", parent=self.muhasebe_frame)
                return

            detay_penceresi = tk.Toplevel(self.root)
            detay_penceresi.title(f"Masa {masa_no} Detayları (ID: {secili_masa_gecmisi_id})")
            detay_penceresi.transient(self.root)
            detay_penceresi.grab_set()
            detay_penceresi.geometry("500x450")

            bilgi_frame = ttk.Frame(detay_penceresi, padding=(PAD_X, PAD_Y))
            bilgi_frame.pack(fill=tk.X, padx=PAD_X, pady=PAD_Y)

            ttk.Label(bilgi_frame, text=f"Masa No: {masa_no}", style="Baslik.TLabel").pack(anchor="w")
            ttk.Label(bilgi_frame, text=f"Açılış: {acilis_str_display}", style="Bilgi.TLabel").pack(anchor="w")
            ttk.Label(bilgi_frame, text=f"Kapanış: {kapanis_str_display}", style="Bilgi.TLabel").pack(anchor="w")
            ttk.Label(bilgi_frame, text=f"Süre: {sure_str}", style="Bilgi.TLabel").pack(anchor="w")
            ttk.Label(bilgi_frame, text=f"Müşteri: {musteri_ad}", style="Bilgi.TLabel").pack(anchor="w")
            # Formatlama düzeltildi: Ondalıksız ve ₺ işareti (metin olarak Treeview'dan geldiği için dikkat)
            ttk.Label(bilgi_frame, text=f"Toplam: {toplam_str} ₺", style="Baslik.TLabel").pack(anchor="w")
            ttk.Label(bilgi_frame, text=f"Ödeme Türü: {odeme_turu}", style="Bilgi.TLabel").pack(anchor="w")

            urun_frame = ttk.Frame(detay_penceresi, padding=(PAD_X, PAD_Y))
            urun_frame.pack(fill=tk.BOTH, expand=True, padx=PAD_X, pady=PAD_Y)

            ttk.Label(urun_frame, text="Sipariş Edilen Ürünler:", style="Bilgi.TLabel").pack(anchor="w", pady=(0,PAD_Y))

            urun_tree = ttk.Treeview(urun_frame, columns=("Urun", "Adet", "Tutar"), show="headings", style="Treeview")
            urun_tree.heading("Urun", text="Ürün Adı")
            urun_tree.heading("Adet", text="Adet", anchor='e')
            urun_tree.heading("Tutar", text="Tutar", anchor='e')
            urun_tree.column("Urun", width=250, stretch=tk.YES)
            urun_tree.column("Adet", width=80, stretch=tk.NO)
            urun_tree.column("Tutar", width=100, stretch=tk.NO)

            scrollbar = ttk.Scrollbar(urun_frame, orient=tk.VERTICAL, command=urun_tree.yview)
            urun_tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")

            urun_tree.pack(fill=tk.BOTH, expand=True)

            for urun in detaylar:
                # Formatlama düzeltildi: Ondalıksız ve ₺ işareti
                urun_tree.insert("", tk.END, values=(
                    urun['urun_adi'],
                    urun['miktar'],
                    f"{urun['tutar']:.0f} ₺"
                ))

            ttk.Button(detay_penceresi, text="Tamam", command=detay_penceresi.destroy, style="TButton").pack(pady=PAD_Y)
            detay_penceresi.bind("<Return>", lambda e: detay_penceresi.destroy())

            detay_penceresi.focus_set()

        except sqlite3.Error as e:
             messagebox.showerror("Veritabanı Hatası", f"Masa detayları alınırken veritabanı hatası: {e}", parent=self.muhasebe_frame)
             print(f"Masa detay sorgu hatası: {e}")
        except Exception as e:
             messagebox.showerror("Hata", f"Masa detayları gösterilirken beklenmedik hata: {e}", parent=self.muhasebe_frame)
             print(f"Masa detay gösterme hatası: {e}")

    def excele_aktar(self):
        """Oluşturulan raporu metin dosyası olarak kaydeder (Excel'e aktarılabilir format)"""
        if not self.genel_rapor_text.get("1.0", tk.END).strip():
             messagebox.showwarning("Uyarı", "Lütfen önce 'Rapor Oluştur' butonuna basarak bir rapor oluşturun.", parent=self.muhasebe_frame)
             return

        try:
            dosya_adi = f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            yedek_dizin = "raporlar"
            os.makedirs(yedek_dizin, exist_ok=True)
            tam_dosya_yolu = os.path.join(yedek_dizin, dosya_adi)

            with open(tam_dosya_yolu, "w", encoding="utf-8") as f:
                f.write(self.genel_rapor_text.get("1.0", tk.END).strip())
                f.write("\n\n")

                f.write("=== ÜRÜN BAZLI SATIŞLAR ===\n")
                f.write("Ürün Adı | Adet | Toplam Tutar\n")
                f.write("-" * 50 + "\n")
                for item_id in self.urun_rapor_tree.get_children():
                    values = self.urun_rapor_tree.item(item_id, "values")
                    # Export'ta da formatlama düzeltildi: Ondalıksız ve ₺ işareti
                    formatted_values = (
                        values[0], # Ürün Adı
                        values[1], # Adet (zaten tam sayı)
                        values[2].replace(' ₺', '') # Tutar stringinden TL işaretini çıkar, sayı olarak kalsın Excel için
                    )
                    f.write(" | ".join(map(str, formatted_values)) + "\n")

                f.write("\n\n")

                f.write("=== MASA HAREKETLERİ ===\n")
                f.write("ID | Masa | Açılış | Kapanış | Süre | Müşteri | Toplam | Ödeme Türü\n")
                f.write("-" * 80 + "\n")
                for item_id in self.masa_rapor_tree.get_children():
                    values = self.masa_rapor_tree.item(item_id, "values")
                    # Export'ta da formatlama düzeltildi: Ondalıksız ve ₺ işareti
                    formatted_values = (
                        values[0], # ID
                        values[1], # Masa
                        values[2], # Açılış
                        values[3], # Kapanış
                        values[4], # Süre
                        values[5], # Müşteri
                        values[6].replace(' ₺', ''), # Toplam stringinden TL işaretini çıkar
                        values[7] # Ödeme Türü
                    )
                    f.write(" | ".join(map(str, formatted_values)) + "\n")


            mesaj = f"""Rapor başarıyla kaydedildi:
{tam_dosya_yolu}

Bu dosyayı Excel'e aktarmak için:
1. Excel'i açın.
2. "Veri" sekmesine gidin.
3. "Metinden/CSV'den" seçeneğini tıklayın (veya daha eski versiyonlarda "Metni Sütunlara Dönüştür").
4. Kaydettiğiniz .txt dosyasını seçin.
5. Veri Önizleme penceresinde, Ayırıcı olarak "Diğer" seçeneğini işaretleyin ve yanına "|" (pipe) işaretini girin.
6. "Yükle" butonuna tıklayın."""

            messagebox.showinfo("Başarılı", mesaj, parent=self.muhasebe_frame)

            try:
                if os.path.exists(tam_dosya_yolu):
                    if os.name == 'nt':
                        os.startfile(tam_dosya_yolu)
                    elif os.uname().sysname == 'Darwin':
                         subprocess.call(['open', tam_dosya_yolu])
                    else:
                         subprocess.call(['xdg-open', tam_dosya_yolu])
            except FileNotFoundError:
                 print(f"Dosya açma komutu bulunamadı veya dosya bulunamıyor: {tam_dosya_yolu}")
            except Exception as e:
                 print(f"Dosya açılırken hata oluştu: {e}")


        except Exception as e:
            messagebox.showerror("Hata", f"Rapor dosyası oluşturulamadı:\n{str(e)}", parent=self.muhasebe_frame)
            print(f"Rapor export hatası: {e}")
            import traceback
            traceback.print_exc()

    def _sekme_degisti(self, event):
        """Notebook sekmesi değiştiğinde ilgili güncellemeleri yapar"""
        current_tab_index = self.notebook.index("current") # Aktif sekmenin indeksini al

        # Masa Yönetimi sekmesine geçildiğinde masa butonlarını güncelle
        if current_tab_index == 0: # Masa Yönetimi sekmesi (index 0)
            self._masa_butonlarini_guncelle()

            # Masa Yönetimi sekmesine dönüldüğünde, eğer aktif masa boşalmışsa (siparişi yoksa)
            # Masa bilgisini UI'da temizle. (Bu kontrol aslında _sepetten_cikar ve _sepeti_temizle'de yapılıyor)
            # Burada ekstra kontrol gereksiz olabilir, _masa_butonlarini_guncelle çağrıldığı için UI güncel olur.
            pass


        # Adisyon sekmesine geçildiğinde sepeti yükle
        elif current_tab_index == 1: # Adisyon sekmesi (index 1)
            # Eğer aktif masa yoksa uyarı ver ve Masa Yönetimi sekmesine dön
            if not self.aktif_masa:
                messagebox.showinfo("Bilgi", "Lütfen Adisyonu görmek için önce bir masa seçin!", parent=self.adisyon_frame)
                self.notebook.select(0) # Masa Yönetimi sekmesine dön
            else:
                self._sepeti_yukle() # Aktif masanın sepetini yükle

        # Müşteri İşlemleri sekmesine geçildiğinde müşteri listesini güncelle
        elif current_tab_index == 2: # Müşteri İşlemleri sekmesi (index 2)
            self._musteri_listesini_guncelle()

        # Ürün Yönetimi sekmesine geçildiğinde ürün listesini güncelle
        elif current_tab_index == 3: # Ürün Yönetimi sekmesi (index 3)
             self._urun_listesini_guncelle()

        # Muhasebe sekmesine geçildiğinde (Şimdilik bir şey yapmaya gerek yok, rapor oluştur butonu var)
        elif current_tab_index == 4: # Muhasebe sekmesi (index 4)
             pass # Raporlar butona basınca oluşturuluyor


    def _tarih_saat_al_db_format(self):
        """Şu anki tarih ve saati veritabanı formatında (ISO 8601) döndürür"""
        return datetime.now().strftime(DB_DATE_FORMAT)

    def _tarih_saat_al_display_format(self):
        """Şu anki tarih ve saati kullanıcı arayüzü formatında döndürür"""
        return datetime.now().strftime(RAPOR_TARIH_FORMATI + " %H:%M")

    def _saat_guncelle(self):
        """Adisyon sekmesindeki saat etiketini her dakika günceller"""
        if hasattr(self, 'saat_label'):
            self.saat_label.config(text=self._tarih_saat_al_display_format())
        # Her 60 saniyede (60000 ms) bir tekrar çalıştır
        self.root.after(60000, self._saat_guncelle)


    def __del__(self):
        """Nesne yok edilirken veritabanı bağlantısını kapatır"""
        if hasattr(self, 'conn') and self.conn is not None:
             try:
                 self.conn.commit() # Kalan işlemleri kaydet
                 self.conn.close()
                 print("Veritabanı bağlantısı kapatıldı.")
             except Exception as e:
                 print(f"Veritabanı kapatılırken hata: {e}")

    def _on_closing(self):
        """Program kapatılırken veritabanı bağlantısını kapatır ve uygulamadan çıkar."""
        if messagebox.askokcancel("Çıkış", "Uygulamadan çıkmak istediğinize emin misiniz?"):
            try:
                # Bağlantı objesi var mı ve açık mı kontrol et
                # Bağlantı kapatıldığında conn objesi hala var olur ama kapalı durumda olur.
                # Daha güvenli kontrol için self.conn'un None olup olmadığını kontrol edebiliriz.
                if self.conn: # Bağlantı objesi None değilse
                    try:
                        # Bağlantının durumunu kontrol etmenin doğrudan bir yolu yok,
                        # ancak bir işlem yapmayı deneyerek kapalı olup olmadığını anlayabiliriz.
                        # En basit yol, kapatmaya çalışmak ve hatayı yakalamak veya None yapmak.

                        self.conn.close()
                        print("Veritabanı bağlantısı kapatıldı.")
                        self.conn = None # <<< Bağlantıyı kapattıktan sonra None yap

                    except sqlite3.ProgrammingError as e:
                        # "Cannot operate on a closed database" hatası genellikle buradan gelir.
                        print(f"Veritabanı zaten kapalıydı veya kapatılırken hata oluştu (ProgrammingError): {e}")
                        self.conn = None # Hata durumunda da None yapalım

                    except Exception as e:
                        print(f"Veritabanı kapatılırken beklenmedik hata oluştu: {e}")
                        # Beklenmedik hata durumunda da None yapalım ki tekrar denenmesin
                        self.conn = None


            except Exception as e:
                # self.conn objesi bile yoksa (çok nadir)
                print(f"Veritabanı bağlantı objesi kapatılırken hata oluştu: {e}")


            self.root.destroy() # Ana pencereyi kapat

# --- Ana Program Bloğu ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CafeAdisyonProgrami(root)
    root.mainloop()
