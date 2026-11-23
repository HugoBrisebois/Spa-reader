from tkinter import *
from tkinter import ttk, filedialog
from datetime import datetime
from sqlite import db_helper
from kindle import kindle
from books import bookData


class GUI:
    _cover_image: object | None = None
    _cover_label: ttk.Label | None = None

    @staticmethod
    def load_cover(mainFrame, book_title):
        clean_title = bookData.clean_book_title(book_title)
        cover_url = bookData.getBookOLID(clean_title) if clean_title else None
        cover_image = (
            bookData.fetch_cover_image(cover_url, width=120, height=180)
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
        cover_label.grid(column=1, row=1, pady=10)
        return cover_label
    
    # open the filadialog module
    @staticmethod
    def open_fileDialog(bookTitleLabel, mainFrame):
        file_path = filedialog.askopenfilename(
            title="Select My Clippings.txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not file_path:
            return  # User canceled the dialog

        clippings = kindle.parse_kindle_clippings(file_path)
        added = db_helper.import_kindle_batch("books.db", clippings)
        print(f"Imported {added} new highlights")

        # Refresh the label with the latest book title
        new_title = db_helper.fetch_bookTitle("books.db")
        clean_title = bookData.clean_book_title(new_title)

        bookTitleLabel.config(text=clean_title)
        GUI.load_cover(mainFrame, clean_title)

    # function to update the time in the application
    @staticmethod
    def update_time(timeLabel):
        now = datetime.now()
        timeLabel.config(text=now.strftime("%H:%M"))
        timeLabel.after(1000, lambda: GUI.update_time(timeLabel))


    # main function to control the GUI
    @staticmethod
    def UI():
        root = Tk()
        root.title("Spa-Reader")

        mainFrame = ttk.Frame(root, padding=30)
        mainFrame.grid(column=0, row=0, sticky=(N, W, E, S))

        # Fetch book title of the most recent book from the database and display it
        book = db_helper.fetch_bookTitle("books.db")
        bookTitle = bookData.clean_book_title(book)

        bookTitleLabel = ttk.Label(mainFrame, text=bookTitle)
        bookTitleLabel.grid(column=1, row=2)

        GUI.load_cover(mainFrame, bookTitle)

        # Define the clock label once
        timeLabel = ttk.Label(mainFrame, text=datetime.now().strftime("%H:%M"))
        timeLabel.grid(column=2, row=2)

        # Pass bookTitleLabel into open_fileDialog using lambda
        file_btn = ttk.Button(
            mainFrame,
            text="open My Clippings.txt",
            command=lambda: GUI.open_fileDialog(bookTitleLabel, mainFrame)
        )
        file_btn.grid(column=3, row=2)

        GUI.update_time(timeLabel)

        # Run the main app loop
        root.mainloop()