import math
from pydub import AudioSegment
from mutagen.mp3 import MP3
from mutagen.mp3 import BitrateMode

def adjust_volume(input_path, output_path, volume_factor):
    audio_info = MP3(input_path)
    bitrate = audio_info.info.bitrate // 1000  # 转换为kbps
    bitrate_str = f"{bitrate}k"
    bitrate_mode = audio_info.info.bitrate_mode

    sound = AudioSegment.from_mp3(input_path)

    gain_db = 20 * math.log10(volume_factor)
    adjusted_sound = sound.apply_gain(gain_db)

    if bitrate_mode == BitrateMode.VBR:
        adjusted_sound.export(output_path, format="mp3", parameters=["-q:a", "0"])
    else:
        adjusted_sound.export(output_path, format="mp3", bitrate=bitrate_str)

if __name__ == "__main__":
    input_file = "input.mp3"
    output_file = "output.mp3"
    adjust_volume(input_file, output_file, 0.001)
