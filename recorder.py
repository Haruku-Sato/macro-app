import time
import threading
from pynput import mouse


class MouseRecorder:
    def __init__(self):
        self.events = []
        self._listener = None
        self._recording = False
        self._start_time = None

    def start(self):
        self.events = []
        self._recording = True
        self._start_time = time.time()
        self._listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._listener.start()

    def stop(self):
        self._recording = False
        if self._listener:
            self._listener.stop()
            self._listener = None

    def _timestamp(self):
        return time.time() - self._start_time

    def _on_move(self, x, y):
        if self._recording:
            self.events.append({"time": self._timestamp(), "x": x, "y": y, "type": "move"})

    def _on_click(self, x, y, button, pressed):
        if self._recording:
            self.events.append({
                "time": self._timestamp(),
                "x": x,
                "y": y,
                "type": "click",
                "button": button.name,
                "pressed": pressed,
            })

    def _on_scroll(self, x, y, dx, dy):
        if self._recording:
            self.events.append({
                "time": self._timestamp(),
                "x": x,
                "y": y,
                "type": "scroll",
                "dx": dx,
                "dy": dy,
            })

    @property
    def event_count(self):
        return len(self.events)
