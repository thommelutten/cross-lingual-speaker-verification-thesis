import pandas as pd
import torch.utils.data as data
import numpy as np
import torch
from pathlib import Path

class VoxCelebDataset(data.Dataset):
    def __init__(self, pandaframe, targets, root_dir):
        self.dataset = pandaframe
        self.targets = targets
        self.root_dir = root_dir
        self.len = len(pandaframe)
        
    def __getitem__(self, index):
        speaker = self.dataset.iloc[index]
        path_to_rpcc = "{}/{}".format(self.root_dir, speaker['Audio Path'])
        rpcc = np.load(path_to_rpcc)

        return torch.Tensor(rpcc[0:13,0:40]), speaker['VoxCeleb1 ID']
    
    def __len__(self):
        return self.len

class VoxCeleb():
    def __init__(self, metadata_path, audio_dev_path, audio_test_path):
        self.metadata_path = metadata_path
        self.audio_dev_path = audio_dev_path
        self.audio_test_path = audio_test_path

    def create_train_and_test_datasets_and_speaker_to_index(self, minimum_frames, minimum_samples):
        print("Splitting dataset into train and test")
        train_pandaframe, test_pandaframe = self.__split_dataset_into_train_and_test_pandaframes__()
        print("Filtering frames from datasets lower than {}".format(minimum_frames))
        train_pandaframe = self.__filter_frames_from_dataset_lower_than__(train_pandaframe, minimum_frames, self.audio_dev_path)
        test_pandaframe = self.__filter_frames_from_dataset_lower_than__(test_pandaframe, minimum_frames, self.audio_test_path)

        print("Filtering samples so each speaker only has {} samples".format(minimum_samples))
        train_pandaframe = self.__filter_samples__(train_pandaframe, minimum_samples)
        test_pandaframe = self.__filter_samples__(test_pandaframe, minimum_samples)

        print("Creating speaker id indexing lists")
        speaker_id_to_index, speaker_index_to_id = self.__amount_of_speakers_total__(train_pandaframe, test_pandaframe)
        print("Creating VoxCelebDatasets")
        train_dataset = VoxCelebDataset(train_pandaframe, speaker_id_to_index, self.audio_dev_path)
        test_dataset = VoxCelebDataset(test_pandaframe, speaker_id_to_index, self.audio_test_path)

        return train_dataset, test_dataset, speaker_id_to_index, speaker_index_to_id


    def __split_dataset_into_train_and_test_pandaframes__(self):
        metadata = pd.read_csv(self.metadata_path, delimiter='\t')
        train_pf = metadata.loc[metadata['Set'] == 'dev']
        test_pf = metadata.loc[metadata['Set'] == 'test']

        train_pf = self.__append_audio_files_to_pf__(train_pf, self.audio_dev_path)
        test_pf = self.__append_audio_files_to_pf__(test_pf, self.audio_test_path)

        return train_pf, test_pf

    def __append_audio_files_to_pf__(self, pandaframe, audio_path):
        list_with_audio_files = []
        
        for _, row in pandaframe.iterrows():
            list_of_audio_files = self.__find_audio_files__(row['VoxCeleb1 ID'], audio_path)
            for audio in list_of_audio_files:
                audio_path_parts = str(audio).split('/')
                list_with_audio_files.append([row['VoxCeleb1 ID'], row['Gender'], row['Nationality'], row['Set'], '/'.join(audio_path_parts[4:])])
        return pd.DataFrame(list_with_audio_files, columns = ['VoxCeleb1 ID', 'Gender', 'Nationality', 'Set', 'Audio Path'])
        
    def __find_audio_files__(self, speaker_id, audio_path):
        audio_path = Path(audio_path)
        return [f for f in audio_path.glob("{}/**/*.wav.npy".format(speaker_id)) if f.is_file()]

    def __filter_frames_from_dataset_lower_than__(self, pandaframe, minimum_frames, audio_path):
        frames_lower_than_minimum = []
        for index, row in pandaframe.iterrows():
            rpcc = np.load("{}/{}".format(audio_path,row['Audio Path']))    
            if len(rpcc[1]) < 40:
                frames_lower_than_minimum.append(index)

        pandaframe = pandaframe.drop(index=frames_lower_than_minimum)

        return pandaframe


    def __filter_samples__(self, pandaframe, samples):
        print("Size of dataset is: {}.".format(len(pandaframe)))
        speakers = pandaframe['VoxCeleb1 ID'].unique()
        pandaframe_cleaned = pd.DataFrame(columns=pandaframe.columns)
        for speaker in speakers:
            utterances = pandaframe.loc[pandaframe['VoxCeleb1 ID'] == speaker]
            utterances_to_keep = utterances[:samples]
            pandaframe_cleaned = pandaframe_cleaned.append(utterances_to_keep)
        print("Cleaned dataset size is now: {}.".format(len(pandaframe_cleaned)))
        return pandaframe_cleaned


    def __amount_of_speakers_total__(self, train_pandaframe, test_pandaframe):
        train_speaker_ids = (train_pandaframe['VoxCeleb1 ID'].unique()).tolist()
        test_speaker_ids = (test_pandaframe['VoxCeleb1 ID'].unique()).tolist()
        complete_list_ids = train_speaker_ids + test_speaker_ids

        speaker_id_to_index = {}
        speaker_index_to_id = {}
        for idx, speaker_id in enumerate(complete_list_ids):
            speaker_id_to_index[speaker_id] = idx
            speaker_index_to_id[idx] = speaker_id
    
        return speaker_id_to_index, speaker_index_to_id

