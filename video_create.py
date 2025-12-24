from moviepy import VideoFileClip
import os

# Kaynak videoların listesi (Uzantıları ile birlikte)
sources = ['ba', 'da', 'ga']
input_folder = "videos_8"  # Ham videoların olduğu klasör

# Speaker ID'yi input_folder'dan çıkar (örn: "videos_2" -> "2")
speaker_id = input_folder.split("_")[-1]

# Output folder'ı dinamik oluştur
output_folder = f"{input_folder}_out"  # Hazır videoların gideceği klasör

# Klasör yoksa oluştur
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Çaprazlama Döngüsü
for visual_label in sources:
    for audio_label in sources:
        
        # 1. Görüntü kaynağını yükle (Sesi kapatıyoruz)
        video_clip = VideoFileClip(f"{input_folder}/{visual_label}.mp4")
        
        # 2. Ses kaynağını yükle (Sadece sesini alacağız)
        audio_clip = VideoFileClip(f"{input_folder}/{audio_label}.mp4").audio
        
        # 3. Sesi görüntüye monte et
        final_clip = video_clip.with_audio(audio_clip)
        
        # 4. Dosya isimlendirme (Örn: Vis-BA_Aud-DA_Speaker-2.mp4)
        output_filename = f"Vis-{visual_label}_Aud-{audio_label}_Speaker-{speaker_id}.mp4"
        save_path = os.path.join(output_folder, output_filename)
        
        print(f"Oluşturuluyor: {output_filename}...")
        
        # 5. Dosyayı kaydet
        final_clip.write_videofile(save_path, codec='libx264', audio_codec='aac')

print("Tüm kombinasyonlar hazır!")