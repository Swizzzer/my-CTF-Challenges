import numpy as np
from scipy.io import wavfile


def generate_sine_wave(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t)


def char_to_frequency(char):
    return ord(char) * 10


def string_to_wave(input_string, output_file="output.wav", sample_rate=44100):
    waves = []
    for char in input_string:
        freq = char_to_frequency(char)
        wav = generate_sine_wave(freq, 1, sample_rate)
        waves.append(wav)

    combined_wave = np.concatenate(waves)

    normalized_wave = np.int16(combined_wave * 32767)

    wavfile.write(output_file, sample_rate, normalized_wave)


input_string = open("flag.txt", "r").read().strip()
string_to_wave(input_string)
