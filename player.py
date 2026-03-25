import time
import threading
from pynput import mouse
from pynput.mouse import Button


class MacroPlayer:
    def __init__(self):
        self._controller = mouse.Controller()
        self._thread = None
        self._stop_flag = False
        self.on_finish = None  # callback when playback ends

    def play(self, events, repeat=1, speed=1.0):
        self._stop_flag = False
        self._thread = threading.Thread(
            target=self._run, args=(events, repeat, speed), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_flag = True

    def is_playing(self):
        return self._thread is not None and self._thread.is_alive()

    def _run(self, events, repeat, speed):
        if not events:
            if self.on_finish:
                self.on_finish()
            return

        for _ in range(repeat):
            if self._stop_flag:
                break
            prev_time = 0.0
            for event in events:
                if self._stop_flag:
                    break
                delay = (event["time"] - prev_time) / speed
                if delay > 0:
                    time.sleep(delay)
                prev_time = event["time"]
                self._dispatch(event)

        if self.on_finish:
            self.on_finish()

    def _dispatch(self, event):
        etype = event["type"]
        if etype == "move":
            self._controller.position = (event["x"], event["y"])
        elif etype == "click":
            self._controller.position = (event["x"], event["y"])
            btn = Button.left if event["button"] == "left" else Button.right
            if event["pressed"]:
                self._controller.press(btn)
            else:
                self._controller.release(btn)
        elif etype == "scroll":
            self._controller.position = (event["x"], event["y"])
            self._controller.scroll(event["dx"], event["dy"])
