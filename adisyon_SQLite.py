import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import sqlite3
import csv

class MasaSistemi:
    def __init__(self, root):
        self.root = root
        self.root.title("Kale Adisyon Sistemi")
        self.root.geometry("1000x800")
        
        # Veritabanı bağlantısı ve tablo oluşturma
        self.db_connect()
        self.create_tables()
        self.insert_sample_data()  # Örnek verileri ekle
        
        # UI ayarları
        self.setup_ui()
        
        # Verileri yükle
        self.load_data()
    
    def db_connect(self):
        """Veritabanı bağlantısını kurar"""
        self.conn = sqlite3.connect('Kafe_Adisyon.db')
        self.cursor = self.conn.cursor()
    
    def create_tables(self):
        """Gerekli tabloları oluşturur"""
        # Kategoriler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS kategoriler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Ürünler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS urunler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT UNIQUE NOT NULL,
                fiyat REAL NOT NULL,
                kategori_id INTEGER,
                FOREIGN KEY (kategori_id) REFERENCES kategoriler(id)
            )
        ''')
        
        # Masalar tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS masalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT UNIQUE NOT NULL,
                durum TEXT NOT NULL,
                toplam REAL DEFAULT 0,
                acilis_zamani TEXT
            )
        ''')
        
        # Siparişler tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS siparisler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_id INTEGER NOT NULL,
                urun_id INTEGER NOT NULL,
                adet INTEGER NOT NULL,
                fiyat REAL NOT NULL,
                tarih TEXT NOT NULL,
                FOREIGN KEY (masa_id) REFERENCES masalar(id),
                FOREIGN KEY (urun_id) REFERENCES urunler(id)
            )
        ''')
        
        # Geçmiş adisyonlar tablosu
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS gecmis_adisyonlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_id INTEGER NOT NULL,
                tutar REAL NOT NULL,
                tarih TEXT NOT NULL,
                tip TEXT NOT NULL,
                FOREIGN KEY (masa_id) REFERENCES masalar(id)
            )
        ''')
        
        self.conn.commit()
    
    def insert_sample_data(self):
        """Örnek verileri ekler (sadece ilk çalışmada)"""
        try:
            # Örnek kategoriler
            kategoriler = ['Yiyecekler', 'İçecekler', 'Tatlılar']
            for kategori in kategoriler:
                self.cursor.execute(
                    "INSERT OR IGNORE INTO kategoriler (ad) VALUES (?)",
                    (kategori,)
                )
            
            # Örnek ürünler
            urunler = [
                ('Çorba', 25, 'Yiyecekler'),
                ('Izgara Tavuk', 45, 'Yiyecekler'),
                ('Kola', 12, 'İçecekler'),
                ('Su', 5, 'İçecekler'),
                ('Baklava', 35, 'Tatlılar')
            ]
            
            for urun in urunler:
                self.cursor.execute("SELECT id FROM kategoriler WHERE ad=?", (urun[2],))
                kategori_id = self.cursor.fetchone()[0]
                
                self.cursor.execute(
                    "INSERT OR IGNORE INTO urunler (ad, fiyat, kategori_id) VALUES (?, ?, ?)",
                    (urun[0], urun[1], kategori_id)
                )
            
            # Örnek masalar
            for i in range(1, 21):
                masa_adi = f"Masa {i}"
                self.cursor.execute(
                    "INSERT OR IGNORE INTO masalar (ad, durum) VALUES (?, ?)",
                    (masa_adi, "boş")
                )
            
            self.conn.commit()
        except sqlite3.Error as e:
            print("Örnek veriler zaten eklenmiş:", str(e))
    
    def setup_ui(self):
        # Ana notebook (sekmeler)
        self.notebook = ttk.Notebook(self.root)
        
        # Masalar sekmesi
        self.masalar_frame = tk.Frame(self.notebook)
        self.setup_masalar_sekme()
        
        # Ürünler sekmesi
        self.urunler_frame = tk.Frame(self.notebook)
        self.setup_urunler_sekme()
        
        # Raporlar sekmesi
        self.raporlar_frame = tk.Frame(self.notebook)
        self.setup_raporlar_sekme()
        
        # Kategoriler sekmesi
        self.kategoriler_frame = tk.Frame(self.notebook)
        self.setup_kategoriler_sekme()
        
        self.notebook.add(self.masalar_frame, text="Masalar")
        self.notebook.add(self.urunler_frame, text="Ürünler")
        self.notebook.add(self.kategoriler_frame, text="Kategoriler")
        self.notebook.add(self.raporlar_frame, text="Raporlar")
        self.notebook.pack(expand=True, fill="both")
        
        # Durum çubuğu
        self.status_bar = tk.Label(self.root, text="Hazır", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_masalar_sekme(self):
        # Başlık
        tk.Label(
            self.masalar_frame, 
            text="Masalar", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Masalar için canvas ve scrollbar
        canvas = tk.Canvas(self.masalar_frame)
        scrollbar = ttk.Scrollbar(self.masalar_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 4x5 masa gridi oluştur
        self.masa_buttons = []
        for i in range(4):
            row_frame = tk.Frame(scrollable_frame)
            row_frame.pack(pady=5)
            
            for j in range(5):
                masa_no = i * 5 + j + 1
                masa_adi = f"Masa {masa_no}"
                
                # Masa butonu - standart boyutta
                btn = tk.Button(
                    row_frame,
                    text=masa_adi,
                    width=16,
                    height=8,
                    command=lambda m=masa_adi: self.masa_click(m),
                    font=("Arial", 12)
                )
                btn.pack(side="left", padx=10)
                self.masa_buttons.append(btn)
    
    def setup_urunler_sekme(self):
        # Başlık
        tk.Label(
            self.urunler_frame, 
            text="Ürün Yönetimi", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Ürün listesi
        self.urun_listbox = tk.Listbox(
            self.urunler_frame, 
            height=15, 
            font=("Arial", 12),
            selectmode=tk.SINGLE
        )
        self.urun_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Ürün ekleme/silme/güncelleme alanı
        urun_islem_frame = tk.Frame(self.urunler_frame)
        urun_islem_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(urun_islem_frame, text="Ürün Adı:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.urun_adi_entry = tk.Entry(urun_islem_frame, font=("Arial", 12), width=20)
        self.urun_adi_entry.pack(side=tk.LEFT, padx=5)
        
        tk.Label(urun_islem_frame, text="Fiyat:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(10,0))
        
        self.urun_fiyat_entry = tk.Entry(urun_islem_frame, font=("Arial", 12), width=10)
        self.urun_fiyat_entry.pack(side=tk.LEFT)
        
        tk.Label(urun_islem_frame, text="Kategori:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(10,0))
        
        self.urun_kategori_combobox = ttk.Combobox(urun_islem_frame, font=("Arial", 12), width=15)
        self.urun_kategori_combobox.pack(side=tk.LEFT)
        
        # Butonlar
        button_frame = tk.Frame(self.urunler_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            button_frame, 
            text="Ürün Ekle", 
            command=self.urun_ekle,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Ürün Sil", 
            command=self.urun_sil,
            font=("Arial", 12),
            bg="#F44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Ürün Güncelle", 
            command=self.urun_guncelle,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Excel'den İçe Aktar", 
            command=self.urun_icerik_aktar,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_kategoriler_sekme(self):
        # Başlık
        tk.Label(
            self.kategoriler_frame, 
            text="Kategori Yönetimi", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Kategori listesi
        self.kategori_listbox = tk.Listbox(
            self.kategoriler_frame, 
            height=15, 
            font=("Arial", 12),
            selectmode=tk.SINGLE
        )
        self.kategori_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Kategori ekleme alanı
        kategori_islem_frame = tk.Frame(self.kategoriler_frame)
        kategori_islem_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(kategori_islem_frame, text="Kategori Adı:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.kategori_adi_entry = tk.Entry(kategori_islem_frame, font=("Arial", 12), width=30)
        self.kategori_adi_entry.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = tk.Frame(self.kategoriler_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            button_frame, 
            text="Kategori Ekle", 
            command=self.kategori_ekle,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Kategori Sil", 
            command=self.kategori_sil,
            font=("Arial", 12),
            bg="#F44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Kategori Güncelle", 
            command=self.kategori_guncelle,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
    
    def setup_raporlar_sekme(self):
        # Başlık
        tk.Label(
            self.raporlar_frame, 
            text="Raporlar", 
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Tarih seçim alanı
        tarih_frame = tk.Frame(self.raporlar_frame)
        tarih_frame.pack(pady=10)
        
        tk.Label(tarih_frame, text="Başlangıç:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.baslangic_tarih = tk.Entry(tarih_frame, font=("Arial", 12), width=10)
        self.baslangic_tarih.pack(side=tk.LEFT, padx=5)
        self.baslangic_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        
        tk.Label(tarih_frame, text="Bitiş:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(10,0))
        self.bitis_tarih = tk.Entry(tarih_frame, font=("Arial", 12), width=10)
        self.bitis_tarih.pack(side=tk.LEFT)
        self.bitis_tarih.insert(0, datetime.now().strftime("%d.%m.%Y"))
        
        # Rapor butonları
        rapor_button_frame = tk.Frame(self.raporlar_frame)
        rapor_button_frame.pack(pady=10)
        
        tk.Button(
            rapor_button_frame, 
            text="Günlük Satış Raporu", 
            command=self.gunluk_satis_raporu,
            font=("Arial", 12),
            bg="#607D8B",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            rapor_button_frame, 
            text="Ürün Bazlı Rapor", 
            command=self.urun_bazli_rapor,
            font=("Arial", 12),
            bg="#795548",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            rapor_button_frame, 
            text="Kategori Bazlı Rapor", 
            command=self.kategori_bazli_rapor,
            font=("Arial", 12),
            bg="#9C27B0",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            rapor_button_frame, 
            text="Raporu Excel'e Aktar", 
            command=self.raporu_excele_aktar,
            font=("Arial", 12),
            bg="#009688",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        # Rapor görüntüleme alanı
        self.rapor_text = tk.Text(
            self.raporlar_frame, 
            height=20,
            font=("Arial", 12),
            state=tk.DISABLED
        )
        self.rapor_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Kaydırma çubuğu
        scrollbar = ttk.Scrollbar(self.rapor_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.rapor_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.rapor_text.yview)
    
    def load_data(self):
        """Verileri veritabanından yükler"""
        try:
            # UI güncellemeleri
            self.update_masa_listesi()
            self.update_urun_listesi()
            self.update_kategori_listesi()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Veri yüklenirken hata oluştu: {str(e)}")
    
    def update_masa_listesi(self):
        """Masa listesini veritabanından günceller"""
        self.cursor.execute("SELECT * FROM masalar ORDER BY ad")
        masalar = self.cursor.fetchall()
        
        for i, masa in enumerate(masalar):
            masa_adi = masa[1]
            durum = masa[2]
            
            # Masa butonunu güncelle
            if durum == "boş":
                self.masa_buttons[i].config(bg="#E1F5FE", fg="black")  # Açık mavi
            else:
                self.masa_buttons[i].config(bg="#FFCDD2", fg="black")  # Açık kırmızı
    
    def update_urun_listesi(self):
        """Ürün listesini veritabanından günceller"""
        self.urun_listbox.delete(0, tk.END)
        
        self.cursor.execute('''
            SELECT u.id, u.ad, u.fiyat, k.ad 
            FROM urunler u
            LEFT JOIN kategoriler k ON u.kategori_id = k.id
            ORDER BY u.ad
        ''')
        self.urunler = self.cursor.fetchall()
        
        for urun in self.urunler:
            kategori = urun[3] if urun[3] else "Kategorisiz"
            self.urun_listbox.insert(tk.END, f"{urun[1]} - {urun[2]:.2f} TL ({kategori})")
        
        # Kategori combobox'ını güncelle
        self.cursor.execute("SELECT ad FROM kategoriler ORDER BY ad")
        kategoriler = [k[0] for k in self.cursor.fetchall()]
        self.urun_kategori_combobox['values'] = kategoriler
        if kategoriler:
            self.urun_kategori_combobox.current(0)
    
    def update_kategori_listesi(self):
        """Kategori listesini veritabanından günceller"""
        self.kategori_listbox.delete(0, tk.END)
        
        self.cursor.execute("SELECT * FROM kategoriler ORDER BY ad")
        self.kategoriler = self.cursor.fetchall()
        
        for kategori in self.kategoriler:
            self.kategori_listbox.insert(tk.END, kategori[1])
    
    def masa_click(self, masa_adi):
        """Masa butonuna tıklandığında çalışır"""
        self.current_masa = masa_adi
        self.open_masa_islem_penceresi()
    
    def open_masa_islem_penceresi(self):
        """Masa işlemleri için yeni pencere açar"""
        self.masa_islem_win = tk.Toplevel(self.root)
        self.masa_islem_win.title(f"{self.current_masa} - İşlemler")
        self.masa_islem_win.geometry("800x600")
        
        # Notebook (sekmeler)
        self.notebook = ttk.Notebook(self.masa_islem_win)
        
        # Siparişler sekmesi
        self.siparisler_frame = tk.Frame(self.notebook)
        self.setup_siparisler_sekme()
        
        # Masa bilgileri sekmesi
        self.bilgiler_frame = tk.Frame(self.notebook)
        self.setup_bilgiler_sekme()
        
        # Geçmiş adisyonlar sekmesi
        self.gecmis_frame = tk.Frame(self.notebook)
        self.setup_gecmis_sekme()
        
        self.notebook.add(self.siparisler_frame, text="Siparişler")
        self.notebook.add(self.bilgiler_frame, text="Masa Bilgileri")
        self.notebook.add(self.gecmis_frame, text="Geçmiş Adisyonlar")
        self.notebook.pack(expand=True, fill="both")
        
        # Pencere kapatıldığında masa durumunu güncelle
        self.masa_islem_win.protocol("WM_DELETE_WINDOW", self.on_masa_islem_close)
    
    def setup_siparisler_sekme(self):
        """Siparişler sekmesini oluşturur"""
        # Sipariş listesi
        self.siparis_listbox = tk.Listbox(self.siparisler_frame, height=15, font=("Arial", 12))
        self.siparis_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Sipariş ekleme alanı
        siparis_ekle_frame = tk.Frame(self.siparisler_frame)
        siparis_ekle_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(siparis_ekle_frame, text="Ürün:", font=("Arial", 12)).pack(side=tk.LEFT)
        
        # Ürün combobox'ını veritabanından doldur
        self.cursor.execute("SELECT ad FROM urunler ORDER BY ad")
        urunler = [u[0] for u in self.cursor.fetchall()]
        
        self.urun_combobox = ttk.Combobox(siparis_ekle_frame, values=urunler, font=("Arial", 12))
        self.urun_combobox.pack(side=tk.LEFT, padx=5)
        
        tk.Label(siparis_ekle_frame, text="Adet:", font=("Arial", 12)).pack(side=tk.LEFT, padx=(10,0))
        
        self.adet_spinbox = tk.Spinbox(siparis_ekle_frame, from_=1, to=10, width=3, font=("Arial", 12))
        self.adet_spinbox.pack(side=tk.LEFT)
        
        # Butonlar
        button_frame = tk.Frame(self.siparisler_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            button_frame, 
            text="Sipariş Ekle", 
            command=self.siparis_ekle,
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Sipariş Sil", 
            command=self.siparis_sil,
            font=("Arial", 12),
            bg="#F44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Ara Ödeme Al", 
            command=self.ara_odeme_al,
            font=("Arial", 12),
            bg="#2196F3",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            button_frame, 
            text="Hesap Kapat", 
            command=self.hesap_kapat,
            font=("Arial", 12),
            bg="#FF9800",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        # Toplam bilgisi
        self.toplam_label = tk.Label(
            self.siparisler_frame, 
            text="Toplam: 0.00 TL",
            font=("Arial", 14, "bold")
        )
        self.toplam_label.pack(pady=10)
        
        # Siparişleri güncelle
        self.update_siparis_listesi()
    
    def setup_bilgiler_sekme(self):
        """Masa bilgileri sekmesini oluşturur"""
        info_frame = tk.Frame(self.bilgiler_frame)
        info_frame.pack(pady=20)
        
        tk.Label(
            info_frame, 
            text=f"{self.current_masa} Bilgileri",
            font=("Arial", 16, "bold")
        ).pack(pady=10)
        
        # Masa durumu
        durum_frame = tk.Frame(info_frame)
        durum_frame.pack(pady=5)
        
        tk.Label(durum_frame, text="Durum:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.durum_label = tk.Label(durum_frame, text="", font=("Arial", 12, "bold"))
        self.durum_label.pack(side=tk.LEFT)
        
        # Masa açılış zamanı
        zaman_frame = tk.Frame(info_frame)
        zaman_frame.pack(pady=5)
        
        tk.Label(zaman_frame, text="Açılış Zamanı:", font=("Arial", 12)).pack(side=tk.LEFT)
        self.zaman_label = tk.Label(zaman_frame, text="", font=("Arial", 12))
        self.zaman_label.pack(side=tk.LEFT)
        
        # Masa bilgilerini güncelle
        self.update_bilgiler_sekme()
    
    def setup_gecmis_sekme(self):
        """Geçmiş adisyonlar sekmesini oluşturur"""
        # Geçmiş adisyonlar listesi
        self.gecmis_listbox = tk.Listbox(self.gecmis_frame, height=15, font=("Arial", 12))
        self.gecmis_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Geçmiş adisyonları yükle
        self.update_gecmis_sekme()
    
    def update_siparis_listesi(self):
        """Sipariş listesini veritabanından günceller"""
        self.siparis_listbox.delete(0, tk.END)
        
        # Masa ID'sini al
        self.cursor.execute("SELECT id FROM masalar WHERE ad=?", (self.current_masa,))
        masa_result = self.cursor.fetchone()
        if not masa_result:
            return
            
        masa_id = masa_result[0]
        
        # Siparişleri getir
        self.cursor.execute('''
            SELECT s.id, u.ad, s.adet, s.fiyat 
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            WHERE s.masa_id=? AND s.tarih >= date('now', 'start of day')
            ORDER BY s.tarih
        ''', (masa_id,))
        siparisler = self.cursor.fetchall()
        
        toplam = 0.0
        for siparis in siparisler:
            urun_adi = siparis[1]
            adet = siparis[2]
            fiyat = siparis[3]
            ara_toplam = adet * fiyat
            toplam += ara_toplam
            
            self.siparis_listbox.insert(tk.END, f"{urun_adi} - {adet} x {fiyat:.2f} TL = {ara_toplam:.2f} TL")
        
        # Toplamı güncelle
        self.toplam_label.config(text=f"Toplam: {toplam:.2f} TL")
        
        # Masanın toplamını güncelle
        self.cursor.execute("UPDATE masalar SET toplam=? WHERE id=?", (toplam, masa_id))
        self.conn.commit()
    
    def update_bilgiler_sekme(self):
        """Masa bilgileri sekmesini günceller"""
        self.cursor.execute("SELECT durum, acilis_zamani FROM masalar WHERE ad=?", (self.current_masa,))
        masa = self.cursor.fetchone()
        
        if masa:
            durum = masa[0]
            acilis_zamani = masa[1]
            
            self.durum_label.config(text=durum.capitalize())
            
            if durum == "dolu":
                self.durum_label.config(fg="red")
                self.zaman_label.config(text=acilis_zamani if acilis_zamani else "")
            else:
                self.durum_label.config(fg="green")
                self.zaman_label.config(text="")
    
    def update_gecmis_sekme(self):
        """Geçmiş adisyonlar sekmesini günceller"""
        self.gecmis_listbox.delete(0, tk.END)
        
        # Masa ID'sini al
        self.cursor.execute("SELECT id FROM masalar WHERE ad=?", (self.current_masa,))
        masa_result = self.cursor.fetchone()
        if not masa_result:
            return
            
        masa_id = masa_result[0]
        
        # Geçmiş adisyonları getir
        self.cursor.execute('''
            SELECT tarih, tutar, tip 
            FROM gecmis_adisyonlar 
            WHERE masa_id=?
            ORDER BY tarih DESC
        ''', (masa_id,))
        gecmis = self.cursor.fetchall()
        
        for kayit in gecmis:
            tip = "Ara Ödeme" if kayit[2] == "ara_odeme" else "Tam Ödeme"
            self.gecmis_listbox.insert(tk.END, f"{kayit[0]} - {kayit[1]:.2f} TL ({tip})")
    
    def siparis_ekle(self):
        """Yeni sipariş ekler"""
        urun_adi = self.urun_combobox.get()
        adet = int(self.adet_spinbox.get())
        
        if not urun_adi:
            messagebox.showerror("Hata", "Lütfen bir ürün seçin!")
            return
        
        # Ürün bilgilerini al
        self.cursor.execute("SELECT id, fiyat FROM urunler WHERE ad=?", (urun_adi,))
        urun = self.cursor.fetchone()
        
        if not urun:
            messagebox.showerror("Hata", "Geçersiz ürün seçimi!")
            return
        
        urun_id, fiyat = urun
        
        # Masa bilgilerini al
        self.cursor.execute("SELECT id, durum FROM masalar WHERE ad=?", (self.current_masa,))
        masa = self.cursor.fetchone()
        masa_id, durum = masa
        
        # Siparişi ekle
        self.cursor.execute(
            "INSERT INTO siparisler (masa_id, urun_id, adet, fiyat, tarih) VALUES (?, ?, ?, ?, ?)",
            (masa_id, urun_id, adet, fiyat, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        
        # Masa durumunu güncelle (eğer boşsa dolu yap)
        if durum == "boş":
            self.cursor.execute(
                "UPDATE masalar SET durum=?, acilis_zamani=? WHERE id=?",
                ("dolu", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), masa_id)
            )
        
        self.conn.commit()
        
        # Listeleri güncelle
        self.update_siparis_listesi()
        self.update_bilgiler_sekme()
        self.update_masa_listesi()
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"{self.current_masa} - {urun_adi} eklendi")
    
    def siparis_sil(self):
        """Seçili siparişi siler"""
        selection = self.siparis_listbox.curselection()
        
        if not selection:
            messagebox.showerror("Hata", "Lütfen silmek istediğiniz siparişi seçin!")
            return
        
        index = selection[0]
        
        # Masa ID'sini al
        self.cursor.execute("SELECT id FROM masalar WHERE ad=?", (self.current_masa,))
        masa_result = self.cursor.fetchone()
        if not masa_result:
            return
            
        masa_id = masa_result[0]
        
        # Sipariş ID'sini al
        self.cursor.execute('''
            SELECT s.id 
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            WHERE s.masa_id=? AND s.tarih >= date('now', 'start of day')
            ORDER BY s.tarih
        ''', (masa_id,))
        siparisler = self.cursor.fetchall()
        
        if index >= len(siparisler):
            messagebox.showerror("Hata", "Geçersiz sipariş seçimi!")
            return
        
        siparis_id = siparisler[index][0]
        
        # Siparişi sil
        self.cursor.execute("DELETE FROM siparisler WHERE id=?", (siparis_id,))
        
        # Eğer sipariş kalmadıysa masayı boş yap
        self.cursor.execute('''
            SELECT COUNT(*) 
            FROM siparisler 
            WHERE masa_id=? AND tarih >= date('now', 'start of day')
        ''', (masa_id,))
        siparis_sayisi = self.cursor.fetchone()[0]
        
        if siparis_sayisi == 0:
            self.cursor.execute(
                "UPDATE masalar SET durum=?, acilis_zamani=NULL, toplam=0 WHERE id=?",
                ("boş", masa_id)
            )
        
        self.conn.commit()
        
        # Listeleri güncelle
        self.update_siparis_listesi()
        self.update_bilgiler_sekme()
        self.update_masa_listesi()
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"{self.current_masa} - sipariş silindi")
    
    def ara_odeme_al(self):
        """Ara ödeme alır ve siparişleri temizler"""
        # Masa bilgilerini al
        self.cursor.execute("SELECT id, toplam FROM masalar WHERE ad=?", (self.current_masa,))
        masa = self.cursor.fetchone()
        
        if not masa or masa[1] <= 0:
            messagebox.showerror("Hata", "Bu masada henüz sipariş yok!")
            return
        
        masa_id, toplam = masa
        
        # Ödeme alındı mesajı
        messagebox.showinfo("Ara Ödeme", f"Ara ödeme alındı: {toplam:.2f} TL")
        
        # Geçmişe ekle
        self.cursor.execute(
            "INSERT INTO gecmis_adisyonlar (masa_id, tutar, tarih, tip) VALUES (?, ?, ?, ?)",
            (masa_id, toplam, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ara_odeme")
        )
        
        # Siparişleri temizle (sadece bugünküleri)
        self.cursor.execute('''
            DELETE FROM siparisler 
            WHERE masa_id=? AND tarih >= date('now', 'start of day')
        ''', (masa_id,))
        
        # Masayı güncelle
        self.cursor.execute(
            "UPDATE masalar SET durum=?, acilis_zamani=NULL, toplam=0 WHERE id=?",
            ("boş", masa_id)
        )
        
        self.conn.commit()
        
        # UI'ı güncelle
        self.update_siparis_listesi()
        self.update_bilgiler_sekme()
        self.update_masa_listesi()
        self.update_gecmis_sekme()
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"{self.current_masa} - ara ödeme alındı")
    
    def hesap_kapat(self):
        """Masa hesabını kapatır"""
        # Masa bilgilerini al
        self.cursor.execute("SELECT id, toplam FROM masalar WHERE ad=?", (self.current_masa,))
        masa = self.cursor.fetchone()
        
        if not masa or masa[1] <= 0:
            messagebox.showerror("Hata", "Bu masada henüz sipariş yok!")
            return
        
        masa_id, toplam = masa
        
        # Ödeme alındı mesajı
        messagebox.showinfo("Hesap Kapat", f"Hesap kapatıldı: {toplam:.2f} TL")
        
        # Geçmişe ekle
        self.cursor.execute(
            "INSERT INTO gecmis_adisyonlar (masa_id, tutar, tarih, tip) VALUES (?, ?, ?, ?)",
            (masa_id, toplam, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "tam_odeme")
        )
        
        # Siparişleri temizle (sadece bugünküleri)
        self.cursor.execute('''
            DELETE FROM siparisler 
            WHERE masa_id=? AND tarih >= date('now', 'start of day')
        ''', (masa_id,))
        
        # Masayı güncelle
        self.cursor.execute(
            "UPDATE masalar SET durum=?, acilis_zamani=NULL, toplam=0 WHERE id=?",
            ("boş", masa_id)
        )
        
        self.conn.commit()
        
        # UI'ı güncelle
        self.update_siparis_listesi()
        self.update_bilgiler_sekme()
        self.update_masa_listesi()
        self.update_gecmis_sekme()
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"{self.current_masa} - hesap kapatıldı")
    
    def urun_ekle(self):
        """Yeni ürün ekler"""
        urun_adi = self.urun_adi_entry.get().strip()
        fiyat_str = self.urun_fiyat_entry.get().strip()
        kategori_adi = self.urun_kategori_combobox.get()
        
        if not urun_adi:
            messagebox.showerror("Hata", "Ürün adı boş olamaz!")
            return
        
        try:
            fiyat = float(fiyat_str)
            if fiyat <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir fiyat girin!")
            return
        
        # Kategori ID'sini al
        kategori_id = None
        if kategori_adi:
            self.cursor.execute("SELECT id FROM kategoriler WHERE ad=?", (kategori_adi,))
            kategori = self.cursor.fetchone()
            if kategori:
                kategori_id = kategori[0]
        
        # Ürünü ekle
        try:
            self.cursor.execute(
                "INSERT INTO urunler (ad, fiyat, kategori_id) VALUES (?, ?, ?)",
                (urun_adi, fiyat, kategori_id)
            )
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_urun_listesi()
            
            # Giriş alanlarını temizle
            self.urun_adi_entry.delete(0, tk.END)
            self.urun_fiyat_entry.delete(0, tk.END)
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Yeni ürün eklendi: {urun_adi}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu ürün adı zaten var!")
    
    def urun_sil(self):
        """Seçili ürünü siler"""
        selection = self.urun_listbox.curselection()
        
        if not selection:
            messagebox.showerror("Hata", "Lütfen silmek istediğiniz ürünü seçin!")
            return
        
        index = selection[0]
        urun_id = self.urunler[index][0]
        urun_adi = self.urunler[index][1]
        
        # Onay iste
        if not messagebox.askyesno("Onay", f"{urun_adi} ürününü silmek istediğinize emin misiniz?"):
            return
        
        # Ürünü sil
        try:
            self.cursor.execute("DELETE FROM urunler WHERE id=?", (urun_id,))
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_urun_listesi()
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Ürün silindi: {urun_adi}")
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Ürün silinirken hata oluştu: {str(e)}")
    
    def urun_guncelle(self):
        """Seçili ürünü günceller"""
        selection = self.urun_listbox.curselection()
        
        if not selection:
            messagebox.showerror("Hata", "Lütfen güncellemek istediğiniz ürünü seçin!")
            return
        
        index = selection[0]
        urun_id = self.urunler[index][0]
        eski_urun_adi = self.urunler[index][1]
        
        yeni_urun_adi = self.urun_adi_entry.get().strip()
        yeni_fiyat_str = self.urun_fiyat_entry.get().strip()
        yeni_kategori_adi = self.urun_kategori_combobox.get()
        
        if not yeni_urun_adi:
            messagebox.showerror("Hata", "Ürün adı boş olamaz!")
            return
        
        try:
            yeni_fiyat = float(yeni_fiyat_str)
            if yeni_fiyat <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçerli bir fiyat girin!")
            return
        
        # Kategori ID'sini al
        yeni_kategori_id = None
        if yeni_kategori_adi:
            self.cursor.execute("SELECT id FROM kategoriler WHERE ad=?", (yeni_kategori_adi,))
            kategori = self.cursor.fetchone()
            if kategori:
                yeni_kategori_id = kategori[0]
        
        # Ürünü güncelle
        try:
            self.cursor.execute(
                "UPDATE urunler SET ad=?, fiyat=?, kategori_id=? WHERE id=?",
                (yeni_urun_adi, yeni_fiyat, yeni_kategori_id, urun_id)
            )
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_urun_listesi()
            
            # Giriş alanlarını temizle
            self.urun_adi_entry.delete(0, tk.END)
            self.urun_fiyat_entry.delete(0, tk.END)
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Ürün güncellendi: {yeni_urun_adi}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu ürün adı zaten kullanılıyor!")
    
    def urun_icerik_aktar(self):
        """CSV dosyasından ürün listesini içe aktarır"""
        dosya_yolu = filedialog.askopenfilename(
            title="Ürün Listesi Dosyasını Seçin",
            filetypes=(("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*"))
        )
        
        if not dosya_yolu:
            return
        
        try:
            with open(dosya_yolu, mode='r', encoding='utf-8') as dosya:
                okuyucu = csv.reader(dosya)
                basarili = 0
                hatali = 0
                
                for satir in okuyucu:
                    if len(satir) >= 2:
                        urun_adi = satir[0].strip()
                        try:
                            fiyat = float(satir[1].strip())
                            
                            # Kategori varsa al
                            kategori_adi = satir[2].strip() if len(satir) > 2 else None
                            kategori_id = None
                            
                            if kategori_adi:
                                self.cursor.execute("SELECT id FROM kategoriler WHERE ad=?", (kategori_adi,))
                                kategori = self.cursor.fetchone()
                                if kategori:
                                    kategori_id = kategori[0]
                            
                            # Ürünü ekle
                            try:
                                self.cursor.execute(
                                    "INSERT INTO urunler (ad, fiyat, kategori_id) VALUES (?, ?, ?)",
                                    (urun_adi, fiyat, kategori_id)
                                )
                                basarili += 1
                            except sqlite3.IntegrityError:
                                hatali += 1
                        except ValueError:
                            hatali += 1
                
                self.conn.commit()
                self.update_urun_listesi()
                
                message = f"{basarili} ürün başarıyla eklendi!"
                if hatali > 0:
                    message += f"\n{hatali} satır hatalı veya tekrar eden ürünler atlandı."
                messagebox.showinfo("Sonuç", message)
                
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya okunurken hata oluştu: {str(e)}")
    
    def kategori_ekle(self):
        """Yeni kategori ekler"""
        kategori_adi = self.kategori_adi_entry.get().strip()
        
        if not kategori_adi:
            messagebox.showerror("Hata", "Kategori adı boş olamaz!")
            return
        
        try:
            self.cursor.execute(
                "INSERT INTO kategoriler (ad) VALUES (?)",
                (kategori_adi,)
            )
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_kategori_listesi()
            self.update_urun_listesi()  # Ürün listesindeki kategori combobox'ını güncelle
            
            # Giriş alanını temizle
            self.kategori_adi_entry.delete(0, tk.END)
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Yeni kategori eklendi: {kategori_adi}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu kategori adı zaten var!")
    
    def kategori_sil(self):
        """Seçili kategoriyi siler"""
        selection = self.kategori_listbox.curselection()
        
        if not selection:
            messagebox.showerror("Hata", "Lütfen silmek istediğiniz kategoriyi seçin!")
            return
        
        index = selection[0]
        kategori_id = self.kategoriler[index][0]
        kategori_adi = self.kategoriler[index][1]
        
        # Onay iste
        if not messagebox.askyesno("Onay", 
            f"{kategori_adi} kategorisini silmek istediğinize emin misiniz?\n"
            "Bu kategoriye ait ürünler 'Kategorisiz' olarak işaretlenecektir."):
            return
        
        try:
            # Önce bu kategorideki ürünleri güncelle
            self.cursor.execute(
                "UPDATE urunler SET kategori_id=NULL WHERE kategori_id=?",
                (kategori_id,)
            )
            
            # Sonra kategoriyi sil
            self.cursor.execute(
                "DELETE FROM kategoriler WHERE id=?",
                (kategori_id,)
            )
            
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_kategori_listesi()
            self.update_urun_listesi()
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Kategori silindi: {kategori_adi}")
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Kategori silinirken hata oluştu: {str(e)}")
    
    def kategori_guncelle(self):
        """Seçili kategoriyi günceller"""
        selection = self.kategori_listbox.curselection()
        
        if not selection:
            messagebox.showerror("Hata", "Lütfen güncellemek istediğiniz kategoriyi seçin!")
            return
        
        index = selection[0]
        kategori_id = self.kategoriler[index][0]
        eski_kategori_adi = self.kategoriler[index][1]
        
        yeni_kategori_adi = self.kategori_adi_entry.get().strip()
        
        if not yeni_kategori_adi:
            messagebox.showerror("Hata", "Kategori adı boş olamaz!")
            return
        
        try:
            self.cursor.execute(
                "UPDATE kategoriler SET ad=? WHERE id=?",
                (yeni_kategori_adi, kategori_id)
            )
            self.conn.commit()
            
            # Listeleri güncelle
            self.update_kategori_listesi()
            self.update_urun_listesi()
            
            # Giriş alanını temizle
            self.kategori_adi_entry.delete(0, tk.END)
            
            # Durum çubuğunu güncelle
            self.status_bar.config(text=f"Kategori güncellendi: {yeni_kategori_adi}")
        except sqlite3.IntegrityError:
            messagebox.showerror("Hata", "Bu kategori adı zaten kullanılıyor!")
    
    def gunluk_satis_raporu(self):
        """Günlük satış raporu oluşturur"""
        baslangic = self.baslangic_tarih.get()
        bitis = self.bitis_tarih.get()
        
        try:
            bas_tarih = datetime.strptime(baslangic, "%d.%m.%Y")
            bit_tarih = datetime.strptime(bitis, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı! (GG.AA.YYYY olmalı)")
            return
        
        # Tarih aralığındaki adisyonları filtrele
        self.cursor.execute('''
            SELECT g.tarih, g.tutar, g.tip, m.ad 
            FROM gecmis_adisyonlar g
            JOIN masalar m ON g.masa_id = m.id
            WHERE date(g.tarih) BETWEEN date(?) AND date(?)
            ORDER BY g.tarih
        ''', (bas_tarih.strftime("%Y-%m-%d"), bit_tarih.strftime("%Y-%m-%d")))
        
        filtreli_adisyonlar = self.cursor.fetchall()
        
        # Raporu oluştur
        toplam_tutar = sum(a[1] for a in filtreli_adisyonlar)
        masa_bazli = {}
        
        for adisyon in filtreli_adisyonlar:
            masa = adisyon[3]
            if masa not in masa_bazli:
                masa_bazli[masa] = 0.0
            masa_bazli[masa] += adisyon[1]
        
        # Rapor metni
        rapor_metni = f"SATIŞ RAPORU\n{baslangic} - {bitis}\n\n"
        rapor_metni += f"Toplam Satış: {toplam_tutar:.2f} TL\n"
        rapor_metni += f"Toplam İşlem: {len(filtreli_adisyonlar)}\n\n"
        
        rapor_metni += "Masa Bazlı Satışlar:\n"
        for masa, tutar in sorted(masa_bazli.items(), key=lambda x: x[1], reverse=True):
            rapor_metni += f"{masa}: {tutar:.2f} TL\n"
        
        # Raporu göster
        self.rapor_text.config(state=tk.NORMAL)
        self.rapor_text.delete(1.0, tk.END)
        self.rapor_text.insert(tk.END, rapor_metni)
        self.rapor_text.config(state=tk.DISABLED)
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Rapor oluşturuldu: {baslangic} - {bitis}")
    
    def urun_bazli_rapor(self):
        """Ürün bazlı satış raporu oluşturur"""
        baslangic = self.baslangic_tarih.get()
        bitis = self.bitis_tarih.get()
        
        try:
            bas_tarih = datetime.strptime(baslangic, "%d.%m.%Y")
            bit_tarih = datetime.strptime(bitis, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı! (GG.AA.YYYY olmalı)")
            return
        
        # Ürün bazlı satışları getir
        self.cursor.execute('''
            SELECT u.ad, SUM(s.adet), SUM(s.adet * s.fiyat)
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            WHERE date(s.tarih) BETWEEN date(?) AND date(?)
            GROUP BY u.ad
            ORDER BY SUM(s.adet * s.fiyat) DESC
        ''', (bas_tarih.strftime("%Y-%m-%d"), bit_tarih.strftime("%Y-%m-%d")))
        
        urun_satis = self.cursor.fetchall()
        
        # Rapor metni
        rapor_metni = f"ÜRÜN BAZLI SATIŞ RAPORU\n{baslangic} - {bitis}\n\n"
        rapor_metni += "Ürün | Satış Adeti | Toplam Tutar\n"
        rapor_metni += "-"*40 + "\n"
        
        for urun in urun_satis:
            rapor_metni += f"{urun[0].ljust(20)} {str(urun[1]).center(12)} {urun[2]:.2f} TL\n"
        
        # Raporu göster
        self.rapor_text.config(state=tk.NORMAL)
        self.rapor_text.delete(1.0, tk.END)
        self.rapor_text.insert(tk.END, rapor_metni)
        self.rapor_text.config(state=tk.DISABLED)
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Ürün bazlı rapor oluşturuldu")
    
    def kategori_bazli_rapor(self):
        """Kategori bazlı satış raporu oluşturur"""
        baslangic = self.baslangic_tarih.get()
        bitis = self.bitis_tarih.get()
        
        try:
            bas_tarih = datetime.strptime(baslangic, "%d.%m.%Y")
            bit_tarih = datetime.strptime(bitis, "%d.%m.%Y")
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz tarih formatı! (GG.AA.YYYY olmalı)")
            return
        
        # Kategori bazlı satışları getir
        self.cursor.execute('''
            SELECT COALESCE(k.ad, 'Kategorisiz'), SUM(s.adet), SUM(s.adet * s.fiyat)
            FROM siparisler s
            JOIN urunler u ON s.urun_id = u.id
            LEFT JOIN kategoriler k ON u.kategori_id = k.id
            WHERE date(s.tarih) BETWEEN date(?) AND date(?)
            GROUP BY COALESCE(k.ad, 'Kategorisiz')
            ORDER BY SUM(s.adet * s.fiyat) DESC
        ''', (bas_tarih.strftime("%Y-%m-%d"), bit_tarih.strftime("%Y-%m-%d")))
        
        kategori_satis = self.cursor.fetchall()
        
        # Rapor metni
        rapor_metni = f"KATEGORİ BAZLI SATIŞ RAPORU\n{baslangic} - {bitis}\n\n"
        rapor_metni += "Kategori | Satış Adeti | Toplam Tutar\n"
        rapor_metni += "-"*40 + "\n"
        
        for kategori in kategori_satis:
            rapor_metni += f"{kategori[0].ljust(20)} {str(kategori[1]).center(12)} {kategori[2]:.2f} TL\n"
        
        # Raporu göster
        self.rapor_text.config(state=tk.NORMAL)
        self.rapor_text.delete(1.0, tk.END)
        self.rapor_text.insert(tk.END, rapor_metni)
        self.rapor_text.config(state=tk.DISABLED)
        
        # Durum çubuğunu güncelle
        self.status_bar.config(text=f"Kategori bazlı rapor oluşturuldu")
    
    def raporu_excele_aktar(self):
        """Raporu Excel (CSV) dosyası olarak kaydeder"""
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=(("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*")),
            title="Raporu Kaydet"
        )
        
        if not dosya_yolu:
            return
        
        try:
            rapor_metni = self.rapor_text.get(1.0, tk.END)
            
            with open(dosya_yolu, 'w', encoding='utf-8') as dosya:
                for satir in rapor_metni.split('\n'):
                    dosya.write(satir + '\n')
            
            messagebox.showinfo("Başarılı", f"Rapor başarıyla kaydedildi:\n{dosya_yolu}")
        except Exception as e:
            messagebox.showerror("Hata", f"Rapor kaydedilirken hata oluştu: {str(e)}")
    
    def on_masa_islem_close(self):
        """Masa işlem penceresi kapatıldığında çalışır"""
        self.update_masa_listesi()
        self.masa_islem_win.destroy()
    
    def __del__(self):
        """Nesne yok edilirken veritabanı bağlantısını kapat"""
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = MasaSistemi(root)
    root.mainloop()
