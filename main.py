import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta # timedelta eklendi
import constants

# Diğer sekmelerin importları (MasaTab, AdisyonTab vb.)
from masa_tab import MasaTab
from adisyon_tab import AdisyonTab
# Diğer sekmelerin importları buraya eklenecek (UrunTab, MusterilerTab, RaporlarTab)
from urun_tab import UrunTab
from musteriler_tab import MusterilerTab
from raporlar_tab import RaporlarTab


class CafeAdisyonApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Late Adisyon Programs")
        self.root.geometry("1200x800") # Başlangıç pencere boyutu

        # Veritabanı bağlantısını başlat
        self.db_manager = DatabaseManager(constants.DB_NAME) # DB_NAME constants.py'den alınıyor
        self.db_manager.connect()
        self.db_manager.create_tables()
        self.db_manager.insert_default_data() # Varsayılan verileri ekle

        # Aktif masa ve sipariş bilgilerini sakla
        self.aktif_masa = None
        self.aktif_siparis_id = None
        # Masa silme modunu takip etmek için değişken
        self.delete_mode = False


        # Arayüz elementlerini oluştur
        self._create_widgets()
        # Stilleri yapılandır
        self._configure_styles()

        # Başlangıçta Masa sekmesini yükle
        self.notebook.select(0) # İlk sekme (Masalar) seçili gelsin
        self._on_tab_change(None) # İlk sekme için içeriği yükle


    def _create_widgets(self):
        """Ana arayüz elementlerini oluşturur."""
        # Notebook (Sekmeler) oluştur
        self.notebook = ttk.Notebook(self.root)
        # Notebook, ana pencerenin üst kısmında kalan tüm alanı kaplayacak
        # expand=True ve fill=tk.BOTH ile Notebook'un kalan tüm alanı doldurmasını sağla
        self.notebook.pack(pady=10, padx=10, expand=True, fill='both')

        # Sekmeleri oluştur ve Notebook'a ekle
        # MasaTab'a Masa Ekle/Sil butonları için referansları geçireceğiz
        self.masa_tab = MasaTab(self.notebook, self)
        self.adisyon_tab = AdisyonTab(self.notebook, self)
        # Diğer sekmeler
        self.urun_tab = UrunTab(self.notebook, self)
        self.musteriler_tab = MusterilerTab(self.notebook, self)
        self.raporlar_tab = RaporlarTab(self.notebook, self)


        # Sekme değiştirme olayını bağla
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        # Alt kontrol çerçevesi: Mevcut Zaman ve Masa Ekle/Sil butonlarını içerir
        # BU ÇERÇEVE ARTIK BURADA OLUŞTURULMUYOR VE PAKETLENMİYOR
        # bottom_control_frame = ttk.Frame(self.root, padding=(10, 0, 10, 10))
        # bottom_control_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Mevcut Zaman Etiketi (Alt kontrol çerçevesi içinde)
        # BU ETİKET ARTIK BURADA OLUŞTURULMUYOR VE PAKETLENMİYOR
        # self.lbl_mevcut_zaman = ttk.Label(bottom_control_frame, text="", font=('Arial', 10))
        # self.lbl_mevcut_zaman.pack(side=tk.LEFT)
        # self.update_clock() # Zamanı güncellemeye başla

        # Masa Ekle/Sil Butonları Alanı (Alt kontrol çerçevesi içinde)
        # BU ÇERÇEVE ARTIK BURADA OLUŞTURULMUYOR VE PAKETLENMİYOR
        # masa_kontrol_frame = ttk.Frame(bottom_control_frame)
        # masa_kontrol_frame.pack(side=tk.RIGHT)


        # Masa Ekle ve Masa Sil butonları (Masa kontrol çerçevesi içinde)
        # BU BUTONLAR ARTIK BURADA OLUŞTURULMUYOR VE PAKETLENMİYOR
        # ttk.Button(masa_kontrol_frame, text="Masa Ekle", command=self._add_masa).pack(side=tk.LEFT, padx=5)
        # self.btn_masa_sil = ttk.Button(masa_kontrol_frame, text="Masa Sil", command=self._delete_masa)
        # self.btn_masa_sil.pack(side=tk.LEFT, padx=5)


    def _configure_styles(self):
        """ttk widget stillerini yapılandırır."""
        style = ttk.Style()
        # Özel stilleri daha iyi destekleyen bir tema kullan
        style.theme_use('clam') # <<< Tema değiştirildi

        # Masa butonları için stiller (constants.py'deki MASA_STYLES'ı kullanır)
        style.configure('Boş.TButton', background=constants.MASA_STYLES['Boş']['bg'], foreground=constants.MASA_STYLES['Boş']['fg'])
        style.map('Boş.TButton',
                  background=[('active', constants.MASA_STYLES['Boş']['active_bg'])]) # Mouse üzerine gelince renk değişimi

        style.configure('Dolu.TButton', background=constants.MASA_STYLES['Dolu']['bg'], foreground=constants.MASA_STYLES['Dolu']['fg'])
        style.map('Dolu.TButton',
                  background=[('active', constants.MASA_STYLES['Dolu']['active_bg'])])

        style.configure('Ödeme Bekliyor.TButton', background=constants.MASA_STYLES['Ödeme Bekliyor']['bg'], foreground=constants.MASA_STYLES['Ödeme Bekliyor']['fg'])
        style.map('Ödeme Bekliyor.TButton',
                  background=[('active', constants.MASA_STYLES['Ödeme Bekliyor']['active_bg'])])

        # Yeni Geçikmiş masa stili tanımlandı
        style.configure('Geçikmiş.TButton', background=constants.MASA_STYLES['Geçikmiş']['bg'], foreground=constants.MASA_STYLES['Geçikmiş']['fg']) # <<< Yeni stil tanımlandı
        style.map('Geçikmiş.TButton',
                  background=[('active', constants.MASA_STYLES['Geçikmiş']['active_bg'])]) # <<< Yeni stil maplendi


        # Adisyon butonları için stil
        style.configure('Adisyon.TButton', background='#f0f0f0', foreground='black') # Açık gri arka plan
        style.map('Adisyon.TButton',
                  background=[('active', '#e0e0e0')]) # Mouse üzerine gelince daha koyu gri

        # Ödeme butonları için stil
        style.configure('Odeme.TButton', background='#d9edf7', foreground='#042a38') # Açık mavi arka plan
        style.map('Odeme.TButton',
                  background=[('active', '#c0e3f3')]) # Mouse üzerine gelince daha koyu mavi

        # Hızlı Satış butonları için genel stil (kategori stilleri üzerine yazabilir)
        style.configure('HizliSatis.TButton', font=('Arial', 9)) # Yazı tipi boyutu

        # Kategoriye özel hızlı satış buton stilleri (constants.py'deki CATEGORY_COLORS'ı kullanır)
        for kategori, colors in constants.CATEGORY_COLORS.items():
            style_name = f"{kategori}.HizliSatis.TButton"
            style.configure(style_name, background=colors['bg'], foreground=colors['fg'])
            style.map(style_name,
                      background=[('active', colors['active_bg'])]) # Mouse üzerine gelince renk değişimi

        # Varsayılan hızlı satış butonu stili (kategorisi olmayanlar için)
        style.configure('default.HizliSatis.TButton', background='#cccccc', foreground='black') # Gri arka plan
        style.map('default.HizliSatis.TButton',
                  background=[('active', '#bbbbbb')])

        # Masa tabında seçili masa butonu için stil
        style.configure('Selected.TButton', borderwidth=3, relief="solid", background="yellow") # Örnek stil


    def update_clock(self):
        """Mevcut zaman etiketini günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # self.lbl_mevcut_zaman artık burada tanımlı değil, MasaTab içinde olacak.
        # Bu metot MasaTab'dan çağrılmalı ve MasaTab'daki etiketi güncellemelidir.
        # En iyisi MasaTab'ın kendi saat güncelleme mekanizmasını oluşturmak.
        pass # <<< Metot boşaltıldı


    def _on_tab_change(self, event):
        """Sekme değiştiğinde ilgili sekmenin içeriğini yükler."""
        selected_tab_index = self.notebook.index(self.notebook.select())
        #print(f"Sekme değişti: {selected_tab_index}") # Debug

        # Sekme değiştiğinde Masa Silme modunu kapat
        self.delete_mode = False
        # self.btn_masa_sil artık burada tanımlı değil, MasaTab içinde olacak.
        # MasaTab'a modu kapatma ve buton metnini sıfırlama bilgisini iletmeliyiz.
        self.masa_tab.exit_delete_mode() # <<< MasaTab'a yeni metot çağrısı

        # Masa tabında seçili masa varsa stilini sıfırla
        self.masa_tab._reset_selected_masa_button_style() # MasaTab'daki metot çağrıldı


        if selected_tab_index == 0: # Masalar sekmesi
            self.masa_tab.load_masa_buttons()
            # Masa sekmesine dönüldüğünde geçikmiş masa kontrolünü başlat
            self.masa_tab.start_late_table_check() # <<< Yeni metot çağrısı
        elif selected_tab_index == 1: # Adisyon sekmesi
            # Adisyon sekmesine geçildiğinde aktif masa seçili ise sepeti yükle
            if self.aktif_masa is not None:
                self.adisyon_tab.load_cart()
            else:
                 self.adisyon_tab._clear_cart_ui() # Aktif masa yoksa sepeti temizle
            # Kategori combobox'ını yükle
            categories = self.db_manager.get_all_categories()
            categories_with_all = ["Tümü"] + [cat['adi'] for cat in categories]
            self.adisyon_tab.load_categories_combobox(categories_with_all)
            # Hızlı satış butonlarını yükle (veya filtrele)
            self.adisyon_tab.filter_hizli_satis_buttons()
            # Adisyon sekmesindeyken geçikmiş masa kontrolünü durdur
            self.masa_tab.stop_late_table_check() # <<< Yeni metot çağrısı


        # Diğer sekmeler için yükleme fonksiyonları buraya eklenebilir
        elif selected_tab_index == 2: # Ürünler sekmesi
             self.urun_tab.load_products()
             categories = self.db_manager.get_all_categories()
             category_names = [cat['adi'] for cat in categories]
             # UrunTab.load_categories_combobox metodu 'categories_with_none' adında bir argüman bekliyor.
             # Bu argüman büyük olasılıkla kategori listesini ve 'Yok' veya 'Tümü' gibi bir seçeneği içeriyor.
             # Adisyon sekmesindeki gibi 'Tümü' seçeneği ekleyelim ve argüman adını düzeltelim.
             categories_with_none = ["Tümü"] + category_names # 'Tümü' seçeneğini ekle
             # Eğer UrunTab 'Yok' gibi bir seçenek istiyorsa burayı düzenlememiz gerekebilir.
             # Şimdilik 'Tümü' ile deneyelim.
             # Argüman adını 'categories_with_none' olarak düzeltiyoruz.
             self.urun_tab.load_categories_combobox(categories_with_none)
             # Ürünler sekmesindeyken geçikmiş masa kontrolünü durdur
             self.masa_tab.stop_late_table_check() # <<< Yeni metot çağrısı


        elif selected_tab_index == 3: # Müşteriler sekmesi
             # Müşteriler sekmesi için load fonksiyonu çağrılabilir
             pass
             # Müşteriler sekmesindeyken geçikmiş masa kontrolünü durdur
             self.masa_tab.stop_late_table_check() # <<< Yeni metot çağrısı

        elif selected_tab_index == 4: # Raporlar sekmesi
             # Raporlar sekmesi için load fonksiyonu çağrılabilir
             pass
             # Raporlar sekmesindeyken geçikmiş masa kontrolünü durdur
             self.masa_tab.stop_late_table_check() # <<< Yeni metot çağrısı


    def select_masa(self, masa_no):
        """Masa sekmesinden bir masa seçildiğinde çağrılır."""
        self.aktif_masa = masa_no
        self.adisyon_tab.lbl_aktif_masa.config(text=f"Masa {masa_no}")
        print(f"Aktif Masa Ayarlandı: Masa {self.aktif_masa}") # Debug

        # Seçilen masanın aktif siparişi var mı kontrol et
        try:
            db = self.db_manager
            db.cursor.execute("SELECT aktif_siparis_id FROM masalar WHERE masa_no = ?", (self.aktif_masa,))
            result = db.cursor.fetchone()
            # Sütun adı 'aktif_siparis_id' olmalı
            if result and result['aktif_siparis_id']:
                self.aktif_siparis_id = result['aktif_siparis_id']
                print(f"Aktif Sipariş ID: {self.aktif_siparis_id}") # Debug
            else:
                self.aktif_siparis_id = None
                print("Aktif Sipariş Yok.") # Debug

            # Adisyon sekmesine geç ve sepeti yükle
            self.notebook.select(1) # Adisyon sekmesi 1. indekste
            # Sepet yükleme _on_tab_change metodunda yapılacak

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masa seçilirken sipariş bilgisi alınamadı: {e}")


    def _add_masa(self):
        """Yeni bir masa ekler (main.py'de)."""
        # Eğer silme modundaysak, masa ekleme işlemini yapma
        if self.delete_mode:
            messagebox.showwarning("Uyarı", "Masa silme modu aktif. Lütfen önce modu kapatın veya bir masa seçin.")
            return

        try:
            db = self.db_manager
            # Son masa numarasını bul
            db.cursor.execute("SELECT MAX(masa_no) FROM masalar")
            last_masa_no = db.cursor.fetchone()[0]
            next_masa_no = (last_masa_no or 0) + 1 # Eğer hiç masa yoksa 1'den başla

            # Veritabanına yeni masa ekle
            db.cursor.execute("INSERT INTO masalar (masa_no) VALUES (?)", (next_masa_no,))
            db.conn.commit()
            messagebox.showinfo("Başarılı", f"Masa {next_masa_no} başarıyla eklendi.")

            # Masa listesini ve butonları MasaTab üzerinden yeniden yükle
            # Bu, MasaTab'ın arayüzünü gü ncelleyecektir.
            self.masa_tab.load_masa_buttons()

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Yeni masa eklenirken hata oluştu: {e}")
            db.conn.rollback()

    def _delete_masa(self):
        """Masa silme modunu açar/kapatır."""
        # Masa silme modunu toggle et
        self.delete_mode = not self.delete_mode

        # Buton metnini ve görünümünü MasaTab üzerinden güncelle
        self.masa_tab.update_delete_button_text(self.delete_mode) # <<< MasaTab'a yeni metot çağrısı

        if self.delete_mode:
            messagebox.showinfo("Bilgi", "Silmek istediğiniz masaya tıklayın.")
        # else: Masa silme modu kapatıldığında MasaTab içindeki stil sıfırlanacak


    def _perform_delete_masa(self, masa_no):
        """Seçili masayı silme işlemini gerçekleştirir."""
        # Masa silme modunu kapat
        self.delete_mode = False
        # Buton metnini ve görünümünü MasaTab üzerinden güncelle
        self.masa_tab.update_delete_button_text(self.delete_mode) # <<< MasaTab'a yeni metot çağrısı

        # MasaTab'daki seçili masa bilgisini sıfırla ve stilini geri yükle
        self.masa_tab._reset_selected_masa_button_style()


        if masa_no is None:
            # Bu durum normalde _on_masa_button_click'ten doğru masa no gelirse oluşmamalı
            messagebox.showwarning("Uyarı", "Silinecek masa belirlenemedi.")
            return

        # Seçili masanın durumunu kontrol et (sadece boş masalar silinebilir)
        try:
            db = self.db_manager
            db.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,))
            masa_durum = db.cursor.fetchone()['durum']

            if masa_durum != 'Boş':
                messagebox.showwarning("Uyarı", f"Sadece boş masalar silinebilir. Masa {masa_no} durumu: {masa_durum}")
                return

            # Kullanıcıdan silme onayı al
            if messagebox.askyesno("Onay", f"Masa {masa_no} silmek istediğinizden emin misiniz? Bu işlem geri alınamaz."):
                # Veritabanından masayı sil
                db.cursor.execute("DELETE FROM masalar WHERE masa_no = ?", (masa_no,))
                db.conn.commit()
                messagebox.showinfo("Başarılı", f"Masa {masa_no} başarıyla silindi.")

                # Masa listesini ve butonları MasaTab üzerinden yeniden yükle
                self.masa_tab.load_masa_buttons()

                # Eğer silinen masa aktif masa ise, aktif masa bilgisini sıfırla
                if self.aktif_masa == masa_no:
                     self.aktif_masa = None
                     self.aktif_siparis_id = None
                     self.adisyon_tab.lbl_aktif_masa.config(text="Seçilmedi")
                     self.adisyon_tab._clear_cart_ui() # Sepeti de temizle

            else:
                messagebox.showinfo("Bilgi", "Silme işlemi iptal edildi.")


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masa silinirken hata oluştu: {e}")
            db.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Masa silinirken beklenmedik hata oluştu: {e}")


class DatabaseManager:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Veritabanı bağlantısını kurar."""
        try:
            self.conn = sqlite3.connect(self.db_name)
            # Sorgu sonuçlarına sütun isimleriyle erişmek için
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            print("Veritabanı bağlantısı başarılı.")
        except sqlite3.Error as e:
            print(f"Veritabanı bağlantı hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Veritabanına bağlanılamadı: {e}")


    def close(self):
        """Veritabanı bağlantısını kapatır."""
        if self.conn:
            self.conn.close()
            print("Veritabanı bağlantısı kapatıldı.")

    def create_tables(self):
        """Gerekli veritabanı tablolarını oluşturur."""
        try:
            # Masalar tablosu
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS masalar (
                    masa_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER UNIQUE NOT NULL,
                    durum TEXT DEFAULT 'Boş', -- 'Boş', 'Dolu', 'Ödeme Bekliyor', 'Geçikmiş' <<< 'Geçikmiş' eklendi
                    aktif_siparis_id INTEGER, -- O anki aktif siparişin ID'si
                    guncel_toplam REAL DEFAULT 0.0,
                    iskonto REAL DEFAULT 0.0,
                    FOREIGN KEY (aktif_siparis_id) REFERENCES siparis_gecmisi(siparis_id)
                );
            """)

            # Kategoriler tablosu
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS kategoriler (
                    kategori_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adi TEXT UNIQUE NOT NULL
                );
            """)

            # Ürünler tablosu
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS urunler (
                    urun_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adi TEXT UNIQUE NOT NULL,
                    fiyat REAL NOT NULL,
                    kategori_id INTEGER,
                    aktif_durumu BOOLEAN DEFAULT 1, -- 1: Aktif, 0: Pasif
                    hizli_satis_sirasi INTEGER, -- Hızlı satış ekranındaki sıralama
                    FOREIGN KEY (kategori_id) REFERENCES kategoriler(kategori_id)
                );
            """)

            # Sipariş Geçmişi tablosu (Adisyonlar)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS siparis_gecmisi (
                    siparis_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    masa_no INTEGER NOT NULL,
                    acilis_zamani TEXT NOT NULL,
                    kapanis_zamani TEXT,
                    durum TEXT DEFAULT 'Açık', -- 'Açık', 'Kapandı', 'İptal Edildi'
                    toplam_tutar REAL DEFAULT 0.0, -- Kapanış anındaki toplam tutar (iskontolu)
                    iskonto REAL DEFAULT 0.0,
                    odeme_yontemi TEXT, -- 'Nakit', 'Kart', vb.
                    son_islem_zamani TEXT -- <<< Yeni sütun eklendi
                );
            """)

            # Sipariş Detayları tablosu (Adisyondaki ürünler)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS siparis_detaylari (
                    detay_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    siparis_id INTEGER NOT NULL,
                    urun_id INTEGER NOT NULL,
                    urun_adi TEXT NOT NULL, -- Ürün adı (raporlama kolaylığı için saklanıyor)
                    miktar REAL NOT NULL,
                    birim_fiyat REAL NOT NULL,
                    tutar REAL NOT NULL, -- Miktar * Birim Fiyat
                    kategori_id INTEGER, -- Ürün kategori ID'si (raporlama kolaylığı için saklanıyor)
                    FOREIGN KEY (siparis_id) REFERENCES siparis_gecmisi(siparis_id),
                    FOREIGN KEY (urun_id) REFERENCES urunler(urun_id),
                    FOREIGN KEY (kategori_id) REFERENCES kategoriler(kategori_id)
                );
            """)

            self.conn.commit()
            print("Veritabanı tabloları kontrol edildi/oluşturuldu.")
        except sqlite3.Error as e:
            print(f"Veritabanı tablo oluşturma hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Veritabanı tabloları oluşturulurken hata oluştu: {e}")


    def insert_default_data(self):
        """Uygulama ilk çalıştığında varsayılan verileri ekler."""
        try:
            # Varsayılan masalar (sadece eğer hiç masa yoksa)
            self.cursor.execute("SELECT COUNT(*) FROM masalar")
            if self.cursor.fetchone()[0] == 0:
                for i in range(1, 11): # 10 tane varsayılan masa
                    self.cursor.execute("INSERT INTO masalar (masa_no) VALUES (?)", (i,))
                self.conn.commit()
                print("Varsayılan masalar eklendi.")

            # Varsayılan kategoriler (sadece eğer hiç kategori yoksa)
            self.cursor.execute("SELECT COUNT(*) FROM kategoriler")
            if self.cursor.fetchone()[0] == 0:
                # constants.py'deki DEFAULT_CATEGORIES listesini kullan
                kategoriler = [(cat,) for cat in constants.DEFAULT_CATEGORIES] # Tuple listesi oluştur
                self.cursor.executemany("INSERT INTO kategoriler (adi) VALUES (?)", kategoriler)
                self.conn.commit()
                print("Varsayılan kategoriler eklendi.")

            # Varsayılan ürünler (sadece eğer hiç ürün yoksa)
            self.cursor.execute("SELECT COUNT(*) FROM urunler")
            if self.cursor.fetchone()[0] == 0:
                # Kategori ID'lerini al
                self.cursor.execute("SELECT kategori_id, adi FROM kategoriler")
                kategori_map = {row['adi']: row['kategori_id'] for row in self.cursor.fetchall()}

                # constants.py'deki DEFAULT_PRODUCTS listesini kullan
                urunler_to_insert = []
                for urun_info in constants.DEFAULT_PRODUCTS:
                    adi, fiyat, kategori_adi, aktif_durumu, hizli_satis_sirasi = urun_info
                    kategori_id = kategori_map.get(kategori_adi) # Kategori adına göre ID'yi bul
                    urunler_to_insert.append((adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi))

                self.cursor.executemany("INSERT INTO urunler (adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi) VALUES (?, ?, ?, ?, ?)", urunler_to_insert)
                self.conn.commit()
                print("Varsayılan ürünler eklendi.")

        except sqlite3.Error as e:
            print(f"Veritabanı varsayılan veri ekleme hatası: {e}")
            messagebox.showerror("Veritabanı Hatası", f"Varsayılan veriler eklenirken hata oluştu: {e}")

    def get_all_categories(self):
        """Tüm kategorileri veritabanından çeker."""
        try:
            self.cursor.execute("SELECT kategori_id, adi FROM kategoriler ORDER BY adi")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Kategori çekme hatası: {e}")
            return []


if __name__ == "__main__":
    root = tk.Tk()
    app = CafeAdisyonApp(root)
    root.mainloop()