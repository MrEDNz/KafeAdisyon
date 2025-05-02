import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
from datetime import datetime, timedelta
import os
import csv

class KafeAdisyonProgrami:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Programı")
        self.root.state('zoomed')  # Tam ekran başlat
        
        # Veritabanı bağlantısı ve tablo oluşturma
        self.baglanti = sqlite3.connect("kafe.db")
        self.cursor = self.baglanti.cursor()
        
        self.tablari_olustur()
        
        # Arayüz oluşturma
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Masalar sekmesi
        self.masalar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.masalar_frame, text="Masalar")
        
        # Masalar için Canvas ve Scrollbar
        self.masalar_canvas = tk.Canvas(self.masalar_frame)
        self.masalar_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.masalar_frame, orient="vertical", command=self.masalar_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.masalar_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Masalar iç çerçevesi
        self.masalar_icerik_frame = ttk.Frame(self.masalar_canvas)
        self.masalar_canvas.create_window((0, 0), window=self.masalar_icerik_frame, anchor=tk.NW)
        
        # Müşteriler sekmesi
        self.musteriler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.musteriler_frame, text="Müşteriler")
        
        # Müşteriler Treeview
        self.musteriler_tree = ttk.Treeview(self.musteriler_frame, columns=("ID", "Ad Soyad", "Telefon", "Eposta", "Kayıt Tarihi"), show="headings")
        self.musteriler_tree.heading("ID", text="ID")
        self.musteriler_tree.heading("Ad Soyad", text="Ad Soyad")
        self.musteriler_tree.heading("Telefon", text="Telefon")
        self.musteriler_tree.heading("Eposta", text="Eposta")
        self.musteriler_tree.heading("Kayıt Tarihi", text="Kayıt Tarihi")
        self.musteriler_tree.pack(fill=tk.BOTH, expand=True)
        
        # Müşteri işlem butonları
        self.musteri_buton_frame = ttk.Frame(self.musteriler_frame)
        self.musteri_buton_frame.pack(fill=tk.X)
        
        ttk.Button(self.musteri_buton_frame, text="Müşteri Ekle", command=self.musteri_ekle).pack(side=tk.LEFT)
        ttk.Button(self.musteri_buton_frame, text="Müşteri Düzenle", command=self.musteri_duzenle).pack(side=tk.LEFT)
        ttk.Button(self.musteri_buton_frame, text="Müşteri Sil", command=self.musteri_sil).pack(side=tk.LEFT)
        
        # Ürünler sekmesi
        self.urunler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.urunler_frame, text="Ürünler")
        
        # Ürünler Treeview
        self.urunler_tree = ttk.Treeview(self.urunler_frame, columns=("ID", "Ürün Adı", "Kategori", "Fiyat", "Stok"), show="headings")
        self.urunler_tree.heading("ID", text="ID")
        self.urunler_tree.heading("Ürün Adı", text="Ürün Adı")
        self.urunler_tree.heading("Kategori", text="Kategori")
        self.urunler_tree.heading("Fiyat", text="Fiyat")
        self.urunler_tree.heading("Stok", text="Stok")
        self.urunler_tree.pack(fill=tk.BOTH, expand=True)
        
        # Ürün işlem butonları
        self.urun_buton_frame = ttk.Frame(self.urunler_frame)
        self.urun_buton_frame.pack(fill=tk.X)
        
        ttk.Button(self.urun_buton_frame, text="Ürün Ekle", command=self.urun_ekle).pack(side=tk.LEFT)
        ttk.Button(self.urun_buton_frame, text="Ürün Düzenle", command=self.urun_duzenle).pack(side=tk.LEFT)
        ttk.Button(self.urun_buton_frame, text="Ürün Sil", command=self.urun_sil).pack(side=tk.LEFT)
        ttk.Button(self.urun_buton_frame, text="Kategori Ekle", command=self.kategori_ekle).pack(side=tk.LEFT)
        
        # Raporlar sekmesi
        self.raporlar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raporlar_frame, text="Raporlar")
        
        # Rapor Treeview
        self.rapor_tree = ttk.Treeview(self.raporlar_frame, columns=("Tarih", "Toplam Ciro", "Toplam Adet"), show="headings")
        self.rapor_tree.heading("Tarih", text="Tarih")
        self.rapor_tree.heading("Toplam Ciro", text="Toplam Ciro")
        self.rapor_tree.heading("Toplam Adet", text="Toplam Adet")
        self.rapor_tree.pack(fill=tk.BOTH, expand=True)
        
        # Rapor işlem butonları
        self.rapor_buton_frame = ttk.Frame(self.raporlar_frame)
        self.rapor_buton_frame.pack(fill=tk.X)
        
        ttk.Button(self.rapor_buton_frame, text="Günlük Rapor", command=self.gunluk_rapor).pack(side=tk.LEFT)
        ttk.Button(self.rapor_buton_frame, text="Tarih Aralığı Rapor", command=self.tarih_araligi_rapor).pack(side=tk.LEFT)
        ttk.Button(self.rapor_buton_frame, text="Excel'e Aktar", command=self.excele_aktar).pack(side=tk.LEFT)
        ttk.Button(self.rapor_buton_frame, text="Text'e Aktar", command=self.texte_aktar).pack(side=tk.LEFT)
        
        # Masaları yükle
        self.masalar = []
        self.masa_butonlari = []
        self.load_masalar()
        
        # Müşterileri yükle
        self.musteriler = []
        self.load_musteriler()
        
        # Ürünleri yükle
        self.urunler = []
        self.kategoriler = []
        self.load_urunler()
        self.load_kategoriler()

    def tablari_olustur(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS masalar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_adi TEXT,
                    durum INTEGER DEFAULT 0,
                    musteri_id INTEGER DEFAULT 0,
                    acilis_zamani TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS musteriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad_soyad TEXT,
                    telefon TEXT,
                    eposta TEXT,
                    kayit_tarihi TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS kategoriler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kategori_adi TEXT
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS urunler (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    urun_adi TEXT,
                    kategori_id INTEGER,
                    fiyat REAL,
                    stok INTEGER DEFAULT 0
                )
            ''')
            
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS adisyonlar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_id INTEGER,
                    musteri_id INTEGER,
                    urun_id INTEGER,
                    adet INTEGER,
                    toplam_fiyat REAL,
                    tarih TEXT,
                    durum INTEGER DEFAULT 0
                )
            ''')
            
            self.baglanti.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Tablo oluşturulurken hata: {str(e)}")

    def load_masalar(self):
        try:
            self.cursor.execute("SELECT id, masa_adi, durum, musteri_id, acilis_zamani FROM masalar")
            self.masalar = self.cursor.fetchall()
            
            # Eski butonları temizle
            for btn in self.masa_butonlari:
                btn.destroy()
            self.masa_butonlari = []
            
            # Yeni butonları oluştur
            for masa in self.masalar:
                masa_id, masa_adi, durum, musteri_id, acilis_zamani = masa
                
                btn = tk.Button(
                    self.masalar_icerik_frame,
                    text=f"{masa_adi}\n{'Dolu' if durum else 'Boş'}",
                    bg="red" if durum else "green",
                    fg="white",
                    font=('Helvetica', 12, 'bold'),
                    width=15,
                    height=8,
                    command=lambda m_id=masa_id: self.masa_penceresi_ac(m_id)
                )
                btn.pack(side=tk.LEFT, padx=10, pady=10)
                self.masa_butonlari.append(btn)
            
            self.masalar_canvas.update_idletasks()
            self.masalar_canvas.configure(scrollregion=self.masalar_canvas.bbox("all"))
            
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masalar yüklenirken hata: {str(e)}")

    def load_musteriler(self):
        """Müşterileri veritabanından yükler ve treeview'a ekler"""
        try:
            # Treeview'ı temizle
            for item in self.musteriler_tree.get_children():
                self.musteriler_tree.delete(item)
            
            # Müşterileri veritabanından çek
            self.cursor.execute("SELECT id, ad_soyad, telefon, eposta, kayit_tarihi FROM musteriler")
            self.musteriler = self.cursor.fetchall()
            
            # Treeview'a ekle
            for musteri in self.musteriler:
                self.musteriler_tree.insert("", tk.END, values=musteri)
                
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteriler yüklenirken hata oluştu: {str(e)}")

    def load_urunler(self):
        """Ürünleri veritabanından yükler ve treeview'a ekler"""
        try:
            # Treeview'ı temizle
            for item in self.urunler_tree.get_children():
                self.urunler_tree.delete(item)
            
            # Ürünleri veritabanından çek (kategori bilgisiyle birlikte)
            self.cursor.execute('''
                SELECT u.id, u.urun_adi, k.kategori_adi, u.fiyat, u.stok 
                FROM urunler u
                LEFT JOIN kategoriler k ON u.kategori_id = k.id
                ORDER BY u.urun_adi
            ''')
            self.urunler = self.cursor.fetchall()
            
            # Treeview'a ekle
            for urun in self.urunler:
                self.urunler_tree.insert("", tk.END, values=urun)
                
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürünler yüklenirken hata oluştu: {str(e)}")

    def load_kategoriler(self):
        """Kategorileri veritabanından yükler"""
        try:
            self.cursor.execute("SELECT id, kategori_adi FROM kategoriler ORDER BY kategori_adi")
            self.kategoriler = self.cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Kategoriler yüklenirken hata oluştu: {str(e)}")

    def masa_penceresi_ac(self, masa_id):
        masa_penceresi = tk.Toplevel(self.root)
        masa_penceresi.title("Masa İşlemleri")
        masa_penceresi.geometry("600x400")
        
        # Masa bilgilerini al
        self.cursor.execute("SELECT masa_adi, durum, musteri_id, acilis_zamani FROM masalar WHERE id=?", (masa_id,))
        masa = self.cursor.fetchone()
        
        if masa:
            masa_adi, durum, musteri_id, acilis_zamani = masa
            
            # Müşteri bilgilerini al
            musteri_adi = ""
            if musteri_id:
                self.cursor.execute("SELECT ad_soyad FROM musteriler WHERE id=?", (musteri_id,))
                musteri = self.cursor.fetchone()
                if musteri:
                    musteri_adi = musteri[0]
            
            # Masa bilgilerini göster
            ttk.Label(masa_penceresi, text=f"Masa: {masa_adi}", font=('Helvetica', 14, 'bold')).pack(pady=10)
            ttk.Label(masa_penceresi, text=f"Durum: {'Dolu' if durum else 'Boş'}").pack()
            ttk.Label(masa_penceresi, text=f"Müşteri: {musteri_adi if musteri_adi else 'Yok'}").pack()
            ttk.Label(masa_penceresi, text=f"Açılış Zamanı: {acilis_zamani if acilis_zamani else 'Yok'}").pack()
            
            # Adisyon bilgilerini göster
            adisyon_frame = ttk.Frame(masa_penceresi)
            adisyon_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            self.adisyon_tree = ttk.Treeview(adisyon_frame, columns=("Ürün", "Adet", "Fiyat", "Toplam"), show="headings")
            self.adisyon_tree.heading("Ürün", text="Ürün")
            self.adisyon_tree.heading("Adet", text="Adet")
            self.adisyon_tree.heading("Fiyat", text="Fiyat")
            self.adisyon_tree.heading("Toplam", text="Toplam")
            self.adisyon_tree.pack(fill=tk.BOTH, expand=True)
            
            self.adisyon_yukle(masa_id)
            
            # İşlem butonları
            button_frame = ttk.Frame(masa_penceresi)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
            
            if durum:
                ttk.Button(button_frame, text="Ürün Ekle", 
                          command=lambda: self.masa_urun_ekle(masa_id, masa_penceresi)).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Müşteri Ata", 
                          command=lambda: self.musteri_ata(masa_id, masa_penceresi)).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Hesap Kapat", 
                          command=lambda: self.hesap_kapat(masa_id, masa_penceresi)).pack(side=tk.LEFT, padx=5)
            else:
                ttk.Button(button_frame, text="Masa Aç", 
                          command=lambda: self.masa_ac(masa_id, masa_penceresi)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Kapat", 
                      command=masa_penceresi.destroy).pack(side=tk.RIGHT, padx=5)
        else:
            messagebox.showerror("Hata", "Masa bulunamadı!")
            masa_penceresi.destroy()

    def pencere_boyutu_degisti(self, event=None):
        """Pencere boyutu değiştiğinde masaların boyutunu ayarlar"""
        try:
            # Canvas boyutunu güncelle
            self.masalar_canvas.update_idletasks()
            self.masalar_canvas.configure(scrollregion=self.masalar_canvas.bbox("all"))
            
            # Masa butonlarının boyutunu ayarla (isteğe bağlı)
            for btn in self.masa_butonlari:
                btn.config(width=15, height=8)  # Sabit boyut veya dinamik hesaplama yapabilirsiniz
                
        except Exception as e:
            # Hata oluşursa görmezden gel (arayüz henüz tam yüklenmemiş olabilir)
            pass

    def adisyon_yukle(self, masa_id):
        self.adisyon_tree.delete(*self.adisyon_tree.get_children())
        toplam = 0.0
        
        self.cursor.execute('''
            SELECT u.urun_adi, a.adet, u.fiyat, a.toplam_fiyat 
            FROM adisyonlar a
            JOIN urunler u ON a.urun_id = u.id
            WHERE a.masa_id=? AND a.durum=0
        ''', (masa_id,))
        
        for row in self.cursor.fetchall():
            self.adisyon_tree.insert("", tk.END, values=row)
            toplam += row[3]
        
        # Toplamı göster
        self.adisyon_tree.insert("", tk.END, values=("TOPLAM", "", "", f"{toplam:.2f} TL"))

    def masa_urun_ekle(self, masa_id, pencere):
        urun_ekle_penceresi = tk.Toplevel(pencere)
        urun_ekle_penceresi.title("Ürün Ekle")
        urun_ekle_penceresi.geometry("400x300")
        
        # Ürün seçimi
        ttk.Label(urun_ekle_penceresi, text="Ürün:").pack(pady=5)
        
        urun_secim = ttk.Combobox(urun_ekle_penceresi, 
                                 values=[f"{u[1]} - {u[3]:.2f} TL" for u in self.urunler])
        urun_secim.pack(pady=5)
        
        # Adet
        ttk.Label(urun_ekle_penceresi, text="Adet:").pack(pady=5)
        adet_secim = ttk.Spinbox(urun_ekle_penceresi, from_=1, to=100)
        adet_secim.pack(pady=5)
        
        # Ekle butonu
        ttk.Button(urun_ekle_penceresi, text="Ekle", 
                  command=lambda: self.urun_ekle_kaydet(masa_id, urun_secim.get(), adet_secim.get(), urun_ekle_penceresi)).pack(pady=10)

    def urun_ekle_kaydet(self, masa_id, urun_secimi, adet, pencere):
        try:
            urun_adi = urun_secimi.split(" - ")[0]
            urun_id = None
            fiyat = 0.0
            
            for urun in self.urunler:
                if urun[1] == urun_adi:
                    urun_id = urun[0]
                    fiyat = urun[3]
                    break
            
            if not urun_id:
                messagebox.showerror("Hata", "Ürün bulunamadı!")
                return
            
            adet = int(adet)
            toplam = fiyat * adet
            tarih = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            self.cursor.execute('''
                INSERT INTO adisyonlar (masa_id, urun_id, adet, toplam_fiyat, tarih)
                VALUES (?, ?, ?, ?, ?)
            ''', (masa_id, urun_id, adet, toplam, tarih))
            self.baglanti.commit()
            
            messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi!")
            pencere.destroy()
            
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz adet değeri!")
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün eklenirken hata: {str(e)}")

    def musteri_ata(self, masa_id, pencere):
        musteri_ata_penceresi = tk.Toplevel(pencere)
        musteri_ata_penceresi.title("Müşteri Ata")
        musteri_ata_penceresi.geometry("400x300")
        
        # Müşteri seçimi
        ttk.Label(musteri_ata_penceresi, text="Müşteri:").pack(pady=5)
        
        musteri_secim = ttk.Combobox(musteri_ata_penceresi, 
                                    values=[f"{m[1]} ({m[2]})" for m in self.musteriler])
        musteri_secim.pack(pady=5)
        
        # Ata butonu
        ttk.Button(musteri_ata_penceresi, text="Ata", 
                  command=lambda: self.musteri_ata_kaydet(masa_id, musteri_secim.get(), musteri_ata_penceresi)).pack(pady=10)

    def musteri_ata_kaydet(self, masa_id, musteri_secimi, pencere):
        try:
            if not musteri_secimi:
                messagebox.showerror("Hata", "Lütfen bir müşteri seçin!")
                return
            
            musteri_adi = musteri_secimi.split(" (")[0]
            musteri_id = None
            
            for musteri in self.musteriler:
                if musteri[1] == musteri_adi:
                    musteri_id = musteri[0]
                    break
            
            if not musteri_id:
                messagebox.showerror("Hata", "Müşteri bulunamadı!")
                return
            
            self.cursor.execute("UPDATE masalar SET musteri_id=? WHERE id=?", (musteri_id, masa_id))
            self.baglanti.commit()
            
            messagebox.showinfo("Başarılı", "Müşteri başarıyla atandı!")
            pencere.destroy()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Müşteri atanırken hata: {str(e)}")
    
    def musteri_ata(self):
        # Masa için müşteri atama penceresi
        masa_id = self.secili_masa
        
        musteri_ata_penceresi = tk.Toplevel(self.root)
        musteri_ata_penceresi.title("Müşteri Ata")
        musteri_ata_penceresi.geometry("400x300")
        
        # Müşteri seçimi
        musteri_label = ttk.Label(musteri_ata_penceresi, text="Müşteri:")
        musteri_label.pack(pady=5)
        
        self.musteri_secim = ttk.Combobox(musteri_ata_penceresi, values=[f"{m[1]} ({m[2]})" for m in self.musteriler])
        self.musteri_secim.pack(pady=5)
        
        # Ata butonu
        ata_btn = ttk.Button(musteri_ata_penceresi, text="Ata", command=lambda: self.musteri_ata_kaydet(masa_id, musteri_ata_penceresi))
        ata_btn.pack(pady=10)
    
    def musteri_ata_kaydet(self, masa_id, pencere):
        # Seçilen müşteriyi masaya ata
        secilen_musteri = self.musteri_secim.get()
        if not secilen_musteri:
            messagebox.showerror("Hata", "Lütfen bir müşteri seçin.")
            return
        
        # Müşteri ID'sini al
        musteri_adi = secilen_musteri.split(" (")[0]
        musteri_id = None
        for musteri in self.musteriler:
            if musteri[1] == musteri_adi:
                musteri_id = musteri[0]
                break
        
        if not musteri_id:
            messagebox.showerror("Hata", "Müşteri bulunamadı.")
            return
        
        # Müşteriyi masaya ata
        self.cursor.execute("UPDATE masalar SET musteri_id=? WHERE id=?", (musteri_id, masa_id))
        self.baglanti.commit()
        
        # Masaları ve masa detaylarını yenile
        self.load_masalar()
        self.masa_detay_yukle(masa_id)
        
        # Pencereyi kapat
        pencere.destroy()
        
        messagebox.showinfo("Başarılı", "Müşteri başarıyla atandı.")
    
    def musteri_ekle(self):
        # Yeni müşteri ekleme penceresi
        musteri_ekle_penceresi = tk.Toplevel(self.root)
        musteri_ekle_penceresi.title("Müşteri Ekle")
        musteri_ekle_penceresi.geometry("500x250")
        
        # Ad Soyad
        ad_soyad_label = ttk.Label(musteri_ekle_penceresi, text="Ad Soyad:")
        ad_soyad_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.ad_soyad_entry = ttk.Entry(musteri_ekle_penceresi, width=30)
        self.ad_soyad_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Telefon
        telefon_label = ttk.Label(musteri_ekle_penceresi, text="Telefon:")
        telefon_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.telefon_entry = ttk.Entry(musteri_ekle_penceresi, width=30)
        self.telefon_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Eposta
        eposta_label = ttk.Label(musteri_ekle_penceresi, text="Eposta:")
        eposta_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.eposta_entry = ttk.Entry(musteri_ekle_penceresi, width=30)
        self.eposta_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Kayıt tarihi
        kayit_tarihi_label = ttk.Label(musteri_ekle_penceresi, text="Kayıt Tarihi:")
        kayit_tarihi_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.kayit_tarihi_entry = ttk.Entry(musteri_ekle_penceresi, width=30)
        self.kayit_tarihi_entry.grid(row=3, column=1, padx=5, pady=5)
        self.kayit_tarihi_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Kaydet butonu
        kaydet_btn = ttk.Button(musteri_ekle_penceresi, text="Kaydet", 
                               command=lambda: self.musteri_kaydet(musteri_ekle_penceresi))
        kaydet_btn.grid(row=4, column=1, padx=5, pady=10, sticky=tk.E)
    
    def musteri_duzenle(self):
        # Müşteri düzenleme penceresi
        secili_item = self.musteriler_tree.selection()
        if not secili_item:
            messagebox.showerror("Hata", "Lütfen düzenlemek istediğiniz müşteriyi seçin.")
            return
        
        musteri_id = self.musteriler_tree.item(secili_item)['values'][0]
        
        musteri_duzenle_penceresi = tk.Toplevel(self.root)
        musteri_duzenle_penceresi.title("Müşteri Düzenle")
        musteri_duzenle_penceresi.geometry("500x250")
        
        # Müşteri bilgilerini al
        self.cursor.execute("SELECT ad_soyad, telefon, eposta, kayit_tarihi FROM musteriler WHERE id=?", (musteri_id,))
        musteri = self.cursor.fetchone()
        
        if not musteri:
            messagebox.showerror("Hata", "Müşteri bulunamadı.")
            musteri_duzenle_penceresi.destroy()
            return
        
        # Ad Soyad
        ad_soyad_label = ttk.Label(musteri_duzenle_penceresi, text="Ad Soyad:")
        ad_soyad_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.ad_soyad_entry = ttk.Entry(musteri_duzenle_penceresi, width=30)
        self.ad_soyad_entry.grid(row=0, column=1, padx=5, pady=5)
        self.ad_soyad_entry.insert(0, musteri[0])
        
        # Telefon
        telefon_label = ttk.Label(musteri_duzenle_penceresi, text="Telefon:")
        telefon_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.telefon_entry = ttk.Entry(musteri_duzenle_penceresi, width=30)
        self.telefon_entry.grid(row=1, column=1, padx=5, pady=5)
        self.telefon_entry.insert(0, musteri[1])
        
        # Eposta
        eposta_label = ttk.Label(musteri_duzenle_penceresi, text="Eposta:")
        eposta_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.eposta_entry = ttk.Entry(musteri_duzenle_penceresi, width=30)
        self.eposta_entry.grid(row=2, column=1, padx=5, pady=5)
        self.eposta_entry.insert(0, musteri[2])
        
        # Kayıt tarihi
        kayit_tarihi_label = ttk.Label(musteri_duzenle_penceresi, text="Kayıt Tarihi:")
        kayit_tarihi_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.kayit_tarihi_entry = ttk.Entry(musteri_duzenle_penceresi, width=30)
        self.kayit_tarihi_entry.grid(row=3, column=1, padx=5, pady=5)
        self.kayit_tarihi_entry.insert(0, musteri[3])
        
        # Güncelle butonu
        guncelle_btn = ttk.Button(musteri_duzenle_penceresi, text="Güncelle", 
                                 command=lambda: self.musteri_guncelle(musteri_id, musteri_duzenle_penceresi))
        guncelle_btn.grid(row=4, column=1, padx=5, pady=10, sticky=tk.E)
    
    def musteri_kaydet(self, pencere):
        # Yeni müşteriyi veritabanına kaydet
        ad_soyad = self.ad_soyad_entry.get()
        telefon = self.telefon_entry.get()
        eposta = self.eposta_entry.get()
        kayit_tarihi = self.kayit_tarihi_entry.get()
        
        if not ad_soyad:
            messagebox.showerror("Hata", "Ad soyad alanı boş bırakılamaz.")
            return
        
        self.cursor.execute('''
            INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi)
            VALUES (?, ?, ?, ?)
        ''', (ad_soyad, telefon, eposta, kayit_tarihi))
        self.baglanti.commit()
        
        # Müşterileri yenile
        self.load_musteriler()
        
        # Pencereyi kapat
        pencere.destroy()
        
        messagebox.showinfo("Başarılı", "Müşteri başarıyla eklendi.")
    
    def musteri_guncelle(self, musteri_id, pencere):
        # Müşteri bilgilerini güncelle
        ad_soyad = self.ad_soyad_entry.get()
        telefon = self.telefon_entry.get()
        eposta = self.eposta_entry.get()
        kayit_tarihi = self.kayit_tarihi_entry.get()
        
        if not ad_soyad:
            messagebox.showerror("Hata", "Ad soyad alanı boş bırakılamaz.")
            return
        
        self.cursor.execute('''
            UPDATE musteriler 
            SET ad_soyad=?, telefon=?, eposta=?, kayit_tarihi=?
            WHERE id=?
        ''', (ad_soyad, telefon, eposta, kayit_tarihi, musteri_id))
        self.baglanti.commit()
        
        # Müşterileri yenile
        self.load_musteriler()
        
        # Pencereyi kapat
        pencere.destroy()
        
        messagebox.showinfo("Başarılı", "Müşteri başarıyla güncellendi.")
    
    def musteri_sil(self):
        # Müşteri silme işlemi
        secili_item = self.musteriler_tree.selection()
        if not secili_item:
            messagebox.showerror("Hata", "Lütfen silmek istediğiniz müşteriyi seçin.")
            return
        
        musteri_id = self.musteriler_tree.item(secili_item)['values'][0]
        
        # Onay al
        onay = messagebox.askyesno("Onay", "Bu müşteriyi silmek istediğinize emin misiniz?")
        if not onay:
            return
        
        # Müşteriyi sil
        self.cursor.execute("DELETE FROM musteriler WHERE id=?", (musteri_id,))
        self.baglanti.commit()
        
        # Müşterileri yenile
        self.load_musteriler()
        
        messagebox.showinfo("Başarılı", "Müşteri başarıyla silindi.")
    
    def gunluk_rapor(self):
        """Günlük rapor oluşturma fonksiyonu"""
        try:
            # Bugünün tarihini al (başlangıç ve bitiş olarak)
            bugun = datetime.now().strftime("%Y-%m-%d")
            baslangic = f"{bugun} 00:00:00"
            bitis = f"{bugun} 23:59:59"
            
            # Raporu oluştur
            self.rapor_tree.delete(*self.rapor_tree.get_children())
            
            self.cursor.execute('''
                SELECT strftime('%Y-%m-%d %H:%M', tarih) AS zaman,
                    SUM(toplam_fiyat) AS ciro,
                    SUM(adet) AS adet
                FROM adisyonlar
                WHERE tarih BETWEEN ? AND ? AND durum=1
                GROUP BY strftime('%Y-%m-%d %H', tarih)
                ORDER BY tarih
            ''', (baslangic, bitis))
            
            rapor = self.cursor.fetchall()
            toplam_ciro = 0
            toplam_adet = 0
            
            for satir in rapor:
                self.rapor_tree.insert("", tk.END, values=satir)
                toplam_ciro += satir[1] if satir[1] else 0
                toplam_adet += satir[2] if satir[2] else 0
            
            # Toplam satırını ekle
            self.rapor_tree.insert("", tk.END, values=("TOPLAM", toplam_ciro, toplam_adet))
            
            messagebox.showinfo("Başarılı", f"Günlük rapor oluşturuldu\nToplam Ciro: {toplam_ciro:.2f} TL\nToplam Satış: {toplam_adet} adet")
        
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Rapor oluşturulamadı: {str(e)}")

    def tarih_araligi_rapor(self):
        """Tarih aralığına göre rapor oluşturur"""
        try:
            # Tarih seçim penceresi oluştur
            tarih_penceresi = tk.Toplevel(self.root)
            tarih_penceresi.title("Tarih Aralığı Seçin")
            tarih_penceresi.geometry("300x200")
            
            # Başlangıç tarihi
            ttk.Label(tarih_penceresi, text="Başlangıç Tarihi (YYYY-AA-GG):").pack(pady=5)
            baslangic_entry = ttk.Entry(tarih_penceresi)
            baslangic_entry.pack(pady=5)
            baslangic_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            # Bitiş tarihi
            ttk.Label(tarih_penceresi, text="Bitiş Tarihi (YYYY-AA-GG):").pack(pady=5)
            bitis_entry = ttk.Entry(tarih_penceresi)
            bitis_entry.pack(pady=5)
            bitis_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
            
            # Rapor oluştur butonu
            def rapor_olustur():
                try:
                    baslangic = f"{baslangic_entry.get()} 00:00:00"
                    bitis = f"{bitis_entry.get()} 23:59:59"
                    
                    self.rapor_tree.delete(*self.rapor_tree.get_children())
                    
                    self.cursor.execute('''
                        SELECT strftime('%Y-%m-%d', tarih) AS tarih,
                            SUM(toplam_fiyat) AS ciro,
                            SUM(adet) AS adet
                        FROM adisyonlar
                        WHERE tarih BETWEEN ? AND ? AND durum=1
                        GROUP BY strftime('%Y-%m-%d', tarih)
                        ORDER BY tarih
                    ''', (baslangic, bitis))
                    
                    rapor = self.cursor.fetchall()
                    toplam_ciro = 0
                    toplam_adet = 0
                    
                    for satir in rapor:
                        self.rapor_tree.insert("", tk.END, values=satir)
                        toplam_ciro += satir[1] if satir[1] else 0
                        toplam_adet += satir[2] if satir[2] else 0
                    
                    # Toplam satırını ekle
                    self.rapor_tree.insert("", tk.END, values=("TOPLAM", toplam_ciro, toplam_adet))
                    
                    messagebox.showinfo("Başarılı", 
                                    f"Tarih aralığı raporu oluşturuldu\n"
                                    f"Toplam Ciro: {toplam_ciro:.2f} TL\n"
                                    f"Toplam Satış: {toplam_adet} adet")
                    tarih_penceresi.destroy()
                    
                except Exception as e:
                    messagebox.showerror("Hata", f"Rapor oluşturulamadı: {str(e)}")
            
            ttk.Button(tarih_penceresi, text="Rapor Oluştur", command=rapor_olustur).pack(pady=10)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Pencere oluşturulamadı: {str(e)}")

    def urun_ekle(self):
        # Yeni ürün ekleme penceresi
        urun_ekle_penceresi = tk.Toplevel(self.root)
        urun_ekle_penceresi.title("Ürün Ekle")
        urun_ekle_penceresi.geometry("500x300")
        
        # Ürün Adı
        urun_adi_label = ttk.Label(urun_ekle_penceresi, text="Ürün Adı:")
        urun_adi_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.urun_adi_entry = ttk.Entry(urun_ekle_penceresi, width=30)
        self.urun_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Kategori
        kategori_label = ttk.Label(urun_ekle_penceresi, text="Kategori:")
        kategori_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.kategori_secim = ttk.Combobox(urun_ekle_penceresi, values=[k[1] for k in self.kategoriler])
        self.kategori_secim.grid(row=1, column=1, padx=5, pady=5)
        
        # Fiyat
        fiyat_label = ttk.Label(urun_ekle_penceresi, text="Fiyat:")
        fiyat_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.fiyat_entry = ttk.Entry(urun_ekle_penceresi, width=30)
        self.fiyat_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Stok
        stok_label = ttk.Label(urun_ekle_penceresi, text="Stok:")
        stok_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.stok_entry = ttk.Entry(urun_ekle_penceresi, width=30)
        self.stok_entry.grid(row=3, column=1, padx=5, pady=5)
        
        # Kaydet butonu
        kaydet_btn = ttk.Button(urun_ekle_penceresi, text="Kaydet", 
                               command=lambda: self.urun_kaydet(urun_ekle_penceresi))
        kaydet_btn.grid(row=4, column=1, padx=5, pady=10, sticky=tk.E)
    
    def urun_duzenle(self):
        # Ürün düzenleme penceresi
        secili_item = self.urunler_tree.selection()
        if not secili_item:
            messagebox.showerror("Hata", "Lütfen düzenlemek istediğiniz ürünü seçin.")
            return
        
        urun_id = self.urunler_tree.item(secili_item)['values'][0]
        
        urun_duzenle_penceresi = tk.Toplevel(self.root)
        urun_duzenle_penceresi.title("Ürün Düzenle")
        urun_duzenle_penceresi.geometry("500x300")
        
        # Ürün bilgilerini al
        self.cursor.execute('''
            SELECT u.urun_adi, k.kategori_adi, u.fiyat, u.stok 
            FROM urunler u
            LEFT JOIN kategoriler k ON u.kategori_id = k.id
            WHERE u.id=?
        ''', (urun_id,))
        urun = self.cursor.fetchone()
        
        if not urun:
            messagebox.showerror("Hata", "Ürün bulunamadı.")
            urun_duzenle_penceresi.destroy()
            return
        
        # Ürün Adı
        urun_adi_label = ttk.Label(urun_duzenle_penceresi, text="Ürün Adı:")
        urun_adi_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.urun_adi_entry = ttk.Entry(urun_duzenle_penceresi, width=30)
        self.urun_adi_entry.grid(row=0, column=1, padx=5, pady=5)
        self.urun_adi_entry.insert(0, urun[0])
        
        # Kategori
        kategori_label = ttk.Label(urun_duzenle_penceresi, text="Kategori:")
        kategori_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.kategori_secim = ttk.Combobox(urun_duzenle_penceresi, values=[k[1] for k in self.kategoriler])
        self.kategori_secim.grid(row=1, column=1, padx=5, pady=5)
        self.kategori_secim.set(urun[1])
        
        # Fiyat
        fiyat_label = ttk.Label(urun_duzenle_penceresi, text="Fiyat:")
        fiyat_label.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.fiyat_entry = ttk.Entry(urun_duzenle_penceresi, width=30)
        self.fiyat_entry.grid(row=2, column=1, padx=5, pady=5)
        self.fiyat_entry.insert(0, urun[2])
        
        # Stok
        stok_label = ttk.Label(urun_duzenle_penceresi, text="Stok:")
        stok_label.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.stok_entry = ttk.Entry(urun_duzenle_penceresi, width=30)
        self.stok_entry.grid(row=3, column=1, padx=5, pady=5)
        self.stok_entry.insert(0, urun[3])
        
        # Güncelle butonu
        guncelle_btn = ttk.Button(urun_duzenle_penceresi, text="Güncelle", 
                                 command=lambda: self.urun_guncelle(urun_id, urun_duzenle_penceresi))
        guncelle_btn.grid(row=4, column=1, padx=5, pady=10, sticky=tk.E)
    
    def urun_kaydet(self, pencere):
        # Yeni ürünü veritabanına kaydet
        urun_adi = self.urun_adi_entry.get()
        kategori_adi = self.kategori_secim.get()
        fiyat = self.fiyat_entry.get()
        stok = self.stok_entry.get()
        
        if not urun_adi:
            messagebox.showerror("Hata", "Ürün adı alanı boş bırakılamaz.")
            return
        
        try:
            fiyat = float(fiyat)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat değeri.")
            return
        
        try:
            stok = int(stok)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz stok değeri.")
            return
        
        # Kategori ID'sini al
        kategori_id = None
        for kategori in self.kategoriler:
            if kategori[1] == kategori_adi:
                kategori_id = kategori[0]
                break
        
        if not kategori_id and kategori_adi:
            # Kategori yoksa ekle
            self.cursor.execute("INSERT INTO kategoriler (kategori_adi) VALUES (?)", (kategori_adi,))
            self.baglanti.commit()
            kategori_id = self.cursor.lastrowid
            self.load_kategoriler()  # Kategorileri yenile
        
        self.cursor.execute('''
            INSERT INTO urunler (urun_adi, kategori_id, fiyat, stok)
            VALUES (?, ?, ?, ?)
        ''', (urun_adi, kategori_id, fiyat, stok))
        self.baglanti.commit()
        
        # Ürünleri yenile
        self.load_urunler()
        
        # Pencereyi kapat
        pencere.destroy()
        
        messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi.")
    
    def urun_guncelle(self, urun_id, pencere):
        # Ürün bilgilerini güncelle
        urun_adi = self.urun_adi_entry.get()
        kategori_adi = self.kategori_secim.get()
        fiyat = self.fiyat_entry.get()
        stok = self.stok_entry.get()
        
        if not urun_adi:
            messagebox.showerror("Hata", "Ürün adı alanı boş bırakılamaz.")
            return
        
        try:
            fiyat = float(fiyat)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz fiyat değeri.")
            return
        
        try:
            stok = int(stok)
        except ValueError:
            messagebox.showerror("Hata", "Geçersiz stok değeri.")
            return
        
        # Kategori ID'sini al
        kategori_id = None
        for kategori in self.kategoriler:
            if kategori[1] == kategori_adi:
                kategori_id = kategori[0]
                break
        
        if not kategori_id and kategori_adi:
            # Kategori yoksa ekle
            self.cursor.execute("INSERT INTO kategoriler (kategori_adi) VALUES (?)", (kategori_adi,))
            self.baglanti.commit()
            kategori_id = self.cursor.lastrowid
            self.load_kategoriler()  # Kategorileri yenile
        
        self.cursor.execute('''
            UPDATE urunler 
            SET urun_adi=?, kategori_id=?, fiyat=?, stok=?
            WHERE id=?
        ''', (urun_adi, kategori_id, fiyat, stok, urun_id))
        self.baglanti.commit()
        
        # Ürünleri yenile
        self.load_urunler()
        
        # Pencereyi kapat
        pencere.destroy()
        
        messagebox.showinfo("Başarılı", "Ürün başarıyla güncellendi.")
    
    def urun_sil(self):
        # Ürün silme işlemi
        secili_item = self.urunler_tree.selection()
        if not secili_item:
            messagebox.showerror("Hata", "Lütfen silmek istediğiniz ürünü seçin.")
            return
        
        urun_id = self.urunler_tree.item(secili_item)['values'][0]
        
        # Onay al
        onay = messagebox.askyesno("Onay", "Bu ürünü silmek istediğinize emin misiniz?")
        if not onay:
            return
        
        # Ürünü sil
        self.cursor.execute("DELETE FROM urunler WHERE id=?", (urun_id,))
        self.baglanti.commit()
        
        # Ürünleri yenile
        self.load_urunler()
        
        messagebox.showinfo("Başarılı", "Ürün başarıyla silindi.")
    
    def urun_ekle(self):
        """Yeni ürün ekleme penceresi açar"""
        urun_penceresi = tk.Toplevel(self.root)
        urun_penceresi.title("Yeni Ürün Ekle")
        urun_penceresi.geometry("400x300")
        
        # Ürün bilgileri için alanlar
        ttk.Label(urun_penceresi, text="Ürün Adı:").pack(pady=5)
        urun_adi_entry = ttk.Entry(urun_penceresi)
        urun_adi_entry.pack(pady=5)
        
        ttk.Label(urun_penceresi, text="Kategori:").pack(pady=5)
        kategori_combobox = ttk.Combobox(urun_penceresi, values=[k[1] for k in self.kategoriler])
        kategori_combobox.pack(pady=5)
        
        ttk.Label(urun_penceresi, text="Fiyat:").pack(pady=5)
        fiyat_entry = ttk.Entry(urun_penceresi)
        fiyat_entry.pack(pady=5)
        
        ttk.Label(urun_penceresi, text="Stok:").pack(pady=5)
        stok_entry = ttk.Entry(urun_penceresi)
        stok_entry.pack(pady=5)
        stok_entry.insert(0, "0")
        
        # Kaydet butonu
        def kaydet():
            try:
                # Kategori ID'sini bul
                kategori_id = None
                for kategori in self.kategoriler:
                    if kategori[1] == kategori_combobox.get():
                        kategori_id = kategori[0]
                        break
                
                self.cursor.execute(
                    "INSERT INTO urunler (urun_adi, kategori_id, fiyat, stok) VALUES (?, ?, ?, ?)",
                    (urun_adi_entry.get(), 
                    kategori_id, 
                    float(fiyat_entry.get()), 
                    int(stok_entry.get())))
                self.baglanti.commit()
                self.load_urunler()
                urun_penceresi.destroy()
                messagebox.showinfo("Başarılı", "Ürün başarıyla eklendi")
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz fiyat veya stok değeri!")
            except sqlite3.Error as e:
                messagebox.showerror("Hata", f"Ürün eklenemedi: {str(e)}")
        
        ttk.Button(urun_penceresi, text="Kaydet", command=kaydet).pack(pady=10)

    def kategori_ekle(self):
        # Yeni kategori ekleme penceresi
        kategori_adi = simpledialog.askstring("Kategori Ekle", "Kategori Adı:")
        if not kategori_adi:
            return
        
        # Kategoriyi veritabanına ekle
        self.cursor.execute("INSERT INTO kategoriler (kategori_adi) VALUES (?)", (kategori_adi,))
        self.baglanti.commit()
        
        # Kategorileri yenile
        self.load_kategoriler()
        
        messagebox.showinfo("Başarılı", "Kategori başarıyla eklendi.")
    
    def rapor_olustur(self):
        # Rapor oluştur
        if self.rapor_turu.get() == "gunluk":
            baslangic_tarihi = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            bitis_tarihi = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        else:
            try:
                baslangic_tarihi = datetime.strptime(self.baslangic_tarihi_entry.get(), "%Y-%m-%d").replace(hour=0, minute=0, second=0, microsecond=0)
                bitis_tarihi = datetime.strptime(self.bitis_tarihi_entry.get(), "%Y-%m-%d").replace(hour=23, minute=59, second=59, microsecond=999999)
            except ValueError:
                messagebox.showerror("Hata", "Geçersiz tarih formatı. Lütfen YYYY-AA-GG formatında girin.")
                return
        
        # Treeview'ı temizle
        for item in self.rapor_tree.get_children():
            self.rapor_tree.delete(item)
        
        # Raporu oluştur
        self.cursor.execute('''
            SELECT 
                strftime('%Y-%m-%d', a.tarih) AS tarih,
                SUM(a.toplam_fiyat) AS toplam_ciro,
                SUM(a.adet) AS toplam_adet
            FROM adisyonlar a
            WHERE a.durum=1 AND a.tarih BETWEEN ? AND ?
            GROUP BY strftime('%Y-%m-%d', a.tarih)
            ORDER BY tarih
        ''', (baslangic_tarihi.strftime("%Y-%m-%d %H:%M:%S"), bitis_tarihi.strftime("%Y-%m-%d %H:%M:%S")))
        
        rapor = self.cursor.fetchall()
        
        # Raporu Treeview'a ekle
        for satir in rapor:
            self.rapor_tree.insert("", tk.END, values=satir)
        
        messagebox.showinfo("Başarılı", f"{len(rapor)} günlük rapor oluşturuldu.")
    
    def excele_aktar(self):
        # Raporu Excel'e aktar
        if not self.rapor_tree.get_children():
            messagebox.showerror("Hata", "Aktarılacak rapor verisi yok.")
            return
        
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Dosyaları", "*.csv"), ("Tüm Dosyalar", "*.*")],
            title="Raporu Excel'e Aktar"
        )
        
        if not dosya_yolu:
            return
        
        try:
            with open(dosya_yolu, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f, delimiter=';')
                
                # Başlık satırı
                basliklar = []
                for col in self.rapor_tree['columns']:
                    basliklar.append(self.rapor_tree.heading(col)['text'])
                writer.writerow(basliklar)
                
                # Veri satırları
                for item in self.rapor_tree.get_children():
                    writer.writerow(self.rapor_tree.item(item)['values'])
            
            messagebox.showinfo("Başarılı", f"Rapor başarıyla {dosya_yolu} dosyasına aktarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yazılırken hata oluştu: {str(e)}")
    
    def texte_aktar(self):
        # Raporu text dosyasına aktar
        if not self.rapor_tree.get_children():
            messagebox.showerror("Hata", "Aktarılacak rapor verisi yok.")
            return
        
        dosya_yolu = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Dosyaları", "*.txt"), ("Tüm Dosyalar", "*.*")],
            title="Raporu Text'e Aktar"
        )
        
        if not dosya_yolu:
            return
        
        try:
            with open(dosya_yolu, 'w', encoding='utf-8') as f:
                # Başlık satırı
                basliklar = []
                for col in self.rapor_tree['columns']:
                    basliklar.append(self.rapor_tree.heading(col)['text'])
                f.write("\t".join(basliklar) + "\n")
                
                # Veri satırları
                for item in self.rapor_tree.get_children():
                    f.write("\t".join(map(str, self.rapor_tree.item(item)['values'])) + "\n")
            
            messagebox.showinfo("Başarılı", f"Rapor başarıyla {dosya_yolu} dosyasına aktarıldı.")
        except Exception as e:
            messagebox.showerror("Hata", f"Dosya yazılırken hata oluştu: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = KafeAdisyonProgrami(root)
    root.mainloop()
