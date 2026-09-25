import sys
import time
import threading
import ctypes
import tkinter as tk
from tkinter import BOTH, Canvas, Frame, Label, Menu, font
import obspython as obs


class AppState:
    def __init__(self):
        self.is_recording = False
        self.is_paused = False
        self.should_exit = False
        self.timer_enabled = True


state = AppState()
app_thread = None


class IndicatorApp(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.master = master
        self.config(bg="#1a1a1a")
        self.pack()

        self.start_time = 0
        self.accumulated_time = 0
        self.timer_running = False

        self.win_opacity = 0.8
        self.master.attributes("-alpha", 0.0)
        self.master.configure(bg="#0f0f0f")
        self.master.overrideredirect(1)
        self.master.attributes("-topmost", True)
        self.master.attributes("-transparentcolor", "#0f0f0f")
        self.config(bg="#0f0f0f")

        if sys.platform == "win32":
            try:
                self.master.update()
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.master.winfo_id())
                user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            except Exception as e:
                print(f"[Indicator] Failed to set window affinity: {e}")

        self.update_position()

        self.container = Frame(
            self,
            bg="#252525",
            bd=0,
            highlightthickness=1,
            highlightbackground="#404040",
        )
        self.container.pack(padx=5, pady=5, fill=BOTH, expand=True)

        self.canvas = Canvas(
            self.container, height=30, width=30, bg="#252525", highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, padx=(10, 5), pady=5)
        self.canvas.bind("<Button-1>", self.toggle_pause)

        font_style = font.Font(size=int(11 * self.scale), weight="bold")
        self.stopwatch_label = Label(
            self.container, text="00:00:00", font=font_style, bg="#252525", fg="#ffffff"
        )
        self.stopwatch_label.grid(row=0, column=1, padx=(0, 15), pady=5, sticky="ew")

        self.popup_menu = Menu(self, tearoff=False)
        self.popup_menu.add_command(label="Pause Recording", command=self.toggle_pause)
        self.popup_menu.add_command(label="Stop Recording", command=self.stop_recording)
        self.popup_menu.add_separator()
        self.popup_menu.add_command(
            label="Reset Window Location", command=self.update_position
        )

        self.master.bind("<Button-3>", self.show_menu)
        self.master.bind("<Button-1>", self.on_click)
        self.master.bind("<B1-Motion>", self.on_drag)
        self.master.bind("<ButtonRelease-1>", self.on_release)

        self.last_x = 0
        self.last_y = 0

        self.check_state_loop()
        self.update_timer_loop()

    def update_position(self):
        screen_w = self.master.winfo_screenwidth()
        w = max(300, min(500, int(screen_w * 0.20)))
        h = max(150, int(w * 0.20))
        x = (screen_w - w) // 2
        y = 20
        self.scale = max(1.0, screen_w / 1920)
        self.master.geometry(f"{w}x{h}+{x}+{y}")
        self.master.update_idletasks()

    def on_click(self, event):
        self.last_x = event.x
        self.last_y = event.y

    def on_drag(self, event):
        x = event.x - self.last_x + self.master.winfo_x()
        y = event.y - self.last_y + self.master.winfo_y()
        self.master.geometry(f"+{x}+{y}")

    def on_release(self, event):
        screen_w = self.master.winfo_screenwidth()
        screen_h = self.master.winfo_screenheight()
        win_w = self.master.winfo_width()
        win_h = self.master.winfo_height()

        new_x = max(0, min(self.master.winfo_x(), screen_w - win_w))
        new_y = max(0, min(self.master.winfo_y(), screen_h - win_h))
        self.master.geometry(f"+{new_x}+{new_y}")

    def show_menu(self, event):
        self.popup_menu.tk_popup(event.x_root, event.y_root)

    def toggle_pause(self, event=None):
        if state.is_paused:
            obs.obs_frontend_recording_pause(False)
        else:
            obs.obs_frontend_recording_pause(True)

    def stop_recording(self):
        obs.obs_frontend_recording_stop()

    def check_state_loop(self):
        if state.should_exit:
            self.master.destroy()
            return

        if state.is_recording:
            self.master.attributes("-alpha", self.win_opacity)
            self.canvas.delete("all")

            if state.is_paused:
                self.canvas.create_rectangle(5, 5, 10, 25, fill="#f8a63d", outline="")
                self.canvas.create_rectangle(15, 5, 20, 25, fill="#f8a63d", outline="")
                self.popup_menu.entryconfig(0, label="Unpause Recording")

                if self.timer_running:
                    self.accumulated_time += time.time() - self.start_time
                    self.timer_running = False
            else:
                self.canvas.create_oval(5, 5, 25, 25, fill="red", outline="")
                self.popup_menu.entryconfig(0, label="Pause Recording")

                if not self.timer_running:
                    self.start_time = time.time()
                    self.timer_running = True
        else:
            self.master.attributes("-alpha", 0.0)
            self.timer_running = False
            self.accumulated_time = 0
            self.stopwatch_label.config(text="00:00:00")

        if state.timer_enabled:
            self.stopwatch_label.grid()
        else:
            self.stopwatch_label.grid_remove()

        self.after(200, self.check_state_loop)

    def update_timer_loop(self):
        if state.should_exit:
            return

        if self.timer_running and state.timer_enabled:
            elapsed = int(time.time() - self.start_time + self.accumulated_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.stopwatch_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

        self.after(1000, self.update_timer_loop)


def run_tkinter():
    root = tk.Tk()
    root.title("OBS Recording Indicator")
    app = IndicatorApp(master=root)
    app.mainloop()


def frontend_event_handler(event):
    if event == obs.OBS_FRONTEND_EVENT_RECORDING_STARTING:
        state.is_recording = True
        state.is_paused = False
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        state.is_recording = False
        state.is_paused = False
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED:
        state.is_paused = True
    elif event == obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED:
        state.is_paused = False


def script_load(settings):
    global app_thread
    state.should_exit = False
    if app_thread is None or not app_thread.is_alive():
        app_thread = threading.Thread(target=run_tkinter, daemon=True)
        app_thread.start()


def script_unload():
    state.should_exit = True


def script_update(settings):
    state.timer_enabled = obs.obs_data_get_bool(settings, "timer_bool")


def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_bool(props, "timer_bool", "Enable Timer")
    return props


def script_description():
    return """
    <h2><font color="white">Recording Indicator</font></h2>
    <p>Recording Indicator For Your OBS Studio</p>
    <hr>

    <p style="font-size: 14px; margin-top: 10px;">
        <img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgd2lkdGg9IjEwMjQiCiAgIGhlaWdodD0iMTAyNCIKICAgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIKICAgZmlsbD0ibm9uZSIKICAgdmVyc2lvbj0iMS4xIgogICBpZD0ic3ZnODM1IgogICBzb2RpcG9kaTpkb2NuYW1lPSJPY3RpY29ucy1tYXJrLWdpdGh1Yi5zdmciCiAgIGlua3NjYXBlOnZlcnNpb249IjEuMC4yIChlODZjODcwOCwgMjAyMS0wMS0xNSkiPgogIDxtZXRhZGF0YQogICAgIGlkPSJtZXRhZGF0YTg0MSI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczgzOSIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjE0NDAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iNzk4IgogICAgIGlkPSJuYW1lZHZpZXc4MzciCiAgICAgc2hvd2dyaWQ9ImZhbHNlIgogICAgIGlua3NjYXBlOnpvb209IjAuNjA0NDkyMTkiCiAgICAgaW5rc2NhcGU6Y3g9IjUxMiIKICAgICBpbmtzY2FwZTpjeT0iNTEyIgogICAgIGlua3NjYXBlOndpbmRvdy14PSIwIgogICAgIGlua3NjYXBlOndpbmRvdy15PSIyNSIKICAgICBpbmtzY2FwZTp3aW5kb3ctbWF4aW1pemVkPSIwIgogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzgzNSIgLz4KICA8cGF0aAogICAgIGZpbGwtcnVsZT0iZXZlbm9kZCIKICAgICBjbGlwLXJ1bGU9ImV2ZW5vZGQiCiAgICAgZD0iTTggMEMzLjU4IDAgMCAzLjU4IDAgOEMwIDExLjU0IDIuMjkgMTQuNTMgNS40NyAxNS41OUM1Ljg3IDE1LjY2IDYuMDIgMTUuNDIgNi4wMiAxNS4yMUM2LjAyIDE1LjAyIDYuMDEgMTQuMzkgNi4wMSAxMy43MkM0IDE0LjA5IDMuNDggMTMuMjMgMy4zMiAxMi43OEMzLjIzIDEyLjU1IDIuODQgMTEuODQgMi41IDExLjY1QzIuMjIgMTEuNSAxLjgyIDExLjEzIDIuNDkgMTEuMTJDMy4xMiAxMS4xMSAzLjU3IDExLjcgMy43MiAxMS45NEM0LjQ0IDEzLjE1IDUuNTkgMTIuODEgNi4wNSAxMi42QzYuMTIgMTIuMDggNi4zMyAxMS43MyA2LjU2IDExLjUzQzQuNzggMTEuMzMgMi45MiAxMC42NCAyLjkyIDcuNThDMi45MiA2LjcxIDMuMjMgNS45OSAzLjc0IDUuNDNDMy42NiA1LjIzIDMuMzggNC40MSAzLjgyIDMuMzFDMy44MiAzLjMxIDQuNDkgMy4xIDYuMDIgNC4xM0M2LjY2IDMuOTUgNy4zNCAzLjg2IDguMDIgMy44NkM4LjcgMy44NiA5LjM4IDMuOTUgMTAuMDIgNC4xM0MxMS41NSAzLjA5IDEyLjIyIDMuMzEgMTIuMjIgMy4zMUMxMi42NiA0LjQxIDEyLjM4IDUuMjMgMTIuMyA1LjQzQzEyLjgxIDUuOTkgMTMuMTIgNi43IDEzLjEyIDcuNThDMTMuMTIgMTAuNjUgMTEuMjUgMTEuMzMgOS40NyAxMS41M0M5Ljc2IDExLjc4IDEwLjAxIDEyLjI2IDEwLjAxIDEzLjAxQzEwLjAxIDE0LjA4IDEwIDE0Ljk0IDEwIDE1LjIxQzEwIDE1LjQyIDEwLjE1IDE1LjY3IDEwLjU1IDE1LjU5QzEzLjcxIDE0LjUzIDE2IDExLjUzIDE2IDhDMTYgMy41OCAxMi40MiAwIDggMFoiCiAgICAgdHJhbnNmb3JtPSJzY2FsZSg2NCkiCiAgICAgZmlsbD0iIzFCMUYyMyIKICAgICBpZD0icGF0aDgzMyIKICAgICBzdHlsZT0iZmlsbDojZmZmZmZmO2ZpbGwtb3BhY2l0eToxIiAvPgo8L3N2Zz4K" width="16" height="16" style="vertical-align: middle;"/>
       <a href="https://github.com/channel101/obs_recording_indicator" style="color: #1E90FF; text-decoration: none; font-weight: bold; margin-left: 5px;">GitHub Repository</a>
    </p>
    """


obs.obs_frontend_add_event_callback(frontend_event_handler)
