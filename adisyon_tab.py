import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime, timedelta
import constants

class AdisyonTab:
    def __init__(self, parent_notebook, app):
        self.app = app
        self.frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(self.frame, text="Adisyon")

        self.cart_items = []

        self._create_ui()

    def _create_ui(self):
        """Adisyon sekmesi arayüzünü oluşturur."""
        top_info_frame = ttk.Frame(self.frame, padding=(0, 0, 0, 10))
        top_info_frame.pack(fill=tk.X)

        self.lbl_aktif_masa = ttk.Label(top_info_frame, text="Aktif Masa: Seçilmedi", font=('Arial', 12, 'bold'))
        self.lbl_aktif_masa.pack(side=tk.LEFT, padx=5)

        search_filter_frame = ttk.Frame(top_info_frame)
        search_filter_frame.pack(side=tk.RIGHT, padx=5)

        ttk.Label(search_filter_frame, text="Ara/Filtre:").pack(side=tk.LEFT)
        self.entry_search = ttk.Entry(search_filter_frame, width=20)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        self.entry_search.bind('<KeyRelease>', self.filter_hizli_satis_buttons)

        self.cmb_kategori_filter = ttk.Combobox(search_filter_frame, width=15, state='readonly')
        self.cmb_kategori_filter.pack(side=tk.LEFT, padx=5)
        self.cmb_kategori_filter.bind('<<ComboboxSelected>>', self.filter_hizli_satis_buttons)

        hizli_satis_label = ttk.Label(self.frame, text="Hızlı Satış Ürünleri:")
        hizli_satis_label.pack(fill=tk.X, pady=(0, 5))

        hizli_satis_area_frame = ttk.Frame(self.frame)
        hizli_satis_area_frame.pack(fill=tk.BOTH, expand=True)

        self.hizli_satis_canvas = tk.Canvas(hizli_satis_area_frame, bg="white")
        self.hizli_satis_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.hizli_satis_scrollbar = ttk.Scrollbar(hizli_satis_area_frame, orient="vertical", command=self.hizli_satis_canvas.yview)
        self.hizli_satis_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.hizli_satis_canvas.configure(yscrollcommand=self.hizli_satis_scrollbar.set)

        # Canvas boyutlandırma olayını yakala ve configure_hizli_satis_canvas metodunu after ile planla
        self.hizli_satis_canvas.bind('<Configure>', self._schedule_hizli_satis_canvas_configure)

        self.hizli_satis_button_frame = ttk.Frame(self.hizli_satis_canvas)
        # create_window çağrılırken width ve height 0 olarak ayarlanmalı, configure içinde güncellenecek
        self.hizli_satis_button_frame_id = self.hizli_satis_canvas.create_window((0, 0), window=self.hizli_satis_button_frame, anchor="nw", width=0, height=0)

        cart_label = ttk.Label(self.frame, text="Adisyon Sepeti:")
        cart_label.pack(fill=tk.X, pady=(10, 5))

        cart_area_frame = ttk.Frame(self.frame)
        cart_area_frame.pack(fill=tk.BOTH, expand=True)

        self.cart_treeview = ttk.Treeview(cart_area_frame, columns=("Ürün Adı", "Miktar", "Birim Fiyat", "Tutar"), show="headings")
        self.cart_treeview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.cart_treeview.heading("Ürün Adı", text="Ürün Adı")
        self.cart_treeview.heading("Miktar", text="Miktar")
        self.cart_treeview.heading("Birim Fiyat", text="Birim Fiyat")
        self.cart_treeview.heading("Tutar", text="Tutar")

        self.cart_treeview.column("Ürün Adı", width=200)
        self.cart_treeview.column("Miktar", width=80, anchor=tk.CENTER)
        self.cart_treeview.column("Birim Fiyat", width=100, anchor=tk.E)
        self.cart_treeview.column("Tutar", width=100, anchor=tk.E)

        cart_scrollbar = ttk.Scrollbar(cart_area_frame, orient="vertical", command=self.cart_treeview.yview)
        cart_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.cart_treeview.configure(yscrollcommand=cart_scrollbar.set)

        bottom_controls_frame = ttk.Frame(self.frame, padding=(0, 10, 0, 0))
        bottom_controls_frame.pack(fill=tk.X)

        quantity_frame = ttk.Frame(bottom_controls_frame)
        quantity_frame.pack(side=tk.LEFT)
        ttk.Label(quantity_frame, text="Miktar:").pack(side=tk.LEFT)
        self.entry_quantity = ttk.Entry(quantity_frame, width=5)
        self.entry_quantity.pack(side=tk.LEFT, padx=5)
        self.entry_quantity.insert(0, "1")

        ttk.Button(quantity_frame, text="Seçiliyi Sil", command=self.remove_selected_cart_item).pack(side=tk.LEFT, padx=5)
        ttk.Button(quantity_frame, text="Sepeti Temizle", command=self.clear_cart).pack(side=tk.LEFT, padx=5)
        ttk.Button(quantity_frame, text="İskonto Uygula", command=self.apply_discount).pack(side=tk.LEFT, padx=5)

        totals_payments_frame = ttk.Frame(bottom_controls_frame)
        totals_payments_frame.pack(side=tk.RIGHT)

        self.lbl_total = ttk.Label(totals_payments_frame, text="Toplam: 0.00 TL", font=('Arial', 10, 'bold'))
        self.lbl_total.pack(anchor=tk.E)

        self.lbl_discount = ttk.Label(totals_payments_frame, text="İskonto: 0.00 TL", font=('Arial', 10))
        self.lbl_discount.pack(anchor=tk.E)

        self.lbl_net_total = ttk.Label(totals_payments_frame, text="Net Tutar: 0.00 TL", font=('Arial', 12, 'bold'), foreground='blue')
        self.lbl_net_total.pack(anchor=tk.E)

        payment_buttons_frame = ttk.Frame(totals_payments_frame)
        payment_buttons_frame.pack(pady=5)
        ttk.Button(payment_buttons_frame, text="Nakit Ödeme", command=lambda: self.process_payment("Nakit"), style='Odeme.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(payment_buttons_frame, text="Kart Ödeme", command=lambda: self.process_payment("Kart"), style='Odeme.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(payment_buttons_frame, text="Ara Ödeme", command=lambda: self.process_payment("Ara"), style='Odeme.TButton').pack(side=tk.LEFT, padx=5)

    def _schedule_hizli_satis_canvas_configure(self, event):
        """Canvas boyutlandırma işlemini after ile planlar."""
        # Mevcut planlanmış işlemleri iptal et (çoklu olayları önlemek için)
        if hasattr(self, '_after_id_canvas_configure') and self._after_id_canvas_configure is not None:
            try:
                self.hizli_satis_canvas.after_cancel(self._after_id_canvas_configure)
            except tk.TclError:
                # Eğer after_cancel sırasında hata olursa (zaten iptal edilmişse), yoksay
                pass

        # configure_hizli_satis_canvas metodunu ana döngü boşta kaldığında çalışacak şekilde planla
        self._after_id_canvas_configure = self.hizli_satis_canvas.after(0, self._configure_hizli_satis_canvas)


    def _configure_hizli_satis_canvas(self):
        """Canvas boyutu değiştiğinde iç frame'in boyutunu günceller."""
        # self.hizli_satis_button_frame'in None olmadığını ve mevcut olduğunu kontrol et
        # winfo_exists() kontrolü yeterli değilse, try-except bloğu içinde winfo_width() gibi
        # bir metoda erişmeyi deneyerek daha sağlam bir kontrol yapabiliriz.
        if self.hizli_satis_button_frame is not None and self.hizli_satis_button_frame.winfo_exists():
            try:
                # Çerçevenin boyutlarını almak için winfo_width() kullanmayı deneyin
                # Eğer bu başarılı olursa, çerçeve kullanıma hazır demektir.
                canvas_width = self.hizli_satis_canvas.winfo_width()
                frame_width_check = self.hizli_satis_button_frame.winfo_width() # <<< Sağlamlık kontrolü
                # Eğer buraya geldiyse ve frame_width_check geçerli bir sayı ise, çerçeve hazır.

                # Canvas içinde oluşturulan pencerenin genişliğini Canvas'ın genişliğine ayarla
                self.hizli_satis_canvas.itemconfig(self.hizli_satis_button_frame_id, width=canvas_width)

                # İç frame'in (hizli_satis_button_frame) gerçek yüksekliğini al
                self.hizli_satis_button_frame.update_idletasks()
                frame_height = self.hizli_satis_button_frame.winfo_height()

                # Canvas'ın kaydırılabilir alanını (scrollregion) iç frame'in boyutuna ayarla
                self.hizli_satis_canvas.config(scrollregion=(0, 0, canvas_width, frame_height))
                # print("DEBUG: _configure_hizli_satis_canvas: Canvas yapılandırması başarılı.") # Debug mesajı
            except Exception as e:
                 print(f"DEBUG: _configure_hizli_satis_canvas beklenmedik hata: {e}")
                 # Hata durumunda scrollregion'ı sıfırla
                 self.hizli_satis_canvas.config(scrollregion=(0, 0, 0, 0))
        else:
             print("DEBUG: _configure_hizli_satis_canvas: hizli_satis_button_frame None veya mevcut değil.") # Debug mesajı
             # Eğer frame henüz yoksa veya geçerli değilse, scrollregion'ı sıfırla
             self.hizli_satis_canvas.config(scrollregion=(0, 0, 0, 0))


    def load_categories_combobox(self, categories):
        """Kategori filtre Combobox'ını günceller."""
        self.cmb_kategori_filter['values'] = categories
        self.cmb_kategori_filter.set("Tümü")

    def filter_hizli_satis_buttons(self, event=None):
        """Arama kutusu veya kategori seçimine göre hızlı satış butonlarını filtreler."""
        search_term = self.entry_search.get().lower()
        selected_category = self.cmb_kategori_filter.get()

        # Mevcut butonları temizle (yeniden oluşturacağız)
        # Butonları temizlemeden önce hizli_satis_button_frame'in geçerli olduğundan emin olalım
        if self.hizli_satis_button_frame is not None and self.hizli_satis_button_frame.winfo_exists():
            for widget in self.hizli_satis_button_frame.winfo_children():
                widget.destroy()
        else:
            print("DEBUG: filter_hizli_satis_buttons: hizli_satis_button_frame None veya mevcut değil, butonlar temizlenemedi.")
            return # Frame geçerli değilse devam etme


        try:
            query = "SELECT urun_id, adi, fiyat, kategori_id FROM urunler WHERE aktif_durumu = 1 AND hizli_satis_sirasi > 0"
            params = []

            if selected_category and selected_category != "Tümü":
                 self.app.db_manager.cursor.execute("SELECT kategori_id FROM kategoriler WHERE adi = ?", (selected_category,))
                 category_result = self.app.db_manager.cursor.fetchone()
                 if category_result:
                     kategori_id = category_result['kategori_id']
                     query += " AND kategori_id = ?"
                     params.append(kategori_id)

            if search_term:
                query += " AND LOWER(adi) LIKE ?"
                params.append(f"%{search_term}%")

            query += " ORDER BY hizli_satis_sirasi"

            self.app.db_manager.cursor.execute(query, params)
            urunler = self.app.db_manager.cursor.fetchall()

            row, col = 0, 0
            max_cols = 5

            # Butonları oluşturmadan önce hizli_satis_button_frame'in hala geçerli olduğundan emin ol
            if not (self.hizli_satis_button_frame is not None and self.hizli_satis_button_frame.winfo_exists()):
                 print("DEBUG: filter_hizli_satis_buttons: hizli_satis_button_frame buton oluşturma sırasında None veya mevcut değil.")
                 return # Frame geçerli değilse buton oluşturma


            for urun in urunler:
                urun_id = urun['urun_id']
                urun_adi = urun['adi']
                urun_fiyat = urun['fiyat']
                urun_kategori_id = urun['kategori_id']

                kategori_adi = "default"
                if urun_kategori_id:
                     self.app.db_manager.cursor.execute("SELECT adi FROM kategoriler WHERE kategori_id = ?", (urun_kategori_id,))
                     kategori_result = self.app.db_manager.cursor.fetchone()
                     if kategori_result:
                          kategori_adi = kategori_result['adi']

                style_name = f"{kategori_adi}.HizliSatis.TButton" if kategori_adi in constants.CATEGORY_COLORS else 'default.HizliSatis.TButton'

                button_text = f"{urun_adi}\n{urun_fiyat:.2f} TL"

                btn = ttk.Button(self.hizli_satis_button_frame,
                                 text=button_text,
                                 command=lambda id=urun_id, adi=urun_adi, fiyat=urun_fiyat: self.add_to_cart(id, adi, fiyat),
                                 style=style_name)

                btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

            for i in range(max_cols):
                self.hizli_satis_button_frame.grid_columnconfigure(i, weight=1)

            for r in range(row + 1):
                 self.hizli_satis_button_frame.grid_rowconfigure(r, weight=1)

            # Butonlar oluşturulduktan sonra canvas boyutunu güncelle
            # Canvas yapılandırmasını after ile planla
            self._schedule_hizli_satis_canvas_configure(None) # None event olarak geçilebilir

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Hızlı satış ürünleri yüklenirken hata oluştu: {e}")
        except Exception as e:
             messagebox.showerror("Hata", f"Hızlı satış ürünleri yüklenirken beklenmedik hata oluştu: {e}")

    def add_to_cart(self, urun_id, urun_adi, urun_fiyat):
        """Sepete ürün ekler."""
        if self.app.aktif_masa is None:
            messagebox.showwarning("Uyarı", "Lütfen önce Masa sekmesinden bir masa seçin.")
            return

        try:
            try:
                quantity = float(self.entry_quantity.get())
                if quantity <= 0:
                    messagebox.showwarning("Uyarı", "Miktar pozitif bir sayı olmalıdır.")
                    return
            except ValueError:
                messagebox.showwarning("Uyarı", "Geçerli bir miktar girin.")
                return

            if self.app.aktif_siparis_id is None:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.app.db_manager.cursor.execute("INSERT INTO siparis_gecmisi (masa_no, acilis_zamani, durum, son_islem_zamani) VALUES (?, ?, ?, ?)",
                                                  (self.app.aktif_masa, now, 'Açık', now))
                self.app.db_manager.conn.commit()
                self.app.aktif_siparis_id = self.app.db_manager.cursor.lastrowid
                print(f"Yeni sipariş oluşturuldu. ID: {self.app.aktif_siparis_id}")

                self.app.db_manager.cursor.execute("UPDATE masalar SET aktif_siparis_id = ?, durum = ? WHERE masa_no = ?",
                                                  (self.app.aktif_siparis_id, 'Dolu', self.app.aktif_masa))
                self.app.db_manager.conn.commit()

            tutar = quantity * urun_fiyat
            kategori_id = None
            self.app.db_manager.cursor.execute("SELECT kategori_id FROM urunler WHERE urun_id = ?", (urun_id,))
            urun_info = self.app.db_manager.cursor.fetchone()
            if urun_info:
                 kategori_id = urun_info['kategori_id']

            self.app.db_manager.cursor.execute("INSERT INTO siparis_detaylari (siparis_id, urun_id, urun_adi, miktar, birim_fiyat, tutar, kategori_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                              (self.app.aktif_siparis_id, urun_id, urun_adi, quantity, urun_fiyat, tutar, kategori_id))
            self.app.db_manager.conn.commit()
            print(f"Sepete eklendi: {urun_adi} x {quantity}")

            self.app.db_manager.cursor.execute("UPDATE masalar SET guncel_toplam = guncel_toplam + ? WHERE masa_no = ?",
                                              (tutar, self.app.aktif_masa))
            self.app.db_manager.conn.commit()

            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.app.db_manager.cursor.execute("UPDATE siparis_gecmisi SET son_islem_zamani = ? WHERE siparis_id = ?",
                                              (now, self.app.aktif_siparis_id))
            self.app.db_manager.conn.commit()

            self.load_cart()

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün sepete eklenirken hata oluştu: {e}")
            self.app.db_manager.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Ürün sepete eklenirken beklenmedik hata oluştu: {e}")

    def load_cart(self):
        """Aktif masanın sepetini (sipariş detaylarını) Treeview'e yükler."""
        for item in self.cart_treeview.get_children():
            self.cart_treeview.delete(item)

        self.cart_items = []
        current_total = 0.0

        if self.app.aktif_siparis_id is not None:
            try:
                self.app.db_manager.cursor.execute("SELECT detay_id, urun_adi, miktar, birim_fiyat, tutar FROM siparis_detaylari WHERE siparis_id = ?", (self.app.aktif_siparis_id,))
                items = self.app.db_manager.cursor.fetchall()

                for item in items:
                    self.cart_treeview.insert("", tk.END, values=(item['urun_adi'], item['miktar'], f"{item['birim_fiyat']:.2f}", f"{item['tutar']:.2f}"), iid=item['detay_id'])
                    self.cart_items.append(item)
                    current_total += item['tutar']

            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Sepet yüklenirken hata oluştu: {e}")

        self.update_totals(current_total)

    def update_totals(self, total_amount):
        """Toplam, İskonto ve Net Tutar etiketlerini günceller."""
        current_discount = 0.0
        if self.app.aktif_masa is not None:
             try:
                 self.app.db_manager.cursor.execute("SELECT iskonto FROM masalar WHERE masa_no = ?", (self.app.aktif_masa,))
                 result = self.app.db_manager.cursor.fetchone()
                 if result:
                      current_discount = result['iskonto']
             except sqlite3.Error as e:
                  print(f"İskonto bilgisi çekilirken hata oluştu: {e}")

        net_total = total_amount - current_discount

        self.lbl_total.config(text=f"Toplam: {total_amount:.2f} TL")
        self.lbl_discount.config(text=f"İskonto: {current_discount:.2f} TL")
        self.lbl_net_total.config(text=f"Net Tutar: {net_total:.2f} TL")

        if self.app.aktif_masa is not None:
             try:
                 self.app.db_manager.cursor.execute("UPDATE masalar SET guncel_toplam = ?, iskonto = ? WHERE masa_no = ?",
                                                   (net_total, current_discount, self.app.aktif_masa))
                 self.app.db_manager.conn.commit()
             except sqlite3.Error as e:
                  print(f"Masa toplamları güncellenirken hata oluştu: {e}")

    def remove_selected_cart_item(self):
        """Sepetten seçili ürünü siler."""
        selected_item_iid = self.cart_treeview.focus()

        if not selected_item_iid:
            messagebox.showwarning("Uyarı", "Lütfen sepetten silmek için bir ürün seçin.")
            return

        detay_id_to_delete = int(selected_item_iid)

        try:
            self.app.db_manager.cursor.execute("SELECT tutar FROM siparis_detaylari WHERE detay_id = ?", (detay_id_to_delete,))
            result = self.app.db_manager.cursor.fetchone()
            if not result:
                 messagebox.showerror("Hata", "Silinecek ürün bulunamadı.")
                 return

            deleted_item_tutar = result['tutar']

            self.app.db_manager.cursor.execute("DELETE FROM siparis_detaylari WHERE detay_id = ?", (detay_id_to_delete,))
            self.app.db_manager.conn.commit()

            if self.app.aktif_masa is not None:
                 self.app.db_manager.cursor.execute("UPDATE masalar SET guncel_toplam = guncel_toplam - ? WHERE masa_no = ?",
                                                   (deleted_item_tutar, self.app.aktif_masa))
                 self.app.db_manager.conn.commit()

            if self.app.aktif_siparis_id is not None:
                 now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                 self.app.db_manager.cursor.execute("UPDATE siparis_gecmisi SET son_islem_zamani = ? WHERE siparis_id = ?",
                                                   (now, self.app.aktif_siparis_id))
                 self.app.db_manager.conn.commit()

            self.load_cart()

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Ürün sepetten silinirken hata oluştu: {e}")
            self.app.db_manager.conn.rollback()
        except Exception as e:
             messagebox.showerror("Hata", f"Ürün sepetten silinirken beklenmedik hata oluştu: {e}")

    def clear_cart(self):
        """Aktif masanın sepetini tamamen temizler."""
        if self.app.aktif_siparis_id is None:
            messagebox.showinfo("Bilgi", "Sepet zaten boş.")
            return

        if messagebox.askyesno("Onay", "Sepeti tamamen temizlemek istediğinizden emin misiniz?"):
            try:
                self.app.db_manager.cursor.execute("DELETE FROM siparis_detaylari WHERE siparis_id = ?", (self.app.aktif_siparis_id,))
                self.app.db_manager.conn.commit()

                if self.app.aktif_masa is not None:
                     self.app.db_manager.cursor.execute("UPDATE masalar SET guncel_toplam = 0.0, iskonto = 0.0 WHERE masa_no = ?", (self.app.aktif_masa,))
                     self.app.db_manager.conn.commit()

                if self.app.aktif_siparis_id is not None:
                     self.app.db_manager.cursor.execute("UPDATE siparis_gecmisi SET durum = ?, kapanis_zamani = ?, son_islem_zamani = ? WHERE siparis_id = ?",
                                                       ('İptal Edildi', datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None, self.app.aktif_siparis_id))
                     self.app.db_manager.conn.commit()

                self.load_cart()

                messagebox.showinfo("Başarılı", "Sepet temizlendi.")

            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Sepet temizlenirken hata oluştu: {e}")
                self.app.db_manager.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Sepet temizlenirken beklenmedik hata oluştu: {e}")

    def apply_discount(self):
        """Aktif masanın adisyonına iskonto uygular."""
        if self.app.aktif_masa is None:
            messagebox.showwarning("Uyarı", "Lütfen önce Masa sekmesinden bir masa seçin.")
            return

        current_total = 0.0
        for item in self.cart_treeview.get_children():
            item_values = self.cart_treeview.item(item, 'values')
            current_total += float(item_values[3])

        if current_total <= 0:
             messagebox.showwarning("Uyarı", "İskonto uygulamak için sepette ürün olmalıdır.")
             return

        try:
            from tkinter.simpledialog import askfloat
            discount_amount = askfloat("İskonto Uygula", "Uygulanacak iskonto miktarını girin (TL):", parent=self.frame)

            if discount_amount is not None:
                if discount_amount < 0:
                    messagebox.showwarning("Uyarı", "İskonto miktarı negatif olamaz.")
                    return
                if discount_amount > current_total:
                     messagebox.showwarning("Uyarı", f"İskonto miktarı toplam tutardan ({current_total:.2f} TL) fazla olamaz.")
                     return

                if self.app.aktif_masa is not None:
                     self.app.db_manager.cursor.execute("UPDATE masalar SET iskonto = ? WHERE masa_no = ?",
                                                       (discount_amount, self.app.aktif_masa))
                     self.app.db_manager.conn.commit()

                if self.app.aktif_siparis_id is not None:
                     now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                     self.app.db_manager.cursor.execute("UPDATE siparis_gecmisi SET son_islem_zamani = ? WHERE siparis_id = ?",
                                                       (now, self.app.aktif_siparis_id))
                     self.app.db_manager.conn.commit()

                self.update_totals(current_total)

                messagebox.showinfo("Başarılı", f"{discount_amount:.2f} TL iskonto uygulandı.")

        except Exception as e:
             messagebox.showerror("Hata", f"İskonto uygulanırken beklenmedik hata oluştu: {e}")

    def process_payment(self, payment_method):
        """Ödeme işlemini gerçekleştirir ve adisyonu kapatır."""
        if self.app.aktif_masa is None or self.app.aktif_siparis_id is None:
            messagebox.showwarning("Uyarı", "Ödeme almak için aktif bir masa ve adisyon olmalıdır.")
            return

        current_total = 0.0
        for item in self.cart_treeview.get_children():
            item_values = self.cart_treeview.item(item, 'values')
            current_total += float(item_values[3])

        current_discount = 0.0
        if self.app.aktif_masa is not None:
             try:
                 self.app.db_manager.cursor.execute("SELECT iskonto FROM masalar WHERE masa_no = ?", (self.app.aktif_masa,))
                 result = self.app.db_manager.cursor.fetchone()
                 if result:
                      current_discount = result['iskonto']
             except sqlite3.Error as e:
                  print(f"İskonto bilgisi çekilirken hata oluştu: {e}")

        net_total = current_total - current_discount

        if net_total <= 0:
             messagebox.showwarning("Uyarı", "Ödeme alınacak tutar sıfır veya daha az olamaz.")
             return

        if messagebox.askyesno("Onay", f"Masa {self.app.aktif_masa} için {net_total:.2f} TL ({payment_method}) ödeme almak istediğinizden emin misiniz?"):
            try:
                self.app.db_manager.cursor.execute("UPDATE siparis_gecmisi SET kapanis_zamani = ?, durum = ?, toplam_tutar = ?, iskonto = ?, odeme_yontemi = ?, son_islem_zamani = NULL WHERE siparis_id = ?",
                                                  (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'Kapandı', net_total, current_discount, payment_method, self.app.aktif_siparis_id))
                self.app.db_manager.conn.commit()

                self.app.db_manager.cursor.execute("UPDATE masalar SET aktif_siparis_id = NULL, durum = ?, guncel_toplam = 0.0, iskonto = 0.0 WHERE masa_no = ?",
                                                  ('Boş', self.app.aktif_masa))
                self.app.db_manager.conn.commit()

                messagebox.showinfo("Başarılı", f"Masa {self.app.aktif_masa} için ödeme alındı. Toplam: {net_total:.2f} TL ({payment_method})")

                self.app.aktif_masa = None
                self.app.aktif_siparis_id = None
                self.lbl_aktif_masa.config(text="Aktif Masa: Seçilmedi")

                self._clear_cart_ui()

            except sqlite3.Error as e:
                messagebox.showerror("Veritabanı Hatası", f"Ödeme işlemi sırasında hata oluştu: {e}")
                self.app.db_manager.conn.rollback()
            except Exception as e:
                 messagebox.showerror("Hata", f"Ödeme işlemi sırasında beklenmedik hata oluştu: {e}")

    def _clear_cart_ui(self):
        """Adisyon sepeti arayüzünü temizler (Treeview ve toplamlar)."""
        for item in self.cart_treeview.get_children():
            self.cart_treeview.delete(item)
        self.cart_items = []
        self.update_totals(0.0)