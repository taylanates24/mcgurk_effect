"""
McGurk Etkisi Testi - PsychoPy Uygulaması
Bu uygulama katılımcılara video göstererek ses algılarını test eder.
"""

from psychopy import prefs
# Ses ayarlarını yapılandır (Düşük gecikme için)
prefs.hardware['audioLatencyMode'] = 3  # Aggressive low latency
prefs.hardware['audioLib'] = ['ptb', 'sounddevice', 'pyo', 'pygame']

from psychopy import visual, core, event, logging
import csv
import os
import warnings
from datetime import datetime
from pathlib import Path

# PsychoPy logging seviyesini ayarla (uyarıları azalt)
logging.console.setLevel(logging.ERROR)  # Sadece hataları göster

# Uyarıları bastır (sdl2 ve ffpyplayer uyarıları için)
warnings.filterwarnings('ignore', message='.*sdl2.*')
warnings.filterwarnings('ignore', message='.*ffpyplayer.*')
warnings.filterwarnings('ignore', message='.*audio.*synchronization.*')

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

# Speaker ID seçimi
print("\nMevcut Speaker ID'ler: 1-8")
speaker_id = input("Speaker ID seçin (1-8): ").strip()

# Speaker ID validasyonu
try:
    speaker_id_int = int(speaker_id)
    if speaker_id_int < 1 or speaker_id_int > 8:
        raise ValueError("Speaker ID 1-8 arasında olmalıdır")
except ValueError as e:
    print(f"HATA: Geçersiz Speaker ID. Varsayılan olarak 1 kullanılıyor.")
    speaker_id = "1"

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

# Koşulları dinamik olarak oluştur
# Visual ve audio kombinasyonları: ba-ba, ba-da, ba-ga, da-da, da-ba, da-ga, ga-ga, ga-da, ga-ba
conditions = []
combinations = [
    ('ba', 'ba'),  # visual, audio
    ('ba', 'da'),
    ('ba', 'ga'),
    ('da', 'da'),
    ('da', 'ba'),
    ('da', 'ga'),
    ('ga', 'ga'),
    ('ga', 'da'),
    ('ga', 'ba'),
]

for visual_label, audio_label in combinations:
    # Video dosya adını oluştur: Vis-{visual}_Aud-{audio}_Speaker-{speaker_id}.mp4
    video_filename = f"Vis-{visual_label}_Aud-{audio_label}_Speaker-{speaker_id}.mp4"
    # Etiket audio'ya göre olacak (audio neyse etiket o)
    expected_sound = audio_label.upper()  # BA, DA, GA
    
    conditions.append({
        'video_file': video_filename,
        'expected_sound': expected_sound
    })

# Veri kayıt dosyası oluştur
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
data_file = data_dir / f"{participant_name}_{timestamp}.csv"

# CSV başlıklarını yaz
with open(data_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Katilimci', 'VideoAdi', 'Cevap', 'DogruCevap', 'DogruMu', 'TepkiSuresi_ms'])

# Görsel öğeleri oluştur (ekran boyutuna göre dinamik)
win_size = win.size
fixation_cross = visual.TextStim(win, text='+', color='white', height=int(win_size[1] * 0.15))
message_text = visual.TextStim(win, text='', color='white', height=int(win_size[1] * 0.05))

# Cevap butonları oluştur (Rect + TextStim kombinasyonu)
# Ekran boyutuna göre dinamik boyutlandırma
win_size = win.size
button_labels = ['BA', 'DA', 'GA', 'PA', 'KA', 'TA']
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
    movie = None  # Video nesnesini dışarıda tanımla
    try:
        # PsychoPy versiyonuna göre en uygun MovieStim sınıfını seç
        movie_class = None
        
        # Kullanıcının bildirdiği "daha önce çözülmüştü" durumunda MovieStim3 kullanılmıştı.
        # MovieStim3 (MoviePy) öncelikli deniyoruz.
        if hasattr(visual, 'MovieStim3'):
            movie_class = visual.MovieStim3
        elif hasattr(visual, 'MovieStim2'):
            movie_class = visual.MovieStim2
        elif hasattr(visual, 'MovieStim'):
            movie_class = visual.MovieStim
        else:
            raise Exception("Video oynatma desteği bulunamadı.")
        
        # Video nesnesini oluştur
        try:
            # Video pozisyonunu ekran boyutuna göre dinamik olarak ayarla
            win_size = win.size
            video_pos = [0, int(win_size[1] * 0.15)]
            
            # Video boyutunu belirle (None hatasını önlemek için somut bir boyut veriyoruz)
            movie_size = [int(win_size[0] * 0.6), int(win_size[1] * 0.6)]
            
            # MovieStim3'ü en basit haliyle, varsayılan ayarlarla başlat
            # autoStart veya noAudio gibi parametreleri vermiyoruz, varsayılanları kullansın
            try:
                movie = movie_class(
                    win,
                    str(video_path),
                    pos=video_pos,
                    size=movie_size, # Somut boyut veriyoruz, None değil
                    flipVert=False,
                    flipHoriz=False,
                    loop=False
                )
            except TypeError:
                # Parametre hatası olursa (çok eski versiyonlar)
                movie = movie_class(
                    win,
                    str(video_path),
                    pos=video_pos,
                    flipVert=False,
                    flipHoriz=False,
                    loop=False
                )
        except Exception as create_error:
             # Eğer somut boyutla da hata alırsak, bir de size parametresini hiç vermeden deneyelim
            try:
                movie = movie_class(
                    win,
                    str(video_path),
                    pos=video_pos,
                    flipVert=False,
                    flipHoriz=False,
                    loop=False
                )
            except Exception as retry_error:
                raise Exception(f"Video nesnesi oluşturulamadı: {create_error} | Retry: {retry_error}")
        
        if movie is None:
            raise Exception("Video oluşturulamadı (None döndü)")
        
        # Video oynatma döngüsü
        # MovieStim3'te video oluşturulur oluşturulmaz (veya ilk draw'da) oynamaya başlar (varsayılan autoStart=True)
        is_finished = False
        while not is_finished:
            # Escape tuşu kontrolü
            keys = event.getKeys()
            if 'escape' in keys:
                print("Kullanıcı Escape tuşuna bastı. Çıkılıyor...")
                break
            
            # Bitiş kontrolü
            if hasattr(movie, 'isFinished'):
                is_finished = movie.isFinished
            elif hasattr(movie, 'status'):
                is_finished = (movie.status == visual.FINISHED)
            
            # Video çerçevesini çiz ve ekranı güncelle
            try:
                movie.draw()
                win.flip()
            except Exception as draw_error:
                win.flip()
        
        # Video bitti
        print(f"Video gösterimi tamamlandı")
        
        # Video nesnesini hemen durdur ve kapat
        try:
            if movie is not None:
                if hasattr(movie, 'stop'):
                    movie.stop()
                # Bellek sızıntısını önlemek için
                # MovieStim3 için özel bir kapatma gerekebilir
                pass
        except Exception as close_err:
            print(f"Video durdurma uyarısı: {close_err}")
            
        # Kısa bir bekleme
        core.wait(0.1)
        
    except Exception as e:
        import traceback
        print(f"HATA: Video oynatma hatası ({video_path}): {e}")
        print(f"Detay: {traceback.format_exc()}")
        continue
        
        # Video nesnesini hemen durdur ve kapat (ses cihazını serbest bırakmak için)
        try:
            if movie is not None:
                # Önce durdur
                if hasattr(movie, 'stop'):
                    movie.stop()
                if hasattr(movie, 'pause'):
                    movie.pause()
                # Sonra kapat
                if hasattr(movie, 'close'):
                    movie.close()
                # Nesneyi None yap ki cevap ekranında kullanılmasın
                movie = None
        except Exception as close_err:
            print(f"Video kapatma uyarısı: {close_err}")
            movie = None
        
        # Kısa bir bekleme (ses cihazının tamamen kapanması için)
        core.wait(0.1)
        
    except Exception as e:
        import traceback
        print(f"HATA: Video oynatma hatası ({video_path}): {e}")
        print(f"Detay: {traceback.format_exc()}")
        # Hata durumunda da video nesnesini kapat
        try:
            if movie is not None:
                if hasattr(movie, 'stop'):
                    movie.stop()
                if hasattr(movie, 'close'):
                    movie.close()
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
        
        # Cevap ekranını çiz (video kapatıldığı için çizmiyoruz)
        # Video son karesini göstermek isterseniz, video kapatmadan önce son frame'i kaydedebilirsiniz
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
        # Cevabın doğru olup olmadığını kontrol et
        dogru_mu = 1 if response.upper() == condition['expected_sound'].upper() else 0
        
        with open(data_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                participant_name,
                condition['video_file'],
                response,
                condition['expected_sound'],  # Doğru cevap (etiket)
                dogru_mu,  # Doğru ise 1, yanlış ise 0
                f"{reaction_time:.2f}" if reaction_time else ""
            ])
    
    # Video nesnesi zaten kapatıldı (yukarıda), burada sadece temizlik yapıyoruz
    if movie is not None:
        try:
            if hasattr(movie, 'stop'):
                movie.stop()
            if hasattr(movie, 'close'):
                movie.close()
        except:
            pass
        movie = None
    
    # Denemeler arası kısa bekleme
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

