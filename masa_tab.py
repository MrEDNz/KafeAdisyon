import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import constants
import math
from datetime import datetime, timedelta # timedelta eklendi

class MasaTab:
    def __init__(self, parent_notebook, app):
        self.app = app
        # Sekmenin ana çerçevesi
        # padding'i sadece üstten ve alttan verelim, yanlardan boşluklar iç çerçevelerde olacak
        self.frame = ttk.Frame(parent_notebook, padding=(0, 10, 0, 10))
        parent_notebook.add(self.frame, text="Masalar")

        # Masa butonlarını tutacak liste
        self.masa_buttons = []
        # Seçili masa numarasını tutacak değişken
        self.selected_masa_no = None
        # Seçili masa butonunu tutacak değişken (görsel işaretleme için)
        self.selected_masa_button = None

        # Geçikmiş masa kontrolü için after id'si
        self._late_table_check_id = None # <<< Yeni değişken

        self._create_ui()

        # Masa butonlarını içeren çerçevenin boyutu değiştiğinde yeniden düzenle
        self.masa_button_frame.bind('<Configure>', self.rearrange_masa_buttons, add=True)

        # Saat güncelleme döngüsünü başlat
        self.update_clock() # <<< Saat güncelleme başlatıldı

        # Geçikmiş masa kontrolünü başlat
        self.start_late_table_check() # <<< Kontrol başlatıldı


    def _create_ui(self):
        """Masalar sekmesi arayüzünü oluşturur."""
        # Üstteki boşluk çerçevesi (isteğe bağlı, görsel dengeleme için)
        # top_spacer_frame = ttk.Frame(self.frame, height=10) # Örnek olarak 10 piksel boşluk
        # top_spacer_frame.pack(side=tk.TOP, fill=tk.X)

        # Masa butonlarını tutacak Frame
        # Bu Frame, üstteki boşluk (varsa), alttaki kontrol çerçevesi ve kendi padding'leri haricinde kalan tüm alanı dolduracak
        self.masa_button_frame = ttk.Frame(self.frame)
        self.masa_button_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Alt kontrol çerçevesi: Mevcut Zaman ve Masa Ekle/Sil butonlarını içerir
        # Bu çerçeve Masa sekmesi çerçevesinin en altına paketlenecek
        bottom_control_frame = ttk.Frame(self.frame, padding=(10, 0, 10, 0))
        # side=tk.BOTTOM ile Masa sekmesi çerçevesinin en altına yerleştir
        # fill=tk.X ile yatayda tam doldurmasını sağla
        bottom_control_frame.pack(side=tk.BOTTOM, fill=tk.X)


        # Mevcut Zaman Etiketi (Alt kontrol çerçevesi içinde)
        self.lbl_mevcut_zaman = ttk.Label(bottom_control_frame, text="", font=('Arial', 10))
        # side=tk.LEFT ile alt çerçeve içinde sola paketle
        self.lbl_mevcut_zaman.pack(side=tk.LEFT)

        # Masa Ekle/Sil Butonları Alanı (Alt kontrol çerçevesi içinde)
        masa_kontrol_frame = ttk.Frame(bottom_control_frame)
        # side=tk.RIGHT ile alt çerçeve içinde sağa paketle
        masa_kontrol_frame.pack(side=tk.RIGHT)


        # Masa Ekle ve Masa Sil butonları (Masa kontrol çerçevesi içinde)
        # command'leri MasaTab sınıfındaki metodlara bağlı olacak, main.py'deki metodları çağıracaklar
        self.btn_masa_ekle = ttk.Button(masa_kontrol_frame, text="Masa Ekle", command=self._add_masa_command)
        self.btn_masa_ekle.pack(side=tk.LEFT, padx=5)

        self.btn_masa_sil = ttk.Button(masa_kontrol_frame, text="Masa Sil", command=self._delete_masa_command)
        self.btn_masa_sil.pack(side=tk.LEFT, padx=5)


    def update_clock(self):
        """Mevcut zaman etiketini günceller."""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self, 'lbl_mevcut_zaman') and self.lbl_mevcut_zaman.winfo_exists():
             self.lbl_mevcut_zaman.config(text=f"Mevcut Zaman: {now}")
        # MasaTab'ın çerçevesi yok edildiğinde after döngüsünü durdurmak için kontrol ekleyelim
        if self.frame.winfo_exists():
             self.frame.after(1000, self.update_clock)
        else:
             print("MasaTab çerçevesi yok edildi, saat güncelleme durduruldu.")

    def start_late_table_check(self):
        """Geçikmiş masa kontrol döngüsünü başlatır."""
        if self._late_table_check_id is None and self.frame.winfo_exists():
             self._check_late_tables() # İlk kontrolü hemen yap
             # Periyodik kontrolü başlat
             self._late_table_check_id = self.frame.after(constants.LATE_TABLE_CHECK_INTERVAL_MS, self._check_late_tables)
             print("Geçikmiş masa kontrolü başlatıldı.")

    def stop_late_table_check(self):
        """Geçikmiş masa kontrol döngüsünü durdurur."""
        if self._late_table_check_id is not None:
            self.frame.after_cancel(self._late_table_check_id)
            self._late_table_check_id = None
            print("Geçikmiş masa kontrolü durduruldu.")


    def _check_late_tables(self):
        """Dolu masaların son işlem zamanını kontrol eder ve stilini günceller."""
        try:
            # Sadece 'Dolu' durumdaki masaları ve aktif siparişlerinin son işlem zamanını çek
            self.app.db_manager.cursor.execute("""
                SELECT m.masa_no, m.durum, sg.son_islem_zamani
                FROM masalar m
                JOIN siparis_gecmisi sg ON m.aktif_siparis_id = sg.siparis_id
                WHERE m.durum = 'Dolu' OR m.durum = 'Geçikmiş' -- Sadece dolu veya geçikmiş masaları kontrol et
            """)
            dolu_masalar = self.app.db_manager.cursor.fetchall()

            now = datetime.now()
            late_threshold = timedelta(minutes=constants.LATE_TABLE_THRESHOLD_MINUTES)

            for masa in dolu_masalar:
                masa_no = masa['masa_no']
                current_durum = masa['durum']
                son_islem_zamani_str = masa['son_islem_zamani']

                needs_update = False
                new_durum = current_durum # Varsayılan olarak mevcut durumu koru

                if son_islem_zamani_str:
                    son_islem_zamani = datetime.strptime(son_islem_zamani_str, "%Y-%m-%d %H:%M:%S")
                    time_difference = now - son_islem_zamani

                    if time_difference > late_threshold and current_durum != 'Geçikmiş':
                        # 30 dakikadan fazla geçmiş ve henüz 'Geçikmiş' değilse durumu güncelle
                        new_durum = 'Geçikmiş'
                        needs_update = True
                        print(f"Masa {masa_no} geçikmiş olarak işaretlendi.") # Debug
                    elif time_difference <= late_threshold and current_durum == 'Geçikmiş':
                         # 30 dakikadan az geçmiş ve 'Geçikmiş' ise durumu 'Dolu'ya geri çek
                         new_durum = 'Dolu'
                         needs_update = True
                         print(f"Masa {masa_no} durumu 'Dolu' olarak güncellendi.") # Debug

                # Eğer durum değiştiyse veritabanını ve buton stilini güncelle
                if needs_update:
                    self.app.db_manager.cursor.execute("UPDATE masalar SET durum = ? WHERE masa_no = ?", (new_durum, masa_no))
                    self.app.db_manager.conn.commit()

                    # İlgili masa butonunu bul ve stilini güncelle
                    for btn in self.masa_buttons:
                        if hasattr(btn, 'masa_no') and btn.masa_no == masa_no:
                            # Seçili masa stilini koru eğer o masa seçiliyse
                            if self.selected_masa_button == btn:
                                 # Seçili stilin üzerine yeni durumu uygulayarak birleşik stil oluşturabiliriz
                                 # Veya şimdilik sadece seçili stilini koruyup durumu güncelleyebiliriz.
                                 # Seçili stilin üzerine 'Geçikmiş' stilini uygulamak daha bilgilendirici olabilir.
                                 # Ancak ttk stilleri katmanlı değildir, son uygulanan stil geçerli olur.
                                 # En basit yol, seçili stilini korumak ve sadece altta yatan durumu güncellemektir.
                                 # load_masa_buttons çağrıldığında doğru stil atanacaktır.
                                 # load_masa_buttons'ı çağırmak tüm butonları yeniden oluşturur, bu da biraz maliyetli olabilir.
                                 # Sadece ilgili butonun stilini güncellemek daha verimlidir.

                                 # Seçili stilini koruyarak sadece masa durumunu güncelle
                                 btn.masa_durum = new_durum # Masa durumu attribute'unu güncelle
                                 # Stil güncellemesi load_masa_buttons içinde yapılıyor,
                                 # veya burada manuel olarak stil adını hesaplayıp atayabiliriz.
                                 # load_masa_buttons'ı çağırmak daha güvenli olabilir.
                                 # self.load_masa_buttons() # Tüm butonları yeniden yüklemek yerine sadece ilgili butonu güncelle.

                                 # Seçili butona özel stil uygulandığı için, sadece altta yatan durumu güncelleyelim.
                                 # load_masa_buttons çağrıldığında doğru stil atanacaktır.
                                 pass # Seçili masa stilini koru
                            else:
                                # Seçili olmayan butonun stilini güncelle
                                style_name = f"{new_durum}.TButton" if new_durum in constants.MASA_STYLES else 'TButton'
                                btn.config(style=style_name)
                                btn.masa_durum = new_durum # Masa durumu attribute'unu güncelle

                            # Buton metnini de güncelle (durum değiştiği için)
                            toplam = self.app.db_manager.cursor.execute("SELECT guncel_toplam FROM masalar WHERE masa_no = ?", (masa_no,)).fetchone()['guncel_toplam']
                            button_text = f"Masa {masa_no}\nDurum: {new_durum}"
                            if new_durum != 'Boş' and toplam is not None and toplam > 0:
                                 button_text += f"\nToplam: {toplam:.2f} TL"
                            btn.config(text=button_text)

                            break # İlgili butonu bulduk, döngüden çık


        except sqlite3.Error as e:
            print(f"Geçikmiş masa kontrol hatası: {e}")
            # messagebox.showerror("Veritabanı Hatası", f"Geçikmiş masalar kontrol edilirken hata oluştu: {e}") # Her dakika hata mesajı göstermeyelim
        except Exception as e:
             print(f"Geçikmiş masa kontrol beklenmedik hata: {e}")
             # messagebox.showerror("Hata", f"Geçikmiş masalar kontrol edilirken beklenmedik hata oluştu: {e}")

        # Kontrol döngüsünü tekrar planla
        if self.frame.winfo_exists():
             self._late_table_check_id = self.frame.after(constants.LATE_TABLE_CHECK_INTERVAL_MS, self._check_late_tables)


    def load_masa_buttons(self):
        """Veritabanından masaları yükler ve butonları oluşturur/günceller."""
        # Mevcut butonları temizle
        for btn in self.masa_buttons:
            btn.destroy()
        self.masa_buttons = [] # Listeyi temizle
        # Butonlar yeniden yüklendiğinde seçili masayı sıfırla
        self.selected_masa_no = None
        self.selected_masa_button = None


        try:
            # Veritabanından masaları çek
            # Masa durumu 'Geçikmiş' olabilir, bu yüzden sorguyu güncelleyelim.
            self.app.db_manager.cursor.execute("SELECT masa_no, durum, guncel_toplam FROM masalar ORDER BY masa_no")
            masalar = self.app.db_manager.cursor.fetchall()

            # Her masa için buton olu tur
            for masa in masalar:
                masa_no = masa['masa_no']
                durum = masa['durum'] # Veritabanından gelen güncel durum
                toplam = masa['guncel_toplam']

                button_text = f"Masa {masa_no}\nDurum: {durum}"
                # toplam None olabilir kontrolü eklendi ve sadece boş olmayan masalar için toplam gösterildi
                if durum != 'Boş' and toplam is not None and toplam > 0:
                     button_text += f"\nToplam: {toplam:.2f} TL"

                # Masa durumuna göre stil belirle (Geçikmiş durumu da dahil)
                style_name = f"{durum}.TButton" if durum in constants.MASA_STYLES else 'TButton'

                # Butonu oluştur
                btn = ttk.Button(self.masa_button_frame,
                                 text=button_text,
                                 # Butona tıklandığında _on_masa_button_click metodunu çağır
                                 command=lambda no=masa_no: self._on_masa_button_click(no),
                                 style=style_name) # Başlangıç stilini ayarla
                # Butonun masa numarasını ve durumunu bir attribute olarak sakla
                btn.masa_no = masa_no
                btn.masa_durum = durum # <<< Masa durumu saklandı
                self.masa_buttons.append(btn) # Butonu listeye ekle

            # Butonları oluşturduktan sonra yeniden düzenleme fonksiyonunu çağır
            # Bu, butonların doğru boyutta ve konumda görünmesini sağlar.
            self.rearrange_masa_buttons()

            # Butonlar yüklendikten sonra geçikmiş masa kontrolünü tetikle
            # Bu, uygulamanın başlangıcında veya Masa sekmesine dönüldüğünde
            # masa durumlarının doğru renklerle gösterilmesini sağlar.
            # _check_late_tables metodu zaten periyodik olarak çalışıyor,
            # ancak load_masa_buttons çağrıldığında hemen bir kontrol yapmak iyi olur.
            # _check_late_tables() # load_masa_buttons içinde çağırmak yerine periyodik döngüye güvenelim.


        except sqlite3.Error as e:
            messagebox.showerror("Veritabanı Hatası", f"Masalar yüklenirken hata oluştu: {e}")
        except Exception as e: # Diğer olası hataları yakala
             messagebox.showerror("Hata", f"Masalar yüklenirken beklenmedik hata oluştu: {e}")

    def _on_masa_button_click(self, masa_no):
        """Bir masa butonuna tıklandığında çağrılır."""
        # Eğer masa silme modu aktifse, silme işlemini tetikle
        if self.app.delete_mode:
            self.app._perform_delete_masa(masa_no) # main.py'deki silme fonksiyonunu çağır
            # Masa silme modu _perform_delete_masa içinde kapatılacak
            # Seçili masa stilini sıfırlama _perform_delete_masa içinde yapılacak
            return # Silme işlemi yapıldı, başka bir şey yapma

        # Eğer masa silme modu aktif değilse, masa seçme mantığını uygula
        # Daha önce bir masa seçildiyse, eski seçili butonun stilini sıfırla
        self._reset_selected_masa_button_style() # <<< Seçili stil sıfırlama metodu çağrıldı

        # Tıklanan masayı seçili olarak ayarla
        self.selected_masa_no = masa_no
        # Tıklanan butonu bul ve seçili buton olarak sakla
        clicked_button = None
        for btn in self.masa_buttons:
            if hasattr(btn, 'masa_no') and btn.masa_no == masa_no:
                clicked_button = btn
                break

        self.selected_masa_button = clicked_button

        # Seçili butona özel bir stil uygula
        if self.selected_masa_button:
             self.selected_masa_button.config(style='Selected.TButton') # Seçili stilini uygula


        # main.py'deki select_masa metodunu çağırarak aktif masayı ayarla ve Adisyon sekmesini güncelle
        self.app.select_masa(masa_no)

    def _reset_selected_masa_button_style(self):
        """Daha önce seçili olan masa butonunun stilini sıfırlar."""
        if self.selected_masa_button:
            # Butonun orijinal stilini bul (masa durumuna göre)
            original_style = 'TButton' # Varsayılan stil
            # Masa durumu attribute'undan veya veritabanından güncel durumu alabiliriz.
            # Attribute daha hızlıdır, ancak veritabanı daha güncel olabilir (geçikmiş durumu gibi).
            # load_masa_buttons içinde butonlar oluşturulurken durum attribute'u güncelleniyor.
            # _check_late_tables içinde de durum veritabanında güncelleniyor.
            # Burada en güncel durumu veritabanından çekmek daha doğru olur.
            masa_no = self.selected_masa_button.masa_no
            current_masa_info = self.app.db_manager.cursor.execute("SELECT durum FROM masalar WHERE masa_no = ?", (masa_no,)).fetchone()
            if current_masa_info and current_masa_info['durum'] in constants.MASA_STYLES:
                 original_style = f"{current_masa_info['durum']}.TButton"
            else:
                 # Eğer veritabanından durum çekilemezse veya stil yoksa, butonun kendi sakladığı durumu kullan
                 if hasattr(self.selected_masa_button, 'masa_durum') and self.selected_masa_button.masa_durum in constants.MASA_STYLES:
                      original_style = f"{self.selected_masa_button.masa_durum}.TButton"


            self.selected_masa_button.config(style=original_style)
            self.selected_masa_button = None # Seçili butonu sıfırla
            self.selected_masa_no = None # Seçili masa numarasını sıfırla

    def _add_masa_command(self):
        """Masa Ekle butonuna basıldığında main.py'deki metodu çağırır."""
        self.app._add_masa() # <<< main.py'deki metot çağrıldı

    def _delete_masa_command(self):
        """Masa Sil butonuna basıldığında main.py'deki metodu çağırır."""
        self.app._delete_masa() # <<< main.py'deki metot çağrıldı

    def update_delete_button_text(self, is_delete_mode):
        """Masa Sil butonunun metnini ve stilini günceller."""
        if hasattr(self, 'btn_masa_sil') and self.btn_masa_sil.winfo_exists():
             if is_delete_mode:
                 self.btn_masa_sil.config(text="Silmek İçin Masa Seçin (İptal)", style='Selected.TButton')
             else:
                 self.btn_masa_sil.config(text="Masa Sil", style='TButton')


    def exit_delete_mode(self):
         """Masa silme modundan çıkar ve MasaTab arayüzünü günceller."""
         # Bu metot main.py'deki _on_tab_change metodundan çağrılacak.
         self.update_delete_button_text(False) # Buton metnini sıfırla
         self._reset_selected_masa_button_style() # Seçili masa stilini sıfırla


    def get_selected_masa_no(self):
        """Seçili masa numarasını döndürür."""
        return self.selected_masa_no


    def rearrange_masa_buttons(self, event=None):
        """Masa butonlarının düzenini yeniden hesaplar ve place ile yerleştirir."""
        # Mevcut masa butonlarının sayısını al
        masa_count = len(self.masa_buttons)
        if masa_count == 0:
            # Eğer masa yoksa, önceki place ile yerleştirilmiş widget'ları temizle
            for widget in self.masa_button_frame.winfo_children():
                 widget.place_forget() # Widget'ı yerleşimden kaldır
            return # Masa yoksa bir şey yapma


        # Butonları içeren çerçevenin güncel boyutlarını al
        self.app.root.update_idletasks()
        width = self.masa_button_frame.winfo_width()
        height = self.masa_button_frame.winfo_height()

        # Boyutlar henüz belirlenmediyse veya çok küçükse çık
        if width <= 1 or height <= 1:
            return

        # Optimal sütun/satır sayısını hesapla (DynamicTableLayout mantığı)
        cols, rows = self.calculate_grid(width, height, masa_count)

        # Eğer hesaplanan sütun sayısı 0 ise veya masa sayısından fazlaysa düzelt
        if cols <= 0:
            cols = 1
        # hesaplanan sütun sayısı toplam masa sayısından fazla olamaz
        if cols > masa_count:
             cols = masa_count

        # Eğer hesaplanan satır sayısı 0 ise düzelt
        if rows <= 0:
            rows = 1
        # Satır sayısını masa sayısına göre yeniden hesapla (cols'a bağlı olarak)
        rows = math.ceil(masa_count / cols)


        # Her bir masa butonunun boyutunu hesapla
        padx = 5
        pady = 5

        cell_width = width / cols
        cell_height = height / rows

        btn_width = cell_width - 2 * padx
        btn_height = cell_height - 2 * pady

        min_btn_size = 40
        btn_width = max(btn_width, min_btn_size)
        btn_height = max(btn_height, min_btn_size)

        if btn_width < 1 or btn_height < 1:
             # Çok küçük boyutlarda yerleşimi atla ve mevcut butonları gizle
             for btn in self.masa_buttons:
                 btn.place_forget()
             return


        # Butonları place ile yerleştir
        for i, btn in enumerate(self.masa_buttons):
            row = i // cols
            col = i % cols

            x_pos = col * cell_width + padx
            y_pos = row * cell_height + pady

            # Butonu place ile yerleştir ve boyutunu ayarla
            btn.place(x=x_pos,
                      y=y_pos,
                      width=btn_width,
                      height=btn_height)

    def calculate_grid(self, width, height, item_count):
        """Ekran boyutuna ve öğe sayısına göre optimal grid'i hesaplar."""
        if height == 0:
            height = 1
        if width == 0:
            width = 1

        ratio = width / height

        best_cols = 1
        min_aspect_diff = float('inf')

        for cols in range(1, item_count + 1):
            rows = math.ceil(item_count / cols)
            if rows == 0:
                continue

            cell_aspect_ratio = (width / cols) / (height / rows)

            aspect_diff = abs(cell_aspect_ratio - 1.0)

            if aspect_diff < min_aspect_diff:
                min_aspect_diff = aspect_diff
                best_cols = cols

        best_rows = math.ceil(item_count / best_cols)

        return best_cols, best_rows