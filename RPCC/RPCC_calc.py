import matplotlib.pyplot as plt
import sys
import librosa
import numpy as np
import scipy
import csv
import contextlib
import wave
from numba import jit, cuda 
from timeit import default_timer as timer 
import torch
from pathlib import Path

import time
from multiprocessing import Process
import os

def calculateRPCC(audio):
    sample_frequency = 16000
    frame_length = sample_frequency // 4 # 25 ms
    low_frequency = 20
    high_frequency = 7600
    num_mel_bins = 30

    # s_n, _ = librosa.load(path, sr=16000)
# #         # Calculate Residual Signal
    lpc_coefficients = librosa.lpc(audio, 22)
    s_n_hat = scipy.signal.lfilter([0] + -1*lpc_coefficients[1:], [1], audio)
    r_n = audio - s_n_hat
    #     # Do Hilbert Transform
    #     # Analytical Signal
    analytical_signal = scipy.signal.hilbert(r_n)
#     # Residual phase
    residual_phase = analytical_signal.real / abs(analytical_signal)
# #         # FFT and magnitude
    win_length = sample_frequency // 4
    hop_length = sample_frequency // 10
    n_fft = 4096 # QUESTION: Should this be changed?
    magnitude_spectrum = np.abs(librosa.stft(residual_phase, n_fft=n_fft, win_length=win_length, hop_length=hop_length))
    # Warp to mel
    mel = librosa.filters.mel(sr=sample_frequency, n_fft=n_fft, n_mels=num_mel_bins, fmin=low_frequency, fmax=high_frequency)
    mel_warped_signal = mel.dot(magnitude_spectrum)
    # Log Signal
    log_spectrum = np.log(mel_warped_signal)
    # DCT of Signal
    dct_spectrum = scipy.fftpack.dct(log_spectrum)

    return dct_spectrum

if __name__=="__main__": 
    log_stamp = time.asctime( time.localtime(time.time()))

    LIST_PROCESSED_FILES = "processed_files.txt"

    log = open("logs/{}.processing.log".format(log_stamp),"w")
    log_processed_files = open("{}".format(LIST_PROCESSED_FILES),"w")

    root = Path("vox1_dev_wav")
    end_root_path = "Processed"

    files = [str(f) for f in root.glob('**/*.wav')  if f.is_file()]

    pre_processed = Path("{}/{}".format(end_root_path, str(root)))
    
    processed_files = [str(f)[(len(end_root_path)+1):-4] for f in pre_processed.glob('**/*.wav.npy')  if f.is_file()]

    files_to_process = [f for f in files if f not in processed_files]

    file_diff = len(files) - len(files_to_process)

    print("Found a total of {} files".format(len(files)))
    print("{} Files have already been processed previously.".format(len(processed_files)))
    print("Processing {} files".format(len(files_to_process)))
    log.write("{} files was previously processed".format(file_diff))

    log.write("Processing {} files \n".format(len(files_to_process)))
    #start = timer()
    i = 0
    for audio_file in files_to_process:
        ts = time.asctime( time.localtime(time.time()))

        # if "1_00011_m_06_" in str(audio_file):
        #     print("Skipped session 6 for speaker 11")
        #     continue
        log.write("{} - Processing file: {}".format(ts, str(audio_file)))
        print("Processing file {}".format(str(audio_file)))
        try:
            waveform, _ =  librosa.load(audio_file, sr=16000)
            result = calculateRPCC(waveform)

            path = "{}/{}".format(end_root_path, str(os.path.dirname(audio_file)))
            if not os.path.exists(path):
                os.makedirs(path)

            np.save("{}/{}".format(end_root_path, str(audio_file)), result)
            if i % 100 == 0:
                timestamp = time.asctime( time.localtime(time.time()))
                print("{} - Processed {} features.".format(timestamp, i))
            log.write(" - processed \n")

            log_processed_files.write("{}\n".format(str(audio_file)))
            i = i + 1

        except:
            
            if i % 100 == 0:
                timestamp = time.asctime( time.localtime(time.time()))
                print("{} - Processed {} features.".format(timestamp, i))
            
            log.write (" - error occured")
            i = i + 1

    log.close()
    log_processed_files.close()
