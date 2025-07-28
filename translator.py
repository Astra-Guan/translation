import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from deep_translator import GoogleTranslator
import threading
import time
import platform


class CrossPlatformTranslator:
    def __init__(self, root):
        self.root = root
        self.system = platform.system()
        self.root.title("实时翻译助手")

        # 窗口大小设置
        if self.system == "Windows":
            self.root.geometry("1200x700")
            self.root.minsize(1000, 600)
        else:
            self.root.geometry("1300x750")
            self.root.minsize(1050, 650)

        # 字体设置
        self._setup_fonts()

        # 变量初始化
        self.last_input = ""
        self.translation_in_progress = False
        self.max_chars = 50000
        self.api_chunk_size = 4500

        # 创建UI
        self.create_widgets()
        self.configure_layout()

    def _setup_fonts(self):
        if self.system == "Windows":
            self.font = ('SimHei', 10)
            self.title_font = ('SimHei', 16, 'bold')
        elif self.system == "Darwin":
            self.font = ('Heiti TC', 12)
            self.title_font = ('Heiti TC', 16, 'bold')
        else:
            self.font = ('WenQuanYi Micro Hei', 10)
            self.title_font = ('WenQuanYi Micro Hei', 16, 'bold')

    def create_widgets(self):
        # 标题
        self.title_label = tk.Label(self.root, text="实时翻译助手", font=self.title_font)
        self.title_label.pack(pady=10)

        # 选项卡
        self.tab_control = ttk.Notebook(self.root)
        self.translate_tab = ttk.Frame(self.tab_control)
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.translate_tab, text="翻译")
        self.tab_control.add(self.settings_tab, text="设置")
        self.tab_control.pack(expand=1, fill="both", padx=10, pady=5)

        # 翻译选项卡 - 语言选择
        lang_frame = ttk.Frame(self.translate_tab)
        lang_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(lang_frame, text="源语言:", font=self.font).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.src_lang_var = tk.StringVar(value="auto")
        self.src_lang_combo = ttk.Combobox(lang_frame, textvariable=self.src_lang_var,
                                           values=["auto"] + sorted(["中文", "英语", "日语", "韩语", "法语", "德语",
                                                                     "西班牙语", "俄语", "印尼语"]), width=20)
        self.src_lang_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(lang_frame, text="目标语言:", font=self.font).grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.dest_lang_var = tk.StringVar(value="中文")
        self.dest_lang_combo = ttk.Combobox(lang_frame, textvariable=self.dest_lang_var,
                                            values=sorted(["中文", "英语", "日语", "韩语", "法语", "德语",
                                                           "西班牙语", "俄语", "印尼语"]), width=20)
        self.dest_lang_combo.grid(row=0, column=3, padx=5, pady=5, sticky="w")

        # 交换语言按钮
        self.swap_btn = ttk.Button(lang_frame, text="交换语言", command=self.swap_languages)
        self.swap_btn.grid(row=0, column=4, padx=10, pady=5)

        # 立即翻译按钮
        self.translate_now_btn = ttk.Button(lang_frame, text="立即翻译", command=self.perform_translation)
        self.translate_now_btn.grid(row=0, column=5, padx=10, pady=5)

        # 翻译选项卡 - 文本区域
        text_frame = ttk.Frame(self.translate_tab)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_columnconfigure(1, weight=1)
        text_frame.grid_rowconfigure(1, weight=1)

        # 源文本输入
        ttk.Label(text_frame, text="输入文本:", font=self.font).grid(row=0, column=0, sticky="w", pady=(0, 5),
                                                                     padx=(0, 5))
        self.src_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=self.font)
        self.src_text.grid(row=1, column=0, sticky="nsew", pady=(0, 5), padx=(0, 5))
        self.src_text.bind("<KeyRelease>", self.on_text_change)

        # 翻译结果
        ttk.Label(text_frame, text="翻译结果:", font=self.font).grid(row=0, column=1, sticky="w", pady=(0, 5),
                                                                     padx=(5, 0))
        self.dest_text = scrolledtext.ScrolledText(text_frame, wrap=tk.WORD, font=self.font)
        self.dest_text.grid(row=1, column=1, sticky="nsew", pady=(0, 5), padx=(5, 0))
        self.dest_text.config(state=tk.DISABLED)

        # 状态区域
        status_frame = ttk.Frame(text_frame)
        status_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
        status_frame.grid_columnconfigure(0, weight=1)

        self.char_count_var = tk.StringVar(value="字符数: 0/50000")
        self.char_count_label = ttk.Label(status_frame, textvariable=self.char_count_var, font=self.font)
        self.char_count_label.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(status_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=5)

        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = ttk.Label(self.translate_tab, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # 设置选项卡内容
        ttk.Label(self.settings_tab, text="翻译设置", font=self.title_font).pack(pady=10)
        settings_frame = ttk.LabelFrame(self.settings_tab, text="翻译选项")
        settings_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(settings_frame, text="自动翻译延迟 (秒):", font=self.font).grid(row=0, column=0, padx=5, pady=5,
                                                                                  sticky="w")
        self.delay_var = tk.DoubleVar(value=0.5)
        ttk.Scale(settings_frame, variable=self.delay_var, from_=0.1, to=2.0, orient=tk.HORIZONTAL, length=200).grid(
            row=0, column=1, padx=5, pady=5)
        self.delay_label = ttk.Label(settings_frame, text=f"{self.delay_var.get():.1f}秒", width=5)
        self.delay_label.grid(row=0, column=2, padx=5, pady=5)
        self.delay_var.trace_add("write", self.on_delay_change)

        ttk.Label(settings_frame, text="最大字符数:", font=self.font).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.max_chars_var = tk.IntVar(value=self.max_chars)
        ttk.Entry(settings_frame, textvariable=self.max_chars_var, width=10).grid(row=1, column=1, padx=5, pady=5,
                                                                                  sticky="w")
        ttk.Label(settings_frame, text="(重启应用生效)", font=self.font).grid(row=1, column=2, padx=5, pady=5,
                                                                              sticky="w")

        # 按钮框架
        btn_frame = ttk.Frame(self.settings_tab)
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.clear_btn = ttk.Button(btn_frame, text="清空所有文本", command=self.clear_text)
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.copy_btn = ttk.Button(btn_frame, text="复制翻译结果", command=self.copy_translation)
        self.copy_btn.pack(side=tk.LEFT, padx=5)

        if self.system == "Darwin":
            self.cancel_btn = ttk.Button(btn_frame, text="取消翻译", command=self.cancel_translation)
            self.cancel_btn.pack(side=tk.LEFT, padx=5)

    def configure_layout(self):
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def on_delay_change(self, *args):
        self.delay_label.config(text=f"{self.delay_var.get():.1f}秒")

    # 核心修复：交换语言和文本的逻辑
    def swap_languages(self):
        src_lang = self.src_lang_var.get()
        dest_lang = self.dest_lang_var.get()

        # 交换语言（特殊处理auto）
        if src_lang == "auto":
            # 源语言是auto时，直接将目标语言设为源语言，源语言保持auto
            self.src_lang_var.set(dest_lang)
        else:
            # 正常交换语言
            self.src_lang_var.set(dest_lang)
            self.dest_lang_var.set(src_lang)

        # 交换文本内容（无论是否有内容都尝试交换，空内容不影响）
        # 获取当前文本（去除首尾空白和自动添加的换行符）
        src_text = self.src_text.get(1.0, tk.END).rstrip('\n')
        dest_text = self.dest_text.get(1.0, tk.END).rstrip('\n')

        # 清空并交换文本
        self.src_text.delete(1.0, tk.END)
        self.src_text.insert(tk.END, dest_text)

        self.dest_text.config(state=tk.NORMAL)
        self.dest_text.delete(1.0, tk.END)
        self.dest_text.insert(tk.END, src_text)
        self.dest_text.config(state=tk.DISABLED)

        # 更新字符计数
        self.on_text_change()

    def clear_text(self):
        self.src_text.delete(1.0, tk.END)
        self.dest_text.config(state=tk.NORMAL)
        self.dest_text.delete(1.0, tk.END)
        self.dest_text.config(state=tk.DISABLED)
        self.status_var.set("就绪")
        self.progress_var.set(0)
        self.last_input = ""

    def copy_translation(self):
        translation = self.dest_text.get(1.0, tk.END).strip()
        if translation:
            self.root.clipboard_clear()
            self.root.clipboard_append(translation)
            self.status_var.set("翻译结果已复制到剪贴板")
        else:
            self.status_var.set("没有可复制的翻译结果")

    def cancel_translation(self):
        if self.translation_in_progress:
            self.translation_in_progress = False
            self.status_var.set("翻译已取消")

    def on_text_change(self, event=None):
        text = self.src_text.get(1.0, tk.END).strip()
        char_count = len(text)

        if char_count > self.max_chars:
            text = text[:self.max_chars]
            self.src_text.delete(1.0, tk.END)
            self.src_text.insert(tk.END, text)
            char_count = self.max_chars
            messagebox.showwarning("警告", f"已达到最大字符数限制 ({self.max_chars})")

        self.char_count_var.set(f"字符数: {char_count}/{self.max_chars}")

        if text != self.last_input:
            self.last_input = text
            self.status_var.set("输入中...")

            if hasattr(self, 'translation_timer'):
                self.root.after_cancel(self.translation_timer)

            self.translation_timer = self.root.after(int(self.delay_var.get() * 1000), self.perform_translation)

    def perform_translation(self):
        text = self.src_text.get(1.0, tk.END).strip()

        if not text or self.translation_in_progress:
            return

        self.translation_in_progress = True
        self.status_var.set("准备翻译...")
        self.progress_var.set(0)

        threading.Thread(target=self._translate_text, args=(text,)).start()

    def _split_text(self, text, chunk_size):
        chunks = []
        start = 0
        text_length = len(text)

        while start < text_length:
            end = min(start + chunk_size, text_length)

            if end < text_length:
                split_pos = text.rfind('\n', start, end)
                if split_pos == -1:
                    split_pos = text.rfind('.', start, end)
                if split_pos == -1:
                    split_pos = text.rfind(',', start, end)
                if split_pos != -1:
                    end = split_pos + 1

            chunks.append(text[start:end])
            start = end

        return chunks

    def _translate_text(self, text):
        max_retries = 3
        retry_delay = 2

        try:
            src_lang = self.src_lang_var.get()
            dest_lang = self.dest_lang_var.get()

            lang_map = {
                "中文": "zh-CN",
                "英语": "en",
                "日语": "ja",
                "韩语": "ko",
                "法语": "fr",
                "德语": "de",
                "西班牙语": "es",
                "俄语": "ru",
                "印尼语": "id",
                "auto": "auto"
            }

            src_code = lang_map.get(src_lang, "auto")
            dest_code = lang_map.get(dest_lang, "zh-CN")

            chunks = self._split_text(text, self.api_chunk_size)
            total_chunks = len(chunks)
            translated_chunks = []

            for i, chunk in enumerate(chunks):
                if not self.translation_in_progress:
                    break

                for attempt in range(max_retries):
                    try:
                        translator = GoogleTranslator(source=src_code, target=dest_code)
                        result = translator.translate(chunk)
                        translated_chunks.append(result)

                        progress = (i + 1) / total_chunks * 100
                        self.root.after(0, lambda p=progress: self.progress_var.set(p))
                        self.root.after(0, lambda i=i + 1, t=total_chunks:
                        self.status_var.set(f"翻译中: 片段 {i}/{t}"))
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise Exception(f"翻译片段 {i + 1} 失败: {str(e)}")
                        time.sleep(retry_delay)

            if self.translation_in_progress:
                full_translation = ''.join(translated_chunks)
                self.root.after(0, self._update_translation_result, full_translation)

        except Exception as e:
            self.root.after(0, self._update_translation_error, str(e))
        finally:
            self.translation_in_progress = False

    def _update_translation_result(self, translation):
        self.dest_text.config(state=tk.NORMAL)
        self.dest_text.delete(1.0, tk.END)
        self.dest_text.insert(tk.END, translation)
        self.dest_text.config(state=tk.DISABLED)
        self.status_var.set("翻译完成")
        self.progress_var.set(100)

    def _update_translation_error(self, error_msg):
        self.dest_text.config(state=tk.NORMAL)
        self.dest_text.delete(1.0, tk.END)
        self.dest_text.insert(tk.END, f"翻译出错: {error_msg}")
        self.dest_text.config(state=tk.DISABLED)
        self.status_var.set("翻译出错")


if __name__ == "__main__":
    if platform.system() == "Darwin":
        import matplotlib

        matplotlib.use('Agg')

    root = tk.Tk()
    app = CrossPlatformTranslator(root)
    root.mainloop()