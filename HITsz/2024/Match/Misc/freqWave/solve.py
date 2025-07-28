import numpy as np
from scipy.io import wavfile

from scipy.fft import fft


def generate_sine_wave(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    return np.sin(2 * np.pi * freq * t)


def char_to_frequency(char):
    return ord(char) * 10


def frequency_to_char(freq):
    return chr(int(round(freq / 10)))


def wave_to_string(input_file="output.wav", sample_rate=44100):
    # Read the WAV file
    rate, data = wavfile.read(input_file)

    # Ensure the sample rate matches
    assert (
        rate == sample_rate
    ), f"Sample rate mismatch: expected {sample_rate}, got {rate}"

    # Split the data into 1-second chunks
    chunk_size = sample_rate
    chunks = [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]

    decoded_string = ""
    for chunk in chunks:
        # Perform FFT on the chunk
        fft_result = fft(chunk)

        # Find the frequency with the highest magnitude
        freqs = np.fft.fftfreq(len(fft_result), 1 / sample_rate)
        magnitudes = np.abs(fft_result)
        peak_freq = abs(freqs[np.argmax(magnitudes)])

        # Convert frequency back to character
        char = frequency_to_char(peak_freq)
        decoded_string += char

    return decoded_string


# Decode the WAV file back to string
decoded_string = wave_to_string()
print(f"Decoded string from WAV: {decoded_string}")
