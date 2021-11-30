#!/usr/bin/env python3
from vosk import Model, KaldiRecognizer
import wave
import json
import time
import os
import argparse
import configparser


class Daemon:
    WAV_RATE = None
    PY_PATH = None
    GLOBAL_PATH = None
    OUTPUT_FILE_PATH = None
    INPUT_FILE_PATH = None

    def __init__(self):
        Daemon.getConfig()
        self.voice_model = self.makeVoiceModel()
        self.rec = self.makeRecognizer()
        self.dirInit()

    @classmethod
    def getConfig(cls):
        config = configparser.ConfigParser()
        config.read("config.ini")
        config_daemon = config['DAEMON']

        cls.WAV_RATE = int(config_daemon['WAV_RATE'])
        cls.SLEEP = float(config_daemon['DAEMON_RESPONSE_FREQUENCY'])
        cls.PY_PATH = config_daemon['PY_PATH']
        cls.GLOBAL_PATH = config_daemon['GLOBAL_PATH']
        cls.INPUT_FILE_PATH = Daemon.GLOBAL_PATH + config_daemon['INPUT_FILE_PATH']
        cls.OUTPUT_FILE_PATH = Daemon.GLOBAL_PATH + config_daemon['OUTPUT_FILE_PATH']

    @staticmethod
    def makeVoiceModel():
        parser = argparse.ArgumentParser(description="voice recognition daemon")
        parser.add_argument("lang", type=str, help='Language for recognizer')
        args = parser.parse_args()
        model_path = Daemon.PY_PATH + "models/" + args.lang
        voice_model = Model(model_path)
        return voice_model

    @staticmethod
    def dirInit():
        os.makedirs(Daemon.INPUT_FILE_PATH, exist_ok=True)
        os.makedirs(Daemon.OUTPUT_FILE_PATH, exist_ok=True)

    def makeRecognizer(self):
        rec = KaldiRecognizer(self.voice_model, Daemon.WAV_RATE)
        return rec

    def recognize(self):
        filenames = self.get_new_files()
        for filename in filenames:
            wav_file = self.fileToWav(filename)
            text = self.read_wav(wav_file)
            self.write_transcript(wav_file, text)
            self.delete_recognized_wav(wav_file)

    @staticmethod
    def fileToWav(filename):
        input_file = filename
        output_file = os.path.splitext(filename)[0] + ".wav"
        # using ffmpeg app for convert all audio file for .wav with rate=16000 and mono
        ffmpeg_command = "ffmpeg -hide_banner -loglevel error -i {input_file} -y -ac 1 -ar {sample_rate} {output_file}"\
            .format(input_file=Daemon.INPUT_FILE_PATH + input_file,
                    sample_rate=Daemon.WAV_RATE,
                    output_file=Daemon.INPUT_FILE_PATH + output_file)
        os.system(ffmpeg_command)
        os.remove(Daemon.INPUT_FILE_PATH + input_file)
        return output_file

    @staticmethod
    def get_new_files():
        files = os.listdir(Daemon.INPUT_FILE_PATH)
        return files

    def read_wav(self, filename):
        with open(Daemon.INPUT_FILE_PATH + filename, "rb") as wf:
            wf.read(44)  # skip wav header
            recognized_words = []

            while True:
                data = wf.read(4000)
                if len(data) == 0:
                    break
                if self.rec.AcceptWaveform(data):
                    res = json.loads(self.rec.Result())
                    recognized_words.append(res['text'])

            res = json.loads(self.rec.FinalResult())
            recognized_words.append(res['text'])
            text = ' '.join(recognized_words)
            return text

    @staticmethod
    def write_transcript(filename, text):
        print(text)
        with open(Daemon.OUTPUT_FILE_PATH + os.path.splitext(filename)[0] + '.txt', 'w') as transcript:
            transcript.write(text)

    @staticmethod
    def delete_recognized_wav(filename):
        os.remove(Daemon.INPUT_FILE_PATH + filename)


if __name__ == '__main__':
    daemon = Daemon()
    print("The daemon has been successfully launched!")
    try:
        while True:
            daemon.recognize()
            time.sleep(Daemon.SLEEP)

    except FileNotFoundError:
        print("No files to recognize!")

    except wave.Error:
        print(wave.Error)

    finally:
        print("Daemon was interrupted for some reasons. "
              "All wavs and texts files will be immediate deleted for this session!")
#        shutil.rmtree(wavs_path)
#        shutil.rmtree(text_path)
