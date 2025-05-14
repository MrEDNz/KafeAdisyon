import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class UrunTab:
    def __init__(self, parent_notebook, app):
        self.app = app
        self.frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(self.frame, text="Ürünler")

        self._create_ui()
        self.load_products() # Ürünleri başlangıçta yükle

    def _create_ui(self):
        """Ürünler sekmesi arayüzünü oluşturur."""
        # Ürün Yönetimi Başlığı
        lbl_title = ttk.Label(self.frame, text="Ürün Yönetimi", font=('Arial', 14, 'bold'))
        lbl_title.pack(pady=10)

        # Ürün Formu Alanı
        form_frame = ttk.LabelFrame(self.frame, text="Ürün Bilgileri", padding="10")
        form_frame.pack(fill=tk.X, pady=5)

        # Ürün Adı
        ttk.Label(form_frame, text="Ürün Adı:").grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_urun_adi = ttk.Entry(form_frame, width=40)
        self.entry_urun_adi.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        # Ürün Fiyatı
        ttk.Label(form_frame, text="Fiyat:").grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_urun_fiyat = ttk.Entry(form_frame, width=20)
        self.entry_urun_fiyat.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)

        # Ürün Kategorisi Combobox
        ttk.Label(form_frame, text="Kategori:").grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        self.cmb_urun_kategori = ttk.Combobox(form_frame, width=37, state='readonly')
        self.cmb_urun_kategori.grid(row=2, column=1, sticky=tk.W, pady=2, padx=5)
        # Kategori Combobox verileri main.py'den _on_tab_change metodu ile yüklenecek

        # Aktif Durumu Checkbutton
        ttk.Label(form_frame, text="Aktif:").grid(row=3, column=0, sticky=tk.W, pady=2, padx=5)
        self.var_aktif_durum = tk.BooleanVar(value=True) # Varsayılan olarak aktif
        # Yazım hatası düzeltildi: var_aktif_durumu -> var_aktif_durum
        chk_aktif_durum = ttk.Checkbutton(form_frame, variable=self.var_aktif_durum) # <<< Düzeltildi
        chk_aktif_durum.grid(row=3, column=1, sticky=tk.W, pady=2, padx=5)

        # Hızlı Satış Sırası
        ttk.Label(form_frame, text="Hızlı Satış Sırası:").grid(row=4, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_hizli_satis_sirasi = ttk.Entry(form_frame, width=10)
        self.entry_hizli_satis_sirasi.grid(row=4, column=1, sticky=tk.W, pady=2, padx=5)
        self.entry_hizli_satis_sirasi.insert(0, "0") # Varsayılan 0 (hızlı satışta yok)


        # Butonlar
        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Ürün Ekle", command=self.add_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ürün Güncelle", command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Ürün Sil", command=self.delete_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Formu Temizle", command=self.clear_form).pack(side=tk.LEFT, padx=5)


        # Ürün Listesi Alanı (Treeview)
        list_frame = ttk.LabelFrame(self.frame, text="Ürün Listesi", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Treeview ve Scrollbar
        self.tree_urunler = ttk.Treeview(list_frame, columns=("ID", "Adı", "Fiyat", "Kategori", "Aktif", "Hızlı Satış Sırası"), show="headings")
        self.tree_urunler.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree_urunler.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_urunler.configure(yscrollcommand=scrollbar.set)

        # Sütun Başlıkları
        self.tree_urunler.heading("ID", text="ID")
        self.tree_urunler.heading("Adı", text="Adı")
        self.tree_urunler.heading("Fiyat", text="Fiyat")
        self.tree_urunler.heading("Kategori", text="Kategori")
        self.tree_urunler.heading("Aktif", text="Aktif")
        self.tree_urunler.heading("Hızlı Satış Sırası", text="Hızlı Satış Sırası")

        # Sütun Genişlikleri (Ayarlanabilir)
        self.tree_urunler.column("ID", width=40, anchor=tk.CENTER)
        self.tree_urunler.column("Adı", width=150)
        self.tree_urunler.column("Fiyat", width=80, anchor=tk.E)
        self.tree_urunler.column("Kategori", width=100)
        self.tree_urunler.column("Aktif", width=60, anchor=tk.CENTER)
        self.tree_urunler.column("Hızlı Satış Sırası", width=100, anchor=tk.CENTER)

        # Treeview'de bir ürün seçildiğinde formu doldur
        self.tree_urunler.bind("<<TreeviewSelect>>", self.on_urun_select)


    def load_categories_combobox(self, categories_with_none):
        """Ürün formundaki kategori Combobox'ını günceller."""
        # Metot artık sadece 'categories_with_none' argümanını kabul ediyor.
        self.cmb_urun_kategori['values'] = categories_with_none
        self.cmb_urun_kategori.set("Kategori Yok") # Varsayılan değer


    def load_products(self):
        """Veritabanından ürünleri çeker ve Treeview'e yükler."""
        # Treeview'i temizle
        for item in self.tree_urunler.get_children():
            self.tree_urunler.delete(item)

        try:
            # Ürünleri ve kategori adlarını çekmek için JOIN kullan
            self.app.db_manager.cursor.execute("""
                SELECT u.urun_id, u.adi, u.fiyat, k.adi AS kategori_adi, u.aktif_durumu, u.hizli_satis_sirasi
                FROM urunler u
                LEFT JOIN kategoriler k ON u.kategori_id = k.kategori_id
                ORDER BY u.urun_id
            """)
            urunler = self.app.db_manager.cursor.fetchall()

            for urun in urunler:
                # Aktif durumu 'Evet' veya 'Hayır' olarak göster
                aktif_durum_text = "Evet" if urun['aktif_durumu'] else "Hayır"
                # Kategori adı None ise 'Yok' olarak göster
                kategori_adi_text = urun['kategori_adi'] if urun['kategori_adi'] is not None else "Yok"

                self.tree_urunler.insert("", tk.END, values=(
                    urun['urun_id'],
                    urun['adi'],
                    f"{urun['fiyat']:.2f}", # Fiyatı formatla
                    kategori_adi_text,
                    aktif_durum_text,
                    urun['hizli_satis_sirasi']
                ))
                # Debug çıktısı
                # print(f"DEBUG: Treeview values: {self.tree_urunler.item(self.tree_urunler.get_children()[-1], 'values')}")


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürünler yüklenirken hata oluştu: {e}")
        except Exception as e:
             messagebox.showerror("Hata", f"Ürünler yüklenirken beklenmedik hata oluştu: {e}")


    def on_urun_select(self, event):
        """Treeview'de bir ürün seçildiğinde form alanlarını doldurur."""
        selected_item = self.tree_urunler.focus() # Seçili öğenin iid'sini al
        if not selected_item:
            self.clear_form() # Seçim kalkarsa formu temizle
            return

        # Seçili öğenin değerlerini al
        values = self.tree_urunler.item(selected_item, 'values')

        # Form alanlarını doldur
        self.entry_urun_adi.delete(0, tk.END)
        self.entry_urun_adi.insert(0, values[1]) # Adı

        self.entry_urun_fiyat.delete(0, tk.END)
        self.entry_urun_fiyat.insert(0, values[2]) # Fiyatı

        # Kategori Combobox'ı ayarla
        kategori_adi = values[3]
        if kategori_adi == "Yok":
            self.cmb_urun_kategori.set("Kategori Yok")
        else:
            self.cmb_urun_kategori.set(kategori_adi)

        # Aktif durumu ayarla
        aktif_durum_text = values[4]
        # Yazım hatası düzeltildi: var_aktif_durumu -> var_aktif_durum
        self.var_aktif_durum.set(aktif_durum_text == "Evet") # <<< Düzeltildi

        # Hızlı satış sırasını ayarla
        self.entry_hizli_satis_sirasi.delete(0, tk.END)
        self.entry_hizli_satis_sirasi.insert(0, values[5])


    def add_product(self):
        """Yeni ürün ekler."""
        adi = self.entry_urun_adi.get().strip()
        fiyat_str = self.entry_urun_fiyat.get().strip()
        kategori_adi = self.cmb_urun_kategori.get()
        aktif_durumu = self.var_aktif_durum.get() # <<< Düzeltildi
        hizli_satis_sirasi_str = self.entry_hizli_satis_sirasi.get().strip()

        if not adi or not fiyat_str:
            messagebox.showwarning("Uyarı", "Ürün Adı ve Fiyat boş bırakılamaz.")
            return

        try:
            fiyat = float(fiyat_str)
            if fiyat < 0:
                 messagebox.showwarning("Uyarı", "Fiyat negatif olamaz.")
                 return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir fiyat girin.")
            return

        try:
             hizli_satis_sirasi = int(hizli_satis_sirasi_str)
             if hizli_satis_sirasi < 0:
                  messagebox.showwarning("Uyarı", "Hızlı Satış Sırası negatif olamaz.")
                  return
        except ValueError:
             messagebox.showwarning("Uyarı", "Geçerli bir hızlı satış sırası girin.")
             return


        # Kategori adına göre kategori_id'yi bul
        kategori_id = None
        if kategori_adi and kategori_adi != "Kategori Yok":
            try:
                self.app.db_manager.cursor.execute("SELECT kategori_id FROM kategoriler WHERE adi = ?", (kategori_adi,))
                result = self.app.db_manager.cursor.fetchone()
                if result:
                    kategori_id = result['kategori_id']
            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Kategori ID çekilirken hata oluştu: {e}")
                 return # Hata olursa işlemi durdur


        try:
            # Veritabanına ürün ekle
            self.app.db_manager.cursor.execute("INSERT INTO urunler (adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi) VALUES (?, ?, ?, ?, ?)",
                                              (adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi))
            self.app.db_manager.conn.commit()
            messagebox.showinfo("Başarılı", f"{adi} başarıyla eklendi.")

            # Ürün listesini yeniden yükle
            self.load_products()
            self.clear_form() # Formu temizle

            # Adisyon sekmesindeki hızlı satış butonlarını güncellemek gerekebilir
            # Sekme değiştiğinde yükleniyor, manuel güncellemeye şimdilik gerek yok.
            # self.app.adisyon_tab.filter_hizli_satis_buttons()


        except sqlite3.IntegrityError: # UNIQUE kısıtlaması hatası (aynı isimde ürün varsa)
            messagebox.showwarning("Uyarı", f"'{adi}' adında bir ürün zaten mevcut.")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün eklenirken hata oluştu: {e}")
            self.app.db_manager.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Ürün eklenirken beklenmedik hata oluştu: {e}")


    def update_product(self):
        """Seçili ürünü günceller."""
        selected_item = self.tree_urunler.focus()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen güncellemek için listeden bir ürün seçin.")
            return

        # Seçili ürünün ID'sini al
        urun_id = self.tree_urunler.item(selected_item, 'values')[0]

        adi = self.entry_urun_adi.get().strip()
        fiyat_str = self.entry_urun_fiyat.get().strip()
        kategori_adi = self.cmb_urun_kategori.get()
        aktif_durumu = self.var_aktif_durum.get() # <<< Düzeltildi
        hizli_satis_sirasi_str = self.entry_hizli_satis_sirasi.get().strip()


        if not adi or not fiyat_str:
            messagebox.showwarning("Uyarı", "Ürün Adı ve Fiyat boş bırakılamaz.")
            return

        try:
            fiyat = float(fiyat_str)
            if fiyat < 0:
                 messagebox.showwarning("Uyarı", "Fiyat negatif olamaz.")
                 return
        except ValueError:
            messagebox.showwarning("Uyarı", "Geçerli bir fiyat girin.")
            return

        try:
             hizli_satis_sirasi = int(hizli_satis_sirasi_str)
             if hizli_satis_sirasi < 0:
                  messagebox.showwarning("Uyarı", "Hızlı Satış Sırası negatif olamaz.")
                  return
        except ValueError:
             messagebox.showwarning("Uyarı", "Geçerli bir hızlı satış sırası girin.")
             return


        # Kategori adına göre kategori_id'yi bul
        kategori_id = None
        if kategori_adi and kategori_adi != "Kategori Yok":
            try:
                self.app.db_manager.cursor.execute("SELECT kategori_id FROM kategoriler WHERE adi = ?", (kategori_adi,))
                result = self.app.db_manager.cursor.fetchone()
                if result:
                    kategori_id = result['kategori_id']
            except sqlite3.Error as e:
                 messagebox.showerror("Veritabanı Hatası", f"Kategori ID çekilirken hata oluştu: {e}")
                 return # Hata olursa işlemi durdur


        try:
            # Veritabanında ürünü güncelle
            self.app.db_manager.cursor.execute("""
                UPDATE urunler SET adi = ?, fiyat = ?, kategori_id = ?, aktif_durumu = ?, hizli_satis_sirasi = ?
                WHERE urun_id = ?
            """, (adi, fiyat, kategori_id, aktif_durumu, hizli_satis_sirasi, urun_id))
            self.app.db_manager.conn.commit()
            messagebox.showinfo("Başarılı", f"{adi} başarıyla güncellendi.")

            # Ürün listesini yeniden yükle
            self.load_products()
            self.clear_form() # Formu temizle

            # Adisyon sekmesindeki hızlı satış butonlarını güncellemek gerekebilir
            # self.app.adisyon_tab.filter_hizli_satis_buttons()


        except sqlite3.IntegrityError: # UNIQUE kısıtlaması hatası
            messagebox.showwarning("Uyarı", f"'{adi}' adında başka bir ürün zaten mevcut.")
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün güncellenirken hata oluştu: {e}")
            self.app.db_manager.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Ürün güncellenirken beklenmedik hata oluştu: {e}")


    def delete_product(self):
        """Seçili ürünü siler."""
        selected_item = self.tree_urunler.focus()
        if not selected_item:
            messagebox.showwarning("Uyarı", "Lütfen silmek için listeden bir ürün seçin.")
            return

        # Seçili ürünün ID'sini ve adını al
        values = self.tree_urunler.item(selected_item, 'values')
        urun_id = values[0]
        urun_adi = values[1]

        if messagebox.askyesno("Onay", f"'{urun_adi}' ürününü silmek istediğinizden emin misiniz?"):
            try:
                # Ürünü veritabanından sil
                self.app.db_manager.cursor.execute("DELETE FROM urunler WHERE urun_id = ?", (urun_id,))
                self.app.db_manager.conn.commit()
                messagebox.showinfo("Başarılı", f"'{urun_adi}' başarıyla silindi.")

                # Ürün listesini yeniden yükle
                self.load_products()
                self.clear_form() # Formu temizle

                # Adisyon sekmesindeki hızlı satış butonlarını güncellemek gerekebilir
                # self.app.adisyon_tab.filter_hizli_satis_buttons()


            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Ürün silinirken hata oluştu: {e}")
                self.app.db_manager.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ürün silinirken beklenmedik hata oluştu: {e}")


    def clear_form(self):
        """Ürün formundaki alanları temizler."""
        self.tree_urunler.selection_remove(self.tree_urunler.focus()) # Treeview seçimini kaldır
        self.entry_urun_adi.delete(0, tk.END)
        self.entry_urun_fiyat.delete(0, tk.END)
        self.cmb_urun_kategori.set("Kategori Yok") # Varsayılan değer
        self.var_aktif_durum.set(True) # Varsayılan olarak aktif <<< Düzeltildi
        self.entry_hizli_satis_sirasi.delete(0, tk.END)
        self.entry_hizli_satis_sirasi.insert(0, "0") # Varsayılan 0