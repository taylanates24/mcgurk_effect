"""
McGurk Etkisi Testi - Hibrit Uygulama (CustomTkinter + PsychoPy)
Optimize Edilmiş Sürüm: Ses Senkronizasyonu ve Modern UI
"""

import os
import sys
import csv
import random
import gc
from pathlib import Path
from datetime import datetime

# --- 1. AYARLAR: PsychoPy Yüklenmeden Önce Yapılmalı ---
from psychopy import prefs

# Linux/Windows Ses Gecikme Ayarı (0-4 arası). 
# 3: Düşük gecikme (agresif olmayan mod), Linux için genelde en kararlısıdır.
prefs.hardware['audioLatencyMode'] = 3

# Ses kütüphanesi önceliği (Psychtoolbox -> SoundDevice -> Pygame)
prefs.hardware['audioLib'] = ['ptb', 'sounddevice', 'pygame']

# Şimdi diğer modülleri çağırabiliriz
from psychopy import visual, core, event, logging
import customtkinter as ctk
from PIL import Image

# Log seviyesini ayarla
logging.console.setLevel(logging.ERROR)

# Klasör yolları
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / 'data'
ASSETS_DIR = BASE_DIR / 'assets'
THUMB_DIR = ASSETS_DIR / 'thumbnails'

# Klasörleri oluştur
DATA_DIR.mkdir(exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# YARDIMCI: Thumbnail Kontrolü
# ---------------------------------------------------------
def ensure_thumbnails():
    """Video dosyalarından thumbnail oluşturur (Opsiyonel görsel şölen için)."""
    try:
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            return # Moviepy yoksa sessizce geç
        
        for i in range(1, 9):
            thumb_path = THUMB_DIR / f"speaker_{i}.jpg"
            if thumb_path.exists(): continue
            
            # Her speaker için örnek bir video (ba-ba) var mı bak
            video_sample = ASSETS_DIR / f"Vis-ba_Aud-ba_Speaker-{i}.mp4"
            if video_sample.exists():
                try:
                    clip = VideoFileClip(str(video_sample))
                    clip.save_frame(str(thumb_path), t=0.5) # 0.5. saniyeden kare al
                    clip.close()
                except: pass
    except: pass


# ---------------------------------------------------------
# BÖLÜM 1: LAUNCHER (Giriş Ekranı - CustomTkinter)
# ---------------------------------------------------------
def show_launcher():
    ensure_thumbnails()
    
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("McGurk Deney Kurulumu")
    root.geometry("450x700")
    
    # Pencereyi ortala
    root.eval('tk::PlaceWindow . center')

    # Başlık
    ctk.CTkLabel(root, text="McGurk Deneyi", font=("Roboto", 24, "bold")).pack(pady=20)

    # Scrollable Frame (Taşmaları önlemek için)
    main_frame = ctk.CTkScrollableFrame(root, fg_color="transparent")
    main_frame.pack(pady=10, padx=20, fill="both", expand=True)

    # Girdiler
    ctk.CTkLabel(main_frame, text="Katılımcı ID / Ad:", font=("Roboto", 14)).pack(pady=(10, 5), anchor="w")
    entry_id = ctk.CTkEntry(main_frame, placeholder_text="Örn: Taylan")
    entry_id.pack(pady=5, fill="x")

    ctk.CTkLabel(main_frame, text="Yaş:", font=("Roboto", 14)).pack(pady=(10, 5), anchor="w")
    entry_age = ctk.CTkEntry(main_frame, placeholder_text="Örn: 28")
    entry_age.pack(pady=5, fill="x")

    ctk.CTkLabel(main_frame, text="Cinsiyet:", font=("Roboto", 14)).pack(pady=(10, 5), anchor="w")
    gender_var = ctk.StringVar(value="Belirtmek İstemiyorum")
    ctk.CTkOptionMenu(main_frame, variable=gender_var, 
                      values=["Kadın", "Erkek", "Diğer", "Belirtmek İstemiyorum"]).pack(pady=5, fill="x")

    # Speaker Seçimi
    ctk.CTkLabel(main_frame, text="Konuşmacı (Speaker) Seçimi:", font=("Roboto", 14, "bold")).pack(pady=(25, 10), anchor="w")
    
    speaker_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    speaker_frame.pack(fill="x")

    selected_speaker = ctk.StringVar(value="1")
    buttons = []

    def select_speaker(sid):
        selected_speaker.set(str(sid))
        for btn, bid in buttons:
            if str(bid) == str(sid):
                btn.configure(fg_color="#2CC985", border_color="white", border_width=2) # Seçili (Yeşil)
            else:
                btn.configure(fg_color="#333333", border_color="gray", border_width=0)

    # 8 Speaker için Grid
    for i in range(1, 9):
        path = THUMB_DIR / f"speaker_{i}.jpg"
        img = None
        text = f"Spk {i}"
        
        if path.exists():
            try:
                pil_img = Image.open(path)
                img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(50, 50))
                text = ""
            except: pass

        row, col = (i-1)//4, (i-1)%4
        btn = ctk.CTkButton(speaker_frame, text=text, image=img, width=60, height=60, 
                            fg_color="#333333", command=lambda x=i: select_speaker(x))
        btn.grid(row=row, column=col, padx=5, pady=5)
        buttons.append((btn, i))
    
    select_speaker(1) # Varsayılan seçimi yap

    participant_data = {}

    def start_exp():
        if not entry_id.get():
            entry_id.configure(placeholder_text="LÜTFEN ID GİRİNİZ!", placeholder_text_color="red")
            return
        
        participant_data['id'] = entry_id.get()
        participant_data['age'] = entry_age.get()
        participant_data['gender'] = gender_var.get()
        participant_data['speaker'] = selected_speaker.get()
        root.destroy()

    ctk.CTkButton(root, text="DENEYİ BAŞLAT", command=start_exp, height=50, 
                  fg_color="#1f538d", hover_color="#14375e", font=("Roboto", 16, "bold")).pack(pady=20, padx=20, fill="x", side="bottom")

    root.mainloop()
    return participant_data


# ---------------------------------------------------------
# BÖLÜM 2: UI SINIFI (ModernButton - PsychoPy için)
# ---------------------------------------------------------
class ModernButton:
    """PsychoPy içinde hover özellikli modern buton."""
    def __init__(self, win, text, pos, size):
        self.rect = visual.Rect(win, width=size[0], height=size[1], pos=pos, 
                                fillColor='#333333', lineColor='white', lineWidth=2)
        self.label = visual.TextStim(win, text=text, pos=pos, height=int(size[1]*0.4), color='white')
        self.text_str = text
        self.default_color = '#333333'
        self.hover_color = '#555555'
        self.click_color = '#2CC985' # Yeşil

    def draw(self):
        self.rect.draw()
        self.label.draw()

    def check_hover(self, mouse):
        if self.rect.contains(mouse):
            self.rect.fillColor = self.hover_color
            return True
        else:
            self.rect.fillColor = self.default_color
            return False

    def set_clicked(self):
        self.rect.fillColor = self.click_color


# ---------------------------------------------------------
# BÖLÜM 3: ANA DENEY MANTIĞI
# ---------------------------------------------------------
def run_experiment():
    # 1. Launcher'ı Başlat
    p_info = show_launcher()
    if not p_info: return # Pencere kapatıldıysa çık

    print(f"Deney Başlıyor: {p_info}")

    # 2. PsychoPy Penceresi
    # Tam ekran yerine büyük pencere (geliştirme aşamasında daha güvenli)
    win = visual.Window(size=[1280, 720], fullscr=False, color='black', units='pix', allowGUI=True)
    win.mouseVisible = False

    # 3. Koşulları Hazırla
    syllables = ['ba', 'da', 'ga']
    conditions = []
    speaker = p_info['speaker']
    
    for vis in syllables:
        for aud in syllables:
            filename = f"Vis-{vis}_Aud-{aud}_Speaker-{speaker}.mp4"
            conditions.append({
                'video': filename,
                'expected': aud.upper()
            })
    random.shuffle(conditions)

    # 4. UI Elemanları
    fixation = visual.TextStim(win, text='+', height=50, color='white')
    msg_wait = visual.TextStim(win, text='Sonraki deneme...', height=30, color='gray')
    msg_q = visual.TextStim(win, text='Ne duydunuz?', pos=(0, 150), height=40, color='white')

    # Butonları oluştur
    labels = ['BA', 'DA', 'GA'] # Seçenekleri buraya ekleyebilirsin
    buttons = []
    spacing = 150
    start_x = -((len(labels)-1) * spacing) / 2
    
    for i, txt in enumerate(labels):
        buttons.append(ModernButton(win, txt, pos=(start_x + i*spacing, -100), size=(120, 80)))

    # Veri Kaydı
    filename = f"{p_info['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    csv_path = DATA_DIR / filename
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['ID', 'Age', 'Gender', 'Video', 'Expected', 'Response', 'RT_ms'])

    mouse = event.Mouse(win=win)
    clock = core.Clock()

    # --- DENEY DÖNGÜSÜ ---
    for trial in conditions:
        video_path = ASSETS_DIR / trial['video']
        
        # Dosya kontrolü
        if not video_path.exists():
            print(f"HATA: Video yok - {video_path}")
            continue

        # A. Fiksasyon
        fixation.draw()
        win.flip()
        core.wait(0.5)

        # B. Video Oynatma (GÜNCELLENMİŞ)
        try:
            # Video dosyasının tam yolunun string olduğundan emin olalım
            video_file_str = str(video_path)
            
            # MovieStim oluştururken 'backend' parametresini açıkça belirtiyoruz.
            # Öncelik: 'ffpyplayer' (Hızlı/Senkron), çalışmazsa 'moviepy' (Yavaş ama güvenli)
            movie = visual.MovieStim(
                win, 
                filename=video_file_str, 
                noAudio=False, 
                loop=False,
                pos=(0, 100)
            )
            
            # --- ÖNEMLİ: Videonun yüklendiğinden emin ol ---
            # Eğer video bozuk yüklendiyse duration None dönebilir, bu da hataya sebep olur.
            if movie.duration is None:
                print(f"UYARI: Video süresi okunamadı, 'moviepy' backend deneniyor...")
                # Backend değiştirip tekrar dene
                del movie
                movie = visual.MovieStim(win, filename=video_file_str, backend='moviepy', pos=(0, 100))

            movie.play()
            
            while movie.status != visual.FINISHED:
                if 'escape' in event.getKeys():
                    if hasattr(movie, 'stop'): movie.stop()
                    win.close()
                    core.quit()
                    return
                movie.draw()
                win.flip()
            
            if hasattr(movie, 'stop'): movie.stop()
            del movie
            win.flip() 

        except Exception as e:
            print(f"Video Hatası ({video_path.name}): {e}")
            continue

        # C. Cevap Ekranı
        win.mouseVisible = True
        mouse.setPos((0, 0))
        mouse.clickReset()
        clock.reset()
        
        responded = False
        response_data = None
        
        while not responded:
            if 'escape' in event.getKeys():
                win.close(); core.quit(); return

            # Butonları çiz ve hover kontrolü yap
            msg_q.draw()
            for btn in buttons:
                btn.check_hover(mouse)
                btn.draw()
            
            win.flip()

            # Tıklama kontrolü
            if mouse.getPressed()[0]: # Sol tık
                for btn in buttons:
                    if btn.rect.contains(mouse):
                        rt = clock.getTime() * 1000
                        response_data = {
                            'resp': btn.text_str,
                            'rt': rt
                        }
                        btn.set_clicked() # Tıklandığını göster
                        msg_q.draw()
                        for b in buttons: b.draw()
                        win.flip()
                        core.wait(0.2) # Görsel geribildirim için bekle
                        responded = True
                        break

        # D. Kayıt
        with open(csv_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                p_info['id'], p_info['age'], p_info['gender'],
                trial['video'], trial['expected'],
                response_data['resp'], f"{response_data['rt']:.2f}"
            ])
        
        # Deneme arası bekleme
        win.mouseVisible = False
        msg_wait.draw()
        win.flip()
        core.wait(0.5)

    # Bitiş
    visual.TextStim(win, text="Deney Tamamlandı.\nTeşekkürler!", height=40).draw()
    win.flip()
    core.wait(2.0)
    win.close()
    core.quit()

if __name__ == "__main__":
    run_experiment()