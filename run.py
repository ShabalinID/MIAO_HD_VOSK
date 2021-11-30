#!/usr/bin/env python3
from vosk import Model, KaldiRecognizer
import wave
import json
import time
import os
import argparse


class daemon:
    def __init__(self):
        self.getConfig()
        self.modelInit()
        self.dirInit()


    def getConfig(self):



    def modelInit(self):
        parser = argparse.ArgumentParser(description="voice recognition daemon")
        parser.add_argument("lang", type=str, help='Language for recognizer')
        args = parser.parse_args()
        model_path = self.py_path + "models/" + args.lang
        model = Model(model_path)
        return model

    def dirInit(self):
        os.makedirs(self.input_file_path, exist_ok=True)
        os.makedirs(self.output_text_path, exist_ok=True)

py_path = ""

WAV_RATE = 16000
DAEMON_RESPONSE_FREQUENCY = 0.3  # seconds

global_path = ""

input_file_path = global_path + "webaudio/"
output_text_path = global_path + "texts/"

rec = KaldiRecognizer(model, WAV_RATE)



def recognizer_daemon():
    filenames = get_new_files()
    for filename in filenames:
        wav_file = fileToWav(filename)
        text = read_wav(wav_file)
        write_transcript(wav_file, text)
        delete_recognized_wav(wav_file)


def fileToWav(filename):
    input_file = filename
    output_file = os.path.splitext(filename)[0] + ".wav"
    # using ffmpeg app for convert all audio file for .wav with rate=16000 and mono
    ffmpeg_command = "ffmpeg -hide_banner -loglevel error -i {input_file} -y -ac 1 -ar {sample_rate} {output_file}"\
        .format(input_file=input_file_path + input_file, sample_rate=WAV_RATE, output_file=input_file_path + output_file)
    os.system(ffmpeg_command)
    os.remove(input_file_path + input_file)
    return output_file


def get_new_files():
    files = os.listdir(input_file_path)
    return files


def read_wav(filename):
    with open(input_file_path + filename, "rb") as wf:
        wf.read(44)  # skip wav header
        recognized_words = []

        while True:
            data = wf.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                recognized_words.append(res['text'])

        res = json.loads(rec.FinalResult())
        recognized_words.append(res['text'])
        text = ' '.join(recognized_words)
        return text


def write_transcript(filename, text):
    print(text)
    with open(output_text_path + os.path.splitext(filename)[0] + '.txt', 'w') as transcript:
        transcript.write(text)


def delete_recognized_wav(filename):
    os.remove(input_file_path + filename)


if __name__ == '__main__':
    model = modelInit()
    print("The daemon has been successfully launched!")
    try:
        while True:
            recognizer_daemon()
            time.sleep(DAEMON_RESPONSE_FREQUENCY)

    except FileNotFoundError:
        print("No files to recognize!")
        with open(output_text_path, 'w') as result:
            result.write('')

    except wave.Error:
        print(wave.Error)

    finally:
        print("Daemon was interrupted for some reasons. "
              "All wavs and texts files will be immediate deleted for this session!")
#        shutil.rmtree(wavs_path)
#        shutil.rmtree(text_path)
