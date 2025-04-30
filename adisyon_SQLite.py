import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime, timedelta
import sqlite3
import os
import shutil
from pathlib import Path
import json
import subprocess

class CafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("MrED Adisyon Programı (SQLite Sürümü)")
        self.root.geometry("1250x700")
        self.root.resizable(False, False)

        # Kategori renk tanımları
        self.kategori_renkleri = {
            "SICAK KAHVE": "#f9e79f",
            "SOĞUK KAHVE": "#edbb99",
            "SICAK İÇECEK": "#e74c3c",
            "SOĞUK İÇECEK": "#85c1e9",
            "MILK SHAKE": "#98fb98",
            "TATLI": "#fad7a0",
            "FRAPPE": "#d2b4de"
        }
        
        # Veritabanı bağlantısı
        self.db_file = 'cafe.db'
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()
        
        # Veritabanı tablolarını oluştur
        self._create_tables()
        self._load_default_data()
        
        # Arayüz
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Sekmeler
        self.masa_frame = tk.Frame(self.notebook)
        self.adisyon_frame = tk.Frame(self.notebook)
        self.musteri_frame = tk.Frame(self.notebook)
        self.urun_frame = tk.Frame(self.notebook)
        self.muhasebe_frame = tk.Frame(self.notebook)
        
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
        
        self.masa_butonlarini_guncelle()
        self.notebook.bind("<<NotebookTabChanged>>", self.sekme_degisti)
        
        # Değişkenler
        self.aktif_masa = None
        self.toplam_tutar = 0
        self.iskonto = 0
        
        # Günlük bakım rutini
        self.gunluk_bakim()

    def _create_tables(self):
        """Veritabanı tablolarını oluşturur"""
        # Önce temel tabloları oluştur
        tables = [
            '''CREATE TABLE IF NOT EXISTS urunler (
                urun_adi TEXT PRIMARY KEY,
                fiyat REAL,
                kategori TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS masalar (
                masa_no TEXT PRIMARY KEY,
                durum TEXT,
                toplam REAL DEFAULT 0,
                musteri_id TEXT,
                acilis TEXT,
                kapanis TEXT,
                son_adisyon_zamani TEXT,
                son_islem_zamani TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS musteriler (
                musteri_id TEXT PRIMARY KEY,
                ad TEXT,
                telefon TEXT,
                puan INTEGER DEFAULT 0,
                kayit_tarihi TEXT
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
                tarih TEXT,
                FOREIGN KEY (masa_no) REFERENCES masalar(masa_no)
            )''',
            '''CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                tarih TEXT,
                odeme_turu TEXT,
                toplam REAL,
                musteri_id TEXT
            )''',
            '''CREATE TABLE IF NOT EXISTS siparis_detaylari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                siparis_id INTEGER,
                urun_adi TEXT,
                fiyat REAL,
                miktar INTEGER,
                tutar REAL,
                FOREIGN KEY (siparis_id) REFERENCES siparis_gecmisi(id),
                FOREIGN KEY (urun_adi) REFERENCES urunler(urun_adi)
            )''',
            '''CREATE TABLE IF NOT EXISTS masa_gecmisi (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_no TEXT,
                acilis TEXT,
                kapanis TEXT,
                musteri_id TEXT,
                toplam REAL,
                odeme_turu TEXT,
                tarih TEXT
            )'''
        ]
        
        for table in tables:
            try:
                self.cursor.execute(table)
            except sqlite3.Error as e:
                print(f"Tablo oluşturulurken hata: {e}")
        
        # Ürünler tablosunda sira sütunu var mı kontrol et
        try:
            self.cursor.execute("PRAGMA table_info(urunler)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'sira' not in columns:
                # Eğer sira sütunu yoksa ekle
                self.cursor.execute("ALTER TABLE urunler ADD COLUMN sira INTEGER DEFAULT 9999")
                print("sira sütunu eklendi")
                
                # Mevcut ürünlere sıra numarası ata (1'den başlayarak)
                self.cursor.execute("""
                    UPDATE urunler 
                    SET sira = (SELECT rowid FROM urunler u2 WHERE urunler.urun_adi = u2.urun_adi)
                """)
                print("Mevcut ürünlere sıra numaraları atandı")
        except sqlite3.Error as e:
            print(f"sira sütunu kontrolü/eklemesi sırasında hata: {e}")
        
        self.conn.commit()

    def _load_default_data(self):
        """Tablolar boşsa varsayılan verileri yükler"""
        # Ürünler kontrolü
        self.cursor.execute("SELECT COUNT(*) FROM urunler")
        if self.cursor.fetchone()[0] == 0:
            default_products = [
                ("MOCHA", 80, "SICAK İÇECEK", 1),
                ("DOPPIO", 80, "SICAK İÇECEK", 2),
                ("ESPR. MOCCHIATO", 80, "SICAK İÇECEK", 3),
                ("AMERICANO", 90, "SICAK İÇECEK", 4),
                ("CAPPUCINO", 80, "SICAK İÇECEK", 5),
                ("LATTE", 90, "SICAK İÇECEK", 6),
                ("FLAT WHITE", 80, "SICAK İÇECEK", 7),
                ("CORTADO", 90, "SICAK İÇECEK", 8),
                ("ESPRESSO", 120, "SICAK İÇECEK", 9),
                ("CAR. MOCCHIATO", 120, "SICAK İÇECEK", 10),
                ("WHITE MOCHA", 120, "SICAK İÇECEK", 11),
                ("TUF. NUT LATTE", 130, "SICAK İÇECEK", 12),
                ("FILTRE KAHVE", 80, "SICAK İÇECEK", 13),
                ("F. KAHVE SÜTLÜ", 90, "SICAK İÇECEK", 14),
                ("SICAK ÇIKOLATA", 120, "SICAK İÇECEK", 15),
                ("ICE LATTE", 120, "SOĞUK KAHVE", 16),
                ("ICE LATTE COSTOM", 120,"SOĞUK KAHVE", 17),
                ("ICE MOCHA", 120, "SOĞUK KAHVE", 18),
                ("ICE AMERICANO", 110, "SOĞUK KAHVE", 19),
                ( "ICE WHITE MOCCA", 120,"SOĞUK KAHVE", 20),
                ("ICE FILTRE KAHVE", 110,"SOĞUK KAHVE", 21),
                ("ICE KAR. MOCHA", 120, "SOĞUK KAHVE", 22),
                ("ICE TUF. NUT LATTE", 130, "SOĞUK KAHVE", 23),
                ("COOL LIME", 130, "MILK SHAKE", 24),
                ("LIMONATA", 70, "MILK SHAKE", 25),
                ("KARADUT SUYU", 90, "MILK SHAKE", 26),
                ("ÇILEKLI MILKSHAKE", 90, "MILK SHAKE", 27),
                ("KIRMIZI ORMAN", 120, "MILK SHAKE", 28),
                ("BÖĞÜRTLEN", 120, "MILK SHAKE", 29),
                ("KARA ORMAN", 100, "MILK SHAKE", 30),
                ("MENENGIÇ KAHVESI", 80, "SICAK İÇECEK", 31),
                ("DIBEK KAHVESI", 80, "SICAK İÇECEK", 32),
                ("DETOX KAHVE", 90, "SICAK İÇECEK", 33),
                ("ADAÇAYI", 60, "SICAK İÇECEK", 34),
                ("ÇAY", 30, "SICAK İÇECEK", 35),
                ("IHLAMUR", 60, "SICAK İÇECEK", 36),
                ("YEŞILÇAY", 60, "SICAK İÇECEK", 37),
                ("HIBISKUS", 60, "SICAK İÇECEK", 38),
                ("COCA KOLA", 60, "SOĞUK İÇECEK", 39),
                ("FANTA", 60, "SOĞUK İÇECEK", 40),
                ("SPRITE", 60, "SOĞUK İÇECEK", 41),
                ("İCE TEA", 60, "SOĞUK İÇECEK", 42),
                ("SODA SADE", 40, "SOĞUK İÇECEK", 43),
                ("MEYVELI SODA", 40, "SOĞUK İÇECEK", 44),
                ("SU", 20, "SOĞUK İÇECEK", 45),
                ("CHURCHILL", 40, "SOĞUK İÇECEK", 46),
                ("OREOLU FRAPPE", 80, "FRAPPE", 47),
                ("ÇIKOLATALI FRAPPE", 90, "FRAPPE", 48),
                ("VANILYALI FRAPPE", 90, "FRAPPE", 49),
                ("KARAMELLI FRAPPE", 100, "FRAPPE", 50),
                ("ÇILEKLI SMOOTHIE", 95, "FRAPPE", 51),
                ("MUZLU SMOOTHIE", 100, "FRAPPE", 52),
                ("SAN SEBASTIAN", 80, "TATLI", 53),
                ("MANGOLIA", 60, "TATLI", 54),
                ("TRAMISU", 60, "TATLI", 55),
            ]
            self.cursor.executemany(
                ### DEĞİŞTİRİLEN KISIM ###
                "INSERT INTO urunler (urun_adi, fiyat, kategori, sira) VALUES (?, ?, ?, ?)",
                default_products
                ### DEĞİŞTİRİLEN KISIM SONU ###
            )
        
        # Masalar kontrolü
        self.cursor.execute("SELECT COUNT(*) FROM masalar")
        if self.cursor.fetchone()[0] == 0:
            for i in range(1, 6):
                self.cursor.execute(
                    "INSERT INTO masalar (masa_no, durum) VALUES (?, ?)",
                    (str(i), "boş")
                )
        
        self.conn.commit()

    ### YENİ EKLENEN KISIM ###
    def urun_sira_degistir(self):
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
            return
        
        # Seçili ürünün tüm bilgilerini al
        item = self.urun_listesi.item(selected[0])
        urun_adi = item['values'][1]  # Artık 1. indeks ürün adı
        mevcut_sira = item['values'][0]  # 0. indeks sıra numarası
        
        yeni_sira = simpledialog.askinteger(
            "Sıra Değiştir", 
            f"{urun_adi} için yeni sıra numarası:",
            minvalue=1,
            initialvalue=mevcut_sira,
            parent=self.root
        )
        
        if yeni_sira and yeni_sira != mevcut_sira:
            self.cursor.execute('''
                UPDATE urunler SET sira = ? WHERE urun_adi = ?
            ''', (yeni_sira, urun_adi))
            self.conn.commit()
            
            self.urun_listesini_guncelle()
            self.hizli_satis_butonlari_olustur()
            messagebox.showinfo("Başarılı", "Ürün sırası güncellendi!")
    ### YENİ EKLENEN KISIM SONU ###

    def gunluk_bakim(self):
        """Günlük veritabanı bakım işlemleri"""
        try:
            # Veritabanı boyut kontrolü ve optimizasyon
            self.cursor.execute("VACUUM")
            
            # 30 günden eski tamamlanmış masaları arşivle
            tarih_esik = (datetime.now() - timedelta(days=30)).strftime("%d.%m.%Y %H:%M")
            
            # Eski masa hareketlerini arşivle
            self.cursor.execute('''
                INSERT INTO masa_gecmisi
                SELECT NULL, masa_no, acilis, kapanis, musteri_id, toplam, 'Arşiv', ?
                FROM masalar 
                WHERE durum = 'boş' AND acilis < ?
            ''', (datetime.now().strftime("%d.%m.%Y %H:%M"), tarih_esik))
            
            # Eski masaları sil
            self.cursor.execute('''
                DELETE FROM masalar 
                WHERE durum = 'boş' AND acilis < ?
            ''', (tarih_esik,))
            
            # Eski sipariş detaylarını sil
            self.cursor.execute('''
                DELETE FROM masa_siparisleri 
                WHERE masa_no IN (
                    SELECT masa_no FROM masalar WHERE durum = 'boş' AND acilis < ?
                )
            ''', (tarih_esik,))
            
            self.conn.commit()
            
            # Yedek al
            self.yedek_al()
            
        except Exception as e:
            print(f"Bakım sırasında hata: {str(e)}")

    def veritabani_temizle(self):
        try:
            # Boş tarihli kayıtları düzelt
            self.cursor.execute('''
                UPDATE masa_gecmisi 
                SET 
                    acilis = COALESCE(acilis, '01.01.2000 00:00'),
                    kapanis = COALESCE(kapanis, '01.01.2000 00:00'),
                    toplam = COALESCE(toplam, 0),
                    odeme_turu = COALESCE(odeme_turu, 'Bilinmiyor')
                WHERE 
                    acilis IS NULL OR 
                    kapanis IS NULL OR 
                    toplam IS NULL OR 
                    odeme_turu IS NULL
            ''')
            self.conn.commit()
            messagebox.showinfo("Başarılı", "Veritabanı temizlendi ve boş kayıtlar düzeltildi")
        except Exception as e:
            messagebox.showerror("Hata", f"Veritabanı temizlenirken hata oluştu:\n{str(e)}")

    def yedek_al(self):
        """Veritabanı yedeği alır"""
        try:
            tarih = datetime.now().strftime("%Y%m%d_%H%M")
            yedek_dizin = "yedekler"
            os.makedirs(yedek_dizin, exist_ok=True)
            
            shutil.copy2(self.db_file, f'{yedek_dizin}/cafe_{tarih}.db')
                
        except Exception as e:
            print(f"Yedek alınırken hata oluştu: {str(e)}")

    # MASA YÖNETİMİ FONKSİYONLARI
    def masa_arayuz_olustur(self):
        btn_frame = tk.Frame(self.masa_frame)
        btn_frame.pack(pady=10)
    
        tk.Button(btn_frame, text="Masa Ekle", width=14, height=2, bg="#fac35b", font=("Arial", 9, "bold"), command=self.masa_ekle).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Masa Sil", width=14, height=2, bg="#f95b42", font=("Arial", 9, "bold"), command=self.masa_sil).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Müşteri Ata", width=14, height=2, bg="#07a2ea", font=("Arial", 9, "bold"), command=self.masa_musteri_ata).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="İndirim Uygula", width=14, height=2, bg="#8e44ad", fg="white", font=("Arial", 9, "bold"), command=self.indirim_uygula).pack(side=tk.LEFT, padx=5)
    
        self.masalar_frame = tk.Frame(self.masa_frame)
        self.masalar_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        self.masa_renk_guncelleme_timer()

    def masa_butonlarini_guncelle(self):
        # Önceki butonları temizle
        for widget in self.masalar_frame.winfo_children():
            widget.destroy()

        # Sabit ayarlar
        COLS = 6
        BTN_WIDTH = 19
        BTN_HEIGHT = 5
        PAD = 5
        
        # Masaları veritabanından çek
        self.cursor.execute('''
            SELECT m.masa_no, m.durum, m.musteri_id, m.toplam, m.son_adisyon_zamani, 
                   COALESCE(SUM(a.miktar), 0) as ara_odeme,
                   mu.ad as musteri_adi,
                   m.son_islem_zamani
            FROM masalar m
            LEFT JOIN ara_odemeler a ON m.masa_no = a.masa_no
            LEFT JOIN musteriler mu ON m.musteri_id = mu.musteri_id
            GROUP BY m.masa_no
            ORDER BY CAST(m.masa_no AS INTEGER)
        ''')
        
        masalar = self.cursor.fetchall()
        
        for index, masa in enumerate(masalar):
            masa_no, durum, musteri_id, toplam, son_adisyon, ara_odeme, musteri_adi, son_islem = masa
            
            # Durum belirleme
            durum_text = "DOLU" if durum == "dolu" else "BOŞ"
            
            # Müşteri adı ve font ayarları
            musteri_bilgi = ""
            font_ayar = ("Arial", 11, "bold")
            wrap_length = BTN_WIDTH*7

            if musteri_adi:
                ad = musteri_adi.split()[0] if ' ' in musteri_adi else musteri_adi[:8]
                musteri_bilgi = f" - {ad}"
                font_ayar = ("Arial", 9)
                wrap_length = BTN_WIDTH*9

            # Temel buton metni
            btn_text = f"Masa {masa_no}{musteri_bilgi}\nDurum: {durum_text}"
            
            # Dolu masalar için ek bilgiler
            if durum == "dolu":
                kalan = toplam - ara_odeme
                
                btn_text += f"\nToplam: {toplam} TL"
                
                if son_adisyon:
                    try:
                        saat = datetime.strptime(son_adisyon, "%d.%m.%Y %H:%M").strftime("%H:%M")
                        btn_text += f"\nSon İşlem: {saat}"
                    except:
                        pass
                
                if ara_odeme > 0:
                    btn_text += f"\nÖ/K: {ara_odeme}/{kalan} TL"

            # RENK AYARLARI
            bg_color = "#fefcbf" if durum == "boş" else "#faa93e"
            
            # MÜŞTERİ ATANMIŞ MASA KONTROLÜ (30 dakika kuralından muaf)
            if musteri_id:
                bg_color = "#ADD8E6"
            elif durum == "dolu" and son_islem:
                try:
                    son_islem_tarih = datetime.strptime(son_islem, "%d.%m.%Y %H:%M")
                    if (datetime.now() - son_islem_tarih).total_seconds() > 1800:
                        bg_color = "#fa2802"
                except:
                    pass

            # Buton oluşturma
            btn = tk.Button(
                self.masalar_frame,
                text=btn_text,
                command=lambda mn=masa_no: self.masa_sec(mn),
                bg=bg_color,
                width=BTN_WIDTH,
                height=BTN_HEIGHT,
                font=font_ayar,
                relief="raised",
                wraplength=wrap_length,
                justify="center"
            )
            
            # Grid'e yerleştirme
            row, col = divmod(index, COLS)
            btn.grid(row=row, column=col, padx=PAD, pady=PAD, sticky="nsew")

        # Grid ayarları
        for c in range(COLS):
            self.masalar_frame.grid_columnconfigure(c, weight=1, uniform="cols", minsize=150)
        
        total_rows = (len(masalar) + COLS - 1) // COLS
        for r in range(total_rows):
            self.masalar_frame.grid_rowconfigure(r, weight=1, minsize=90)

    def masa_sec(self, masa_no):
        try:
            masa_no = str(masa_no)
        
            # Eğer zaten aktif masa aynı ise
            if self.aktif_masa == masa_no:
                self.sepeti_yukle()
                self.notebook.select(1)  # Adisyon sekmesine geç
                return
            
            # Önceki aktif masayı kapat
            if self.aktif_masa:
                self.cursor.execute('''
                    UPDATE masalar 
                    SET kapanis = ?
                    WHERE masa_no = ?
                ''', (self.tarih_saat_al(), masa_no))
                self.conn.commit()
            
            # Yeni masayı aktif yap
            self.aktif_masa = masa_no
            
            # Masanın durumunu kontrol et
            self.cursor.execute('''
                SELECT durum FROM masalar WHERE masa_no = ?
            ''', (masa_no,))
            durum = self.cursor.fetchone()[0]
        
            # Masayı boşsa açılış kaydı yap
            if durum == "boş":
                self.cursor.execute('''
                    UPDATE masalar 
                    SET acilis = ?, durum = 'dolu', son_islem_zamani = ?
                    WHERE masa_no = ?
                ''', (self.tarih_saat_al(), self.tarih_saat_al(), masa_no))
                self.conn.commit()
        
            # UI güncellemeleri
            if hasattr(self, 'aktif_masa_label'):
                self.aktif_masa_label.config(text=f"Aktif Masa: {masa_no}")
        
            if hasattr(self, 'musteri_label'):
                self.cursor.execute('''
                    SELECT m.ad FROM masalar ma
                    LEFT JOIN musteriler m ON ma.musteri_id = m.musteri_id
                    WHERE ma.masa_no = ?
                ''', (masa_no,))
                musteri = self.cursor.fetchone()
                if musteri and musteri[0]:
                    self.musteri_label.config(text=f"Müşteri: {musteri[0]}")
                else:
                    self.musteri_label.config(text="Müşteri: -")
        
            # Sepeti yükle, veritabanını kaydet ve Adisyon sekmesine geç
            self.sepeti_yukle()
            self.conn.commit()
            self.masa_butonlarini_guncelle()
            self.notebook.select(1)  # Adisyon sekmesine geç
        
        except Exception as e:
            messagebox.showerror("Hata", f"Masa seçilirken hata oluştu: {str(e)}")
            self.aktif_masa = None
            if hasattr(self, 'aktif_masa_label'):
                self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")

    def masa_renk_guncelleme_timer(self):
        try:
            if hasattr(self, 'masalar_frame'):
                self.masa_butonlarini_guncelle()
        except Exception as e:
            print(f"Timer hatası: {str(e)}")
        finally:
            self.root.after(600000, self.masa_renk_guncelleme_timer)

    def masa_ekle(self):
        try:
            # Mevcut masa numaralarını al
            self.cursor.execute("SELECT masa_no FROM masalar ORDER BY CAST(masa_no AS INTEGER)")
            masa_nolar = [int(row[0]) for row in self.cursor.fetchall()]
            
            yeni_masa_no = str(max(masa_nolar) + 1) if masa_nolar else "1"
            
            self.cursor.execute(
                "INSERT INTO masalar (masa_no, durum) VALUES (?, ?)",
                (yeni_masa_no, "boş")
            )
            self.conn.commit()
            self.masa_butonlarini_guncelle()
            messagebox.showinfo("Başarılı", f"Masa {yeni_masa_no} eklendi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Masa eklenirken hata oluştu: {str(e)}")
    
    def masa_sil(self):
        try:
            # Mevcut masaları listele
            self.cursor.execute("SELECT masa_no FROM masalar ORDER BY CAST(masa_no AS INTEGER)")
            masalar = [row[0] for row in self.cursor.fetchall()]
            
            if not masalar:
                messagebox.showwarning("Uyarı", "Silinecek masa yok!")
                return
            
            masa_no = simpledialog.askstring("Masa Sil", "Silinecek masa numarasını girin:", 
                                           parent=self.root)
            
            if masa_no and masa_no in masalar:
                # Masa dolu mu kontrol et
                self.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
                durum = self.cursor.fetchone()[0]
                
                if durum == "dolu":
                    messagebox.showwarning("Uyarı", "Bu masada sipariş var, önce ödeme yapılmalı!")
                    return
                
                # Masayı sil
                self.cursor.execute("DELETE FROM masalar WHERE masa_no = ?", (masa_no,))
                
                if self.aktif_masa == masa_no:
                    self.aktif_masa = None
                    if hasattr(self, 'aktif_masa_label'):
                        self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
                    if hasattr(self, 'musteri_label'):
                        self.musteri_label.config(text="Müşteri: -")
                    self.sepeti_temizle()
                
                self.conn.commit()
                self.masa_butonlarini_guncelle()
                messagebox.showinfo("Başarılı", f"Masa {masa_no} silindi.")
            else:
                messagebox.showwarning("Uyarı", "Geçersiz masa numarası!")
        except Exception as e:
            messagebox.showerror("Hata", f"Masa silinirken hata oluştu: {str(e)}")

    def masa_musteri_ata(self):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        musteri_id = simpledialog.askstring("Müşteri Ata", "Müşteri ID veya Telefon:")
        if musteri_id:
            # Müşteriyi ara
            self.cursor.execute('''
                SELECT musteri_id, ad FROM musteriler 
                WHERE musteri_id = ? OR telefon = ?
            ''', (musteri_id, musteri_id))
            musteri = self.cursor.fetchone()
            
            if musteri:
                musteri_id, musteri_adi = musteri
                self.cursor.execute('''
                    UPDATE masalar SET musteri_id = ? WHERE masa_no = ?
                ''', (musteri_id, self.aktif_masa))
                self.conn.commit()
                
                if hasattr(self, 'musteri_label'):
                    self.musteri_label.config(text=f"Müşteri: {musteri_adi}")
                
                self.masa_butonlarini_guncelle()
                messagebox.showinfo("Başarılı", f"Masa {self.aktif_masa} için müşteri atandı!")
            else:
                messagebox.showwarning("Uyarı", "Müşteri bulunamadı!")

    def indirim_uygula(self):
        # Masaları veritabanından kontrol et
        self.cursor.execute("SELECT COUNT(*) FROM masalar")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showwarning("Uyarı", "Masa bulunamadı!")
            return
        
        # İndirim penceresi oluştur
        indirim_pencere = tk.Toplevel(self.root)
        indirim_pencere.title("İndirim Uygula")
        indirim_pencere.resizable(False, False)
        
        # Masa seçimi
        tk.Label(indirim_pencere, text="Masa Seçin:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.cursor.execute("SELECT masa_no FROM masalar ORDER BY CAST(masa_no AS INTEGER)")
        masa_listesi = [row[0] for row in self.cursor.fetchall()]
        
        masa_combobox = ttk.Combobox(indirim_pencere, values=masa_listesi, state="readonly", width=15)
        masa_combobox.grid(row=0, column=1, padx=5, pady=5)
        
        # İndirim miktarı
        tk.Label(indirim_pencere, text="İndirim Miktarı (TL):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        indirim_entry = tk.Entry(indirim_pencere, width=18)
        indirim_entry.grid(row=1, column=1, padx=5, pady=5)
        
        def indirimi_uygula():
            masa_no = masa_combobox.get()
            if not masa_no:
                messagebox.showwarning("Uyarı", "Lütfen bir masa seçin!")
                return
            
            try:
                indirim = float(indirim_entry.get())
                if indirim <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz indirim miktarı!")
                return
            
            # Masa bilgilerini al
            self.cursor.execute('''
                SELECT durum, toplam FROM masalar WHERE masa_no = ?
            ''', (masa_no,))
            durum, toplam = self.cursor.fetchone()
            
            if durum != "dolu":
                messagebox.showwarning("Uyarı", "Bu masada sipariş bulunmamaktadır!")
                return
            
            if indirim > toplam:
                messagebox.showwarning("Uyarı", "İndirim miktarı toplam tutardan fazla olamaz!")
                return
            
            # İndirimi uygula
            yeni_tutar = toplam - indirim
            self.cursor.execute('''
                UPDATE masalar 
                SET toplam = ?, son_adisyon_zamani = ?
                WHERE masa_no = ?
            ''', (yeni_tutar, self.tarih_saat_al(), masa_no))
            self.conn.commit()
            
            self.masa_butonlarini_guncelle()
            messagebox.showinfo("Başarılı", f"Masa {masa_no} için {indirim} TL indirim uygulandı.")
            indirim_pencere.destroy()
        
        # Uygula butonu
        tk.Button(
            indirim_pencere,
            text="İndirimi Uygula",
            command=indirimi_uygula,
            bg="#f6f93c",
            fg="black"
        ).grid(row=2, column=0, columnspan=2, pady=10)

    # ADİSYON İŞLEMLERİ
    def adisyon_arayuz_olustur(self):
        bilgi_frame = tk.Frame(self.adisyon_frame)
        bilgi_frame.pack(pady=5, fill=tk.X)
    
        self.aktif_masa_label = tk.Label(bilgi_frame, text="Aktif Masa: Seçili değil", font=("Arial", 11, "bold"))
        self.aktif_masa_label.pack(side=tk.LEFT, padx=5)
    
        self.musteri_label = tk.Label(bilgi_frame, text="Müşteri: -", font=("Arial", 11))
        self.musteri_label.pack(side=tk.LEFT, padx=5)
    
        tk.Label(bilgi_frame, text=self.tarih_saat_al(), font=("Arial", 11)).pack(side=tk.RIGHT)

        arama_frame = tk.Frame(self.adisyon_frame)
        arama_frame.pack(pady=5, fill=tk.X)
    
        tk.Label(arama_frame, font=("Arial", 11), text="Ürün Ara:").pack(side=tk.LEFT)
        self.urun_arama_entry = tk.Entry(arama_frame, width=25)
        self.urun_arama_entry.pack(side=tk.LEFT, padx=5)
        self.urun_arama_entry.bind("<Return>", self.urun_ara)

        self.hizli_satis_container = tk.Frame(self.adisyon_frame, height=350)
        self.hizli_satis_container.pack(pady=5, fill=tk.X)
        self.hizli_satis_container.pack_propagate(False)
    
        self.hizli_satis_frame = tk.Frame(self.hizli_satis_container)
        self.hizli_satis_frame.pack(fill=tk.BOTH, expand=True)
    
        self.sepet_tablo = ttk.Treeview(self.adisyon_frame, columns=("Urun", "Fiyat", "Miktar", "Tutar"), show="headings", height=4)
        self.sepet_tablo.heading("Urun", text="Ürün")
        self.sepet_tablo.heading("Fiyat", text="Fiyat")
        self.sepet_tablo.heading("Miktar", text="Miktar")
        self.sepet_tablo.heading("Tutar", text="Tutar")
        self.sepet_tablo.column("Urun", width=200)
        self.sepet_tablo.column("Fiyat", width=80, anchor='e')
        self.sepet_tablo.column("Miktar", width=80, anchor='e')
        self.sepet_tablo.column("Tutar", width=100, anchor='e')
        self.sepet_tablo.pack(pady=2, fill=tk.BOTH, expand=True)
    
        kontrol_frame = tk.Frame(self.adisyon_frame)
        kontrol_frame.pack(pady=2, fill=tk.X)
    
        tk.Label(kontrol_frame, font=("Arial", 9), text="Adetli Ürün Ekle:").pack(side=tk.LEFT)
        self.miktar_spinbox = tk.Spinbox(kontrol_frame, from_=1, to=10, width=4)
        self.miktar_spinbox.pack(side=tk.LEFT, padx=2)
    
        tk.Button(kontrol_frame, text="Ekle", bg="#c8fb8a", font=("Arial", 9), command=self.sepete_ekle, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(kontrol_frame, text="Çıkar", bg="#c8fb8a", font=("Arial", 9), command=self.sepetten_cikar, width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(kontrol_frame, text="Temizle", bg="#c8fb8a", font=("Arial", 9), command=self.sepeti_temizle, width=8).pack(side=tk.LEFT, padx=2)

        odeme_frame = tk.Frame(self.adisyon_frame)
        odeme_frame.pack(pady=2, fill=tk.X)
    
        tk.Button(odeme_frame, text="Masa Hesap", bg="#fab918", font=("Arial", 9, "bold"), command=self.nakit_odeme, width=12).pack(side=tk.RIGHT, padx=2)
        tk.Button(odeme_frame, text="Masa Kapat", bg="#fa5939", font=("Arial", 9, "bold"), command=lambda: self.odeme_yap("Hesap"), width=12).pack(side=tk.RIGHT, padx=2)
        tk.Button(odeme_frame, text="Ara Ödeme", bg="#39b1fa", font=("Arial", 9, "bold"), command=self.ara_odeme, width=12).pack(side=tk.RIGHT, padx=2)

        toplam_frame = tk.Frame(self.adisyon_frame)
        toplam_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
    
        self.toplam_label = tk.Label(toplam_frame, text="Toplam: 0 TL", font=("Arial", 9, "bold"))
        self.toplam_label.pack(side=tk.RIGHT, padx=10)
    
        self.iskonto_label = tk.Label(toplam_frame, text="İskonto: 0 TL", font=("Arial", 9, "bold"))
        self.iskonto_label.pack(side=tk.RIGHT, padx=10)
    
        self.net_tutar_label = tk.Label(toplam_frame, text="Net Tutar: 0 TL", font=("Arial", 9, "bold"))
        self.net_tutar_label.pack(side=tk.RIGHT, padx=10)
    
        self.hizli_satis_butonlari_olustur()

    def hizli_satis_butonlari_olustur(self):
        for widget in self.hizli_satis_frame.winfo_children():
            widget.destroy()

        ### DEĞİŞTİRİLEN KISIM ###
        self.cursor.execute("""
            SELECT urun_adi, fiyat, kategori 
            FROM urunler 
            ORDER BY sira, urun_adi
        """)
        ### DEĞİŞTİRİLEN KISIM SONU ###
        urunler = self.cursor.fetchall()
        
        for i, (urun_adi, fiyat, kategori) in enumerate(urunler):
            bg_color = self.kategori_renkleri.get(kategori, "#f0f0f0")
        
            btn = tk.Button(
                self.hizli_satis_frame,
                text=f"{urun_adi}\n{fiyat} TL",
                command=lambda u=urun_adi: self.urun_ekle(u),
                bg=bg_color,
                fg="#f4f6f7" if bg_color in ["#e74c3c", "#85c1e9"] else "black",
                width=16,
                height=2,
                font=("Arial", 9, "bold")
            )
            btn.grid(row=i//9, column=i%9, padx=8, pady=4)
    
    def sepeti_yukle(self):
        self.sepet_tablo.delete(*self.sepet_tablo.get_children())
        
        if self.aktif_masa:
            # Masanın siparişlerini getir
            self.cursor.execute('''
                SELECT urun_adi, fiyat, miktar, tutar 
                FROM masa_siparisleri 
                WHERE masa_no = ?
            ''', (self.aktif_masa,))
            
            for siparis in self.cursor.fetchall():
                self.sepet_tablo.insert("", "end", values=siparis)
            
            # Toplam tutarı güncelle
            self.cursor.execute('''
                SELECT COALESCE(SUM(tutar), 0) FROM masa_siparisleri 
                WHERE masa_no = ?
            ''', (self.aktif_masa,))
            self.toplam_tutar = self.cursor.fetchone()[0]
            self.toplam_guncelle()
    
    def urun_ara(self, event=None):
        arama_metni = self.urun_arama_entry.get().strip().upper()
        if not arama_metni:
            return
        
        self.cursor.execute('''
            SELECT urun_adi FROM urunler 
            WHERE urun_adi LIKE ? 
            LIMIT 1
        ''', (f'%{arama_metni}%',))
        
        bulunan_urun = self.cursor.fetchone()
        
        if bulunan_urun:
            self.urun_ekle(bulunan_urun[0])
        else:
            messagebox.showinfo("Bilgi", "Ürün bulunamadı!")
    
    def urun_ekle(self, urun_adi):
        self.urun_arama_entry.delete(0, tk.END)
        self.urun_arama_entry.insert(0, urun_adi)
        self.sepete_ekle()
    
    def sepete_ekle(self):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        urun_adi = self.urun_arama_entry.get().strip().upper()
        try:
            miktar = int(self.miktar_spinbox.get())
            if miktar <= 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçersiz miktar! Pozitif tam sayı girin.")
            return
        
        # Ürün var mı kontrol et
        self.cursor.execute('''
            SELECT fiyat FROM urunler WHERE urun_adi = ?
        ''', (urun_adi,))
        urun = self.cursor.fetchone()
        
        if urun:
            fiyat = urun[0]
            tutar = fiyat * miktar
            
            # Aynı üründen var mı kontrol et
            self.cursor.execute('''
                SELECT id, miktar FROM masa_siparisleri 
                WHERE masa_no = ? AND urun_adi = ?
            ''', (self.aktif_masa, urun_adi))
            eski_siparis = self.cursor.fetchone()
            
            if eski_siparis:
                # Miktarı güncelle
                yeni_miktar = eski_siparis[1] + miktar
                yeni_tutar = fiyat * yeni_miktar
                
                self.cursor.execute('''
                    UPDATE masa_siparisleri 
                    SET miktar = ?, tutar = ? 
                    WHERE id = ?
                ''', (yeni_miktar, yeni_tutar, eski_siparis[0]))
            else:
                # Yeni sipariş ekle
                self.cursor.execute('''
                    INSERT INTO masa_siparisleri 
                    (masa_no, urun_adi, fiyat, miktar, tutar) 
                    VALUES (?, ?, ?, ?, ?)
                ''', (self.aktif_masa, urun_adi, fiyat, miktar, tutar))
            
            # Masanın toplamını güncelle
            self.cursor.execute('''
                UPDATE masalar 
                SET toplam = (
                    SELECT COALESCE(SUM(tutar), 0) 
                    FROM masa_siparisleri 
                    WHERE masa_no = ?
                ),
                son_adisyon_zamani = ?,
                son_islem_zamani = ?,
                durum = 'dolu'
                WHERE masa_no = ?
            ''', (self.aktif_masa, self.tarih_saat_al(), self.tarih_saat_al(), self.aktif_masa))
            
            self.conn.commit()
            self.sepeti_yukle()
        else:
            messagebox.showwarning("Uyarí", "Geçersiz ürün adı!")
    
    def sepetten_cikar(self):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        selected_item = self.sepet_tablo.selection()
        if selected_item:
            urun_adi = self.sepet_tablo.item(selected_item, "values")[0]
            miktar = int(self.sepet_tablo.item(selected_item, "values")[2])
            
            cikar_miktar = int(self.miktar_spinbox.get())
            yeni_miktar = miktar - cikar_miktar
            
            if yeni_miktar <= 0:
                # Siparişi tamamen sil
                self.cursor.execute('''
                    DELETE FROM masa_siparisleri 
                    WHERE masa_no = ? AND urun_adi = ?
                ''', (self.aktif_masa, urun_adi))
            else:
                # Miktarı güncelle
                self.cursor.execute('''
                    SELECT fiyat FROM urunler WHERE urun_adi = ?
                ''', (urun_adi,))
                fiyat = self.cursor.fetchone()[0]
                yeni_tutar = fiyat * yeni_miktar
                
                self.cursor.execute('''
                    UPDATE masa_siparisleri 
                    SET miktar = ?, tutar = ? 
                    WHERE masa_no = ? AND urun_adi = ?
                ''', (yeni_miktar, yeni_tutar, self.aktif_masa, urun_adi))
            
            # Masanın toplamını güncelle
            self.cursor.execute('''
                UPDATE masalar 
                SET toplam = (
                    SELECT COALESCE(SUM(tutar), 0) 
                    FROM masa_siparisleri 
                    WHERE masa_no = ?
                ),
                son_adisyon_zamani = ?,
                son_islem_zamani = ?
                WHERE masa_no = ?
            ''', (self.aktif_masa, self.tarih_saat_al(), self.tarih_saat_al(), self.aktif_masa))
            
            self.conn.commit()
            self.sepeti_yukle()
    
    def sepeti_temizle(self):
        self.sepet_tablo.delete(*self.sepet_tablo.get_children())
        self.toplam_tutar = 0
        self.iskonto = 0
        self.toplam_guncelle()
        
        if self.aktif_masa:
            # Masanın siparişlerini sil
            self.cursor.execute('''
                DELETE FROM masa_siparisleri WHERE masa_no = ?
            ''', (self.aktif_masa,))
            
            # Masayı güncelle
            self.cursor.execute('''
                UPDATE masalar 
                SET toplam = 0, durum = 'boş', son_islem_zamani = ?
                WHERE masa_no = ?
            ''', (self.tarih_saat_al(), self.aktif_masa))
            
            self.conn.commit()
            self.masa_butonlarini_guncelle()
    
    def toplam_guncelle(self):
        self.toplam_tutar = 0
        for item in self.sepet_tablo.get_children():
            tutar = float(self.sepet_tablo.item(item, "values")[3])
            self.toplam_tutar += tutar
        
        self.toplam_label.config(text=f"Toplam: {self.toplam_tutar:.2f} TL")
        self.iskonto_label.config(text=f"İskonto: {self.iskonto:.2f} TL")
        self.net_tutar_label.config(text=f"Net Tutar: {self.toplam_tutar - self.iskonto:.2f} TL")
    
    def nakit_odeme(self):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        # Ara ödemeleri topla
        self.cursor.execute('''
            SELECT COALESCE(SUM(miktar), 0) FROM ara_odemeler 
            WHERE masa_no = ?
        ''', (self.aktif_masa,))
        ara_odemeler_toplam = self.cursor.fetchone()[0]
        
        # Toplam tutarı al
        self.cursor.execute('''
            SELECT toplam FROM masalar WHERE masa_no = ?
        ''', (self.aktif_masa,))
        toplam_tutar = self.cursor.fetchone()[0]
        
        kalan_tutar = toplam_tutar - ara_odemeler_toplam
        
        messagebox.showinfo(
            "Masa Hesap Bilgisi",
            f"Masa: {self.aktif_masa}\n"
            f"Toplam Tutar: {toplam_tutar:.2f} TL\n"
            f"Yapılan Ara Ödemeler: {ara_odemeler_toplam:.2f} TL\n"
            f"Kalan Tutar: {kalan_tutar:.2f} TL\n\n"
            "Nakit ödeme alındıktan sonra 'Masa Kapat' butonu ile kapatabilirsiniz."
        )
    
    def ara_odeme(self):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        if not self.sepet_tablo.get_children():
            messagebox.showwarning("Uyarı", "Sepetiniz boş!")
            return
        
        # Ara ödemeleri topla
        self.cursor.execute('''
            SELECT COALESCE(SUM(miktar), 0) FROM ara_odemeler 
            WHERE masa_no = ?
        ''', (self.aktif_masa,))
        ara_odemeler_toplam = self.cursor.fetchone()[0]
        
        # Toplam tutarı al
        self.cursor.execute('''
            SELECT toplam FROM masalar WHERE masa_no = ?
        ''', (self.aktif_masa,))
        toplam_tutar = self.cursor.fetchone()[0]
        
        kalan_tutar = toplam_tutar - ara_odemeler_toplam
        
        odeme = simpledialog.askfloat(
            "Ara Ödeme", 
            f"Kalan Tutar: {kalan_tutar:.2f} TL\nÖdeme Miktarı (TL):",
            minvalue=0,
            maxvalue=kalan_tutar,
            parent=self.root
        )
        
        if odeme and odeme > 0:
            # Ara ödemeyi kaydet
            self.cursor.execute('''
                INSERT INTO ara_odemeler (masa_no, miktar, tarih)
                VALUES (?, ?, ?)
            ''', (self.aktif_masa, odeme, self.tarih_saat_al()))
            
            self.conn.commit()
            self.masa_butonlarini_guncelle()
            
            yeni_kalan = kalan_tutar - odeme
            messagebox.showinfo(
                "Başarılı", 
                f"{odeme:.2f} TL ara ödeme alındı.\nKalan tutar: {yeni_kalan:.2f} TL"
            )
    
    def odeme_yap(self, odeme_turu):
        if not self.aktif_masa:
            messagebox.showwarning("Uyarı", "Önce bir masa seçmelisiniz!")
            return
        
        if not self.sepet_tablo.get_children():
            messagebox.showwarning("Uyarı", "Sepetiniz boş!")
            return
        
        masa_no = self.aktif_masa
        
        # Masa bilgilerini al
        self.cursor.execute('''
            SELECT toplam, musteri_id, acilis FROM masalar 
            WHERE masa_no = ?
        ''', (masa_no,))
        toplam, musteri_id, acilis = self.cursor.fetchone()
        
        # Ara ödemeleri topla
        self.cursor.execute('''
            SELECT COALESCE(SUM(miktar), 0) FROM ara_odemeler 
            WHERE masa_no = ?
        ''', (masa_no,))
        ara_odemeler_toplam = self.cursor.fetchone()[0]
        
        net_tutar = toplam - ara_odemeler_toplam
        
        if net_tutar <= 0:
            messagebox.showwarning("Uyarı", "Bu masanın ödemesi zaten tamamlanmış!")
            return
        
        # Sipariş geçmişine kaydet
        self.cursor.execute('''
            INSERT INTO siparis_gecmisi 
            (masa_no, tarih, odeme_turu, toplam, musteri_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (masa_no, self.tarih_saat_al(), odeme_turu, toplam, musteri_id))
        
        siparis_id = self.cursor.lastrowid
        
        # Sipariş detaylarını kaydet
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
            ''', (siparis_id, *detay))
        
        # Masa geçmişine kaydet
        self.cursor.execute('''
            INSERT INTO masa_gecmisi 
            (masa_no, acilis, kapanis, musteri_id, toplam, odeme_turu, tarih)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (masa_no, acilis, self.tarih_saat_al(), musteri_id, toplam, odeme_turu, self.tarih_saat_al()))
        
        # Müşteri puanını güncelle
        if musteri_id and net_tutar > 0:
            self.cursor.execute('''
                UPDATE musteriler 
                SET puan = puan + ?
                WHERE musteri_id = ?
            ''', (int(net_tutar / 10), musteri_id))
        
        # Fatura oluştur
        fatura = f" ADİSYON DETAY & FATURA \n"
        fatura += f"Masa: {masa_no}\n"
        fatura += f"Açılış: {acilis}\n"
        fatura += f"Kapanış: {self.tarih_saat_al()}\n"
        fatura += f"Ödeme Türü: {odeme_turu}\n"
        
        if musteri_id:
            self.cursor.execute('''
                SELECT ad FROM musteriler WHERE musteri_id = ?
            ''', (musteri_id,))
            musteri_adi = self.cursor.fetchone()[0]
            fatura += f"Müşteri: {musteri_adi}\n"
        
        fatura += "/ - / -/ - / - / - / - / - / - / - /- /\n"
        for detay in siparis_detaylari:
            fatura += f"{detay[0]} x{detay[2]}: {detay[3]:.2f} TL\n"
        
        fatura += "/ - / -/ - / - / - / - / - / - / - /- /\n"
        fatura += f"Toplam: {toplam:.2f} TL\n"
        if ara_odemeler_toplam > 0:
            fatura += f"Ara Ödemeler: {ara_odemeler_toplam:.2f} TL\n"
        fatura += f"Net Ödeme: {net_tutar:.2f} TL\n"
        fatura += "=== Teşekkür Ederiz ==="
        
        popup = tk.Toplevel(self.root)
        popup.title("Fatura")
        tk.Label(popup, text=fatura, font=("Arial", 10, "bold"), justify="center").pack(padx=20, pady=20)
        tk.Button(popup, text="Tamam", command=popup.destroy).pack(pady=10)
        
        # Masayı temizle
        self.cursor.execute('''
            DELETE FROM masa_siparisleri WHERE masa_no = ?
        ''', (masa_no,))
        
        self.cursor.execute('''
            DELETE FROM ara_odemeler WHERE masa_no = ?
        ''', (masa_no,))
        
        self.cursor.execute('''
            UPDATE masalar 
            SET durum = 'boş', toplam = 0, musteri_id = NULL,
                acilis = NULL, kapanis = NULL, 
                son_adisyon_zamani = NULL, son_islem_zamani = ?
            WHERE masa_no = ?
        ''', (self.tarih_saat_al(), masa_no))
        
        self.conn.commit()
        
        self.aktif_masa = None
        if hasattr(self, 'aktif_masa_label'):
            self.aktif_masa_label.config(text="Aktif Masa: Seçili değil")
        if hasattr(self, 'musteri_label'):
            self.musteri_label.config(text="Müşteri: -")
        self.sepeti_temizle()
        self.masa_butonlarini_guncelle()

    # MÜŞTERİ İŞLEMLERİ
    def musteri_arayuz_olustur(self):
        liste_frame = tk.Frame(self.musteri_frame)
        liste_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.musteri_listesi = ttk.Treeview(
            liste_frame,
            columns=("ID", "Ad", "Telefon", "Puan", "Kayıt"),
            show="headings",
            padding=0,
            style="Treeview"
        )

        self.musteri_listesi.heading("ID", text="ID")
        self.musteri_listesi.heading("Ad", text="Müşteri Adı")
        self.musteri_listesi.heading("Telefon", text="Telefon")
        self.musteri_listesi.heading("Puan", text="Puan")
        self.musteri_listesi.heading("Kayıt", text="Kayıt Tarihi")
        self.musteri_listesi.column("ID", width=50, stretch=False, anchor='center')
        self.musteri_listesi.column("Ad", width=200, stretch=False, anchor='center')
        self.musteri_listesi.column("Telefon", width=100, stretch=False, anchor='center')
        self.musteri_listesi.column("Puan", width=50, stretch=False, anchor='center')
        self.musteri_listesi.column("Kayıt", width=100, stretch=False, anchor='center')
        self.musteri_listesi.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self.musteri_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Müşteri Ekle", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.musteri_ekle).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Müşteri Sil", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.musteri_sil).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Müşteri Düzenle", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.musteri_duzenle).pack(side=tk.LEFT, padx=5)
        
        self.musteri_listesini_guncelle()
    
    def musteri_ekle(self):
        ad = simpledialog.askstring("Müşteri Ekle", "Müşteri Adı:")
        if ad:
            telefon = simpledialog.askstring("Müşteri Ekle", "Telefon:")
            if telefon:
                musteri_id = str(int(datetime.now().timestamp()))[-6:]
                self.cursor.execute('''
                    INSERT INTO musteriler 
                    (musteri_id, ad, telefon, kayit_tarihi)
                    VALUES (?, ?, ?, ?)
                ''', (musteri_id, ad, telefon, datetime.now().strftime("%d.%m.%Y")))
                
                self.conn.commit()
                self.musteri_listesini_guncelle()
                messagebox.showinfo("Başarılı", "Müşteri eklendi!")
    
    def musteri_sil(self):
        selected = self.musteri_listesi.selection()
        if selected:
            musteri_id = self.musteri_listesi.item(selected[0], "values")[0]
            if messagebox.askyesno("Onay", "Bu müşteriyi silmek istediğinize emin misiniz?"):
                # Masalardan müşteri referanslarını kaldır
                self.cursor.execute('''
                    UPDATE masalar SET musteri_id = NULL 
                    WHERE musteri_id = ?
                ''', (musteri_id,))
                
                # Müşteriyi sil
                self.cursor.execute('''
                    DELETE FROM musteriler WHERE musteri_id = ?
                ''', (musteri_id,))
                
                self.conn.commit()
                self.musteri_listesini_guncelle()
                self.masa_butonlarini_guncelle()
                if self.aktif_masa:
                    self.musteri_label.config(text="Müşteri: -")
    
    def musteri_duzenle(self):
        selected = self.musteri_listesi.selection()
        if selected:
            musteri_id = self.musteri_listesi.item(selected[0], "values")[0]
            
            self.cursor.execute('''
                SELECT ad, telefon FROM musteriler WHERE musteri_id = ?
            ''', (musteri_id,))
            musteri = self.cursor.fetchone()
            
            yeni_ad = simpledialog.askstring("Düzenle", "Yeni Ad:", initialvalue=musteri[0])
            if yeni_ad:
                yeni_tel = simpledialog.askstring("Düzenle", "Yeni Telefon:", initialvalue=musteri[1])
                if yeni_tel:
                    self.cursor.execute('''
                        UPDATE musteriler 
                        SET ad = ?, telefon = ? 
                        WHERE musteri_id = ?
                    ''', (yeni_ad, yeni_tel, musteri_id))
                    
                    self.conn.commit()
                    self.musteri_listesini_guncelle()
                    
                    # Aktif masadaki müşteri bilgisini güncelle
                    if self.aktif_masa:
                        self.cursor.execute('''
                            SELECT musteri_id FROM masalar WHERE masa_no = ?
                        ''', (self.aktif_masa,))
                        aktif_musteri = self.cursor.fetchone()[0]
                        
                        if aktif_musteri == musteri_id:
                            self.musteri_label.config(text=f"Müşteri: {yeni_ad}")
                    
                    messagebox.showinfo("Başarılı", "Müşteri bilgileri güncellendi!")
    
    def musteri_listesini_guncelle(self):
        self.musteri_listesi.delete(*self.musteri_listesi.get_children())
        
        self.cursor.execute('''
            SELECT musteri_id, ad, telefon, puan, kayit_tarihi 
            FROM musteriler 
            ORDER BY ad
        ''')
        
        for musteri in self.cursor.fetchall():
            self.musteri_listesi.insert("", "end", values=musteri)

    # ÜRÜN YÖNETİMİ
    def urun_arayuz_olustur(self):
        liste_frame = tk.Frame(self.urun_frame)
        liste_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sıra sütununu ekleyerek Treeview'ı güncelle
        style = ttk.Style()
        style.configure("Treeview", padding=0, borderwidth=0)

        self.urun_listesi = ttk.Treeview(
            liste_frame,
            columns=("Sira", "Ad", "Fiyat", "Kategori"),
            show="headings",
            padding=0,
            style="Treeview"
        )
        self.urun_listesi.heading("Sira", text="Sıra")
        self.urun_listesi.heading("Ad", text="Ürün Adı")
        self.urun_listesi.heading("Fiyat", text="Fiyat")
        self.urun_listesi.heading("Kategori", text="Kategori")
        self.urun_listesi.column("Sira", width=50, stretch=False, anchor='center')
        self.urun_listesi.column("Ad", width=200, stretch=False, anchor='center')
        self.urun_listesi.column("Fiyat", width=100, stretch=False, anchor='center')
        self.urun_listesi.column("Kategori", width=200, stretch=False, anchor='center')
        self.urun_listesi.pack(fill=tk.BOTH, expand=True)
        
        btn_frame = tk.Frame(self.urun_frame)
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Ürün Ekle", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.urun_ekle_panel).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Ürün Sil", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.urun_sil).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Fiyat Güncelle", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.urun_fiyat_guncelle).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Kategori Değiştir", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.urun_kategori_degistir).pack(side=tk.LEFT, padx=5)
        ### YENİ EKLENEN BUTON ###
        tk.Button(btn_frame, text="Sıra Değiştir", width=14, height=2, bg="#fdd364", font=("Arial", 9, "bold"), command=self.urun_sira_degistir).pack(side=tk.LEFT, padx=5)
        
        self.urun_listesini_guncelle()
    
    def urun_ekle_panel(self):
        ekle_pencere = tk.Toplevel(self.root)
        ekle_pencere.title("Yeni Ürün Ekle")
        ekle_pencere.resizable(False, False)
        
        tk.Label(ekle_pencere, text="Ürün Adı:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        urun_adi_entry = tk.Entry(ekle_pencere, width=25)
        urun_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(ekle_pencere, text="Fiyat (TL):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        fiyat_entry = tk.Entry(ekle_pencere, width=10)
        fiyat_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(ekle_pencere, text="Kategori:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        kategori_combobox = ttk.Combobox(ekle_pencere, values=list(self.kategori_renkleri.keys()), state="readonly")
        kategori_combobox.current(0)
        kategori_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        ### YENİ EKLENEN KISIM ###
        tk.Label(ekle_pencere, text="Sıra No:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        sira_spinbox = tk.Spinbox(ekle_pencere, from_=1, to=999, width=5)
        sira_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        ### YENİ EKLENEN KISIM SONU ###

        # Otomatik sıra numarası önerisi
        self.cursor.execute("SELECT MAX(sira) FROM urunler")
        max_sira = self.cursor.fetchone()[0] or 0
        tk.Label(ekle_pencere, text="Sıra No:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        sira_spinbox = tk.Spinbox(ekle_pencere, from_=1, to=999, width=5)
        sira_spinbox.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        sira_spinbox.delete(0, tk.END)
        sira_spinbox.insert(0, max_sira + 1)  # En yüksek sıradan sonraki numarayı öner
        
        def kaydet():
            urun_adi = urun_adi_entry.get().strip().upper()
            if not urun_adi:
                messagebox.showwarning("Uyarı", "Ürün adı boş olamaz!")
                return
            
            try:
                fiyat = float(fiyat_entry.get())
                if fiyat <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz fiyat değeri! Pozitif sayı girin.")
                return
            
            kategori = kategori_combobox.get()
            
            ### DEĞİŞTİRİLEN KISIM ###
            try:
                sira = int(sira_spinbox.get())
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçersiz sıra numarası! Sayı girin.")
                return
            
            try:
                self.cursor.execute('''
                    INSERT INTO urunler (urun_adi, fiyat, kategori, sira)
                    VALUES (?, ?, ?, ?)
                ''', (urun_adi, fiyat, kategori, sira))
                ### DEĞİŞTİRİLEN KISIM SONU ###
                
                self.conn.commit()
                self.urun_listesini_guncelle()
                self.hizli_satis_butonlari_olustur()
                messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!")
                ekle_pencere.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Hata", "Bu ürün adı zaten mevcut!")

        tk.Button(ekle_pencere, text="Kaydet", command=kaydet).grid(row=4, column=0, columnspan=2, pady=10)
    
    def urun_sil(self):
        selected = self.urun_listesi.selection()
        if selected:
            urun = self.urun_listesi.item(selected[0], "values")[0]
            if messagebox.askyesno("Onay", f"{urun} ürününü silmek istediğinize emin misiniz?"):
                try:
                    # Ürünü sil
                    self.cursor.execute('''
                        DELETE FROM urunler WHERE urun_adi = ?
                    ''', (urun,))
                    
                    # Masalardaki bu ürünün siparişlerini sil
                    self.cursor.execute('''
                        DELETE FROM masa_siparisleri WHERE urun_adi = ?
                    ''', (urun,))
                    
                    # Masaların toplamını güncelle
                    self.cursor.execute('''
                        UPDATE masalar 
                        SET toplam = (
                            SELECT COALESCE(SUM(tutar), 0) 
                            FROM masa_siparisleri 
                            WHERE masa_no = masalar.masa_no
                        )
                    ''')
                    
                    self.conn.commit()
                    self.urun_listesini_guncelle()
                    self.hizli_satis_butonlari_olustur()
                    
                    if self.aktif_masa:
                        self.sepeti_yukle()
                        self.toplam_guncelle()
                    
                    self.masa_butonlarini_guncelle()
                    messagebox.showinfo("Başarılı", "Ürün silindi!")
                except Exception as e:
                    messagebox.showerror("Hata", f"Ürün silinirken hata oluştu: {str(e)}")
    
    def urun_fiyat_guncelle(self):
        selected = self.urun_listesi.selection()
        if selected:
            urun = self.urun_listesi.item(selected[0], "values")[0]
            
            self.cursor.execute('''
                SELECT fiyat FROM urunler WHERE urun_adi = ?
            ''', (urun,))
            mevcut_fiyat = self.cursor.fetchone()[0]
            
            while True:
                yeni_fiyat = simpledialog.askstring("Fiyat Güncelle", 
                                                  f"{urun} için yeni fiyat (TL):",
                                                  initialvalue=str(mevcut_fiyat))
                if yeni_fiyat is None:
                    return
                
                try:
                    fiyat_float = float(yeni_fiyat)
                    if fiyat_float <= 0:
                        raise ValueError
                        
                    # Ürün fiyatını güncelle
                    self.cursor.execute('''
                        UPDATE urunler SET fiyat = ? WHERE urun_adi = ?
                    ''', (fiyat_float, urun))
                    
                    # Masalardaki bu ürünün fiyatlarını güncelle
                    self.cursor.execute('''
                        UPDATE masa_siparisleri 
                        SET fiyat = ?, tutar = ? * miktar
                        WHERE urun_adi = ?
                    ''', (fiyat_float, fiyat_float, urun))
                    
                    # Masaların toplamını güncelle
                    self.cursor.execute('''
                        UPDATE masalar 
                        SET toplam = (
                            SELECT COALESCE(SUM(tutar), 0) 
                            FROM masa_siparisleri 
                            WHERE masa_no = masalar.masa_no
                        )
                    ''')
                    
                    self.conn.commit()
                    break
                    
                except ValueError:
                    messagebox.showwarning("Uyarı", "Lütfen pozitif sayı giriniz!")
                    continue
                
            self.urun_listesini_guncelle()
            self.hizli_satis_butonlari_olustur()
            
            if self.aktif_masa:
                self.sepeti_yukle()
                self.toplam_guncelle()
            
            self.masa_butonlarini_guncelle()
            messagebox.showinfo("Başarılı", "Fiyat güncellendi!")
    
    def urun_kategori_degistir(self):
        selected = self.urun_listesi.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
            return
        
        urun_adi = self.urun_listesi.item(selected[0], "values")[0]
        
        self.cursor.execute('''
            SELECT kategori FROM urunler WHERE urun_adi = ?
        ''', (urun_adi,))
        mevcut_kategori = self.cursor.fetchone()[0]
        
        degistir_pencere = tk.Toplevel(self.root)
        degistir_pencere.title("Kategori Değiştir")
        degistir_pencere.geometry("300x200")
        degistir_pencere.resizable(False, False)
        
        tk.Label(degistir_pencere, text=f"Ürün: {urun_adi}").pack(pady=5)
        tk.Label(degistir_pencere, text="Yeni Kategori:").pack(pady=5)
        
        kategori_combobox = ttk.Combobox(degistir_pencere, values=list(self.kategori_renkleri.keys()), state="readonly")
        kategori_combobox.set(mevcut_kategori)
        kategori_combobox.pack(pady=5)
        
        def kaydet():
            yeni_kategori = kategori_combobox.get()
            self.cursor.execute('''
                UPDATE urunler SET kategori = ? WHERE urun_adi = ?
            ''', (yeni_kategori, urun_adi))
            self.conn.commit()
            
            self.urun_listesini_guncelle()
            self.hizli_satis_butonlari_olustur()
            messagebox.showinfo("Başarılı", "Kategori başarıyla değiştirildi!")
            degistir_pencere.destroy()
        
        tk.Button(degistir_pencere, text="Kaydet", command=kaydet).pack(pady=10)
    
    def urun_listesini_guncelle(self):
        self.urun_listesi.delete(*self.urun_listesi.get_children())
        
        self.cursor.execute('''
            SELECT sira, urun_adi, fiyat, kategori FROM urunler 
            ORDER BY sira, urun_adi
        ''')
        
        for urun in self.cursor.fetchall():
            self.urun_listesi.insert("", "end", values=urun)

    # MUHASEBE İŞLEMLERİ
    def muhasebe_arayuz_olustur(self):
        # Ana Frame
        main_frame = tk.Frame(self.muhasebe_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Rapor Kontrol Frame
        kontrol_frame = tk.Frame(main_frame)
        kontrol_frame.pack(pady=10, fill=tk.X)

        # Rapor Türü Seçimi
        tk.Label(kontrol_frame, text="Rapor Türü:").pack(side=tk.LEFT, padx=5)
        self.rapor_turu = ttk.Combobox(kontrol_frame,
                                    values=["Günlük", "Haftalık", "Aylık", "Özel Aralık"],
                                    state="readonly",
                                    width=12)
        self.rapor_turu.current(0)
        self.rapor_turu.pack(side=tk.LEFT, padx=5)
        self.rapor_turu.bind("<<ComboboxSelected>>", self._rapor_turu_degisti)

        # Tarih Seçim Frame (Dinamik içerik)
        self.tarih_frame = tk.Frame(kontrol_frame)
        self.tarih_frame.pack(side=tk.LEFT, padx=5)

        # Varsayılan olarak günlük tarih alanı
        tk.Label(self.tarih_frame, text="Tarih:").pack(side=tk.LEFT)
        self.tek_tarih = ttk.Entry(self.tarih_frame, width=10)
        self.tek_tarih.pack(side=tk.LEFT, padx=5)
        self.tek_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))

        # Rapor Butonları
        btn_frame = tk.Frame(kontrol_frame)
        btn_frame.pack(side=tk.RIGHT, padx=10)

        tk.Button(btn_frame, text="Rapor Oluştur", 
                command=self.rapor_olustur, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="TXT Olarak Kaydet", 
                command=self.excele_aktar, bg="#2196F3", fg="white").pack(side=tk.LEFT)
        
        temizle_btn = tk.Button(kontrol_frame, text="DB Temizle", 
                       command=self.veritabani_temizle, bg="#FF5722", fg="white")
        temizle_btn.pack(side=tk.LEFT, padx=5)

        # Rapor Görüntüleme Alanı
        self.rapor_notebook = ttk.Notebook(main_frame)
        self.rapor_notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Genel Rapor Sekmesi
        self.genel_rapor_frame = tk.Frame(self.rapor_notebook)
        self.rapor_notebook.add(self.genel_rapor_frame, text="Genel Rapor")
        
        self.genel_rapor_text = tk.Text(self.genel_rapor_frame, wrap=tk.WORD, font=("Arial", 10))
        scrollbar = tk.Scrollbar(self.genel_rapor_frame, command=self.genel_rapor_text.yview)
        self.genel_rapor_text.config(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.genel_rapor_text.pack(fill=tk.BOTH, expand=True)

        # Ürün Bazlı Rapor Sekmesi
        self.urun_rapor_frame = tk.Frame(self.rapor_notebook)
        self.rapor_notebook.add(self.urun_rapor_frame, text="Ürün Bazlı")
        
        self.urun_rapor_tree = ttk.Treeview(self.urun_rapor_frame, 
                                        columns=("Ürün", "Adet", "Tutar"), 
                                        show="headings")
        for col in ("Ürün", "Adet", "Tutar"):
            self.urun_rapor_tree.heading(col, text=col)
        self.urun_rapor_tree.column("Ürün", width=200)
        self.urun_rapor_tree.column("Adet", width=80, anchor='e')
        self.urun_rapor_tree.column("Tutar", width=100, anchor='e')
        scrollbar = ttk.Scrollbar(self.urun_rapor_frame, orient="vertical", command=self.urun_rapor_tree.yview)
        self.urun_rapor_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.urun_rapor_tree.pack(fill=tk.BOTH, expand=True)

        # Masa Hareketleri Sekmesi
        self.masa_rapor_frame = tk.Frame(self.rapor_notebook)
        self.rapor_notebook.add(self.masa_rapor_frame, text="Masa Hareketleri")
        
        self.masa_rapor_tree = ttk.Treeview(self.masa_rapor_frame,
                                        columns=("Masa", "Açılış", "Kapanış", "Süre", "Müşteri", "Toplam", "Ödeme"),
                                        show="headings")
                                        # Treeview stil ayarları
        for col in ("Masa", "Açılış", "Kapanış", "Süre", "Müşteri", "Toplam", "Ödeme"):
            self.masa_rapor_tree.heading(col, text=col)
        self.masa_rapor_tree.column("Masa", width=50)
        self.masa_rapor_tree.column("Açılış", width=120)
        self.masa_rapor_tree.column("Kapanış", width=120)
        self.masa_rapor_tree.column("Süre", width=80)
        self.masa_rapor_tree.column("Müşteri", width=150)
        self.masa_rapor_tree.column("Toplam", width=80, anchor='e')
        self.masa_rapor_tree.column("Ödeme", width=100)
        scrollbar = ttk.Scrollbar(self.masa_rapor_frame, orient="vertical", command=self.masa_rapor_tree.yview)
        self.masa_rapor_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.masa_rapor_tree.pack(fill=tk.BOTH, expand=True)
        
        # Masa detay butonu
        tk.Button(self.masa_rapor_frame, text="Detay Göster", 
                command=self.masa_detay_goster).pack(side=tk.BOTTOM, pady=5)

    def _rapor_turu_degisti(self, event=None):
        for widget in self.tarih_frame.winfo_children():
            widget.destroy()

        secim = self.rapor_turu.get()
        
        if secim == "Özel Aralık":
            tk.Label(self.tarih_frame, text="Başlangıç:").pack(side=tk.LEFT)
            self.baslangic_tarih = ttk.Entry(self.tarih_frame, width=10)
            self.baslangic_tarih.pack(side=tk.LEFT, padx=5)
            self.baslangic_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
            
            tk.Label(self.tarih_frame, text="Bitiş:").pack(side=tk.LEFT)
            self.bitis_tarih = ttk.Entry(self.tarih_frame, width=10)
            self.bitis_tarih.pack(side=tk.LEFT, padx=5)
            self.bitis_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        else:
            tk.Label(self.tarih_frame, text="Tarih:").pack(side=tk.LEFT)
            self.tek_tarih = ttk.Entry(self.tarih_frame, width=10)
            self.tek_tarih.pack(side=tk.LEFT, padx=5)
            self.tek_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))

    def rapor_olustur(self):
        try:
            # Önce rapor alanlarını temizle
            self.genel_rapor_text.delete(1.0, tk.END)
            self.urun_rapor_tree.delete(*self.urun_rapor_tree.get_children())
            self.masa_rapor_tree.delete(*self.masa_rapor_tree.get_children())

            # Tarih kontrol fonksiyonu
            def parse_date(date_str):
                try:
                    return datetime.strptime(date_str, "%d.%m.%Y")
                except ValueError:
                    messagebox.showerror("Hata", f"Geçersiz tarih: {date_str}\nLütfen gg.aa.yyyy formatında girin.")
                    return None

            # Rapor türüne göre tarih aralığını belirle
            rapor_turu = self.rapor_turu.get()
            bugun = datetime.now()
            
            if rapor_turu == "Özel Aralık":
                baslangic = parse_date(self.baslangic_tarih.get())
                bitis = parse_date(self.bitis_tarih.get())
                if baslangic is None or bitis is None:
                    return
                bitis += timedelta(days=1)  # Bitiş tarihini dahil etmek için
            else:
                tarih = parse_date(self.tek_tarih.get())
                if tarih is None:
                    return
                    
                if rapor_turu == "Günlük":
                    baslangic = tarih.replace(hour=0, minute=0, second=0)
                    bitis = tarih.replace(hour=23, minute=59, second=59)
                elif rapor_turu == "Haftalık":
                    baslangic = tarih - timedelta(days=tarih.weekday())
                    bitis = baslangic + timedelta(days=6, hours=23, minutes=59, seconds=59)
                elif rapor_turu == "Aylık":
                    baslangic = tarih.replace(day=1, hour=0, minute=0, second=0)
                    bitis = (baslangic + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                    bitis = bitis.replace(hour=23, minute=59, second=59)

            # Tarih formatını düzelt
            baslangic_str = baslangic.strftime("%d.%m.%Y %H:%M")
            bitis_str = bitis.strftime("%d.%m.%Y %H:%M")

            # 1. Genel Rapor Verileri
            self.cursor.execute('''
                SELECT strftime('%d.%m.%Y', tarih) as gun,
                    SUM(toplam) as ciro,
                    COUNT(*) as siparis_sayisi
                FROM siparis_gecmisi
                WHERE tarih BETWEEN ? AND ?
                GROUP BY gun
                ORDER BY date(gun)''', (baslangic_str, bitis_str))
            
            gunluk_hasilat = self.cursor.fetchall()
            
            # Genel raporu oluştur
            self.genel_rapor_text.insert(tk.END, f"=== {rapor_turu.upper()} RAPOR ===\n")
            self.genel_rapor_text.insert(tk.END, f"Tarih Aralığı: {baslangic.strftime('%d.%m.%Y')} - {bitis.strftime('%d.%m.%Y')}\n\n")
            
            self.genel_rapor_text.insert(tk.END, "GÜNLÜK HASILAT\n")
            self.genel_rapor_text.insert(tk.END, "Tarih\t\tToplam Ciro\tSipariş Sayısı\n")
            self.genel_rapor_text.insert(tk.END, "-"*50 + "\n")
            
            toplam_ciro = 0
            toplam_siparis = 0
            
            for gun, ciro, siparis_sayisi in gunluk_hasilat:
                self.genel_rapor_text.insert(tk.END, f"{gun}\t{ciro:.2f} TL\t\t{siparis_sayisi}\n")
                toplam_ciro += ciro
                toplam_siparis += siparis_sayisi
            
            self.genel_rapor_text.insert(tk.END, "-"*50 + "\n")
            self.genel_rapor_text.insert(tk.END, f"TOPLAM: \t{toplam_ciro:.2f} TL\t\t{toplam_siparis}\n\n")

            # 2. Ürün Bazlı Satışlar
            self.cursor.execute('''
                SELECT sd.urun_adi, SUM(sd.miktar), SUM(sd.tutar)
                FROM siparis_detaylari sd
                JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
                WHERE sg.tarih BETWEEN ? AND ?
                GROUP BY sd.urun_adi
                ORDER BY SUM(sd.tutar) DESC''', (baslangic_str, bitis_str))
            
            urun_satis = self.cursor.fetchall()
            
            for urun in urun_satis:
                self.urun_rapor_tree.insert("", tk.END, values=(
                    urun[0], 
                    int(urun[1]), 
                    f"{urun[2]:.2f} TL"
                ))

            # 3. Masa Hareketleri
            self.cursor.execute('''
                SELECT masa_no, acilis, kapanis,
                    ROUND((julianday(kapanis) - julianday(acilis)) * 1440) as sure_dakika,
                    (SELECT ad FROM musteriler WHERE musteri_id = mg.musteri_id),
                    toplam, odeme_turu
                FROM masa_gecmisi mg
                WHERE tarih BETWEEN ? AND ?
                ORDER BY date(acilis)''', (baslangic_str, bitis_str))
            
            masa_hareketleri = self.cursor.fetchall()
            
            for hareket in masa_hareketleri:
                sure_dakika = hareket[3] or 0
                sure_str = f"{sure_dakika//60} sa {sure_dakika%60} dk"
                
                self.masa_rapor_tree.insert("", tk.END, values=(
                    hareket[0],  # Masa No
                    hareket[1] or "-",  # Açılış
                    hareket[2] or "-",  # Kapanış
                    sure_str,
                    hareket[4] or "Misafir",  # Müşteri
                    f"{hareket[5]:.2f}" if hareket[5] else "0.00",  # Toplam
                    hareket[6] or "Bilinmiyor"  # Ödeme Türü
                ))

            messagebox.showinfo("Başarılı", "Rapor başarıyla oluşturuldu")

        except Exception as e:
            messagebox.showerror("Hata", f"Rapor oluşturulamadı:\n{str(e)}")
            import traceback
            traceback.print_exc()

    def masa_detay_goster(self):
        selected = self.masa_rapor_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir masa hareketi seçin!")
            return
        
        secili = self.masa_rapor_tree.item(selected[0], "values")
        masa_no = secili[0]
        acilis = secili[1]
        
        # Sipariş detaylarını getir
        self.cursor.execute('''
            SELECT sd.urun_adi, sd.fiyat, sd.miktar, sd.tutar
            FROM siparis_detaylari sd
            JOIN siparis_gecmisi sg ON sd.siparis_id = sg.id
            WHERE sg.masa_no = ? AND sg.tarih = (
                SELECT tarih FROM masa_gecmisi 
                WHERE masa_no = ? AND acilis = ?
            )
        ''', (masa_no, masa_no, acilis))
        
        detaylar = self.cursor.fetchall()
        
        if not detaylar:
            messagebox.showwarning("Uyarı", "Detay bilgisi bulunamadı!")
            return
        
        detay_penceresi = tk.Toplevel(self.root)
        detay_penceresi.title(f"Masa {masa_no} Detayları")
        detay_penceresi.geometry("500x400")
        
        bilgi_frame = tk.Frame(detay_penceresi)
        bilgi_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(bilgi_frame, text=f"Masa No: {masa_no}", font=("Arial", 10, "bold")).pack(anchor="w")
        tk.Label(bilgi_frame, text=f"Açılış: {acilis}").pack(anchor="w")
        tk.Label(bilgi_frame, text=f"Kapanış: {secili[2]}").pack(anchor="w")
        tk.Label(bilgi_frame, text=f"Süre: {secili[3]}").pack(anchor="w")
        tk.Label(bilgi_frame, text=f"Müşteri: {secili[4]}").pack(anchor="w")
        tk.Label(bilgi_frame, text=f"Toplam: {secili[5]} TL", font=("Arial", 10, "bold")).pack(anchor="w")
        
        urun_frame = tk.Frame(detay_penceresi)
        urun_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        tk.Label(urun_frame, text="Sipariş Edilen Ürünler:", font=("Arial", 9, "bold")).pack(anchor="w")
        
        urun_tree = ttk.Treeview(urun_frame, columns=("Urun", "Adet", "Tutar"), show="headings", height=5)
        urun_tree.heading("Urun", text="Ürün Adı")
        urun_tree.heading("Adet", text="Adet")
        urun_tree.heading("Tutar", text="Tutar")
        urun_tree.column("Urun", width=250)
        urun_tree.column("Adet", width=80, anchor='e')
        urun_tree.column("Tutar", width=80, anchor='e')
        
        scrollbar = ttk.Scrollbar(urun_frame, orient="vertical", command=urun_tree.yview)
        urun_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        urun_tree.pack(fill=tk.BOTH, expand=True)
        
        for urun in detaylar:
            urun_tree.insert("", "end", values=(
                urun[0],
                urun[2],
                f"{urun[3]:.2f} TL"
            ))

    def excele_aktar(self):
        try:
            # Rapor başlığını ve tarih aralığını al
            rapor_basligi = self.genel_rapor_text.get("1.0", "1.end").strip("= \n")
            tarih_araligi = self.genel_rapor_text.get("2.0", "2.end").strip()
            
            # Dosya adını oluştur (tarihe göre otomatik)
            dosya_adi = f"rapor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(dosya_adi, "w", encoding="utf-8") as f:
                # Başlık
                f.write(f"{'='*50}\n{rapor_basligi}\n{tarih_araligi}\n{'='*50}\n\n")
                
                # Genel rapor
                f.write(self.genel_rapor_text.get("4.0", tk.END))
                
                # Ürün bazlı veriler
                f.write("\nÜRÜN BAZLI SATIŞLAR:\n")
                f.write("-"*50 + "\n")
                for item in self.urun_rapor_tree.get_children():
                    f.write(" | ".join(self.urun_rapor_tree.item(item, "values")))
                    f.write("\n")
                
                # Masa hareketleri
                f.write("\nMASA HAREKETLERİ:\n")
                f.write("-"*50 + "\n")
                for item in self.masa_rapor_tree.get_children():
                    f.write(" | ".join(self.masa_rapor_tree.item(item, "values")))
                    f.write("\n")
            
            # Başarı mesajı
            mesaj = f"""Rapor başarıyla kaydedildi:
    {dosya_adi}

    Excel'e aktarmak için:
    1. Excel'de "Veri" sekmesini açın
    2. "Metni Sütunlara Dönüştür" seçeneğini tıklayın
    3. Ayırıcı olarak "|" işaretini seçin"""
            
            messagebox.showinfo("Başarılı", mesaj)
            
            # Dosyayı otomatik aç
            if os.name == 'nt':
                os.startfile(dosya_adi)
            else:
                subprocess.call(['xdg-open' if os.name == 'posix' else 'open', dosya_adi])
                
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya oluşturulamadı:\n{str(e)}")

    def sekme_degisti(self, event):
        current_tab = self.notebook.index("current")
    
        if current_tab == 0:
            self.masa_butonlarini_guncelle()
        
            if self.aktif_masa:
                self.cursor.execute('''
                    SELECT COUNT(*) FROM masa_siparisleri 
                    WHERE masa_no = ?
                ''', (self.aktif_masa,))
                siparis_sayisi = self.cursor.fetchone()[0]
                
                if siparis_sayisi == 0:
                    self.cursor.execute('''
                        UPDATE masalar 
                        SET durum = 'boş', son_islem_zamani = ?
                        WHERE masa_no = ?
                    ''', (self.tarih_saat_al(), self.aktif_masa))
                   
                    self.conn.commit()
                    self.masa_butonlarini_guncelle()
    
        elif current_tab == 1:
            if self.aktif_masa:
                self.sepeti_yukle()
            else:
                messagebox.showinfo("Bilgi", "Lütfen önce bir masa seçin!")
                self.notebook.select(0)

    def tarih_saat_al(self):
        return datetime.now().strftime("%d.%m.%Y %H:%M")

    def __del__(self):
        """Nesne yok edilirken veritabanı bağlantısını kapat"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = CafeAdisyonProgrami(root)
    root.mainloop()