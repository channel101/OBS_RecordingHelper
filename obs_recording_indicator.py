import ctypes  
import tkinter as tk
from tkinter import BOTH, Canvas, Frame, Label, Menu, threading
import sys 
import obspython as obs

# --------------------------------------------------

lastClickX = 0
lastClickY = 0

clickReleaseX = 0
clickReleaseY = 0

window = None
is_paused = False

# ----------------------------------------------------------------------------------------

# ***** VARIABLES *****
# use a boolean variable to help control state of time (running or not running)
running = False
# time variables initially set to 0
hours, minutes, seconds = 0, 0, 0

# ***** Settings Variables *****
# whether to view total time pasted
timer_enable = True
# whether the recording is working or not for accessibility
status_text_enable = True

# ----------------------------------------------------------------------------------------

loop_destroy = False
window_start = False


class Application(tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.config(bg="#1a1a1a")
        self.pack()

        # Dynamic position based on config
        self.update_position()

        win_opacity = 0.8

        self.master.attributes("-alpha", 0.0)  # Start hidden
        self.master.configure(bg="#0f0f0f")  # Darker background
        self.master.overrideredirect(1)  # Borderless window
        self.master.attributes("-topmost", True)  # Always on top

        # Add rounded corners effect
        self.master.attributes("-transparentcolor", "#0f0f0f")
        self.config(bg="#0f0f0f")

        if sys.platform == "win32":
            try:
                self.master.update()
                WDA_EXCLUDEFROMCAPTURE = 0x00000011
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.master.winfo_id())
                user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            except Exception:
                pass

        self.master.attributes("-alpha", win_opacity) 
        container = Frame(
            self,
            bg="#252525",
            bd=0,
            highlightthickness=1,
            highlightbackground="#404040",
            highlightcolor="#404040",
        )
        container.pack(padx=5, pady=5, fill=BOTH, expand=True)

        font_size = int(11 * self.scale)

        # canvas for REC button
        self.canvas = Canvas(
            container,
            height=30,
            width=30,
            bg="#252525",
            highlightthickness=0,
        )
        self.canvas.grid(row=0, column=0, padx=(10, 5), pady=5)

        if timer_enable == True:
            # Label For Timer
            self.stopwatch_label = Label(
                container, text="00:00:00", font=("Segoe UI", font_size, "bold")
            )
            self.stopwatch_label.grid(row=0, column=1, padx=(0, 15), pady=5)
            self.stopwatch_label.config(bg="#252525", fg="#ffffff")

        if status_text_enable == True:
            # Label For Text Status
            self.status_label = Label(
                container, text="", font=("Segoe UI", font_size, "bold")
            )
            self.status_label.grid(row=1, column=1, padx=(0, 15), pady=5)
            self.status_label.config(bg="#252525", fg="#ffffff")

        # snap window to borders function
        def ClickRelease(event):
            resolutionX = (
                self.master.winfo_screenwidth()
            )  # gets the actual screen resolution
            resolutionY = self.master.winfo_screenheight()
            global x, y
            if (
                self.master.winfo_y() < 0
            ):  # if the current window position is below 0 , then move the window
                self.master.geometry("+%s+%s" % (x, 0))
            if self.master.winfo_y() > (resolutionY - 60):
                self.master.geometry("+%s+%s" % (x, (resolutionY - 61)))
            if self.master.winfo_x() < 0:
                self.master.geometry("+%s+%s" % (0, y))
            if self.master.winfo_x() > (resolutionX - 140):
                self.master.geometry("+%s+%s" % ((resolutionX - 140), y))

        # left click window dragging function
        def SaveLastClickPos(event):
            global lastClickX, lastClickY
            lastClickX = event.x
            lastClickY = event.y

        def Dragging(event):
            global x, y
            x, y = (
                event.x - lastClickX + self.master.winfo_x(),
                event.y - lastClickY + self.master.winfo_y(),
            )
            self.master.geometry("+%s+%s" % (x, y))

            self.master.attributes("-alpha", win_opacity)
            self.master.attributes("-topmost", True)
            self.master.bind("<ButtonRelease-1>", ClickRelease)

            self.master.bind(
                "<Button-1>", SaveLastClickPos
            )  # click to drag and drop window
            self.master.bind("<B1-Motion>", Dragging)

        # open the popup menu
        def open_menu(e):
            popup_menu.tk_popup(e.x_root, e.y_root)

        def pause_from_menu():
            global is_paused
            if not is_paused:
                popup_menu.entryconfig(0, label="Unpause Recording")
                obs.obs_frontend_recording_pause(True)
                is_paused = True
            else:
                popup_menu.entryconfig(0, label="Pause Recording")
                obs.obs_frontend_recording_pause(False)
                is_paused = False

        def stop_from_menu():
            global window_start
            global is_paused
            window_start = False
            is_paused = False
            obs.obs_frontend_recording_stop()

        # adds a right-click popup menu to the main frame
        popup_menu = Menu(self, tearoff=False)
        popup_menu.add_command(label="Pause Recording", command=pause_from_menu)
        popup_menu.add_command(label="Stop Recording", command=stop_from_menu)
        popup_menu.add_separator()
        popup_menu.add_command(
            label="Reset Window Location", command=self.update_position
        )
        self.master.bind("<Button-3>", open_menu)

        self.master.bind("<ButtonRelease-1>", ClickRelease)
        self.master.bind(
            "<Button-1>", SaveLastClickPos
        )  # click to drag and drop window
        self.master.bind("<B1-Motion>", Dragging)

    def update_position(self):
        """Update window position and size based on screen resolution."""
        screen_w = self.master.winfo_screenwidth()
        # Scale window: width = 15% of screen, height proportional
        w = max(300, min(500, int(screen_w * 0.20)))
        h = max(150, int(w * 0.20))
        x = (screen_w - w) // 2
        y = 20
        self.scale = max(1.0, screen_w / 1920)  # 1.0 at 1080p, scales up for higher res
        self.master.geometry(f"{w}x{h}+{x}+{y}")
        self.master.update_idletasks()

    # update stopwatch function
    def update(self):
        # update seconds with (addition) compound assignment operator
        global hours, minutes, seconds
        seconds += 1
        if seconds == 60:
            minutes += 1
            seconds = 0
        if minutes == 60:
            hours += 1
            minutes = 0
        # format time to include leading zeros
        hours_string = f"{hours}" if hours > 9 else f"0{hours}"
        minutes_string = f"{minutes}" if minutes > 9 else f"0{minutes}"
        seconds_string = f"{seconds}" if seconds > 9 else f"0{seconds}"
        # update timer label after 1000 ms (1 second)
        self.stopwatch_label.config(
            text=hours_string + ":" + minutes_string + ":" + seconds_string
        )
        # after each second (1000 milliseconds), call update function
        # use update_time variable to cancel or pause the time using after_cancel
        global update_time
        update_time = self.stopwatch_label.after(1000, self.update)

    def start(self):
        global running
        if not running:
            self.update()
            running = True

    # reset function
    def reset(self):
        global running
        if running:
            # cancel updating of time using after_cancel()
            self.stopwatch_label.after_cancel(update_time)
            running = False
        # set variables back to zero
        global hours, minutes, seconds
        hours, minutes, seconds = 0, 0, -1
        # set label back to zero
        self.stopwatch_label.config(text="00:00:00")

    # pause function
    def pause(self):
        global running
        if running:
            self.stopwatch_label.after_cancel(update_time)
            running = False

    def check_loop_status(self):
        global window_start
        global loop_destroy
        global is_paused

        if window_start and not is_paused:
            self.start()
            self.master.attributes("-alpha", 0.9)  # window opacity
            if status_text_enable:
                self.status_label.config(text="OBS Is Recording")
            self.canvas.delete("all")
            self.canvas.create_oval(21, 21, 2, 3, outline="grey10", fill="grey40")
            self.canvas.create_oval(20, 20, 4, 5, fill="red", outline="")
        elif not window_start:
            try:  # ingnore the error when the clock stops..
                self.reset()
            except Exception:
                pass
            self.master.attributes("-alpha", 0.0)  # window opacity

        if loop_destroy:
            self.destroy()

        elif is_paused:
            self.pause()
            if status_text_enable:
                self.status_label.config(text="OBS Recording paused")
            self.canvas.delete("all")
            self.canvas.create_rectangle(10, 20, 5, 5, fill="grey20", outline="grey30")
            self.canvas.create_rectangle(20, 20, 15, 5, fill="grey20", outline="grey30")

        self.after(100, self.check_loop_status)  # Check again after delay.


def runtk():  # runs in background thread
    app = Application()
    app.master.title("Background Application Thread")
    app.check_loop_status()
    app.mainloop()


thd = threading.Thread(target=runtk)  # gui thread
thd.daemon = True  # background thread will exit if main thread exits

# ----------------------------   OBS script    ------------------------------------------------------------


class Data:
    OutputDir = None


# this function responds to events inside OBS
def frontend_event_handler(data):
    global is_paused
    global window_start
    global loop_destroy

    if data == obs.OBS_FRONTEND_EVENT_RECORDING_STARTING:
        window_start = True
        is_paused = False

    if data == obs.OBS_FRONTEND_EVENT_RECORDING_STOPPED:
        window_start = False
        is_paused = False
        print("REC stops..")

    if data == obs.OBS_FRONTEND_EVENT_RECORDING_PAUSED:
        is_paused = True
        print("REC paused..")

    if data == obs.OBS_FRONTEND_EVENT_RECORDING_UNPAUSED:
        is_paused = False

def script_load(settings):
    global thd
    if not thd.is_alive():
        thd.start()

def script_unload():
    global loop_destroy
    loop_destroy = True     

def script_update(settings):
    obs.obs_data_set_default_bool(settings, "timer_bool", True)
    Data.TimerEnable = obs.obs_data_get_bool(settings, "timer_bool")

    obs.obs_data_set_default_bool(settings, "status_text_bool", True)
    Data.StatusTextEnable = obs.obs_data_get_bool(settings, "status_text_bool")

    global timer_enable
    if Data.TimerEnable == True:
        timer_enable = True
    else:
        timer_enable = False

    global status_text_enable
    if Data.StatusTextEnable == True:
        status_text_enable = True
    else:
        status_text_enable = False


def script_description():
    return f"""
    <h2><font color="white">Recording Indicator</font></h2>
    <p>Recording Indicator For Your OBS Studio</p>
    <hr>

    <p style="font-size: 14px; margin-top: 10px;">
        <img src="data:image/svg+xml;base64,PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiIHN0YW5kYWxvbmU9Im5vIj8+CjxzdmcKICAgeG1sbnM6ZGM9Imh0dHA6Ly9wdXJsLm9yZy9kYy9lbGVtZW50cy8xLjEvIgogICB4bWxuczpjYz0iaHR0cDovL2NyZWF0aXZlY29tbW9ucy5vcmcvbnMjIgogICB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiCiAgIHhtbG5zOnN2Zz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciCiAgIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIKICAgeG1sbnM6c29kaXBvZGk9Imh0dHA6Ly9zb2RpcG9kaS5zb3VyY2Vmb3JnZS5uZXQvRFREL3NvZGlwb2RpLTAuZHRkIgogICB4bWxuczppbmtzY2FwZT0iaHR0cDovL3d3dy5pbmtzY2FwZS5vcmcvbmFtZXNwYWNlcy9pbmtzY2FwZSIKICAgd2lkdGg9IjEwMjQiCiAgIGhlaWdodD0iMTAyNCIKICAgdmlld0JveD0iMCAwIDEwMjQgMTAyNCIKICAgZmlsbD0ibm9uZSIKICAgdmVyc2lvbj0iMS4xIgogICBpZD0ic3ZnODM1IgogICBzb2RpcG9kaTpkb2NuYW1lPSJPY3RpY29ucy1tYXJrLWdpdGh1Yi5zdmciCiAgIGlua3NjYXBlOnZlcnNpb249IjEuMC4yIChlODZjODcwOCwgMjAyMS0wMS0xNSkiPgogIDxtZXRhZGF0YQogICAgIGlkPSJtZXRhZGF0YTg0MSI+CiAgICA8cmRmOlJERj4KICAgICAgPGNjOldvcmsKICAgICAgICAgcmRmOmFib3V0PSIiPgogICAgICAgIDxkYzpmb3JtYXQ+aW1hZ2Uvc3ZnK3htbDwvZGM6Zm9ybWF0PgogICAgICAgIDxkYzp0eXBlCiAgICAgICAgICAgcmRmOnJlc291cmNlPSJodHRwOi8vcHVybC5vcmcvZGMvZGNtaXR5cGUvU3RpbGxJbWFnZSIgLz4KICAgICAgPC9jYzpXb3JrPgogICAgPC9yZGY6UkRGPgogIDwvbWV0YWRhdGE+CiAgPGRlZnMKICAgICBpZD0iZGVmczgzOSIgLz4KICA8c29kaXBvZGk6bmFtZWR2aWV3CiAgICAgcGFnZWNvbG9yPSIjZmZmZmZmIgogICAgIGJvcmRlcmNvbG9yPSIjNjY2NjY2IgogICAgIGJvcmRlcm9wYWNpdHk9IjEiCiAgICAgb2JqZWN0dG9sZXJhbmNlPSIxMCIKICAgICBncmlkdG9sZXJhbmNlPSIxMCIKICAgICBndWlkZXRvbGVyYW5jZT0iMTAiCiAgICAgaW5rc2NhcGU6cGFnZW9wYWNpdHk9IjAiCiAgICAgaW5rc2NhcGU6cGFnZXNoYWRvdz0iMiIKICAgICBpbmtzY2FwZTp3aW5kb3ctd2lkdGg9IjE0NDAiCiAgICAgaW5rc2NhcGU6d2luZG93LWhlaWdodD0iNzk4IgogICAgIGlkPSJuYW1lZHZpZXc4MzciCiAgICAgc2hvd2dyaWQ9ImZhbHNlIgogICAgIGlua3NjYXBlOnpvb209IjAuNjA0NDkyMTkiCiAgICAgaW5rc2NhcGU6Y3g9IjUxMiIKICAgICBpbmtzY2FwZTpjeT0iNTEyIgogICAgIGlua3NjYXBlOndpbmRvdy14PSIwIgogICAgIGlua3NjYXBlOndpbmRvdy15PSIyNSIKICAgICBpbmtzY2FwZTp3aW5kb3ctbWF4aW1pemVkPSIwIgogICAgIGlua3NjYXBlOmN1cnJlbnQtbGF5ZXI9InN2ZzgzNSIgLz4KICA8cGF0aAogICAgIGZpbGwtcnVsZT0iZXZlbm9kZCIKICAgICBjbGlwLXJ1bGU9ImV2ZW5vZGQiCiAgICAgZD0iTTggMEMzLjU4IDAgMCAzLjU4IDAgOEMwIDExLjU0IDIuMjkgMTQuNTMgNS40NyAxNS41OUM1Ljg3IDE1LjY2IDYuMDIgMTUuNDIgNi4wMiAxNS4yMUM2LjAyIDE1LjAyIDYuMDEgMTQuMzkgNi4wMSAxMy43MkM0IDE0LjA5IDMuNDggMTMuMjMgMy4zMiAxMi43OEMzLjIzIDEyLjU1IDIuODQgMTEuODQgMi41IDExLjY1QzIuMjIgMTEuNSAxLjgyIDExLjEzIDIuNDkgMTEuMTJDMy4xMiAxMS4xMSAzLjU3IDExLjcgMy43MiAxMS45NEM0LjQ0IDEzLjE1IDUuNTkgMTIuODEgNi4wNSAxMi42QzYuMTIgMTIuMDggNi4zMyAxMS43MyA2LjU2IDExLjUzQzQuNzggMTEuMzMgMi45MiAxMC42NCAyLjkyIDcuNThDMi45MiA2LjcxIDMuMjMgNS45OSAzLjc0IDUuNDNDMy42NiA1LjIzIDMuMzggNC40MSAzLjgyIDMuMzFDMy44MiAzLjMxIDQuNDkgMy4xIDYuMDIgNC4xM0M2LjY2IDMuOTUgNy4zNCAzLjg2IDguMDIgMy44NkM4LjcgMy44NiA5LjM4IDMuOTUgMTAuMDIgNC4xM0MxMS41NSAzLjA5IDEyLjIyIDMuMzEgMTIuMjIgMy4zMUMxMi42NiA0LjQxIDEyLjM4IDUuMjMgMTIuMyA1LjQzQzEyLjgxIDUuOTkgMTMuMTIgNi43IDEzLjEyIDcuNThDMTMuMTIgMTAuNjUgMTEuMjUgMTEuMzMgOS40NyAxMS41M0M5Ljc2IDExLjc4IDEwLjAxIDEyLjI2IDEwLjAxIDEzLjAxQzEwLjAxIDE0LjA4IDEwIDE0Ljk0IDEwIDE1LjIxQzEwIDE1LjQyIDEwLjE1IDE1LjY3IDEwLjU1IDE1LjU5QzEzLjcxIDE0LjUzIDE2IDExLjUzIDE2IDhDMTYgMy41OCAxMi40MiAwIDggMFoiCiAgICAgdHJhbnNmb3JtPSJzY2FsZSg2NCkiCiAgICAgZmlsbD0iIzFCMUYyMyIKICAgICBpZD0icGF0aDgzMyIKICAgICBzdHlsZT0iZmlsbDojZmZmZmZmO2ZpbGwtb3BhY2l0eToxIiAvPgo8L3N2Zz4K" width="16" height="16" style="vertical-align: middle;"/>
       <a href="https://github.com/channel101/obs_recording_indicator" style="color: #1E90FF; text-decoration: none; font-weight: bold; margin-left: 5px;">GitHub Repository</a>
    </p>
    """
 

def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_bool(props, "timer_bool", "Enable Timer")
    obs.obs_properties_add_bool(props, "status_text_bool", "Show Status Text")

    return props


obs.obs_frontend_add_event_callback(frontend_event_handler)
