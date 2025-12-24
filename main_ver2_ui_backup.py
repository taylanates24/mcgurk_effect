"""
McGurk Etkisi Testi - PsychoPy Uygulaması
Bu uygulama katılımcılara video göstererek ses algılarını test eder.
"""

import gc
from psychopy import prefs

# --- AYAR 1: Ses Gecikme Modu (Critical) ---
# Sesi videoyla senkron tutmak için en agresif modu açıyoruz.
prefs.hardware['audioLatencyMode'] = 4 

# Ses kütüphanesi önceliği (PTB en düşük gecikme için ilk sırada)
prefs.hardware['audioLib'] = ['ptb', 'sounddevice', 'pygame']

from psychopy import visual, core, event, logging
import csv
import os
import random
import warnings
from datetime import datetime
from pathlib import Path
import customtkinter as ctk
from PIL import Image

# PsychoPy logging seviyesini ayarla (uyarıları azalt)
logging.console.setLevel(logging.ERROR)

# Veri klasörünü oluştur
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Thumbnail klasörü
thumb_dir = Path('assets/thumbnails')
thumb_dir.mkdir(parents=True, exist_ok=True)

def ensure_thumbnails():
    """
    Her speaker için bir thumbnail oluşturur (varsa atlar).
    """
    try:
        # moviepy v2.x uyumluluğu
        try:
            from moviepy import VideoFileClip
        except ImportError:
            try:
                from moviepy.editor import VideoFileClip
            except ImportError:
                raise ImportError("moviepy module not found")
        
        for i in range(1, 9):
            thumb_path = thumb_dir / f"speaker_{i}.jpg"
            if thumb_path.exists():
                continue
            
            # Her speaker için örnek bir video bul (ba-ba kombinasyonu)
            video_path = Path(f"assets/Vis-ba_Aud-ba_Speaker-{i}.mp4")
            if not video_path.exists():
                print(f"Uyarı: Speaker {i} için video bulunamadı: {video_path}")
                continue
                
            try:
                clip = VideoFileClip(str(video_path))
                # 0.5. saniyeden kare al (yüzün net olduğu bir an)
                clip.save_frame(str(thumb_path), t=0.5)
                clip.close()
                print(f"Thumbnail oluşturuldu: {thumb_path}")
            except Exception as e:
                print(f"Thumbnail hatası (Speaker {i}): {e}")
                
    except ImportError:
        print("UYARI: moviepy yüklü değil, thumbnail oluşturulamadı.")
    except Exception as e:
        print(f"Thumbnail genel hata: {e}")

# ---------------------------------------------------------
# 1. CustomTkinter Giriş Ekranı (Launcher)
# ---------------------------------------------------------
def show_launcher():
    """
    Modern, koyu temalı giriş ekranını gösterir ve katılımcı bilgilerini döndürür.
    """
    # Thumbnails hazırla
    ensure_thumbnails()
    
    ctk.set_appearance_mode("Dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("McGurk Testi")
    root.geometry("400x750") # Biraz daha yükselttik
    
    # Pencereyi ekranın ortasına al
    root.eval('tk::PlaceWindow . center')

    # Başlık
    title_label = ctk.CTkLabel(root, text="McGurk Deneyi", font=("Roboto", 24, "bold"))
    title_label.pack(pady=20)

    # Form Alanları Container
    # Scrollable frame kullanarak ekran taşmasını önleyelim
    main_frame = ctk.CTkScrollableFrame(root, fg_color="transparent")
    main_frame.pack(pady=10, padx=20, fill="both", expand=True)

    # Katılımcı ID
    ctk.CTkLabel(main_frame, text="Katılımcı ID:", font=("Roboto", 14)).pack(pady=(10, 5))
    entry_id = ctk.CTkEntry(main_frame, placeholder_text="Örn: P01")
    entry_id.pack(pady=5, padx=20, fill="x")

    # Yaş
    ctk.CTkLabel(main_frame, text="Yaş:", font=("Roboto", 14)).pack(pady=(10, 5))
    entry_age = ctk.CTkEntry(main_frame, placeholder_text="Örn: 25")
    entry_age.pack(pady=5, padx=20, fill="x")

    # Cinsiyet
    ctk.CTkLabel(main_frame, text="Cinsiyet:", font=("Roboto", 14)).pack(pady=(10, 5))
    gender_var = ctk.StringVar(value="Belirtmek İstemiyorum")
    gender_menu = ctk.CTkOptionMenu(main_frame, variable=gender_var, values=["Kadın", "Erkek", "Diğer", "Belirtmek İstemiyorum"])
    gender_menu.pack(pady=5, padx=20, fill="x")

    # --- Speaker Seçimi (Grid) ---
    ctk.CTkLabel(main_frame, text="Speaker Seçiniz:", font=("Roboto", 14, "bold")).pack(pady=(20, 10))
    
    speaker_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
    speaker_grid.pack(pady=5, padx=5)
    
    selected_speaker_var = ctk.StringVar(value="1")
    speaker_buttons = []
    
    def on_speaker_select(sid):
        selected_speaker_var.set(str(sid))
        update_speaker_buttons()
        
    def update_speaker_buttons():
        current = selected_speaker_var.get()
        for btn, sid in speaker_buttons:
            if str(sid) == current:
                btn.configure(fg_color="green", border_color="white", border_width=2)
            else:
                btn.configure(fg_color="gray20", border_color="gray", border_width=0)

    # 1'den 8'e kadar speakerlar
    for i in range(1, 9):
        img_path = thumb_dir / f"speaker_{i}.jpg"
        
        # Resim yükle (varsa)
        if img_path.exists():
            try:
                pil_img = Image.open(img_path)
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(60, 60))
                btn_text = ""
            except:
                ctk_img = None
                btn_text = f"Spk {i}"
        else:
            ctk_img = None
            btn_text = f"Spk {i}"
            
        row = (i-1) // 4
        col = (i-1) % 4
        
        btn = ctk.CTkButton(
            speaker_grid,
            text=btn_text,
            image=ctk_img,
            width=70,
            height=70,
            fg_color="gray20",
            hover_color="gray40",
            command=lambda sid=i: on_speaker_select(sid)
        )
        btn.grid(row=row, column=col, padx=5, pady=5)
        speaker_buttons.append((btn, i))
        
    update_speaker_buttons() # İlk durumu ayarla

    info = {}

    def on_start():
        info['participant'] = entry_id.get().strip()
        if not info['participant']:
            info['participant'] = f"Katilimci_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        info['age'] = entry_age.get().strip()
        info['gender'] = gender_var.get()
        info['speaker'] = selected_speaker_var.get()
        
        root.destroy()

    # Başla Butonu (Ana pencereye ekliyoruz, scroll içinde olmasın ki hep görünsün)
    start_button = ctk.CTkButton(root, text="DENEYE BAŞLA", command=on_start, height=50, font=("Roboto", 16, "bold"), fg_color="green", hover_color="darkgreen")
    start_button.pack(pady=20, padx=40, fill="x", side="bottom")

    root.mainloop()
    return info

# Launcher'ı çalıştır ve bilgileri al
participant_info = show_launcher()

participant_name = participant_info['participant']
participant_age = participant_info['age']
participant_gender = participant_info['gender']
speaker_id = participant_info['speaker']

print(f"\nKatılımcı: {participant_name} (Yaş: {participant_age}, Cinsiyet: {participant_gender})")
print(f"Speaker ID: {speaker_id}")
print("Test başlıyor...\n")

# ---------------------------------------------------------
# 2. ModernButton Sınıfı
# ---------------------------------------------------------
class ModernButton:
    def __init__(self, win, label, pos, size):
        self.win = win
        self.label = label
        self.pos = pos
        self.size = size
        
        # Renkler
        self.default_color = 'gray'
        self.hover_color = '#505050'  # Biraz daha koyu/açık gri
        self.click_color = 'green'
        
        # Dikdörtgen Şekli
        self.rect = visual.Rect(
            win,
            width=size[0],
            height=size[1],
            pos=pos,
            fillColor=self.default_color,
            lineColor='white',
            lineWidth=2,
            opacity=1.0
        )
        
        # Yazı
        self.text = visual.TextStim(
            win,
            text=label,
            pos=pos,
            color='white',
            height=int(size[1] * 0.4),
            font='Arial',
            alignText='center'
        )

    def draw(self):
        self.rect.draw()
        self.text.draw()

    def contains(self, mouse):
        return self.rect.contains(mouse)

    def update_hover(self, mouse):
        """Mouse buton üzerindeyse rengi değiştirir."""
        if self.contains(mouse):
            self.rect.fillColor = self.hover_color
        else:
            self.rect.fillColor = self.default_color

    def set_clicked(self):
        self.rect.fillColor = self.click_color

    def reset(self):
        self.rect.fillColor = self.default_color

# ---------------------------------------------------------
# PsychoPy Başlangıç
# ---------------------------------------------------------

# Ekran boyutunu al
screen_size = None
try:
    from psychopy import monitors
    monitor = monitors.Monitor('default')
    screen_size = monitor.getSizePix()
    if screen_size is None or len(screen_size) < 2:
        screen_size = [1920, 1080]
except:
    screen_size = [1920, 1080]

if screen_size and len(screen_size) >= 2:
    window_size = [int(screen_size[0] * 0.8), int(screen_size[1] * 0.8)]
else:
    window_size = [1536, 864]

win = visual.Window(
    size=window_size,
    fullscr=False,
    screen=0,
    winType='pyglet',
    allowGUI=True,
    color='black',
    colorSpace='rgb',
    units='pix'
)

# Koşulları oluştur
conditions = []
syllables = ['ba', 'da', 'ga']

for vis in syllables:
    for aud in syllables:
        video_file = f"Vis-{vis}_Aud-{aud}_Speaker-{speaker_id}.mp4"
        expected_sound = aud.upper()
        
        conditions.append({
            'video_file': video_file,
            'expected_sound': expected_sound
        })

random.shuffle(conditions)
print(f"Toplam {len(conditions)} koşul oluşturuldu.")

# Veri kayıt dosyası
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
data_file = data_dir / f"{participant_name}_{timestamp}.csv"

with open(data_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Katilimci', 'Yas', 'Cinsiyet', 'VideoAdi', 'BeklenenCevap', 'Cevap', 'DogruMu', 'TepkiSuresi_ms'])

# Görsel öğeler
win_size = win.size
fixation_cross = visual.TextStim(win, text='+', color='white', height=int(win_size[1] * 0.15))
message_text = visual.TextStim(win, text='', color='white', height=int(win_size[1] * 0.05))

# Butonları Oluştur (ModernButton sınıfı ile)
button_labels = ['BA', 'DA', 'GA']
buttons = []
button_width = int(win_size[0] * 0.12)
button_height = int(win_size[1] * 0.12)
button_spacing = int(win_size[0] * 0.02)
start_x = -(len(button_labels) * (button_width + button_spacing)) / 2 + button_width / 2
button_y_pos = -int(win_size[1] * 0.25)

for i, label in enumerate(button_labels):
    x_pos = start_x + i * (button_width + button_spacing)
    btn = ModernButton(
        win=win,
        label=label,
        pos=[x_pos, button_y_pos],
        size=[button_width, button_height]
    )
    buttons.append(btn)

mouse = event.Mouse(win=win)
trial_clock = core.Clock()

for condition_idx, condition in enumerate(conditions):
    keys = event.getKeys()
    if 'escape' in keys:
        print("Kullanıcı Escape tuşuna bastı. Çıkılıyor...")
        break
    
    video_path = Path('assets') / condition['video_file']
    
    if not video_path.exists():
        print(f"UYARI: Video dosyası bulunamadı: {video_path}")
        continue
    
    # 1. Fixation
    fixation_cross.draw()
    win.flip()
    core.wait(0.5)
    
    # 2. Video Oynatma
    movie = None
    try:
        # --- AYAR 2: MovieStim3 Önceliği ---
        # MovieStim3, FFpyplayer kullanarak sesi çok daha iyi senkronize eder.
        movie_class = None
        
        if hasattr(visual, 'MovieStim3'):
            movie_class = visual.MovieStim3
        elif hasattr(visual, 'MovieStim2'):
            movie_class = visual.MovieStim2
        elif hasattr(visual, 'MovieStim'):
            movie_class = visual.MovieStim
        else:
            raise Exception("Video oynatma desteği bulunamadı.")
        
        win_size = win.size
        video_pos = [0, int(win_size[1] * 0.15)]
        
        # Movie nesnesini oluştur
        try:
            movie = movie_class(
                win,
                str(video_path),
                pos=video_pos,
                flipVert=False,
                flipHoriz=False,
                loop=False,
                noAudio=False  # Sesin açık olduğundan emin ol
            )
        except TypeError:
            # Parametre uyumsuzluğu olursa size parametresi ile dene
            movie = movie_class(
                win,
                str(video_path),
                pos=video_pos,
                size=win_size, # Gerekirse boyutu zorla
                flipVert=False,
                flipHoriz=False,
                loop=False
            )
            
        if movie is None:
            raise Exception("Video oluşturulamadı.")
        
        # --- AYAR 3: Wait Kaldırma ---
        # Video çizilip flip edildiği an ses başlar. Araya wait koymak senkronu bozar.
        # Sadece ilk kareyi bufferlamak için draw yapıyoruz ama bekletmiyoruz.
        movie.draw()
        win.flip()
        
        clock = core.Clock()
        video_duration = 2.0 
        
        while clock.getTime() < video_duration:
            keys = event.getKeys()
            if 'escape' in keys:
                print("Çıkılıyor...")
                break
            
            try:
                movie.draw()
                win.flip()
            except Exception:
                win.flip()
        
        print(f"Video bitti: {video_path.name}")
        
    except Exception as e:
        import traceback
        print(f"HATA: Video oynatma hatası: {e}")
        if movie is not None:
            try:
                if hasattr(movie, 'stop'): movie.stop()
                del movie
                gc.collect()
            except: pass
        continue
    
    # 3. Cevap Ekranı
    for btn in buttons:
        btn.reset()
    
    win_size = win.size
    response_text = visual.TextStim(
        win,
        text='Hangi sesi duydunuz?',
        pos=[0, -int(win_size[1] * 0.08)],
        color='white',
        height=int(win_size[1] * 0.05)
    )
    
    trial_clock.reset()
    response_received = False
    response = None
    reaction_time = None
    mouse_was_pressed = False
    
    # Mouse state'i temizle
    mouse.clickReset()
    
    while not response_received:
        keys = event.getKeys()
        if 'escape' in keys:
            response_received = True
            break
        
        try:
            if movie is not None:
                movie.draw()
        except: pass
        
        response_text.draw()
        
        # ModernButton Hover ve Draw mantığı
        for btn in buttons:
            btn.update_hover(mouse)
            btn.draw()
        
        win.flip()
        
        # Mouse tıklama kontrolü
        mouse_clicked = mouse.getPressed()[0]
        
        if mouse_clicked and not mouse_was_pressed:
            for btn in buttons:
                if btn.contains(mouse):
                    response = btn.label
                    reaction_time = trial_clock.getTime() * 1000
                    response_received = True
                    
                    btn.set_clicked()
                    
                    # Son bir kez çiz ki tıklama efekti görünsün
                    response_text.draw()
                    for b in buttons: b.draw()
                    win.flip()
                    core.wait(0.3)
                    break
        
        mouse_was_pressed = mouse_clicked
    
    if response:
        with open(data_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                participant_name,
                participant_age,
                participant_gender,
                condition['video_file'],
                condition['expected_sound'],
                response,
                1 if response == condition['expected_sound'] else 0,
                f"{reaction_time:.2f}" if reaction_time else ""
            ])
    
    if movie is not None:
        try:
            if hasattr(movie, 'stop'): movie.stop()
            del movie
            movie = None
            gc.collect()
        except Exception: pass

    if condition_idx < len(conditions) - 1:
        message_text.text = 'Bir sonraki denemeye hazır olun...'
        message_text.draw()
        win.flip()
        core.wait(1.0)

finish_text = visual.TextStim(win, text='Test tamamlandı. Teşekkürler!', color='white', height=50)
finish_text.draw()
win.flip()
core.wait(2.0)
win.close()
core.quit()