import sys
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

class KafeAdisyon:
    def __init__(self, root):
        self.root = root
        self.root.title("Kafe Adisyon Sistemi")
        self.root.geometry("1000x800")
        
        # Veritabanı bağlantısı
        self.conn = sqlite3.connect('kafe_adisyon.db')
        self.cursor = self.conn.cursor()
        
        # Tabloları oluştur (yeniden düzenlenmiş hali)
        self.create_tables()
        
        # Stil ayarlarını yap
        self.configure_styles()
        
        # Arayüz oluştur
        self.create_ui()
        
        # Başlangıç verilerini yükle
        self.load_initial_data()

    def create_tables(self):
        """Tüm gerekli tabloları oluşturur"""
        tables = [
            '''CREATE TABLE IF NOT EXISTS masalar (
                masa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_adi TEXT,
                durum TEXT DEFAULT 'bos',
                musteri_adi TEXT,
                son_islem_zamani DATETIME
            )''',
            '''CREATE TABLE IF NOT EXISTS kategoriler (
                kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                kategori_adi TEXT UNIQUE
            )''',
            '''CREATE TABLE IF NOT EXISTS urunler (
                urun_id INTEGER PRIMARY KEY AUTOINCREMENT,
                urun_adi TEXT,
                kategori_id INTEGER,
                fiyat REAL,
                FOREIGN KEY (kategori_id) REFERENCES kategoriler(kategori_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS musteriler (
                musteri_id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad_soyad TEXT,
                telefon TEXT,
                eposta TEXT,
                kayit_tarihi DATETIME
            )''',
            '''CREATE TABLE IF NOT EXISTS adisyonlar (
                adisyon_id INTEGER PRIMARY KEY AUTOINCREMENT,
                masa_id INTEGER,
                musteri_id INTEGER,
                baslangic_zamani DATETIME,
                kapanis_zamani DATETIME,
                toplam_tutar REAL,
                odeme_durumu TEXT DEFAULT 'acik',
                FOREIGN KEY (masa_id) REFERENCES masalar(masa_id),
                FOREIGN KEY (musteri_id) REFERENCES musteriler(musteri_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS adisyon_detay (
                detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
                adisyon_id INTEGER,
                urun_id INTEGER,
                adet INTEGER,
                fiyat REAL,
                eklenme_zamani DATETIME,
                islem_tipi TEXT,
                FOREIGN KEY (adisyon_id) REFERENCES adisyonlar(adisyon_id),
                FOREIGN KEY (urun_id) REFERENCES urunler(urun_id)
            )''',
            '''CREATE TABLE IF NOT EXISTS ara_odemeler (
                odeme_id INTEGER PRIMARY KEY AUTOINCREMENT,
                adisyon_id INTEGER,
                odeme_miktari REAL,
                odeme_zamani DATETIME,
                FOREIGN KEY (adisyon_id) REFERENCES adisyonlar(adisyon_id)
            )'''
        ]
        
        for table in tables:
            try:
                self.cursor.execute(table)
            except Exception as e:
                print(f"Tablo oluşturulurken hata: {str(e)}")
        
        self.conn.commit()
    
    def configure_styles(self):
        """Tüm stil ayarlarını merkezi olarak yapar"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Combobox stili
        style.configure('TCombobox',
                      foreground='black',
                      background='white',
                      fieldbackground='white',
                      selectbackground='#0078d7',
                      selectforeground='white',
                      padding=5,
                      relief='solid',
                      bordercolor='#cccccc')
        
        style.map('TCombobox',
                fieldbackground=[('readonly', 'white')],
                selectbackground=[('readonly', '#0078d7')],
                selectforeground=[('readonly', 'white')])
        
        # Diğer stiller
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', foreground='black')
        style.configure('TButton', padding=5, background='#e1e1e1')
        style.configure('Treeview', background='white', fieldbackground='white', foreground='black')
        style.map('Treeview', background=[('selected', '#0078d7')], foreground=[('selected', 'white')])
    
    def create_ui(self):
        # Notebook (sekmeler) oluştur
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True)
        
        # Masalar sekmesi
        self.masalar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.masalar_frame, text='Masalar')
        
        # Ürünler sekmesi
        self.urunler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.urunler_frame, text='Ürünler')
        
        # Müşteriler sekmesi
        self.musteriler_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.musteriler_frame, text='Müşteriler')
        
        # Raporlar sekmesi
        self.raporlar_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raporlar_frame, text='Raporlar')
        
        # Masalar sekmesi içeriği
        self.create_masalar_tab()
        
        # Ürünler sekmesi içeriği
        self.create_urunler_tab()
        
        # Müşteriler sekmesi içeriği
        self.create_musteriler_tab()
        
        # Raporlar sekmesi içeriği
        self.create_raporlar_tab()
    
    def create_masalar_tab(self):
        # Masa yönetim butonları
        btn_frame = ttk.Frame(self.masalar_frame)
        btn_frame.pack(pady=10)
        
        self.btn_masa_ekle = ttk.Button(btn_frame, text="Masa Ekle", command=self.masa_ekle)
        self.btn_masa_ekle.pack(side='left', padx=5)
        
        self.btn_masa_sil = ttk.Button(btn_frame, text="Masa Sil", command=self.masa_sil)
        self.btn_masa_sil.pack(side='left', padx=5)
        
        # Masaları gösterecek canvas ve frame
        self.canvas = tk.Canvas(self.masalar_frame, bg='#f0f0f0', highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.masalar_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        
        # Masaları yükle
        self.load_masalar()
    
    def load_masalar(self):
        # Önceki masaları temizle
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Masaları veritabanından al
        self.cursor.execute("SELECT masa_id, masa_adi, durum, musteri_adi, son_islem_zamani FROM masalar ORDER BY masa_id")
        masalar = self.cursor.fetchall()
        
        if not masalar:
            label = ttk.Label(self.scrollable_frame, text="Henüz masa eklenmemiş.")
            label.pack(pady=20)
            return
        
        # Her satır için frame oluştur
        row_frame = None
        for i, masa in enumerate(masalar):
            masa_id, masa_adi, durum, musteri_adi, son_islem_zamani = masa
            
            # Her 6 masada bir yeni satır başlat
            if i % 6 == 0:
                row_frame = ttk.Frame(self.scrollable_frame)
                row_frame.pack(fill='x', pady=5)
            
            # Masa buton metni düzenlemesi
            btn_lines = [f"Masa {masa_id}"]  # 1. satır her zaman "Masa X"
            
            if masa_adi and masa_adi != f"Masa {masa_id}":  # Özel isim varsa
                btn_lines.append(masa_adi)  # 2. satır masa özel adı
                
            if musteri_adi:  # Müşteri adı varsa
                btn_lines.append(musteri_adi)  # 3. satır müşteri adı
                
            btn_text = '\n'.join(btn_lines)
            
            # Masa durumuna göre renk belirle
            bg_color = self.get_masa_rengi(durum, son_islem_zamani)
            
            btn = tk.Button(
                row_frame,
                text=btn_text,
                width=19,
                height=10,
                bg=bg_color,
                fg='black',
                relief='raised',
                borderwidth=2,
                command=lambda m_id=masa_id: self.masa_ac(m_id)
            )
            btn.pack(side='left', padx=10, pady=5, expand=True)
    
    def get_masa_rengi(self, durum, son_islem_zamani):
        """Masa durumuna göre renk belirle"""
        if durum == 'bos':
            return '#e6ffe6'  # Açık yeşil
        elif durum == 'dolu':
            if son_islem_zamani:
                son_islem = datetime.strptime(son_islem_zamani, '%Y-%m-%d %H:%M:%S')
                if (datetime.now() - son_islem) > timedelta(minutes=30):
                    return '#fff2e6'  # Açık turuncu (30 dakikadır boş)
            return '#ffe6e6'  # Açık kırmızı (dolu)
        elif durum == 'sabit_musteri':
            return '#e6f3ff'  # Açık mavi
        return 'white'
    
    def masa_ekle(self):
        def save_masa():
            masa_adi = entry_masa_adi.get()
            
            # Son masa numarasını bul
            self.cursor.execute("SELECT MAX(masa_id) FROM masalar")
            last_id = self.cursor.fetchone()[0]
            new_id = (last_id or 0) + 1
            
            # Masa adı yoksa sadece numarayı kullan
            if not masa_adi:
                masa_adi = f"Masa {new_id}"
            
            self.cursor.execute("INSERT INTO masalar (masa_id, masa_adi) VALUES (?, ?)", 
                              (new_id, masa_adi))
            self.conn.commit()
            top.destroy()
            self.load_masalar()
        
        top = tk.Toplevel(self.root)
        top.title("Masa Ekle")
        
        # Son masa numarasını göster
        self.cursor.execute("SELECT MAX(masa_id) FROM masalar")
        last_id = self.cursor.fetchone()[0]
        new_id = (last_id or 0) + 1
        
        ttk.Label(top, text=f"Yeni Masa Numarası: {new_id}", font=('Arial', 10, 'bold')).pack(pady=5)
        
        ttk.Label(top, text="Masa Adı (Opsiyonel):").pack(pady=5)
        entry_masa_adi = ttk.Entry(top)
        entry_masa_adi.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_masa).pack(pady=10)
    
    def masa_sil(self):
        def delete_masa():
            selected = listbox.curselection()
            if selected:
                masa_id = masalar[selected[0]][0]
                self.cursor.execute("DELETE FROM masalar WHERE masa_id=?", (masa_id,))
                self.conn.commit()
                top.destroy()
                self.load_masalar()
        
        self.cursor.execute("SELECT masa_id, masa_adi FROM masalar")
        masalar = self.cursor.fetchall()
        
        if not masalar:
            messagebox.showinfo("Bilgi", "Silinecek masa bulunamadı.")
            return
        
        top = tk.Toplevel(self.root)
        top.title("Masa Sil")
        
        ttk.Label(top, text="Silinecek Masayı Seçin:").pack(pady=5)
        
        listbox = tk.Listbox(top)
        for masa in masalar:
            listbox.insert('end', f"Masa {masa[0]} - {masa[1]}")
        listbox.pack(pady=5, fill='both', expand=True)
        
        ttk.Button(top, text="Sil", command=delete_masa).pack(pady=10)
    
    def masa_ac(self, masa_id):
        try:
            self.masa_penceresi = tk.Toplevel(self.root)
            self.masa_penceresi.title(f"Masa {masa_id}")
            self.masa_penceresi.geometry("800x600")
            
            self.current_masa_id = masa_id
            
            # Masa bilgilerini al
            self.cursor.execute("SELECT masa_adi, musteri_adi FROM masalar WHERE masa_id=?", (masa_id,))
            masa_info = self.cursor.fetchone()
            masa_adi, musteri_adi = masa_info if masa_info else (None, None)
            
            # Notebook oluştur
            self.masa_notebook = ttk.Notebook(self.masa_penceresi)
            self.masa_notebook.pack(fill='both', expand=True)
            
            # Sipariş sekmesi
            self.siparis_frame = ttk.Frame(self.masa_notebook)
            self.masa_notebook.add(self.siparis_frame, text='Sipariş')
            
            # Geçmiş Adisyonlar sekmesi
            self.gecmis_frame = ttk.Frame(self.masa_notebook)
            self.masa_notebook.add(self.gecmis_frame, text='Geçmiş Adisyonlar')
            
            # Müşteri bilgileri sekmesi
            self.musteri_frame = ttk.Frame(self.masa_notebook)
            self.masa_notebook.add(self.musteri_frame, text='Müşteri Bilgileri')
            
            # Masa bilgileri üst kısım
            info_frame = ttk.Frame(self.siparis_frame)
            info_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Label(info_frame, text=f"Masa {masa_id}").pack(side='left')
            if masa_adi:
                ttk.Label(info_frame, text=f" - {masa_adi}").pack(side='left')
            
            # Müşteri seçim alanı
            musteri_frame = ttk.Frame(self.siparis_frame)
            musteri_frame.pack(fill='x', padx=10, pady=5)
            
            ttk.Label(musteri_frame, text="Müşteri:").pack(side='left')
            
            # Müşteri seçim combobox'ı
            self.musteri_combobox = ttk.Combobox(musteri_frame, state='readonly')
            self.musteri_combobox.pack(side='left', padx=5, fill='x', expand=True)
            
            # Mevcut müşterileri yükle
            self.load_musteriler_combobox()
            
            # Mevcut müşteriyi seç
            if musteri_adi:
                self.musteri_combobox.set(musteri_adi)
            
            # Yeni müşteri ekle butonu
            btn_yeni_musteri = ttk.Button(musteri_frame, text="Yeni Müşteri", 
                                        command=self.yeni_musteri_ekle)
            btn_yeni_musteri.pack(side='left', padx=5)
            
            # Müşteri kaydet butonu
            btn_musteri_kaydet = ttk.Button(musteri_frame, text="Kaydet", 
                                          command=lambda: self.musteri_ata_kaydet(masa_id))
            btn_musteri_kaydet.pack(side='left')
            
            # Ürün ekleme alanı
            urun_ekle_frame = ttk.Frame(self.siparis_frame)
            urun_ekle_frame.pack(fill='x', padx=10, pady=10)
            
            ttk.Label(urun_ekle_frame, text="Ürün:").pack(side='left')
            
            # Kategori filtreleme
            self.kategori_var = tk.StringVar()
            self.kategori_var.set("Tüm Kategoriler")
            
            self.cursor.execute("SELECT kategori_adi FROM kategoriler")
            kategoriler = ["Tüm Kategoriler"] + [k[0] for k in self.cursor.fetchall()]
            
            kategori_menu = ttk.OptionMenu(urun_ekle_frame, self.kategori_var, *kategoriler, command=self.filter_urunler)
            kategori_menu.pack(side='left', padx=5)
            
            # Ürün seçimi
            self.urun_var = tk.StringVar()
            self.urun_combobox = ttk.Combobox(urun_ekle_frame, textvariable=self.urun_var, state='readonly')
            self.urun_combobox.pack(side='left', padx=5, fill='x', expand=True)
            self.filter_urunler()
            
            ttk.Label(urun_ekle_frame, text="Adet:").pack(side='left', padx=5)
            self.adet_var = tk.IntVar(value=1)
            spin_adet = ttk.Spinbox(urun_ekle_frame, from_=1, to=10, textvariable=self.adet_var, width=3)
            spin_adet.pack(side='left')
            
            btn_urun_ekle = ttk.Button(urun_ekle_frame, text="Ekle", command=self.urun_ekle)
            btn_urun_ekle.pack(side='left', padx=5)
            
            # Sipariş listesi
            columns = ('urun', 'adet', 'fiyat', 'toplam', 'islem')
            self.siparis_tree = ttk.Treeview(self.siparis_frame, columns=columns, show='headings')
            
            self.siparis_tree.heading('urun', text='Ürün')
            self.siparis_tree.heading('adet', text='Adet')
            self.siparis_tree.heading('fiyat', text='Birim Fiyat')
            self.siparis_tree.heading('toplam', text='Toplam')
            self.siparis_tree.heading('islem', text='İşlem')
            
            self.siparis_tree.column('urun', width=200)
            self.siparis_tree.column('adet', width=50, anchor='center')
            self.siparis_tree.column('fiyat', width=100, anchor='e')
            self.siparis_tree.column('toplam', width=100, anchor='e')
            self.siparis_tree.column('islem', width=100, anchor='center')
            
            self.siparis_tree.pack(fill='both', expand=True, padx=10, pady=10)
            
            # Sil butonu
            btn_urun_sil = ttk.Button(self.siparis_frame, text="Seçili Ürünü Sil", command=self.urun_sil)
            btn_urun_sil.pack(side='left', padx=10, pady=5)
            
            # Toplam ve ödeme butonları
            bottom_frame = ttk.Frame(self.siparis_frame)
            bottom_frame.pack(fill='x', padx=10, pady=10)
            
            self.toplam_var = tk.StringVar(value="Toplam: 0.00 TL")
            ttk.Label(bottom_frame, textvariable=self.toplam_var, font=('Arial', 12, 'bold')).pack(side='left')
            
            btn_ara_odeme = ttk.Button(bottom_frame, text="Ara Ödeme", command=self.ara_odeme)
            btn_ara_odeme.pack(side='right', padx=5)
            
            btn_kapat = ttk.Button(bottom_frame, text="Hesap Kapat", command=self.hesap_kapat)
            btn_kapat.pack(side='right', padx=5)
            
            # Geçmiş adisyonlar sekmesini doldur
            self.load_gecmis_adisyonlar()
            
            # Müşteri bilgileri sekmesini doldur
            self.load_musteri_bilgileri()
            
            # Masa durumunu güncelle
            self.update_masa_durum(masa_id, 'dolu')
            
            # Aktif adisyonu kontrol et
            self.check_active_adisyon(masa_id)
            
        except Exception as e:
            messagebox.showerror("Hata", f"Masa açılırken hata oluştu: {str(e)}")
            if hasattr(self, 'masa_penceresi'):
                self.masa_penceresi.destroy()
    
    def load_musteriler_combobox(self):
        """Müşteri combobox'ını doldur"""
        self.cursor.execute("SELECT ad_soyad FROM musteriler ORDER BY ad_soyad")
        musteriler = [m[0] for m in self.cursor.fetchall()]
        self.musteri_combobox['values'] = musteriler
    
    def yeni_musteri_ekle(self):
        """Masa penceresinden yeni müşteri ekle"""
        def save_musteri():
            ad_soyad = entry_ad.get()
            telefon = entry_tel.get()
            eposta = entry_eposta.get()
            
            if not ad_soyad:
                messagebox.showwarning("Uyarı", "Ad soyad boş olamaz!")
                return
            
            self.cursor.execute('''
                INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi)
                VALUES (?, ?, ?, ?)
            ''', (ad_soyad, telefon if telefon else None, 
                  eposta if eposta else None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            
            top.destroy()
            self.load_musteriler_combobox()
            self.musteri_combobox.set(ad_soyad)
            messagebox.showinfo("Bilgi", "Müşteri başarıyla eklendi.")
        
        top = tk.Toplevel(self.root)
        top.title("Yeni Müşteri Ekle")
        
        ttk.Label(top, text="Ad Soyad:").pack(pady=5)
        entry_ad = ttk.Entry(top)
        entry_ad.pack(pady=5)
        
        ttk.Label(top, text="Telefon:").pack(pady=5)
        entry_tel = ttk.Entry(top)
        entry_tel.pack(pady=5)
        
        ttk.Label(top, text="E-posta:").pack(pady=5)
        entry_eposta = ttk.Entry(top)
        entry_eposta.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_musteri).pack(pady=10)
    
    def musteri_ata_kaydet(self, masa_id):
        """Seçili müşteriyi masaya ata"""
        musteri_adi = self.musteri_combobox.get()
        
        # Masa durumunu belirle
        durum = 'dolu' if not musteri_adi else 'sabit_musteri'
        
        self.cursor.execute('''
            UPDATE masalar 
            SET musteri_adi = ?, durum = ?
            WHERE masa_id = ?
        ''', (musteri_adi if musteri_adi else None, durum, masa_id))
        self.conn.commit()
        
        # Müşteri bilgilerini hemen yenile
        self.load_musteri_bilgileri()
        messagebox.showinfo("Bilgi", "Müşteri ataması kaydedildi.")
        self.load_masalar()  # Ana masa listesini de güncelle
    
    def filter_urunler(self, event=None):
        try:
            kategori = self.kategori_var.get()
            
            # Combobox yapılandırması
            if hasattr(self, 'urun_combobox'):
                self.urun_combobox.config(
                    foreground='black',
                    background='white'
                )
            
            if kategori == "Tüm Kategoriler":
                self.cursor.execute('''
                    SELECT u.urun_id, u.urun_adi, k.kategori_adi, u.fiyat 
                    FROM urunler u
                    LEFT JOIN kategoriler k ON u.kategori_id = k.kategori_id
                    ORDER BY k.kategori_adi, u.urun_adi
                ''')
            else:
                self.cursor.execute('''
                    SELECT u.urun_id, u.urun_adi, k.kategori_adi, u.fiyat 
                    FROM urunler u
                    JOIN kategoriler k ON u.kategori_id = k.kategori_id
                    WHERE k.kategori_adi = ?
                    ORDER BY u.urun_adi
                ''', (kategori,))
            
            urunler = self.cursor.fetchall()
            display_list = [f"{u[1]} ({u[2]}) - {u[3]:.2f} TL" for u in urunler]
            
            if hasattr(self, 'urun_combobox'):
                self.urun_combobox['values'] = display_list
                if display_list:
                    self.urun_combobox.current(0)
                
                self.urun_id_map = {display: u[0] for display, u in zip(display_list, urunler)}
        except Exception as e:
            print(f"Ürün filtreleme hatası: {str(e)}")
    
    def urun_ekle(self):
        try:
            selected_display = self.urun_var.get()
            if not selected_display:
                messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin!")
                return
            
            urun_id = self.urun_id_map[selected_display]
            adet = self.adet_var.get()
            
            # Ürün bilgilerini al
            self.cursor.execute("SELECT urun_adi, fiyat FROM urunler WHERE urun_id=?", (urun_id,))
            urun_adi, fiyat = self.cursor.fetchone()
            
            # Treeview'a ekle
            toplam = adet * fiyat
            self.siparis_tree.insert('', 'end', values=(urun_adi, adet, f"{fiyat:.2f}", f"{toplam:.2f}", "Ekle"))
            
            # Toplamı güncelle
            self.update_toplam()
            
            # Adisyon detayına ekle
            if hasattr(self, 'active_adisyon_id'):
                self.cursor.execute('''
                    INSERT INTO adisyon_detay (adisyon_id, urun_id, adet, fiyat, eklenme_zamani, islem_tipi)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.active_adisyon_id, urun_id, adet, fiyat, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'ekleme'))
                self.conn.commit()
            
            # Masa son işlem zamanını güncelle
            self.update_son_islem_zamani(self.current_masa_id)
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün eklenirken hata oluştu: {str(e)}")
    
    def update_toplam(self):
        toplam = 0.0
        for item in self.siparis_tree.get_children():
            values = self.siparis_tree.item(item)['values']
            if values[4] == 'Ekle':  # Sadece eklenen ürünleri toplama dahil et
                toplam += float(values[3])
        
        self.toplam_var.set(f"Toplam: {toplam:.2f} TL")
    
    def urun_sil(self):
        try:
            selected_item = self.siparis_tree.selection()
            if not selected_item:
                messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz ürünü seçin!")
                return
            
            item = self.siparis_tree.item(selected_item)
            urun_adi = item['values'][0]
            adet = item['values'][1]
            
            # Ürün ID'sini al
            self.cursor.execute("SELECT urun_id FROM urunler WHERE urun_adi=?", (urun_adi,))
            urun_id = self.cursor.fetchone()[0]
            
            # Treeview'dan sil
            self.siparis_tree.delete(selected_item)
            
            # Toplamı güncelle
            self.update_toplam()
            
            # Adisyon detayına silme işlemini ekle
            if hasattr(self, 'active_adisyon_id'):
                self.cursor.execute('''
                    INSERT INTO adisyon_detay (adisyon_id, urun_id, adet, fiyat, eklenme_zamani, islem_tipi)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (self.active_adisyon_id, urun_id, adet, 0, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'silme'))
                self.conn.commit()
            
            # Masa son işlem zamanını güncelle
            self.update_son_islem_zamani(self.current_masa_id)
        except Exception as e:
            messagebox.showerror("Hata", f"Ürün silinirken hata oluştu: {str(e)}")
    
    def ara_odeme(self):
        try:
            if not hasattr(self, 'active_adisyon_id'):
                messagebox.showwarning("Uyarı", "Aktif bir adisyon bulunamadı!")
                return
            
            # Toplamı hesapla
            toplam = 0.0
            for item in self.siparis_tree.get_children():
                values = self.siparis_tree.item(item)['values']
                if values[4] == 'Ekle':  # Sadece eklenen ürünleri toplama dahil et
                    toplam += float(values[3])
            
            if toplam <= 0:
                messagebox.showwarning("Uyarı", "Ödenecek tutar bulunamadı!")
                return

            def save_odeme():
                try:
                    odeme_miktari = float(entry_odeme.get())
                    if odeme_miktari <= 0:
                        messagebox.showwarning("Uyarı", "Geçerli bir ödeme miktarı girin!")
                        return
                    
                    # Ara ödemeyi kaydet
                    self.cursor.execute('''
                        INSERT INTO ara_odemeler (adisyon_id, odeme_miktari, odeme_zamani)
                        VALUES (?, ?, ?)
                    ''', (self.active_adisyon_id, odeme_miktari, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
                    self.conn.commit()
                    
                    # Verileri yenile
                    self.load_adisyon_detay(self.active_adisyon_id)  # Adisyon detaylarını yenile
                    self.load_gecmis_adisyonlar()  # Geçmiş adisyonları yenile
                    
                    top.destroy()
                    messagebox.showinfo("Bilgi", f"{odeme_miktari:.2f} TL ara ödeme kaydedildi.")
                    
                except ValueError:
                    messagebox.showwarning("Uyarı", "Geçerli bir sayı girin!")
            
            top = tk.Toplevel(self.root)
            top.title("Ara Ödeme")
            
            ttk.Label(top, text=f"Ödenecek Tutar: {toplam:.2f} TL").pack(pady=10)
            ttk.Label(top, text="Ödeme Miktarı:").pack()
            
            entry_odeme = ttk.Entry(top)
            entry_odeme.pack(pady=5)
            
            ttk.Button(top, text="Ödemeyi Kaydet", command=save_odeme).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Hata", f"Ara ödeme sırasında hata oluştu: {str(e)}")
    
    def hesap_kapat(self):
        try:
            if not hasattr(self, 'active_adisyon_id'):
                messagebox.showwarning("Uyarı", "Aktif bir adisyon bulunamadı!")
                return
            
            # Toplamı hesapla
            toplam = 0.0
            for item in self.siparis_tree.get_children():
                values = self.siparis_tree.item(item)['values']
                if values[4] == 'Ekle':  # Sadece eklenen ürünleri toplama dahil et
                    toplam += float(values[3])
            
            if toplam <= 0:
                messagebox.showwarning("Uyarı", "Kapatılacak tutar bulunamadı!")
                return
            
            # Adisyonu kapat
            self.cursor.execute('''
                UPDATE adisyonlar 
                SET kapanis_zamani = ?, toplam_tutar = ?, odeme_durumu = 'kapali'
                WHERE adisyon_id = ?
            ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), toplam, self.active_adisyon_id))
            self.conn.commit()
            
            # Masa durumunu güncelle
            self.update_masa_durum(self.current_masa_id, 'bos')
            self.update_son_islem_zamani(self.current_masa_id)
            
            # Treeview'ı temizle
            for item in self.siparis_tree.get_children():
                self.siparis_tree.delete(item)
            
            self.toplam_var.set("Toplam: 0.00 TL")
            
            # Aktif adisyonu temizle
            del self.active_adisyon_id
            
            messagebox.showinfo("Bilgi", f"Hesap kapatıldı. Toplam: {toplam:.2f} TL")
            self.masa_penceresi.destroy()
            self.load_masalar()
        except Exception as e:
            messagebox.showerror("Hata", f"Hesap kapatılırken hata oluştu: {str(e)}")
    
    def update_masa_durum(self, masa_id, durum):
        self.cursor.execute('''
            UPDATE masalar 
            SET durum = ?
            WHERE masa_id = ?
        ''', (durum, masa_id))
        self.conn.commit()
    
    def update_son_islem_zamani(self, masa_id):
        self.cursor.execute('''
            UPDATE masalar 
            SET son_islem_zamani = ?
            WHERE masa_id = ?
        ''', (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), masa_id))
        self.conn.commit()
    
    def check_active_adisyon(self, masa_id):
        # Masa için aktif adisyon var mı kontrol et
        self.cursor.execute('''
            SELECT adisyon_id FROM adisyonlar 
            WHERE masa_id = ? AND odeme_durumu = 'acik'
        ''', (masa_id,))
        result = self.cursor.fetchone()
        
        if result:
            self.active_adisyon_id = result[0]
            # Adisyon detaylarını yükle
            self.load_adisyon_detay(self.active_adisyon_id)
        else:
            # Yeni adisyon oluştur
            self.cursor.execute('''
                INSERT INTO adisyonlar (masa_id, baslangic_zamani)
                VALUES (?, ?)
            ''', (masa_id, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            self.active_adisyon_id = self.cursor.lastrowid
    
    def load_adisyon_detay(self, adisyon_id):
        # Önceki siparişleri temizle
        for item in self.siparis_tree.get_children():
            self.siparis_tree.delete(item)
        
        # Adisyon detaylarını yükle
        self.cursor.execute('''
            SELECT u.urun_adi, ad.adet, ad.fiyat, ad.islem_tipi
            FROM adisyon_detay ad
            JOIN urunler u ON ad.urun_id = u.urun_id
            WHERE ad.adisyon_id = ?
            ORDER BY ad.eklenme_zamani
        ''', (adisyon_id,))
        
        toplam = 0.0
        for urun_adi, adet, fiyat, islem_tipi in self.cursor.fetchall():
            if islem_tipi == 'ekleme':
                toplam_urun = adet * fiyat
                toplam += toplam_urun
                self.siparis_tree.insert('', 'end', values=(urun_adi, adet, f"{fiyat:.2f}", f"{toplam_urun:.2f}", "Ekle"))
            elif islem_tipi == 'silme':
                self.siparis_tree.insert('', 'end', values=(urun_adi, adet, "0.00", "0.00", "Sil"))
        
        self.toplam_var.set(f"Toplam: {toplam:.2f} TL")
    
    def load_gecmis_adisyonlar(self):
        # Geçmiş adisyonlar için treeview oluştur
        columns = ('tarih', 'toplam', 'durum')
        self.gecmis_tree = ttk.Treeview(self.gecmis_frame, columns=columns, show='headings')
        
        self.gecmis_tree.heading('tarih', text='Tarih')
        self.gecmis_tree.heading('toplam', text='Toplam')
        self.gecmis_tree.heading('durum', text='Durum')
        
        self.gecmis_tree.column('tarih', width=200)
        self.gecmis_tree.column('toplam', width=100, anchor='e')
        self.gecmis_tree.column('durum', width=100, anchor='center')
        
        self.gecmis_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Detay gösterim alanı
        self.detay_frame = ttk.Frame(self.gecmis_frame)
        self.detay_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Geçmiş adisyonları yükle
        self.cursor.execute('''
            SELECT adisyon_id, baslangic_zamani, kapanis_zamani, toplam_tutar, odeme_durumu
            FROM adisyonlar
            WHERE masa_id = ?
            ORDER BY baslangic_zamani DESC
        ''', (self.current_masa_id,))
        
        for adisyon_id, baslangic, kapanis, toplam, durum in self.cursor.fetchall():
            tarih = baslangic
            if kapanis:
                tarih = f"{baslangic} - {kapanis}"
            
            toplam_display = f"{toplam:.2f} TL" if toplam else "-"
            self.gecmis_tree.insert('', 'end', values=(tarih, toplam_display, durum.capitalize()), iid=adisyon_id)
        
        # Tıklama olayı
        self.gecmis_tree.bind('<<TreeviewSelect>>', self.show_adisyon_detay)
    
    def show_adisyon_detay(self, event):
        # Önceki detayları temizle
        for widget in self.detay_frame.winfo_children():
            widget.destroy()
        
        selected = self.gecmis_tree.selection()
        if not selected:
            return
        
        adisyon_id = selected[0]
        
        # Adisyon detaylarını al
        self.cursor.execute('''
            SELECT u.urun_adi, ad.adet, ad.fiyat, ad.eklenme_zamani, ad.islem_tipi
            FROM adisyon_detay ad
            JOIN urunler u ON ad.urun_id = u.urun_id
            WHERE ad.adisyon_id = ?
            ORDER BY ad.eklenme_zamani
        ''', (adisyon_id,))
        
        detaylar = self.cursor.fetchall()
        
        if not detaylar:
            ttk.Label(self.detay_frame, text="Bu adisyona ait detay bulunamadı.").pack()
            return
        
        # Treeview oluştur
        columns = ('zaman', 'islem', 'urun', 'adet', 'fiyat', 'toplam')
        detay_tree = ttk.Treeview(self.detay_frame, columns=columns, show='headings')
        
        detay_tree.heading('zaman', text='Zaman')
        detay_tree.heading('islem', text='İşlem')
        detay_tree.heading('urun', text='Ürün')
        detay_tree.heading('adet', text='Adet')
        detay_tree.heading('fiyat', text='Birim Fiyat')
        detay_tree.heading('toplam', text='Toplam')
        
        detay_tree.column('zaman', width=150)
        detay_tree.column('islem', width=80, anchor='center')
        detay_tree.column('urun', width=150)
        detay_tree.column('adet', width=50, anchor='center')
        detay_tree.column('fiyat', width=80, anchor='e')
        detay_tree.column('toplam', width=80, anchor='e')
        
        detay_tree.pack(fill='both', expand=True)
        
        # Ara ödemeleri al
        self.cursor.execute('''
            SELECT odeme_miktari, odeme_zamani
            FROM ara_odemeler
            WHERE adisyon_id = ?
            ORDER BY odeme_zamani
        ''', (adisyon_id,))
        
        ara_odemeler = self.cursor.fetchall()
        
        # Detayları ekle
        for urun_adi, adet, fiyat, zaman, islem_tipi in detaylar:
            if islem_tipi == 'ekleme':
                toplam = adet * fiyat
                detay_tree.insert('', 'end', values=(
                    zaman, 
                    islem_tipi.capitalize(), 
                    urun_adi, 
                    adet, 
                    f"{fiyat:.2f}", 
                    f"{toplam:.2f}"
                ))
            elif islem_tipi == 'silme':
                detay_tree.insert('', 'end', values=(
                    zaman, 
                    islem_tipi.capitalize(), 
                    urun_adi, 
                    adet, 
                    "-", 
                    "-"
                ))
        
        # Ara ödemeleri ekle
        for odeme_miktari, odeme_zamani in ara_odemeler:
            detay_tree.insert('', 'end', values=(
                odeme_zamani, 
                "Ara Ödeme", 
                "-", 
                "-", 
                "-", 
                f"{odeme_miktari:.2f}"
            ))
    
    def load_musteri_bilgileri(self):
        # Önceki bilgileri temizle
        for widget in self.musteri_frame.winfo_children():
            widget.destroy()
        
        # Müşteri bilgilerini al
        self.cursor.execute("SELECT musteri_adi FROM masalar WHERE masa_id=?", (self.current_masa_id,))
        musteri_adi = self.cursor.fetchone()[0]
        
        if not musteri_adi:
            ttk.Label(self.musteri_frame, text="Bu masa için müşteri bilgisi kayıtlı değil.").pack(pady=20)
            return
        
        musteri_id, ad_soyad, telefon, eposta, kayit_tarihi = musteri
        
        # Bilgileri göster
        info_frame = ttk.Frame(self.musteri_frame)
        info_frame.pack(pady=10)
        
        ttk.Label(info_frame, text="Ad Soyad:", font=('Arial', 10, 'bold')).grid(row=0, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(info_frame, text=ad_soyad).grid(row=0, column=1, sticky='w', pady=5)
        
        ttk.Label(info_frame, text="Telefon:", font=('Arial', 10, 'bold')).grid(row=1, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(info_frame, text=telefon).grid(row=1, column=1, sticky='w', pady=5)
        
        ttk.Label(info_frame, text="E-posta:", font=('Arial', 10, 'bold')).grid(row=2, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(info_frame, text=eposta).grid(row=2, column=1, sticky='w', pady=5)
        
        ttk.Label(info_frame, text="Kayıt Tarihi:", font=('Arial', 10, 'bold')).grid(row=3, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(info_frame, text=kayit_tarihi).grid(row=3, column=1, sticky='w', pady=5)
        
        # Geçmiş adisyonlar
        ttk.Label(self.musteri_frame, text="Geçmiş Adisyonlar", font=('Arial', 10, 'bold')).pack(pady=10)
        
        columns = ('tarih', 'masa', 'toplam')
        musteri_adisyon_tree = ttk.Treeview(self.musteri_frame, columns=columns, show='headings')
        
        musteri_adisyon_tree.heading('tarih', text='Tarih')
        musteri_adisyon_tree.heading('masa', text='Masa')
        musteri_adisyon_tree.heading('toplam', text='Toplam')
        
        musteri_adisyon_tree.column('tarih', width=200)
        musteri_adisyon_tree.column('masa', width=100)
        musteri_adisyon_tree.column('toplam', width=100, anchor='e')
        
        musteri_adisyon_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Müşterinin geçmiş adisyonlarını al
        self.cursor.execute('''
            SELECT a.adisyon_id, a.baslangic_zamani, a.kapanis_zamani, a.toplam_tutar, m.masa_id, m.masa_adi
            FROM adisyonlar a
            JOIN masalar m ON a.masa_id = m.masa_id
            WHERE m.musteri_adi = ? AND a.odeme_durumu = 'kapali'
            ORDER BY a.baslangic_zamani DESC
            LIMIT 20
        ''', (musteri_adi,))
        
        for adisyon_id, baslangic, kapanis, toplam, masa_id, masa_adi in self.cursor.fetchall():
            tarih = baslangic
            if kapanis:
                tarih = f"{baslangic} - {kapanis}"
            
            masa_text = f"Masa {masa_id}"
            if masa_adi:
                masa_text += f" ({masa_adi})"
            
            musteri_adisyon_tree.insert('', 'end', values=(
                tarih, 
                masa_text, 
                f"{toplam:.2f} TL" if toplam else "-"
            ))
    
    def create_urunler_tab(self):
        # Üst butonlar
        btn_frame = ttk.Frame(self.urunler_frame)
        btn_frame.pack(pady=10)
        
        self.btn_urun_ekle = ttk.Button(btn_frame, text="Ürün Ekle", command=self.urun_ekle_form)
        self.btn_urun_ekle.pack(side='left', padx=5)
        
        self.btn_urun_duzenle = ttk.Button(btn_frame, text="Ürün Düzenle", command=self.urun_duzenle)
        self.btn_urun_duzenle.pack(side='left', padx=5)
        
        self.btn_urun_sil = ttk.Button(btn_frame, text="Ürün Sil", command=self.urun_sil_form)
        self.btn_urun_sil.pack(side='left', padx=5)
        
        self.btn_kategori_ekle = ttk.Button(btn_frame, text="Kategori Ekle", command=self.kategori_ekle)
        self.btn_kategori_ekle.pack(side='left', padx=5)
        
        # Ürün listesi
        columns = ('id', 'urun_adi', 'kategori', 'fiyat')
        self.urun_tree = ttk.Treeview(self.urunler_frame, columns=columns, show='headings')
        
        self.urun_tree.heading('id', text='ID')
        self.urun_tree.heading('urun_adi', text='Ürün Adı')
        self.urun_tree.heading('kategori', text='Kategori')
        self.urun_tree.heading('fiyat', text='Fiyat')
        
        self.urun_tree.column('id', width=50, anchor='center')
        self.urun_tree.column('urun_adi', width=200)
        self.urun_tree.column('kategori', width=150)
        self.urun_tree.column('fiyat', width=100, anchor='e')
        
        self.urun_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Ürünleri yükle
        self.load_urunler()
    
    def load_urunler(self):
        # Önceki ürünleri temizle
        for item in self.urun_tree.get_children():
            self.urun_tree.delete(item)
        
        # Ürünleri veritabanından al
        self.cursor.execute('''
            SELECT u.urun_id, u.urun_adi, k.kategori_adi, u.fiyat
            FROM urunler u
            LEFT JOIN kategoriler k ON u.kategori_id = k.kategori_id
            ORDER BY k.kategori_adi, u.urun_adi
        ''')
        
        for urun_id, urun_adi, kategori_adi, fiyat in self.cursor.fetchall():
            self.urun_tree.insert('', 'end', values=(urun_id, urun_adi, kategori_adi if kategori_adi else "-", f"{fiyat:.2f}"))
    
    def urun_ekle_form(self):
        def save_urun():
            urun_adi = entry_urun_adi.get()
            kategori = kategori_var.get()
            fiyat = entry_fiyat.get()
            
            if not urun_adi or not fiyat:
                messagebox.showwarning("Uyarı", "Ürün adı ve fiyat boş olamaz!")
                return
            
            try:
                fiyat = float(fiyat)
                if fiyat <= 0:
                    messagebox.showwarning("Uyarı", "Fiyat 0'dan büyük olmalıdır!")
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir fiyat girin!")
                return
            
            # Kategori ID'sini al
            kategori_id = None
            if kategori != "Kategori Seçin":
                self.cursor.execute("SELECT kategori_id FROM kategoriler WHERE kategori_adi=?", (kategori,))
                result = self.cursor.fetchone()
                if result:
                    kategori_id = result[0]
            
            # Ürünü ekle
            self.cursor.execute('''
                INSERT INTO urunler (urun_adi, kategori_id, fiyat)
                VALUES (?, ?, ?)
            ''', (urun_adi, kategori_id, fiyat))
            self.conn.commit()
            
            top.destroy()
            self.load_urunler()
            messagebox.showinfo("Bilgi", "Ürün başarıyla eklendi.")
        
        top = tk.Toplevel(self.root)
        top.title("Yeni Ürün Ekle")
        
        ttk.Label(top, text="Ürün Adı:").pack(pady=5)
        entry_urun_adi = ttk.Entry(top)
        entry_urun_adi.pack(pady=5)
        
        # Kategorileri al
        self.cursor.execute("SELECT kategori_adi FROM kategoriler")
        kategoriler = ["Kategori Seçin"] + [k[0] for k in self.cursor.fetchall()]
        
        ttk.Label(top, text="Kategori:").pack(pady=5)
        kategori_var = tk.StringVar()
        kategori_var.set("Kategori Seçin")
        kategori_menu = ttk.OptionMenu(top, kategori_var, *kategoriler)
        kategori_menu.pack(pady=5)
        
        ttk.Label(top, text="Fiyat:").pack(pady=5)
        entry_fiyat = ttk.Entry(top)
        entry_fiyat.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_urun).pack(pady=10)
    
    def urun_duzenle(self):
        selected = self.urun_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz ürünü seçin!")
            return
        
        item = self.urun_tree.item(selected[0])
        urun_id, urun_adi, kategori_adi, fiyat = item['values']
        fiyat = float(fiyat)
        
        def save_changes():
            new_urun_adi = entry_urun_adi.get()
            new_kategori = kategori_var.get()
            new_fiyat = entry_fiyat.get()
            
            if not new_urun_adi or not new_fiyat:
                messagebox.showwarning("Uyarı", "Ürün adı ve fiyat boş olamaz!")
                return
            
            try:
                new_fiyat = float(new_fiyat)
                if new_fiyat <= 0:
                    messagebox.showwarning("Uyarı", "Fiyat 0'dan büyük olmalıdır!")
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir fiyat girin!")
                return
            
            # Kategori ID'sini al
            new_kategori_id = None
            if new_kategori != "Kategori Seçin":
                self.cursor.execute("SELECT kategori_id FROM kategoriler WHERE kategori_adi=?", (new_kategori,))
                result = self.cursor.fetchone()
                if result:
                    new_kategori_id = result[0]
            
            # Ürünü güncelle
            self.cursor.execute('''
                UPDATE urunler
                SET urun_adi = ?, kategori_id = ?, fiyat = ?
                WHERE urun_id = ?
            ''', (new_urun_adi, new_kategori_id, new_fiyat, urun_id))
            self.conn.commit()
            
            top.destroy()
            self.load_urunler()
            messagebox.showinfo("Bilgi", "Ürün başarıyla güncellendi.")
        
        top = tk.Toplevel(self.root)
        top.title("Ürün Düzenle")
        
        ttk.Label(top, text="Ürün Adı:").pack(pady=5)
        entry_urun_adi = ttk.Entry(top)
        entry_urun_adi.insert(0, urun_adi)
        entry_urun_adi.pack(pady=5)
        
        # Kategorileri al
        self.cursor.execute("SELECT kategori_adi FROM kategoriler")
        kategoriler = ["Kategori Seçin"] + [k[0] for k in self.cursor.fetchall()]
        
        ttk.Label(top, text="Kategori:").pack(pady=5)
        kategori_var = tk.StringVar()
        kategori_var.set(kategori_adi if kategori_adi != "-" else "Kategori Seçin")
        kategori_menu = ttk.OptionMenu(top, kategori_var, *kategoriler)
        kategori_menu.pack(pady=5)
        
        ttk.Label(top, text="Fiyat:").pack(pady=5)
        entry_fiyat = ttk.Entry(top)
        entry_fiyat.insert(0, str(fiyat))
        entry_fiyat.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_changes).pack(pady=10)
    
    def urun_sil_form(self):
        selected = self.urun_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz ürünü seçin!")
            return
        
        item = self.urun_tree.item(selected[0])
        urun_id, urun_adi, _, _ = item['values']
        
        if messagebox.askyesno("Onay", f"'{urun_adi}' adlı ürünü silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM urunler WHERE urun_id=?", (urun_id,))
            self.conn.commit()
            self.load_urunler()
            messagebox.showinfo("Bilgi", "Ürün başarıyla silindi.")
    
    def kategori_ekle(self):
        def save_kategori():
            kategori_adi = entry_kategori.get()
            if kategori_adi:
                try:
                    self.cursor.execute("INSERT INTO kategoriler (kategori_adi) VALUES (?)", (kategori_adi,))
                    self.conn.commit()
                    top.destroy()
                    messagebox.showinfo("Bilgi", "Kategori başarıyla eklendi.")
                except sqlite3.IntegrityError:
                    messagebox.showwarning("Uyarı", "Bu kategori zaten var!")
            else:
                messagebox.showwarning("Uyarı", "Kategori adı boş olamaz!")
        
        top = tk.Toplevel(self.root)
        top.title("Yeni Kategori Ekle")
        
        ttk.Label(top, text="Kategori Adı:").pack(pady=5)
        entry_kategori = ttk.Entry(top)
        entry_kategori.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_kategori).pack(pady=10)
    
    def create_musteriler_tab(self):
        # Üst butonlar
        btn_frame = ttk.Frame(self.musteriler_frame)
        btn_frame.pack(pady=10)
        
        self.btn_musteri_ekle = ttk.Button(btn_frame, text="Müşteri Ekle", command=self.musteri_ekle)
        self.btn_musteri_ekle.pack(side='left', padx=5)
        
        self.btn_musteri_duzenle = ttk.Button(btn_frame, text="Müşteri Düzenle", command=self.musteri_duzenle)
        self.btn_musteri_duzenle.pack(side='left', padx=5)
        
        self.btn_musteri_sil = ttk.Button(btn_frame, text="Müşteri Sil", command=self.musteri_sil)
        self.btn_musteri_sil.pack(side='left', padx=5)
        
        # Müşteri listesi
        columns = ('id', 'ad_soyad', 'telefon', 'eposta', 'kayit_tarihi')
        self.musteri_tree = ttk.Treeview(self.musteriler_frame, columns=columns, show='headings')
        
        self.musteri_tree.heading('id', text='ID')
        self.musteri_tree.heading('ad_soyad', text='Ad Soyad')
        self.musteri_tree.heading('telefon', text='Telefon')
        self.musteri_tree.heading('eposta', text='E-posta')
        self.musteri_tree.heading('kayit_tarihi', text='Kayıt Tarihi')
        
        self.musteri_tree.column('id', width=50, anchor='center')
        self.musteri_tree.column('ad_soyad', width=150)
        self.musteri_tree.column('telefon', width=100)
        self.musteri_tree.column('eposta', width=150)
        self.musteri_tree.column('kayit_tarihi', width=120)
        
        self.musteri_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Müşterileri yükle
        self.load_musteriler()
    
    def load_musteriler(self):
        # Önceki müşterileri temizle
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)
        
        # Müşterileri veritabanından al
        self.cursor.execute('''
            SELECT musteri_id, ad_soyad, telefon, eposta, kayit_tarihi
            FROM musteriler
            ORDER BY ad_soyad
        ''')
        
        for musteri_id, ad_soyad, telefon, eposta, kayit_tarihi in self.cursor.fetchall():
            self.musteri_tree.insert('', 'end', values=(
                musteri_id, 
                ad_soyad, 
                telefon if telefon else "-", 
                eposta if eposta else "-", 
                kayit_tarihi
            ))
    
    def musteri_ekle(self):
        def save_musteri():
            ad_soyad = entry_ad.get()
            telefon = entry_tel.get()
            eposta = entry_eposta.get()
            
            if not ad_soyad:
                messagebox.showwarning("Uyarı", "Ad soyad boş olamaz!")
                return
            
            self.cursor.execute('''
                INSERT INTO musteriler (ad_soyad, telefon, eposta, kayit_tarihi)
                VALUES (?, ?, ?, ?)
            ''', (ad_soyad, telefon if telefon else None, eposta if eposta else None, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            self.conn.commit()
            
            top.destroy()
            self.load_musteriler()
            messagebox.showinfo("Bilgi", "Müşteri başarıyla eklendi.")
        
        top = tk.Toplevel(self.root)
        top.title("Yeni Müşteri Ekle")
        
        ttk.Label(top, text="Ad Soyad:").pack(pady=5)
        entry_ad = ttk.Entry(top)
        entry_ad.pack(pady=5)
        
        ttk.Label(top, text="Telefon:").pack(pady=5)
        entry_tel = ttk.Entry(top)
        entry_tel.pack(pady=5)
        
        ttk.Label(top, text="E-posta:").pack(pady=5)
        entry_eposta = ttk.Entry(top)
        entry_eposta.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_musteri).pack(pady=10)
    
    def musteri_duzenle(self):
        selected = self.musteri_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen düzenlemek istediğiniz müşteriyi seçin!")
            return
        
        item = self.musteri_tree.item(selected[0])
        musteri_id, ad_soyad, telefon, eposta, _ = item['values']
        
        def save_changes():
            new_ad = entry_ad.get()
            new_tel = entry_tel.get()
            new_eposta = entry_eposta.get()
            
            if not new_ad:
                messagebox.showwarning("Uyarı", "Ad soyad boş olamaz!")
                return
            
            self.cursor.execute('''
                UPDATE musteriler
                SET ad_soyad = ?, telefon = ?, eposta = ?
                WHERE musteri_id = ?
            ''', (new_ad, new_tel if new_tel else None, new_eposta if new_eposta else None, musteri_id))
            self.conn.commit()
            
            top.destroy()
            self.load_musteriler()
            messagebox.showinfo("Bilgi", "Müşteri başarıyla güncellendi.")
        
        top = tk.Toplevel(self.root)
        top.title("Müşteri Düzenle")
        
        ttk.Label(top, text="Ad Soyad:").pack(pady=5)
        entry_ad = ttk.Entry(top)
        entry_ad.insert(0, ad_soyad)
        entry_ad.pack(pady=5)
        
        ttk.Label(top, text="Telefon:").pack(pady=5)
        entry_tel = ttk.Entry(top)
        entry_tel.insert(0, telefon if telefon != "-" else "")
        entry_tel.pack(pady=5)
        
        ttk.Label(top, text="E-posta:").pack(pady=5)
        entry_eposta = ttk.Entry(top)
        entry_eposta.insert(0, eposta if eposta != "-" else "")
        entry_eposta.pack(pady=5)
        
        ttk.Button(top, text="Kaydet", command=save_changes).pack(pady=10)
    
    def musteri_sil(self):
        selected = self.musteri_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen silmek istediğiniz müşteriyi seçin!")
            return
        
        item = self.musteri_tree.item(selected[0])
        musteri_id, ad_soyad, _, _, _ = item['values']
        
        # Müşterinin aktif adisyonu var mı kontrol et
        self.cursor.execute('''
            SELECT COUNT(*) FROM masalar WHERE musteri_adi = ?
        ''', (ad_soyad,))
        count = self.cursor.fetchone()[0]
        
        if count > 0:
            messagebox.showwarning("Uyarı", "Bu müşteriye ait aktif masa bulunuyor. Önce masalardaki müşteri bilgisini kaldırın.")
            return
        
        if messagebox.askyesno("Onay", f"'{ad_soyad}' adlı müşteriyi silmek istediğinize emin misiniz?"):
            self.cursor.execute("DELETE FROM musteriler WHERE musteri_id=?", (musteri_id,))
            self.conn.commit()
            self.load_musteriler()
            messagebox.showinfo("Bilgi", "Müşteri başarıyla silindi.")
    
    def create_raporlar_tab(self):
        # Rapor tarih aralığı
        date_frame = ttk.Frame(self.raporlar_frame)
        date_frame.pack(pady=10)
        
        ttk.Label(date_frame, text="Başlangıç:").pack(side='left')
        self.baslangic_tarih = ttk.Entry(date_frame, width=10)
        self.baslangic_tarih.pack(side='left', padx=5)
        self.baslangic_tarih.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Label(date_frame, text="Bitiş:").pack(side='left', padx=5)
        self.bitis_tarih = ttk.Entry(date_frame, width=10)
        self.bitis_tarih.pack(side='left', padx=5)
        self.bitis_tarih.insert(0, datetime.now().strftime('%Y-%m-%d'))
        
        ttk.Button(date_frame, text="Raporu Göster", command=self.load_rapor).pack(side='left', padx=5)
        
        # Rapor treeview
        columns = ('tarih', 'toplam', 'masa_sayisi', 'urun_sayisi')
        self.rapor_tree = ttk.Treeview(self.raporlar_frame, columns=columns, show='headings')
        
        self.rapor_tree.heading('tarih', text='Tarih')
        self.rapor_tree.heading('toplam', text='Toplam Ciro')
        self.rapor_tree.heading('masa_sayisi', text='Masa Sayısı')
        self.rapor_tree.heading('urun_sayisi', text='Ürün Sayısı')
        
        self.rapor_tree.column('tarih', width=100)
        self.rapor_tree.column('toplam', width=100, anchor='e')
        self.rapor_tree.column('masa_sayisi', width=100, anchor='center')
        self.rapor_tree.column('urun_sayisi', width=100, anchor='center')
        
        self.rapor_tree.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Detay frame
        self.rapor_detay_frame = ttk.Frame(self.raporlar_frame)
        self.rapor_detay_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Başlangıçta bugünün raporunu yükle
        self.load_rapor()
    
    def load_rapor(self):
        # Önceki raporu temizle
        for item in self.rapor_tree.get_children():
            self.rapor_tree.delete(item)
        
        # Detay frame'i temizle
        for widget in self.rapor_detay_frame.winfo_children():
            widget.destroy()
        
        baslangic = self.baslangic_tarih.get()
        bitis = self.bitis_tarih.get()
        
        try:
            baslangic_date = datetime.strptime(baslangic, '%Y-%m-%d')
            bitis_date = datetime.strptime(bitis, '%Y-%m-%d')
            
            if baslangic_date > bitis_date:
                messagebox.showwarning("Uyarı", "Başlangıç tarihi bitiş tarihinden büyük olamaz!")
                return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir tarih formatı girin (YYYY-MM-DD)!")
            return
        
        # Günlük raporları al
        self.cursor.execute('''
            SELECT 
                DATE(a.kapanis_zamani) AS tarih,
                SUM(a.toplam_tutar) AS toplam,
                COUNT(DISTINCT a.masa_id) AS masa_sayisi,
                SUM(ad.adet) AS urun_sayisi
            FROM adisyonlar a
            JOIN adisyon_detay ad ON a.adisyon_id = ad.adisyon_id
            WHERE 
                a.odeme_durumu = 'kapali' AND
                ad.islem_tipi = 'ekleme' AND
                DATE(a.kapanis_zamani) BETWEEN ? AND ?
            GROUP BY DATE(a.kapanis_zamani)
            ORDER BY DATE(a.kapanis_zamani)
        ''', (baslangic, bitis))
        
        raporlar = self.cursor.fetchall()
        
        if not raporlar:
            ttk.Label(self.rapor_detay_frame, text="Seçilen tarih aralığında rapor bulunamadı.").pack(pady=20)
            return
        
        for tarih, toplam, masa_sayisi, urun_sayisi in raporlar:
            self.rapor_tree.insert('', 'end', values=(
                tarih,
                f"{toplam:.2f} TL" if toplam else "0.00 TL",
                masa_sayisi,
                urun_sayisi
            ), iid=tarih)
        
        # İlk raporun detayını göster
        if raporlar:
            self.show_rapor_detay(raporlar[0][0])
        
        # Tıklama olayı
        self.rapor_tree.bind('<<TreeviewSelect>>', lambda e: self.show_rapor_detay(self.rapor_tree.selection()[0]))
    
    def show_rapor_detay(self, tarih):
        # Detay frame'i temizle
        for widget in self.rapor_detay_frame.winfo_children():
            widget.destroy()
        
        # Adisyonları al
        self.cursor.execute('''
            SELECT 
                a.adisyon_id,
                a.masa_id,
                m.masa_adi,
                a.toplam_tutar,
                TIME(a.kapanis_zamani) AS saat
            FROM adisyonlar a
            JOIN masalar m ON a.masa_id = m.masa_id
            WHERE 
                a.odeme_durumu = 'kapali' AND
                DATE(a.kapanis_zamani) = ?
            ORDER BY a.kapanis_zamani
        ''', (tarih,))
        
        adisyonlar = self.cursor.fetchall()
        
        if not adisyonlar:
            ttk.Label(self.rapor_detay_frame, text="Bu tarihe ait detay bulunamadı.").pack(pady=20)
            return
        
        # Toplam bilgisi
        toplam_frame = ttk.Frame(self.rapor_detay_frame)
        toplam_frame.pack(fill='x', pady=5)
        
        toplam_tutar = sum(a[3] for a in adisyonlar)
        ttk.Label(toplam_frame, text=f"Toplam Ciro: {toplam_tutar:.2f} TL", font=('Arial', 10, 'bold')).pack(side='left')
        
        # Adisyon listesi
        list_frame = ttk.Frame(self.rapor_detay_frame)
        list_frame.pack(fill='both', expand=True)
        
        columns = ('masa', 'saat', 'tutar')
        detay_tree = ttk.Treeview(list_frame, columns=columns, show='headings')
        
        detay_tree.heading('masa', text='Masa')
        detay_tree.heading('saat', text='Saat')
        detay_tree.heading('tutar', text='Tutar')
        
        detay_tree.column('masa', width=150)
        detay_tree.column('saat', width=100, anchor='center')
        detay_tree.column('tutar', width=100, anchor='e')
        
        detay_tree.pack(fill='both', expand=True)
        
        for adisyon_id, masa_id, masa_adi, tutar, saat in adisyonlar:
            masa_text = f"Masa {masa_id}"
            if masa_adi:
                masa_text += f" ({masa_adi})"
            
            detay_tree.insert('', 'end', values=(
                masa_text,
                saat,
                f"{tutar:.2f} TL"
            ), iid=adisyon_id)
        
        # Ürün satışları
        ttk.Label(self.rapor_detay_frame, text="En Çok Satılan Ürünler", font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.cursor.execute('''
            SELECT 
                u.urun_adi,
                SUM(ad.adet) AS toplam_adet,
                SUM(ad.adet * ad.fiyat) AS toplam_tutar
            FROM adisyon_detay ad
            JOIN urunler u ON ad.urun_id = u.urun_id
            JOIN adisyonlar a ON ad.adisyon_id = a.adisyon_id
            WHERE 
                ad.islem_tipi = 'ekleme' AND
                a.odeme_durumu = 'kapali' AND
                DATE(a.kapanis_zamani) = ?
            GROUP BY u.urun_adi
            ORDER BY toplam_adet DESC
            LIMIT 5
        ''', (tarih,))
        
        urunler = self.cursor.fetchall()
        
        if urunler:
            urun_frame = ttk.Frame(self.rapor_detay_frame)
            urun_frame.pack(fill='x', pady=5)
            
            for i, (urun_adi, adet, tutar) in enumerate(urunler):
                ttk.Label(urun_frame, text=f"{i+1}. {urun_adi}: {adet} adet ({tutar:.2f} TL)").pack(anchor='w')
    
    def load_initial_data(self):
        # Başlangıçta bazı örnek veriler ekleyelim (tablolar boşsa)
        self.cursor.execute("SELECT COUNT(*) FROM kategoriler")
        if self.cursor.fetchone()[0] == 0:
            kategoriler = ['SICAK KAHVE', 'SOĞUK KAHVE', 'SOĞUK İÇECEK', 'TATLI', 'FRAPPE', 'MILK SHAKE']
            for kategori in kategoriler:
                self.cursor.execute("INSERT INTO kategoriler (kategori_adi) VALUES (?)", (kategori,))
            
            urunler = [
                ('LATTE', 'SICAK KAHVE', 110),
                ('ESPRESSO', 'SICAK KAHVE', 120),
                ('LATTE', 'SICAK KAHVE', 90),
                ('ICE WHITE MOCCA', 'SOĞUK KAHVE', 120),
                ('SU', 'SOĞUK İÇECEK', 20),
                ('SAN SEBASTİAN', 'TATLI', 80),
                ('KARAMELLI FRAPPE', 'FRAPPE', 100),
                ('KIRMIZI ORMAN', 'MILK SHAKE', 120)
            ]
            
            for urun_adi, kategori_adi, fiyat in urunler:
                self.cursor.execute("SELECT kategori_id FROM kategoriler WHERE kategori_adi=?", (kategori_adi,))
                kategori_id = self.cursor.fetchone()[0]
                self.cursor.execute("INSERT INTO urunler (urun_adi, kategori_id, fiyat) VALUES (?, ?, ?)", 
                                  (urun_adi, kategori_id, fiyat))
            
            self.conn.commit()
        
        # Örnek masalar ekleyelim
        self.cursor.execute("SELECT COUNT(*) FROM masalar")
        if self.cursor.fetchone()[0] == 0:
            for i in range(1, 11):
                self.cursor.execute("INSERT INTO masalar (masa_adi) VALUES (?)", (f"Masa {i}",))
            
            self.conn.commit()
    
    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()

if __name__ == "__main__":
    root = tk.Tk()
    app = KafeAdisyon(root)
    root.mainloop()
