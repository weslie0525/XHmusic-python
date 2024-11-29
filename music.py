import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pygame import mixer
from threading import Thread
import requests
from io import BytesIO
import zipfile
import time


class MusicPlayer:
    def __init__(self, root):
        self.root = root
        self.root.title("喜灰音乐播放器")
        self.root.geometry("600x500")
        self.music_folder = os.path.expanduser("~/Music")  # 默认音乐文件夹
        self.playlist = []
        self.current_index = -1
        self.current_music_length = 0
        self.is_playing = False

        # 初始化音频混音器
        mixer.init()

        # 创建UI组件
        self.create_widgets()

        # 加载默认音乐文件夹
        self.load_music_folder()

    def create_widgets(self):
        # 文件夹选择按钮
        frame_controls = tk.Frame(self.root)
        frame_controls.pack(pady=5, fill=tk.X)

        self.btn_select_folder = tk.Button(frame_controls, text="选择文件夹", command=self.select_folder, width=15)
        self.btn_select_folder.pack(side=tk.LEFT, padx=10)

        self.entry_link = tk.Entry(frame_controls, width=30)
        self.entry_link.pack(side=tk.LEFT, padx=10, expand=True)

        self.btn_download = tk.Button(frame_controls, text="从链接下载", command=self.download_from_link, width=15)
        self.btn_download.pack(side=tk.LEFT, padx=10)

        # 下载进度条
        self.progress_download = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_download.pack(pady=5)

        # 音乐列表
        self.music_listbox = tk.Listbox(self.root, selectmode=tk.SINGLE, width=60, height=15)
        self.music_listbox.pack(pady=10, fill=tk.BOTH, expand=True)
        self.music_listbox.bind("<<ListboxSelect>>", self.play_selected)

        # 播放进度时间显示
        self.time_label = tk.Label(self.root, text="00:00 / 00:00", font=("Arial", 12))
        self.time_label.pack(pady=5)

        # 播放进度条
        self.progress_music = ttk.Progressbar(self.root, orient=tk.HORIZONTAL, length=400, mode='determinate')
        self.progress_music.pack(pady=5)

        # 控制按钮
        control_frame = tk.Frame(self.root)
        control_frame.pack(pady=10)

        self.btn_prev = tk.Button(control_frame, text="上一首", command=self.play_previous, width=10)
        self.btn_prev.pack(side=tk.LEFT, padx=5)

        self.btn_play_pause = tk.Button(control_frame, text="播放", command=self.play_pause, width=10)
        self.btn_play_pause.pack(side=tk.LEFT, padx=5)

        self.btn_next = tk.Button(control_frame, text="下一首", command=self.play_next, width=10)
        self.btn_next.pack(side=tk.LEFT, padx=5)

    def load_music_folder(self):
        # 缓存音乐文件路径
        self.playlist = [os.path.join(self.music_folder, f) for f in os.listdir(self.music_folder) if f.endswith((".mp3", ".wav"))]
        self.update_playlist()

    def update_playlist(self):
        # 在UI中只显示文件名
        self.music_listbox.delete(0, tk.END)
        for music_path in self.playlist:
            self.music_listbox.insert(tk.END, os.path.basename(music_path))

    def select_folder(self):
        # 选择文件夹
        folder = filedialog.askdirectory()
        if folder:
            self.music_folder = folder
            self.load_music_folder()

    def play_selected(self, event=None):
        # 播放选中的音乐
        try:
            self.current_index = self.music_listbox.curselection()[0]
            self.play_music()
        except IndexError:
            pass

    def play_music(self):
        if self.current_index >= 0 and self.current_index < len(self.playlist):
            mixer.music.stop()
            music_path = self.playlist[self.current_index]

            # 加载音乐长度到缓存
            self.current_music_length = mixer.Sound(music_path).get_length()

            # 播放音乐
            mixer.music.load(music_path)
            mixer.music.play()
            self.is_playing = True
            self.btn_play_pause.config(text="暂停")

            # 更新播放时间和进度条
            Thread(target=self.update_playback_progress, daemon=True).start()

    def play_pause(self):
        if self.is_playing:
            mixer.music.pause()
            self.is_playing = False
            self.btn_play_pause.config(text="播放")
        else:
            mixer.music.unpause()
            self.is_playing = True
            self.btn_play_pause.config(text="暂停")

    def play_previous(self):
        if self.current_index > 0:
            self.current_index -= 1
            self.play_music()

    def play_next(self):
        if self.current_index < len(self.playlist) - 1:
            self.current_index += 1
            self.play_music()

    def update_playback_progress(self):
        while self.is_playing and mixer.music.get_busy():
            pos = mixer.music.get_pos() / 1000  # 当前播放时间（秒）

            # 更新UI进度条和时间
            self.progress_music["maximum"] = self.current_music_length
            self.progress_music["value"] = pos
            current_time = time.strftime("%M:%S", time.gmtime(pos))
            total_time = time.strftime("%M:%S", time.gmtime(self.current_music_length))
            self.time_label.config(text=f"{current_time} / {total_time}")

            # 每隔0.5秒更新一次
            time.sleep(0.5)

    def download_from_link(self):
        url = self.entry_link.get()
        if not url.startswith("https://"):
            messagebox.showerror("错误", "请输入有效的 HTTPS 链接！")
            return

        def download_task():
            try:
                response = requests.get(url, stream=True)
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                buffer = BytesIO()
                for chunk in response.iter_content(1024):
                    buffer.write(chunk)
                    downloaded_size += len(chunk)

                    # 每隔一定数据量更新UI，避免阻塞
                    if total_size > 0:
                        self.progress_download["value"] = (downloaded_size / total_size) * 100
                        self.root.update_idletasks()

                with zipfile.ZipFile(buffer) as zf:
                    zf.extractall(self.music_folder)

                self.load_music_folder()
                self.progress_download["value"] = 0
                messagebox.showinfo("完成", "下载并解压完成！")
            except Exception as e:
                messagebox.showerror("错误", f"下载失败: {e}")

        Thread(target=download_task, daemon=True).start()


# 主程序
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicPlayer(root)
    root.mainloop()
