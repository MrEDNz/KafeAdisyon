import sqlite3
import sys
from tkinter import messagebox
import constants # Göreceli import kaldırıldı, mutlak import kullanıldı

class DatabaseManager:
    def __init__(self, db_name=constants.DB_NAME):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self._connect_db()
        self._create_tables()
        self._add_default_data()

    def _connect_db(self):
        """SQLite veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            print("Veritabanı bağlantısı başarılı.")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Veritabanına bağlanılamadı: {e}")
            sys.exit()

    def _create_tables(self):
        """Gerekli veritabanı tablolarını oluşturur."""
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS masalar (
                    masa_no INTEGER PRIMARY KEY,
                    durum TEXT DEFAULT 'Boş', -- 'Boş', 'Dolu', 'Odeme Bekliyor'
                    aktif_siparis_id INTEGER,
                    guncel_toplam REAL DEFAULT 0.0,
                    iskonto REAL DEFAULT 0.0,
                    acilis_zamani TEXT
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS kategoriler (
                    kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adi TEXT UNIQUE NOT NULL
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS urunler (
                    urun_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adi TEXT UNIQUE NOT NULL,
                    fiyat REAL NOT NULL,
                    kategori_id INTEGER,
                    aktif_durumu INTEGER DEFAULT 1, -- 1:Aktif, 0:Pasif
                    hizli_satis_sirasi INTEGER DEFAULT 0,
                    FOREIGN KEY (kategori_id) REFERENCES kategoriler (kategori_id) ON DELETE SET NULL
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                    siparis_id INTEGER PRIMARY KEY AUTOINCREMENT, -- Adisyon ID
                    masa_no INTEGER NOT NULL,
                    acilis_zamani TEXT NOT NULL,
                    kapanis_zamani TEXT,
                    toplam_tutar REAL, -- Kapanış anındaki net tutar
                    iskonto REAL DEFAULT 0.0, -- Kapanış anındaki iskonto
                    odeme_yontemi TEXT, -- 'Nakit', 'Kart', 'Ara Odeme' vb.
                    durum TEXT DEFAULT 'Açık', -- 'Açık', 'Kapandı', 'İptal Edildi'
                    musteri_id INTEGER, -- İlişkilendirilen müşteri
                    FOREIGN KEY (masa_no) REFERENCES masalar (masa_no),
                    FOREIGN KEY (musteri_id) REFERENCES musteriler (musteri_id)
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS siparis_detaylari (
                    detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_id INTEGER NOT NULL,
                    urun_id INTEGER, -- Bağlantılı ürün
                    urun_adi TEXT NOT NULL, -- Ürünün sipariş anındaki adı (fiyat değişse de tutarlılık için)
                    miktar REAL NOT NULL,
                    birim_fiyat REAL NOT NULL, -- Ürünün sipariş anındaki fiyatı
                    tutar REAL NOT NULL, -- miktar * birim_fiyat
                    kategori_id INTEGER,
                    FOREIGN KEY (siparis_id) REFERENCES siparis_gecmisi (siparis_id),
                    FOREIGN KEY (urun_id) REFERENCES urunler (urun_id) ON DELETE SET NULL,
                    FOREIGN KEY (kategori_id) REFERENCES kategoriler (kategori_id) ON DELETE SET NULL
                )
            ''')

            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteriler (
                    musteri_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_soyad TEXT NOT NULL,
                    telefon TEXT UNIQUE,
                    bakiye REAL DEFAULT 0.0
                )
            ''')

            self.conn.commit()
            print("Veritabanı tabloları kontrol edildi/oluşturuldu.")

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Tablolar oluşturulurken hata oluştu: {e}")
            self.conn.rollback()

    def _add_default_data(self):
        """Veritabanı boşsa varsayılan masa ve ürünleri ekler."""
        try:
            self.cursor.execute("SELECT COUNT(*) FROM masalar")
            if self.cursor.fetchone()[0] == 0:
                for i in range(1, 11):
                    self.cursor.execute("INSERT INTO masalar (masa_no) VALUES (?)", (i,))
                print("Varsayılan masalar eklendi.")

            self.cursor.execute("SELECT COUNT(*) FROM kategoriler")
            if self.cursor.fetchone()[0] == 0:
                kategori_ekle_query = "INSERT OR IGNORE INTO kategoriler (adi) VALUES (?)"
                self.cursor.executemany(kategori_ekle_query, [(cat,) for cat in constants.DEFAULT_CATEGORIES])
                print("Varsayılan kategoriler eklendi.")

            self.cursor.execute("SELECT COUNT(*) FROM urunler")
            if self.cursor.fetchone()[0] == 0:
                self.cursor.execute("SELECT kategori_id, adi FROM kategoriler")
                kategori_map = {row['adi']: row['kategori_id'] for row in self.cursor.fetchall()}

                urunler_to_insert = []
                for ad, fiyat, kategori_ad, aktif, sira in constants.DEFAULT_PRODUCTS:
                    kategori_id = kategori_map.get(kategori_ad, None)
                    urunler_to_insert.append((ad, fiyat, kategori_id, aktif, sira))

                urun_ekle_query = "INSERT OR IGNORE INTO urunler (adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi) VALUES (?, ?, ?, ?, ?)"
                self.cursor.executemany(urun_ekle_query, urunler_to_insert)
                print("Varsayılan ürünler eklendi.")

            self.conn.commit()

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Varsayılan veri eklenirken hata oluştu: {e}")
            self.conn.rollback()

    def close_connection(self):
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            print("Veritabanı bağlantısı kapatıldı.")