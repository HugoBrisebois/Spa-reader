from tkinter import *
from tkinter import ttk
from datetime import datetime






class GUI:
    @staticmethod
    def update_time(timeLabel):
        now = datetime.now()
        time = now.strftime("%H:%M")

        timeLabel.config(text=time)
        timeLabel.after(1000, lambda: GUI.update_time(timeLabel))

    @staticmethod
    def UI():
        root = Tk()
        root.title("Spa-Reader")
        print("DEBUG: init the windows")

        # define the grid in which content will be placed
        mainFrame = ttk.Frame(root, padding= 30)
        mainFrame.grid(column= 0, row= 0, sticky=(N, W, E, S))


        now = datetime.now()

        time = now.strftime("%H:%M")
        print(time)

        # define the time/clock standby
        timeLabel = ttk.Label(mainFrame, text=time)
        timeLabel.grid(column=2, row=2)
        
        GUI.update_time(timeLabel)

        # run main loop
        root.mainloop()
