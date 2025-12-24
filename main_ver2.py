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

# PsychoPy logging seviyesini ayarla (uyarıları azalt)
logging.console.setLevel(logging.ERROR)

# Veri klasörünü oluştur
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Katılımcı bilgilerini al
print("=" * 50)
print("McGurk Etkisi Testi")
print("=" * 50)
participant_name = input("Katılımcı Adı: ").strip()

if not participant_name:
    participant_name = f"Katilimci_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Varsayılan isim kullanılıyor: {participant_name}")

speaker_id = input("Speaker ID (1-8): ").strip()
if not speaker_id:
    speaker_id = "1"
    print(f"Varsayılan Speaker ID kullanılıyor: {speaker_id}")

print(f"\nKatılımcı: {participant_name}")
print(f"Speaker ID: {speaker_id}")
print("Test başlıyor...\n")

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
    writer.writerow(['Katilimci', 'VideoAdi', 'BeklenenCevap', 'Cevap', 'DogruMu', 'TepkiSuresi_ms'])

# Görsel öğeler
win_size = win.size
fixation_cross = visual.TextStim(win, text='+', color='white', height=int(win_size[1] * 0.15))
message_text = visual.TextStim(win, text='', color='white', height=int(win_size[1] * 0.05))

# Butonlar
button_labels = ['BA', 'DA', 'GA']
buttons = []
button_width = int(win_size[0] * 0.12)
button_height = int(win_size[1] * 0.12)
button_spacing = int(win_size[0] * 0.02)
start_x = -(len(button_labels) * (button_width + button_spacing)) / 2 + button_width / 2
button_y_pos = -int(win_size[1] * 0.25)

for i, label in enumerate(button_labels):
    x_pos = start_x + i * (button_width + button_spacing)
    button_rect = visual.Rect(
        win,
        width=button_width,
        height=button_height,
        pos=[x_pos, button_y_pos],
        fillColor='gray',
        lineColor='white',
        lineWidth=2
    )
    button_text = visual.TextStim(
        win,
        text=label,
        pos=[x_pos, button_y_pos],
        color='white',
        height=int(win_size[1] * 0.04),
        font='Arial'
    )
    buttons.append({
        'rect': button_rect,
        'text': button_text,
        'pos': [x_pos, button_y_pos],
        'size': [button_width, button_height],
        'label': label
    })

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
    for button in buttons:
        button['rect'].fillColor = 'gray'
    
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
        for button in buttons:
            button['rect'].draw()
            button['text'].draw()
        
        win.flip()
        
        mouse_clicked = mouse.getPressed()[0]
        
        if mouse_clicked and not mouse_was_pressed:
            mouse_pos = mouse.getPos()
            for button in buttons:
                b_pos = button['pos']
                b_size = button['size']
                if (b_pos[0] - b_size[0]/2 <= mouse_pos[0] <= b_pos[0] + b_size[0]/2 and
                    b_pos[1] - b_size[1]/2 <= mouse_pos[1] <= b_pos[1] + b_size[1]/2):
                    
                    response = button['label']
                    reaction_time = trial_clock.getTime() * 1000
                    response_received = True
                    
                    button['rect'].fillColor = 'green'
                    response_text.draw()
                    button['rect'].draw()
                    button['text'].draw()
                    win.flip()
                    core.wait(0.3)
                    break
        mouse_was_pressed = mouse_clicked
    
    if response:
        with open(data_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                participant_name,
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