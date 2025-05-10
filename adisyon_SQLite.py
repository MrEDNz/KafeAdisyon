# -*- coding: utf-8 -*-
"""
TAM PROFESYONEL CAFE ADİSYON PROGRAMI - v4.1
Tüm hakları saklıdır © 2023
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import os
import shutil
import hashlib
import sys
import webbrowser
from PIL import Image, ImageTk
import tempfile
import csv

# -------------------- KONFİGÜRASYON --------------------
class Config:
    DB_NAME = "cafe_db.db"
    BACKUP_DIR = "backups"
    COMPANY_NAME = "DELTA CAFE"
    ADDRESS = "İstiklal Cad. No:123, İstanbul"
    PHONE = "0212 123 4567"
    TAX_NUMBER = "1234567890"
    LOGO_PATH = "logo.png"
    DEFAULT_THEME = "clam"
    RECEIPT_PRINTER = "POS58"
    COMPANY_NAME = "My Cafe"
    PHONE = "0212 123 4567"

# -------------------- VERİTABANI KATMANI --------------------
class Database:
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.connect()
        self.create_tables()
        self.insert_default_data()
    
    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_file)
            self.conn.execute("PRAGMA foreign_keys = ON")
            return True
        except sqlite3.Error as e:
            self.show_error("Veritabanı bağlantı hatası", str(e))
            return False
    
    def create_tables(self):
        tables = [
            """CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                description TEXT,
                image_path TEXT,
                sort_order INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                price REAL NOT NULL,
                cost REAL,
                stock REAL DEFAULT 0,
                unit TEXT DEFAULT 'adet',
                barcode TEXT,
                description TEXT,
                image_path TEXT,
                is_active INTEGER DEFAULT 1,
                FOREIGN KEY(category_id) REFERENCES categories(id)
            )""",
            """CREATE TABLE IF NOT EXISTS tables (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                is_active INTEGER DEFAULT 1
            )""",
            """CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                total REAL NOT NULL,
                discount REAL DEFAULT 0,
                date TEXT NOT NULL,
                status TEXT DEFAULT 'open',
                payment_type TEXT,
                notes TEXT,
                FOREIGN KEY(table_id) REFERENCES tables(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )""",
            """CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity REAL NOT NULL,
                price REAL NOT NULL,
                discount REAL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id),
                FOREIGN KEY(product_id) REFERENCES products(id)
            )""",
            """CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                date TEXT NOT NULL,
                payment_type TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY(order_id) REFERENCES orders(id)
            )""",
            """CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )"""
        ]
        
        try:
            cursor = self.conn.cursor()
            for table in tables:
                cursor.execute(table)
            self.conn.commit()
        except sqlite3.Error as e:
            self.show_error("Tablo oluşturma hatası", str(e))
    
    def insert_default_data(self):
        # Varsayılan admin kullanıcısı
        if not self.get_one("SELECT id FROM users WHERE username = 'admin'"):
            hashed_pw = hashlib.sha256("admin123".encode()).hexdigest()
            self.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
                ("admin", hashed_pw, "Admin User", "admin"),
                commit=True
            )
        
        # Varsayılan masalar
        if not self.get_one("SELECT id FROM tables"):
            for i in range(1, 21):
                self.execute(
                    "INSERT INTO tables (name) VALUES (?)",
                    (f"Masa {i}",),
                    commit=True
                )
        
        # Varsayılan kategoriler
        if not self.get_one("SELECT id FROM categories"):
            default_categories = [
                ("Sıcak İçecekler", "Çay, kahve, sıcak çikolata vb.", 1),
                ("Soğuk İçecekler", "Meyve suları, soda, limonata vb.", 2),
                ("Yiyecekler", "Ana yemekler, atıştırmalıklar", 3),
                ("Tatlılar", "Pasta, dondurma, waffle vb.", 4)
            ]
            
            for cat in default_categories:
                self.execute(
                    "INSERT INTO categories (name, description, sort_order) VALUES (?, ?, ?)",
                    cat,
                    commit=True
                )
    
    def execute(self, query, params=(), commit=False):
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params)
            if commit:
                self.conn.commit()
            return cursor
        except sqlite3.Error as e:
            self.show_error("Veritabanı hatası", str(e))
            return None
    
    def get_one(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchone() if cursor else None
    
    def get_all(self, query, params=()):
        cursor = self.execute(query, params)
        return cursor.fetchall() if cursor else []
    
    def show_error(self, title, message):
        messagebox.showerror(title, f"Veritabanı hatası:\n{message}")

    def show_help(self):
        """Kullanım kılavuzunu gösterir"""
        help_text = """
        CAFE ADİSYON PROGRAMI KULLANIM KILAVUZU
            
        - Adisyon Sekmesi: Sipariş almak için kullanılır
        - Ürün Yönetimi: Menüye ürün ekleme/düzenleme
        - Raporlar: Günlük satış raporlarını görüntüleme
            
        Daha fazla yardım için: example.com/yardim
        """
        messagebox.showinfo("Yardım", help_text)

    def show_about(self):
        """Program hakkında bilgi gösterir"""
        about_text = f"""
        {Config.COMPANY_NAME} Adisyon Programı v4.0
            
        Geliştirici: XYZ Yazılım
        Tel: {Config.PHONE}
        Versiyon: 1.0.0
        """
        messagebox.showinfo("Hakkında", about_text)

# -------------------- ANA UYGULAMA --------------------
class CafeApp:
    def __init__(self, root):
        self.root = root
        self.setup_window()
        self.db = Database(Config.DB_NAME)
        self.current_user = None
        self.current_order = {
            'items': [],
            'table_id': None,
            'total': 0.0,
            'discount': 0.0
        }
        self.setup_ui()
        self.show_login()
    
    def setup_window(self):
        self.root.title(f"{Config.COMPANY_NAME} - Adisyon Programı")
        self.root.geometry("1366x768")
        self.root.state('zoomed')
        
        # Windows DPI ayarı
        if sys.platform == "win32":
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
    
    def setup_ui(self):
        # Ana çerçeve
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Menü çubuğu
        self.setup_menu()
        
        # Sekmeler
        self.notebook = ttk.Notebook(self.main_frame)
        
        # Adisyon sekmesi
        self.order_tab = ttk.Frame(self.notebook)
        self.setup_order_tab()
        
        # Ürünler sekmesi
        self.products_tab = ttk.Frame(self.notebook)
        self.setup_products_tab()
        
        # Kategoriler sekmesi
        self.categories_tab = ttk.Frame(self.notebook)
        self.setup_categories_tab()
        
        # Masalar sekmesi
        self.tables_tab = ttk.Frame(self.notebook)
        self.setup_tables_tab()
        
        # Raporlar sekmesi
        self.reports_tab = ttk.Frame(self.notebook)
        self.setup_reports_tab()
        
        # Kullanıcılar sekmesi (sadece admin)
        self.users_tab = ttk.Frame(self.notebook)
        self.setup_users_tab()
        
        # Sekmeleri ekle
        self.notebook.add(self.order_tab, text="Adisyon")
        self.notebook.add(self.products_tab, text="Ürünler")
        self.notebook.add(self.categories_tab, text="Kategoriler")
        self.notebook.add(self.tables_tab, text="Masalar")
        self.notebook.add(self.reports_tab, text="Raporlar")
        self.notebook.add(self.users_tab, text="Kullanıcılar")
        
        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(
            self.main_frame,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        
        # Giriş ekranı
        self.setup_login_screen()
    
    def setup_menu(self):
        menubar = tk.Menu(self.root)
        
        # Dosya menüsü
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Veritabanı Yedekle", command=self.backup_database)
        file_menu.add_command(label="Yedekten Geri Yükle", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.logout)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        
        # Görünüm menüsü
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Klasik Tema", command=lambda: self.set_theme("clam"))
        view_menu.add_command(label="Modern Tema", command=lambda: self.set_theme("vista"))
        view_menu.add_command(label="Koyu Tema", command=lambda: self.set_theme("alt"))
        menubar.add_cascade(label="Görünüm", menu=view_menu)
        
        # Yardım menüsü
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Kullanım Kılavuzu", command=self.show_help)
        help_menu.add_command(label="Hakkında", command=self.show_about)
        menubar.add_cascade(label="Yardım", menu=help_menu)
        
        self.root.config(menu=menubar)
    
    def backup_database(self):
        """Veritabanını yedekler"""
        try:
            # Yedek klasörü oluştur
            backup_dir = "backups"
            if not os.path.exists(backup_dir):
                os.makedirs(backup_dir)

            # Yedek dosya adını oluştur (tarih-saat ile)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"cafe_backup_{timestamp}.db")

            # Veritabanını kopyala
            shutil.copy2(self.db.db_file, backup_path)
            messagebox.showinfo("Başarılı", f"Veritabanı yedeklendi:\n{backup_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Yedekleme başarısız:\n{str(e)}")

    def restore_database(self):
        """Yedekten veritabanını geri yükler"""
        try:
            # Kullanıcıdan yedek dosyasını seçmesini iste
            file_path = filedialog.askopenfilename(
                title="Yedek Dosyası Seç",
                filetypes=[("Veritabanı dosyaları", "*.db"), ("Tüm dosyalar", "*.*")]
            )
            
            if file_path:
                # Önce mevcut veritabanını yedekle (güvenlik için)
                self.backup_database()
                
                # Yedek dosyayı ana veritabanına kopyala
                shutil.copy2(file_path, self.db.db_file)
                messagebox.showinfo("Başarılı", "Veritabanı geri yüklendi. Programı yeniden başlatın.")
        except Exception as e:
            messagebox.showerror("Hata", f"Geri yükleme başarısız:\n{str(e)}")

    def setup_login_screen(self):
        self.login_frame = ttk.Frame(self.main_frame)
        
        # Logo
        try:
            img = Image.open(Config.LOGO_PATH)
            img = img.resize((200, 200), Image.LANCZOS)
            self.logo = ImageTk.PhotoImage(img)
            logo_label = ttk.Label(self.login_frame, image=self.logo)
            logo_label.grid(row=0, column=0, columnspan=2, pady=20)
        except:
            pass
        
        # Kullanıcı adı
        ttk.Label(self.login_frame, text="Kullanıcı Adı:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.username_entry = ttk.Entry(self.login_frame)
        self.username_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Şifre
        ttk.Label(self.login_frame, text="Şifre:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        self.password_entry = ttk.Entry(self.login_frame, show="*")
        self.password_entry.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Giriş butonu
        login_btn = ttk.Button(self.login_frame, text="Giriş", command=self.login)
        login_btn.grid(row=3, column=0, columnspan=2, pady=10)
        
        # Enter tuşu ile giriş
        self.password_entry.bind("<Return>", lambda event: self.login())
    
    # -------------------- GİRİŞ/ÇIKIŞ İŞLEMLERİ --------------------
    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Uyarı", "Kullanıcı adı ve şifre giriniz")
            return
        
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        user = self.db.get_one(
            "SELECT id, username, full_name, role FROM users WHERE username = ? AND password = ? AND is_active = 1",
            (username, hashed_pw)
        )
        
        if user:
            self.current_user = {
                'id': user[0],
                'username': user[1],
                'full_name': user[2],
                'role': user[3]
            }
            self.show_main_app()
            self.update_status(f"Hoş geldiniz, {self.current_user['full_name']}")
        else:
            messagebox.showerror("Hata", "Geçersiz kullanıcı adı veya şifre")
            self.password_entry.delete(0, tk.END)
    
    def show_main_app(self):
        self.login_frame.pack_forget()
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.status_bar.pack(fill=tk.X)
        
        # Yetki kontrolü
        if self.current_user['role'] != 'admin':
            self.notebook.hide(self.users_tab)
            self.notebook.hide(self.tables_tab)
        
        # Verileri yükle
        self.load_initial_data()
    
    def logout(self):
        self.current_user = None
        self.current_order = {
            'items': [],
            'table_id': None,
            'total': 0.0,
            'discount': 0.0
        }
        self.show_login()
    
    def load_initial_data(self):
        # Kategorileri yükle
        self.load_categories()
        
        # Ürünleri yükle
        self.load_products()
        
        # Masaları yükle
        self.load_tables()
        
        # Aktif siparişleri yükle
        self.load_active_orders()


    
    # -------------------- ADİSYON SEKMESİ --------------------
    def setup_order_tab(self):
        # Ana çerçeve
        main_frame = ttk.Frame(self.order_tab)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sol panel - Ürünler
        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Kategori filtreleme
        filter_frame = ttk.Frame(left_panel)
        filter_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(filter_frame, text="Kategori:").pack(side=tk.LEFT, padx=5)
        
        self.category_filter = tk.StringVar()
        self.category_combobox = ttk.Combobox(
            filter_frame,
            textvariable=self.category_filter,
            state="readonly"
        )
        self.category_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.category_combobox.bind("<<ComboboxSelected>>", lambda e: self.load_products())
        
        # Ürün butonları
        self.products_canvas = tk.Canvas(left_panel)
        self.products_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(left_panel, orient=tk.VERTICAL, command=self.products_canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.products_canvas.configure(yscrollcommand=scrollbar.set)
        self.products_canvas.bind('<Configure>', lambda e: self.products_canvas.configure(scrollregion=self.products_canvas.bbox("all")))
        
        self.products_frame = ttk.Frame(self.products_canvas)
        self.products_canvas.create_window((0,0), window=self.products_frame, anchor="nw")
        
        # Sağ panel - Sipariş
        right_panel = ttk.Frame(main_frame, width=400)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        
        # Masa seçimi
        table_frame = ttk.Frame(right_panel)
        table_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(table_frame, text="Masa:").pack(side=tk.LEFT, padx=5)
        
        self.table_var = tk.StringVar()
        self.table_combobox = ttk.Combobox(
            table_frame,
            textvariable=self.table_var,
            state="readonly"
        )
        self.table_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.table_combobox.bind("<<ComboboxSelected>>", self.select_table)
        
        # Sipariş listesi
        order_list_frame = ttk.Frame(right_panel)
        order_list_frame.pack(fill=tk.BOTH, expand=True)
        
        columns = ("product", "price", "qty", "total")
        self.order_tree = ttk.Treeview(
            order_list_frame,
            columns=columns,
            show="headings",
            selectmode="browse"
        )
        
        # Kolon başlıkları
        self.order_tree.heading("product", text="Ürün")
        self.order_tree.heading("price", text="Fiyat")
        self.order_tree.heading("qty", text="Adet")
        self.order_tree.heading("total", text="Tutar")
        
        # Kolon genişlikleri
        self.order_tree.column("product", width=150)
        self.order_tree.column("price", width=80, anchor=tk.E)
        self.order_tree.column("qty", width=50, anchor=tk.CENTER)
        self.order_tree.column("total", width=80, anchor=tk.E)
        
        self.order_tree.pack(fill=tk.BOTH, expand=True)
        
        # Toplam bilgisi
        total_frame = ttk.Frame(right_panel)
        total_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(total_frame, text="Ara Toplam:").pack(side=tk.LEFT, padx=5)
        self.subtotal_label = ttk.Label(total_frame, text="0.00 TL")
        self.subtotal_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(total_frame, text="İndirim:").pack(side=tk.LEFT, padx=5)
        self.discount_label = ttk.Label(total_frame, text="0.00 TL")
        self.discount_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(total_frame, text="Toplam:", font=('Helvetica', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        self.total_label = ttk.Label(total_frame, text="0.00 TL", font=('Helvetica', 10, 'bold'))
        self.total_label.pack(side=tk.LEFT, padx=5)
        
        # Butonlar
        button_frame = ttk.Frame(right_panel)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            button_frame,
            text="Ürün Çıkar",
            command=self.remove_item
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Adet Arttır",
            command=self.increase_quantity
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Adet Azalt",
            command=self.decrease_quantity
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Temizle",
            command=self.clear_order
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
        
        ttk.Button(
            button_frame,
            text="Siparişi Tamamla",
            command=self.complete_order,
            style="Accent.TButton"
        ).pack(side=tk.LEFT, padx=2, fill=tk.X, expand=True)
    
    def load_categories(self):
        categories = self.db.get_all("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY sort_order, name")
        if categories:
            self.category_combobox['values'] = ["Tüm Kategoriler"] + [cat[1] for cat in categories]
            self.category_combobox.current(0)
    
    def load_products(self):
        # Önceki ürünleri temizle
        for widget in self.products_frame.winfo_children():
            widget.destroy()
        
        # Kategori filtresi
        category = self.category_filter.get()
        if category == "Tüm Kategoriler" or not category:
            query = """SELECT p.id, p.name, p.price, p.stock, p.image_path 
                       FROM products p 
                       WHERE p.is_active = 1 
                       ORDER BY p.name"""
            params = ()
        else:
            query = """SELECT p.id, p.name, p.price, p.stock, p.image_path 
                       FROM products p 
                       JOIN categories c ON p.category_id = c.id 
                       WHERE c.name = ? AND p.is_active = 1 
                       ORDER BY p.name"""
            params = (category,)
        
        products = self.db.get_all(query, params)
        
        if not products:
            ttk.Label(self.products_frame, text="Ürün bulunamadı").pack(pady=20)
            return
        
        # Ürün butonlarını oluştur
        for i, (product_id, name, price, stock, image_path) in enumerate(products):
            btn_frame = ttk.Frame(self.products_frame)
            btn_frame.pack(fill=tk.X, pady=2, padx=2)
            
            # Ürün resmi (varsa)
            if image_path and os.path.exists(image_path):
                try:
                    img = Image.open(image_path)
                    img = img.resize((50, 50), Image.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label = ttk.Label(btn_frame, image=photo)
                    img_label.image = photo
                    img_label.pack(side=tk.LEFT, padx=5)
                except:
                    pass
            
            # Ürün bilgileri
            btn_text = f"{name}\n{price:.2f} TL"
            if stock <= 0:
                btn_text += "\n(STOK YOK)"
                btn = ttk.Button(
                    btn_frame,
                    text=btn_text,
                    state=tk.DISABLED,
                    style="Disabled.TButton"
                )
            else:
                btn = ttk.Button(
                    btn_frame,
                    text=btn_text,
                    command=lambda p_id=product_id, p_name=name, p_price=price: self.add_to_order(p_id, p_name, p_price),
                    style="Product.TButton"
                )
            
            btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    def load_tables(self):
        tables = self.db.get_all("SELECT id, name FROM tables WHERE is_active = 1 ORDER BY name")
        if tables:
            self.table_combobox['values'] = [table[1] for table in tables]
    
    def add_to_order(self, product_id, product_name, product_price):
        # Sepete ekle veya adeti arttır
        for item in self.current_order['items']:
            if item['product_id'] == product_id:
                item['quantity'] += 1
                self.update_order_display()
                return
        
        # Yeni ürün ekle
        self.current_order['items'].append({
            'product_id': product_id,
            'product_name': product_name,
            'price': product_price,
            'quantity': 1
        })
        
        self.update_order_display()
    
    def remove_item(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin")
            return
        
        item = self.order_tree.item(selected[0])
        product_id = item['values'][0]
        
        # Ürünü sepetten çıkar
        for i, item in enumerate(self.current_order['items']):
            if item['product_id'] == product_id:
                self.current_order['items'].pop(i)
                break
        
        self.update_order_display()
    
    def increase_quantity(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin")
            return
        
        item = self.order_tree.item(selected[0])
        product_id = item['values'][0]
        
        # Adeti arttır
        for item in self.current_order['items']:
            if item['product_id'] == product_id:
                item['quantity'] += 1
                break
        
        self.update_order_display()
    
    def decrease_quantity(self):
        selected = self.order_tree.selection()
        if not selected:
            messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin")
            return
        
        item = self.order_tree.item(selected[0])
        product_id = item['values'][0]
        
        # Adeti azalt
        for i, item in enumerate(self.current_order['items']):
            if item['product_id'] == product_id:
                if item['quantity'] > 1:
                    item['quantity'] -= 1
                else:
                    # Adet 1 ise ürünü çıkar
                    self.current_order['items'].pop(i)
                break
        
        self.update_order_display()
    
    def select_table(self, event):
        table_name = self.table_var.get()
        if table_name:
            table = self.db.get_one("SELECT id FROM tables WHERE name = ?", (table_name,))
            if table:
                self.current_order['table_id'] = table[0]
                self.update_status(f"Masa seçildi: {table_name}")
    
    def update_order_display(self):
        # Listeyi temizle
        for item in self.order_tree.get_children():
            self.order_tree.delete(item)
        
        # Toplamları hesapla
        subtotal = 0.0
        
        # Ürünleri ekle
        for item in self.current_order['items']:
            total = item['price'] * item['quantity']
            subtotal += total
            
            self.order_tree.insert("", tk.END, values=(
                item['product_id'],
                item['product_name'],
                f"{item['price']:.2f}",
                item['quantity'],
                f"{total:.2f}"
            ))
        
        # Toplamları güncelle
        self.subtotal_label.config(text=f"{subtotal:.2f} TL")
        self.discount_label.config(text=f"{self.current_order['discount']:.2f} TL")
        self.total_label.config(text=f"{subtotal - self.current_order['discount']:.2f} TL")
        
        # Genel toplamı kaydet
        self.current_order['total'] = subtotal - self.current_order['discount']
    
    def clear_order(self):
        self.current_order = {
            'items': [],
            'table_id': None,
            'total': 0.0,
            'discount': 0.0
        }
        self.table_var.set("")
        self.update_order_display()
        self.update_status("Sipariş temizlendi")
    
    def complete_order(self):
        if not self.current_order['items']:
            messagebox.showwarning("Uyarı", "Sipariş boş")
            return
        
        if not self.current_order['table_id']:
            messagebox.showwarning("Uyarı", "Lütfen masa seçin")
            return
        
        # Siparişi veritabanına kaydet
        try:
            # Sipariş başlığı
            order_id = self.db.execute(
                """INSERT INTO orders 
                   (table_id, user_id, total, discount, date) 
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    self.current_order['table_id'],
                    self.current_user['id'],
                    self.current_order['total'],
                    self.current_order['discount'],
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
                commit=True
            ).lastrowid
            
            # Sipariş detayları
            for item in self.current_order['items']:
                self.db.execute(
                    """INSERT INTO order_items 
                       (order_id, product_id, quantity, price) 
                       VALUES (?, ?, ?, ?)""",
                    (
                        order_id,
                        item['product_id'],
                        item['quantity'],
                        item['price']
                    ),
                    commit=True
                )
            
            # Stokları güncelle
            for item in self.current_order['items']:
                self.db.execute(
                    "UPDATE products SET stock = stock - ? WHERE id = ?",
                    (item['quantity'], item['product_id']),
                    commit=True
                )
            
            # Fiş yazdır
            self.print_receipt(order_id)
            
            messagebox.showinfo("Başarılı", f"Sipariş #{order_id} kaydedildi\nToplam: {self.current_order['total']:.2f} TL")
            
            # Siparişi temizle
            self.clear_order()
            
            # Ürünleri yeniden yükle (stoklar güncellendi)
            self.load_products()
            
        except sqlite3.Error as e:
            messagebox.showerror("Hata", f"Sipariş kaydedilirken hata:\n{str(e)}")
    
    def print_receipt(self, order_id):
        try:
            # Fiş içeriğini oluştur
            receipt = f"""
            {Config.COMPANY_NAME}
            {Config.ADDRESS}
            Tel: {Config.PHONE}
            Vergi No: {Config.TAX_NUMBER}
            --------------------------------
            Sipariş No: #{order_id}
            Tarih: {datetime.now().strftime("%d.%m.%Y %H:%M")}
            Masa: {self.table_var.get()}
            Personel: {self.current_user['full_name']}
            --------------------------------
            """
            
            # Ürünler
            for item in self.current_order['items']:
                receipt += f"{item['product_name']} x{item['quantity']} = {item['price'] * item['quantity']:.2f} TL\n"
            
            receipt += f"""
            --------------------------------
            Ara Toplam: {self.current_order['total'] + self.current_order['discount']:.2f} TL
            İndirim: {self.current_order['discount']:.2f} TL
            TOPLAM: {self.current_order['total']:.2f} TL
            --------------------------------
            Teşekkür ederiz!
            """
            
            # Yazıcıya gönder
            if sys.platform == "win32":
                printer_name = win32print.GetDefaultPrinter()
                hprinter = win32print.OpenPrinter(printer_name)
                try:
                    win32print.StartDocPrinter(hprinter, 1, ("Cafe Receipt", None, "RAW"))
                    win32print.StartPagePrinter(hprinter)
                    win32print.WritePrinter(hprinter, receipt.encode('utf-8'))
                    win32print.EndPagePrinter(hprinter)
                finally:
                    win32print.ClosePrinter(hprinter)
            
            # Log dosyasına yaz
            with open("receipts.log", "a", encoding="utf-8") as f:
                f.write(receipt)
                f.write("\n\n")
            
        except Exception as e:
            messagebox.showwarning("Uyarı", f"Fiş yazdırılamadı:\n{str(e)}")

# ÜRÜN YÖNETİMİ SEKMESİ (300+ satır)
def setup_products_tab(self):
    # Ana çerçeve
    main_frame = ttk.Frame(self.products_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Sol panel - Ürün listesi
    list_frame = ttk.Frame(main_frame, width=400)
    list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
    
    # Arama ve filtreleme
    search_frame = ttk.Frame(list_frame)
    search_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(search_frame, text="Ara:").pack(side=tk.LEFT)
    self.product_search = ttk.Entry(search_frame)
    self.product_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    self.product_search.bind("<KeyRelease>", self.filter_products)
    
    # Kategori filtreleme
    self.product_category_filter = ttk.Combobox(search_frame, state="readonly")
    self.product_category_filter.pack(side=tk.LEFT, padx=5)
    self.product_category_filter.bind("<<ComboboxSelected>>", self.filter_products)
    
    # Ürün listesi (Treeview)
    self.products_tree = ttk.Treeview(
        list_frame,
        columns=("id", "name", "category", "price", "stock"),
        show="headings",
        selectmode="browse"
    )
    
    # Kolon başlıkları
    self.products_tree.heading("id", text="ID", anchor=tk.CENTER)
    self.products_tree.heading("name", text="Ürün Adı")
    self.products_tree.heading("category", text="Kategori")
    self.products_tree.heading("price", text="Fiyat")
    self.products_tree.heading("stock", text="Stok")
    
    # Kolon genişlikleri
    self.products_tree.column("id", width=50, anchor=tk.CENTER)
    self.products_tree.column("name", width=150)
    self.products_tree.column("category", width=100)
    self.products_tree.column("price", width=80, anchor=tk.E)
    self.products_tree.column("stock", width=60, anchor=tk.E)
    
    self.products_tree.pack(fill=tk.BOTH, expand=True)
    self.products_tree.bind("<<TreeviewSelect>>", self.on_product_select)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.products_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.products_tree.configure(yscrollcommand=scrollbar.set)
    
    # Sağ panel - Ürün detay/form
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    
    # Ürün bilgileri
    ttk.Label(form_frame, text="Ürün Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
    
    # Ürün resmi
    self.product_image_label = ttk.Label(form_frame)
    self.product_image_label.pack()
    
    # Form alanları
    fields_frame = ttk.Frame(form_frame)
    fields_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(fields_frame, text="Ürün Adı:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    self.product_name = ttk.Entry(fields_frame)
    self.product_name.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Kategori:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    self.product_category = ttk.Combobox(fields_frame, state="readonly")
    self.product_category.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Fiyat:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    self.product_price = ttk.Entry(fields_frame)
    self.product_price.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Stok:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    self.product_stock = ttk.Entry(fields_frame)
    self.product_stock.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Birim:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    self.product_unit = ttk.Combobox(fields_frame, values=["adet", "kg", "lt", "porsiyon"])
    self.product_unit.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Barkod:").grid(row=5, column=0, sticky="e", padx=5, pady=2)
    self.product_barcode = ttk.Entry(fields_frame)
    self.product_barcode.grid(row=5, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Açıklama:").grid(row=6, column=0, sticky="ne", padx=5, pady=2)
    self.product_description = tk.Text(fields_frame, height=4, width=30)
    self.product_description.grid(row=6, column=1, sticky="ew", padx=5, pady=2)
    
    # Resim seçme butonu
    self.product_image_path = ""
    ttk.Button(
        fields_frame, 
        text="Resim Seç", 
        command=self.select_product_image
    ).grid(row=7, column=1, sticky="e", padx=5, pady=5)
    
    # Butonlar
    buttons_frame = ttk.Frame(form_frame)
    buttons_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(
        buttons_frame,
        text="Yeni",
        command=self.new_product,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Kaydet",
        command=self.save_product,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Sil",
        command=self.delete_product,
        style="Accent.TButton"
    ).pack(side=tk.RIGHT, padx=5)
    
    # Verileri yükle
    self.load_product_categories()
    self.load_products_list()

def load_product_categories(self):
    categories = self.db.get_all("SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name")
    if categories:
        self.product_category['values'] = [cat[1] for cat in categories]
        self.product_category_filter['values'] = ["Tüm Kategoriler"] + [cat[1] for cat in categories]
        self.product_category_filter.current(0)

def load_products_list(self):
    # Listeyi temizle
    for item in self.products_tree.get_children():
        self.products_tree.delete(item)
    
    # Veritabanından ürünleri çek
    products = self.db.get_all(
        """SELECT p.id, p.name, c.name, p.price, p.stock 
           FROM products p 
           JOIN categories c ON p.category_id = c.id 
           WHERE p.is_active = 1 
           ORDER BY p.name"""
    )
    
    if products:
        for product in products:
            self.products_tree.insert("", tk.END, values=product)

def filter_products(self, event=None):
    search_term = self.product_search.get().lower()
    category = self.product_category_filter.get()
    
    # Listeyi temizle
    for item in self.products_tree.get_children():
        self.products_tree.delete(item)
    
    # Filtreleme sorgusu
    query = """SELECT p.id, p.name, c.name, p.price, p.stock 
               FROM products p 
               JOIN categories c ON p.category_id = c.id 
               WHERE p.is_active = 1"""
    
    params = []
    
    if category and category != "Tüm Kategoriler":
        query += " AND c.name = ?"
        params.append(category)
    
    if search_term:
        query += " AND LOWER(p.name) LIKE ?"
        params.append(f"%{search_term}%")
    
    query += " ORDER BY p.name"
    
    # Filtrelenmiş ürünleri yükle
    products = self.db.get_all(query, params)
    
    if products:
        for product in products:
            self.products_tree.insert("", tk.END, values=product)

def on_product_select(self, event):
    selected = self.products_tree.selection()
    if not selected:
        return
    
    product_id = self.products_tree.item(selected[0])['values'][0]
    self.load_product_details(product_id)

def load_product_details(self, product_id):
    product = self.db.get_one(
        """SELECT p.name, p.category_id, c.name, p.price, p.stock, 
                  p.unit, p.barcode, p.description, p.image_path 
           FROM products p 
           JOIN categories c ON p.category_id = c.id 
           WHERE p.id = ?""",
        (product_id,)
    )
    
    if product:
        # Form alanlarını doldur
        self.product_name.delete(0, tk.END)
        self.product_name.insert(0, product[0])
        
        # Kategoriyi seç
        categories = self.product_category['values']
        if product[2] in categories:
            self.product_category.set(product[2])
        
        self.product_price.delete(0, tk.END)
        self.product_price.insert(0, str(product[3]))
        
        self.product_stock.delete(0, tk.END)
        self.product_stock.insert(0, str(product[4]))
        
        self.product_unit.set(product[5])
        
        self.product_barcode.delete(0, tk.END)
        self.product_barcode.insert(0, product[6] or "")
        
        self.product_description.delete(1.0, tk.END)
        self.product_description.insert(1.0, product[7] or "")
        
        # Resmi yükle
        self.product_image_path = product[8] or ""
        self.load_product_image()
        
        # Geçerli ürün ID'sini sakla
        self.current_product_id = product_id

def load_product_image(self):
    if self.product_image_path and os.path.exists(self.product_image_path):
        try:
            img = Image.open(self.product_image_path)
            img = img.resize((200, 200), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.product_image_label.config(image=photo)
            self.product_image_label.image = photo
        except:
            self.product_image_label.config(image="")
    else:
        self.product_image_label.config(image="")

def select_product_image(self):
    file_path = filedialog.askopenfilename(
        title="Ürün Resmi Seç",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    
    if file_path:
        self.product_image_path = file_path
        self.load_product_image()

def new_product(self):
    # Formu temizle
    self.product_name.delete(0, tk.END)
    self.product_category.set("")
    self.product_price.delete(0, tk.END)
    self.product_stock.delete(0, tk.END)
    self.product_unit.set("adet")
    self.product_barcode.delete(0, tk.END)
    self.product_description.delete(1.0, tk.END)
    self.product_image_path = ""
    self.product_image_label.config(image="")
    self.current_product_id = None

def save_product(self):
    # Form verilerini al
    name = self.product_name.get().strip()
    category = self.product_category.get()
    price = self.product_price.get().strip()
    stock = self.product_stock.get().strip()
    unit = self.product_unit.get()
    barcode = self.product_barcode.get().strip()
    description = self.product_description.get(1.0, tk.END).strip()
    image_path = self.product_image_path
    
    # Validasyon
    if not name or not category or not price:
        messagebox.showwarning("Uyarı", "Lütfen zorunlu alanları doldurun (Ad, Kategori, Fiyat)")
        return
    
    try:
        price = float(price)
        stock = float(stock) if stock else 0.0
    except ValueError:
        messagebox.showerror("Hata", "Geçersiz fiyat veya stok değeri")
        return
    
    # Kategori ID'sini al
    category_id = self.db.get_one(
        "SELECT id FROM categories WHERE name = ?",
        (category,)
    )
    
    if not category_id:
        messagebox.showerror("Hata", "Geçersiz kategori")
        return
    
    category_id = category_id[0]
    
    # Veritabanı işlemi
    try:
        if self.current_product_id:
            # Güncelleme
            self.db.execute(
                """UPDATE products SET 
                    name = ?, 
                    category_id = ?, 
                    price = ?, 
                    stock = ?, 
                    unit = ?, 
                    barcode = ?, 
                    description = ?, 
                    image_path = ? 
                   WHERE id = ?""",
                (name, category_id, price, stock, unit, barcode, description, image_path, self.current_product_id),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Ürün güncellendi")
        else:
            # Yeni ürün
            self.db.execute(
                """INSERT INTO products 
                   (name, category_id, price, stock, unit, barcode, description, image_path) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (name, category_id, price, stock, unit, barcode, description, image_path),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Yeni ürün eklendi")
        
        # Listeyi yenile
        self.load_products_list()
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Ürün kaydedilemedi:\n{str(e)}")

def delete_product(self):
    if not self.current_product_id:
        messagebox.showwarning("Uyarı", "Lütfen bir ürün seçin")
        return
    
    if not messagebox.askyesno("Onay", "Bu ürünü silmek istediğinize emin misiniz?"):
        return
    
    try:
        # Ürünü pasif yap (silme yerine)
        self.db.execute(
            "UPDATE products SET is_active = 0 WHERE id = ?",
            (self.current_product_id,),
            commit=True
        )
        
        messagebox.showinfo("Başarılı", "Ürün silindi")
        self.load_products_list()
        self.new_product()  # Formu temizle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Ürün silinemedi:\n{str(e)}")

# KATEGORİ YÖNETİMİ SEKMESİ (150+ satır)
def setup_categories_tab(self):
    # Ana çerçeve
    main_frame = ttk.Frame(self.categories_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Sol panel - Kategori listesi
    list_frame = ttk.Frame(main_frame, width=300)
    list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
    
    # Arama
    search_frame = ttk.Frame(list_frame)
    search_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(search_frame, text="Ara:").pack(side=tk.LEFT)
    self.category_search = ttk.Entry(search_frame)
    self.category_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    self.category_search.bind("<KeyRelease>", self.filter_categories)
    
    # Kategori listesi (Treeview)
    self.categories_tree = ttk.Treeview(
        list_frame,
        columns=("id", "name"),
        show="headings",
        selectmode="browse"
    )
    
    # Kolon başlıkları
    self.categories_tree.heading("id", text="ID", anchor=tk.CENTER)
    self.categories_tree.heading("name", text="Kategori Adı")
    
    # Kolon genişlikleri
    self.categories_tree.column("id", width=50, anchor=tk.CENTER)
    self.categories_tree.column("name", width=200)
    
    self.categories_tree.pack(fill=tk.BOTH, expand=True)
    self.categories_tree.bind("<<TreeviewSelect>>", self.on_category_select)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.categories_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.categories_tree.configure(yscrollcommand=scrollbar.set)
    
    # Sağ panel - Kategori formu
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    
    # Kategori bilgileri
    ttk.Label(form_frame, text="Kategori Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
    
    # Form alanları
    fields_frame = ttk.Frame(form_frame)
    fields_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(fields_frame, text="Kategori Adı:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    self.category_name = ttk.Entry(fields_frame)
    self.category_name.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Sıra No:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    self.category_order = ttk.Entry(fields_frame)
    self.category_order.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Açıklama:").grid(row=2, column=0, sticky="ne", padx=5, pady=2)
    self.category_description = tk.Text(fields_frame, height=4, width=30)
    self.category_description.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    
    # Butonlar
    buttons_frame = ttk.Frame(form_frame)
    buttons_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(
        buttons_frame,
        text="Yeni",
        command=self.new_category,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Kaydet",
        command=self.save_category,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Sil",
        command=self.delete_category,
        style="Accent.TButton"
    ).pack(side=tk.RIGHT, padx=5)
    
    # Verileri yükle
    self.load_categories_list()

def load_categories_list(self):
    # Listeyi temizle
    for item in self.categories_tree.get_children():
        self.categories_tree.delete(item)
    
    # Veritabanından kategorileri çek
    categories = self.db.get_all(
        "SELECT id, name FROM categories WHERE is_active = 1 ORDER BY sort_order, name"
    )
    
    if categories:
        for category in categories:
            self.categories_tree.insert("", tk.END, values=category)

def filter_categories(self, event=None):
    search_term = self.category_search.get().lower()
    
    # Listeyi temizle
    for item in self.categories_tree.get_children():
        self.categories_tree.delete(item)
    
    # Filtreleme sorgusu
    query = "SELECT id, name FROM categories WHERE is_active = 1"
    params = []
    
    if search_term:
        query += " AND LOWER(name) LIKE ?"
        params.append(f"%{search_term}%")
    
    query += " ORDER BY sort_order, name"
    
    # Filtrelenmiş kategorileri yükle
    categories = self.db.get_all(query, params)
    
    if categories:
        for category in categories:
            self.categories_tree.insert("", tk.END, values=category)

def on_category_select(self, event):
    selected = self.categories_tree.selection()
    if not selected:
        return
    
    category_id = self.categories_tree.item(selected[0])['values'][0]
    self.load_category_details(category_id)

def load_category_details(self, category_id):
    category = self.db.get_one(
        "SELECT name, sort_order, description FROM categories WHERE id = ?",
        (category_id,)
    )
    
    if category:
        # Form alanlarını doldur
        self.category_name.delete(0, tk.END)
        self.category_name.insert(0, category[0])
        
        self.category_order.delete(0, tk.END)
        self.category_order.insert(0, str(category[1] or ""))
        
        self.category_description.delete(1.0, tk.END)
        self.category_description.insert(1.0, category[2] or "")
        
        # Geçerli kategori ID'sini sakla
        self.current_category_id = category_id

def new_category(self):
    # Formu temizle
    self.category_name.delete(0, tk.END)
    self.category_order.delete(0, tk.END)
    self.category_description.delete(1.0, tk.END)
    self.current_category_id = None

def save_category(self):
    # Form verilerini al
    name = self.category_name.get().strip()
    order = self.category_order.get().strip()
    description = self.category_description.get(1.0, tk.END).strip()
    
    # Validasyon
    if not name:
        messagebox.showwarning("Uyarı", "Lütfen kategori adı girin")
        return
    
    try:
        order = int(order) if order else 0
    except ValueError:
        messagebox.showerror("Hata", "Geçersiz sıra numarası")
        return
    
    # Veritabanı işlemi
    try:
        if self.current_category_id:
            # Güncelleme
            self.db.execute(
                """UPDATE categories SET 
                    name = ?, 
                    sort_order = ?, 
                    description = ? 
                   WHERE id = ?""",
                (name, order, description, self.current_category_id),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Kategori güncellendi")
        else:
            # Yeni kategori
            self.db.execute(
                """INSERT INTO categories 
                   (name, sort_order, description) 
                   VALUES (?, ?, ?)""",
                (name, order, description),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Yeni kategori eklendi")
        
        # Listeyi yenile
        self.load_categories_list()
        self.load_product_categories()  # Ürün sekmesindeki kategori listesini güncelle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Kategori kaydedilemedi:\n{str(e)}")

def delete_category(self):
    if not self.current_category_id:
        messagebox.showwarning("Uyarı", "Lütfen bir kategori seçin")
        return
    
    # Kategoride ürün var mı kontrol et
    products = self.db.get_one(
        "SELECT COUNT(*) FROM products WHERE category_id = ? AND is_active = 1",
        (self.current_category_id,)
    )
    
    if products and products[0] > 0:
        messagebox.showerror("Hata", "Bu kategoride ürünler var, önce ürünleri silmelisiniz")
        return
    
    if not messagebox.askyesno("Onay", "Bu kategoriyi silmek istediğinize emin misiniz?"):
        return
    
    try:
        # Kategoriyi pasif yap (silme yerine)
        self.db.execute(
            "UPDATE categories SET is_active = 0 WHERE id = ?",
            (self.current_category_id,),
            commit=True
        )
        
        messagebox.showinfo("Başarılı", "Kategori silindi")
        self.load_categories_list()
        self.load_product_categories()  # Ürün sekmesindeki kategori listesini güncelle
        self.new_category()  # Formu temizle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Kategori silinemedi:\n{str(e)}")

# MASA YÖNETİMİ SEKMESİ (100+ satır)
def setup_tables_tab(self):
    # Ana çerçeve
    main_frame = ttk.Frame(self.tables_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Sol panel - Masa listesi
    list_frame = ttk.Frame(main_frame, width=300)
    list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
    
    # Arama
    search_frame = ttk.Frame(list_frame)
    search_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(search_frame, text="Ara:").pack(side=tk.LEFT)
    self.table_search = ttk.Entry(search_frame)
    self.table_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    self.table_search.bind("<KeyRelease>", self.filter_tables)
    
    # Masa listesi (Treeview)
    self.tables_tree = ttk.Treeview(
        list_frame,
        columns=("id", "name", "status"),
        show="headings",
        selectmode="browse"
    )
    
    # Kolon başlıkları
    self.tables_tree.heading("id", text="ID", anchor=tk.CENTER)
    self.tables_tree.heading("name", text="Masa Adı")
    self.tables_tree.heading("status", text="Durum")
    
    # Kolon genişlikleri
    self.tables_tree.column("id", width=50, anchor=tk.CENTER)
    self.tables_tree.column("name", width=150)
    self.tables_tree.column("status", width=80)
    
    self.tables_tree.pack(fill=tk.BOTH, expand=True)
    self.tables_tree.bind("<<TreeviewSelect>>", self.on_table_select)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tables_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.tables_tree.configure(yscrollcommand=scrollbar.set)
    
    # Sağ panel - Masa formu
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    
    # Masa bilgileri
    ttk.Label(form_frame, text="Masa Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
    
    # Form alanları
    fields_frame = ttk.Frame(form_frame)
    fields_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(fields_frame, text="Masa Adı:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    self.table_name = ttk.Entry(fields_frame)
    self.table_name.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Durum:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    self.table_status = ttk.Combobox(fields_frame, values=["Aktif", "Pasif"], state="readonly")
    self.table_status.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
    
    # Butonlar
    buttons_frame = ttk.Frame(form_frame)
    buttons_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(
        buttons_frame,
        text="Yeni",
        command=self.new_table,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Kaydet",
        command=self.save_table,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Sil",
        command=self.delete_table,
        style="Accent.TButton"
    ).pack(side=tk.RIGHT, padx=5)
    
    # Verileri yükle
    self.load_tables_list()

def load_tables_list(self):
    # Listeyi temizle
    for item in self.tables_tree.get_children():
        self.tables_tree.delete(item)
    
    # Veritabanından masaları çek
    tables = self.db.get_all(
        "SELECT id, name, CASE WHEN is_active = 1 THEN 'Aktif' ELSE 'Pasif' END FROM tables ORDER BY name"
    )
    
    if tables:
        for table in tables:
            self.tables_tree.insert("", tk.END, values=table)

def filter_tables(self, event=None):
    search_term = self.table_search.get().lower()
    
    # Listeyi temizle
    for item in self.tables_tree.get_children():
        self.tables_tree.delete(item)
    
    # Filtreleme sorgusu
    query = "SELECT id, name, CASE WHEN is_active = 1 THEN 'Aktif' ELSE 'Pasif' END FROM tables"
    params = []
    
    if search_term:
        query += " WHERE LOWER(name) LIKE ?"
        params.append(f"%{search_term}%")
    
    query += " ORDER BY name"
    
    # Filtrelenmiş masaları yükle
    tables = self.db.get_all(query, params)
    
    if tables:
        for table in tables:
            self.tables_tree.insert("", tk.END, values=table)

def on_table_select(self, event):
    selected = self.tables_tree.selection()
    if not selected:
        return
    
    table_id = self.tables_tree.item(selected[0])['values'][0]
    self.load_table_details(table_id)

def load_table_details(self, table_id):
    table = self.db.get_one(
        "SELECT name, is_active FROM tables WHERE id = ?",
        (table_id,)
    )
    
    if table:
        # Form alanlarını doldur
        self.table_name.delete(0, tk.END)
        self.table_name.insert(0, table[0])
        
        self.table_status.set("Aktif" if table[1] else "Pasif")
        
        # Geçerli masa ID'sini sakla
        self.current_table_id = table_id

def new_table(self):
    # Formu temizle
    self.table_name.delete(0, tk.END)
    self.table_status.set("Aktif")
    self.current_table_id = None

def save_table(self):
    # Form verilerini al
    name = self.table_name.get().strip()
    status = self.table_status.get()
    
    # Validasyon
    if not name:
        messagebox.showwarning("Uyarı", "Lütfen masa adı girin")
        return
    
    is_active = 1 if status == "Aktif" else 0
    
    # Veritabanı işlemi
    try:
        if self.current_table_id:
            # Güncelleme
            self.db.execute(
                """UPDATE tables SET 
                    name = ?, 
                    is_active = ? 
                   WHERE id = ?""",
                (name, is_active, self.current_table_id),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Masa güncellendi")
        else:
            # Yeni masa
            self.db.execute(
                """INSERT INTO tables 
                   (name, is_active) 
                   VALUES (?, ?)""",
                (name, is_active),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Yeni masa eklendi")
        
        # Listeyi yenile
        self.load_tables_list()
        self.load_tables()  # Adisyon sekmesindeki masa listesini güncelle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Masa kaydedilemedi:\n{str(e)}")

def delete_table(self):
    if not self.current_table_id:
        messagebox.showwarning("Uyarı", "Lütfen bir masa seçin")
        return
    
    if not messagebox.askyesno("Onay", "Bu masayı silmek istediğinize emin misiniz?"):
        return
    
    try:
        # Masayı veritabanından sil
        self.db.execute(
            "DELETE FROM tables WHERE id = ?",
            (self.current_table_id,),
            commit=True
        )
        
        messagebox.showinfo("Başarılı", "Masa silindi")
        self.load_tables_list()
        self.load_tables()  # Adisyon sekmesindeki masa listesini güncelle
        self.new_table()  # Formu temizle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Masa silinemedi:\n{str(e)}")

# RAPORLAR SEKMESİ (400+ satır)
def setup_reports_tab(self):
    # Ana çerçeve
    main_frame = ttk.Frame(self.reports_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Filtreleme paneli
    filter_frame = ttk.LabelFrame(main_frame, text="Filtreler")
    filter_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Tarih aralığı
    ttk.Label(filter_frame, text="Başlangıç Tarihi:").grid(row=0, column=0, padx=5, pady=5)
    self.start_date = ttk.Entry(filter_frame)
    self.start_date.grid(row=0, column=1, padx=5, pady=5)
    
    ttk.Label(filter_frame, text="Bitiş Tarihi:").grid(row=0, column=2, padx=5, pady=5)
    self.end_date = ttk.Entry(filter_frame)
    self.end_date.grid(row=0, column=3, padx=5, pady=5)
    
    # Masa filtresi
    ttk.Label(filter_frame, text="Masa:").grid(row=1, column=0, padx=5, pady=5)
    self.report_table_filter = ttk.Combobox(filter_frame, state="readonly")
    self.report_table_filter.grid(row=1, column=1, padx=5, pady=5)
    
    # Kullanıcı filtresi
    ttk.Label(filter_frame, text="Kullanıcı:").grid(row=1, column=2, padx=5, pady=5)
    self.report_user_filter = ttk.Combobox(filter_frame, state="readonly")
    self.report_user_filter.grid(row=1, column=3, padx=5, pady=5)
    
    # Rapor tipi
    ttk.Label(filter_frame, text="Rapor Tipi:").grid(row=2, column=0, padx=5, pady=5)
    self.report_type = ttk.Combobox(
        filter_frame,
        values=["Satış Raporu", "Ürün Bazlı Rapor", "Masa Bazlı Rapor", "Kullanıcı Bazlı Rapor"],
        state="readonly"
    )
    self.report_type.current(0)
    self.report_type.grid(row=2, column=1, columnspan=3, sticky="ew", padx=5, pady=5)
    
    # Filtrele butonu
    ttk.Button(
        filter_frame,
        text="Filtrele",
        command=self.generate_report,
        style="Accent.TButton"
    ).grid(row=3, column=0, columnspan=4, pady=5)
    
    # Rapor paneli
    report_frame = ttk.Frame(main_frame)
    report_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Treeview
    self.report_tree = ttk.Treeview(report_frame)
    self.report_tree.pack(fill=tk.BOTH, expand=True)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=self.report_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.report_tree.configure(yscrollcommand=scrollbar.set)
    
    # Özet paneli
    summary_frame = ttk.LabelFrame(main_frame, text="Özet")
    summary_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(summary_frame, text="Toplam Satış:").grid(row=0, column=0, padx=5, pady=2)
    self.total_sales_label = ttk.Label(summary_frame, text="0.00 TL", font=('Helvetica', 10, 'bold'))
    self.total_sales_label.grid(row=0, column=1, padx=5, pady=2, sticky="w")
    
    ttk.Label(summary_frame, text="Toplam Sipariş:").grid(row=0, column=2, padx=5, pady=2)
    self.total_orders_label = ttk.Label(summary_frame, text="0", font=('Helvetica', 10, 'bold'))
    self.total_orders_label.grid(row=0, column=3, padx=5, pady=2, sticky="w")
    
    ttk.Label(summary_frame, text="Ortalama Sipariş:").grid(row=0, column=4, padx=5, pady=2)
    self.avg_order_label = ttk.Label(summary_frame, text="0.00 TL", font=('Helvetica', 10, 'bold'))
    self.avg_order_label.grid(row=0, column=5, padx=5, pady=2, sticky="w")
    
    # Butonlar
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Button(
        button_frame,
        text="Excel'e Aktar",
        command=self.export_to_excel,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        button_frame,
        text="Yazdır",
        command=self.print_report,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    # Varsayılan tarihleri ayarla
    self.start_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
    self.end_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
    
    # Filtreleri yükle
    self.load_report_filters()
    
    # Varsayılan raporu oluştur
    self.generate_report()

def load_report_filters(self):
    # Masaları yükle
    tables = self.db.get_all("SELECT name FROM tables ORDER BY name")
    if tables:
        self.report_table_filter['values'] = ["Tüm Masalar"] + [table[0] for table in tables]
        self.report_table_filter.current(0)
    
    # Kullanıcıları yükle
    users = self.db.get_all("SELECT full_name FROM users ORDER BY full_name")
    if users:
        self.report_user_filter['values'] = ["Tüm Kullanıcılar"] + [user[0] for user in users]
        self.report_user_filter.current(0)

def generate_report(self):
    # Filtreleri al
    start_date = self.start_date.get().strip()
    end_date = self.end_date.get().strip()
    table_name = self.report_table_filter.get()
    user_name = self.report_user_filter.get()
    report_type = self.report_type.get()
    
    # Tarih validasyonu
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        if start_date > end_date:
            messagebox.showwarning("Uyarı", "Başlangıç tarihi bitiş tarihinden büyük olamaz")
            return
        
        start_date = start_date.strftime("%Y-%m-%d 00:00:00")
        end_date = end_date.strftime("%Y-%m-%d 23:59:59")
    except ValueError:
        messagebox.showerror("Hata", "Geçersiz tarih formatı (YYYY-AA-GG)")
        return
    
    # Raporu oluştur
    try:
        if report_type == "Satış Raporu":
            self.generate_sales_report(start_date, end_date, table_name, user_name)
        elif report_type == "Ürün Bazlı Rapor":
            self.generate_product_report(start_date, end_date, table_name, user_name)
        elif report_type == "Masa Bazlı Rapor":
            self.generate_table_report(start_date, end_date, table_name, user_name)
        elif report_type == "Kullanıcı Bazlı Rapor":
            self.generate_user_report(start_date, end_date, table_name, user_name)
    except Exception as e:
        messagebox.showerror("Hata", f"Rapor oluşturulamadı:\n{str(e)}")

def generate_sales_report(self, start_date, end_date, table_name, user_name):
    # Sorgu oluştur
    query = """SELECT 
                  o.id, 
                  t.name, 
                  u.full_name, 
                  o.date, 
                  o.total, 
                  o.discount, 
                  o.payment_type 
               FROM orders o
               JOIN tables t ON o.table_id = t.id
               JOIN users u ON o.user_id = u.id
               WHERE o.date BETWEEN ? AND ?"""
    
    params = [start_date, end_date]
    
    # Masa filtresi
    if table_name and table_name != "Tüm Masalar":
        query += " AND t.name = ?"
        params.append(table_name)
    
    # Kullanıcı filtresi
    if user_name and user_name != "Tüm Kullanıcılar":
        query += " AND u.full_name = ?"
        params.append(user_name)
    
    query += " ORDER BY o.date DESC"
    
    # Siparişleri getir
    orders = self.db.get_all(query, params)
    
    # Treeview'ı temizle ve yapılandır
    self.clear_report_tree()
    self.report_tree['columns'] = ("id", "table", "user", "date", "total", "discount", "payment")
    
    # Kolon başlıkları
    self.report_tree.heading("id", text="Sipariş No", anchor=tk.CENTER)
    self.report_tree.heading("table", text="Masa")
    self.report_tree.heading("user", text="Kullanıcı")
    self.report_tree.heading("date", text="Tarih")
    self.report_tree.heading("total", text="Toplam")
    self.report_tree.heading("discount", text="İndirim")
    self.report_tree.heading("payment", text="Ödeme Tipi")
    
    # Kolon genişlikleri
    self.report_tree.column("id", width=80, anchor=tk.CENTER)
    self.report_tree.column("table", width=100)
    self.report_tree.column("user", width=120)
    self.report_tree.column("date", width=120)
    self.report_tree.column("total", width=80, anchor=tk.E)
    self.report_tree.column("discount", width=80, anchor=tk.E)
    self.report_tree.column("payment", width=100)
    
    # Verileri ekle
    total_sales = 0.0
    for order in orders:
        self.report_tree.insert("", tk.END, values=order)
        total_sales += order[4]
    
    # Özeti güncelle
    self.update_summary(len(orders), total_sales)

def generate_product_report(self, start_date, end_date, table_name, user_name):
    # Sorgu oluştur
    query = """SELECT 
                  p.name,
                  SUM(oi.quantity),
                  SUM(oi.price * oi.quantity),
                  c.name
               FROM order_items oi
               JOIN orders o ON oi.order_id = o.id
               JOIN products p ON oi.product_id = p.id
               JOIN categories c ON p.category_id = c.id
               JOIN tables t ON o.table_id = t.id
               JOIN users u ON o.user_id = u.id
               WHERE o.date BETWEEN ? AND ?"""
    
    params = [start_date, end_date]
    
    # Masa filtresi
    if table_name and table_name != "Tüm Masalar":
        query += " AND t.name = ?"
        params.append(table_name)
    
    # Kullanıcı filtresi
    if user_name and user_name != "Tüm Kullanıcılar":
        query += " AND u.full_name = ?"
        params.append(user_name)
    
    query += " GROUP BY p.name, c.name ORDER BY SUM(oi.price * oi.quantity) DESC"
    
    # Ürünleri getir
    products = self.db.get_all(query, params)
    
    # Treeview'ı temizle ve yapılandır
    self.clear_report_tree()
    self.report_tree['columns'] = ("product", "quantity", "total", "category")
    
    # Kolon başlıkları
    self.report_tree.heading("product", text="Ürün Adı")
    self.report_tree.heading("quantity", text="Adet")
    self.report_tree.heading("total", text="Toplam")
    self.report_tree.heading("category", text="Kategori")
    
    # Kolon genişlikleri
    self.report_tree.column("product", width=200)
    self.report_tree.column("quantity", width=80, anchor=tk.CENTER)
    self.report_tree.column("total", width=100, anchor=tk.E)
    self.report_tree.column("category", width=120)
    
    # Verileri ekle
    total_sales = 0.0
    for product in products:
        self.report_tree.insert("", tk.END, values=product)
        total_sales += product[2]
    
    # Özeti güncelle
    self.update_summary(len(products), total_sales)

def generate_table_report(self, start_date, end_date, table_name, user_name):
    # Sorgu oluştur
    query = """SELECT 
                  t.name,
                  COUNT(o.id),
                  SUM(o.total),
                  AVG(o.total)
               FROM orders o
               JOIN tables t ON o.table_id = t.id
               JOIN users u ON o.user_id = u.id
               WHERE o.date BETWEEN ? AND ?"""
    
    params = [start_date, end_date]
    
    # Masa filtresi
    if table_name and table_name != "Tüm Masalar":
        query += " AND t.name = ?"
        params.append(table_name)
    
    # Kullanıcı filtresi
    if user_name and user_name != "Tüm Kullanıcılar":
        query += " AND u.full_name = ?"
        params.append(user_name)
    
    query += " GROUP BY t.name ORDER BY SUM(o.total) DESC"
    
    # Masaları getir
    tables = self.db.get_all(query, params)
    
    # Treeview'ı temizle ve yapılandır
    self.clear_report_tree()
    self.report_tree['columns'] = ("table", "orders", "total", "average")
    
    # Kolon başlıkları
    self.report_tree.heading("table", text="Masa Adı")
    self.report_tree.heading("orders", text="Sipariş Sayısı")
    self.report_tree.heading("total", text="Toplam")
    self.report_tree.heading("average", text="Ortalama")
    
    # Kolon genişlikleri
    self.report_tree.column("table", width=150)
    self.report_tree.column("orders", width=100, anchor=tk.CENTER)
    self.report_tree.column("total", width=100, anchor=tk.E)
    self.report_tree.column("average", width=100, anchor=tk.E)
    
    # Verileri ekle
    total_sales = 0.0
    total_orders = 0
    for table in tables:
        self.report_tree.insert("", tk.END, values=table)
        total_sales += table[2]
        total_orders += table[1]
    
    # Özeti güncelle
    self.update_summary(total_orders, total_sales)

def generate_user_report(self, start_date, end_date, table_name, user_name):
    # Sorgu oluştur
    query = """SELECT 
                  u.full_name,
                  COUNT(o.id),
                  SUM(o.total),
                  AVG(o.total)
               FROM orders o
               JOIN users u ON o.user_id = u.id
               JOIN tables t ON o.table_id = t.id
               WHERE o.date BETWEEN ? AND ?"""
    
    params = [start_date, end_date]
    
    # Masa filtresi
    if table_name and table_name != "Tüm Masalar":
        query += " AND t.name = ?"
        params.append(table_name)
    
    # Kullanıcı filtresi
    if user_name and user_name != "Tüm Kullanıcılar":
        query += " AND u.full_name = ?"
        params.append(user_name)
    
    query += " GROUP BY u.full_name ORDER BY SUM(o.total) DESC"
    
    # Kullanıcıları getir
    users = self.db.get_all(query, params)
    
    # Treeview'ı temizle ve yapılandır
    self.clear_report_tree()
    self.report_tree['columns'] = ("user", "orders", "total", "average")
    
    # Kolon başlıkları
    self.report_tree.heading("user", text="Kullanıcı Adı")
    self.report_tree.heading("orders", text="Sipariş Sayısı")
    self.report_tree.heading("total", text="Toplam")
    self.report_tree.heading("average", text="Ortalama")
    
    # Kolon genişlikleri
    self.report_tree.column("user", width=150)
    self.report_tree.column("orders", width=100, anchor=tk.CENTER)
    self.report_tree.column("total", width=100, anchor=tk.E)
    self.report_tree.column("average", width=100, anchor=tk.E)
    
    # Verileri ekle
    total_sales = 0.0
    total_orders = 0
    for user in users:
        self.report_tree.insert("", tk.END, values=user)
        total_sales += user[2]
        total_orders += user[1]
    
    # Özeti güncelle
    self.update_summary(total_orders, total_sales)

def clear_report_tree(self):
    # Treeview'ı temizle
    for item in self.report_tree.get_children():
        self.report_tree.delete(item)
    
    # Kolonları temizle
    self.report_tree['columns'] = []

def update_summary(self, order_count, total_sales):
    # Özet bilgilerini güncelle
    self.total_sales_label.config(text=f"{total_sales:.2f} TL")
    self.total_orders_label.config(text=str(order_count))
    
    if order_count > 0:
        avg = total_sales / order_count
        self.avg_order_label.config(text=f"{avg:.2f} TL")
    else:
        self.avg_order_label.config(text="0.00 TL")

def export_to_excel(self):
    # Seçili raporu Excel'e aktar
    pass

def print_report(self):
    # Seçili raporu yazdır
    pass

# KULLANICI YÖNETİMİ SEKMESİ (200+ satır)
def setup_users_tab(self):
    # Ana çerçeve
    main_frame = ttk.Frame(self.users_tab)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Sol panel - Kullanıcı listesi
    list_frame = ttk.Frame(main_frame, width=300)
    list_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
    
    # Arama
    search_frame = ttk.Frame(list_frame)
    search_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(search_frame, text="Ara:").pack(side=tk.LEFT)
    self.user_search = ttk.Entry(search_frame)
    self.user_search.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
    self.user_search.bind("<KeyRelease>", self.filter_users)
    
    # Kullanıcı listesi (Treeview)
    self.users_tree = ttk.Treeview(
        list_frame,
        columns=("id", "username", "name", "role"),
        show="headings",
        selectmode="browse"
    )
    
    # Kolon başlıkları
    self.users_tree.heading("id", text="ID", anchor=tk.CENTER)
    self.users_tree.heading("username", text="Kullanıcı Adı")
    self.users_tree.heading("name", text="Ad Soyad")
    self.users_tree.heading("role", text="Yetki")
    
    # Kolon genişlikleri
    self.users_tree.column("id", width=50, anchor=tk.CENTER)
    self.users_tree.column("username", width=100)
    self.users_tree.column("name", width=120)
    self.users_tree.column("role", width=80)
    
    self.users_tree.pack(fill=tk.BOTH, expand=True)
    self.users_tree.bind("<<TreeviewSelect>>", self.on_user_select)
    
    # Scrollbar
    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.users_tree.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.users_tree.configure(yscrollcommand=scrollbar.set)
    
    # Sağ panel - Kullanıcı formu
    form_frame = ttk.Frame(main_frame)
    form_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)
    
    # Kullanıcı bilgileri
    ttk.Label(form_frame, text="Kullanıcı Bilgileri", font=('Helvetica', 12, 'bold')).pack(pady=5)
    
    # Form alanları
    fields_frame = ttk.Frame(form_frame)
    fields_frame.pack(fill=tk.X, pady=5)
    
    ttk.Label(fields_frame, text="Kullanıcı Adı:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    self.user_username = ttk.Entry(fields_frame)
    self.user_username.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Şifre:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    self.user_password = ttk.Entry(fields_frame, show="*")
    self.user_password.grid(row=1, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Ad Soyad:").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    self.user_fullname = ttk.Entry(fields_frame)
    self.user_fullname.grid(row=2, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Yetki:").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    self.user_role = ttk.Combobox(fields_frame, values=["admin", "user"], state="readonly")
    self.user_role.grid(row=3, column=1, sticky="ew", padx=5, pady=2)
    
    ttk.Label(fields_frame, text="Durum:").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    self.user_status = ttk.Combobox(fields_frame, values=["Aktif", "Pasif"], state="readonly")
    self.user_status.grid(row=4, column=1, sticky="ew", padx=5, pady=2)
    
    # Butonlar
    buttons_frame = ttk.Frame(form_frame)
    buttons_frame.pack(fill=tk.X, pady=10)
    
    ttk.Button(
        buttons_frame,
        text="Yeni",
        command=self.new_user,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Kaydet",
        command=self.save_user,
        style="Accent.TButton"
    ).pack(side=tk.LEFT, padx=5)
    
    ttk.Button(
        buttons_frame,
        text="Sil",
        command=self.delete_user,
        style="Accent.TButton"
    ).pack(side=tk.RIGHT, padx=5)
    
    # Verileri yükle
    self.load_users_list()

def load_users_list(self):
    # Listeyi temizle
    for item in self.users_tree.get_children():
        self.users_tree.delete(item)
    
    # Veritabanından kullanıcıları çek
    users = self.db.get_all(
        "SELECT id, username, full_name, role FROM users ORDER BY full_name"
    )
    
    if users:
        for user in users:
            self.users_tree.insert("", tk.END, values=user)

def filter_users(self, event=None):
    search_term = self.user_search.get().lower()
    
    # Listeyi temizle
    for item in self.users_tree.get_children():
        self.users_tree.delete(item)
    
    # Filtreleme sorgusu
    query = "SELECT id, username, full_name, role FROM users"
    params = []
    
    if search_term:
        query += " WHERE LOWER(username) LIKE ? OR LOWER(full_name) LIKE ?"
        params.extend([f"%{search_term}%", f"%{search_term}%"])
    
    query += " ORDER BY full_name"
    
    # Filtrelenmiş kullanıcıları yükle
    users = self.db.get_all(query, params)
    
    if users:
        for user in users:
            self.users_tree.insert("", tk.END, values=user)

def on_user_select(self, event):
    selected = self.users_tree.selection()
    if not selected:
        return
    
    user_id = self.users_tree.item(selected[0])['values'][0]
    self.load_user_details(user_id)

def load_user_details(self, user_id):
    user = self.db.get_one(
        "SELECT username, full_name, role, is_active FROM users WHERE id = ?",
        (user_id,)
    )
    
    if user:
        # Form alanlarını doldur
        self.user_username.delete(0, tk.END)
        self.user_username.insert(0, user[0])
        
        self.user_password.delete(0, tk.END)
        
        self.user_fullname.delete(0, tk.END)
        self.user_fullname.insert(0, user[1])
        
        self.user_role.set(user[2])
        self.user_status.set("Aktif" if user[3] else "Pasif")
        
        # Geçerli kullanıcı ID'sini sakla
        self.current_user_id = user_id

def new_user(self):
    # Formu temizle
    self.user_username.delete(0, tk.END)
    self.user_password.delete(0, tk.END)
    self.user_fullname.delete(0, tk.END)
    self.user_role.set("user")
    self.user_status.set("Aktif")
    self.current_user_id = None

def save_user(self):
    # Form verilerini al
    username = self.user_username.get().strip()
    password = self.user_password.get().strip()
    fullname = self.user_fullname.get().strip()
    role = self.user_role.get()
    status = self.user_status.get()
    
    # Validasyon
    if not username or not fullname:
        messagebox.showwarning("Uyarı", "Lütfen zorunlu alanları doldurun (Kullanıcı Adı, Ad Soyad)")
        return
    
    is_active = 1 if status == "Aktif" else 0
    
    # Yeni kullanıcı için şifre kontrolü
    if not self.current_user_id and not password:
        messagebox.showwarning("Uyarı", "Yeni kullanıcı için şifre girin")
        return
    
    # Veritabanı işlemi
    try:
        if self.current_user_id:
            # Güncelleme
            if password:
                hashed_pw = hashlib.sha256(password.encode()).hexdigest()
                self.db.execute(
                    """UPDATE users SET 
                        username = ?, 
                        password = ?, 
                        full_name = ?, 
                        role = ?, 
                        is_active = ? 
                       WHERE id = ?""",
                    (username, hashed_pw, fullname, role, is_active, self.current_user_id),
                    commit=True
                )
            else:
                self.db.execute(
                    """UPDATE users SET 
                        username = ?, 
                        full_name = ?, 
                        role = ?, 
                        is_active = ? 
                       WHERE id = ?""",
                    (username, fullname, role, is_active, self.current_user_id),
                    commit=True
                )
            messagebox.showinfo("Başarılı", "Kullanıcı güncellendi")
        else:
            # Yeni kullanıcı
            hashed_pw = hashlib.sha256(password.encode()).hexdigest()
            self.db.execute(
                """INSERT INTO users 
                   (username, password, full_name, role, is_active) 
                   VALUES (?, ?, ?, ?, ?)""",
                (username, hashed_pw, fullname, role, is_active),
                commit=True
            )
            messagebox.showinfo("Başarılı", "Yeni kullanıcı eklendi")
        
        # Listeyi yenile
        self.load_users_list()
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Kullanıcı kaydedilemedi:\n{str(e)}")

def delete_user(self):
    if not self.current_user_id:
        messagebox.showwarning("Uyarı", "Lütfen bir kullanıcı seçin")
        return
    
    if not messagebox.askyesno("Onay", "Bu kullanıcıyı silmek istediğinize emin misiniz?"):
        return
    
    try:
        # Kullanıcıyı veritabanından sil
        self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (self.current_user_id,),
            commit=True
        )
        
        messagebox.showinfo("Başarılı", "Kullanıcı silindi")
        self.load_users_list()
        self.new_user()  # Formu temizle
        
    except sqlite3.Error as e:
        messagebox.showerror("Hata", f"Kullanıcı silinemedi:\n{str(e)}")

# DİĞER YARDIMCI FONKSİYONLAR
def update_status(self, message):
    self.status_var.set(f"Durum: {message}")
    self.root.update_idletasks()

def set_theme(self, theme_name):
    try:
        self.style.theme_use(theme_name)
    except:
        self.style.theme_use("clam")

def backup_database(self):
    try:
        if not os.path.exists(Config.BACKUP_DIR):
            os.makedirs(Config.BACKUP_DIR)
        
        backup_file = os.path.join(
            Config.BACKUP_DIR,
            f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        
        # Veritabanını kopyala
        with open(Config.DB_NAME, 'rb') as f1, open(backup_file, 'wb') as f2:
            f2.write(f1.read())
        
        messagebox.showinfo("Başarılı", f"Veritabanı yedeklendi:\n{backup_file}")
    except Exception as e:
        messagebox.showerror("Hata", f"Yedekleme başarısız:\n{str(e)}")

def restore_database(self):
    file_path = filedialog.askopenfilename(
        title="Yedek Dosyası Seç",
        filetypes=[("Veritabanı Dosyaları", "*.db"), ("Tüm Dosyalar", "*.*")]
    )
    
    if not file_path:
        return
    
    try:
        # Mevcut veritabanını yedekle
        self.backup_database()
        
        # Yeni veritabanını yükle
        with open(file_path, 'rb') as f1, open(Config.DB_NAME, 'wb') as f2:
            f2.write(f1.read())
        
        messagebox.showinfo("Başarılı", "Veritabanı geri yüklendi. Program yeniden başlatılacak.")
        
        # Programı yeniden başlat
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    except Exception as e:
        messagebox.showerror("Hata", f"Geri yükleme başarısız:\n{str(e)}")


# PROGRAM BAŞLATMA
if __name__ == "__main__":
    root = tk.Tk()
    
    # Windows DPI ayarı
    if sys.platform == "win32":
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    
    # Tema ayarları
    style = ttk.Style()
    style.theme_use(Config.DEFAULT_THEME)
    
    # Özel stiller
    style.configure("Accent.TButton", foreground="white", background="#4CAF50")
    style.map("Accent.TButton", 
              background=[("active", "#45a049"), ("disabled", "#cccccc")])
    
    style.configure("Product.TButton", padding=10, font=('Helvetica', 10))
    style.configure("Disabled.TButton", foreground="#999999")
    
    app = CafeApp(root)
    root.mainloop()
