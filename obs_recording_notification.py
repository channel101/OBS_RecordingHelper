import tkinter as tk
from tkinter import *
import threading
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

        # Modern container frame with subtle border
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

    if data == obs.OBS_FRONTEND_EVENT_FINISHED_LOADING:
        if not thd.is_alive():
            thd.start()

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
    return (
        "OBS RECORDING NOTIFICATION\n\n"
        "ATTENTION:\n\n"
        " Restart OBS after adding the script\n\n\n"
        " Installation: \n"
        " You have to select a Python 3.6.8 version package "
        " in the configuration that includes TKinter library,"
        " you can find the embedded package and instructions in my github \n\n "
        " github.com/tobsailbot/obs_recording_notification\n\n"
    )


def script_properties():
    props = obs.obs_properties_create()

    obs.obs_properties_add_bool(props, "timer_bool", "Enable Timer")
    obs.obs_properties_add_bool(props, "status_text_bool", "Show Status Text")

    return props


obs.obs_frontend_add_event_callback(frontend_event_handler)
