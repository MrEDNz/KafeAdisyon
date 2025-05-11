import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import os
from datetime import datetime, timedelta
import subprocess # Dosya açmak için
import sys # Sistem bilgisi için

# Sabitler (Constants)
DB_DATE_FORMAT = "%Y-%m-%d %H:%M:%S" # Veritabanında kullanılacak ISO tarih formatı
RAPOR_TARIH_FORMATI = "%d.%m.%Y" # Raporlarda ve UI'da gösterilecek tarih formatı
PAD_X = 10 # Yatay boşluk
PAD_Y = 10 # Dikey boşluk
MASA_BTN_WIDTH = 12 # Masa butonu genişliği
MASA_BTN_HEIGHT = 5 # Masa butonu yüksekliği
INACTIVITY_THRESHOLD_MIN = 30 # Masa bekleme süresi (dakika)

# Renk Tanımları
RENK_BOS_MASA = "#a8d5ba" # Açık yeşil
RENK_DOLU_MASA = "#f7b267" # Turuncu
RENK_MUSTERILI_MASA = "#a2d2ff" # Açık mavi
RENK_BEKLEYEN_MASA = "#e56b6f" # Kırmızı
RENK_BUTON_MASA_YONETIM = "#f7b267" # Turuncu
RENK_BUTON_ODEME = "#f0c808" # Sarı
RENK_BUTON_KAPAT = "#d9534f" # Kırmızı
RENK_BUTON_ARA_ODEME = "#5bc0de" # Mavi
RENK_BUTON_EKLE_CIKAR = "#90be6d" # Yeşil
RENK_BUTON_YONETIM = "#f8f9fa" # Beyazımsı
RENK_BUTON_RAPOR = "#4CAF50" # Yeşil
RENK_BUTON_EXPORT = "#2196F3" # Mavi
RENK_BUTON_TEMIZLE = "#f44336" # Kırmızı

# Kategori Renkleri (Örnek - Kendi kategorilerinize göre ayarlayın)
KATEGORI_RENKLERI = {
    "Sıcak İçecekler": "#ffadad",
    "Soğuk İçecekler": "#9de0fe",
    "Kahveler": "#fcf6bd",
    "Pastalar": "#d8a4f7",
    "Yiyecekler": "#a0c4ff",
    "Diğer": "#bdb2ff",
    "Tümü": "#cccccc" # 'Tümü' kategorisi için varsayılan renk
}

# Metin rengini arkaplan rengine göre otomatik belirleme
def get_text_color(bg_color):
    """Arkaplan rengine göre okunabilir siyah veya beyaz metin rengi döndürür."""
    # Basit bir parlaklık hesaplaması (RGB değerlerinin ortalaması)
    # Tkinter renk isimlerini RGB'ye çevirmek daha karmaşık olabilir,
    # şimdilik sadece hex renk kodları için çalışır.
    try:
        bg_color = bg_color.lstrip('#')
        r, g, b = int(bg_color[0:2], 16), int(bg_color[2:4], 16), int(bg_color[4:6], 16)
        luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "black" if luminance > 0.5 else "white"
    except:
        return "black" # Hata durumunda varsayılan siyah


# Varsayılan ürün listesi (Uygulama ilk çalıştığında ve ürünler tablosu boşsa kullanılır)
default_products = [
    {'sira': 1, 'urun_adi': 'Türk Kahvesi', 'fiyat': 30.0, 'kategori': 'Kahveler'},
    {'sira': 2, 'urun_adi': 'Çay', 'fiyat': 20.0, 'kategori': 'Sıcak İçecekler'},
    {'sira': 3, 'urun_adi': 'Espresso', 'fiyat': 40.0, 'kategori': 'Kahveler'},
    {'sira': 4, 'urun_adi': 'Latte', 'fiyat': 45.0, 'kategori': 'Kahveler'},
    {'sira': 5, 'urun_adi': 'Mocha', 'fiyat': 50.0, 'kategori': 'Kahveler'},
    {'sira': 6, 'urun_adi': 'Limonata', 'fiyat': 30.0, 'kategori': 'Soğuk İçecekler'},
    {'sira': 7, 'urun_adi': 'Portakal Suyu', 'fiyat': 35.0, 'kategori': 'Soğuk İçecekler'},
    {'sira': 8, 'urun_adi': 'Ayran', 'fiyat': 25.0, 'kategori': 'Soğuk İçecekler'},
    {'sira': 9, 'urun_adi': 'Su', 'fiyat': 15.0, 'kategori': 'Soğuk İçecekler'},
    {'sira': 10, 'urun_adi': 'Cheesecake', 'fiyat': 60.0, 'kategori': 'Pastalar'},
    {'sira': 11, 'urun_adi': 'Tiramisu', 'fiyat': 55.0, 'kategori': 'Pastalar'},
    {'sira': 12, 'urun_adi': 'Sandviç', 'fiyat': 70.0, 'kategori': 'Yiyecekler'},
    {'sira': 13, 'urun_adi': 'Salata', 'fiyat': 65.0, 'kategori': 'Yiyecekler'},
    # ... (Diğer ürünleriniz buraya gelecek) ...
]

# Varsayılan masa sayısı
DEFAULT_MASA_SAYISI = 10


class CafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Cafe Adisyon Sistemi")
        self.root.geometry("1200x800")

        self.style = ttk.Style()
        self._configure_styles()

        # Veritabanı bağlantısı
        self.db_file = 'cafe.db' # Veritabanı dosya adını sakla
        self.conn = None
        self.cursor = None
        self._veritabani_baglantisi_kur() # Bağlantıyı kur

        self._veritabani_tablolarini_olustur() # Tabloları oluştur

        # musteriler tablosuna cumulative_balance sütununu ekle (Savunma amaçlı tekrar kontrol)
        try:
            self.cursor.execute("SELECT cumulative_balance FROM musteriler LIMIT 1")
            # print("musteriler tablosunda cumulative_balance sütunu mevcut.") # Çok sık mesaj vermesin
        except sqlite3.OperationalError:
            print("musteriler tablosunda cumulative_balance sütunu eksik, ekleniyor...")
            try:
                self.cursor.execute("ALTER TABLE musteriler ADD COLUMN cumulative_balance REAL DEFAULT 0.0")
                self.conn.commit()
                print("cumulative_balance sütunu başarıyla eklendi.")
            except sqlite3.Error as e:
                print(f"Hata: musteriler tablosuna cumulative_balance sütunu eklenirken veritabanı hatası: {e}")
                self.conn.rollback()
        except Exception as e:
             print(f"cumulative_balance sütunu kontrol edilirken beklenmedik hata: {e}")


        # Yedek alırken db_file kullanılır, bu yüzden db_file tanımından sonra çağrılmalı
        self._yedek_al()

        # Başlangıç değişkenleri
        self.aktif_masa = None
        self.current_mode = "normal" # Uygulama modunu takip et (normal, assign_customer vb.)
        self.secili_musteri_id = None # Müşteri işlemleri sekmesinde seçili müşteri ID'si
        self.toplam_tutar = 0.0 # Adisyon sekmesinde anlık masa toplamı
        self.iskonto = 0.0 # Adisyon sekmesinde anlık iskonto
        self.sepet_urun_ids = {} # Sepetteki ürünlerin Treeview item ID'lerini saklamak için (miktar güncelleme/silme için)


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
        self.musteri_arayuz_olustur() # Alt çizgisiz olanı çağır
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

        # print(f"Veritabanı yedeği alındı: {self.last_backup_path}") # Artık _yedek_al içinde yazdırılıyor


    def _configure_styles(self):
        """ttk stillerini yapılandırır."""
        try:
            self.style.theme_use('clam') # Modern bir tema kullan
            self.style.configure("TButton", padding=6, relief="flat", font=('Arial', 10))
            self.style.configure("TLabel", font=('Arial', 10))
            self.style.configure("TEntry", padding=5)
            self.style.configure("TCombobox", padding=5)
            self.style.configure("Treeview.Heading", font=('Arial', 10, 'bold'))
            self.style.configure("Treeview", font=('Arial', 10), rowheight=25)


            # Özel Buton Stilleri
            self.style.configure("Masa.TButton", font=('Arial', 10, 'bold'), padding=10)
            self.style.map("Masa.TButton",
                           background=[('active', RENK_MUSTERILI_MASA), ('!disabled', RENK_BOS_MASA)],
                           foreground=[('active', 'black'), ('!disabled', 'black')])


            self.style.configure("DoluMasa.TButton", font=('Arial', 10, 'bold'), padding=10, background=RENK_DOLU_MASA)
            self.style.map("DoluMasa.TButton",
                           background=[('active', RENK_BEKLEYEN_MASA), ('!disabled', RENK_DOLU_MASA)],
                           foreground=[('active', 'white'), ('!disabled', 'black')])


            self.style.configure("MusteriliMasa.TButton", font=('Arial', 10, 'bold'), padding=10, background=RENK_MUSTERILI_MASA)
            self.style.map("MusteriliMasa.TButton",
                           background=[('active', RENK_BEKLEYEN_MASA), ('!disabled', RENK_MUSTERILI_MASA)],
                           foreground=[('active', 'white'), ('!disabled', 'black')])

            self.style.configure("BekleyenMasa.TButton", font=('Arial', 10, 'bold'), padding=10, background=RENK_BEKLEYEN_MASA)
            self.style.map("BekleyenMasa.TButton",
                           background=[('active', RENK_DOLU_MASA), ('!disabled', RENK_BEKLEYEN_MASA)],
                           foreground=[('active', 'black'), ('!disabled', 'white')])

            self.style.configure("AktifMasa.TButton", font=('Arial', 10, 'bold'), padding=10, background="blue", foreground="white") # Seçili masa için mavi

            self.style.configure("Baslik.TLabel", font=('Arial', 12, 'bold'))
            self.style.configure("Bilgi.TLabel", font=('Arial', 10))
            self.style.configure("Toplam.TLabel", font=('Arial', 14, 'bold'))
            self.style.configure("HizliSatis.TFrame", background="#f0f0f0") # Canvas arka plan rengiyle uyumlu

            # Adisyon Sekmesi Buton Stilleri
            self.style.configure("EkleCikar.TButton", background=RENK_BUTON_EKLE_CIKAR, foreground=get_text_color(RENK_BUTON_EKLE_CIKAR))
            self.style.configure("Odeme.TButton", background=RENK_BUTON_ODEME, foreground=get_text_color(RENK_BUTON_ODEME))
            self.style.configure("Kapat.TButton", background=RENK_BUTON_KAPAT, foreground=get_text_color(RENK_BUTON_KAPAT))
            self.style.configure("AraOdeme.TButton", background=RENK_BUTON_ARA_ODEME, foreground=get_text_color(RENK_BUTON_ARA_ODEME))

            # Yönetim Sekmesi Buton Stilleri
            self.style.configure("Yonetim.TButton", background=RENK_BUTON_YONETIM, foreground="black")
            self.style.configure("Temizle.TButton", background=RENK_BUTON_TEMIZLE, foreground=get_text_color(RENK_BUTON_TEMIZLE))

            # Rapor Sekmesi Buton Stilleri
            self.style.configure("Rapor.TButton", background=RENK_BUTON_RAPOR, foreground=get_text_color(RENK_BUTON_RAPOR))
            self.style.configure("Export.TButton", background=RENK_BUTON_EXPORT, foreground=get_text_color(RENK_BUTON_EXPORT))


        except tk.TclError as e:
            print(f"Stil yapılandırma hatası: {e}")
            messagebox.showwarning("Stil Hatası", "Stiller yapılandırılırken bir sorun oluştu. Uygulama varsayılan görünüme dönebilir.")
        except Exception as e:
            print(f"Beklenmedik stil hatası: {e}")


    def _veritabani_baglantisi_kur(self):
        """Veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.row_factory = sqlite3.Row # Sütun isimleriyle erişim için
            self.cursor = self.conn.cursor()
            print("Veritabanı bağlantısı başarıyla kuruldu.")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Veritabanı bağlantısı kurulurken hata oluştu: {e}")
            self.root.destroy() # Hata durumunda uygulamayı kapat
        except Exception as e:
            messagebox.showerror("Hata", f"Beklenmedik hata oluştu: {e}")
            self.root.destroy() # Hata durumunda uygulamayı kapat


    def _veritabani_tablolarini_olustur(self):
        """Gerekli veritabanı tablolarını oluşturur."""
        try:
            # Masalar tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS masalar (
                    masa_no INTEGER PRIMARY KEY,
                    durum TEXT DEFAULT 'boş', -- 'boş', 'dolu'
                    toplam REAL DEFAULT 0.0,
                    musteri_id INTEGER,
                    acilis TEXT, -- Masa açılış zamanı
                    kapanis TEXT, -- Masa kapanış zamanı
                    son_adisyon_zamani TEXT, -- Son ürün ekleme/çıkarma zamanı
                    son_islem_zamani TEXT, -- Son herhangi bir işlem zamanı (adisyon, ödeme, müşteri atama vb.)
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (musteri_id)
                )
            ''')

            # Ürünler tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS urunler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, -- Otomatik artan ID
                    sira INTEGER UNIQUE, -- Sıra numarası (null olabilir)
                    urun_adi TEXT UNIQUE NOT NULL,
                    fiyat REAL NOT NULL,
                    kategori TEXT,
                    aktif INTEGER DEFAULT 1 -- 1: Aktif, 0: Pasif
                )
            ''')

            # Masa Siparişleri tablosu (Aktif masaların siparişleri)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS masa_siparisleri (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER,
                    urun_adi TEXT,
                    fiyat REAL,
                    miktar INTEGER,
                    tutar REAL, -- fiyat * miktar
                    eklenme_zamani TEXT,
                    FOREIGN KEY (masa_no) REFERENCES masalar (masa_no),
                    FOREIGN KEY (urun_adi) REFERENCES urunler (urun_adi),
                    UNIQUE(masa_no, urun_adi) -- Bir masada aynı üründen sadece bir satır olsun (miktarı güncellenir)
                )
            ''')

            # Sipariş Geçmişi tablosu (Kapatılan masaların özet bilgileri)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER,
                    tarih TEXT, -- Kapanış tarihi
                    odeme_turu TEXT, -- 'Nakit', 'Kart', 'Veresiye'
                    toplam REAL, -- Masa oturumunun toplam tutarı
                    musteri_id INTEGER,
                    FOREIGN KEY (masa_no) REFERENCES masalar (masa_no),
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (musteri_id)
                )
            ''')

            # Sipariş Detayları tablosu (Sipariş geçmişindeki her bir kalemin detayı)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparis_detaylari (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_id INTEGER,
                    urun_adi TEXT,
                    fiyat REAL,
                    miktar INTEGER,
                    tutar REAL,
                    FOREIGN KEY (siparis_id) REFERENCES siparis_gecmisi (id),
                    FOREIGN KEY (urun_adi) REFERENCES urunler (urun_adi)
                )
            ''')

            # Müşteriler tablosu
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteriler (
                    musteri_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT,
                    telefon TEXT UNIQUE,
                    adres TEXT,
                    kayit_tarihi TEXT, -- Müşteri kayıt tarihi eklendi
                    cumulative_balance REAL DEFAULT 0.0 -- Kümülatif bakiye (veresiye için)
                )
            ''')

            # Ara Ödemeler tablosu (Masaya yapılan ara ödemeler)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ara_odemeler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER,
                    miktar REAL,
                    tarih TEXT,
                    FOREIGN KEY (masa_no) REFERENCES masalar (masa_no)
                )
            ''')

            # Masa Geçmişi tablosu (Her masa açılış ve kapanış kaydı)
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS masa_gecmisi (
                    kayit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER,
                    acilis TEXT,
                    kapanis TEXT,
                    musteri_id INTEGER,
                    toplam REAL, -- O oturumun toplam tutarı
                    odeme_turu TEXT, -- O oturumun ödeme türü
                    tarih TEXT, -- Kayıt tarihi (genellikle kapanış tarihi)
                    FOREIGN KEY (masa_no) REFERENCES masalar (masa_no),
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (musteri_id)
                )
            ''')


            self.conn.commit()
            print("Veritabanı tabloları başarıyla oluşturuldu veya zaten mevcut.")

            # Ürünler tablosu boşsa varsayılan ürünleri ekle
            self.cursor.execute("SELECT COUNT(*) FROM urunler")
            if self.cursor.fetchone()[0] == 0:
                 print("Ürünler tablosu boş, varsayılan ürünler ekleniyor...")
                 self._varsayilan_urunleri_ekle()

            # Masalar tablosu boşsa varsayılan masaları ekle
            self.cursor.execute("SELECT COUNT(*) FROM masalar")
            if self.cursor.fetchone()[0] == 0:
                 print(f"Masalar tablosu boş, {DEFAULT_MASA_SAYISI} adet varsayılan masa ekleniyor...")
                 self._varsayilan_masalari_ekle(DEFAULT_MASA_SAYISI)


        except sqlite3.Error as e:
            print(f"Veritabanı tablosu oluşturma hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Veritabanı tabloları oluşturulurken hata oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik hata oluştu: {e}")
            messagebox.showerror("Hata", f"Beklenmedik hata oluştu: {e}")

    def _varsayilan_urunleri_ekle(self):
        """Ürünler tablosu boşsa varsayılan ürünleri ekler."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM urunler")
            if self.cursor.fetchone()[0] == 0:
                urun_listesi = [
                    (1, 'Türk Kahvesi', 30.0, 'Kahveler', 1),
                    (2, 'Çay', 20.0, 'Sıcak İçecekler', 1),
                    (3, 'Espresso', 40.0, 'Kahveler', 1),
                    (4, 'Latte', 45.0, 'Kahveler', 1),
                    (5, 'Mocha', 50.0, 'Kahveler', 1),
                    (6, 'Limonata', 30.0, 'Soğuk İçecekler', 1),
                    (7, 'Portakal Suyu', 35.0, 'Soğuk İçecekler', 1),
                    (8, 'Ayran', 25.0, 'Soğuk İçecekler', 1),
                    (9, 'Su', 15.0, 'Soğuk İçecekler', 1),
                    (10, 'Cheesecake', 60.0, 'Pastalar', 1),
                    (11, 'Tiramisu', 55.0, 'Pastalar', 1),
                    (12, 'Sandviç', 70.0, 'Yiyecekler', 1),
                    (13, 'Salata', 65.0, 'Yiyecekler', 1),
                    # ... (Diğer varsayılan ürünler) ...
                ]
                self.cursor.executemany('''
                    INSERT INTO urunler (sira, urun_adi, fiyat, kategori, aktif)
                    VALUES (?, ?, ?, ?, ?)
                ''', urun_listesi)
                self.conn.commit()
                print(f"{len(urun_listesi)} adet varsayılan ürün eklendi.")
        except sqlite3.Error as e:
            print(f"Varsayılan ürünleri ekleme hatası: {e}")
            self.conn.rollback()
        except Exception as e:
            print(f"Varsayılan ürünleri ekleme beklenmedik hata: {e}")

    def _varsayilan_masalari_ekle(self, sayi):
        """Masalar tablosu boşsa belirtilen sayıda varsayılan masa ekler."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM masalar")
            if self.cursor.fetchone()[0] == 0:
                masalar = [(i,) for i in range(1, sayi + 1)] # (1,), (2,), ... (sayi,) tuple listesi
                self.cursor.executemany('''
                    INSERT INTO masalar (masa_no)
                    VALUES (?)
                ''', masalar)
                self.conn.commit()
                print(f"{sayi} adet varsayılan masa eklendi.")
        except sqlite3.Error as e:
            print(f"Varsayılan masaları ekleme hatası: {e}")
            self.conn.rollback()
        except Exception as e:
            print(f"Varsayılan masaları ekleme beklenmedik hata: {e}")


    def _yedek_al(self):
        """Veritabanının yedeğini alır."""
        yedek_klasoru = "yedekler"
        if not os.path.exists(yedek_klasoru):
            os.makedirs(yedek_klasoru)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        yedek_dosya_adi = f"cafe_yedek_{timestamp}.db"
        yedek_yolu = os.path.join(yedek_klasoru, yedek_dosya_adi)

        try:
            # Mevcut veritabanını kapat
            if self.conn:
                 self.conn.close()
                 self.conn = None
                 self.cursor = None

            # Orijinal dosyayı kopyala
            import shutil
            shutil.copy2(self.db_file, yedek_yolu)

            # Bağlantıyı tekrar kur
            self._veritabani_baglantisi_kur()

            self.last_backup_path = yedek_yolu # Son yedek yolunu sakla
            print(f"Veritabanı yedeği alındı: {yedek_yolu}")
            # messagebox.showinfo("Yedekleme", f"Veritabanı yedeği başarıyla alındı:\n{yedek_yolu}") # Çok sık mesaj vermesin

        except FileNotFoundError:
            print(f"Hata: Yedeklenecek veritabanı dosyası bulunamadı: {self.db_file}")
            messagebox.showerror("Yedekleme Hatası", "Veritabanı dosyası bulunamadı. Yedekleme yapılamadı.")
            # Uygulama çalışmaya devam edebilir ama yedekleme olmaz
            if self.conn is None: # Bağlantı kapandıysa ve tekrar kurulamadıysa
                 self._veritabani_baglantisi_kur() # Tekrar kurmayı dene
        except Exception as e:
            print(f"Yedekleme hatası: {e}")
            messagebox.showerror("Yedekleme Hatası", f"Veritabanı yedeği alınırken bir hata oluştu:\n{e}")
            if self.conn is None: # Bağlantı kapandıysa ve tekrar kurulamadıysa
                 self._veritabani_baglantisi_kur() # Tekrar kurmayı dene


    def _uygulamayi_kapat(self):
        """Uygulama kapatılırken veritabanı bağlantısını kapatır ve yedek alır."""
        if messagebox.askokcancel("Çıkış", "Uygulamayı kapatmak istediğinize emin misiniz?"):
            try:
                self._yedek_al() # Kapatırken son bir yedek al
                if self.conn:
                    self.conn.close()
                    print("Veritabanı bağlantısı kapatıldı.")
            except Exception as e:
                print(f"Uygulama kapatılırken hata oluştu: {e}")
            self.root.destroy()

    def _on_closing(self):
        """Pencere kapatma butonuna basıldığında çalışır."""
        self._uygulamayi_kapat() # _uygulamayi_kapat fonksiyonunu çağır


    def _tarih_saat_al_db_format(self):
        """Şu anki tarih ve saati veritabanı formatında döndürür."""
        return datetime.now().strftime(DB_DATE_FORMAT)

    def _tarih_saat_al_display_format(self):
        """Şu anki tarih ve saati gösterim formatında döndürür."""
        return datetime.now().strftime(RAPOR_TARIH_FORMATI + " %H:%M:%S")

    def _saat_guncelle(self):
        """Saati günceller ve her saniye tekrar çalışmak için planlar."""
        if hasattr(self, 'saat_label'):
            self.saat_label.config(text=self._tarih_saat_al_display_format())
            self.root.after(1000, self._saat_guncelle) # 1000 ms (1 saniye) sonra tekrar çağır


    def _sekme_degisti(self, event):
        """Notebook sekmesi değiştiğinde çalışır."""
        secili_sekme_index = self.notebook.index(self.notebook.select())
        # print(f"Sekme değişti: {secili_sekme_index}")

        # Masa Yönetimi sekmesine dönüldüğünde masa butonlarını güncelle
        if secili_sekme_index == 0: # Masa Yönetimi sekmesi
            self._masa_butonlarini_olustur()
            self.aktif_masa = None # Sekme değişince aktif masayı sıfırla
            if hasattr(self, 'aktif_masa_label'):
                 self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
            if hasattr(self, 'musteri_label'):
                 self.musteri_label.config(text="Müşteri: -")
            if hasattr(self, 'musteri_bakiye_adisyon_label'):
                 self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")
            self._sepeti_temizle_ui_only() # Sepet UI'ı temizle

        # Adisyon sekmesine geçildiğinde sepeti yükle ve hızlı satış butonlarını güncelle
        elif secili_sekme_index == 1: # Adisyon sekmesi
             self._sepeti_yukle()
             self._filter_hizli_satis_buttons(self.kategori_filtre_combobox.get() if hasattr(self, 'kategori_filtre_combobox') else "Tümü") # Hızlı satış butonlarını güncelle

        # Müşteri İşlemleri sekmesine geçildiğinde müşteri listesini güncelle
        elif secili_sekme_index == 2: # Müşteri İşlemleri sekmesi
             self._musteri_listesini_guncelle()
             self._musteri_formu_temizle() # Formu temizle

        # Ürün Yönetimi sekmesine geçildiğinde ürün listesini güncelle
        elif secili_sekme_index == 3: # Ürün Yönetimi sekmesi
             self._urunleri_yukle()
             self._urun_formunu_temizle() # Formu temizle

        # Muhasebe sekmesine geçildiğinde rapor alanını temizle
        elif secili_sekme_index == 4: # Muhasebe sekmesi
             if hasattr(self, 'muhasebe_rapor_text'):
                 self.muhasebe_rapor_text.config(state='normal')
                 self.muhasebe_rapor_text.delete(1.0, tk.END)
                 self.muhasebe_rapor_text.config(state='disabled')
             # Muhasebe rapor seçimi değiştiğinde çağrılan fonksiyonu da tetikle
             self._muhasebe_rapor_secimi_degisti()


    # --- Masa Yönetimi Sekmesi Fonksiyonları ---

    def masa_arayuz_olustur(self):
        """Masa Yönetimi sekmesi arayüzünü oluşturur."""
        # Masa butonları için bir frame oluştur
        self.masa_buton_frame = ttk.Frame(self.masa_frame)
        self.masa_buton_frame.pack(pady=PAD_Y, padx=PAD_X, fill=tk.BOTH, expand=True)

        # Masa butonlarını oluştur ve yerleştir
        self._masa_butonlarini_olustur()

        # Masa ekleme/silme/müşteri atama butonları için ayrı bir frame oluştur
        masa_yonetim_kontrol_frame = ttk.Frame(self.masa_frame)
        masa_yonetim_kontrol_frame.pack(pady=PAD_Y, padx=PAD_X, fill=tk.X)

        ttk.Button(masa_yonetim_kontrol_frame, text="Yeni Masa Ekle", style="Yonetim.TButton", command=self._masa_ekle).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(masa_yonetim_kontrol_frame, text="Masa Sil", style="Temizle.TButton", command=self._masa_sil).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        # Müşteri atama butonu Müşteri İşlemleri sekmesinde.

    def _masa_butonlarini_olustur(self):
        """Masa butonlarını veritabanındaki masalara göre dinamik olarak oluşturur."""
        # Mevcut butonları temizle
        for widget in self.masa_buton_frame.winfo_children():
            widget.destroy()

        try:
            self.cursor.execute("SELECT masa_no, durum, toplam, musteri_id, son_islem_zamani FROM masalar ORDER BY masa_no")
            masalar = self.cursor.fetchall()

            # Grid ayarları
            COLS = 5 # Her satırda kaç masa butonu olacağı (ayarlanabilir)
            PAD = 5 # Butonlar arası boşluk

            # Grid için satır ve sütun ağırlıklarını ayarla
            total_rows = (len(masalar) + COLS - 1) // COLS if len(masalar) > 0 else 1
            for r in range(total_rows):
                 self.masa_buton_frame.grid_rowconfigure(r, weight=1)

            for c in range(COLS):
                 self.masa_buton_frame.grid_columnconfigure(c, weight=1)


            for i, masa in enumerate(masalar):
                masa_no = masa['masa_no']
                durum = masa['durum']
                toplam = masa['toplam'] if masa['toplam'] is not None else 0.0
                musteri_id = masa['musteri_id']
                son_islem_zamani_str = masa['son_islem_zamani']

                # Müşteri adı ve bakiye bilgisini çek
                musteri_adi = "Misafir"
                musteri_bakiye = 0.0
                if musteri_id:
                    try:
                        self.cursor.execute("SELECT ad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                        musteri = self.cursor.fetchone()
                        if musteri:
                            musteri_adi = musteri['ad']
                            musteri_bakiye = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0
                    except sqlite3.Error as e:
                        print(f"Masa butonu müşteri bilgisi çekme hatası (Masa {masa_no}): {e}")
                        musteri_adi = "Hata!"
                        musteri_bakiye = "Hata!"
                    except Exception as e:
                         print(f"Masa butonu müşteri bilgisi çekme beklenmedik hata (Masa {masa_no}): {e}")
                         musteri_adi = "Hata!"
                         musteri_bakiye = "Hata!"


                # Bekleme süresini kontrol et ve durumu güncelle (sadece dolu masalar için)
                current_style = "Masa.TButton" # Varsayılan boş masa stili
                if durum == 'dolu':
                    current_style = "DoluMasa.TButton" # Varsayılan dolu masa stili
                    if son_islem_zamani_str:
                        try:
                            son_islem_zamani = datetime.strptime(son_islem_zamani_str, DB_DATE_FORMAT)
                            gecen_sure = datetime.now() - son_islem_zamani
                            if gecen_sure > timedelta(minutes=INACTIVITY_THRESHOLD_MIN):
                                current_style = "BekleyenMasa.TButton" # Bekleyen masa stili
                        except ValueError:
                            print(f"Hata: Masa {masa_no} için geçersiz son_islem_zamani formatı: {son_islem_zamani_str}")
                        except Exception as e:
                             print(f"Masa bekleme süresi hesaplama hatası (Masa {masa_no}): {e}")


                # Aktif masa ise stilini değiştir
                if self.aktif_masa == masa_no:
                     current_style = "AktifMasa.TButton"


                button_text = f"Masa {masa_no}\n"
                if durum == 'dolu':
                    button_text += f"{toplam:.0f} ₺\n"
                    if musteri_id:
                        button_text += f"({musteri_adi})\n"
                        if isinstance(musteri_bakiye, (int, float)):
                             button_text += f"Bakiye: {musteri_bakiye:.0f} ₺" # Masa butonunda da bakiye göster
                        else:
                             button_text += f"Bakiye: {musteri_bakiye}" # Hata durumunda hata metnini göster
                    else:
                        button_text += "(Misafir)"


                btn = ttk.Button(self.masa_buton_frame, text=button_text,
                                 command=lambda mn=masa_no: self._masa_sec(mn),
                                 style=current_style) # Stili uygula
                # Grid'e yerleştirme
                row, col = divmod(i, COLS)
                btn.grid(row=row, column=col, padx=PAD, pady=PAD, sticky="nsew")


        except sqlite3.Error as e:
            print(f"Masa butonları oluşturma hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Masa butonları oluşturulurken hata oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik hata oluştu (_masa_butonlarini_olustur): {e}")

    def _masa_ekle(self):
        """Yeni masa ekler."""
        try:
            # Mevcut en yüksek masa numarasını bul
            self.cursor.execute("SELECT MAX(masa_no) FROM masalar")
            max_masa_no = self.cursor.fetchone()[0]
            yeni_masa_no = (max_masa_no if max_masa_no is not None else 0) + 1

            # Yeni masayı veritabanına ekle
            self.cursor.execute("INSERT INTO masalar (masa_no, durum, toplam) VALUES (?, 'boş', 0.0)", (yeni_masa_no,))
            self.conn.commit()

            messagebox.showinfo("Başarılı", f"Masa {yeni_masa_no} başarıyla eklendi.", parent=self.masa_frame)
            self._masa_butonlarini_olustur() # Masa butonlarını yenile

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masa eklenirken hata oluştu: {e}", parent=self.masa_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Masa eklenirken beklenmedik hata: {e}", parent=self.masa_frame)
            print(f"Masa ekleme hatası: {e}")


    def _masa_sil(self):
        """Seçili masayı siler."""
        # Kullanıcının silmek istediği masa numarasını girmesini iste
        masa_no_str = simpledialog.askstring("Masa Sil", "Silmek istediğiniz masa numarasını girin:", parent=self.masa_frame)

        if masa_no_str is None or not masa_no_str.strip():
            return # Kullanıcı iptal etti veya boş girdi

        try:
            masa_no = int(masa_no_str.strip())

            # Masanın varlığını ve durumunu kontrol et
            self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_info = self.cursor.fetchone()

            if not masa_info:
                messagebox.showwarning("Uyarı", f"Masa {masa_no} bulunamadı.", parent=self.masa_frame)
                return

            masa_durum = masa_info['durum']

            if masa_durum != 'boş':
                messagebox.showwarning("Uyarı", f"Masa {masa_no} boş değil ({masa_durum}). Dolu masalar silinemez.", parent=self.masa_frame)
                return

            # Silme onayı al
            if not messagebox.askyesno("Silme Onayı", f"Masa {masa_no}'yu silmek istediğinize emin misiniz?", parent=self.masa_frame):
                return

            # Masayı veritabanından sil
            self.cursor.execute("DELETE FROM masalar WHERE masa_no = ?", (masa_no,))
            self.conn.commit()

            messagebox.showinfo("Başarılı", f"Masa {masa_no} başarıyla silindi.", parent=self.masa_frame)
            self._masa_butonlarini_olustur() # Masa butonlarını yenile

        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir masa numarası girin.", parent=self.masa_frame)
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masa silinirken hata oluştu: {e}", parent=self.masa_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Masa silinirken beklenmedik hata: {e}", parent=self.masa_frame)
            print(f"Masa silme hatası: {e}")

    def _masa_sec(self, masa_no):
        """Bir masa seçildiğinde adisyon detaylarını yükler ve UI'ı günceller."""
        # Eğer müşteri atama modundaysak, masa seçimi farklı bir işlem yapar
        if self.current_mode == "assign_customer_selection":
            self._assign_customer_to_clicked_masa(masa_no)
            return # Müşteri atama işlemi yapıldıktan sonra normal masa seçimi yapma


        # Normal masa seçimi
        self.aktif_masa = masa_no
        if hasattr(self, 'aktif_masa_label'):
             self.aktif_masa_label.config(text=f"Aktif Masa: Masa {masa_no}")

        # Adisyon sekmesine geç
        self.notebook.select(self.adisyon_frame)

        # Sepeti ve UI'ı seçilen masanın verileriyle yükle
        self._sepeti_yukle()

        # Masa butonlarının stilini güncelle (seçili masanın rengini değiştirmek için)
        self._masa_butonlarini_olustur() # _masa_butonlarini_guncelle yerine tüm butonları yeniden oluştur


    def _masanin_toplamini_guncelle(self, masa_no):
        """Belirtilen masanın toplam tutarını masa_siparisleri tablosundan hesaplar ve masalar tablosunda günceller."""
        try:
            self.cursor.execute('''
                SELECT COALESCE(SUM(tutar), 0) AS toplam_tutar
                FROM masa_siparisleri
                WHERE masa_no = ?
            ''', (masa_no,))
            toplam_row = self.cursor.fetchone()
            yeni_toplam = toplam_row['toplam_tutar'] if toplam_row else 0.0

            self.cursor.execute("UPDATE masalar SET toplam = ? WHERE masa_no = ?", (yeni_toplam, masa_no))
            self.conn.commit()

        except sqlite3.Error as e:
            print(f"Masa toplamını güncelleme hatası (Masa {masa_no}): {e}")
            self.conn.rollback()
            messagebox.showerror("Veritabanı Hatası", f"Masa toplamı güncellenirken hata oluştu (Masa {masa_no}): {e}")
        except Exception as e:
            print(f"Masa toplamını güncelleme beklenmedik hata (Masa {masa_no}): {e}")
            messagebox.showerror("Hata", f"Masa toplamı güncellenirken beklenmedik hata oluştu (Masa {masa_no}): {e}")


    # --- Adisyon Sekmesi Fonksiyonları ---

    def adisyon_arayuz_olustur(self):
        """Adisyon sekmesi arayüzünü oluşturur
        ve hızlı satış butonlarını ilk kez yükler."""
        # Bilgi Frame (üst kısım, sabit yükseklik)
        bilgi_frame = ttk.Frame(self.adisyon_frame)
        bilgi_frame.pack(pady=PAD_Y, fill=tk.X)

        self.aktif_masa_label = ttk.Label(bilgi_frame, text="Aktif Masa: Seçili değil", style="Baslik.TLabel")
        self.aktif_masa_label.pack(side=tk.LEFT, padx=PAD_X)

        self.musteri_label = ttk.Label(bilgi_frame, text="Müşteri: -", style="Bilgi.TLabel")
        self.musteri_label.pack(side=tk.LEFT, padx=PAD_X)

        # Müşteri Kümülatif Bakiye Etiketi
        self.musteri_bakiye_adisyon_label = ttk.Label(bilgi_frame, text="Bakiye: 0 ₺", style="Bilgi.TLabel") # Başlangıç metni
        self.musteri_bakiye_adisyon_label.pack(side=tk.LEFT, padx=PAD_X)

        # Sağ tarafa saati ekle
        self.saat_label = ttk.Label(bilgi_frame, text=self._tarih_saat_al_display_format(), style="Bilgi.TLabel")
        self.saat_label.pack(side=tk.RIGHT)
        # _saat_guncelle() __init__ içinde çağrılıyor


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

        # Adisyon combobox'ını doldur (bu fonksiyon Part 7'de tanımlanmıştı)
        # Kategoriler _kategorileri_getir(include_tumu=True) ile alınıyor
        self._adisyon_kategori_combobox_guncelle() # Ayrı fonksiyona taşındı

        # Eğer "Tümü" seçeneği varsa varsayılan olarak ayarla
        if "Tümü" in self.kategori_filtre_combobox['values']:
             self.kategori_filtre_combobox.set("Tümü")

        self.kategori_filtre_combobox.bind("<<ComboboxSelected>>", self._filter_hizli_satis_buttons) # Event alan yeni fonksiyon


        # Hızlı Satış Butonları Alanı
        self.hizli_satis_container = ttk.Frame(self.adisyon_frame)
        self.hizli_satis_container.pack(pady=PAD_Y, fill=tk.BOTH, expand=True)

        self.hizli_satis_canvas = tk.Canvas(self.hizli_satis_container, bg="#f0f0f0")
        self.hizli_satis_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hizli_satis_scrollbar = ttk.Scrollbar(self.hizli_satis_container, orient=tk.VERTICAL, command=self.hizli_satis_canvas.yview)
        self.hizli_satis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hizli_satis_canvas.configure(yscrollcommand=self.hizli_satis_scrollbar.set)
        # Canvas resize olduğunda içindeki frame'in genişliğini ayarla
        self.hizli_satis_canvas.bind('<Configure>', lambda e: self.hizli_satis_canvas.itemconfigure("frame", width=self.hizli_satis_canvas.winfo_width()))

        self.hizli_satis_frame = ttk.Frame(self.hizli_satis_canvas, style="HizliSatis.TFrame") # <-- self.hizli_satis_frame burada oluşturuldu
        self.hizli_satis_canvas.create_window((0, 0), window=self.hizli_satis_frame, anchor="nw", tags="frame")

        # Frame resize olduğunda Canvas'ın scroll bölgesini güncelle
        self.hizli_satis_frame.bind('<Configure>', lambda e: self.hizli_satis_canvas.config(scrollregion=self.hizli_satis_canvas.bbox("all")))

        # Sepet Tablosu (Treeview kullanılıyor)
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
        self.sepet_tablo.bind("<<TreeviewSelect>>", self._sepet_kalem_secildi) # Sepet kalem seçildiğinde

        # Kontrol Frame
        kontrol_frame = ttk.Frame(self.adisyon_frame)
        kontrol_frame.pack(pady=PAD_Y, fill=tk.X)

        ttk.Label(kontrol_frame, text="Adetli Ürün Miktarı:", style="Bilgi.TLabel").pack(side=tk.LEFT, padx=PAD_X)
        self.miktar_spinbox = tk.Spinbox(kontrol_frame, from_=1, to=99, width=5, font=("Arial", 10))
        self.miktar_spinbox.pack(side=tk.LEFT, padx=PAD_X)

        # Miktar güncelleme butonu eklendi (Seçileni Çıkar butonunun yerine)
        ttk.Button(kontrol_frame, text="Seçileni Miktarını Güncelle", style="EkleCikar.TButton", command=self._adisyon_kalem_miktar_guncelle).pack(side=tk.LEFT, padx=PAD_X)

        ttk.Button(kontrol_frame, text="Seçileni Sil", style="EkleCikar.TButton", command=self._adisyon_kalem_sil).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(kontrol_frame, text="Sepeti Temizle", style="EkleCikar.TButton", command=self._sepeti_temizle).pack(side=tk.LEFT, padx=PAD_X)
        ttk.Button(kontrol_frame, text="İndirim Uygula (%)", style="Odeme.TButton", command=self.indirimi_uygula_action).pack(side=tk.LEFT, padx=PAD_X)

        # Ödeme ve Toplam Frame
        odeme_toplam_frame = ttk.Frame(self.adisyon_frame)
        odeme_toplam_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=PAD_Y)

        # Ödeme Butonları (Sol tarafa)
        odeme_button_frame = ttk.Frame(odeme_toplam_frame)
        odeme_button_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        ttk.Button(odeme_button_frame, text="Masa Hesap Bilgisi", style="Odeme.TButton",
                   command=self._nakit_odeme_bilgi).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(odeme_button_frame, text="Ara Ödeme Al", style="AraOdeme.TButton", command=self._ara_odeme).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(odeme_button_frame, text="Masa Kapat (Kart)", style="Kapat.TButton", command=lambda: self._odeme_yap("Kredi Kartı")).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(odeme_button_frame, text="Masa Kapat (Nakit)", style="Kapat.TButton", command=lambda: self._odeme_yap("Nakit")).pack(side=tk.LEFT, fill=tk.X, expand=True)


        # Toplam Etiketleri (Sağ tarafa)
        toplam_label_frame = ttk.Frame(odeme_toplam_frame)
        toplam_label_frame.pack(side=tk.RIGHT) # Sağ tarafa yerleştir

        # Etiketlerin sırası değiştirildi (Net Tutar en sağda)
        self.toplam_label = ttk.Label(toplam_label_frame, text="Toplam: 0 ₺", style="Toplam.TLabel") # Burası brüt toplam olacak
        self.toplam_label.pack(side=tk.RIGHT, padx=PAD_X)

        self.iskonto_label = ttk.Label(toplam_label_frame, text="İskonto: 0 ₺", style="Toplam.TLabel")
        self.iskonto_label.pack(side=tk.RIGHT, padx=PAD_X)

        self.net_tutar_label = ttk.Label(toplam_label_frame, text="Net Tutar: 0 ₺", style="Toplam.TLabel")
        self.net_tutar_label.pack(side=tk.RIGHT, padx=PAD_X)

        # --- Hızlı satış butonlarını ilk kez yükle ---
        # Bu çağrı, self.hizli_satis_frame oluşturulduktan sonra yapılır.
        self._filter_hizli_satis_buttons() # <-- Bu satır eklendi


    def _sepete_ekle_action(self):
        """Hızlı satıştan seçilen ürünü aktif masanın sepetine ekler."""
        # Bu fonksiyon _urun_ekle_hizli_satis fonksiyonunu çağırmalıdır.
        # _urun_ekle_hizli_satis fonksiyonu, tıklanan butonun bilgisini alarak işlem yapar.
        # Bu buton, adisyon_arayuz_olustur içinde hızlı satış butonlarına atanır.
        # Yani, bu fonksiyon doğrudan çağrılmaz, hızlı satış butonuna tıklandığında _urun_ekle_hizli_satis çağrılır.
        # Ancak, eğer ayrı bir "Sepete Ekle" butonu varsa, bu butona tıklanınca
        # seçili hızlı satış ürünü veya manuel girilen ürün sepete eklenmelidir.
        # Mevcut arayüzde "Sepete Ekle" butonu var ve bu _sepete_ekle_action'ı çağırıyor.
        # Bu butonın işlevi, hızlı satış alanından seçili bir ürün varsa onu eklemek olmalıdır.

        # Hızlı satış alanından seçili ürünü bulma mekanizması eklenmeli.
        # Şu anki yapıda, hızlı satış butonlarına tıklamak doğrudan _urun_ekle_hizli_satis'i çağırıyor.
        # Eğer bu "Sepete Ekle" butonu kullanılacaksa, hızlı satış alanından
        # hangi ürünün seçili olduğunu takip etmemiz gerekir.
        # Şimdilik bu butonun işlevselliği eksik kalacaktır.

        # Alternatif olarak, bu butona tıklanınca bir ürün seçme penceresi açılabilir.
        # Veya, hızlı satış butonlarına tıklamak yerine, ürünleri Listbox'a ekleyip oradan seçim yapılabilir.
        # Mevcut arayüzde hızlı satış butonları doğrudan ekleme yapıyor.
        # Bu "Sepete Ekle" butonu muhtemelen gereksiz veya farklı bir amaçla kullanılmalı.

        # Geçici olarak bir uyarı mesajı ekleyelim:
        messagebox.showinfo("Bilgi", "Bu 'Sepete Ekle' butonu henüz aktif değil.\nLütfen ürünleri hızlı satış butonlarına tıklayarak ekleyin.", parent=self.adisyon_frame)
        pass # Fonksiyon şu an için bir işlem yapmıyor


    def _urun_ekle_hizli_satis(self, urun_adi):
        """Hızlı satış butonuna tıklanarak ürünü aktif masanın adisyonuna ekler."""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        try:
            # Ürün fiyatını veritabanından çek
            self.cursor.execute("SELECT fiyat FROM urunler WHERE urun_adi = ?", (urun_adi,))
            urun_info = self.cursor.fetchone()
            if not urun_info:
                messagebox.showerror("Hata", f"Ürün bilgisi bulunamadı: {urun_adi}", parent=self.adisyon_frame)
                return
            fiyat = urun_info['fiyat']

            # Miktarı spinbox'tan al
            try:
                miktar = int(self.miktar_spinbox.get())
                if miktar <= 0:
                    messagebox.showwarning("Uyarı", "Miktar 1 veya daha büyük olmalıdır.", parent=self.adisyon_frame)
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir miktar girin.", parent=self.adisyon_frame)
                return

            tutar = fiyat * miktar

            # Masanın durumunu kontrol et, boşsa dolu yap ve açılış zamanını kaydet
            self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_durum = self.cursor.fetchone()['durum']

            current_time = self._tarih_saat_al_db_format()

            if masa_durum == 'boş':
                self.cursor.execute('''
                    UPDATE masalar
                    SET durum = 'dolu', acilis = ?, son_adisyon_zamani = ?, son_islem_zamani = ?
                    WHERE masa_no = ?
                ''', (current_time, current_time, current_time, masa_no))
            else:
                 # Masa doluysa sadece son işlem zamanını güncelle
                 self.cursor.execute('''
                     UPDATE masalar
                     SET son_adisyon_zamani = ?, son_islem_zamani = ?
                     WHERE masa_no = ?
                 ''', (current_time, current_time, masa_no))


            # Ürünü masa siparişlerine ekle veya miktarını artır
            # Burada UNIQUE kısıtlaması olduğu için INSERT OR REPLACE veya SELECT ve UPDATE/INSERT yapılmalı
            self.cursor.execute("SELECT id, miktar FROM masa_siparisleri WHERE masa_no = ? AND urun_adi = ?", (masa_no, urun_adi))
            existing_item = self.cursor.fetchone()

            if existing_item:
                # Eğer aynı ürün varsa miktarı ve tutarı güncelle
                new_miktar = existing_item['miktar'] + miktar
                new_tutar = new_miktar * fiyat
                self.cursor.execute('''
                    UPDATE masa_siparisleri
                    SET miktar = ?, tutar = ?
                    WHERE id = ?
                ''', (new_miktar, new_tutar, existing_item['id']))
            else:
                # Ürün yoksa yeni satır ekle
                self.cursor.execute('''
                    INSERT INTO masa_siparisleri (masa_no, urun_adi, fiyat, miktar, tutar, eklenme_zamani)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (masa_no, urun_adi, fiyat, miktar, tutar, current_time))

            # Masanın toplam tutarını güncelle
            self._masanin_toplamini_guncelle(masa_no)

            self.conn.commit()
            self._sepeti_yukle() # Adisyon listesini yenile
            self._masa_butonlarini_olustur() # Masa butonundaki toplamı ve durumu güncelle

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün adisyona eklenirken hata oluştu: {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün adisyona eklenirken beklenmedik hata: {e}", parent=self.adisyon_frame)
            print(f"Ürün adisyon ekleme hatası: {e}")


    def _sepet_kalem_secildi(self, event):
        """Sepet Treeview'ında bir kalem seçildiğinde miktar spinbox'ını günceller."""
        selected_item = self.sepet_tablo.selection()
        if not selected_item:
            self._miktar_spinbox_reset() # Seçim kalkarsa spinbox'ı sıfırla
            return

        # Seçilen öğenin değerlerini al
        item_values = self.sepet_tablo.item(selected_item, 'values')

        if len(item_values) >= 3: # En az ürün adı, fiyat ve miktar sütunları olmalı
            try:
                miktar = int(item_values[2]) # Miktar 3. sütunda (index 2)
                self.miktar_spinbox.delete(0, tk.END)
                self.miktar_spinbox.insert(0, str(miktar))
            except ValueError:
                print(f"Hata: Seçilen sepet kaleminden miktar alınamadı: {item_values}")
                self._miktar_spinbox_reset() # Hata durumunda spinbox'ı sıfırla
            except Exception as e:
                 print(f"Beklenmedik hata oluştu (_sepet_kalem_secildi): {e}")
                 self._miktar_spinbox_reset() # Hata durumunda spinbox'ı sıfırla
        else:
             self._miktar_spinbox_reset() # Seçim geçersizse spinbox'ı sıfırla


    def _miktar_spinbox_reset(self):
         """Miktar spinbox'ını varsayılan değerine (1) ayarlar."""
         if hasattr(self, 'miktar_spinbox'):
             self.miktar_spinbox.delete(0, tk.END)
             self.miktar_spinbox.insert(0, "1")


    def _adisyon_kalem_miktar_guncelle(self):
        """Sepette seçili olan kalemin miktarını günceller."""
        selected_item = self.sepet_tablo.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen önce sepetten bir ürün seçin.", parent=self.adisyon_frame)
            return

        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Aktif masa seçili değil.", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        try:
            yeni_miktar = int(self.miktar_spinbox.get())
            if yeni_miktar <= 0:
                messagebox.showwarning("Uyarı", "Miktar 1 veya daha büyük olmalıdır.", parent=self.adisyon_frame)
                return

            # Seçilen öğenin mevcut değerlerini al
            item_values = self.sepet_tablo.item(selected_item, 'values')
            if len(item_values) < 2: # Ürün adı ve fiyat olmalı
                 messagebox.showwarning("Hata", "Seçili sepet kalem bilgisi eksik.", parent=self.adisyon_frame)
                 return

            urun_adi = item_values[0]
            # Fiyatı string'den float'a çevirirken ' ₺' karakterini temizle
            fiyat = float(item_values[1].replace(' ₺', '').strip())


            # Veritabanında ilgili sipariş kalemini bul ve güncelle
            # masa_siparisleri tablosunda UNIQUE(masa_no, urun_adi) kısıtlaması olduğu için
            # urun_adi ve masa_no ile bulabiliriz.
            self.cursor.execute('''
                SELECT id FROM masa_siparisleri
                WHERE masa_no = ? AND urun_adi = ?
            ''', (masa_no, urun_adi))
            siparis_kalem_row = self.cursor.fetchone()

            if not siparis_kalem_row:
                 messagebox.showerror("Hata", "Güncellenecek sipariş kalemi veritabanında bulunamadı.", parent=self.adisyon_frame)
                 self._sepeti_yukle() # Sepeti yeniden yükleyerek UI'ı senkronize et
                 return

            siparis_kalem_id = siparis_kalem_row['id']
            yeni_tutar = yeni_miktar * fiyat

            self.cursor.execute('''
                UPDATE masa_siparisleri
                SET miktar = ?, tutar = ?
                WHERE id = ?
            ''', (yeni_miktar, yeni_tutar, siparis_kalem_id))

            # Masanın toplam tutarını güncelle
            self._masanin_toplamini_guncelle(masa_no)

            self.conn.commit()
            self._sepeti_yukle() # Adisyon listesini yenile
            self._masa_butonlarini_olustur() # Masa butonundaki toplamı güncelle

        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir sayısal miktar girin.", parent=self.adisyon_frame)
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Sipariş miktarı güncellenirken hata oluştu: {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Sipariş miktarı güncellenirken beklenmedik hata: {e}", parent=self.adisyon_frame)
            print(f"Miktar güncelleme hatası: {e}")


    def _adisyon_kalem_sil(self):
        """Sepette seçili olan kalemi siler."""
        selected_item = self.sepet_tablo.selection()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen önce sepetten bir ürün seçin.", parent=self.adisyon_frame)
            return

        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Aktif masa seçili değil.", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        # Seçilen öğenin mevcut değerlerini al
        item_values = self.sepet_tablo.item(selected_item, 'values')
        if len(item_values) < 1: # Ürün adı olmalı
             messagebox.showwarning("Hata", "Seçili sepet kalem bilgisi eksik.", parent=self.adisyon_frame)
             return
        urun_adi = item_values[0]


        if not messagebox.askyesno("Silme Onayı", f"{urun_adi} ürününü sepetten silmek istediğinize emin misiniz?", parent=self.adisyon_frame):
            return

        try:
            # Veritabanında ilgili sipariş kalemini bul ve sil
            self.cursor.execute('''
                DELETE FROM masa_siparisleri
                WHERE masa_no = ? AND urun_adi = ?
            ''', (masa_no, urun_adi))

            # Masanın toplam tutarını güncelle
            self._masanin_toplamini_guncelle(masa_no)

            self.conn.commit()
            self._sepeti_yukle() # Adisyon listesini yenile
            self._masa_butonlarini_olustur() # Masa butonundaki toplamı ve durumu güncelle

            # Eğer sepet boşaldıysa masanın durumunu 'boş' yap
            self.cursor.execute("SELECT COUNT(*) FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))
            kalan_urun_sayisi = self.cursor.fetchone()[0]
            if kalan_urun_sayisi == 0:
                 self.cursor.execute("UPDATE masalar SET durum = 'boş', musteri_id = NULL, acilis = NULL, son_adisyon_zamani = NULL WHERE masa_no = ?", (masa_no,))
                 self.conn.commit()
                 self._masa_butonlarini_olustur() # Masa butonunu boş olarak güncelle
                 self.aktif_masa = None # Aktif masayı sıfırla
                 if hasattr(self, 'aktif_masa_label'):
                      self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
                 if hasattr(self, 'musteri_label'):
                      self.musteri_label.config(text="Müşteri: -")
                 if hasattr(self, 'musteri_bakiye_adisyon_label'):
                      self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Sipariş kalemi silinirken hata oluştu: {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Sipariş kalemi silinirken beklenmedik hata: {e}", parent=self.adisyon_frame)
            print(f"Kalem silme hatası: {e}")


    def _sepeti_temizle(self):
        """Aktif masanın sepetini veritabanından ve UI'dan tamamen temizler."""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Aktif masa seçili değil.", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        if not messagebox.askyesno("Sepeti Temizle Onayı", f"Masa {masa_no}'nun sepetini tamamen temizlemek istediğinize emin misiniz?", parent=self.adisyon_frame):
            return

        try:
            # Masa siparişlerini veritabanından sil
            self.cursor.execute("DELETE FROM masa_siparisleri WHERE masa_no = ?", (masa_no,))

            # Ara ödemeleri veritabanından sil
            self.cursor.execute("DELETE FROM ara_odemeler WHERE masa_no = ?", (masa_no,))

            # Masanın toplamını sıfırla ve durumu boş yap
            self.cursor.execute('''
                UPDATE masalar
                SET durum = 'boş', toplam = 0, musteri_id = NULL,
                acilis = NULL, kapanis = NULL, son_adisyon_zamani = NULL, son_islem_zamani = ?
                WHERE masa_no = ?
            ''', (self._tarih_saat_al_db_format(), masa_no))


            self.conn.commit()
            self._sepeti_temizle_ui_only() # UI'ı temizle
            self._masa_butonlarini_olustur() # Masa butonunu boş olarak güncelle

            messagebox.showinfo("Başarılı", f"Masa {masa_no} sepeti temizlendi.", parent=self.adisyon_frame)

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Sepet temizlenirken hata oluştu: {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Sepet temizlenirken beklenmedik hata: {e}", parent=self.adisyon_frame)
            print(f"Sepet temizleme hatası: {e}")


    def _sepeti_temizle_ui_only(self):
        """Sadece kullanıcı arayüzündeki sepet listesini ve toplam etiketlerini temizler."""
        # Kontrol et: self.sepet_tablo Treeview widget'ı tanımlı mı?
        if hasattr(self, 'sepet_tablo') and isinstance(self.sepet_tablo, ttk.Treeview):
             for item in self.sepet_tablo.get_children():
                 self.sepet_tablo.delete(item)
        # else:
        #     print("Uyarı: self.sepet_tablo Treeview widget'ı tanımlı değil veya doğru tipte değil.")


        # Toplamları sıfırla (UI etiketleri varsa)
        if hasattr(self, 'toplam_label'):
             self.toplam_label.config(text="Toplam: 0 ₺")
        if hasattr(self, 'iskonto_label'):
             self.iskonto_label.config(text="İskonto: 0 ₺")
        if hasattr(self, 'net_tutar_label'):
             self.net_tutar_label.config(text="Net Tutar: 0 ₺")


        # Müşteri ve bakiye etiketlerini de sıfırla
        if hasattr(self, 'musteri_label'):
             self.musteri_label.config(text="Müşteri: -")
        if hasattr(self, 'musteri_bakiye_adisyon_label'):
             self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")

        # Miktar spinbox'ını sıfırla
        self._miktar_spinbox_reset()

        # Aktif masa seçimini kaldır
        self.aktif_masa = None
        if hasattr(self, 'aktif_masa_label'):
            self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")

        # Masa butonlarını güncelle (tüm masalar boş görünecek)
        self._masa_butonlarini_olustur() # _masa_butonlarini_guncelle yerine _masa_butonlarini_olustur çağrıldı


    def _sepeti_yukle(self):
        """Aktif masanın siparişlerini sepet Treeview'ına yükler ve UI'ı günceller (Müşteri bilgisi ve Bakiye dahil)"""
        # Kontrol et: self.sepet_tablo Treeview widget'ı tanımlı mı?
        if not hasattr(self, 'sepet_tablo') or not isinstance(self.sepet_tablo, ttk.Treeview):
             print("Hata: self.sepet_tablo Treeview widget'ı tanımlı değil veya doğru tipte değil.")
             # Hata mesajı gösterebilir veya sessizce geçebiliriz
             # messagebox.showerror("UI Hatası", "Sepet görüntüleme alanı bulunamadı.")
             # UI güncellemelerine devam etme, sadece veritabanı işlemleri yapılır
             self._sepeti_temizle_ui_only() # UI elementleri yoksa hata vermez
             return

        # Sepeti temizle
        for item in self.sepet_tablo.get_children():
            self.sepet_tablo.delete(item)

        # Toplamları sıfırla (UI etiketleri varsa)
        if hasattr(self, 'toplam_label'):
             self.toplam_label.config(text="Toplam: 0 ₺")
        if hasattr(self, 'iskonto_label'):
             self.iskonto_label.config(text="İskonto: 0 ₺")
        if hasattr(self, 'net_tutar_label'):
             self.net_tutar_label.config(text="Net Tutar: 0 ₺")


        # Müşteri ve Bakiye etiketlerini varsayılana ayarla (UI elementleri varsa)
        if hasattr(self, 'musteri_label'):
             self.musteri_label.config(text="Müşteri: -")
        if hasattr(self, 'musteri_bakiye_adisyon_label'):
             self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")

        self.toplam_tutar = 0.0 # Masa toplamını hesaplamak için sıfırla
        self.iskonto = 0.0 # İskonto hesaplamak için sıfırla

        if self.aktif_masa:
            # Aktif masanın siparişlerini çek
            try:
                self.cursor.execute('''
                    SELECT urun_adi, fiyat, miktar, tutar
                    FROM masa_siparisleri
                    WHERE masa_no = ?
                ''', (self.aktif_masa,))

                siparisler = self.cursor.fetchall() # row_factory sayesinde sütun isimleriyle erişilir

                # Sepet Treeview'ına siparişleri ekle ve toplam tutarı hesapla
                for siparis in siparisler:
                    self.sepet_tablo.insert("", tk.END, values=(
                        siparis['urun_adi'],
                        f"{siparis['fiyat']:.0f} ₺",
                        siparis['miktar'],
                        f"{siparis['tutar']:.0f} ₺"
                    ))
                    self.toplam_tutar += siparis['tutar'] # Toplam tutarı hesapla

            except sqlite3.Error as e:
                 print(f"Sepet siparişleri çekme hatası: {e}")
                 # Hata durumunda UI'ı temizleyebiliriz
                 self.sepet_tablo.delete(*self.sepet_tablo.get_children())
                 if hasattr(self, 'toplam_label'):
                      self.toplam_label.config(text="Toplam: Hata!")
                 if hasattr(self, 'iskonto_label'):
                      self.iskonto_label.config(text="İskonto: Hata!")
                 if hasattr(self, 'net_tutar_label'):
                      self.net_tutar_label.config(text="Net Tutar: Hata!")
                 if hasattr(self, 'musteri_label'):
                      self.musteri_label.config(text="Müşteri: Hata!")
                 if hasattr(self, 'musteri_bakiye_adisyon_label'):
                      self.musteri_bakiye_adisyon_label.config(text="Bakiye: Hata!")
                 return # İşleme devam etme


            # Masanın müşteri ID'sini çek
            musteri_id = None
            try:
                 self.cursor.execute("SELECT musteri_id FROM masalar WHERE masa_no = ?", (self.aktif_masa,))
                 masa_info = self.cursor.fetchone()
                 musteri_id = masa_info['musteri_id'] if masa_info else None

                 if musteri_id:
                     try:
                         self.cursor.execute("SELECT ad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,)) # cumulative_balance çekildi
                         musteri = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir
                         if musteri: # Müşteri bulunduysa
                             if hasattr(self, 'musteri_label'):
                                  self.musteri_label.config(text=f"Müşteri: {musteri['ad']}")
                             if hasattr(self, 'musteri_bakiye_adisyon_label'):
                                  # Kümülatif bakiye etiketini güncelle (formatlı)
                                  bakiye = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0
                                  self.musteri_bakiye_adisyon_label.config(text=f"Bakiye: {bakiye:.0f} ₺")
                         else: # Müşteri ID var ama müşteri bulunamadı (DB tutarsızlığı)
                             if hasattr(self, 'musteri_label'):
                                  self.musteri_label.config(text="Müşteri: Bulunamadı")
                             if hasattr(self, 'musteri_bakiye_adisyon_label'):
                                  self.musteri_bakiye_adisyon_label.config(text="Bakiye: ? ₺")

                     except sqlite3.Error as e:
                          print(f"Müşteri bilgisi çekme hatası: {e}")
                          if hasattr(self, 'musteri_label'):
                               self.musteri_label.config(text="Müşteri: Hata!")
                          if hasattr(self, 'musteri_bakiye_adisyon_label'):
                               self.musteri_bakiye_adisyon_label.config(text="Bakiye: Hata!")
                     except Exception as e:
                          print(f"Müşteri bilgisi çekme beklenmedik hata: {e}")
                          if hasattr(self, 'musteri_label'):
                               self.musteri_label.config(text="Müşteri: Hata!")
                          if hasattr(self, 'musteri_bakiye_adisyon_label'):
                               self.musteri_bakiye_adisyon_label.config(text="Bakiye: Hata!")

                 # Müşteri ID yoksa etiketleri varsayılana ayarla (fonksiyon başında yapılıyor)
                 # else:
                 #     if hasattr(self, 'musteri_label'):
                 #          self.musteri_label.config(text="Müşteri: -")
                 #     if hasattr(self, 'musteri_bakiye_adisyon_label'):
                 #          self.musteri_bakiye_adisyon_label.config(text="Bakiye: 0 ₺")


            except sqlite3.Error as e:
                 print(f"Masa müşteri ID çekme hatası: {e}")
                 if hasattr(self, 'musteri_label'):
                      self.musteri_label.config(text="Müşteri: Hata!")
                 if hasattr(self, 'musteri_bakiye_adisyon_label'):
                      self.musteri_bakiye_adisyon_label.config(text="Bakiye: Hata!")
            except Exception as e:
                 print(f"Masa müşteri ID çekme beklenmedik hata: {e}")
                 if hasattr(self, 'musteri_label'):
                      self.musteri_label.config(text="Müşteri: Hata!")
                 if hasattr(self, 'musteri_bakiye_adisyon_label'):
                      self.musteri_bakiye_adisyon_label.config(text="Bakiye: Hata!")


            # Ara ödemeler toplamını çek
            try:
                self.cursor.execute('''
                    SELECT COALESCE(SUM(miktar), 0) as ara_odeme_toplam FROM ara_odemeler
                    WHERE masa_no = ?
                ''', (self.aktif_masa,))
                ara_odeme_row = self.cursor.fetchone() # row_factory sayesinde sütun isimleriyle erişilir
                ara_odeme_toplam = ara_odeme_row['ara_odeme_toplam'] if ara_odeme_row and 'ara_odeme_toplam' in ara_odeme_row and ara_odeme_row['ara_odeme_toplam'] is not None else 0.0

            except sqlite3.Error as e:
                 print(f"Ara ödeme toplamı çekme hatası: {e}")
                 ara_odeme_toplam = 0.0 # Hata durumunda ara ödemeyi sıfır kabul et
            except Exception as e:
                 print(f"Ara ödeme toplamı çekme beklenmedik hata: {e}")
                 ara_odeme_toplam = 0.0 # Hata durumunda ara ödemeyi sıfır kabul et


            # Toplam UI etiketlerini güncelle (ara ödeme dahil)
            self._toplam_guncelle_ui(ara_odeme_toplam)

        # else: # Aktif masa yoksa - Zaten fonksiyon başında sıfırlanıyor
        #     pass # UI sıfırlama zaten yapıldı


    def _toplam_guncelle_ui(self, ara_odeme_toplam=0.0):
        """Adisyon sekmesindeki toplam, iskonto ve net tutar etiketlerini günceller."""
        # Kontrol et: Toplam etiketleri tanımlı mı?
        if not hasattr(self, 'toplam_label') or not hasattr(self, 'iskonto_label') or not hasattr(self, 'net_tutar_label'):
             print("Uyarı: Toplam UI etiketleri tanımlı değil.")
             return # Etiketler yoksa güncelleme yapma


        # Toplam tutar _sepeti_yukle içinde hesaplanıyor
        # İskonto şu an için 0, ileride iskonto özelliği eklenirse burada hesaplanır
        self.iskonto = 0.0

        # Net Tutar = Toplam Tutar - İskonto - Ara Ödemeler
        net_tutar = self.toplam_tutar - self.iskonto - ara_odeme_toplam

        self.toplam_label.config(text=f"Toplam: {self.toplam_tutar:.0f} ₺")
        self.iskonto_label.config(text=f"İskonto: {self.iskonto:.0f} ₺")
        self.net_tutar_label.config(text=f"Net Tutar: {max(0.0, net_tutar):.0f} ₺") # Negatif olmaması için max(0.0, ...)


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
                self.cursor.execute("SELECT ad, soyad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri:
                    musteri_adi = f"{musteri['ad']} {musteri['soyad']}".strip() if musteri['ad'] or musteri['soyad'] else "Misafir"
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
                self.cursor.execute("SELECT ad, soyad, cumulative_balance FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri:
                    musteri_adi = f"{musteri['ad']} {musteri['soyad']}".strip() if musteri['ad'] or musteri['soyad'] else "Misafir"
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
                self._masa_butonlarini_olustur() # Masa butonlarını günceller


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
             self._masa_butonlarini_olustur()
             return

        masa_durum = masa_info['durum']
        musteri_id = masa_info['musteri_id']
        masa_oturum_toplami = masa_info['toplam'] if masa_info['toplam'] is not None else 0.0


        if masa_durum != 'dolu':
             messagebox.showwarning("Uyarı", "Bu masa dolu değil veya zaten kapatılmış.", parent=self.adisyon_frame)
             self._sepeti_yukle()
             self._masa_butonlarini_olustur()
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

        # Anahtar adı 'ara_odeme_toplam' olarak kullanılmalı
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
            self.cursor.execute("SELECT acilis FROM masa_gecmisi WHERE masa_no = ? ORDER BY kapanis DESC LIMIT 1", (masa_no,))
            acilis_gecmis_row = self.cursor.fetchone()
            acilis_str_display = datetime.strptime(acilis_gecmis_row['acilis'], DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if acilis_gecmis_row and acilis_gecmis_row['acilis'] else '-'

            fatura += f"Açılış: {acilis_str_display}\n"
            fatura += f"Kapanış: {self._tarih_saat_al_display_format()}\n"
            fatura += f"Ödeme Türü: {odeme_turu}\n"

            if musteri_id:
                self.cursor.execute("SELECT ad, soyad FROM musteriler WHERE musteri_id = ?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri and (musteri['ad'] or musteri['soyad']):
                    fatura += f"Müşteri: {musteri['ad']} {musteri['soyad']}".strip() + "\n"
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

            self._masa_butonlarini_olustur()

            messagebox.showinfo("Başarılı", f"Masa {masa_no} kapatıldı ({odeme_turu}).", parent=self.adisyon_frame)

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ödeme yapılırken hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Ödeme yapılırken beklenmedik hata oluştu (Masa {masa_no}): {e}", parent=self.adisyon_frame)
            print(f"Ödeme yapma hatası (Masa {masa_no}): {e}")
            import traceback
            traceback.print_exc()


    def indirimi_uygula_action(self):
        """Adisyon toplamına indirim uygular."""
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!", parent=self.adisyon_frame)
            return

        masa_no = self.aktif_masa

        try:
            indirim_orani = simpledialog.askfloat("İndirim Uygula", "Uygulanacak indirim oranını girin (%):",
                                                 minvalue=0.0, maxvalue=100.0, parent=self.root)

            if indirim_orani is None: # Kullanıcı iptal etti
                return

            if indirim_orani < 0 or indirim_orani > 100:
                 messagebox.showwarning("Uyarı", "Geçerli bir indirim oranı girin (0-100 arası).", parent=self.adisyon_frame)
                 return

            # Masanın mevcut toplamını al
            self.cursor.execute("SELECT toplam FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_toplam_row = self.cursor.fetchone()
            if not masa_toplam_row:
                 messagebox.showwarning("Uyarı", f"Masa {masa_no} bilgisi bulunamadı.", parent=self.adisyon_frame)
                 return

            mevcut_toplam = masa_toplam_row['toplam'] if masa_toplam_row['toplam'] is not None else 0.0

            # İndirimli toplamı hesapla
            indirim_miktari = mevcut_toplam * (indirim_orani / 100.0)
            indirimli_toplam = mevcut_toplam - indirim_miktari

            # Masanın toplamını veritabanında güncelle
            self.cursor.execute("UPDATE masalar SET toplam = ? WHERE masa_no = ?", (indirimli_toplam, masa_no))
            self.conn.commit()

            # UI'ı güncelle
            self._sepeti_yukle() # Adisyon listesini ve toplam etiketini günceller
            self._masa_butonlarini_olustur() # Masa butonundaki toplamı güncelle

            messagebox.showinfo("Başarılı", f"Masa {masa_no} hesabına %{indirim_orani:.0f} indirim uygulandı.\nYeni Toplam: {indirimli_toplam:.0f} ₺", parent=self.adisyon_frame)


        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir sayısal değer girin.", parent=self.adisyon_frame)
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"İndirim uygulanırken hata oluştu: {e}", parent=self.adisyon_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"İndirim uygulanırken beklenmedik hata: {e}", parent=self.adisyon_frame)
            print(f"İndirim uygulama hatası: {e}")


    # --- Ürün Yönetimi Sekmesi Fonksiyonları ---

    def urun_arayuz_olustur(self):
        """Ürün Yönetimi sekmesi arayüzünü oluşturur.
        Kategori alanı Combobox olarak güncellendi ve 'Kategori Ekle Bilgi' butonu kaldırıldı."""
        # Sol Panel (Ürün Listesi)
        urun_liste_frame = ttk.Frame(self.urun_frame)
        urun_liste_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PAD_X))

        ttk.Label(urun_liste_frame, text="Ürün Listesi", font=('Arial', 12, 'bold')).pack(pady=PAD_Y)

        # Treeview ve Scrollbar
        treeview_scrollbar_frame = ttk.Frame(urun_liste_frame)
        treeview_scrollbar_frame.pack(fill=tk.BOTH, expand=True)

        self.urun_tree = ttk.Treeview(treeview_scrollbar_frame, columns=("Sıra", "Adı", "Fiyatı", "Kategori", "Aktif"),
                                      show="headings")
        self.urun_tree.heading("Sıra", text="Sıra")
        self.urun_tree.heading("Adı", text="Ürün Adı")
        self.urun_tree.heading("Fiyatı", text="Fiyatı (₺)")
        self.urun_tree.heading("Kategori", text="Kategori")
        self.urun_tree.heading("Aktif", text="Aktif") # Aktif sütunu eklendi

        self.urun_tree.column("Sıra", width=50, anchor='center')
        self.urun_tree.column("Adı", width=150)
        self.urun_tree.column("Fiyatı", width=80, anchor='e')
        self.urun_tree.column("Kategori", width=100)
        self.urun_tree.column("Aktif", width=60, anchor='center') # Aktif sütun genişliği

        self.urun_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        urun_tree_scrollbar = ttk.Scrollbar(treeview_scrollbar_frame, orient=tk.VERTICAL, command=self.urun_tree.yview)
        urun_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.urun_tree.configure(yscrollcommand=urun_tree_scrollbar.set)

        self.urun_tree.bind("<<TreeviewSelect>>", self._urun_sec) # Ürün seçildiğinde _urun_sec çağrılır


        # Sağ Panel (Ürün Bilgileri ve Ekle/Güncelle/Sil Formu)
        urun_form_frame = ttk.Frame(self.urun_frame)
        urun_form_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(urun_form_frame, text="Ürün Bilgileri", font=('Arial', 12, 'bold')).pack(pady=PAD_Y)

        ttk.Label(urun_form_frame, text="Sıra:").pack(anchor=tk.W)
        self.urun_sira_entry = ttk.Entry(urun_form_frame, width=30)
        self.urun_sira_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(urun_form_frame, text="Ürün Adı:").pack(anchor=tk.W)
        self.urun_adi_entry = ttk.Entry(urun_form_frame, width=30)
        self.urun_adi_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(urun_form_frame, text="Fiyatı (₺):").pack(anchor=tk.W)
        self.urun_fiyat_entry = ttk.Entry(urun_form_frame, width=30)
        self.urun_fiyat_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(urun_form_frame, text="Kategori:").pack(anchor=tk.W)
        # Kategori Combobox eklendi
        self.urun_kategori_combobox = ttk.Combobox(urun_form_frame, width=27) # Genişlik ayarlandı
        self.urun_kategori_combobox.pack(pady=(0, PAD_Y), fill=tk.X)
        # Combobox'ı mevcut kategorilerle doldur
        self.urun_kategori_combobox['values'] = self._kategorileri_getir(include_tumu=False) # 'Tümü' hariç kategoriler

        # Aktif Checkbutton
        self.urun_aktif_var = tk.IntVar(value=1)
        ttk.Checkbutton(urun_form_frame, text="Aktif", variable=self.urun_aktif_var).pack(anchor=tk.W, pady=(0, PAD_Y))


        # Butonlar Frame (Yan yana butonlar için)
        button_frame = ttk.Frame(urun_form_frame)
        button_frame.pack(pady=PAD_Y, fill=tk.X)

        # Ürün Yönetimi Butonları
        ttk.Button(button_frame, text="Yeni Ürün Ekle", style="Yonetim.TButton",
                   command=self._urun_ekle).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Ürünü Güncelle", style="Yonetim.TButton",
                   command=self._urun_guncelle).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Ürünü Sil", style="Temizle.TButton", command=self._urun_sil).pack(side=tk.LEFT,
                                                                                                      fill=tk.X, expand=True)

        # Kategori Yönetimi Butonları (Ayrı satırda)
        kategori_button_frame = ttk.Frame(urun_form_frame)
        kategori_button_frame.pack(pady=(0, PAD_Y), fill=tk.X)
        # 'Kategori Ekle Bilgi' butonu kaldırıldı.
        # ttk.Button(kategori_button_frame, text="Kategori Ekle Bilgi", style="Yonetim.TButton",
        #            command=self._kategori_ekle_bilgi).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(kategori_button_frame, text="Kategori Sil", style="Temizle.TButton",
                   command=self._kategori_sil).pack(side=tk.LEFT, fill=tk.X, expand=True) # Bu buton kalıyor

        # Formu temizle ve listeyi yükle
        self._urun_formunu_temizle() # Ürün formu temizlendi
        self._urunleri_yukle() # Ürünleri Treeview'e yükle

    def _urunleri_yukle(self):
        """Ürünler tablosundaki tüm ürünleri Ürün Yönetimi sekmesindeki Treeview'a yükler."""
        # Treeview'ı temizle
        for item in self.urun_tree.get_children():
            self.urun_tree.delete(item)

        try:
            # Ürünleri sıraya göre çek
            self.cursor.execute("SELECT id, sira, urun_adi, fiyat, kategori, aktif FROM urunler ORDER BY sira ASC, urun_adi ASC")
            urunler = self.cursor.fetchall()

            for urun in urunler:
                # Aktif bilgisini string'e çevir ("Aktif" veya "Pasif")
                aktif_status = "Aktif" if urun['aktif'] == 1 else "Pasif"
                self.urun_tree.insert("", tk.END, iid=urun['id'], values=(
                    urun['sira'],
                    urun['urun_adi'],
                    f"{urun['fiyat']:.0f} ₺", # Fiyatı formatla
                    urun['kategori'],
                    aktif_status # Aktif statusunu ekle
                ))

        except sqlite3.Error as e:
            print(f"Ürünleri yükleme hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Ürünler yüklenirken hata oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik hata oluştu (_urunleri_yukle): {e}")

    def _urun_sec(self, event):
        """Ürün listesinden bir ürün seçildiğinde form alanlarını doldurur.
        Kategori Combobox doldurma eklendi."""
        # selection() seçili öğelerin iid'lerini içeren bir tuple döndürür.
        selected_items = self.urun_tree.selection()
        if not selected_items:
            self._urun_formunu_temizle() # Seçim kalkarsa formu temizle
            self.secili_urun_id = None
            return

        # Genellikle tek bir öğe seçilir, tuple'ın ilk öğesini (yani iid'yi) alalım.
        selected_iid = selected_items[0]

        # selected_iid zaten Treeview öğesinin iid'si (veritabanındaki urun['id'] integer değeri)
        # Bu değeri doğrudan secili_urun_id'ye atayın.
        self.secili_urun_id = selected_iid

        # Seçilen öğenin değerlerini al (form alanlarını doldurmak için)
        # item() metoduna tekil iid'yi gönderebiliriz.
        item_values = self.urun_tree.item(selected_iid, 'values')

        # item_values tuple'ının boyutunu kontrol et
        # Beklenen 5 sütun var: Sıra, Adı, Fiyatı, Kategori, Aktif
        if len(item_values) < 5:
            print(f"Hata: Seçilen ürün öğesi beklenenden az değer içeriyor: {item_values}")
            messagebox.showwarning("Hata", "Seçilen ürün bilgisi eksik.", parent=self.urun_frame)
            self._urun_formunu_temizle()
            self.secili_urun_id = None
            return

        try:
            # Değerleri ilgili giriş alanlarına yerleştir
            # İndexler: Sıra=0, Adı=1, Fiyatı=2, Kategori=3, Aktif=4
            sira = item_values[0] if item_values[0] is not None else ""
            urun_adi = item_values[1] if item_values[1] is not None else ""
            # Fiyatı alırken ' ₺' karakterini temizle, None kontrolü eklendi
            fiyat_str = item_values[2].replace(' ₺', '').strip() if item_values[2] is not None else ""
            kategori = item_values[3] if item_values[3] is not None else ""
            aktif_str = item_values[4] if item_values[4] is not None else "Pasif" # "Aktif" veya "Pasif"


            if hasattr(self, 'urun_sira_entry'): self.urun_sira_entry.delete(0, tk.END); self.urun_sira_entry.insert(0, sira)
            if hasattr(self, 'urun_adi_entry'): self.urun_adi_entry.delete(0, tk.END); self.urun_adi_entry.insert(0, urun_adi)
            if hasattr(self, 'urun_fiyat_entry'): self.urun_fiyat_entry.delete(0, tk.END); self.urun_fiyat_entry.insert(0, fiyat_str) # String olarak insert et

            # Kategori Combobox'ı doldur
            if hasattr(self, 'urun_kategori_combobox'):
                 # Mevcut kategorileri yükle (eğer Combobox boşsa veya kategori listede yoksa diye)
                 self.urun_kategori_combobox['values'] = self._kategorileri_getir(include_tumu=False)
                 # Seçilen ürünün kategorisini Combobox'ta göster
                 self.urun_kategori_combobox.set(kategori) # <-- Combobox'a değeri set et

            # if hasattr(self, 'urun_kategori_entry'): self.urun_kategori_entry.delete(0, tk.END); self.urun_kategori_entry.insert(0, kategori) # <-- Entry doldurma kaldırıldı


            # Aktif checkbox'ı ayarla
            if hasattr(self, 'urun_aktif_var'):
                if aktif_str == "Aktif":
                    self.urun_aktif_var.set(1)
                else:
                    self.urun_aktif_var.set(0)


        except IndexError:
            print(f"Hata: Treeview öğesi değerlerine erişirken index hatası (_urun_sec): {item_values}")
            messagebox.showerror("Hata", "Ürün bilgileri yüklenirken beklenmedik hata (IndexError).", parent=self.urun_frame)
            self._urun_formunu_temizle()
            self.secili_urun_id = None
        except Exception as e: # Genel Exception yakalama eklendi
            print(f"Beklenmedik hata oluştu (_urun_sec): {e}")
            messagebox.showerror("Hata", f"Ürün bilgileri yüklenirken beklenmedik hata: {e}", parent=self.urun_frame)
            self._urun_formunu_temizle()
            self.secili_urun_id = None


    def _urun_formunu_temizle(self):
        """Ürün yönetim form alanlarını temizler.
        Kategori Combobox temizleme eklendi."""
        if hasattr(self, 'urun_sira_entry'): self.urun_sira_entry.delete(0, tk.END)
        if hasattr(self, 'urun_adi_entry'): self.urun_adi_entry.delete(0, tk.END)
        if hasattr(self, 'urun_fiyat_entry'): self.urun_fiyat_entry.delete(0, tk.END)
        # Kategori Combobox'ı temizle
        if hasattr(self, 'urun_kategori_combobox'): self.urun_kategori_combobox.set("") # Değerini boş string yap
        # if hasattr(self, 'urun_kategori_entry'): self.urun_kategori_entry.delete(0, tk.END) # <-- Entry temizleme kaldırıldı
        if hasattr(self, 'urun_aktif_var'): self.urun_aktif_var.set(1) # Varsayılan olarak Aktif seçili gelsin
        self.secili_urun_id = None # Seçili ürün ID'sini sıfırla


    def _urun_ekle(self):
        """Yeni ürün ekler. Kategori Combobox'tan alınır."""
        # UI elementlerinin tanımlı olup olmadığını kontrol et
        if not hasattr(self, 'urun_sira_entry') or \
           not hasattr(self, 'urun_adi_entry') or \
           not hasattr(self, 'urun_fiyat_entry') or \
           not hasattr(self, 'urun_kategori_combobox') or \
           not hasattr(self, 'urun_aktif_var'):
            print("Hata: Ürün formu UI elementleri tanımlı değil (_urun_ekle).")
            messagebox.showerror("Hata", "Ürün ekleme formu hazır değil.", parent=self.urun_frame)
            return

        sira_str = self.urun_sira_entry.get().strip()
        urun_adi = self.urun_adi_entry.get().strip()
        fiyat_str = self.urun_fiyat_entry.get().strip()
        # Kategori Combobox'tan alındı
        kategori = self.urun_kategori_combobox.get().strip() # <-- Combobox değeri alındı
        aktif = self.urun_aktif_var.get() # 1 veya 0

        if not urun_adi or not fiyat_str:
            messagebox.showwarning("Uyarı", "Ürün Adı ve Fiyatı boş bırakılamaz.", parent=self.urun_frame)
            return
        # Kategori boş bırakılabilir, ama uyarı verilebilir
        # if not kategori:
        #     messagebox.showwarning("Uyarı", "Ürün Kategorisi boş bırakılamaz.", parent=self.urun_frame)
        #     return


        try:
            sira = int(sira_str) if sira_str else None # Sıra boş bırakılabilir
            fiyat = float(fiyat_str)
            if fiyat < 0:
                messagebox.showwarning("Uyarı", "Fiyat negatif olamaz.", parent=self.urun_frame)
                return

        except ValueError:
            messagebox.showwarning("Uyarı", "Sıra ve Fiyat için geçerli sayısal değerler girin.", parent=self.urun_frame)
            return

        try:
            self.cursor.execute('''
                INSERT INTO urunler (sira, urun_adi, fiyat, kategori, aktif)
                VALUES (?, ?, ?, ?, ?)
            ''', (sira, urun_adi, fiyat, kategori if kategori else None, aktif)) # Boş kategori None olarak kaydedildi
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi.", parent=self.urun_frame)
            self._urunleri_yukle() # Listeyi yenile
            self._urun_formunu_temizle() # Formu temizle
            self._filter_hizli_satis_buttons() # Hızlı satış butonlarını yenile (yeni kategori/ürün eklenmiş olabilir)
            # Kategori combobox'larını güncelle (Ürün Yönetimi ve Adisyon)
            self._urun_kategori_combobox_guncelle() # Ürün Yönetimi combobox
            self._adisyon_kategori_combobox_guncelle() # Adisyon combobox


        except sqlite3.IntegrityError:
            messagebox.showwarning("Uyarı", "Bu ürün adı zaten mevcut.", parent=self.urun_frame) # Ürün adı unique
            self.conn.rollback() # Hata durumunda geri al
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün eklenirken hata oluştu: {e}", parent=self.urun_frame)
            print(f"Veritabanı hatası _urun_ekle: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün eklenirken beklenmedik hata: {e}", parent=self.urun_frame)
            print(f"Beklenmedik hata _urun_ekle: {e}")


    def _urun_guncelle(self):
        """Seçili ürünü günceller. Kategori Combobox'tan alınır."""
        if self.secili_urun_id is None:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden güncellenecek bir ürün seçin.", parent=self.urun_frame)
            return

        # UI elementlerinin tanımlı olup olmadığını kontrol et
        if not hasattr(self, 'urun_sira_entry') or \
           not hasattr(self, 'urun_adi_entry') or \
           not hasattr(self, 'urun_fiyat_entry') or \
           not hasattr(self, 'urun_kategori_combobox') or \
           not hasattr(self, 'urun_aktif_var'):
            print("Hata: Ürün formu UI elementleri tanımlı değil (_urun_guncelle).")
            messagebox.showerror("Hata", "Ürün güncelleme formu hazır değil.", parent=self.urun_frame)
            return


        sira_str = self.urun_sira_entry.get().strip()
        urun_adi = self.urun_adi_entry.get().strip()
        fiyat_str = self.urun_fiyat_entry.get().strip()
        # Kategori Combobox'tan alındı
        kategori = self.urun_kategori_combobox.get().strip() # <-- Combobox değeri alındı
        aktif = self.urun_aktif_var.get() # 1 veya 0

        if not urun_adi or not fiyat_str:
            messagebox.showwarning("Uyarı", "Ürün Adı ve Fiyatı boş bırakılamaz.", parent=self.urun_frame)
            return
        # if not kategori:
        #     messagebox.showwarning("Uyarı", "Ürün Kategorisi boş bırakılamaz.", parent=self.urun_frame)
        #     return


        try:
            sira = int(sira_str) if sira_str else None # Sıra boş bırakılabilir
            fiyat = float(fiyat_str)
            if fiyat < 0:
                messagebox.showwarning("Uyarı", "Fiyat negatif olamaz.", parent=self.urun_frame)
                return

        except ValueError:
            messagebox.showwarning("Uyarı", "Sıra ve Fiyat için geçerli sayısal değerler girin.", parent=self.urun_frame)
            return

        try:
            self.cursor.execute('''
                UPDATE urunler
                SET sira = ?, urun_adi = ?, fiyat = ?, kategori = ?, aktif = ?
                WHERE id = ?
            ''', (sira, urun_adi, fiyat, kategori if kategori else None, aktif, self.secili_urun_id)) # Boş kategori None olarak kaydedildi
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ürün başarıyla güncellendi.", parent=self.urun_frame)
            self._urunleri_yukle() # Listeyi yenile
            self._urun_formunu_temizle() # Formu temizle
            self._filter_hizli_satis_buttons() # Hızlı satış butonlarını yenile (ürün bilgisi değişmiş olabilir)
            # Kategori combobox'larını güncelle (Ürün Yönetimi ve Adisyon)
            self._urun_kategori_combobox_guncelle() # Ürün Yönetimi combobox
            self._adisyon_kategori_combobox_guncelle() # Adisyon combobox


        except sqlite3.IntegrityError:
            messagebox.showwarning("Uyarı", "Bu ürün adı zaten mevcut.", parent=self.urun_frame) # Ürün adı unique
            self.conn.rollback() # Hata durumunda geri al
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün güncellenirken hata oluştu: {e}", parent=self.urun_frame)
            print(f"Veritabanı hatası _urun_guncelle: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün güncellenirken beklenmedik hata: {e}", parent=self.urun_frame)
            print(f"Beklenmedik hata _urun_guncelle: {e}")


    def _urun_sil(self):
        """Seçili ürünü siler."""
        if self.secili_urun_id is None:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden silinecek bir ürün seçin.", parent=self.urun_frame)
            return

        # Silinecek ürünün adını al
        urun_adi = "Seçili Ürün" # Hata durumunda varsayılan metin
        try:
            self.cursor.execute("SELECT urun_adi FROM urunler WHERE id = ?", (self.secili_urun_id,))
            urun_adi_row = self.cursor.fetchone()
            if urun_adi_row:
                 urun_adi = urun_adi_row['urun_adi']
            else:
                 print(f"Uyarı: Silinecek ürün (ID: {self.secili_urun_id}) veritabanında bulunamadı.")
                 messagebox.showwarning("Uyarı", "Silinecek ürün veritabanında bulunamadı.", parent=self.urun_frame)
                 self._urun_formunu_temizle() # Formu temizle
                 self._urunleri_yukle() # Listeyi yenile
                 return # Ürün yoksa silme işlemine devam etme

        except Exception as e:
            print(f"Silinecek ürün adı alınırken hata (_urun_sil): {e}")
            # urun_adi varsayılan değerinde kalır


        if not messagebox.askyesno("Silme Onayı", f"'{urun_adi}' ürününü silmek istediğinize emin misiniz?", parent=self.urun_frame):
            return # Kullanıcı iptal etti


        try:
            # Ürünü sil
            self.cursor.execute("DELETE FROM urunler WHERE id = ?", (self.secili_urun_id,))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Ürün başarıyla silindi.", parent=self.urun_frame)
            self._urunleri_yukle() # Listeyi yenile
            self._urun_formunu_temizle() # Formu temizle
            self._filter_hizli_satis_buttons() # Hızlı satış butonlarını yenile (ürün silindi)
            # Kategori combobox'larını güncelle (Ürün Yönetimi ve Adisyon)
            self._urun_kategori_combobox_guncelle() # Ürün Yönetimi combobox
            self._adisyon_kategori_combobox_guncelle() # Adisyon combobox


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün silinirken hata oluştu: {e}", parent=self.urun_frame)
            print(f"Veritabanı hatası _urun_sil: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün silinirken beklenmedik hata: {e}", parent=self.urun_frame)
            print(f"Beklenmedik hata _urun_sil: {e}")

    def _kategorileri_getir(self, include_tumu=True):
        """Veritabanındaki aktif ürün kategorilerini getirir ve isteğe bağlı olarak 'Tümü'
        seçeneğini ekler."""
        try:
            # Sadece aktif ürünlerin kategorilerini çek
            self.cursor.execute("SELECT DISTINCT kategori FROM urunler WHERE aktif = 1 AND kategori IS NOT NULL AND kategori != '' ORDER BY kategori")
            # Boş veya NULL kategorileri atla
            kategoriler = [row['kategori'] for row in self.cursor.fetchall()]

            if include_tumu:
                 kategoriler.insert(0, "Tümü") # Başa 'Tümü' seçeneğini ekle

            return kategoriler
        except sqlite3.Error as e:
            print(f"Kategorileri getirme hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Kategoriler yüklenirken hata oluştu: {e}")
            return ["Hata!"] # Hata durumunda sadece hata mesajı dönsün (boş liste yerine)
        except Exception as e:
            print(f"Beklenmedik hata oluştu (_kategorileri_getir): {e}")
            return ["Hata!"] # Hata durumunda sadece hata mesajı dönsün

    def _kategori_ekle(self):
        """Yeni kategori eklemek için pencere açar."""
        yeni_kategori = simpledialog.askstring("Kategori Ekle", "Eklemek istediğiniz kategori adını girin:", parent=self.urun_frame)
        if yeni_kategori and yeni_kategori.strip():
            kategori_adi = yeni_kategori.strip()
            # Kategori ekleme aslında yeni bir ürün eklerken kategori alanına yeni bir değer girmekle olur.
            # Bu fonksiyon sadece kullanıcıya bilgi verebilir veya ürün ekleme formunu açabilir.
            # Şu anki yapıda kategori, ürün ekleme formunda giriliyor.
            messagebox.showinfo("Bilgi", f"'{kategori_adi}' kategorisi, yeni ürün eklerken Kategori alanına yazılarak oluşturulur.", parent=self.urun_frame)
            # Kategori combobox'ını güncelle
            kategoriler = self._kategorileri_getir()
            self.kategori_filtre_combobox['values'] = kategoriler
            # Combobox'ın seçili değerini koru veya 'Tümü' yap
            current_category = self.kategori_filtre_combobox.get()
            if current_category not in kategoriler:
                 self.kategori_filtre_combobox.set("Tümü")


        elif yeni_kategori is not None: # Kullanıcı boş girdi ama iptal etmedi
             messagebox.showwarning("Uyarı", "Kategori adı boş bırakılamaz.", parent=self.urun_frame)


    def _kategori_sil(self):
        """Mevcut kategorilerden birini açılır menüden seçerek siler."""
        kategoriler = self._kategorileri_getir(include_tumu=False) # 'Tümü' hariç kategoriler

        if not kategoriler:
            messagebox.showinfo("Bilgi", "Silinecek aktif kategori bulunamadı.", parent=self.urun_frame)
            return

        # --- Özel Kategori Silme Seçim Penceresi Oluştur ---
        delete_category_dialog = tk.Toplevel(self.root)
        delete_category_dialog.title("Kategori Sil Seçim")
        delete_category_dialog.transient(self.root) # Ana pencere üzerinde kalmasını sağlar
        delete_category_dialog.grab_set() # Ana pencere etkileşimini engeller

        dialog_frame = ttk.Frame(delete_category_dialog, padding="10")
        dialog_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(dialog_frame, text="Lütfen silmek istediğiniz kategoriyi seçin:").pack(pady=PAD_Y)

        # Kategori Seçim Combobox'ı
        delete_category_combobox = ttk.Combobox(dialog_frame, state="readonly", width=30)
        delete_category_combobox.pack(pady=PAD_Y)
        delete_category_combobox['values'] = kategoriler

        # Varsayılan olarak ilk kategoriyi seçili yap
        if kategoriler:
            delete_category_combobox.set(kategoriler[0])

        # Butonlar Frame
        button_frame = ttk.Frame(dialog_frame)
        button_frame.pack(pady=PAD_Y)

        # Silme Butonu
        def on_delete():
            selected_category = delete_category_combobox.get().strip()
            if not selected_category:
                messagebox.showwarning("Uyarı", "Lütfen silmek için bir kategori seçin.", parent=delete_category_dialog)
                return
            # Seçilen kategoriyi pencere objesine ata, böylece ana fonksiyonda erişebiliriz
            delete_category_dialog.selected_category = selected_category
            delete_category_dialog.destroy() # Pencereyi kapat

        # İptal Butonu
        def on_cancel():
            delete_category_dialog.cancelled = True # İptal edildiğini işaretle
            delete_category_dialog.destroy() # Pencereyi kapat

        ttk.Button(button_frame, text="Sil", command=on_delete, style="Temizle.TButton").pack(side=tk.LEFT, padx=(0, PAD_X))
        ttk.Button(button_frame, text="İptal", command=on_cancel).pack(side=tk.LEFT)

        # Pencere kapatma butonuna basıldığında on_cancel'i çağır
        delete_category_dialog.protocol("WM_DELETE_WINDOW", on_cancel)

        # Pencereyi mod_sal yap ve kapanmasını bekle
        self.root.wait_window(delete_category_dialog)
        # --- Özel Pencere Sonu ---

        # Pencere kapandıktan sonra seçilen kategoriyi kontrol et
        if not hasattr(delete_category_dialog, 'selected_category'):
             # Eğer 'selected_category' özelliği yoksa (iptal edildi veya seçilmeden kapatıldı)
             print("Kategori silme işlemi iptal edildi veya kategori seçilmedi.")
             return # İşlemi durdur

        kategori_adi_sil = delete_category_dialog.selected_category # Seçilen kategori adını al

        # Seçilen kategori gerçekten mevcut kategoriler listesinde mi bir kez daha kontrol edebiliriz (Opsiyonel)
        # Ancak Combobox 'readonly' olduğu için listedeki kategorilerden biri seçilmiş olmalı.

        if not messagebox.askyesno("Silme Onayı",
                                   f"'{kategori_adi_sil}' kategorisindeki TÜM ÜRÜNLER silinecektir.\n"
                                   "Bu işlem geri alınamaz!\nDevam etmek istediğinize emin misiniz?",
                                   parent=self.urun_frame):
            print("Kategori silme onayı kullanıcı tarafından iptal edildi.")
            return # Kullanıcı iptal etti

        try:
            # Belirtilen kategorideki ürünleri sil (tam eşleşme ile)
            self.cursor.execute("DELETE FROM urunler WHERE kategori = ?", (kategori_adi_sil,))
            self.conn.commit()
            messagebox.showinfo("Başarılı", f"'{kategori_adi_sil}' kategorisindeki tüm ürünler başarıyla silindi.", parent=self.urun_frame)
            self._urunleri_yukle() # Ürün listesini yenile
            self._urun_formunu_temizle() # Formu temizle
            self._filter_hizli_satis_buttons() # Hızlı satış butonlarını yenile (ürün silindi)
            # Kategori combobox'larını güncelle (Ürün Yönetimi ve Adisyon)
            self._urun_kategori_combobox_guncelle() # Ürün Yönetimi combobox
            self._adisyon_kategori_combobox_guncelle() # Adisyon combobox


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Kategori silinirken hata oluştu: {e}", parent=self.urun_frame)
            print(f"Veritabanı hatası _kategori_sil: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Kategori silinirken beklenmedik hata: {e}", parent=self.urun_frame)
            print(f"Beklenmedik hata _kategori_sil: {e}")

    def _urun_kategori_combobox_guncelle(self):
        """Ürün Yönetimi sekmesindeki kategori Combobox'ını güncel kategorilerle doldurur."""
        if hasattr(self, 'urun_kategori_combobox') and isinstance(self.urun_kategori_combobox, ttk.Combobox):
             try:
                 kategoriler = self._kategorileri_getir(include_tumu=False)
                 self.urun_kategori_combobox['values'] = kategoriler
                 # Combobox'ın mevcut seçili değeri (varsa) listeden silindiyse boş kalır, bu beklenen bir durum.
             except Exception as e:
                  print(f"Ürün kategori combobox güncelleme hatası: {e}")
                  # Hata durumunda bir şey yapmayalım, mevcut liste kalsın veya boş olsun.


    def _adisyon_kategori_combobox_guncelle(self):
        """Adisyon sekmesindeki kategori filtre Combobox'ını güncel kategorilerle doldurur."""
        if hasattr(self, 'kategori_filtre_combobox') and isinstance(self.kategori_filtre_combobox, ttk.Combobox):
             try:
                 kategoriler = self._kategorileri_getir(include_tumu=True) # Adisyon combobox'a 'Tümü' eklenmeli
                 self.kategori_filtre_combobox['values'] = kategoriler
                 # Eğer mevcut seçili değer artık listede yoksa, Combobox ilk değere (Tümü) veya boş değerine döner.
                 # Eğer mevcut seçili değer "Tümü" ise, o seçili kalır.
                 # Basitçe değerleri yeniden atamak genellikle yeterlidir.
                 # Eğer seçili değer kaybolduysa ve ilk değere dönmesini istemiyorsanız, değeri alıp yeni listede var mı kontrol edip tekrar set edebilirsiniz.
                 # self.kategori_filtre_combobox.get() ile mevcut değeri alıp, kategoriler listesinde var mı kontrol edip
                 # varsa tekrar set(mevcut_deger) yapabiliriz. Aksi takdirde set("Tümü") veya set("") yapabiliriz.
                 # Şimdilik basit güncelleme yeterli.

             except Exception as e:
                  print(f"Adisyon kategori combobox güncelleme hatası: {e}")
                   # Hata durumunda bir şey yapmayalım.

    def _filter_hizli_satis_buttons(self, category="Tümü"): # category parametresi eklendi
        """Kategori combobox seçimine veya arama çubuğuna göre hızlı satış butonlarını filtreler."""
        # Önceki butonları temizle
        if hasattr(self, 'hizli_satis_frame') and isinstance(self.hizli_satis_frame, ttk.Frame):
             for widget in self.hizli_satis_frame.winfo_children():
                 widget.destroy()
        else:
             print("Uyarı: self.hizli_satis_frame Frame widget'ı tanımlı değil veya doğru tipte değil.")
             return # İşleme devam etme

        # Ürünleri veritabanından çek
        sql_query = """
            SELECT urun_adi, fiyat, kategori
            FROM urunler
            WHERE aktif = 1 -- Sadece aktif ürünleri göster
        """
        params = [] # Sorgu parametreleri için liste

        # Kategoriye göre filtreleme (eğer 'Tümü' seçilmediyse ve category parametresi geldiyse)
        if category and category != "Tümü":
            sql_query += " AND kategori = ?"
            params.append(category)

        # Arama metnine göre filtreleme (eğer arama metni varsa)
        arama_metni = self.urun_arama_entry.get().strip().lower() if hasattr(self, 'urun_arama_entry') else ""
        if arama_metni:
            # Eğer zaten aktif filtresi varsa AND ile ekle, yoksa WHERE ile ekle (aktif=1 zaten var)
            sql_query += " AND LOWER(urun_adi) LIKE ?"
            params.append(f"%{arama_metni}%")


        # Sıralama koşulunu ekle
        sql_query += " ORDER BY sira ASC, urun_adi ASC"

        try:
            # Sorguyu çalıştır
            self.cursor.execute(sql_query, params)
            urunler = self.cursor.fetchall()

            # Butonları yerleştirmek için grid ayarları
            COLS = 6 # Hızlı satış butonları için sütun sayısı (ayarlanabilir)
            PAD = 4 # Butonlar arası boşluk

            # Grid için satır ağırlıklarını ayarla (Responsive olması için)
            total_rows = (len(urunler) + COLS - 1) // COLS if len(urunler) > 0 else 1 # En az 1 satır yap
            for r in range(total_rows):
                 self.hizli_satis_frame.grid_rowconfigure(r, weight=1)

            # Grid için sütun ağırlıklarını ayarla
            for c in range(COLS):
                 self.hizli_satis_frame.grid_columnconfigure(c, weight=1)


            # Ürün butonlarını oluştur
            for i, urun in enumerate(urunler):
                urun_adi = urun['urun_adi']
                fiyat = urun['fiyat']
                kategori = urun['kategori']

                # Kategori rengini al, yoksa varsayılan
                # KATEGORI_RENKLERI sözlüğünde kategori adı yoksa varsayılan renk kullanılır
                bg_color = KATEGORI_RENKLERI.get(kategori, "#f0f0f0")
                fg_color = get_text_color(bg_color)

                # Buton oluşturma (Formatlama düzeltildi)
                btn = tk.Button(
                    self.hizli_satis_frame,
                    text=f"{urun_adi}\n{fiyat:.0f} ₺",
                    command=lambda u=urun_adi: self._urun_ekle_hizli_satis(u),
                    bg=bg_color,
                    fg=fg_color,
                    font=("Arial", 8, "bold"),
                    relief="raised",
                    justify="center",
                    wraplength=80 # Buton metninin sarmalanacağı genişlik (piksel)
                )

                # Grid'e yerleştirme
                row, col = divmod(i, COLS)
                btn.grid(row=row, column=col, padx=PAD, pady=PAD, sticky="nsew")

            # Canvas'ın scroll bölgesini güncelle
            self.hizli_satis_frame.update_idletasks()
            if hasattr(self, 'hizli_satis_canvas') and isinstance(self.hizli_satis_canvas, tk.Canvas):
                 bbox = self.hizli_satis_canvas.bbox("all")
                 if bbox:
                     self.hizli_satis_canvas.config(scrollregion=bbox)
                 else:
                     # Ürün yoksa scroll bölgesini sıfırla
                     self.hizli_satis_canvas.config(scrollregion=(0,0,self.hizli_satis_canvas.winfo_width(), self.hizli_satis_canvas.winfo_height()))


        except sqlite3.Error as e:
            print(f"Hızlı satış butonları oluşturma hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Hızlı satış butonları oluşturulurken hata oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik hata oluştu (_hizli_satis_butonlari_olustur): {e}")


    def _urun_ara(self, event=None):
        """Ürün arama girişine göre hızlı satış butonlarını filtreler ve kategori filtresini sıfırlar."""
        # Arama yapıldığında kategori filtresini 'Tümü' yap
        if hasattr(self, 'kategori_filtre_combobox'):
             self.kategori_filtre_combobox.set("Tümü")

        # Filterleme işlemini _filter_hizli_satis_buttons fonksiyonuna devret
        self._filter_hizli_satis_buttons("Tümü") # Arama yapıldığında tüm kategorileri göster


    # --- Müşteri İşlemleri Sekmesi Fonksiyonları ---

    def musteri_arayuz_olustur(self):
        """Müşteri İşlemleri sekmesi arayüzünü oluşturur.
        Bakiye alanı yeni müşteri için aktif hale getirildi."""
        # Sol Panel (Müşteri Listesi)
        musteri_liste_frame = ttk.Frame(self.musteri_frame)
        musteri_liste_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, PAD_X))

        ttk.Label(musteri_liste_frame, text="Müşteri Listesi", font=('Arial', 12, 'bold')).pack(pady=PAD_Y)

        # Treeview ve Scrollbar
        treeview_scrollbar_frame = ttk.Frame(musteri_liste_frame)
        treeview_scrollbar_frame.pack(fill=tk.BOTH, expand=True)

        self.musteri_tree = ttk.Treeview(treeview_scrollbar_frame,
                                         columns=("Adı Soyadı", "Telefon", "Adres", "Bakiye"), show="headings")
        self.musteri_tree.heading("Adı Soyadı", text="Adı Soyadı")
        self.musteri_tree.heading("Telefon", text="Telefon")
        self.musteri_tree.heading("Adres", text="Adres")
        self.musteri_tree.heading("Bakiye", text="Bakiye (₺)")


        self.musteri_tree.column("Adı Soyadı", width=150)
        self.musteri_tree.column("Telefon", width=100)
        self.musteri_tree.column("Adres", width=200)
        self.musteri_tree.column("Bakiye", width=80, anchor='e') # Bakiye sağa hizalı


        self.musteri_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        musteri_tree_scrollbar = ttk.Scrollbar(treeview_scrollbar_frame, orient=tk.VERTICAL, command=self.musteri_tree.yview)
        musteri_tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.musteri_tree.configure(yscrollcommand=musteri_tree_scrollbar.set)

        self.musteri_tree.bind("<<TreeviewSelect>>", self._musteri_sec) # Müşteri seçildiğinde _musteri_sec çağrılır


        # Sağ Panel (Müşteri Bilgileri ve Ekle/Güncelle/Sil Formu)
        musteri_form_frame = ttk.Frame(self.musteri_frame)
        musteri_form_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(musteri_form_frame, text="Müşteri Bilgileri", font=('Arial', 12, 'bold')).pack(pady=PAD_Y)

        ttk.Label(musteri_form_frame, text="Adı:").pack(anchor=tk.W)
        self.musteri_ad_entry = ttk.Entry(musteri_form_frame, width=30)
        self.musteri_ad_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(musteri_form_frame, text="Soyadı:").pack(anchor=tk.W)
        self.musteri_soyad_entry = ttk.Entry(musteri_form_frame, width=30)
        self.musteri_soyad_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(musteri_form_frame, text="Telefon:").pack(anchor=tk.W)
        self.musteri_telefon_entry = ttk.Entry(musteri_form_frame, width=30)
        self.musteri_telefon_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(musteri_form_frame, text="Adres:").pack(anchor=tk.W)
        self.musteri_adres_entry = ttk.Entry(musteri_form_frame, width=30)
        self.musteri_adres_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        ttk.Label(musteri_form_frame, text="Bakiye (₺):").pack(anchor=tk.W)
        # Bakiye alanı artık başlangıçta normal, durumu _musteri_formu_temizle ve _musteri_sec içinde ayarlanacak
        self.musteri_bakiye_entry = ttk.Entry(musteri_form_frame, width=30, state='normal') # <-- state='readonly' kaldırıldı
        self.musteri_bakiye_entry.pack(pady=(0, PAD_Y), fill=tk.X)

        # Butonlar Frame (Yan yana butonlar için)
        button_frame = ttk.Frame(musteri_form_frame)
        button_frame.pack(pady=PAD_Y, fill=tk.X)

        # Müşteri Yönetimi Butonları
        ttk.Button(button_frame, text="Yeni Müşteri Ekle", style="Yonetim.TButton",
                   command=self._musteri_ekle).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Müşteriyi Güncelle", style="Yonetim.TButton",
                   command=self._musteri_guncelle).pack(side=tk.LEFT, padx=(0, PAD_X), fill=tk.X, expand=True)
        ttk.Button(button_frame, text="Müşteriyi Sil", style="Temizle.TButton",
                   command=self._musteri_sil).pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Müşteri Atama Butonu (Ayrı satırda)
        assign_button_frame = ttk.Frame(musteri_form_frame)
        assign_button_frame.pack(pady=(0, PAD_Y), fill=tk.X)
        ttk.Button(assign_button_frame, text="Müşteriyi Masaya Ata", style="Yonetim.TButton",
                   command=self._initiate_assign_customer_mode).pack(fill=tk.X)

        # Formu temizle ve listeyi yükle (Bu çağrı bakiye alanının durumunu ayarlayacak)
        self._musteri_formu_temizle() # Müşteri formu temizlendi
        self._musteri_listesini_guncelle() # Müşterileri Treeview'e yükle

    def _musteri_listesini_guncelle(self):
        """Müşteriler tablosundaki tüm müşterileri Müşteri İşlemleri sekmesindeki Treeview'a yükler."""
        # Treeview'ı temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)

        try:
            self.cursor.execute("SELECT musteri_id, ad, soyad, telefon, adres, cumulative_balance FROM musteriler ORDER BY ad ASC, soyad ASC")
            musteriler = self.cursor.fetchall()

            for musteri in musteriler:
                tam_ad = f"{musteri['ad']} {musteri['soyad']}".strip() # Ad ve soyadı birleştir
                self.musteri_tree.insert("", tk.END, iid=musteri['musteri_id'], values=(
                    tam_ad,
                    musteri['telefon'],
                    musteri['adres'],
                    f"{musteri['cumulative_balance']:.0f} ₺" # Bakiye formatlı
                ))

        except sqlite3.Error as e:
            print(f"Müşteri listesi yükleme hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Müşteriler yüklenirken hata oluştu: {e}")
        except Exception as e:
            print(f"Beklenmedik hata oluştu (_musteri_listesini_guncelle): {e}")


    def _musteri_sec(self, event):
        """Müşteri listesinden bir müşteri seçildiğinde form alanlarını
        doldurur ve bakiye alanını salt okunur yapar."""
        # selection() seçili öğelerin iid'lerini içeren bir tuple döndürür.
        selected_items = self.musteri_tree.selection()
        if not selected_items:
            # Seçim kalkarsa veya boşsa formu temizle ve secili_musteri_id'yi sıfırla
            self._musteri_formu_temizle()
            self.secili_musteri_id = None
            return

        # Genellikle tek bir öğe seçilir, tuple'ın ilk öğesini alalım.
        selected_item_id = selected_items[0]

        # selected_item_id zaten Treeview öğesinin iid'si (veritabanındaki musteri_id)
        # Bu değeri doğrudan secili_musteri_id'ye atayın.
        self.secili_musteri_id = selected_item_id

        try:
            # Müşteri bilgilerini veritabanından çek
            self.cursor.execute("SELECT ad, soyad, telefon, adres, cumulative_balance FROM musteriler WHERE musteri_id = ?", (self.secili_musteri_id,))
            musteri = self.cursor.fetchone()

            if musteri:
                # UI elementlerinin tanımlı olup olmadığını kontrol etmeden set etme
                if hasattr(self, 'musteri_ad_entry'):
                    self.musteri_ad_entry.delete(0, tk.END); self.musteri_ad_entry.insert(0, musteri['ad'] if musteri['ad'] is not None else "")
                if hasattr(self, 'musteri_soyad_entry'):
                    self.musteri_soyad_entry.delete(0, tk.END); self.musteri_soyad_entry.insert(0, musteri['soyad'] if musteri['soyad'] is not None else "")
                if hasattr(self, 'musteri_telefon_entry'):
                    self.musteri_telefon_entry.delete(0, tk.END); self.musteri_telefon_entry.insert(0, musteri['telefon'] if musteri['telefon'] is not None else "")
                if hasattr(self, 'musteri_adres_entry'):
                    self.musteri_adres_entry.delete(0, tk.END); self.musteri_adres_entry.insert(0, musteri['adres'] if musteri['adres'] is not None else "")

                # Bakiye alanını güncelle (manuel girişi engellemek için readonly yap)
                if hasattr(self, 'musteri_bakiye_entry'):
                    self.musteri_bakiye_entry.config(state='normal') # Değeri set etmeden önce normal yap
                    self.musteri_bakiye_entry.delete(0, tk.END)
                    bakiye = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0
                    self.musteri_bakiye_entry.insert(0, f"{bakiye:.0f}") # Bakiye formatlı
                    self.musteri_bakiye_entry.config(state='readonly') # <-- Bakiye alanı salt okunur yapıldı

            else:
                # Seçili müşteri veritabanında bulunamazsa formu temizle
                print(f"Uyarı: Seçili müşteri (ID: {self.secili_musteri_id}) _musteri_sec içinde veritabanında bulunamadı.")
                self._musteri_formu_temizle()
                self.secili_musteri_id = None # ID'yi sıfırla
                messagebox.showwarning("Uyarı", "Seçili müşteri bilgisi veritabanında bulunamadı.", parent=self.musteri_frame)


        except sqlite3.Error as e:
            print(f"Müşteri seçme hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Müşteri bilgileri yüklenirken hata oluştu: {e}")
            self._musteri_formu_temizle()
            self.secili_musteri_id = None
        except Exception as e: # Genel Exception yakalama eklendi
            print(f"Beklenmedik hata oluştu (_musteri_sec): {e}")
            messagebox.showerror("Hata", f"Müşteri bilgileri yüklenirken beklenmedik hata: {e}")
            self._musteri_formu_temizle()
            self.secili_musteri_id = None


    def _musteri_formu_temizle(self):
        """Müşteri yönetim form alanlarını temizler ve bakiye alanını aktif yapar."""
        if hasattr(self, 'musteri_ad_entry'): self.musteri_ad_entry.delete(0, tk.END)
        if hasattr(self, 'musteri_soyad_entry'): self.musteri_soyad_entry.delete(0, tk.END)
        if hasattr(self, 'musteri_telefon_entry'): self.musteri_telefon_entry.delete(0, tk.END)
        if hasattr(self, 'musteri_adres_entry'): self.musteri_adres_entry.delete(0, tk.END)

        if hasattr(self, 'musteri_bakiye_entry'):
            self.musteri_bakiye_entry.config(state='normal') # <-- Bakiye alanı aktif yapıldı
            self.musteri_bakiye_entry.delete(0, tk.END)
            self.musteri_bakiye_entry.insert(0, "0.0") # <-- Varsayılan başlangıç bakiyesi
            self.musteri_bakiye_entry.config(state='normal') # Tekrar aktif yapma garantisi


        self.secili_musteri_id = None # Seçili müşteri ID'sini sıfırla


    def _musteri_ekle(self):
        """Yeni müşteri ekler. Başlangıç bakiyesi formdan alınır."""
        # UI elementlerinin tanımlı olup olmadığını kontrol et
        if not hasattr(self, 'musteri_ad_entry') or \
           not hasattr(self, 'musteri_soyad_entry') or \
           not hasattr(self, 'musteri_telefon_entry') or \
           not hasattr(self, 'musteri_adres_entry') or \
           not hasattr(self, 'musteri_bakiye_entry'):
            print("Hata: Müşteri formu UI elementleri tanımlı değil (_musteri_ekle).")
            messagebox.showerror("Hata", "Müşteri ekleme formu hazır değil.", parent=self.musteri_frame)
            return

        ad = self.musteri_ad_entry.get().strip()
        soyad = self.musteri_soyad_entry.get().strip()
        telefon = self.musteri_telefon_entry.get().strip()
        adres = self.musteri_adres_entry.get().strip()
        # Başlangıç bakiyesi formdan alındı
        bakiye_str = self.musteri_bakiye_entry.get().strip() # <-- Bakiye değeri alındı

        if not ad:
            messagebox.showwarning("Uyarı", "Müşteri Adı boş bırakılamaz.", parent=self.musteri_frame)
            return
        if not telefon:
             # Telefon numarası unique olduğu için boş olmaması daha iyi olabilir
             messagebox.showwarning("Uyarı", "Telefon numarası boş bırakılamaz.", parent=self.musteri_frame)
             return


        try:
            # Bakiye değerini float'a çevir, boşsa 0 kabul et
            initial_balance = float(bakiye_str) if bakiye_str else 0.0
            # Negatif bakiye (alacak) de girilebilir, kontrol etmeye gerek yok.


        except ValueError:
            messagebox.showwarning("Uyarı", "Bakiye için geçerli bir sayısal değer girin.", parent=self.musteri_frame)
            return


        try:
            # Kayıt tarihi ekle
            kayit_tarihi = self._tarih_saat_al_db_format()

            self.cursor.execute('''
                INSERT INTO musteriler (ad, soyad, telefon, adres, kayit_tarihi, cumulative_balance)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (ad, soyad, telefon, adres, kayit_tarihi, initial_balance)) # <-- Bakiye değeri eklendi

            self.conn.commit()
            messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi.", parent=self.musteri_frame)
            self._musteri_listesini_guncelle() # Listeyi yenile
            self._musteri_formu_temizle() # Formu temizle (bu bakiye alanını tekrar aktif yapar)


        except sqlite3.IntegrityError:
            messagebox.showwarning("Uyarı", f"Bu telefon numarası ({telefon}) zaten mevcut bir müşteriye ait.", parent=self.musteri_frame) # Telefon unique
            self.conn.rollback() # Hata durumunda geri al
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri eklenirken hata oluştu: {e}", parent=self.musteri_frame)
            print(f"Veritabanı hatası _musteri_ekle: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri eklenirken beklenmedik hata: {e}", parent=self.musteri_frame)
            print(f"Beklenmedik hata _musteri_ekle: {e}")

    def _musteri_guncelle(self):
        """Seçili müşteriyi günceller. Bakiye alanı güncellenmez."""
        if self.secili_musteri_id is None:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden güncellenecek bir müşteri seçin.", parent=self.musteri_frame)
            return

        # UI elementlerinin tanımlı olup olmadığını kontrol et
        if not hasattr(self, 'musteri_ad_entry') or \
           not hasattr(self, 'musteri_soyad_entry') or \
           not hasattr(self, 'musteri_telefon_entry') or \
           not hasattr(self, 'musteri_adres_entry'):
            print("Hata: Müşteri formu UI elementleri tanımlı değil (_musteri_guncelle).")
            messagebox.showerror("Hata", "Müşteri güncelleme formu hazır değil.", parent=self.musteri_frame)
            return

        ad = self.musteri_ad_entry.get().strip()
        soyad = self.musteri_soyad_entry.get().strip()
        telefon = self.musteri_telefon_entry.get().strip()
        adres = self.musteri_adres_entry.get().strip()

        if not ad:
            messagebox.showwarning("Uyarı", "Müşteri Adı boş bırakılamaz.", parent=self.musteri_frame)
            return
        if not telefon:
             messagebox.showwarning("Uyarı", "Telefon numarası boş bırakılamaz.", parent=self.musteri_frame)
             return

        try:
            # Müşteri bilgilerini güncelle, bakiye alanını DAHİL ETME
            self.cursor.execute('''
                UPDATE musteriler
                SET ad = ?, soyad = ?, telefon = ?, adres = ?
                WHERE musteri_id = ?
            ''', (ad, soyad, telefon, adres, self.secili_musteri_id)) # <-- Bakiye güncelleme sorgusundan çıkarıldı

            self.conn.commit()
            messagebox.showinfo("Başarılı", "Müşteri başarıyla güncellendi.", parent=self.musteri_frame)
            self._musteri_listesini_guncelle() # Listeyi yenile
            self._musteri_formu_temizle() # Formu temizle


        except sqlite3.IntegrityError:
            messagebox.showwarning("Uyarı", f"Bu telefon numarası ({telefon}) zaten mevcut bir müşteriye ait.", parent=self.musteri_frame) # Telefon unique
            self.conn.rollback() # Hata durumunda geri al
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri güncellenirken hata oluştu: {e}", parent=self.musteri_frame)
            print(f"Veritabanı hatası _musteri_guncelle: {e}")
            self.conn.rollback() # Hata durumunda geri al
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri güncellenirken beklenmedik hata: {e}", parent=self.musteri_frame)
            print(f"Beklenmedik hata _musteri_guncelle: {e}")


    def _musteri_sil(self):
        """Seçili müşteriyi siler."""
        if self.secili_musteri_id is None:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden silinecek bir müşteri seçin.", parent=self.musteri_frame)
            return

        # Müşteriye ait açık masa veya bakiye var mı kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar WHERE musteri_id = ? AND durum = 'dolu'", (self.secili_musteri_id,))
        acik_masa_sayisi = self.cursor.fetchone()[0]

        self.cursor.execute("SELECT cumulative_balance FROM musteriler WHERE musteri_id = ?", (self.secili_musteri_id,))
        musteri_bakiye_row = self.cursor.fetchone()
        bakiye = musteri_bakiye_row['cumulative_balance'] if musteri_bakiye_row and musteri_bakiye_row['cumulative_balance'] is not None else 0.0

        if acik_masa_sayisi > 0:
            messagebox.showwarning("Uyarı", f"Bu müşteriye ait {acik_masa_sayisi} adet açık masa bulunmaktadır. Müşteriyi silemezsiniz.", parent=self.musteri_frame)
            return

        # Bakiyesi sıfırdan farklıysa silme
        # Küçük float hatalarını önlemek için bakiye 0'a çok yakınsa da silmeye izin verilebilir
        if abs(bakiye) > 0.01: # 0.01'den büyükse (pozitif veya negatif bakiye)
             messagebox.showwarning("Uyarı", f"Müşterinin bakiyesi ({bakiye:.0f} ₺) sıfırdan farklı olduğu için silinemez.", parent=self.musteri_frame)
             return


        # Silinecek müşterinin adını al
        try:
            self.cursor.execute("SELECT ad, soyad FROM musteriler WHERE musteri_id = ?", (self.secili_musteri_id,))
            musteri_info = self.cursor.fetchone()
            musteri_ad_soyad = f"{musteri_info['ad']} {musteri_info['soyad']}".strip() if musteri_info else "Seçili Müşteri"
        except Exception as e:
             print(f"Silinecek müşteri adı alınırken hata: {e}")
             musteri_ad_soyad = "Seçili Müşteri" # Hata durumunda varsayılan metin


        if not messagebox.askyesno("Silme Onayı", f"{musteri_ad_soyad} müşterisini silmek istediğinize emin misiniz?", parent=self.musteri_frame):
            return

        try:
            self.cursor.execute("DELETE FROM musteriler WHERE musteri_id = ?", (self.secili_musteri_id,))
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Müşteri başarıyla silindi.", parent=self.musteri_frame)
            self._musteri_listesini_guncelle() # Listeyi yenile
            self._musteri_formu_temizle() # Formu temizle

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri silinirken hata oluştu: {e}", parent=self.musteri_frame)
            self.conn.rollback()
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri silinirken beklenmedik hata: {e}", parent=self.musteri_frame)
            print(f"Müşteri silme hatası: {e}")


    def _initiate_assign_customer_mode(self):
        """Müşteri atama modunu başlatır."""
        if self.secili_musteri_id is None:
            messagebox.showwarning("Uyarı", "Lütfen önce listeden atanacak bir müşteri seçin.", parent=self.musteri_frame)
            return

        # Müşteri atama moduna geç
        self.current_mode = "assign_customer_selection"
        messagebox.showinfo("Bilgi", "Lütfen müşteriyi atamak istediğiniz masayı seçin.", parent=self.musteri_frame)

        # Masa yönetimi sekmesine geç
        self.notebook.select(self.masa_frame)

        # Masa butonlarını güncelle (belki renkleri değişebilir veya sadece bilgi mesajı gösterilebilir)
        # Şimdilik sadece mod bilgisini yazdıralım
        print(f"Mod Değişti: {self.current_mode}")
        # İstenirse masa butonlarının görünümü bu moda göre değiştirilebilir.


    def _assign_customer_to_clicked_masa(self, masa_no):
        """Müşteri atama modunda tıklanan masaya seçili müşteriyi atar."""
        if self.current_mode != "assign_customer_selection":
            # Bu fonksiyon sadece müşteri atama modunda çalışmalı
            return

        if self.secili_musteri_id is None:
            # Mod yanlışlıkla aktif kaldıysa veya müşteri seçimi kaybolduysa
            messagebox.showwarning("Hata", "Atanacak müşteri seçili değil.", parent=self.masa_frame)
            self.current_mode = "normal" # Modu sıfırla
            self._masa_butonlarini_olustur() # Butonları normale döndür
            return

        try:
            # Masanın mevcut durumunu ve müşteri ID'sini kontrol et
            self.cursor.execute("SELECT durum, musteri_id FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_info = self.cursor.fetchone()

            if not masa_info:
                 messagebox.showwarning("Uyarı", f"Masa {masa_no} bilgisi bulunamadı.", parent=self.masa_frame)
                 self.current_mode = "normal" # Modu sıfırla
                 self._masa_butonlarini_olustur() # Butonları normale döndür
                 return

            masa_durum = masa_info['durum']
            mevcut_musteri_id = masa_info['musteri_id']

            # Eğer masa dolu ve başka bir müşteriye aitse uyarı ver
            if masa_durum == 'dolu' and mevcut_musteri_id is not None and mevcut_musteri_id != self.secili_musteri_id:
                 # Mevcut müşterinin adını al
                 self.cursor.execute("SELECT ad, soyad FROM musteriler WHERE musteri_id = ?", (mevcut_musteri_id,))
                 mevcut_musteri_info = self.cursor.fetchone()
                 mevcut_musteri_ad = f"{mevcut_musteri_info['ad']} {mevcut_musteri_info['soyad']}".strip() if mevcut_musteri_info else "Başka Bir Müşteri"

                 response = messagebox.askyesno(
                     "Masa Zaten Dolu",
                     f"Masa {masa_no} şu anda {mevcut_musteri_ad} müşterisine ait.\n"
                     "Seçili müşteriyi bu masaya atamak mevcut müşteriyi kaldıracaktır.\n"
                     "Devam etmek istiyor musunuz?",
                     parent=self.masa_frame
                 )
                 if not response:
                     self.current_mode = "normal" # Modu sıfırla
                     self._masa_butonlarini_olustur() # Butonları normale döndür
                     return # Kullanıcı iptal etti


            # Masaya müşteriyi ata ve durumu güncelle (eğer boşsa dolu yap)
            # Masa doluysa sadece musteri_id güncellenir, toplam değişmez
            # Masa boşsa durum 'dolu' yapılır, musteri_id atanır, açılış zamanı kaydedilir.
            current_time = self._tarih_saat_al_db_format()

            if masa_durum == 'boş':
                self.cursor.execute('''
                    UPDATE masalar
                    SET durum = 'dolu', musteri_id = ?, acilis = ?, son_islem_zamani = ?
                    WHERE masa_no = ?
                ''', (self.secili_musteri_id, current_time, current_time, masa_no))
            else: # Masa doluysa
                 self.cursor.execute('''
                     UPDATE masalar
                     SET musteri_id = ?, son_islem_zamani = ?
                     WHERE masa_no = ?
                 ''', (self.secili_musteri_id, current_time, masa_no))


            self.conn.commit()

            # Müşteri atama modundan çık
            self.current_mode = "normal"
            self.secili_musteri_id = None # Seçili müşteri ID'sini sıfırla

            # UI'ı güncelle
            self._masa_butonlarini_olustur() # Masa butonlarını yenile (yeni müşteri bilgisi görünür)
            # Eğer atanılan masa aktif masaysa adisyon sekmesindeki müşteri bilgisini de güncelle
            if self.aktif_masa == masa_no:
                 self._sepeti_yukle() # Adisyon sekmesindeki müşteri bilgisini günceller

            messagebox.showinfo("Başarılı", f"Müşteri masaya başarıyla atandı.", parent=self.masa_frame)


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri masaya atanırken hata oluştu: {e}", parent=self.masa_frame)
            self.conn.rollback()
            self.current_mode = "normal" # Hata durumunda modu sıfırla
            self._masa_butonlarini_olustur() # Butonları normale döndür
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri masaya atanırken beklenmedik hata: {e}", parent=self.masa_frame)
            print(f"Müşteri atama hatası: {e}")
            self.current_mode = "normal" # Hata durumunda modu sıfırla
            self._masa_butonlarini_olustur() # Butonları normale döndür


    # --- Muhasebe Sekmesi Fonksiyonları ---

    def muhasebe_arayuz_olustur(self):
        """Muhasebe sekmesi arayüzünü oluşturur."""
        ttk.Label(self.muhasebe_frame, text="Muhasebe Raporları", font=('Arial', 14, 'bold')).pack(pady=PAD_Y)

        # Rapor Türü Seçimi
        rapor_secim_frame = ttk.Frame(self.muhasebe_frame)
        rapor_secim_frame.pack(pady=PAD_Y)

        ttk.Label(rapor_secim_frame, text="Rapor Türü:").pack(side=tk.LEFT, padx=(0, PAD_X))
        self.muhasebe_rapor_turu_var = tk.StringVar()
        self.muhasebe_rapor_turu_combobox = ttk.Combobox(rapor_secim_frame, textvariable=self.muhasebe_rapor_turu_var,
                                                values=["Günlük Satış Özeti", "Tarih Aralığı Satış Özeti", "Masa Geçmişi Detaylı Raporu", "Müşteri Bakiye Raporu", "Ürün Satış Raporu"],
                                                state="readonly", width=30)
        self.muhasebe_rapor_turu_combobox.pack(side=tk.LEFT, padx=(0, PAD_X))
        self.muhasebe_rapor_turu_combobox.set("Günlük Satış Özeti") # Varsayılan değer
        # Hata veren satır düzeltildi: Fonksiyon tanımı aşağıda olduğu için burada bind edilebilir.
        self.muhasebe_rapor_turu_combobox.bind("<<ComboboxSelected>>", self._muhasebe_rapor_secimi_degisti)


        # Tarih Seçimi (Tarih Aralığı Raporu için görünür olacak)
        self.muhasebe_tarih_araligi_frame = ttk.Frame(self.muhasebe_frame) # Başlangıçta gizli

        ttk.Label(self.muhasebe_tarih_araligi_frame, text="Başlangıç Tarihi (GG.AA.YYYY):").pack(side=tk.LEFT, padx=(0, PAD_X))
        self.muhasebe_baslangic_tarihi_entry = ttk.Entry(self.muhasebe_tarih_araligi_frame, width=15)
        self.muhasebe_baslangic_tarihi_entry.pack(side=tk.LEFT, padx=(0, PAD_X))
        self.muhasebe_baslangic_tarihi_entry.insert(0, datetime.now().strftime(RAPOR_TARIH_FORMATI)) # Varsayılan bugün

        ttk.Label(self.muhasebe_tarih_araligi_frame, text="Bitiş Tarihi (GG.AA.YYYY):").pack(side=tk.LEFT, padx=(0, PAD_X))
        self.muhasebe_bitis_tarihi_entry = ttk.Entry(self.muhasebe_tarih_araligi_frame, width=15)
        self.muhasebe_bitis_tarihi_entry.pack(side=tk.LEFT)
        self.muhasebe_bitis_tarihi_entry.insert(0, datetime.now().strftime(RAPOR_TARIH_FORMATI)) # Varsayılan bugün

        # Rapor Oluştur Butonu
        ttk.Button(self.muhasebe_frame, text="Rapor Oluştur", style="Rapor.TButton", command=self._muhasebe_rapor_olustur).pack(pady=PAD_Y)

        # Rapor Görüntüleme Alanı
        self.muhasebe_rapor_text = tk.Text(self.muhasebe_frame, wrap=tk.WORD, font=("Courier New", 10))
        self.muhasebe_rapor_text.pack(fill=tk.BOTH, expand=True)

        # Rapor seçimi değiştiğinde tarih aralığı frame'ini göster/gizle
        # Hata veren satır düzeltildi: Fonksiyon tanımı aşağıda olduğu için burada çağrılabilir.
        self._muhasebe_rapor_secimi_degisti()


    def _muhasebe_rapor_secimi_degisti(self, event=None):
        """Muhasebe rapor türü seçimi değiştiğinde tarih aralığı girişlerini gösterir/gizler."""
        secili_rapor = self.muhasebe_rapor_turu_combobox.get()
        if secili_rapor == "Tarih Aralığı Satış Özeti" or secili_rapor == "Masa Geçmişi Detaylı Raporu" or secili_rapor == "Ürün Satış Raporu":
            self.muhasebe_tarih_araligi_frame.pack(pady=(0, PAD_Y), fill=tk.X)
        else:
            self.muhasebe_tarih_araligi_frame.pack_forget()


    def _muhasebe_rapor_olustur(self):
        """Seçilen muhasebe raporunu oluşturur ve görüntüler."""
        secili_rapor = self.muhasebe_rapor_turu_combobox.get()
        self.muhasebe_rapor_text.config(state='normal') # Yazılabilir yap
        self.muhasebe_rapor_text.delete(1.0, tk.END) # Önceki raporu temizle

        try:
            if secili_rapor == "Günlük Satış Özeti":
                self._rapor_gunluk_satis_ozeti()
            elif secili_rapor == "Tarih Aralığı Satış Özeti":
                self._rapor_tarih_araligi_satis_ozeti()
            elif secili_rapor == "Masa Geçmişi Detaylı Raporu":
                self._rapor_masa_gecmisi_detayli()
            elif secili_rapor == "Müşteri Bakiye Raporu":
                self._rapor_musteri_bakiye()
            elif secili_rapor == "Ürün Satış Raporu":
                 self._rapor_urun_satis()
            else:
                self.muhasebe_rapor_text.insert(tk.END, "Lütfen bir rapor türü seçin.")

        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"Rapor oluşturulurken bir hata oluştu: {e}")
            print(f"Rapor oluşturma hatası: {e}")

        self.muhasebe_rapor_text.config(state='disabled') # Salt okunur yap


    def _parse_date_entry(self, date_entry_widget):
        """GG.AA.YYYY formatındaki girişten datetime objesi döndürür."""
        date_str = date_entry_widget.get().strip()
        if not date_str:
            return None
        try:
            # Kullanıcının girdiği formatı parse et
            return datetime.strptime(date_str, RAPOR_TARIH_FORMATI)
        except ValueError:
            messagebox.showwarning("Geçersiz Tarih Formatı", f"Lütfen tarihi {RAPOR_TARIH_FORMATI} formatında girin.", parent=self.muhasebe_frame)
            return None
        except Exception as e:
             print(f"Tarih parse hatası: {e}")
             messagebox.showerror("Hata", f"Tarih işlenirken beklenmedik hata: {e}", parent=self.muhasebe_frame)
             return None


    def _rapor_gunluk_satis_ozeti(self):
        """Günlük satış özet raporunu oluşturur."""
        bugun = datetime.now().strftime(RAPOR_TARIH_FORMATI)
        baslangic_tarihi_db = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).strftime(DB_DATE_FORMAT)
        bitis_tarihi_db = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999).strftime(DB_DATE_FORMAT)


        self.muhasebe_rapor_text.insert(tk.END, f"=== Günlük Satış Özeti ({bugun}) ===\n\n")

        try:
            # Toplam satışları ödeme türüne göre al
            self.cursor.execute('''
                SELECT odeme_turu, COALESCE(SUM(toplam), 0) as toplam_satis
                FROM siparis_gecmisi
                WHERE tarih BETWEEN ? AND ?
                GROUP BY odeme_turu
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            satis_ozeti = self.cursor.fetchall()

            if satis_ozeti:
                for row in satis_ozeti:
                    self.muhasebe_rapor_text.insert(tk.END, f"{row['odeme_turu']}: {row['toplam_satis']:.0f} ₺\n")
            else:
                self.muhasebe_rapor_text.insert(tk.END, "Bugün henüz satış yapılmadı.\n")

            # Toplam ara ödemeleri al
            self.cursor.execute('''
                 SELECT COALESCE(SUM(miktar), 0) as toplam_ara_odeme
                 FROM ara_odemeler
                 WHERE tarih BETWEEN ? AND ?
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            ara_odeme_row = self.cursor.fetchone()
            toplam_ara_odeme = ara_odeme_row['toplam_ara_odeme'] if ara_odeme_row else 0.0

            self.muhasebe_rapor_text.insert(tk.END, f"\nToplam Ara Ödemeler: {toplam_ara_odeme:.0f} ₺\n")


            # En çok satılan ürünleri bul
            self.muhasebe_rapor_text.insert(tk.END, "\n--- En Çok Satılan Ürünler ---\n")
            self.cursor.execute('''
                SELECT sd.urun_adi, SUM(sd.miktar) as toplam_miktar, SUM(sd.tutar) as toplam_tutar
                FROM siparis_detaylari sd
                JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
                WHERE sg.tarih BETWEEN ? AND ?
                GROUP BY sd.urun_adi
                ORDER BY toplam_miktar DESC
                LIMIT 10 -- İlk 10 ürün
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            en_cok_satilanlar = self.cursor.fetchall()

            if en_cok_satilanlar:
                for urun in en_cok_satilanlar:
                    self.muhasebe_rapor_text.insert(tk.END, f"{urun['urun_adi']}: {urun['toplam_miktar']} adet ({urun['toplam_tutar']:.0f} ₺)\n")
            else:
                self.muhasebe_rapor_text.insert(tk.END, "Bugün henüz ürün satışı yapılmadı.\n")


        except sqlite3.Error as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nVeritabanı hatası: {e}")
            print(f"Günlük satış raporu hatası: {e}")
        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nBeklenmedik hata: {e}")
            print(f"Günlük satış raporu beklenmedik hata: {e}")


    def _rapor_tarih_araligi_satis_ozeti(self):
        """Belirtilen tarih aralığı için satış özet raporunu oluşturur."""
        baslangic_dt = self._parse_date_entry(self.muhasebe_baslangic_tarihi_entry)
        bitis_dt = self._parse_date_entry(self.muhasebe_bitis_tarihi_entry)

        if baslangic_dt is None or bitis_dt is None:
            return # Hatalı tarih formatı uyarısı parse_date_entry içinde verildi

        # Bitiş tarihini gün sonuna ayarla
        bitis_dt = bitis_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        baslangic_tarihi_db = baslangic_dt.strftime(DB_DATE_FORMAT)
        bitis_tarihi_db = bitis_dt.strftime(DB_DATE_FORMAT)

        self.muhasebe_rapor_text.insert(tk.END, f"=== Satış Özeti Raporu ({baslangic_dt.strftime(RAPOR_TARIH_FORMATI)} - {bitis_dt.strftime(RAPOR_TARIH_FORMATI)}) ===\n\n")

        try:
            # Toplam satışları ödeme türüne göre al
            self.cursor.execute('''
                SELECT odeme_turu, COALESCE(SUM(toplam), 0) as toplam_satis
                FROM siparis_gecmisi
                WHERE tarih BETWEEN ? AND ?
                GROUP BY odeme_turu
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            satis_ozeti = self.cursor.fetchall()

            if satis_ozeti:
                for row in satis_ozeti:
                    self.muhasebe_rapor_text.insert(tk.END, f"{row['odeme_turu']}: {row['toplam_satis']:.0f} ₺\n")
            else:
                self.muhasebe_rapor_text.insert(tk.END, "Belirtilen tarih aralığında satış yapılmadı.\n")

            # Toplam ara ödemeleri al
            self.cursor.execute('''
                 SELECT COALESCE(SUM(miktar), 0) as toplam_ara_odeme
                 FROM ara_odemeler
                 WHERE tarih BETWEEN ? AND ?
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            ara_odeme_row = self.cursor.fetchone()
            toplam_ara_odeme = ara_odeme_row['toplam_ara_odeme'] if ara_odeme_row else 0.0

            self.muhasebe_rapor_text.insert(tk.END, f"\nToplam Ara Ödemeler: {toplam_ara_odeme:.0f} ₺\n")


            # En çok satılan ürünleri bul (bu tarih aralığı için)
            self.muhasebe_rapor_text.insert(tk.END, "\n--- En Çok Satılan Ürünler ---\n")
            self.cursor.execute('''
                SELECT sd.urun_adi, SUM(sd.miktar) as toplam_miktar, SUM(sd.tutar) as toplam_tutar
                FROM siparis_detaylari sd
                JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
                WHERE sg.tarih BETWEEN ? AND ?
                GROUP BY sd.urun_adi
                ORDER BY toplam_miktar DESC
                LIMIT 10 -- İlk 10 ürün
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            en_cok_satilanlar = self.cursor.fetchall()

            if en_cok_satilanlar:
                for urun in en_cok_satilanlar:
                    self.muhasebe_rapor_text.insert(tk.END, f"{urun['urun_adi']}: {urun['toplam_miktar']} adet ({urun['toplam_tutar']:.0f} ₺)\n")
            else:
                self.muhasebe_rapor_text.insert(tk.END, "Belirtilen tarih aralığında ürün satışı yapılmadı.\n")


        except sqlite3.Error as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nVeritabanı hatası: {e}")
            print(f"Tarih aralığı satış raporu hatası: {e}")
        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nBeklenmedik hata: {e}")
            print(f"Tarih aralığı satış raporu beklenmedik hata: {e}")


    def _rapor_masa_gecmisi_detayli(self):
        """Belirtilen tarih aralığı için masa geçmişi detaylı
        raporunu oluşturur (kapanış tarihine göre)."""
        baslangic_dt = self._parse_date_entry(self.muhasebe_baslangic_tarihi_entry)
        bitis_dt = self._parse_date_entry(self.muhasebe_bitis_tarihi_entry)

        if baslangic_dt is None or bitis_dt is None:
            return # Hatalı tarih formatı uyarısı parse_date_entry içinde verildi

        # Bitiş tarihini gün sonuna ayarla
        bitis_dt = bitis_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Başlangıç ve bitiş tarihlerinin mantıksal sırasını kontrol et
        if baslangic_dt > bitis_dt:
             messagebox.showwarning("Uyarı", "Başlangıç tarihi bitiş tarihinden sonra olamaz.", parent=self.muhasebe_frame)
             return

        baslangic_tarihi_db = baslangic_dt.strftime(DB_DATE_FORMAT)
        bitis_tarihi_db = bitis_dt.strftime(DB_DATE_FORMAT)

        self.muhasebe_rapor_text.insert(tk.END, f"=== Masa Geçmişi Detaylı Raporu ({baslangic_dt.strftime(RAPOR_TARIH_FORMATI)} - "
                                                f"{bitis_dt.strftime(RAPOR_TARIH_FORMATI)}) ===\n\n")

        try:
            # Masa geçmişini çek (kapanış tarihine göre filtrele)
            # Masa geçmişi tablosu kapanış tarihini içerir
            self.cursor.execute('''
                SELECT mg.kayit_id, mg.masa_no, mg.acilis, mg.kapanis, mg.toplam, mg.odeme_turu, m.ad, m.soyad, sg.id AS siparis_id
                FROM masa_gecmisi mg
                LEFT JOIN musteriler m ON mg.musteri_id = m.musteri_id
                LEFT JOIN siparis_gecmisi sg ON mg.kapanis = sg.tarih AND mg.masa_no = sg.masa_no AND ABS(mg.toplam - sg.toplam) < 0.01 -- Kapanış, masa ve yaklaşık toplam ile eşleştirme
                WHERE mg.kapanis BETWEEN ? AND ?
                ORDER BY mg.kapanis ASC
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            masa_gecmisi_kayitlari = self.cursor.fetchall()

            if masa_gecmisi_kayitlari:
                for kayit in masa_gecmisi_kayitlari:
                    masa_no = kayit['masa_no']
                    acilis_str = kayit['acilis']
                    kapanis_str = kayit['kapanis']
                    toplam = kayit['toplam'] if kayit['toplam'] is not None else 0.0 # Masa geçmişindeki toplam (Net Toplam olmalı)
                    odeme_turu = kayit['odeme_turu'] if kayit['odeme_turu'] is not None else "-"
                    musteri_ad_soyad = f"{kayit['ad']} {kayit['soyad']}".strip() if kayit['ad'] or kayit['soyad'] else "Misafir"
                    siparis_id_from_join = kayit['siparis_id'] # JOIN sonucundan gelen siparis_id

                    acilis_display = datetime.strptime(acilis_str, DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if acilis_str else '-'
                    kapanis_display = datetime.strptime(kapanis_str, DB_DATE_FORMAT).strftime(RAPOR_TARIH_FORMATI + " %H:%M") if kapanis_str else '-'

                    self.muhasebe_rapor_text.insert(tk.END, f"Masa No: {masa_no}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Müşteri: {musteri_ad_soyad}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Açılış: {acilis_display}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Kapanış: {kapanis_display}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Toplam (Net): {toplam:.0f} ₺\n") # Net Toplam gösterildi
                    self.muhasebe_rapor_text.insert(tk.END, f"Ödeme Türü: {odeme_turu}\n")

                    # Sipariş detaylarını çek (JOIN ile gelen siparis_id kullanılarak)
                    if siparis_id_from_join:
                        try:
                            self.cursor.execute('''
                                SELECT urun_adi, miktar, tutar
                                FROM siparis_detaylari
                                WHERE siparis_id = ?
                            ''', (siparis_id_from_join,)) # JOIN sonucundan gelen siparis_id kullanıldı
                            detaylar = self.cursor.fetchall()

                            if detaylar:
                                self.muhasebe_rapor_text.insert(tk.END, "  Detaylar:\n")
                                for detay in detaylar:
                                     self.muhasebe_rapor_text.insert(tk.END,
                                     f"    - {detay['urun_adi']:<20} x{detay['miktar']:<3} {detay['tutar']:.0f} ₺\n") # Formatlama düzeltildi
                            else:
                                self.muhasebe_rapor_text.insert(tk.END, "  Detay bulunamadı (siparis_detaylari boş).\n")

                        except sqlite3.Error as e:
                             self.muhasebe_rapor_text.insert(tk.END, f"  Detay çekme veritabanı hatası: {e}\n")
                             print(f"Masa geçmişi detay çekme hatası: {e}")
                        except Exception as e:
                             self.muhasebe_rapor_text.insert(tk.END, f"  Detay çekme beklenmedik hata: {e}\n")
                             print(f"Masa geçmişi detay çekme beklenmedik hata: {e}")

                    else:
                        self.muhasebe_rapor_text.insert(tk.END, "  İlgili sipariş geçmişi kaydı bulunamadı (Detaylar için).\n")


                    self.muhasebe_rapor_text.insert(tk.END, "-"*40 + "\n")

            else:
                self.muhasebe_rapor_text.insert(tk.END, "Belirtilen tarih aralığında masa geçmişi kaydı bulunamadı.\n")


        except sqlite3.Error as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nVeritabanı hatası: {e}")
            print(f"Masa geçmişi raporu hatası: {e}")
        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nBeklenmedik hata: {e}")
            print(f"Masa geçmişi raporu beklenmedik hata: {e}")


    def _rapor_musteri_bakiye(self):
        """Müşteri bakiye raporunu oluşturur."""
        self.muhasebe_rapor_text.insert(tk.END, "=== Müşteri Bakiye Raporu ===\n\n")

        try:
            # Bakiyesi sıfırdan farklı olan müşterileri çek (abs > 0.01 toleransı ile)
            self.cursor.execute('''
                SELECT musteri_id, ad, soyad, telefon, cumulative_balance
                FROM musteriler
                WHERE ABS(cumulative_balance) > 0.01 -- Bakiyesi sıfıra çok yakın olmayanlar
                ORDER BY cumulative_balance DESC, ad ASC
            ''')
            musteriler = self.cursor.fetchall()

            if musteriler:
                toplam_borc = 0.0
                toplam_alacak = 0.0

                for musteri in musteriler:
                    tam_ad = f"{musteri['ad']} {musteri['soyad']}".strip()
                    bakiye = musteri['cumulative_balance'] if musteri['cumulative_balance'] is not None else 0.0

                    self.muhasebe_rapor_text.insert(tk.END, f"Müşteri ID: {musteri['musteri_id']}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Adı Soyadı: {tam_ad}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Telefon: {musteri['telefon']}\n")
                    self.muhasebe_rapor_text.insert(tk.END, f"Bakiye: {bakiye:.0f} ₺\n")
                    self.muhasebe_rapor_text.insert(tk.END, "-"*30 + "\n")

                    if bakiye > 0:
                        toplam_borc += bakiye
                    else:
                        toplam_alacak += bakiye # Alacak negatif değer olarak toplanır


                self.muhasebe_rapor_text.insert(tk.END, "\n" + "="*30 + "\n")
                self.muhasebe_rapor_text.insert(tk.END, f"Toplam Müşteri Borcu: {toplam_borc:.0f} ₺\n")
                self.muhasebe_rapor_text.insert(tk.END, f"Toplam Müşteri Alacağı: {abs(toplam_alacak):.0f} ₺\n") # Alacak pozitif gösterildi
                self.muhasebe_rapor_text.insert(tk.END, "="*30 + "\n")


            else:
                self.muhasebe_rapor_text.insert(tk.END, "Bakiyesi olan müşteri bulunamadı.\n")

        except sqlite3.Error as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nVeritabanı hatası: {e}")
            print(f"Müşteri bakiye raporu hatası: {e}")
        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nBeklenmedik hata: {e}")
            print(f"Müşteri bakiye raporu beklenmedik hata: {e}")

    def _rapor_urun_satis(self):
        """Belirtilen tarih aralığı için ürün satış raporunu
        oluşturur (toplam miktar ve tutar)."""
        baslangic_dt = self._parse_date_entry(self.muhasebe_baslangic_tarihi_entry)
        bitis_dt = self._parse_date_entry(self.muhasebe_bitis_tarihi_entry)

        if baslangic_dt is None or bitis_dt is None:
            return # Hatalı tarih formatı uyarısı parse_date_entry içinde verildi

        # Bitiş tarihini gün sonuna ayarla
        bitis_dt = bitis_dt.replace(hour=23, minute=59, second=59, microsecond=999999)

        # Başlangıç ve bitiş tarihlerinin mantıksal sırasını kontrol et
        if baslangic_dt > bitis_dt:
             messagebox.showwarning("Uyarı", "Başlangıç tarihi bitiş tarihinden sonra olamaz.", parent=self.muhasebe_frame)
             return

        baslangic_tarihi_db = baslangic_dt.strftime(DB_DATE_FORMAT)
        bitis_tarihi_db = bitis_dt.strftime(DB_DATE_FORMAT)

        self.muhasebe_rapor_text.insert(tk.END, f"=== Ürün Satış Raporu ({baslangic_dt.strftime(RAPOR_TARIH_FORMATI)} - "
                                                f"{bitis_dt.strftime(RAPOR_TARIH_FORMATI)}) ===\n\n")

        try:
            # Ürün satışlarını toplam miktar ve tutara göre al (belirtilen tarih aralığında)
            self.cursor.execute('''
                SELECT sd.urun_adi, SUM(sd.miktar) as toplam_miktar, SUM(sd.tutar) as toplam_tutar
                FROM siparis_detaylari sd
                JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
                WHERE sg.tarih BETWEEN ? AND ?
                GROUP BY sd.urun_adi
                ORDER BY toplam_miktar DESC, sd.urun_adi ASC
            ''', (baslangic_tarihi_db, bitis_tarihi_db))
            urun_satis_verileri = self.cursor.fetchall()

            if urun_satis_verileri:
                toplam_satis_miktari = 0
                toplam_satis_tutari = 0.0

                for urun in urun_satis_verileri:
                    self.muhasebe_rapor_text.insert(tk.END, f"{urun['urun_adi']:<20}: {urun['toplam_miktar']:<5} adet ({urun['toplam_tutar']:.0f} ₺)\n") # Formatlama düzeltildi
                    toplam_satis_miktari += urun['toplam_miktar']
                    toplam_satis_tutari += urun['toplam_tutari'] # Hata: toplam_tutari yerine toplam_tutar olmalı

                # Hata düzeltildi: toplam_tutari yerine toplam_tutar kullanıldı
                toplam_satis_tutari = sum(urun['toplam_tutar'] for urun in urun_satis_verileri)


                self.muhasebe_rapor_text.insert(tk.END, "\n" + "="*40 + "\n")
                self.muhasebe_rapor_text.insert(tk.END, f"TOPLAM ÜRÜN SATIŞ MİKTARI: {toplam_satis_miktari} adet\n")
                self.muhasebe_rapor_text.insert(tk.END, f"TOPLAM ÜRÜN SATIŞ HASILATI: {toplam_satis_tutari:.0f} ₺\n")
                self.muhasebe_rapor_text.insert(tk.END, "="*40 + "\n")

            else:
                self.muhasebe_rapor_text.insert(tk.END, "Belirtilen tarih aralığında ürün satışı yapılmadı.\n")


        except sqlite3.Error as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nVeritabanı hatası: {e}")
            print(f"Ürün satış raporu hatası: {e}")
        except Exception as e:
            self.muhasebe_rapor_text.insert(tk.END, f"\nBeklenmedik hata: {e}")
            print(f"Ürün satış raporu beklenmedik hata: {e}")


# Uygulamayı başlat
if __name__ == "__main__":
    root = tk.Tk()
    app = CafeAdisyonProgrami(root)
    root.mainloop()
