import os
import tkinter as tk
from tkinter import messagebox, ttk
import requests
from bs4 import BeautifulSoup
from threading import Thread

class MusicDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("喜灰音乐POR下载器")
        self.root.geometry("700x500")

        # 创建搜索栏
        search_frame = tk.Frame(self.root)
        search_frame.pack(pady=10)
        tk.Label(search_frame, text="搜索音乐：").pack(side=tk.LEFT, padx=5)
        self.entry_search = tk.Entry(search_frame, width=40)
        self.entry_search.pack(side=tk.LEFT, padx=5)
        self.btn_search = tk.Button(search_frame, text="搜索", command=self.search_music)
        self.btn_search.pack(side=tk.LEFT)

        # 搜索结果列表
        self.tree = ttk.Treeview(self.root, columns=("name", "author", "duration", "download"), show="headings")
        self.tree.heading("name", text="歌曲名称")
        self.tree.heading("author", text="歌手")
        self.tree.heading("duration", text="时长")
        self.tree.heading("download", text="下载")
        self.tree.column("name", width=200)
        self.tree.column("author", width=150)
        self.tree.column("duration", width=80)
        self.tree.column("download", width=100)
        self.tree.pack(pady=10, fill=tk.BOTH, expand=True)

        # 下载按钮
        self.btn_download = tk.Button(self.root, text="下载选中歌曲", command=self.download_selected_music)
        self.btn_download.pack(pady=10)

        self.search_results = []  # 用于存储搜索结果

    def search_music(self):
        """根据关键词搜索音乐"""
        keyword = self.entry_search.get().strip()
        if not keyword:
            messagebox.showwarning("提示", "请输入搜索关键词呀！")
            return

        url = f"https://www.52gj.com/music?name={keyword}"

        def search_task():
            try:
                response = requests.get(url)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                # 清空结果列表
                self.search_results = []
                self.tree.delete(*self.tree.get_children())

                # 解析歌曲信息
                rows = soup.find_all("tr")
                for row in rows:
                    columns = row.find_all("td")
                    if len(columns) >= 4:  # 确保有完整的数据列
                        name = columns[0].text.strip()
                        author = columns[1].text.strip()
                        duration = columns[2].text.strip()
                        download_link = columns[3].find("a")["href"].strip()  # 获取下载链接
                        self.search_results.append((name, author, duration, download_link))
                        self.tree.insert("", tk.END, values=(name, author, duration, "点击下载"))

                if not self.search_results:
                    messagebox.showinfo("结果", "未找到任何音乐，请尝试其他关键词！")

            except Exception as e:
                messagebox.showerror("错误", f"搜索失败：{e}")

        # 使用线程防止界面卡顿
        Thread(target=search_task, daemon=True).start()

    def download_selected_music(self):
        """下载选中的音乐"""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("提示", "请先选择一首歌曲！")
            return

        index = self.tree.index(selected_item[0])  # 获取选中的索引
        music_data = self.search_results[index]
        music_name, _, _, download_url = music_data

        def download_task():
            try:
                response = requests.get(download_url, stream=True)
                response.raise_for_status()

                # 保存文件到本地
                save_path = os.path.join(os.getcwd(), f"{music_name}.mp3")
                with open(save_path, "wb") as file:
                    for chunk in response.iter_content(chunk_size=1024):
                        file.write(chunk)

                messagebox.showinfo("完成", f"音乐已下载到 {save_path}")
            except Exception as e:
                messagebox.showerror("错误", f"下载失败：{e}")

        # 使用线程进行下载
        Thread(target=download_task, daemon=True).start()

# 主程序入口
if __name__ == "__main__":
    root = tk.Tk()
    app = MusicDownloader(root)
    root.mainloop()
