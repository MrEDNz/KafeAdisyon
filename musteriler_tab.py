import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
#constants bu modülde doğrudan kullanılmıyor, import etmeye gerek yok


class MusterilerTab:
    def __init__(self, parent_notebook, app):
        self.app = app
        self.frame = ttk.Frame(parent_notebook, padding="10")
        parent_notebook.add(self.frame, text="Müşteriler")

        self.aktif_musteri_id = None
        self._create_ui()


    def _create_ui(self):
        """Müşteriler sekmesi arayüzünü oluşturur."""
        left_panel = ttk.Frame(self.frame, width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        right_panel = ttk.Frame(self.frame)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Sol Panel: Müşteri Listesi Treeview
        ttk.Label(left_panel, text="Müşteri Listesi:", font=('Arial', 10, 'bold')).pack(pady=(0, 5))
        self.musteri_tree = ttk.Treeview(left_panel, columns=('Ad Soyad', 'Telefon', 'Bakiye'), show='headings')
        self.musteri_tree.heading('Ad Soyad', text='Ad Soyad')
        self.musteri_tree.heading('Telefon', text='Telefon')
        self.musteri_tree.heading('Bakiye', text='Bakiye')

        self.musteri_tree.column('Ad Soyad', width=150)
        self.musteri_tree.column('Telefon', width=100)
        self.musteri_tree.column('Bakiye', width=80, anchor=tk.E)

        musteri_scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=self.musteri_tree.yview)
        self.musteri_tree.configure(yscrollcommand=musteri_scrollbar.set)
        musteri_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.musteri_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.musteri_tree.bind("<<TreeviewSelect>>", self._musteri_sec)

        # Sağ Panel: Müşteri Bilgileri Formu ve Kontrol Butonları
        form_frame = ttk.LabelFrame(right_panel, text="Müşteri Detayları", padding="10")
        form_frame.pack(pady=10, padx=10, fill=tk.X)

        ttk.Label(form_frame, text="ID:").grid(row=0, column=0, sticky=tk.W, pady=2, padx=5)
        self.lbl_musteri_id = ttk.Label(form_frame, text="")
        self.lbl_musteri_id.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)

        ttk.Label(form_frame, text="Ad Soyad:").grid(row=1, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_musteri_adsoyad = ttk.Entry(form_frame)
        self.entry_musteri_adsoyad.grid(row=1, column=1, sticky=tk.W+tk.E, pady=2, padx=5)

        ttk.Label(form_frame, text="Telefon:").grid(row=2, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_musteri_telefon = ttk.Entry(form_frame)
        self.entry_musteri_telefon.grid(row=2, column=1, sticky=tk.W+tk.E, pady=2, padx=5)

        ttk.Label(form_frame, text="Bakiye:").grid(row=3, column=0, sticky=tk.W, pady=2, padx=5)
        self.entry_musteri_bakiye = ttk.Entry(form_frame)
        self.entry_musteri_bakiye.grid(row=3, column=1, sticky=tk.W+tk.E, pady=2, padx=5)
        self.entry_musteri_bakiye.config(state="readonly")

        form_frame.grid_columnconfigure(1, weight=1)


        # Kontrol Butonları
        control_buttons_frame = ttk.Frame(right_panel)
        control_buttons_frame.pack(pady=10)
        ttk.Button(control_buttons_frame, text="Yeni Ekle", command=self._save_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons_frame, text="Güncelle", command=self._save_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons_frame, text="Sil", command=self._delete_customer).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_buttons_frame, text="Temizle", command=self._clear_musteri_form).pack(side=tk.LEFT, padx=5)

        # Bakiye İşlemleri (Placeholder)
        balance_frame = ttk.LabelFrame(right_panel, text="Bakiye İşlemleri", padding="10")
        balance_frame.pack(pady=10, padx=10, fill=tk.X)
        ttk.Label(balance_frame, text="Miktar:").pack(side=tk.LEFT, padx=(0,5))
        self.entry_bakiye_miktar = ttk.Entry(balance_frame, width=10)
        self.entry_bakiye_miktar.pack(side=tk.LEFT, padx=(0,5))
        ttk.Button(balance_frame, text="Yükle", command=lambda: messagebox.showinfo("Bilgi", "Bakiye Yükle fonksiyonu henüz tanımlanmadı.")).pack(side=tk.LEFT, padx=5)
        ttk.Button(balance_frame, text="Tahsil Et", command=lambda: messagebox.showinfo("Bilgi", "Bakiye Tahsil Et fonksiyonu henüz tanımlanmadı.")).pack(side=tk.LEFT, padx=5)


    def load_customers(self):
        """Müşterileri veritabanından çeker ve müşteriler Treeview'ını günceller."""
        for item in self.musteri_tree.get_children():
            self.musteri_tree.delete(item)

        try:
            self.app.db_manager.cursor.execute("SELECT musteri_id, ad_soyad, telefon, bakiye FROM musteriler ORDER BY ad_soyad")
            musteriler = self.app.db_manager.cursor.fetchall()

            for musteri in musteriler:
                self.musteri_tree.insert('', tk.END, values=(musteri['ad_soyad'], musteri['telefon'], f"{musteri['bakiye']:.2f}"), iid=musteri['musteri_id'])

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri listesi yüklenirken hata oluştu: {e}")

    def _musteri_sec(self, event):
        """Müşteri listesinden bir öğe seçildiğinde form alanlarını doldurur."""
        selected_item_id = self.musteri_tree.focus()
        if not selected_item_id:
            self._clear_musteri_form()
            self.aktif_musteri_id = None
            return

        self.aktif_musteri_id = selected_item_id

        db = self.app.db_manager
        try:
            db.cursor.execute("SELECT musteri_id, ad_soyad, telefon, bakiye FROM musteriler WHERE musteri_id = ?", (selected_item_id,))
            musteri_info = db.cursor.fetchone()

            if musteri_info:
                self.lbl_musteri_id.config(text=musteri_info['musteri_id'])
                self.entry_musteri_adsoyad.delete(0, tk.END)
                self.entry_musteri_adsoyad.insert(0, musteri_info['ad_soyad'])
                self.entry_musteri_telefon.delete(0, tk.END)
                self.entry_musteri_telefon.insert(0, musteri_info['telefon'] if musteri_info['telefon'] else "")
                self.entry_musteri_bakiye.config(state="normal")
                self.entry_musteri_bakiye.delete(0, tk.END)
                self.entry_musteri_bakiye.insert(0, f"{musteri_info['bakiye']:.2f}")
                self.entry_musteri_bakiye.config(state="readonly")


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri bilgileri yüklenirken hata oluştu: {e}")

    def _save_customer(self):
        """Müşteri bilgilerini veritabanına kaydeder (Yeni Ekle veya Güncelle)."""
        ad_soyad = self.entry_musteri_adsoyad.get().strip()
        telefon = self.entry_musteri_telefon.get().strip()

        if not ad_soyad:
            messagebox.showwarning("Uyarı", "Ad Soyad boş bırakılamaz.")
            return

        db = self.app.db_manager
        try:
            if self.aktif_musteri_id:
                 if telefon:
                      db.cursor.execute("SELECT musteri_id FROM musteriler WHERE telefon = ? AND musteri_id != ?", (telefon, self.aktif_musteri_id))
                      if db.cursor.fetchone():
                           messagebox.showwarning("Uyarı", f"'{telefon}' numaralı başka bir müşteri zaten mevcut.")
                           return

                 db.cursor.execute("""
                     UPDATE musteriler SET ad_soyad = ?, telefon = ? WHERE musteri_id = ?
                 """, (ad_soyad, telefon if telefon else None, self.aktif_musteri_id))
                 db.conn.commit()
                 messagebox.showinfo("Başarılı", "Müşteri güncellendi.")
            else:
                if telefon:
                     db.cursor.execute("SELECT COUNT(*) FROM musteriler WHERE telefon = ?", (telefon,))
                     if db.cursor.fetchone()[0] > 0:
                          messagebox.showwarning("Uyarı", f"'{telefon}' numaralı bir müşteri zaten mevcut.")
                          return

                db.cursor.execute("""
                    INSERT INTO musteriler (ad_soyad, telefon) VALUES (?, ?)
                """, (ad_soyad, telefon if telefon else None))
                db.conn.commit()
                messagebox.showinfo("Başarılı", "Müşteri eklendi.")

            self.load_customers()
            self._clear_musteri_form()

        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri kaydedilirken hata oluştu: {e}")
            db.conn.rollback()

    def _delete_customer(self):
        """Seçili müşteriyi veritabanından siler."""
        if not self.aktif_musteri_id:
            messagebox.showwarning("Uyarı", "Silmek için lütfen bir müşteri seçin.")
            return

        db = self.app.db_manager
        try:
             db.cursor.execute("SELECT COUNT(*) FROM siparis_gecmisi WHERE musteri_id = ?", (self.aktif_musteri_id,))
             kullanim_sayisi = db.cursor.fetchone()[0]

             if kullanim_sayisi > 0:
                  messagebox.showwarning("Uyarı", f"Bu müşteri geçmiş adisyonlarda kullanıldığı için silinemez.")
                  return


             if messagebox.askyesno("Onay", "Seçili müşteriyi silmek istediğinizden emin misiniz?"):
                 db.cursor.execute("DELETE FROM musteriler WHERE musteri_id = ?", (self.aktif_musteri_id,))
                 db.conn.commit()
                 messagebox.showinfo("Başarılı", "Müşteri silindi.")
                 self.load_customers()
                 self._clear_musteri_form()
        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Müşteri silinirken hata oluştu: {e}")
            db.conn.rollback()

    def _clear_musteri_form(self):
        """Müşteri form alanlarını temizler ve aktif müşteri ID'sini sıfırlar."""
        self.lbl_musteri_id.config(text="")
        self.entry_musteri_adsoyad.delete(0, tk.END)
        self.entry_musteri_telefon.delete(0, tk.END)
        self.entry_musteri_bakiye.config(state="normal")
        self.entry_musteri_bakiye.delete(0, tk.END)
        self.entry_musteri_bakiye.insert(0, "0.00")
        self.entry_musteri_bakiye.config(state="readonly")

        self.aktif_musteri_id = None
        self.musteri_tree.selection_remove(self.musteri_tree.selection())