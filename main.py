import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pynput import keyboard

from recorder import MouseRecorder
from player import MacroPlayer

HOTKEY_RECORD = "<f9>"
HOTKEY_PLAY   = "<f10>"


class MacroApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("マウスマクロ")
        self.resizable(False, False)
        self.attributes("-topmost", True)

        self._recorder = MouseRecorder()
        self._player = MacroPlayer()
        self._player.on_finish = self._on_playback_finish
        self._macro = []

        self._build_ui()
        self._start_hotkeys()
        self._update_status("待機中")

    def _build_ui(self):
        pad = {"padx": 8, "pady": 6}

        # --- Record controls ---
        rec_frame = tk.LabelFrame(self, text="記録", **pad)
        rec_frame.pack(fill="x", padx=10, pady=(10, 4))

        self._btn_start = tk.Button(
            rec_frame, text="● 記録開始", width=14, command=self._start_recording
        )
        self._btn_start.grid(row=0, column=0, **pad)

        self._btn_stop_rec = tk.Button(
            rec_frame, text="■ 記録停止", width=14, state="disabled",
            command=self._stop_recording
        )
        self._btn_stop_rec.grid(row=0, column=1, **pad)

        # --- Playback controls ---
        play_frame = tk.LabelFrame(self, text="再生", **pad)
        play_frame.pack(fill="x", padx=10, pady=4)

        self._btn_play = tk.Button(
            play_frame, text="▶ 再生", width=14, state="disabled",
            command=self._start_playback
        )
        self._btn_play.grid(row=0, column=0, **pad)

        self._btn_stop_play = tk.Button(
            play_frame, text="⏹ 停止", width=14, state="disabled",
            command=self._stop_playback
        )
        self._btn_stop_play.grid(row=0, column=1, **pad)

        repeat_label = tk.Label(play_frame, text="繰り返し:")
        repeat_label.grid(row=1, column=0, sticky="e", padx=(8, 2), pady=4)

        self._spin_repeat = tk.Spinbox(play_frame, from_=1, to=999, width=5)
        self._spin_repeat.grid(row=1, column=1, sticky="w", padx=(2, 8), pady=4)

        speed_label = tk.Label(play_frame, text="速度:")
        speed_label.grid(row=2, column=0, sticky="e", padx=(8, 2), pady=4)

        self._speed_var = tk.StringVar(value="1.0")
        speed_combo = ttk.Combobox(
            play_frame, textvariable=self._speed_var, width=6,
            values=["0.5", "1.0", "1.5", "2.0"], state="readonly"
        )
        speed_combo.grid(row=2, column=1, sticky="w", padx=(2, 8), pady=4)

        # --- Save / Load ---
        file_frame = tk.LabelFrame(self, text="ファイル", **pad)
        file_frame.pack(fill="x", padx=10, pady=4)

        self._btn_save = tk.Button(
            file_frame, text="💾 保存", width=14, state="disabled",
            command=self._save_macro
        )
        self._btn_save.grid(row=0, column=0, **pad)

        self._btn_load = tk.Button(
            file_frame, text="📂 読み込み", width=14, command=self._load_macro
        )
        self._btn_load.grid(row=0, column=1, **pad)

        # --- Hotkey hint ---
        hint = tk.Label(self, text="F9: 記録開始/停止　F10: 再生/停止", fg="gray", font=("", 8))
        hint.pack(pady=(0, 2))

        # --- Status bar ---
        status_frame = tk.Frame(self, relief="sunken", bd=1)
        status_frame.pack(fill="x", padx=10, pady=(0, 10))

        self._lbl_status = tk.Label(status_frame, text="", anchor="w")
        self._lbl_status.pack(side="left", padx=6)

        self._lbl_count = tk.Label(status_frame, text="イベント数: 0", anchor="e")
        self._lbl_count.pack(side="right", padx=6)

    # ------------------------------------------------------------------
    # Recording
    # ------------------------------------------------------------------

    def _start_recording(self):
        self._btn_start.config(state="disabled")
        self._btn_stop_rec.config(state="normal")
        self._btn_play.config(state="disabled")
        self._btn_save.config(state="disabled")
        self._btn_start.config(bg="#e74c3c", fg="white")
        self._recorder.start()
        self._update_status("記録中...")
        self._poll_count()

    def _stop_recording(self):
        self._recorder.stop()
        self._macro = list(self._recorder.events)
        self._btn_start.config(state="normal", bg="SystemButtonFace", fg="black")
        self._btn_stop_rec.config(state="disabled")
        has_data = len(self._macro) > 0
        self._btn_play.config(state="normal" if has_data else "disabled")
        self._btn_save.config(state="normal" if has_data else "disabled")
        self._lbl_count.config(text=f"イベント数: {len(self._macro)}")
        self._update_status(f"記録完了 ({len(self._macro)} イベント)")

    def _poll_count(self):
        if self._recorder._recording:
            self._lbl_count.config(text=f"イベント数: {self._recorder.event_count}")
            self.after(200, self._poll_count)

    # ------------------------------------------------------------------
    # Playback
    # ------------------------------------------------------------------

    def _start_playback(self):
        if not self._macro:
            return
        repeat = int(self._spin_repeat.get())
        speed = float(self._speed_var.get())
        self._btn_play.config(state="disabled")
        self._btn_start.config(state="disabled")
        self._btn_stop_play.config(state="normal")
        self._update_status(f"再生中... (×{repeat}, {speed}x)")
        self._player.play(self._macro, repeat=repeat, speed=speed)

    def _stop_playback(self):
        self._player.stop()
        self._reset_playback_ui()
        self._update_status("再生停止")

    def _on_playback_finish(self):
        self.after(0, self._reset_playback_ui)
        self.after(0, lambda: self._update_status("再生完了"))

    def _reset_playback_ui(self):
        self._btn_play.config(state="normal")
        self._btn_start.config(state="normal")
        self._btn_stop_play.config(state="disabled")

    # ------------------------------------------------------------------
    # File I/O
    # ------------------------------------------------------------------

    def _save_macro(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._macro, f, ensure_ascii=False, indent=2)
            self._update_status(f"保存: {path}")

    def _load_macro(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if path:
            with open(path, "r", encoding="utf-8") as f:
                self._macro = json.load(f)
            self._lbl_count.config(text=f"イベント数: {len(self._macro)}")
            self._btn_play.config(state="normal")
            self._btn_save.config(state="normal")
            self._update_status(f"読み込み完了: {len(self._macro)} イベント")

    # ------------------------------------------------------------------
    # Hotkeys
    # ------------------------------------------------------------------

    def _start_hotkeys(self):
        self._hotkey_listener = keyboard.GlobalHotKeys({
            HOTKEY_RECORD: self._hotkey_record,
            HOTKEY_PLAY:   self._hotkey_play,
        })
        self._hotkey_listener.start()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _hotkey_record(self):
        if self._recorder._recording:
            self.after(0, self._stop_recording)
        elif self._btn_start["state"] == "normal":
            self.after(0, self._start_recording)

    def _hotkey_play(self):
        if self._player.is_playing():
            self.after(0, self._stop_playback)
        elif self._btn_play["state"] == "normal":
            self.after(0, self._start_playback)

    def _on_close(self):
        self._hotkey_listener.stop()
        self.destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _update_status(self, text):
        self._lbl_status.config(text=f"状態: {text}")


if __name__ == "__main__":
    app = MacroApp()
    app.mainloop()
