import tkinter as tk
from tkinter import messagebox, filedialog
import sounddevice as sd
from scipy.io.wavfile import write
import threading
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
from pydub import AudioSegment, effects, silence
import pygame

class VoiceRecorderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 Voice Recorder - Enhanced")
        self.root.geometry("550x600")

        self.fs = 44100
        self.is_recording = False
        self.is_monitoring = False
        self.recorded_data = []
        self.start_time = None
        self.audio_filename = "temp_recording.wav"

        tk.Label(root, text="Voice Recorder", font=("Arial", 16)).pack(pady=10)
        self.duration_label = tk.Label(root, text="Duration: 0.0 s")
        self.duration_label.pack()

        self.start_button = tk.Button(root, text="Start Recording", command=self.start_recording)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Stop Recording", command=self.stop_recording, state=tk.DISABLED)
        self.stop_button.pack(pady=5)

        self.play_button = tk.Button(root, text="Play Recording", command=self.play_recording, state=tk.DISABLED)
        self.play_button.pack(pady=5)

        self.stop_play_button = tk.Button(root, text="Stop Playback", command=self.stop_playback, state=tk.DISABLED)
        self.stop_play_button.pack(pady=2)

        self.save_button = tk.Button(root, text="Save (WAV)", command=self.save_recording, state=tk.DISABLED)
        self.save_button.pack(pady=5)

        self.clean_button = tk.Button(root, text="Clean (Noise/Silence)", command=self.clean_audio, state=tk.DISABLED)
        self.clean_button.pack(pady=5)

        self.monitor_button = tk.Button(root, text="Start Mic Monitor", command=self.toggle_monitor)
        self.monitor_button.pack(pady=5)

        self.fig, self.ax = plt.subplots(figsize=(5, 2), dpi=100)
        self.ax.set_ylim([-1, 1])
        self.line, = self.ax.plot([], [], lw=1)
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=10)

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def start_recording(self):
        self.is_recording = True
        self.recorded_data = []
        self.start_time = time.time()
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.save_button.config(state=tk.DISABLED)
        self.play_button.config(state=tk.DISABLED)
        self.clean_button.config(state=tk.DISABLED)
        self.stop_play_button.config(state=tk.DISABLED)
        self.update_timer()
        threading.Thread(target=self.record).start()

    def record(self):
        def callback(indata, frames, time_info, status):
            if self.is_recording:
                self.recorded_data.append(indata.copy())
                self.update_plot(indata[:, 0])
            else:
                raise sd.CallbackStop

        with sd.InputStream(samplerate=self.fs, channels=1, callback=callback):
            sd.sleep(100000)

    def stop_recording(self):
        self.is_recording = False
        audio_data = np.concatenate(self.recorded_data, axis=0)
        write(self.audio_filename, self.fs, audio_data)
        self.duration_label.config(text="Recording stopped.")
        self.save_button.config(state=tk.NORMAL)
        self.play_button.config(state=tk.NORMAL)
        self.clean_button.config(state=tk.NORMAL)
        self.stop_play_button.config(state=tk.NORMAL)

        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        messagebox.showinfo("Done", "Recording completed and saved temporarily.")

    def play_recording(self):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(self.audio_filename)
            pygame.mixer.music.play()
            self.stop_play_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Playback Error", str(e))

    def stop_playback(self):
        try:
            pygame.mixer.music.stop()
        except:
            pass
        self.stop_play_button.config(state=tk.DISABLED)

    def save_recording(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".wav",
                                                 filetypes=[("WAV files", "*.wav")])
        if file_path:
            AudioSegment.from_wav(self.audio_filename).export(file_path, format="wav")
            messagebox.showinfo("Saved", f"Recording saved as:\n{file_path}")
            self.save_button.config(state=tk.DISABLED)

    def clean_audio(self):
        try:
            audio = AudioSegment.from_wav(self.audio_filename)
            normalized = effects.normalize(audio)
            trimmed = silence.strip_silence(normalized, silence_thresh=-40, padding=100)
            cleaned_path = self.audio_filename.replace(".wav", "_cleaned.wav")
            trimmed.export(cleaned_path, format="wav")
            self.audio_filename = cleaned_path
            messagebox.showinfo("Cleaned", "Silence removed and audio normalized.")
            self.play_button.config(state=tk.NORMAL)
        except Exception as e:
            messagebox.showerror("Cleaning Error", str(e))

    def toggle_monitor(self):
        if not self.is_monitoring:
            self.is_monitoring = True
            self.monitor_button.config(text="Stop Mic Monitor")
            threading.Thread(target=self.monitor_microphone).start()
        else:
            self.is_monitoring = False
            self.monitor_button.config(text="Start Mic Monitor")

    def monitor_microphone(self):
        def callback(indata, frames, time_info, status):
            if not self.is_monitoring:
                raise sd.CallbackStop
            sd.play(indata, self.fs)

        with sd.InputStream(samplerate=self.fs, channels=1, callback=callback):
            sd.sleep(100000)

    def update_timer(self):
        if self.is_recording:
            elapsed = round(time.time() - self.start_time, 1)
            self.duration_label.config(text=f"Duration: {elapsed} s")
            self.root.after(100, self.update_timer)

    def update_plot(self, data):
        self.line.set_ydata(data)
        self.line.set_xdata(np.arange(len(data)))
        self.ax.set_xlim(0, len(data))
        self.canvas.draw()

    def on_close(self):
        self.is_recording = False
        self.is_monitoring = False
        pygame.mixer.quit()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceRecorderGUI(root)
    root.mainloop()
