import os
from pathlib import Path
import pandas as pd
import wave
import contextlib
import numpy as np
from shutil import copyfile
import os

class SWAN_file_generation():

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
            language = self.__determine_language_from_site__(file_properties[0], file_properties[4])
            subject_id_with_site = "{}{}".format(file_properties[0], str(file_properties[1])[1::])
            list_of_audio_file_properties.append([file_properties[0], subject_id_with_site, file_properties[2], language, file_properties[3], file_properties[5], file_properties[4]])
        pframe_audio_file_properties = pd.DataFrame(list_of_audio_file_properties, columns = ['site', 'subject_id', 'sex', 'language', 'session_id', 'channel', 'utterance'])
        offset_for_six_digits_id = 100000
        pframe_audio_file_properties.insert(0, 'utterance_id',range(offset_for_six_digits_id, len(pframe_audio_file_properties) + offset_for_six_digits_id))
        return pframe_audio_file_properties

    def __determine_language_from_site__(self, site, recording_number):
        if(int(recording_number) > 4): return "English"
        elif(site == '1' or site == '2'): return "Norwegian"
        elif(site == '4'): return "French"
        elif(site == '5'): return "German"
        elif(site == '6'): return "Hindi"
        return "Unknown language"

    def __get_list_of_all_files__(self):
        path_to_root = Path(self.audio_folder_path)
        file_list_full_path = [f for f in path_to_root.glob('**/*.wav') if f.is_file()]
        file_list = []
        for file in file_list_full_path:
            file_list.append(os.path.basename(file)[:-4])
        return file_list

    def create_metadata_files(self, pframe_audio_files, destination_folder):
        self.__create_language_tsv__(pframe_audio_files, destination_folder)
        self.__create_subject_and_sex_tsv__(pframe_audio_files, destination_folder)
        self.__create_utterances_tsv__(pframe_audio_files, destination_folder)


    def __create_language_tsv__(self, pframe_audio_files, destination_folder):
        list_of_languages = pframe_audio_files['language'].unique()
        pframe_languages_full = pd.DataFrame(list_of_languages, columns = ['language'])
        pframe_languages_full.to_csv("{}/metadata/languages.tsv".format(destination_folder), sep = '\t')

    def __create_subject_and_sex_tsv__(self, pframe_audio_files, destination_folder):
        subject_and_sex = pframe_audio_files[['subject_id', 'sex']]
        pframe_subject_and_sex = pd.DataFrame(subject_and_sex.drop_duplicates(subset='subject_id'))
        pframe_subject_and_sex = pframe_subject_and_sex.reset_index(drop=True)
        pframe_subject_and_sex.to_csv("{}/metadata/subjects.tsv".format(destination_folder), sep = '\t')

    def __create_utterances_tsv__(self, pframe_audio_files, destination_folder):
        pframe_subject_utterance_language_channel = pframe_audio_files[['subject_id', 'channel', 'session_id','language', 'utterance_id']]
        pframe_subject_utterance_language_channel.to_csv("{}/metadata/utterances.tsv".format(destination_folder), sep = '\t')

    def append_audio_length_to_pframe(self, audio_folder, pframe_audio_files):
        list_of_segments_paths = self.__create_list_of_segments__(pframe_audio_files)
        pframe_audio_files['segment'] = list_of_segments_paths
        list_of_audio_files_length = self.__get_list_of_audio_files_lengths__(audio_folder, pframe_audio_files)
        pframe_audio_files['segment_length'] = list_of_audio_files_length
        return pframe_audio_files

    def __create_list_of_segments__(self, pframe_audio_files):
        list_of_segments = []
        for index, row in pframe_audio_files.iterrows():
            subject_id_without_site = "0{}".format(str(row['subject_id'])[1::])
            list_of_segments.append("{}_{}_{}_{}_{}_{}_2".format(row['site'], subject_id_without_site, row['sex'], row['session_id'], row['utterance'], row['channel']))
        return list_of_segments

    def __get_list_of_audio_files_lengths__(self, audio_folder, pframe_audio_files):
        list_of_audio_files_lengths = []
        for index, row in pframe_audio_files.iterrows():
            site = self.__get_site_from_index__(row['site'])
            channel = "iPhone" if row['channel'] == 'p' else "iPad"
            subject_id_without_site = "0{}".format(str(row['subject_id'])[1::])
            file_path = "{}/session_{}/{}/{}/{}".format(site, row['session_id'], channel, subject_id_without_site, str(row['segment']))
            audio_length = self.__get_audio_length_of_file__(audio_folder, file_path)
            list_of_audio_files_lengths.append(audio_length)
        return list_of_audio_files_lengths

    def __get_site_from_index__(self, site):
        if(site == '1'): return "NTNU"
        elif(site == '2'): return "UIO"
        elif(site == '4'): return "IDIAP"
        elif(site == '5'): return "HDA"
        elif(site == '6'): return "MPH-IND"

    def __get_audio_length_of_file__(self, audio_folder, audio_file):
        path_to_file = "{}/{}.wav".format(audio_folder, audio_file)
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

        pframe_enrollment = pframe_data.loc[(pframe_data['language'] == enrollment_language)  & (pframe_data['session_id'] == enroll_session_id) & (pframe_data['channel'] == channel_enroll)]
        pframe_test = pframe_data.loc[(pframe_data['language'] == test_language)  & (pframe_data['session_id'] == test_session_id) & (pframe_data['channel'] == channel_test)]

        # subject_ids_from_enrollment = pframe_enrollment['subject_id'].unique()
        # pframe_test_with_subjects_only_from_enrollment = pframe_test[pframe_test['subject_id'].isin(subject_ids_from_enrollment)]
        # subject_ids_from_test = pframe_test_with_subjects_only_from_enrollment['subject_id'].unique()
        # pframe_enroll_with_only_test_subjects = pframe_test_with_subjects_only_from_enrollment[pframe_test_with_subjects_only_from_enrollment['subject_id'].isin(subject_ids_from_test)]
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

        pframe_segment_key = pd.concat(joined_tables).drop_duplicates(subset='segment')
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
        parent_folder = self.audio_folder_path

        if not os.path.exists("{}/enrollment".format(destination)):
            os.mkdir("{}/enrollment".format(destination))

        if not os.path.exists("{}/test".format(destination)):
            os.mkdir("{}/test".format(destination))

        for index, row in enrollment.iterrows():
            site = self.__get_site_from_index__(row['site'])
            channel = "iPhone" if row['channel'] == 'p' else "iPad"
            subject_id_without_site = "0{}".format(str(row['subject_id'])[1::])
            file_path = "{}/session_{}/{}/{}/{}".format(site, row['session_id'], channel, subject_id_without_site, str(row['segment']))
            self.__copy_segment_from_source_to_destination__(parent_folder, file_path, "{}/enrollment".format(destination))

        for index, row in test.iterrows():
            site = self.__get_site_from_index__(row['site'])
            channel = "iPhone" if row['channel'] == 'p' else "iPad"
            subject_id_without_site = "0{}".format(str(row['subject_id'])[1::])
            file_path = "{}/session_{}/{}/{}/{}".format(site, row['session_id'], channel, subject_id_without_site, str(row['segment']))
            self.__copy_segment_from_source_to_destination__(parent_folder, file_path, "{}/test".format(destination))

    def __copy_segment_from_source_to_destination__(self, parent_folder, file_path, destination_folder):
        source_complete_file_path = "{}/{}.wav".format(parent_folder, file_path)
        segment_name = os.path.basename(source_complete_file_path)
        destination = "{}/{}".format(destination_folder, segment_name)
        copyfile(source_complete_file_path, destination)