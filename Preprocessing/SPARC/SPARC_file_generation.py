import os
from pathlib import Path
import pandas as pd
import wave
import contextlib
import numpy as np
from shutil import copyfile
import os

class SPARC_file_generation():

    def __init__(self, audio_folder_path):
        self.audio_folder_path = audio_folder_path

    def create_folder_structure(self, target_path):
        SPARC_dataset = target_path
        meta_folder = "{}/metadata".format(SPARC_dataset)
        docs_folder = "{}/docs".format(SPARC_dataset)
        if not os.path.exists(SPARC_dataset):
            os.mkdir(SPARC_dataset)
        if not os.path.exists(meta_folder):
            os.mkdir(meta_folder)
        if not os.path.exists(docs_folder):
            os.mkdir(docs_folder)

    def make_pandaframe_from_list_of_audio_files(self):
        audio_files = self.__get_list_of_all_files__()
        list_of_audio_file_properties = []
        for audio_file in audio_files:
            file_properties = audio_file.split('_')
            list_of_audio_file_properties.append([file_properties[0][:-1], file_properties[0][-1:], file_properties[1], file_properties[2][-1:], file_properties[3], file_properties[4]])
        pframe_audio_file_properties = pd.DataFrame(list_of_audio_file_properties, columns = ['subject_id', 'sex', 'channel', 'session_id', 'language', 'utterance'])
        offset_for_six_digits_id = 100000
        pframe_audio_file_properties.insert(0, 'utterance_id',range(offset_for_six_digits_id, len(pframe_audio_file_properties) + offset_for_six_digits_id))
        return pframe_audio_file_properties

    def __get_list_of_all_files__(self):
        path_to_root = Path(self.audio_folder_path)
        file_list_full_path = [f for f in path_to_root.glob('**/*') if f.is_file()]
        file_list = []
        for file in file_list_full_path:
            file_list.append(os.path.basename(file)[:-4])
        return file_list

    def __create_list_of_segments__(self, pframe_audio_files):
        list_of_segments = []
        for index, row in pframe_audio_files.iterrows():
            list_of_segments.append("{}{}_{}_session{}_{}_{}".format(row['subject_id'], row['sex'], row['channel'], row['session_id'], row['language'], row['utterance']))
        return list_of_segments

    def create_language_tsv(self, pframe_audio_files, destination_folder):
        list_of_languages = pframe_audio_files['language'].unique()
        pframe_languages_full = pd.DataFrame(list_of_languages, columns = ['language'])
        pframe_languages_full.to_csv("{}/metadata/languages.tsv".format(destination_folder), sep = '\t')

    # def create_subjects_tsv(self, destination_folder):
    #     list_of_subjects_folders = [f for f in os.listdir(audio_parent_folder)]
    #     list_of_subjects_with_gender = []
    #     for subject_and_gender in list_of_subjects_folders:
    #         subject_id = subject_and_gender[:4]
    #         subject_gender = subject_and_gender[-1:]
    #         list_of_subjects_with_gender.append([subject_id, subject_gender])
    #     pframe_subjects_with_gender = pd.DataFrame(list_of_subjects_with_gender, columns = ['subject_id', 'sex'])
    #     pframe_subjects_with_gender.to_csv("{}/metadata/subjects.tsv".format(destination_folder), sep = '\t')

    def create_subject_and_sex_tsv(self, pframe_audio_files, destination_folder):
        subject_and_sex = pframe_audio_files[['subject_id', 'sex']]
        pframe_subject_and_sex = pd.DataFrame(subject_and_sex.drop_duplicates(subset='subject_id'))
        pframe_subject_and_sex = pframe_subject_and_sex.reset_index(drop=True)
        pframe_subject_and_sex.to_csv("{}/metadata/subjects.tsv".format(destination_folder), sep = '\t')

    def create_utterances_tsv(self, pframe_audio_files, destination_folder):
        pframe_subject_utterance_language_channel = pframe_audio_files[['subject_id', 'channel', 'session_id','language', 'utterance_id']]
        pframe_subject_utterance_language_channel.to_csv("{}/metadata/utterances.tsv".format(destination_folder), sep = '\t')

    def append_audio_length_to_pframe(self, audio_folder, pframe_audio_files):
        list_of_segments_paths = self.__create_list_of_segments__(pframe_audio_files)
        pframe_audio_files['segment'] = list_of_segments_paths
        list_of_audio_files_length = self.__get_list_of_audio_files_lengths__(audio_folder, pframe_audio_files)
        pframe_audio_files['segment_length'] = list_of_audio_files_length
        return pframe_audio_files

    def __get_list_of_audio_files_lengths__(self, audio_folder, pframe_audio_files):
        list_of_audio_files_lengths = []
        for index, row in pframe_audio_files.iterrows():
            segment = "{}{}_{}_session{}_{}_{}".format(row['subject_id'], row['sex'], row['channel'], row['session_id'], row['language'], row['utterance'])
            audio_length = self.__get_audio_length_of_file__(audio_folder, segment)
            list_of_audio_files_lengths.append(audio_length)
        return list_of_audio_files_lengths

    def __get_audio_length_of_file__(self, audio_folder, audio_file):
        audio_file_path = audio_file.replace("_","/")[:-2]
        path_to_file = "{}{}/{}.wav".format(audio_folder, audio_file_path, audio_file)
        with contextlib.closing(wave.open(path_to_file,'r')) as f:
            frames = f.getnframes()
            rate = f.getframerate()
            duration = frames / float(rate)
            return duration

    def split_data_into_enrollment_and_test(self, pframe_data, enrollment_language, test_language, channel_enroll, channel_test, enroll_session_id, test_session_id):
        if "modelid" not in pframe_data.columns:
            pframe_subjects = pframe_data['subject_id'].unique()
            modelids = self.__create_model_ids_from_pframe__(pframe_data, pframe_subjects)
            pframe_data.insert(0, 'modelid', modelids)
        pframe_enrollment = pframe_data.loc[(pframe_data['language'] == enrollment_language) & (pframe_data['session_id'] == enroll_session_id) & (pframe_data['channel'] == channel_enroll)]
        pframe_test = pframe_data.loc[(pframe_data['language'] == test_language) & (pframe_data['session_id'] == test_session_id) & (pframe_data['channel'] == channel_test)]
            # pframe_enrollment = []
            # pframe_test = []
        # if not use_all_languages:
        #     pframe_enrollment = pframe_data.loc[pframe_data['language'].isin(enrollment_languages)]
        #     pframe_test = pframe_data.loc[~pframe_data['language'].isin(enrollment_languages)]
        # else:
        #     pframe_enrollment = pframe_data.loc[pframe_data['utterance'].isin(["1", "2", "3"])]
        #     pframe_test = pframe_data.loc[~pframe_data['utterance'].isin(["1", "2", "3"])]
        return pframe_enrollment, pframe_test

    def __create_model_ids_from_pframe__(self, pframe_audio_files, pframe_subjects):
        model_ids = []
        offset_with_four_digits = 1000
        for index, row in pframe_audio_files.iterrows():
            index_of_subject = np.where(pframe_subjects == row['subject_id'])
            model_ids.append((index_of_subject[0][0] + offset_with_four_digits))
        return model_ids

    def create_eval_files(self, p_enrolment, pframe_test, destination_folder):
        pframe_enrollment_segment = p_enrolment[['utterance_id','segment', 'segment_length']]
        pframe_test_segment = pframe_test[['utterance_id','segment', 'segment_length']]
        joined_tables = [pframe_enrollment_segment, pframe_test_segment]

        pframe_segment_key = pd.concat(joined_tables)
        pframe_segment_key.to_csv("{}/docs/segment_key.tsv".format(destination_folder), sep = '\t', index=False)

        pframe_enrollment = pd.DataFrame(p_enrolment[['modelid', 'segment', 'channel']])
        pframe_enrollment.to_csv("{}/docs/enrollment.tsv".format(destination_folder), sep = '\t', index=False)

        pframe_enrollment_segment_key = pd.DataFrame(p_enrolment[['segment', 'utterance_id', 'channel', 'segment_length']])
        pframe_enrollment_segment_key.to_csv("{}/docs/enrollment_segment_key.tsv".format(destination_folder), sep = '\t', index=False)

        trial_key = self.__create_trial_key_table__(pframe_test)
        trial_key.to_csv("{}/docs/trial_key.tsv".format(destination_folder), sep = '\t', index=False)

    def __create_trial_key_table__(self, pframe):
        modelids = pframe['modelid'].unique()
        model_with_targettypes = []
        pframe = pframe[['modelid', 'segment', 'channel']]
        for modelid in modelids:
            model_targets = pd.DataFrame(pframe[pframe['modelid'].isin([modelid])])
            model_nontargets = pd.DataFrame(pframe[~pframe['modelid'].isin([modelid])])
            model_nontargets['modelid'] = modelid
            model_targets['targettype'] = 'target'
            model_nontargets['targettype'] = 'nontarget'
            model_with_targettypes.append(model_targets)
            model_with_targettypes.append(model_nontargets)
        trial_key_table = pd.concat(model_with_targettypes)
        return trial_key_table

    def copy_files_to_enrollment_and_test(self, enrollment, test, destination):
        parent_folder = "SPARC_data/audio_multilingual/"
        self.__copy_segment_from_source_to_destination__(parent_folder, enrollment['segment'], "{}/enrollment".format(destination))
        test_unique_files = test['segment'].unique()
        self.__copy_segment_from_source_to_destination__(parent_folder, test_unique_files, "{}/test".format(destination))


    def __copy_segment_from_source_to_destination__(self, parent_folder, segment_list, destination_folder):
        if not os.path.exists(destination_folder):
            os.mkdir(destination_folder)

        for segment in segment_list:
            folder_path = segment[:-1].replace("_","/")
            source_complete_file_path = "{}/{}{}.wav".format(parent_folder, folder_path, segment)
            destination = "{}/{}.wav".format(destination_folder, segment)
            copyfile(source_complete_file_path, destination)
