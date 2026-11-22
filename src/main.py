import threading
import kindle
from sqlite import db_helper
from UI import GUI
from books import bookData

def run_background_service():
    # initialize and or make sure the tables are initialized properly
    print("DEBUG: running services in background")
    db_helper.create_tables("books.db")
    db_helper.create_indexes("books.db")
    book_title = db_helper.fetch_bookTitle("books.db")
    bookData.getBookOLID(book_title)
    

if __name__ == "__main__":

    # create a background thread
    bg_thread = threading.Thread(target=run_background_service, daemon=True)

    # start the background thread
    bg_thread.start()


    # call and run the gui
    GUI.UI()
