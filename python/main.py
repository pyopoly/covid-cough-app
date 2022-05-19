import sys
import wave
import numpy as np
from os import listdir
import shutil, os, os.path
import subprocess
from os.path import isfile
import pandas as pd
from scipy.io.wavfile import write, read

from scipy.signal import find_peaks

# Sampling rate is 48kHz (originally)
sampling_rate = 48000
cough_length = 30000
reduction_ratio = 4


def read_sound_file(file):
    # Read file to get buffer
    ifile = wave.open(file)
    samples = ifile.getnframes()
    audio = ifile.readframes(samples)
    # sampleRate, data = read(file)


    # Convert buffer to float32 using NumPy
    audio_as_np_int16 = np.frombuffer(audio, dtype=np.int16)
    audio_as_np_float32 = audio_as_np_int16.astype(np.float32)

    # Normalise float32 array so that values are between -1.0 and +1.0
    max_int16 = 2 ** 15
    audio_normalised = audio_as_np_float32 / max_int16
    return audio_normalised
    # return sampleRate, data

def segment_cough(x, fs, cough_padding=0.2, min_cough_len=0.2, th_l_multiplier=0.1, th_h_multiplier=2):
    """Preprocess the data by segmenting each file into individual coughs using a hysteresis comparator on the signal power

    Inputs:
    *x (np.array): cough signal
    *fs (float): sampling frequency in Hz
    *cough_padding (float): number of seconds added to the beginning and end of each detected cough to make sure coughs are not cut short
    *min_cough_length (float): length of the minimum possible segment that can be considered a cough
    *th_l_multiplier (float): multiplier of the RMS energy used as a lower threshold of the hysteresis comparator
    *th_h_multiplier (float): multiplier of the RMS energy used as a high threshold of the hysteresis comparator

    Outputs:
    *coughSegments (np.array of np.arrays): a list of cough signal arrays corresponding to each cough
    cough_mask (np.array): an array of booleans that are True at the indices where a cough is in progress"""

    cough_mask = np.array([False] * len(x))

    # Define hysteresis thresholds
    rms = np.sqrt(np.mean(np.square(x)))
    seg_th_l = th_l_multiplier * rms
    seg_th_h = th_h_multiplier * rms

    # Segment coughs
    coughSegments = []
    padding = round(fs * cough_padding)
    min_cough_samples = round(fs * min_cough_len)
    cough_start = 0
    cough_end = 0
    cough_in_progress = False
    tolerance = round(0.01 * fs)
    below_th_counter = 0

    for i, sample in enumerate(x ** 2):
        if cough_in_progress:
            if sample < seg_th_l:
                below_th_counter += 1
                if below_th_counter > tolerance:
                    cough_end = i + padding if (i + padding < len(x)) else len(x) - 1
                    cough_in_progress = False
                    if (cough_end + 1 - cough_start - 2 * padding > min_cough_samples):
                        coughSegments.append(x[cough_start:cough_end + 1])
                        cough_mask[cough_start:cough_end + 1] = True
            elif i == (len(x) - 1):
                cough_end = i
                cough_in_progress = False
                if (cough_end + 1 - cough_start - 2 * padding > min_cough_samples):
                    coughSegments.append(x[cough_start:cough_end + 1])
            else:
                below_th_counter = 0
        else:
            if sample > seg_th_h:
                cough_start = i - padding if (i - padding >= 0) else 0
                cough_in_progress = True

    return coughSegments, cough_mask


def clean_wav_files(data):
    length = 7500
    max = 1
    low_peaks = []
    padded = []
    while len(low_peaks) < 2 or (low_peaks[-1] - low_peaks[0]) < 2000:
        low_peaks, properties = find_peaks(data, prominence=(None, max))
        max = max + 1
    start, end = low_peaks[0], low_peaks[-1]

    for i, p in enumerate(low_peaks):
        if (p - start) < 2000:
            start = p
        else:
            end = low_peaks[i]
            break
    if start != end:
        trimmed = data[start:end]
        padded = np.pad(trimmed, (0, length - len(trimmed)), 'constant')
    return padded

def pad_cough(np_cough, length):
    if len(np_cough) > length:
        np_cough = np_cough[:length]
    elif len(np_cough) < length:
        pad_len = length - len(np_cough)
        np_cough = np.pad(np_cough, (0, pad_len), 'constant', constant_values=(0, 0))
    return np_cough


def custom_segment(file, new_folder, path, cough_length):
    new_filenames = []
    names = []
    length = []
    final = []
    max_int16 = 2 ** 15
    name = file.replace('.wav', '')
    np_file = read_sound_file(path + '/' + file)
    final, seg_m = segment_cough(np_file, sampling_rate, min_cough_len=0.01)
    # for s in seg:
    #     segment, seg_m = segment_cough(s, sampling_rate, min_cough_len=0.01)
    #     for cough in segment:
    #         final.append(cough)

    for index, cough in enumerate(final):
        cough = pad_cough(cough, cough_length)
        cough = cough * max_int16  # undo normalized audio
        reduced = cough[::reduction_ratio]
        reduced_cleaned = clean_wav_files(reduced)
        new_name = name + "_" + str(index)
        if len(reduced_cleaned) != 0:
            new = path + '/' + new_folder + '/' + new_name + '.wav'
            write(new, int(sampling_rate / reduction_ratio), reduced_cleaned.astype(np.int16))
            # new_filenames.append(new_name)
            names.append(new_name)
            length.append(len(reduced_cleaned))

    return names, length


# ===============
# print('main.py started')
new_files, length = custom_segment('cough.wav', "segmented_coughs", sys.argv[1], cough_length)
# cough = sys.argv[2]
print(new_files, end="")
# for n in new_files:
#     print(n)
# print('main.py ended')
