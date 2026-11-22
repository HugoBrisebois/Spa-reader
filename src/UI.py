from tkinter import *
from tkinter import ttk, filedialog
from datetime import datetime
from sqlite import db_helper
from kindle import kindle
from books import bookData


class GUI:
    # Update the book cover in the aplication
    @staticmethod
    def update_bookCover(bookName):
        clean_bookTitle = bookData.clean_book_title(bookName)
        bookData.getBookOLID(clean_bookTitle)
    
    # open the filadialog module
    @staticmethod
    def open_fileDialog(bookTitleLabel):
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
        bookTitleLabel.config(text=new_title)

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

        # Define the clock label once
        timeLabel = ttk.Label(mainFrame, text=datetime.now().strftime("%H:%M"))
        timeLabel.grid(column=2, row=2)

        # Pass bookTitleLabel into open_fileDialog using lambda
        file_btn = ttk.Button(
            mainFrame,
            text="open My Clippings.txt",
            command=lambda: GUI.open_fileDialog(bookTitleLabel)
        )
        file_btn.grid(column=3, row=2)

        GUI.update_time(timeLabel)

        # Run the main app loop
        root.mainloop()