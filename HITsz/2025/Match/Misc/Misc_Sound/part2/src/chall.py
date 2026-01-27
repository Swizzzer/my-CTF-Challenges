import numpy as np
from scipy.io import wavfile
import sys

dtmf_frequencies = {
    '1': (697, 1209),
    '2': (697, 1336),
    '3': (697, 1477),
    '4': (770, 1209),
    '5': (770, 1336),
    '6': (770, 1477),
    '7': (852, 1209),
    '8': (852, 1336),
    '9': (852, 1477),
    '0': (941, 1336),
    '*': (941, 1209),
    '#': (941, 1477),
}

def generate_dtmf_tone(freq1, freq2, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone1 = 0.02 * np.sin(2 * np.pi * freq1 * t)
    tone2 = 0.02 * np.sin(2 * np.pi * freq2 * t)
    dtmf_tone = tone1 + tone2
    return dtmf_tone

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python script.py <input_string> <base_audio_file>")
        sys.exit(1)

    input_string = sys.argv[1]
    base_audio_path = sys.argv[2]

    input_string = ''.join([c for c in input_string if c in dtmf_frequencies])
    N = len(input_string)

    if N == 0:
        print("No valid DTMF characters found.")
        sys.exit(0)

    sample_rate = 44100
    tone_duration = 0.1
    silence_duration = 0.05
    tone_samples = int(sample_rate * tone_duration)
    silence_samples = int(sample_rate * silence_duration)
    period_samples = tone_samples + silence_samples
    total_samples = N * period_samples

    sample_rate_base, base_audio = wavfile.read(base_audio_path)

    if sample_rate_base != sample_rate:
        print(f"Error: The sample rate of the base audio must be {sample_rate} Hz.")
        sys.exit(1)

    if np.issubdtype(base_audio.dtype, np.integer):
        max_val = np.iinfo(base_audio.dtype).max
        base_audio = base_audio.astype(np.float32) / max_val
    else:
        base_audio = base_audio.astype(np.float32)
    
    print(base_audio.shape)
    if len(base_audio.shape) == 1:
        base_audio = np.column_stack((base_audio, base_audio))
    elif base_audio.shape[1] == 1:
        base_audio = np.repeat(base_audio[:, :1], 2, axis=1)
    else:
        base_audio = base_audio[:, :2]

    # audio padding
    current_length = base_audio.shape[0]
    print(current_length)
    if current_length < total_samples:
        repeat_times = (total_samples // current_length) + 1
        base_audio = np.tile(base_audio, (repeat_times, 1))[:total_samples]

    audio = base_audio.copy()

    for i, char in enumerate(input_string):
        freq1, freq2 = dtmf_frequencies[char]
        tone = generate_dtmf_tone(freq1, freq2, tone_duration, sample_rate)
        start = i * period_samples + 133337
        end = start + tone_samples
        audio[start:end, 0] += tone

    # audio = np.clip(audio, -1, 1)
    audio_int = np.int16(audio * 32767)
    wavfile.write('output.wav', sample_rate, audio_int)
    print(f"Generated output.wav with {N} DTMF tones.")