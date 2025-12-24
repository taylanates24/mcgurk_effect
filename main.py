"""
McGurk Etkisi Testi - PsychoPy Uygulaması
Bu uygulama katılımcılara video göstererek ses algılarını test eder.
"""

import gc
from psychopy import prefs
# Ses kütüphanesi önceliğini ayarla (PTB daha kararlıdır)
prefs.hardware['audioLib'] = ['ptb', 'sounddevice', 'pygame']
from psychopy import visual, core, event, logging
import csv
import os
import warnings
from datetime import datetime
from pathlib import Path

# PsychoPy logging seviyesini ayarla (uyarıları azalt)
logging.console.setLevel(logging.ERROR)  # Sadece hataları göster


# Veri klasörünü oluştur
data_dir = Path('data')
data_dir.mkdir(exist_ok=True)

# Katılımcı bilgilerini al (terminal input - Qt bağımlılığı yok)
print("=" * 50)
print("McGurk Etkisi Testi")
print("=" * 50)
participant_name = input("Katılımcı Adı: ").strip()

# Eğer boşsa varsayılan isim kullan
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

# PsychoPy pencere oluştur (dinamik ve resize edilebilir)
# Ekran boyutunu al (veya varsayılan kullan)
screen_size = None
try:
    from psychopy import monitors
    monitor = monitors.Monitor('default')
    screen_size = monitor.getSizePix()
    # Eğer None döndüyse varsayılan kullan
    if screen_size is None or len(screen_size) < 2:
        screen_size = [1920, 1080]
except:
    # Varsayılan boyut
    screen_size = [1920, 1080]

# Pencere boyutunu ekran boyutunun %80'i yap (veya istediğiniz boyutu ayarlayın)
if screen_size and len(screen_size) >= 2:
    window_size = [int(screen_size[0] * 0.8), int(screen_size[1] * 0.8)]
else:
    window_size = [1536, 864]  # Varsayılan: 1920x1080'nin %80'i

win = visual.Window(
    size=window_size,
    fullscr=False,  # Tam ekran modu (True yapılabilir)
    screen=0,
    winType='pyglet',
    allowGUI=True,  # allowGUI=True ile pencere resize edilebilir olur
    color='black',
    colorSpace='rgb',
    units='pix'
)

# Koşulları oluştur (Speaker ID'ye göre)
conditions = []
syllables = ['ba', 'da', 'ga']

# Tüm kombinasyonları oluştur (Visual x Audio)
# Pairler: Vis-ba_Aud-ba, Vis-ba_Aud-da, ..., Vis-ga_Aud-ga
for vis in syllables:
    for aud in syllables:
        video_file = f"Vis-{vis}_Aud-{aud}_Speaker-{speaker_id}.mp4"
        # Etiket audio neyse o olacak (büyük harfle)
        expected_sound = aud.upper()
        
        conditions.append({
            'video_file': video_file,
            'expected_sound': expected_sound
        })

print(f"Toplam {len(conditions)} koşul oluşturuldu.")

# Veri kayıt dosyası oluştur
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
data_file = data_dir / f"{participant_name}_{timestamp}.csv"

# CSV başlıklarını yaz
with open(data_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Katilimci', 'VideoAdi', 'BeklenenCevap', 'Cevap', 'DogruMu', 'TepkiSuresi_ms'])

# Görsel öğeleri oluştur (ekran boyutuna göre dinamik)
win_size = win.size
fixation_cross = visual.TextStim(win, text='+', color='white', height=int(win_size[1] * 0.15))
message_text = visual.TextStim(win, text='', color='white', height=int(win_size[1] * 0.05))

# Cevap butonları oluştur (Rect + TextStim kombinasyonu)
# Ekran boyutuna göre dinamik boyutlandırma
win_size = win.size
button_labels = ['BA', 'DA', 'GA']
buttons = []  # Her buton için (rect, text) tuple'ları saklayacağız

# Butonları ekran boyutuna göre dinamik olarak yerleştir
button_width = int(win_size[0] * 0.12)  # Ekran genişliğinin %12'si
button_height = int(win_size[1] * 0.12)  # Ekran yüksekliğinin %12'si
button_spacing = int(win_size[0] * 0.02)  # Ekran genişliğinin %2'si
start_x = -(len(button_labels) * (button_width + button_spacing)) / 2 + button_width / 2
button_y_pos = -int(win_size[1] * 0.25)  # Ekranın alt %25'inde

for i, label in enumerate(button_labels):
    x_pos = start_x + i * (button_width + button_spacing)
    # Buton arka planı (Rect)
    button_rect = visual.Rect(
        win,
        width=button_width,
        height=button_height,
        pos=[x_pos, button_y_pos],
        fillColor='gray',
        lineColor='white',
        lineWidth=2
    )
    # Buton metni (TextStim)
    button_text = visual.TextStim(
        win,
        text=label,
        pos=[x_pos, button_y_pos],
        color='white',
        height=int(win_size[1] * 0.04),  # Ekran yüksekliğine göre
        font='Arial'
    )
    buttons.append({
        'rect': button_rect,
        'text': button_text,
        'pos': [x_pos, button_y_pos],
        'size': [button_width, button_height],
        'label': label
    })

# Mouse kontrolü için
mouse = event.Mouse(win=win)

# Deneme döngüsü
trial_clock = core.Clock()

for condition_idx, condition in enumerate(conditions):
    # Escape tuşu kontrolü
    keys = event.getKeys()
    if 'escape' in keys:
        print("Kullanıcı Escape tuşuna bastı. Çıkılıyor...")
        break
    
    video_path = Path('assets') / condition['video_file']
    
    # Video dosyasının varlığını kontrol et
    if not video_path.exists():
        print(f"UYARI: Video dosyası bulunamadı: {video_path}")
        continue
    
    # 1. Fixation cross göster (500ms)
    fixation_cross.draw()
    win.flip()
    core.wait(0.5)
    
    # 2. Video oynat
    movie = None  # Video nesnesini dışarıda tanımla (cevap ekranında kullanmak için)
    try:
        # PsychoPy versiyonuna göre MovieStim2 veya MovieStim kullan
        movie_class = None
        
        # Önce hangi sınıfın mevcut olduğunu kontrol et
        if hasattr(visual, 'MovieStim2'):
            movie_class = visual.MovieStim2
        elif hasattr(visual, 'MovieStim'):
            movie_class = visual.MovieStim
        else:
            raise Exception("Video oynatma desteği bulunamadı. PsychoPy'nin güncel bir versiyonunu kullanın.")
        
        # Video nesnesini oluştur (yukarıda konumlandır)
        try:
            # Video pozisyonunu ekran boyutuna göre dinamik olarak ayarla
            win_size = win.size
            video_pos = [0, int(win_size[1] * 0.15)]  # Ekranın üst %15'inde
            # size parametresini belirtmiyoruz - PsychoPy otomatik algılayacak
            # Eğer hata alırsak, pencere boyutuna göre ayarlayacağız
            try:
                movie = movie_class(
                    win,
                    str(video_path),
                    pos=video_pos,
                    flipVert=False,
                    flipHoriz=False,
                    loop=False
                )
            except TypeError:
                # Eğer size gerekliyse, pencere boyutunu kullan
                win_size = win.size
                movie = movie_class(
                    win,
                    str(video_path),
                    pos=video_pos,
                    size=win_size,
                    flipVert=False,
                    flipHoriz=False,
                    loop=False
                )
        except Exception as create_error:
            raise Exception(f"Video nesnesi oluşturulamadı: {create_error}")
        
        if movie is None:
            raise Exception("Video oluşturulamadı (None döndü)")
        
        # Video ve ses senkronizasyonu için hazırlık
        # Video nesnesini hazırla ve ilk frame'i göster
        try:
            movie.draw()
            win.flip()
            # Kısa bir hazırlık süresi (ses ve görüntü buffer'larını hazırla)
            core.wait(0.1)
        except:
            pass
        
        # Video oynatma döngüsü - 2 saniye sonra kesin çık
        clock = core.Clock()
        video_duration = 2.0  # 2 saniye sonra test ekranına geç
        
        while clock.getTime() < video_duration:
            # Escape tuşu kontrolü
            keys = event.getKeys()
            if 'escape' in keys:
                print("Kullanıcı Escape tuşuna bastı. Çıkılıyor...")
                break
            
            # Video çerçevesini çiz
            try:
                movie.draw()
                win.flip()
            except Exception as draw_error:
                # Video çiziminde hata - ekranı güncelle ve devam et
                win.flip()
        
        # 2 saniye tamamlandı - test ekranına geç
        print(f"Video gösterimi tamamlandı ({video_duration} saniye)")
        
    except Exception as e:
        import traceback
        print(f"HATA: Video oynatma hatası ({video_path}): {e}")
        print(f"Detay: {traceback.format_exc()}")
        
        # Hata durumunda da temizlik yap
        if movie is not None:
            try:
                if hasattr(movie, 'stop'):
                    movie.stop()
                del movie
                movie = None
                gc.collect()
            except:
                pass
        
        continue
    
    # 3. Cevap ekranı (videonun altında)
    # Tüm butonların renklerini sıfırla (önceki denemelerden kalan yeşil renkleri temizle)
    for button in buttons:
        button['rect'].fillColor = 'gray'
    
    # Cevap metnini ekran boyutuna göre dinamik olarak ayarla
    win_size = win.size
    response_text = visual.TextStim(
        win,
        text='Hangi sesi duydunuz?',
        pos=[0, -int(win_size[1] * 0.08)],  # Video altında, ekran boyutuna göre
        color='white',
        height=int(win_size[1] * 0.05)  # Ekran yüksekliğine göre
    )
    
    # Tepki süresi ölçümü başlat
    trial_clock.reset()
    response_received = False
    response = None
    reaction_time = None
    mouse_was_pressed = False
    
    # Cevap bekleme döngüsü
    while not response_received:
        # Escape tuşu kontrolü
        keys = event.getKeys()
        if 'escape' in keys:
            print("Kullanıcı Escape tuşuna bastı. Çıkılıyor...")
            response_received = True
            break
        
        # Video son karesini ve cevap ekranını çiz
        try:
            # Video nesnesi hala yaşıyorsa son kareyi çiz
            # Eğer temizlendiyse atla
            if movie is not None:
                movie.draw()  # Video son karesini göster
        except:
            pass  # Video çizilemezse devam et
        
        response_text.draw()
        for button in buttons:
            button['rect'].draw()
            button['text'].draw()
        
        win.flip()
        
        # Mouse tıklamasını kontrol et (sadece yeni tıklamaları yakala)
        mouse_clicked = mouse.getPressed()[0]  # Sol tıklama
        
        if mouse_clicked and not mouse_was_pressed:
            mouse_pos = mouse.getPos()
            
            # Hangi butona tıklandığını kontrol et
            for button in buttons:
                # Butonun sınırlarını kontrol et
                button_pos = button['pos']
                button_size = button['size']
                
                if (button_pos[0] - button_size[0]/2 <= mouse_pos[0] <= button_pos[0] + button_size[0]/2 and
                    button_pos[1] - button_size[1]/2 <= mouse_pos[1] <= button_pos[1] + button_size[1]/2):
                    
                    response = button['label']
                    reaction_time = trial_clock.getTime() * 1000  # ms'ye çevir
                    response_received = True
                    
                    # Tıklanan butonu vurgula
                    button['rect'].fillColor = 'green'
                    response_text.draw()
                    button['rect'].draw()
                    button['text'].draw()
                    win.flip()
                    core.wait(0.3)
                    break
        
        mouse_was_pressed = mouse_clicked
    
    # Veriyi kaydet
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
    
    # Denemeler arası kısa bekleme
    # TEMİZLİK: Bir sonraki videoya geçmeden önce ses kanalını serbest bırak
    if movie is not None:
        try:
            # Video nesnesini durdur (sesi keser)
            if hasattr(movie, 'stop'):
                movie.stop()
            # Bazı PsychoPy versiyonlarında pause/stop yeterli olmayabilir
            # Açıkça belleği temizle
            del movie
            movie = None
            # Çöp toplayıcıyı zorla çalıştır (C++ kaynaklarını serbest bırakmak için)
            gc.collect()
        except Exception as e:
            print(f"Uyarı: Video temizlenirken hata: {e}")

    if condition_idx < len(conditions) - 1:
        message_text.text = 'Bir sonraki denemeye hazır olun...'
        message_text.draw()
        win.flip()
        core.wait(1.0)

# Bitirme mesajı
finish_text = visual.TextStim(
    win,
    text='Test tamamlandı. Teşekkürler!',
    color='white',
    height=50
)
finish_text.draw()
win.flip()
core.wait(2.0)

# Pencereyi kapat
win.close()
core.quit()

