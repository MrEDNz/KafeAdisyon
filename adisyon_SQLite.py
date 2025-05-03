import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime

class CafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Programı")
        self.root.geometry("1200x700")
        
        # Veritabanı bağlantısı
        self.conn = sqlite3.connect('kafe_adisyon.db')
        self.create_tables()
        self.insert_sample_data()
        
        # Arayüz
        self.create_ui()
        
        # Başlangıç verilerini yükle
        self.load_urunler()
        self.load_musteriler()
        self.load_masalar()
    
    def insert_sample_data(self):
        cursor = self.conn.cursor()
        
        # Masalar tablosuna örnek veriler ekle
        cursor.execute("SELECT COUNT(*) FROM masalar")
        if cursor.fetchone()[0] == 0:
            for i in range(1, 11):
                cursor.execute("INSERT INTO masalar (masa_adi, durum) VALUES (?, ?)", 
                              (f"Masa {i}", "bos"))
        
        # Müşteriler tablosuna örnek veriler ekle
        cursor.execute("SELECT COUNT(*) FROM musteriler")
        if cursor.fetchone()[0] == 0:
            sample_customers = [
                ("Ahmet Yılmaz", "5551234567", "ahmet@example.com"),
                ("Ayşe Kaya", "5557654321", "ayse@example.com"),
                ("Mehmet Demir", "5559876543", "mehmet@example.com")
            ]
            for customer in sample_customers:
                cursor.execute("INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi) VALUES (?, ?, ?, ?)",
                             (customer[0], customer[1], customer[2], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        # Ürünler tablosuna örnek veriler ekle
        cursor.execute("SELECT COUNT(*) FROM urunler")
        if cursor.fetchone()[0] == 0:
            sample_products = [
                ("Çay", 5.0, "Sıcak İçecek", 100),
                ("Kahve", 10.0, "Sıcak İçecek", 80),
                ("Su", 2.0, "Soğuk İçecek", 200),
                ("Kola", 8.0, "Soğuk İçecek", 150),
                ("Tost", 15.0, "Yiyecek", 50)
            ]
            for product in sample_products:
                cursor.execute("INSERT INTO urunler (urun_adi, fiyat, kategori, stok) VALUES (?, ?, ?, ?)",
                             (product[0], product[1], product[2], product[3]))
        
        self.conn.commit()

    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Masalar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS masalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_adi TEXT NOT NULL,
                durum TEXT NOT NULL DEFAULT 'bos',
                musteri_id INTEGER,
                acilis_zamani TEXT,
                kapanis_zamani TEXT,
                toplam_tutar REAL DEFAULT 0,
                FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
            )
        ''')
        
        # Müşteriler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS musteriler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT NOT NULL,
                telefon TEXT,
                eposta TEXT,
                kayit_tarihi TEXT
            )
        ''')
        
        # Ürünler tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS urunler (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun_adi TEXT NOT NULL,
                fiyat REAL NOT NULL,
                kategori TEXT,
                stok INTEGER DEFAULT 0
            )
        ''')
        
        # Adisyonlar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adisyonlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_id INTEGER NOT NULL,
                urun_id INTEGER NOT NULL,
                adet INTEGER NOT NULL,
                tarih TEXT NOT NULL,
                durum TEXT NOT NULL DEFAULT 'aktif',
                FOREIGN KEY (masa_id) REFERENCES masalar(id),
                FOREIGN KEY (urun_id) REFERENCES urunler(id)
            )
        ''')
        
        # Geçmiş adisyonlar tablosu
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gecmis_adisyonlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_id INTEGER NOT NULL,
                musteri_id INTEGER,
                acilis_zamani TEXT,
                kapanis_zamani TEXT,
                toplam_tutar REAL,
                adisyon_detay TEXT,
                FOREIGN KEY (masa_id) REFERENCES masalar(id),
                FOREIGN KEY (musteri_id) REFERENCES musteriler(id)
            )
        ''')
        
        self.conn.commit()
    
    def create_ui(self):
        # Notebook (Sekmeler)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        
        # Masalar Sekmesi
        self.masalar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.masalar_frame, text='Masalar')
        
        # Müşteriler Sekmesi
        self.musteriler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.musteriler_frame, text='Müşteriler')
        
        # Ürünler Sekmesi
        self.urunler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.urunler_frame, text='Ürünler')
        
        # Raporlar Sekmesi
        self.raporlar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raporlar_frame, text='Raporlar')
        
        # Masalar sekmesi içeriği
        self.create_masalar_ui()
        
        # Müşteriler sekmesi içeriği
        self.create_musteriler_ui()
        
        # Ürünler sekmesi içeriği
        self.create_urunler_ui()
        
        # Raporlar sekmesi içeriği
        self.create_raporlar_ui()
    
    def create_masalar_ui(self):
        # Ana frame
        main_frame = ttk.Frame(self.masalar_frame)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Sol Frame (Masa Listesi)
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side='left', fill='both', expand=True)
        
        # Masa işlemleri butonları
        masa_islem_frame = ttk.Frame(left_frame)
        masa_islem_frame.pack(fill='x', pady=5)
        
        ttk.Button(masa_islem_frame, text="Yeni Masa Ekle", command=self.yeni_masa_ekle).pack(side='left', padx=5)
        ttk.Button(masa_islem_frame, text="Masa Sil", command=self.masa_sil).pack(side='left', padx=5)
        
        ttk.Label(left_frame, text="Masalar", font=('Arial', 12, 'bold')).pack(pady=5)
        
        # Masa butonları için frame
        self.masalar_inner_frame = ttk.Frame(left_frame)
        self.masalar_inner_frame.pack(fill='both', expand=True)
        
        # Sağ Frame (Masa Detayları)
        right_frame = ttk.Frame(main_frame, width=400)
        right_frame.pack(side='right', fill='y')
        
        # Masa Detayları
        self.masa_detay_frame = ttk.LabelFrame(right_frame, text="Masa Detayları")
        self.masa_detay_frame.pack(fill='x', pady=5)
        
        ttk.Label(self.masa_detay_frame, text="Masa Adı:").grid(row=0, column=0, sticky='w', padx=5, pady=2)
        self.masa_adi_label = ttk.Label(self.masa_detay_frame, text="")
        self.masa_adi_label.grid(row=0, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.masa_detay_frame, text="Durum:").grid(row=1, column=0, sticky='w', padx=5, pady=2)
        self.masa_durum_label = ttk.Label(self.masa_detay_frame, text="")
        self.masa_durum_label.grid(row=1, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.masa_detay_frame, text="Müşteri:").grid(row=2, column=0, sticky='w', padx=5, pady=2)
        self.masa_musteri_label = ttk.Label(self.masa_detay_frame, text="")
        self.masa_musteri_label.grid(row=2, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.masa_detay_frame, text="Açılış Zamanı:").grid(row=3, column=0, sticky='w', padx=5, pady=2)
        self.masa_acilis_label = ttk.Label(self.masa_detay_frame, text="")
        self.masa_acilis_label.grid(row=3, column=1, sticky='w', padx=5, pady=2)
        
        ttk.Label(self.masa_detay_frame, text="Toplam Tutar:").grid(row=4, column=0, sticky='w', padx=5, pady=2)
        self.masa_tutar_label = ttk.Label(self.masa_detay_frame, text="")
        self.masa_tutar_label.grid(row=4, column=1, sticky='w', padx=5, pady=2)
        
        # Masa İşlemleri
        self.masa_islemleri_frame = ttk.LabelFrame(right_frame, text="Masa İşlemleri")
        self.masa_islemleri_frame.pack(fill='x', pady=5)
        
        self.masa_ac_button = ttk.Button(self.masa_islemleri_frame, text="Masa Aç", command=self.masa_ac_pencere)
        self.masa_ac_button.pack(fill='x', padx=5, pady=2)
        
        self.masa_kapat_button = ttk.Button(self.masa_islemleri_frame, text="Hesap Kapat", command=self.hesap_kapat_pencere)
        self.masa_kapat_button.pack(fill='x', padx=5, pady=2)
        
        # Başlangıçta masa işlemlerini devre dışı bırak
        self.masa_ac_button.config(state='disabled')
        self.masa_kapat_button.config(state='disabled')
    
    def load_masalar(self):
        # Önce mevcut butonları temizle
        for widget in self.masalar_inner_frame.winfo_children():
            widget.destroy()
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, masa_adi, durum FROM masalar ORDER BY id")
        masalar = cursor.fetchall()
        
        # 5 sütunlu bir grid oluştur
        for i, masa in enumerate(masalar):
            masa_id, masa_adi, durum = masa
            
            # Masa durumuna göre renk belirle
            if durum == 'dolu':
                bg_color = '#ffcccc'  # Kırmızı
            else:
                bg_color = '#ccffcc'  # Yeşil
            
            row = i // 5
            col = i % 5
            
            masa_btn = tk.Button(
                self.masalar_inner_frame,
                text=masa_adi,
                width=15,
                height=3,
                bg=bg_color,
                command=lambda id=masa_id: self.masa_sec(id)
            )
            masa_btn.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            # Grid hücrelerinin genişlemesini sağla
            self.masalar_inner_frame.grid_rowconfigure(row, weight=1)
            self.masalar_inner_frame.grid_columnconfigure(col, weight=1)
    
    def masa_sec(self, masa_id):
        self.secili_masa_id = masa_id
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT masa_adi, durum, musteri_id, acilis_zamani, toplam_tutar FROM masalar WHERE id=?", (masa_id,))
        masa = cursor.fetchone()
        
        if masa:
            masa_adi, durum, musteri_id, acilis_zamani, toplam_tutar = masa
            
            # Masa detaylarını göster
            self.masa_adi_label.config(text=masa_adi)
            self.masa_durum_label.config(text=durum.capitalize())
            self.masa_acilis_label.config(text=acilis_zamani if acilis_zamani else "-")
            self.masa_tutar_label.config(text=f"{toplam_tutar:.2f} TL" if toplam_tutar else "0.00 TL")
            
            # Müşteri bilgilerini yükle
            if musteri_id:
                cursor.execute("SELECT ad_soyad FROM musteriler WHERE id=?", (musteri_id,))
                musteri = cursor.fetchone()
                if musteri:
                    self.masa_musteri_label.config(text=musteri[0])
                else:
                    self.masa_musteri_label.config(text="-")
            else:
                self.masa_musteri_label.config(text="-")
            
            # Duruma göre butonları ayarla
            if durum == 'bos':
                self.masa_ac_button.config(state='normal')
                self.masa_kapat_button.config(state='disabled')
            else:
                self.masa_ac_button.config(state='disabled')
                self.masa_kapat_button.config(state='normal')
    
    def yeni_masa_ekle(self):
        self.masa_ekle_window = tk.Toplevel(self.root)
        self.masa_ekle_window.title("Yeni Masa Ekle")
        self.masa_ekle_window.geometry("300x150")
        
        ttk.Label(self.masa_ekle_window, text="Masa Adı:").pack(pady=5)
        self.yeni_masa_adi = ttk.Entry(self.masa_ekle_window)
        self.yeni_masa_adi.pack(fill='x', padx=10, pady=5)
        
        button_frame = ttk.Frame(self.masa_ekle_window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Button(button_frame, text="Ekle", command=self.masa_ekle_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.masa_ekle_window.destroy).pack(side='right', padx=5)
    
    def masa_ekle_kaydet(self):
        masa_adi = self.yeni_masa_adi.get().strip()
        if not masa_adi:
            messagebox.showerror("Hata", "Masa adı boş olamaz!")
            return
        
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO masalar (masa_adi) VALUES (?)", (masa_adi,))
        self.conn.commit()
        
        self.masa_ekle_window.destroy()
        self.load_masalar()
        messagebox.showinfo("Başarılı", "Masa başarıyla eklendi!")
    
    def masa_sil(self):
        if not hasattr(self, 'secili_masa_id'):
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz masayı seçin!")
            return
        
        masa_id = self.secili_masa_id
        cursor = self.conn.cursor()
        
        # Masa durumunu kontrol et
        cursor.execute("SELECT durum FROM masalar WHERE id=?", (masa_id,))
        durum = cursor.fetchone()[0]
        
        if durum == 'dolu':
            messagebox.showerror("Hata", "Dolu olan bir masa silinemez!")
            return
        
        # Masa adisyonlarını kontrol et
        cursor.execute("SELECT COUNT(*) FROM adisyonlar WHERE masa_id=? AND durum='aktif'", (masa_id,))
        if cursor.fetchone()[0] > 0:
            messagebox.showerror("Hata", "Bu masada aktif adisyonlar var. Önce adisyonları temizlemelisiniz!")
            return
        
        masa_adi = self.masa_adi_label.cget("text")
        if messagebox.askyesno("Onay", f"'{masa_adi}' adlı masayı silmek istediğinize emin misiniz?"):
            cursor.execute("DELETE FROM masalar WHERE id=?", (masa_id,))
            self.conn.commit()
            
            self.load_masalar()
            messagebox.showinfo("Başarılı", "Masa başarıyla silindi!")
    
    def masa_ac_pencere(self):
        if not hasattr(self, 'secili_masa_id'):
            messagebox.showwarning("Uyarı", "Lütfen bir masa seçin!")
            return
        
        self.masa_ac_window = tk.Toplevel(self.root)
        self.masa_ac_window.title("Masa Aç")
        self.masa_ac_window.geometry("400x300")
        
        # Müşteri Seçimi
        ttk.Label(self.masa_ac_window, text="Müşteri Seçin:").pack(pady=5)
        
        self.musteri_combobox_masa = ttk.Combobox(self.masa_ac_window, state='readonly')
        self.musteri_combobox_masa.pack(fill='x', padx=10, pady=5)
        
        # Müşterileri yükle
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, ad_soyad FROM musteriler ORDER BY ad_soyad")
        musteriler = cursor.fetchall()
        self.musteri_combobox_masa['values'] = [f"{id_} - {ad}" for id_, ad in musteriler]
        
        # Yeni Müşteri Butonu
        ttk.Button(self.masa_ac_window, text="Yeni Müşteri Ekle", command=self.yeni_musteri_ekle).pack(pady=5)
        
        # Masa Aç Butonu
        ttk.Button(self.masa_ac_window, text="Masayı Aç", command=self.masa_ac).pack(pady=10)
    
    def masa_ac(self):
        masa_id = self.secili_masa_id
        secili_musteri = self.musteri_combobox_masa.get()
        
        if not secili_musteri:
            messagebox.showwarning("Uyarı", "Lütfen bir müşteri seçin veya yeni müşteri ekleyin!")
            return
        
        musteri_id = int(secili_musteri.split(" - ")[0])
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE masalar SET durum='dolu', musteri_id=?, acilis_zamani=? WHERE id=?", 
                      (musteri_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), masa_id))
        self.conn.commit()
        
        self.masa_ac_window.destroy()
        self.load_masalar()
        self.masa_sec(masa_id)
        messagebox.showinfo("Başarılı", "Masa başarıyla açıldı!")
    
    def hesap_kapat_pencere(self):
        if not hasattr(self, 'secili_masa_id'):
            messagebox.showwarning("Uyarı", "Lütfen bir masa seçin!")
            return
        
        masa_id = self.secili_masa_id
        
        # Adisyon bilgilerini al
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.urun_adi, a.adet, u.fiyat, (a.adet * u.fiyat) as tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            WHERE a.masa_id=? AND a.durum='aktif'
        ''', (masa_id,))
        
        adisyonlar = cursor.fetchall()
        
        self.hesap_kapat_window = tk.Toplevel(self.root)
        self.hesap_kapat_window.title("Hesap Kapat")
        self.hesap_kapat_window.geometry("500x400")
        
        # Adisyon Listesi
        adisyon_frame = ttk.LabelFrame(self.hesap_kapat_window, text="Adisyon")
        adisyon_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('urun', 'adet', 'fiyat', 'tutar')
        self.adisyon_tree_hesap = ttk.Treeview(adisyon_frame, columns=columns, show='headings', height=10)
        
        self.adisyon_tree_hesap.heading('urun', text='Ürün')
        self.adisyon_tree_hesap.heading('adet', text='Adet')
        self.adisyon_tree_hesap.heading('fiyat', text='Birim Fiyat')
        self.adisyon_tree_hesap.heading('tutar', text='Tutar')
        
        self.adisyon_tree_hesap.column('urun', width=150)
        self.adisyon_tree_hesap.column('adet', width=50, anchor='center')
        self.adisyon_tree_hesap.column('fiyat', width=100, anchor='e')
        self.adisyon_tree_hesap.column('tutar', width=100, anchor='e')
        
        self.adisyon_tree_hesap.pack(fill='both', expand=True)
        
        # Toplam Tutar
        toplam_tutar = 0
        for urun_adi, adet, fiyat, tutar in adisyonlar:
            self.adisyon_tree_hesap.insert('', 'end', values=(urun_adi, adet, f"{fiyat:.2f}", f"{tutar:.2f}"))
            toplam_tutar += tutar
        
        toplam_frame = ttk.Frame(adisyon_frame)
        toplam_frame.pack(fill='x', pady=5)
        
        ttk.Label(toplam_frame, text="Toplam Tutar:", font=('Arial', 10, 'bold')).pack(side='left', padx=5)
        ttk.Label(toplam_frame, text=f"{toplam_tutar:.2f} TL", font=('Arial', 10, 'bold')).pack(side='right', padx=5)
        
        # Hesap Kapat Butonu
        ttk.Button(self.hesap_kapat_window, text="Hesabı Kapat", command=lambda: self.hesap_kapat(masa_id, toplam_tutar)).pack(pady=10)
    
    def hesap_kapat(self, masa_id, toplam_tutar):
        # Adisyon detaylarını al
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.urun_adi, a.adet, u.fiyat, (a.adet * u.fiyat) as tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            WHERE a.masa_id=? AND a.durum='aktif'
        ''', (masa_id,))
        
        adisyon_detay = ""
        for urun_adi, adet, fiyat, tutar in cursor.fetchall():
            adisyon_detay += f"{urun_adi} x {adet} = {tutar:.2f} TL\n"
        
        # Müşteri bilgilerini al
        cursor.execute("SELECT musteri_id FROM masalar WHERE id=?", (masa_id,))
        musteri_id = cursor.fetchone()[0]
        
        # Geçmiş adisyonlara kaydet
        cursor.execute('''
            INSERT INTO gecmis_adisyonlar 
            (masa_id, musteri_id, acilis_zamani, kapanis_zamani, toplam_tutar, adisyon_detay)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            masa_id,
            musteri_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            toplam_tutar,
            adisyon_detay
        ))
        
        # Adisyonları pasif yap
        cursor.execute("UPDATE adisyonlar SET durum='pasif' WHERE masa_id=?", (masa_id,))
        
        # Masayı boşalt
        cursor.execute("UPDATE masalar SET durum='bos', musteri_id=NULL, acilis_zamani=NULL, toplam_tutar=0 WHERE id=?", (masa_id,))
        
        self.conn.commit()
        
        self.hesap_kapat_window.destroy()
        self.load_masalar()
        self.masa_sec(masa_id)
        messagebox.showinfo("Başarılı", "Hesap başarıyla kapatıldı!")
    
    def yeni_musteri_ekle(self):
        self.musteri_ekle_window = tk.Toplevel(self.masa_ac_window)
        self.musteri_ekle_window.title("Yeni Müşteri Ekle")
        self.musteri_ekle_window.geometry("400x300")
        
        # Müşteri Bilgileri
        ttk.Label(self.musteri_ekle_window, text="Ad Soyad:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.musteri_ad_soyad = ttk.Entry(self.musteri_ekle_window)
        self.musteri_ad_soyad.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_ekle_window, text="Telefon:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.musteri_telefon = ttk.Entry(self.musteri_ekle_window)
        self.musteri_telefon.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_ekle_window, text="E-posta:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.musteri_eposta = ttk.Entry(self.musteri_ekle_window)
        self.musteri_eposta.grid(row=2, column=1, padx=5, pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(self.musteri_ekle_window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", command=self.musteri_ekle_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.musteri_ekle_window.destroy).pack(side='right', padx=5)
    
    def musteri_ekle_kaydet(self):
        ad_soyad = self.musteri_ad_soyad.get().strip()
        telefon = self.musteri_telefon.get().strip()
        eposta = self.musteri_eposta.get().strip()
        
        if not ad_soyad:
            messagebox.showerror("Hata", "Ad soyad alanı boş bırakılamaz!")
            return
        
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi)
            VALUES (?, ?, ?, ?)
        ''', (ad_soyad, telefon if telefon else None, eposta if eposta else None, 
             datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()
        
        # Müşteri combobox'ını güncelle
        cursor.execute("SELECT id, ad_soyad FROM musteriler ORDER BY ad_soyad")
        musteriler = cursor.fetchall()
        self.musteri_combobox_masa['values'] = [f"{id_} - {ad}" for id_, ad in musteriler]
        
        # Yeni eklenen müşteriyi seç
        yeni_musteri_id = cursor.lastrowid
        for i, (id_, ad) in enumerate(musteriler):
            if id_ == yeni_musteri_id:
                self.musteri_combobox_masa.current(i)
                break
        
        self.musteri_ekle_window.destroy()
        messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi!")
    
    def load_adisyon(self, masa_id):
        # Adisyonu temizle
        for item in self.adisyon_tree.get_children():
            self.adisyon_tree.delete(item)
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT a.id, u.urun_adi, a.adet, u.fiyat, (a.adet * u.fiyat) as tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            WHERE a.masa_id=? AND a.durum='aktif'
        ''', (masa_id,))
        
        toplam_tutar = 0
        for adisyon in cursor.fetchall():
            adisyon_id, urun_adi, adet, fiyat, tutar = adisyon
            self.adisyon_tree.insert('', 'end', values=(urun_adi, adet, f"{fiyat:.2f}", f"{tutar:.2f}"))
            toplam_tutar += tutar
        
        self.toplam_tutar_label.config(text=f"Toplam: {toplam_tutar:.2f} TL")
        
        # Masadaki toplam tutarı güncelle
        cursor.execute("UPDATE masalar SET toplam_tutar=? WHERE id=?", (toplam_tutar, masa_id))
        self.conn.commit()
    
    def load_masa_gecmis(self, masa_id):
        self.masa_gecmis_text.config(state='normal')
        self.masa_gecmis_text.delete('1.0', 'end')
        
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT acilis_zamani, kapanis_zamani, toplam_tutar, adisyon_detay
            FROM gecmis_adisyonlar
            WHERE masa_id=?
            ORDER BY kapanis_zamani DESC
            LIMIT 5
        ''', (masa_id,))
        
        for kayit in cursor.fetchall():
            acilis, kapanis, tutar, detay = kayit
            self.masa_gecmis_text.insert('end', f"Açılış: {acilis}\n")
            self.masa_gecmis_text.insert('end', f"Kapanış: {kapanis}\n")
            self.masa_gecmis_text.insert('end', f"Toplam: {tutar:.2f} TL\n")
            self.masa_gecmis_text.insert('end', "-"*30 + "\n")
        
        self.masa_gecmis_text.config(state='disabled')
    
    def masa_ac(self):
        masa_id = self.secili_masa_id
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE masalar SET durum='dolu', acilis_zamani=? WHERE id=?", 
                      (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), masa_id))
        self.conn.commit()
        
        self.load_masalar()
        self.masa_sec(masa_id)
    
    def hesap_kapat(self):
        masa_id = self.secili_masa_id
        
        # Önce masanın adisyon bilgilerini al
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT u.urun_adi, a.adet, u.fiyat, (a.adet * u.fiyat) as tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            WHERE a.masa_id=? AND a.durum='aktif'
        ''', (masa_id,))
        
        adisyon_detay = ""
        toplam_tutar = 0
        for urun_adi, adet, fiyat, tutar in cursor.fetchall():
            adisyon_detay += f"{urun_adi} x {adet} = {tutar:.2f} TL\n"
            toplam_tutar += tutar
        
        # Müşteri bilgilerini al
        cursor.execute("SELECT musteri_id FROM masalar WHERE id=?", (masa_id,))
        musteri_id = cursor.fetchone()[0]
        
        # Geçmiş adisyonlara kaydet
        cursor.execute('''
            INSERT INTO gecmis_adisyonlar 
            (masa_id, musteri_id, acilis_zamani, kapanis_zamani, toplam_tutar, adisyon_detay)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            masa_id,
            musteri_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            toplam_tutar,
            adisyon_detay
        ))
        
        # Adisyonları pasif yap
        cursor.execute("UPDATE adisyonlar SET durum='pasif' WHERE masa_id=?", (masa_id,))
        
        # Masayı boşalt
        cursor.execute("UPDATE masalar SET durum='bos', musteri_id=NULL, acilis_zamani=NULL, toplam_tutar=0 WHERE id=?", (masa_id,))
        
        self.conn.commit()
        
        self.load_masalar()
        self.masa_sec(masa_id)
    
    def musteri_ata(self):
        secili_musteri = self.musteri_combobox.get()
        if not secili_musteri:
            messagebox.showwarning("Uyarı", "Lütfen bir müşteri seçin!")
            return
        
        musteri_id = int(secili_musteri.split(" - ")[0])
        masa_id = self.secili_masa_id
        
        cursor = self.conn.cursor()
        cursor.execute("UPDATE masalar SET musteri_id=? WHERE id=?", (musteri_id, masa_id))
        self.conn.commit()
        
        self.masa_sec(masa_id)
    
    def urun_ekle(self):
        secili_urun = self.urun_combobox.get()
        if not secili_urun:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
            return
        
        try:
            adet = int(self.urun_adet_spinbox.get())
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz adet!")
            return
        
        if adet <= 0:
            messagebox.showerror("Hata", "Adet 0'dan büyük olmalıdır!")
            return
        
        urun_id = int(secili_urun.split(" - ")[0])
        masa_id = self.secili_masa_id
        
        cursor = self.conn.cursor()
        
        # Aynı ürün zaten eklenmiş mi kontrol et
        cursor.execute("SELECT id, adet FROM adisyonlar WHERE masa_id=? AND urun_id=? AND durum='aktif'", (masa_id, urun_id))
        existing = cursor.fetchone()
        
        if existing:
            # Var olan kaydı güncelle
            new_adet = existing[1] + adet
            cursor.execute("UPDATE adisyonlar SET adet=? WHERE id=?", (new_adet, existing[0]))
        else:
            # Yeni kayıt ekle
            cursor.execute('''
                INSERT INTO adisyonlar (masa_id, urun_id, adet, tarih)
                VALUES (?, ?, ?, ?)
            ''', (masa_id, urun_id, adet, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        
        self.conn.commit()
        
        # Adisyonu yenile
        self.load_adisyon(masa_id)
        
        # Ürün adedini sıfırla
        self.urun_adet_spinbox.set(1)
    
    def load_musteriler(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, ad_soyad FROM musteriler ORDER BY ad_soyad")
        musteriler = cursor.fetchall()
        
        # Müşteri combobox'ını güncelle
        self.musteri_combobox['values'] = [f"{id_} - {ad}" for id_, ad in musteriler]
        
        # Müşteri treeview'ını güncelle
        self.musteriler_tree.delete(*self.musteriler_tree.get_children())
        
        cursor.execute("SELECT id, ad_soyad, telefon, eposta, kayit_tarihi FROM musteriler ORDER BY ad_soyad")
        for musteri in cursor.fetchall():
            self.musteriler_tree.insert('', 'end', values=musteri)
    
    def load_urunler(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, urun_adi FROM urunler ORDER BY urun_adi")
        urunler = cursor.fetchall()
        
        # Ürün combobox'ını güncelle
        self.urun_combobox['values'] = [f"{id_} - {ad}" for id_, ad in urunler]
        
        # Ürün treeview'ını güncelle
        self.urunler_tree.delete(*self.urunler_tree.get_children())
        
        cursor.execute("SELECT id, urun_adi, fiyat, kategori, stok FROM urunler ORDER BY urun_adi")
        for urun in cursor.fetchall():
            self.urunler_tree.insert('', 'end', values=urun)
    
    def create_musteriler_ui(self):
        # Müşteri Listesi
        musteriler_list_frame = ttk.Frame(self.musteriler_frame)
        musteriler_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('id', 'ad_soyad', 'telefon', 'eposta', 'kayit_tarihi')
        self.musteriler_tree = ttk.Treeview(musteriler_list_frame, columns=columns, show='headings', height=15)
        
        self.musteriler_tree.heading('id', text='ID')
        self.musteriler_tree.heading('ad_soyad', text='Ad Soyad')
        self.musteriler_tree.heading('telefon', text='Telefon')
        self.musteriler_tree.heading('eposta', text='E-posta')
        self.musteriler_tree.heading('kayit_tarihi', text='Kayıt Tarihi')
        
        self.musteriler_tree.column('id', width=50, anchor='center')
        self.musteriler_tree.column('ad_soyad', width=150)
        self.musteriler_tree.column('telefon', width=120)
        self.musteriler_tree.column('eposta', width=150)
        self.musteriler_tree.column('kayit_tarihi', width=120)
        
        self.musteriler_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(musteriler_list_frame, orient='vertical', command=self.musteriler_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.musteriler_tree.configure(yscrollcommand=scrollbar.set)
        
        # Müşteri İşlemleri
        musteriler_islem_frame = ttk.Frame(self.musteriler_frame)
        musteriler_islem_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(musteriler_islem_frame, text="Yeni Müşteri", command=self.yeni_musteri).pack(side='left', padx=5)
        ttk.Button(musteriler_islem_frame, text="Müşteri Düzenle", command=self.musteri_duzenle).pack(side='left', padx=5)
        ttk.Button(musteriler_islem_frame, text="Müşteri Sil", command=self.musteri_sil).pack(side='left', padx=5)
    
    def yeni_musteri(self):
        self.musteri_duzenle_window = tk.Toplevel(self.root)
        self.musteri_duzenle_window.title("Yeni Müşteri")
        self.musteri_duzenle_window.geometry("400x300")
        
        # Müşteri Bilgileri
        ttk.Label(self.musteri_duzenle_window, text="Ad Soyad:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.musteri_ad_soyad_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_ad_soyad_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_duzenle_window, text="Telefon:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.musteri_telefon_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_telefon_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_duzenle_window, text="E-posta:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.musteri_eposta_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_eposta_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(self.musteri_duzenle_window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", command=self.musteri_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.musteri_duzenle_window.destroy).pack(side='left', padx=5)
        
        # Yeni müşteri modunda olduğumuzu belirtmek için
        self.musteri_duzenle_mode = "yeni"
        self.musteri_id = None
    
    def musteri_duzenle(self):
        selected = self.musteriler_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz müşteriyi seçin!")
            return
        
        item = self.musteriler_tree.item(selected[0])
        musteri_id = item['values'][0]
        
        self.musteri_duzenle_window = tk.Toplevel(self.root)
        self.musteri_duzenle_window.title("Müşteri Düzenle")
        self.musteri_duzenle_window.geometry("400x300")
        
        # Müşteri Bilgileri
        ttk.Label(self.musteri_duzenle_window, text="Ad Soyad:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.musteri_ad_soyad_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_ad_soyad_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_duzenle_window, text="Telefon:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.musteri_telefon_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_telefon_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.musteri_duzenle_window, text="E-posta:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.musteri_eposta_entry = ttk.Entry(self.musteri_duzenle_window, width=30)
        self.musteri_eposta_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(self.musteri_duzenle_window)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", command=self.musteri_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.musteri_duzenle_window.destroy).pack(side='left', padx=5)
        
        # Verileri yükle
        cursor = self.conn.cursor()
        cursor.execute("SELECT ad_soyad, telefon, eposta FROM musteriler WHERE id=?", (musteri_id,))
        musteri = cursor.fetchone()
        
        if musteri:
            self.musteri_ad_soyad_entry.insert(0, musteri[0])
            self.musteri_telefon_entry.insert(0, musteri[1] if musteri[1] else "")
            self.musteri_eposta_entry.insert(0, musteri[2] if musteri[2] else "")
        
        # Düzenleme modunda olduğumuzu belirtmek için
        self.musteri_duzenle_mode = "duzenle"
        self.musteri_id = musteri_id
    
    def musteri_kaydet(self):
        ad_soyad = self.musteri_ad_soyad_entry.get().strip()
        telefon = self.musteri_telefon_entry.get().strip()
        eposta = self.musteri_eposta_entry.get().strip()
        
        if not ad_soyad:
            messagebox.showerror("Hata", "Ad soyad alanı boş bırakılamaz!")
            return
        
        cursor = self.conn.cursor()
        
        if self.musteri_duzenle_mode == "yeni":
            # Yeni müşteri ekle
            cursor.execute('''
                INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi)
                VALUES (?, ?, ?, ?)
            ''', (ad_soyad, telefon if telefon else None, eposta if eposta else None, 
                 datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        else:
            # Müşteri güncelle
            cursor.execute('''
                UPDATE musteriler 
                SET ad_soyad=?, telefon=?, eposta=?
                WHERE id=?
            ''', (ad_soyad, telefon if telefon else None, eposta if eposta else None, self.musteri_id))
        
        self.conn.commit()
        
        # Müşteri listesini yenile
        self.load_musteriler()
        
        # Pencereyi kapat
        self.musteri_duzenle_window.destroy()
        
        messagebox.showinfo("Başarılı", "Müşteri bilgileri kaydedildi!")
    
    def musteri_sil(self):
        selected = self.musteriler_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz müşteriyi seçin!")
            return
        
        item = self.musteriler_tree.item(selected[0])
        musteri_id = item['values'][0]
        ad_soyad = item['values'][1]
        
        # Müşterinin masalarda kullanılıp kullanılmadığını kontrol et
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM masalar WHERE musteri_id=?", (musteri_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showerror("Hata", "Bu müşteri bir masada kullanılıyor. Önce müşteriyi masalardan çıkarmalısınız!")
            return
        
        if messagebox.askyesno("Onay", f"'{ad_soyad}' adlı müşteriyi silmek istediğinize emin misiniz?"):
            cursor.execute("DELETE FROM musteriler WHERE id=?", (musteri_id,))
            self.conn.commit()
            
            self.load_musteriler()
            messagebox.showinfo("Başarılı", "Müşteri silindi!")
    
    def create_urunler_ui(self):
        # Ürün Listesi
        urunler_list_frame = ttk.Frame(self.urunler_frame)
        urunler_list_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        columns = ('id', 'urun_adi', 'fiyat', 'kategori', 'stok')
        self.urunler_tree = ttk.Treeview(urunler_list_frame, columns=columns, show='headings', height=15)
        
        self.urunler_tree.heading('id', text='ID')
        self.urunler_tree.heading('urun_adi', text='Ürün Adı')
        self.urunler_tree.heading('fiyat', text='Fiyat')
        self.urunler_tree.heading('kategori', text='Kategori')
        self.urunler_tree.heading('stok', text='Stok')
        
        self.urunler_tree.column('id', width=50, anchor='center')
        self.urunler_tree.column('urun_adi', width=200)
        self.urunler_tree.column('fiyat', width=100, anchor='e')
        self.urunler_tree.column('kategori', width=100)
        self.urunler_tree.column('stok', width=80, anchor='center')
        
        self.urunler_tree.pack(side='left', fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(urunler_list_frame, orient='vertical', command=self.urunler_tree.yview)
        scrollbar.pack(side='right', fill='y')
        self.urunler_tree.configure(yscrollcommand=scrollbar.set)
        
        # Ürün İşlemleri
        urunler_islem_frame = ttk.Frame(self.urunler_frame)
        urunler_islem_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(urunler_islem_frame, text="Yeni Ürün", command=self.yeni_urun).pack(side='left', padx=5)
        ttk.Button(urunler_islem_frame, text="Ürün Düzenle", command=self.urun_duzenle).pack(side='left', padx=5)
        ttk.Button(urunler_islem_frame, text="Ürün Sil", command=self.urun_sil).pack(side='left', padx=5)
    
    def yeni_urun(self):
        self.urun_duzenle_window = tk.Toplevel(self.root)
        self.urun_duzenle_window.title("Yeni Ürün")
        self.urun_duzenle_window.geometry("400x300")
        
        # Ürün Bilgileri
        ttk.Label(self.urun_duzenle_window, text="Ürün Adı:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.urun_adi_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Fiyat:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.urun_fiyat_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_fiyat_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Kategori:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.urun_kategori_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_kategori_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Stok:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.urun_stok_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_stok_entry.grid(row=3, column=1, padx=5, pady=5)
        self.urun_stok_entry.insert(0, "0")
        
        # Butonlar
        button_frame = ttk.Frame(self.urun_duzenle_window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", command=self.urun_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.urun_duzenle_window.destroy).pack(side='left', padx=5)
        
        # Yeni ürün modunda olduğumuzu belirtmek için
        self.urun_duzenle_mode = "yeni"
        self.urun_id = None
    
    def urun_duzenle(self):
        selected = self.urunler_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz ürünü seçin!")
            return
        
        item = self.urunler_tree.item(selected[0])
        urun_id = item['values'][0]
        
        self.urun_duzenle_window = tk.Toplevel(self.root)
        self.urun_duzenle_window.title("Ürün Düzenle")
        self.urun_duzenle_window.geometry("400x300")
        
        # Ürün Bilgileri
        ttk.Label(self.urun_duzenle_window, text="Ürün Adı:").grid(row=0, column=0, padx=5, pady=5, sticky='e')
        self.urun_adi_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Fiyat:").grid(row=1, column=0, padx=5, pady=5, sticky='e')
        self.urun_fiyat_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_fiyat_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Kategori:").grid(row=2, column=0, padx=5, pady=5, sticky='e')
        self.urun_kategori_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_kategori_entry.grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(self.urun_duzenle_window, text="Stok:").grid(row=3, column=0, padx=5, pady=5, sticky='e')
        self.urun_stok_entry = ttk.Entry(self.urun_duzenle_window, width=30)
        self.urun_stok_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Butonlar
        button_frame = ttk.Frame(self.urun_duzenle_window)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        ttk.Button(button_frame, text="Kaydet", command=self.urun_kaydet).pack(side='left', padx=5)
        ttk.Button(button_frame, text="İptal", command=self.urun_duzenle_window.destroy).pack(side='left', padx=5)
        
        # Verileri yükle
        cursor = self.conn.cursor()
        cursor.execute("SELECT urun_adi, fiyat, kategori, stok FROM urunler WHERE id=?", (urun_id,))
        urun = cursor.fetchone()
        
        if urun:
            self.urun_adi_entry.insert(0, urun[0])
            self.urun_fiyat_entry.insert(0, str(urun[1]))
            self.urun_kategori_entry.insert(0, urun[2] if urun[2] else "")
            self.urun_stok_entry.insert(0, str(urun[3]))
        
        # Düzenleme modunda olduğumuzu belirtmek için
        self.urun_duzenle_mode = "duzenle"
        self.urun_id = urun_id
    
    def urun_kaydet(self):
        urun_adi = self.urun_adi_entry.get().strip()
        fiyat = self.urun_fiyat_entry.get().strip()
        kategori = self.urun_kategori_entry.get().strip()
        stok = self.urun_stok_entry.get().strip()
        
        if not urun_adi:
            messagebox.showerror("Hata", "Ürün adı alanı boş bırakılamaz!")
            return
        
        try:
            fiyat = float(fiyat)
            if fiyat <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat değeri!")
            return
        
        try:
            stok = int(stok)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz stok değeri!")
            return
        
        cursor = self.conn.cursor()
        
        if self.urun_duzenle_mode == "yeni":
            # Yeni ürün ekle
            cursor.execute('''
                INSERT INTO urunler (urun_adi, fiyat, kategori, stok)
                VALUES (?, ?, ?, ?)
            ''', (urun_adi, fiyat, kategori if kategori else None, stok))
        else:
            # Ürün güncelle
            cursor.execute('''
                UPDATE urunler 
                SET urun_adi=?, fiyat=?, kategori=?, stok=?
                WHERE id=?
            ''', (urun_adi, fiyat, kategori if kategori else None, stok, self.urun_id))
        
        self.conn.commit()
        
        # Ürün listesini yenile
        self.load_urunler()
        
        # Pencereyi kapat
        self.urun_duzenle_window.destroy()
        
        messagebox.showinfo("Başarılı", "Ürün bilgileri kaydedildi!")
    
    def urun_sil(self):
        selected = self.urunler_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz ürünü seçin!")
            return
        
        item = self.urunler_tree.item(selected[0])
        urun_id = item['values'][0]
        urun_adi = item['values'][1]
        
        # Ürünün adisyonlarda kullanılıp kullanılmadığını kontrol et
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM adisyonlar WHERE urun_id=?", (urun_id,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showerror("Hata", "Bu ürün adisyonlarda kullanılıyor. Önce ürünü adisyonlardan çıkarmalısınız!")
            return
        
        if messagebox.askyesno("Onay", f"'{urun_adi}' adlı ürünü silmek istediğinize emin misiniz?"):
            cursor.execute("DELETE FROM urunler WHERE id=?", (urun_id,))
            self.conn.commit()
            
            self.load_urunler()
            messagebox.showinfo("Başarılı", "Ürün silindi!")
    
    def create_raporlar_ui(self):
        # Rapor Seçenekleri
        rapor_secim_frame = ttk.LabelFrame(self.raporlar_frame, text="Rapor Seçenekleri")
        rapor_secim_frame.pack(fill='x', padx=10, pady=10)
        
        ttk.Label(rapor_secim_frame, text="Rapor Türü:").grid(row=0, column=0, padx=5, pady=5, sticky='w')
        self.rapor_turu = tk.StringVar()
        self.rapor_turu.set("gunluk")
        
        ttk.Radiobutton(rapor_secim_frame, text="Günlük Rapor", variable=self.rapor_turu, value="gunluk").grid(row=0, column=1, padx=5, pady=5, sticky='w')
        ttk.Radiobutton(rapor_secim_frame, text="Tarih Aralığı Raporu", variable=self.rapor_turu, value="tarih_araligi").grid(row=0, column=2, padx=5, pady=5, sticky='w')
        
        # Tarih Seçimi
        self.tarih_secim_frame = ttk.Frame(rapor_secim_frame)
        self.tarih_secim_frame.grid(row=1, column=0, columnspan=3, padx=5, pady=5, sticky='we')
        
        ttk.Label(self.tarih_secim_frame, text="Tarih:").pack(side='left', padx=5)
        self.rapor_tarih = ttk.Entry(self.tarih_secim_frame, width=12)
        self.rapor_tarih.pack(side='left', padx=5)
        self.rapor_tarih.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(self.tarih_secim_frame, text="Başlangıç Tarihi:").pack(side='left', padx=5)
        self.baslangic_tarih = ttk.Entry(self.tarih_secim_frame, width=12)
        self.baslangic_tarih.pack(side='left', padx=5)
        self.baslangic_tarih.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        ttk.Label(self.tarih_secim_frame, text="Bitiş Tarihi:").pack(side='left', padx=5)
        self.bitis_tarih = ttk.Entry(self.tarih_secim_frame, width=12)
        self.bitis_tarih.pack(side='left', padx=5)
        self.bitis_tarih.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # Rapor Butonları
        rapor_buton_frame = ttk.Frame(rapor_secim_frame)
        rapor_buton_frame.grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        
        ttk.Button(rapor_buton_frame, text="Rapor Oluştur", command=self.rapor_olustur).pack(side='left', padx=5)
        ttk.Button(rapor_buton_frame, text="Raporu Kaydet", command=self.rapor_kaydet).pack(side='left', padx=5)
        
        # Rapor Görüntüleme
        rapor_goruntule_frame = ttk.LabelFrame(self.raporlar_frame, text="Rapor")
        rapor_goruntule_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.rapor_text = tk.Text(rapor_goruntule_frame, wrap='word', state='disabled')
        self.rapor_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Başlangıçta tarih aralığı alanlarını gizle
        self.baslangic_tarih.pack_forget()
        self.bitis_tarih.pack_forget()
        ttk.Label(self.tarih_secim_frame, text="Başlangıç Tarihi:").pack_forget()
        ttk.Label(self.tarih_secim_frame, text="Bitiş Tarihi:").pack_forget()
        
        # Rapor türü değiştiğinde arayüzü güncelle
        self.rapor_turu.trace('w', self.update_rapor_arayuz)
    
    def update_rapor_arayuz(self, *args):
        if self.rapor_turu.get() == "gunluk":
            self.rapor_tarih.pack(side='left', padx=5)
            ttk.Label(self.tarih_secim_frame, text="Tarih:").pack(side='left', padx=5)
            
            self.baslangic_tarih.pack_forget()
            self.bitis_tarih.pack_forget()
            ttk.Label(self.tarih_secim_frame, text="Başlangıç Tarihi:").pack_forget()
            ttk.Label(self.tarih_secim_frame, text="Bitiş Tarihi:").pack_forget()
        else:
            self.rapor_tarih.pack_forget()
            ttk.Label(self.tarih_secim_frame, text="Tarih:").pack_forget()
            
            self.baslangic_tarih.pack(side='left', padx=5)
            self.bitis_tarih.pack(side='left', padx=5)
            ttk.Label(self.tarih_secim_frame, text="Başlangıç Tarihi:").pack(side='left', padx=5)
            ttk.Label(self.tarih_secim_frame, text="Bitiş Tarihi:").pack(side='left', padx=5)
    
    def rapor_olustur(self):
        rapor_turu = self.rapor_turu.get()
        
        if rapor_turu == "gunluk":
            tarih = self.rapor_tarih.get()
            try:
                datetime.strptime(tarih, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tarih formatı! Lütfen YYYY-AA-GG formatında girin.")
                return
            
            self.gunluk_rapor_olustur(tarih)
        else:
            baslangic = self.baslangic_tarih.get()
            bitis = self.bitis_tarih.get()
            
            try:
                datetime.strptime(baslangic, "%Y-%m-%d")
                datetime.strptime(bitis, "%Y-%m-%d")
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tarih formatı! Lütfen YYYY-AA-GG formatında girin.")
                return
            
            if baslangic > bitis:
                messagebox.showerror("Hata", "Başlangıç tarihi bitiş tarihinden büyük olamaz!")
                return
            
            self.tarih_araligi_rapor_olustur(baslangic, bitis)
    
    def gunluk_rapor_olustur(self, tarih):
        cursor = self.conn.cursor()
        
        # Toplam satış bilgileri
        cursor.execute('''
            SELECT COUNT(*) as masa_sayisi, 
                   SUM(toplam_tutar) as toplam_ciro,
                   AVG(toplam_tutar) as ortalama_ciro
            FROM gecmis_adisyonlar
            WHERE DATE(kapanis_zamani) = ?
        ''', (tarih,))
        
        rapor_istatistik = cursor.fetchone()
        masa_sayisi, toplam_ciro, ortalama_ciro = rapor_istatistik
        
        # Masa bazlı satışlar
        cursor.execute('''
            SELECT masa_id, COUNT(*) as islem_sayisi, 
                   SUM(toplam_tutar) as toplam_tutar
            FROM gecmis_adisyonlar
            WHERE DATE(kapanis_zamani) = ?
            GROUP BY masa_id
            ORDER BY toplam_tutar DESC
        ''', (tarih,))
        
        masa_bazli_satislar = cursor.fetchall()
        
        # Ürün bazlı satışlar
        cursor.execute('''
            SELECT u.urun_adi, SUM(a.adet) as toplam_adet, 
                   SUM(a.adet * u.fiyat) as toplam_tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            JOIN gecmis_adisyonlar g ON a.masa_id = g.masa_id
            WHERE DATE(g.kapanis_zamani) = ? AND a.durum='pasif'
            GROUP BY u.urun_adi
            ORDER BY toplam_tutar DESC
        ''', (tarih,))
        
        urun_bazli_satislar = cursor.fetchall()
        
        # Raporu oluştur
        rapor_metni = f"GÜNLÜK RAPOR - {tarih}\n"
        rapor_metni += "="*50 + "\n\n"
        
        rapor_metni += f"Toplam Masa Sayısı: {masa_sayisi if masa_sayisi else 0}\n"
        rapor_metni += f"Toplam Ciro: {toplam_ciro:.2f} TL\n" if toplam_ciro else "Toplam Ciro: 0.00 TL\n"
        rapor_metni += f"Ortalama Masa Cirosu: {ortalama_ciro:.2f} TL\n\n" if ortalama_ciro else "Ortalama Masa Cirosu: 0.00 TL\n\n"
        
        rapor_metni += "Masa Bazlı Satışlar:\n"
        rapor_metni += "-"*50 + "\n"
        for masa in masa_bazli_satislar:
            masa_id, islem_sayisi, toplam_tutar = masa
            rapor_metni += f"Masa {masa_id}: {islem_sayisi} işlem, Toplam: {toplam_tutar:.2f} TL\n"
        
        rapor_metni += "\nÜrün Bazlı Satışlar:\n"
        rapor_metni += "-"*50 + "\n"
        for urun in urun_bazli_satislar:
            urun_adi, toplam_adet, toplam_tutar = urun
            rapor_metni += f"{urun_adi}: {toplam_adet} adet, Toplam: {toplam_tutar:.2f} TL\n"
        
        # Raporu göster
        self.rapor_text.config(state='normal')
        self.rapor_text.delete('1.0', 'end')
        self.rapor_text.insert('end', rapor_metni)
        self.rapor_text.config(state='disabled')
    
    def tarih_araligi_rapor_olustur(self, baslangic, bitis):
        cursor = self.conn.cursor()
        
        # Toplam satış bilgileri
        cursor.execute('''
            SELECT COUNT(*) as masa_sayisi, 
                   SUM(toplam_tutar) as toplam_ciro,
                   AVG(toplam_tutar) as ortalama_ciro
            FROM gecmis_adisyonlar
            WHERE DATE(kapanis_zamani) BETWEEN ? AND ?
        ''', (baslangic, bitis))
        
        rapor_istatistik = cursor.fetchone()
        masa_sayisi, toplam_ciro, ortalama_ciro = rapor_istatistik
        
        # Günlük ciro
        cursor.execute('''
            SELECT DATE(kapanis_zamani) as tarih, 
                   COUNT(*) as islem_sayisi,
                   SUM(toplam_tutar) as gunluk_ciro
            FROM gecmis_adisyonlar
            WHERE DATE(kapanis_zamani) BETWEEN ? AND ?
            GROUP BY DATE(kapanis_zamani)
            ORDER BY DATE(kapanis_zamani)
        ''', (baslangic, bitis))
        
        gunluk_cirolar = cursor.fetchall()
        
        # Masa bazlı satışlar
        cursor.execute('''
            SELECT masa_id, COUNT(*) as islem_sayisi, 
                   SUM(toplam_tutar) as toplam_tutar
            FROM gecmis_adisyonlar
            WHERE DATE(kapanis_zamani) BETWEEN ? AND ?
            GROUP BY masa_id
            ORDER BY toplam_tutar DESC
        ''', (baslangic, bitis))
        
        masa_bazli_satislar = cursor.fetchall()
        
        # Ürün bazlı satışlar
        cursor.execute('''
            SELECT u.urun_adi, SUM(a.adet) as toplam_adet, 
                   SUM(a.adet * u.fiyat) as toplam_tutar
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            JOIN gecmis_adisyonlar g ON a.masa_id = g.masa_id
            WHERE DATE(g.kapanis_zamani) BETWEEN ? AND ? AND a.durum='pasif'
            GROUP BY u.urun_adi
            ORDER BY toplam_tutar DESC
        ''', (baslangic, bitis))
        
        urun_bazli_satislar = cursor.fetchall()
        
        # Raporu oluştur
        rapor_metni = f"TARİH ARALIĞI RAPORU - {baslangic} / {bitis}\n"
        rapor_metni += "="*50 + "\n\n"
        
        rapor_metni += f"Toplam Masa Sayısı: {masa_sayisi if masa_sayisi else 0}\n"
        rapor_metni += f"Toplam Ciro: {toplam_ciro:.2f} TL\n" if toplam_ciro else "Toplam Ciro: 0.00 TL\n"
        rapor_metni += f"Ortalama Masa Cirosu: {ortalama_ciro:.2f} TL\n\n" if ortalama_ciro else "Ortalama Masa Cirosu: 0.00 TL\n\n"
        
        rapor_metni += "Günlük Ciro:\n"
        rapor_metni += "-"*50 + "\n"
        for gun in gunluk_cirolar:
            tarih, islem_sayisi, gunluk_ciro = gun
            rapor_metni += f"{tarih}: {islem_sayisi} işlem, Toplam: {gunluk_ciro:.2f} TL\n"
        
        rapor_metni += "\nMasa Bazlı Satışlar:\n"
        rapor_metni += "-"*50 + "\n"
        for masa in masa_bazli_satislar:
            masa_id, islem_sayisi, toplam_tutar = masa
            rapor_metni += f"Masa {masa_id}: {islem_sayisi} işlem, Toplam: {toplam_tutar:.2f} TL\n"
        
        rapor_metni += "\nÜrün Bazlı Satışlar:\n"
        rapor_metni += "-"*50 + "\n"
        for urun in urun_bazli_satislar:
            urun_adi, toplam_adet, toplam_tutar = urun
            rapor_metni += f"{urun_adi}: {toplam_adet} adet, Toplam: {toplam_tutar:.2f} TL\n"
        
        # Raporu göster
        self.rapor_text.config(state='normal')
        self.rapor_text.delete('1.0', 'end')
        self.rapor_text.insert('end', rapor_metni)
        self.rapor_text.config(state='disabled')
    
    def rapor_kaydet(self):
        rapor_metni = self.rapor_text.get("1.0", "end-1c")
        if not rapor_metni.strip():
            messagebox.showwarning("Uyarı", "Kaydedilecek rapor bulunamadı!")
            return
        
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Dosyası", "*.txt"), ("Tüm Dosyalar", "*.*")],
            title="Raporu Kaydet"
        )
        
        if dosya_yolu:
            try:
                with open(dosya_yolu, 'w', encoding='utf-8') as dosya:
                    dosya.write(rapor_metni)
                messagebox.showinfo("Başarılı", "Rapor başarıyla kaydedildi!")
            except Exception as e:
                messagebox.showerror("Hata", f"Rapor kaydedilirken hata oluştu:\n{str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CafeAdisyonProgrami(root)
    root.mainloop()
