import numpy as np
from scipy.io import wavfile

def ensure_stereo(audio):
    """确保音频为立体声（二维数组）"""
    if audio.ndim == 1:
        return np.column_stack((audio, audio))
    return audio

def normalize_audio(audio):
    """将音频数据归一化到[-1, 1]范围"""
    if np.issubdtype(audio.dtype, np.integer):
        max_val = np.iinfo(audio.dtype).max
        return audio.astype(np.float32) / max_val
    return audio.astype(np.float32)

base_path = 'input.wav'
output_path = 'output.wav'

sr_base, base_audio = wavfile.read(base_path)
sr_output, output_audio = wavfile.read(output_path)

if sr_base != sr_output:
    raise ValueError("错误：两个音频文件的采样率不一致")

base_audio = ensure_stereo(base_audio)
output_audio = ensure_stereo(output_audio)

output_length = output_audio.shape[0]
base_length = base_audio.shape[0]

if base_length < output_length:
    repeat_times = (output_length // base_length) + 1
    base_audio = np.tile(base_audio, (repeat_times, 1))[:output_length]
else:
    base_audio = base_audio[:output_length]

base_float = normalize_audio(base_audio)
output_float = normalize_audio(output_audio)
dtmf_audio = output_float - base_float
dtmf_audio = np.clip(dtmf_audio, -1.0, 1.0)
dtmf_int16 = (dtmf_audio * 32767).astype(np.int16)
wavfile.write('dtmf_extracted.wav', sr_base, dtmf_int16)
print("DTMF音频已成功保存为 dtmf_extracted.wav")