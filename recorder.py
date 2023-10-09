import tkinter as tk
from tkinter import messagebox
from tkinter import Entry
import pyaudio
import os
import wave
from sys import byteorder
from array import array
from struct import pack

THRESHOLD = 500
CHUNK_SIZE = 1024
FORMAT = pyaudio.paInt16
RATE = 16000
SILENCE = 30

class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder")

        self.recording = False
        self.filename = ""
        self.p = pyaudio.PyAudio()

        self.record_button = tk.Button(root, text="Record", command=self.toggle_recording)
        self.record_button.pack(pady=20)

        self.filename_entry = Entry(root, width=40)
        self.filename_entry.insert(0, "test.wav")
        self.filename_entry.pack()

    def is_silent(self, snd_data):
        return max(snd_data) < THRESHOLD

    def normalize(self, snd_data):
        MAXIMUM = 16384
        times = float(MAXIMUM) / max(abs(i) for i in snd_data)
        r = array('h')
        for i in snd_data:
            r.append(int(i * times))
        return r

    def trim(self, snd_data):
        def _trim(snd_data):
            snd_started = False
            r = array('h')

            for i in snd_data:
                if not snd_started and abs(i) > THRESHOLD:
                    snd_started = True
                    r.append(i)

                elif snd_started:
                    r.append(i)
            return r

        snd_data = _trim(snd_data)
        snd_data.reverse()
        snd_data = _trim(snd_data)
        snd_data.reverse()
        return snd_data

    def add_silence(self, snd_data, seconds):
        r = array('h', [0 for i in range(int(seconds * RATE))])
        r.extend(snd_data)
        r.extend([0 for i in range(int(seconds * RATE))])
        return r

    def record_audio(self):
        self.recording = True
        self.record_button.config(text="Stop Recording")
        self.filename = self.filename_entry.get()

        stream = self.p.open(format=FORMAT, channels=1, rate=RATE, input=True, output=True,
                             frames_per_buffer=CHUNK_SIZE)

        num_silent = 0
        snd_started = False
        r = array('h')

        while self.recording:
            snd_data = array('h', stream.read(CHUNK_SIZE))
            if byteorder == 'big':
                snd_data.byteswap()
            r.extend(snd_data)

            silent = self.is_silent(snd_data)

            if silent and snd_started:
                num_silent += 1
            elif not silent and not snd_started:
                snd_started = True

            if snd_started and num_silent > SILENCE:
                break

        sample_width = self.p.get_sample_size(FORMAT)
        stream.stop_stream()
        stream.close()
        self.p.terminate()

        r = self.normalize(r)
        r = self.trim(r)
        r = self.add_silence(r, 0.5)

        data = pack('<' + ('h' * len(r)), *r)

        wf = wave.open(self.filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(sample_width)
        wf.setframerate(RATE)
        wf.writeframes(data)
        wf.close()

        self.recording = False
        self.record_button.config(text="Record")
        messagebox.showinfo("Info", f"Recording saved as {self.filename}")

    def toggle_recording(self):
        if not self.recording:
            self.record_audio()
        else:
            self.recording = False
            self.record_button.config(text="Record")

if __name__ == "__main__":
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()
