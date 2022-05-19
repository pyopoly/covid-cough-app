import json
import os
import math
import librosa
import sys

# give the desire path
# DATASET_PATH = "C:/Users/tommy/Documents/rnn_model/spectrum_test/"
# JSON_PATH = "data.json"


DATASET_PATH = "file/" + sys.argv[1]
JSON_PATH = "file/" + sys.argv[1] + '/data.json'
# SAMPLE_RATE = 22050
SAMPLE_RATE = 7500
TRACK_DURATION = 0.55 # measured in seconds
SAMPLES_PER_TRACK = SAMPLE_RATE * TRACK_DURATION


def save_mfcc(dataset_path, json_path, num_mfcc=13, n_fft=2048, hop_length=512, num_segments=5):
    """Extracts MFCCs from music dataset and saves them into a json file along witgh genre labels.
        :param dataset_path (str): Path to dataset
        :param json_path (str): Path to json file used to save MFCCs
        :param num_mfcc (int): Number of coefficients to extract
        :param n_fft (int): Interval we consider to apply FFT. Measured in # of samples
        :param hop_length (int): Sliding window for FFT. Measured in # of samples
        :param: num_segments (int): Number of segments we want to divide sample tracks into
        :return:
        """

    # dictionary to store mapping, labels, and MFCCs
    data = {
        "mapping": [],
        "labels": [],
        "mfcc": []
    }
    hop_length = 505
    samples_per_segment = int(SAMPLES_PER_TRACK / num_segments)
    num_mfcc_vectors_per_segment = math.ceil(samples_per_segment / hop_length)
    # loop through all genre sub-folder
    print(dataset_path)
    for i, (dirpath, dirnames, filenames) in enumerate(os.walk(dataset_path)):
        print(i)

        # ensure we're processing a genre sub-folder level
        print(dirpath is not dataset_path)
        if dirpath is not dataset_path:

            # save genre label (i.e., sub-folder name) in the mapping
            semantic_label = dirpath.split("/")[-1]
            data["mapping"].append(semantic_label)
            print("\nProcessing: {}".format(semantic_label))

            # process all audio files in genre sub-dir
            for f in filenames:
                print(f)

        # load audio file
                file_path = os.path.join(dirpath, f)
                print(file_path)
                signal, sample_rate = librosa.load(file_path, sr=SAMPLE_RATE)
                # print(f"sample rate {sample_rate}")
                # process all segments of audio file
                for d in range(num_segments):

                    # calculate start and finish sample for current segment
                    start = samples_per_segment * d
                    finish = start + samples_per_segment
                    # extract mfcc
                    mfcc = librosa.feature.mfcc(signal[start:finish], sample_rate, n_mfcc=num_mfcc, n_fft=n_fft, hop_length=hop_length)
                    mfcc = mfcc.T
                    # store only mfcc feature with expected number of vectors
                    if len(mfcc) == num_mfcc_vectors_per_segment:
                        data["mfcc"].append(mfcc.tolist())
                        data["labels"].append(i-1)

    # save MFCCs to json file
    with open(json_path, "w") as fp:
        json.dump(data, fp, indent=4)
        
        
# if __name__ == "__main__":
# print('start')
# print(DATASET_PATH, JSON_PATH)
save_mfcc(DATASET_PATH, JSON_PATH, num_segments=1)