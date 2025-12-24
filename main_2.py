#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
McGurk Effect Experiment - PsychoPy Implementation
Author: McGurk Proje Uzmanı
"""

# ==============================================================================
# 1. AYARLAR VE KÜTÜPHANELER (GECİKME ÖNLEME)
# ==============================================================================
from psychopy import prefs

# Ses gecikmesini önlemek için 'ptb' (Psychtoolbox) öncelikli yapıyoruz.
# Latency Mode 3: "Aggressive low latency" (En düşük gecikme modu)
prefs.hardware['audioLib'] = ['ptb', 'sounddevice', 'pyo', 'pygame']
prefs.hardware['audioLatencyMode'] = 3

from psychopy import visual, core, event, gui, data, logging
import pandas as pd
import os
import random

# ==============================================================================
# 2. KURULUM (SETUP)
# ==============================================================================

# Dizin tanımları
ASSETS_DIR = 'assets'
DATA_DIR = 'data'
CONDITIONS_FILE = 'conditions.csv'

# Klasör kontrolü
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
if not os.path.exists(ASSETS_DIR):
    print(f"UYARI: '{ASSETS_DIR}' klasörü bulunamadı. Lütfen videoları buraya ekleyin.")
    os.makedirs(ASSETS_DIR)

# ==============================================================================
# 3. GUI: KATILIMCI BİLGİLERİ (Startup Dialog)
# ==============================================================================
expInfo = {
    'Katılımcı ID': '',
    'Yaş': '',
    'Cinsiyet': ['Kadin', 'Erkek', 'Diger']
}

# Dialog kutusunu göster
dlg = gui.DlgFromDict(dictionary=expInfo, title='McGurk Etkisi Deneyi', sortKeys=False)

if not dlg.OK:
    print("Kullanıcı iptal etti.")
    core.quit()

# Tarih ekle
expInfo['date'] = data.getDateStr(format="%Y-%m-%d_%Hh%M")
filename = f"{expInfo['Katılımcı ID']}_{expInfo['date']}"
filepath = os.path.join(DATA_DIR, filename)

# ==============================================================================
# 4. PENCERE VE UYARANLARIN HAZIRLANMASI
# ==============================================================================
# Tam ekran siyah pencere
win = visual.Window(
    size=[1920, 1080], 
    fullscr=True, 
    screen=0, 
    color='black', 
    units='pix',
    waitBlanking=True # V-Sync açık (Yırtılmaları önler)
)

# Mouse nesnesi
mouse = event.Mouse(visible=False, win=win)

# Fixation Cross (Odaklanma noktası)
fixation = visual.TextStim(win, text='+', color='white', height=50)

# Yönerge Metni
instruction_text = visual.TextStim(win, 
    text="Lütfen videoları dikkatlice izleyin.\n\n"
         "Videodan sonra, DUYDUĞUNUZ heceyi seçin.\n\n"
         "Başlamak için farenin sol tuşuna tıklayın.",
    color='white', height=30, wrapWidth=1000
)

# Cevap Seçenekleri (Butonlar)
button_labels = ["BA", "DA", "GA", "PA", "KA", "TA"]
buttons = []
button_positions = [-400, -250, -100, 100, 250, 400] # X koordinatları

for i, label in enumerate(button_labels):
    # Buton Kutusu
    rect = visual.Rect(win, width=120, height=80, pos=(button_positions[i], -200),
                       fillColor='gray', lineColor='white')
    # Buton Yazısı
    text = visual.TextStim(win, text=label, pos=(button_positions[i], -200),
                           color='white', height=40, bold=True)
    buttons.append({'rect': rect, 'text': text, 'label': label})

# ==============================================================================
# 5. DENEY VERİSİ YÜKLEME
# ==============================================================================
try:
    # Pandas ile CSV oku (daha güvenli) veya PsychoPy TrialHandler kullan
    conditions_df = pd.read_csv(CONDITIONS_FILE)
    # DataFrame'i sözlük listesine çevir
    trial_list = conditions_df.to_dict('records')
except FileNotFoundError:
    print(f"HATA: {CONDITIONS_FILE} bulunamadı!")
    core.quit()

# Deney İşleyicisi (ExperimentHandler veriyi otomatik kaydeder)
thisExp = data.ExperimentHandler(name='McGurkExp', version='1.0',
                                 extraInfo=expInfo, 
                                 dataFileName=filepath)

# Döngüyü oluştur (TrialHandler)
trials = data.TrialHandler(trialList=trial_list, nReps=1, method='random')
thisExp.addLoop(trials)

# ==============================================================================
# 6. DENEY AKIŞI (EXPERIMENT LOOP)
# ==============================================================================

# Yönerge Ekranı
instruction_text.draw()
win.flip()
mouse.setVisible(True)
event.waitKeys(keyList=['space', 'return']) # Klavye veya mouse beklenebilir
while not mouse.getPressed()[0]: # Mouse tıklaması bekle
    core.wait(0.01)

mouse.setVisible(False) 

# Ana Döngü
for trial in trials:
    # ESC Kontrolü
    if 'escape' in event.getKeys():
        print("Deney kullanıcı tarafından sonlandırıldı.")
        break

    video_path = os.path.join(ASSETS_DIR, trial['video_file'])
    
    # Video Dosyası Var mı?
    if not os.path.exists(video_path):
        print(f"Video bulunamadı atlanıyor: {video_path}")
        continue

    # --- 1. FIXATION (500ms) ---
    fixation.draw()
    win.flip()
    core.wait(0.500)
    
    # --- 2. STIMULUS (VIDEO) ---
    # MovieStim: FFmpeg backend kullanır, sync daha iyidir.
    movie = visual.MovieStim(
        win, 
        video_path, 
        size=(1280, 720), # Videoyu orantılı scale eder
        pos=(0, 100),
        flipVert=False, 
        flipHoriz=False, 
        loop=False,
        noAudio=False
    )
    
    # Video oynarken bekle
    while movie.status != visual.FINISHED:
        movie.draw()
        win.flip()
        
        # Acil çıkış kontrolü video sırasında da olmalı
        if 'escape' in event.getKeys():
            core.quit()
            
    # Video bittiğinde kaynakları temizle (önemli!)
    # Bu yapılmazsa bellek dolar ve sonraki videolarda ses kayması olur.
    movie.stop() 
    del movie 
    win.flip() # Ekranı temizle

    # --- 3. RESPONSE SCREEN ---
    mouse.setPos(newPos=(0, -200)) # Mouse'u butonların yakınına ışınla
    mouse.setVisible(True)
    mouse.clickReset() # Önceki tıklamaları temizle
    
    response_clock = core.Clock() # RT sayacı
    responded = False
    
    while not responded:
        # Butonları çiz
        for btn in buttons:
            # Mouse üzerine gelirse renk değiştir (Hover effect)
            if btn['rect'].contains(mouse):
                btn['rect'].fillColor = 'dimgray'
            else:
                btn['rect'].fillColor = 'gray'
            
            btn['rect'].draw()
            btn['text'].draw()
            
        win.flip()

        # Tıklama kontrolü
        if mouse.getPressed()[0]: # Sol tık
            for btn in buttons:
                if btn['rect'].contains(mouse):
                    # Cevap alındı
                    rt = response_clock.getTime() * 1000 # ms cinsinden
                    response_val = btn['label']
                    responded = True
                    
                    # Seçilen butonu yeşil yak (Geri bildirim)
                    btn['rect'].fillColor = 'green'
                    btn['rect'].draw()
                    btn['text'].draw()
                    win.flip()
                    core.wait(0.2) # Kısa bir süre sonucu göster
                    break
        
        # ESC Kontrolü
        if 'escape' in event.getKeys():
            core.quit()

    mouse.setVisible(False)

    # --- 4. DATA LOGGING ---
    # ExperimentHandler otomatik olarak .csv sütunlarını yönetir
    trials.addData('response', response_val)
    trials.addData('rt_ms', rt)
    
    # Beklenen cevapla karşılaştırma (Opsiyonel analiz için)
    is_correct = 1 if response_val == trial['expected_sound'] else 0
    trials.addData('accuracy', is_correct)
    
    # Satırı kaydet (Her trial sonunda kaydeder, veri kaybını önler)
    thisExp.nextEntry()

# ==============================================================================
# 7. BİTİŞ (CLEANUP)
# ==============================================================================
end_text = visual.TextStim(win, text="Deney tamamlandı.\nKatılımınız için teşekkürler.", color='white')
end_text.draw()
win.flip()
core.wait(2)

win.close()
core.quit()