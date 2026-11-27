from datetime import datetime
from tkinter import *
from tkinter import ttk, filedialog
import tkinter.font as tkfont
from books import bookData
from kindle import kindle
from sqlite import db_helper


class GUI:
    _cover_image: object | None = None
    _cover_label: ttk.Label | None = None
    _last_rendered_title: str = ""

    @staticmethod
    def load_cover(mainFrame, clean_title: str):
        cover_url = bookData.getBookOLID(clean_title)
        cover_image = (
            bookData.fetch_cover_image(cover_url, width=140, height=210)
            if cover_url
            else None
        )

        if cover_image:
            cover_label = ttk.Label(mainFrame, image=cover_image)
        else:
            cover_label = ttk.Label(mainFrame, text="[No Available Cover]")

        if GUI._cover_label is not None:
            GUI._cover_label.destroy()

        GUI._cover_image = cover_image
        GUI._cover_label = cover_label
        cover_label.grid(column=0, row=0, rowspan=3, padx=(0, 24), sticky=W)

    @staticmethod
    def refresh_display(db_path: str, mainFrame, bookTitleLabel, quoteLabel):
        raw_title = db_helper.fetch_bookTitle(db_path)
        clean_title = bookData.clean_book_title(raw_title)
        quote = db_helper.fetch_latest_quote(db_path)

        bookTitleLabel.config(text=clean_title)
        quoteLabel.config(text=quote)

        if clean_title != GUI._last_rendered_title:
            GUI._last_rendered_title = clean_title
            GUI.load_cover(mainFrame, clean_title)

    @staticmethod
    def open_fileDialog(db_path: str, mainFrame, bookTitleLabel, quoteLabel):
        file_path = filedialog.askopenfilename(
            title="Select Kindle Clippings or KoboReader.sqlite",
            filetypes=[("Reader Files", "*.txt *.sqlite"), ("All files", "*.*")]
        )
        if not file_path:
            return
        GUI.refresh_display(db_path, mainFrame, bookTitleLabel, quoteLabel)

    @staticmethod
    def update_time(timeLabel):
        timeLabel.config(text=datetime.now().strftime("%H:%M"))
        timeLabel.after(1000, lambda: GUI.update_time(timeLabel))

    @staticmethod
    def poll_database(db_path: str, root, mainFrame, bookTitleLabel, quoteLabel):
        GUI.refresh_display(db_path, mainFrame, bookTitleLabel, quoteLabel)
        root.after(3000, lambda: GUI.poll_database(db_path, root, mainFrame, bookTitleLabel, quoteLabel))

    @staticmethod
    def UI(db_path: str, fullscreen: bool = False):
        root = Tk()
        root.title("Spa-Reader")
        root.geometry("800x480")

        # Fullscreen toggle (F11 to toggle, Escape to exit)
        root.attributes("-fullscreen", fullscreen)
        root.bind("<F11>", lambda e: root.attributes("-fullscreen", not root.attributes("-fullscreen")))
        root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))

        # Responsive grid weights for auto-scaling
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        mainFrame = ttk.Frame(root, padding=24)
        mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))
        mainFrame.columnconfigure(1, weight=1)
        mainFrame.rowconfigure(1, weight=1)

        # Dynamic font & quote wrap scaling on window resize
        base_font = tkfont.nametofont("TkDefaultFont")
        quoteLabel = ttk.Label(mainFrame, text="", wraplength=480, justify=LEFT)

        def on_resize(event):
            if event.widget is root:
                new_size = max(10, min(24, int(event.width / 55)))
                base_font.configure(size=new_size)
                quoteLabel.config(wraplength=max(240, event.width - 240))

        root.bind("<Configure>", on_resize)

        # Header row: Book title (left) + Clock (right)
        bookTitleLabel = ttk.Label(mainFrame, text="Loading...")
        bookTitleLabel.grid(column=1, row=0, sticky=(W, N))

        timeLabel = ttk.Label(mainFrame, text=datetime.now().strftime("%H:%M"))
        timeLabel.grid(column=2, row=0, sticky=(E, N))

        # Middle row: Latest highlight
        quoteLabel.grid(column=1, row=1, columnspan=2, pady=12, sticky=(W, N))

        # Bottom row: Import button
        file_btn = ttk.Button(
            mainFrame,
            text="Import Kindle / Kobo",
            command=lambda: GUI.open_fileDialog(db_path, mainFrame, bookTitleLabel, quoteLabel)
        )
        file_btn.grid(column=1, row=2, sticky=(W, S))

        GUI.refresh_display(db_path, mainFrame, bookTitleLabel, quoteLabel)
        GUI.update_time(timeLabel)
        GUI.poll_database(db_path, root, mainFrame, bookTitleLabel, quoteLabel)

        root.mainloop()