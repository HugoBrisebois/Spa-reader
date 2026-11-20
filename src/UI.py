from tkinter import *
from tkinter import ttk

class GUI:
    @staticmethod
    def UI():
        root = Tk()
        root.title("Spa-Reader")
        print("DEBUG: init the windows")

        # define the grid in which content will be placed
        mainFrame = ttk.Frame(root, padding= 30)
        mainFrame.grid(column= 0, row= 0, sticky=(N, W, E, S))

        # run main loop
        root.mainloop()