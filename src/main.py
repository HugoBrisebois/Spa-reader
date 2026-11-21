import threading
import kindle
from sqlite import db_helper
from UI import GUI

def run_background_service():
    # initialize and or make sure the tables are initialized properly
    print("DEBUG: running services in background")
    db_helper.create_tables("books.db")
    db_helper.create_indexes("books.db")

if __name__ == "__main__":

    # create a background thread
    bg_thread = threading.Thread(target=run_background_service, daemon=True)

    # start the background thread
    bg_thread.start()

    clippings = kindle.parse_kindle_clippings(file_path)
    added = db_helper.import_kindle_batch("books.db", clippings)
    print(f"Imported {added} new highlights")


    # call and run the gui
    GUI.UI()
