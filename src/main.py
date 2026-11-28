import os
import threading
import time
from pathlib import Path
from kindle import kindle
from sqlite import db_helper

DB_PATH = os.getenv("SPA_DB_PATH", "data/books.db")
MODE = os.getenv("SPA_MODE", "gui") # gui or headless

def run_background_service(db_path: str):
    print("DEBUG: starting and running the background thread for file watching")
    user = os.getenv("USER", "pi")
    kindle_paths = [
        f"/media/{user}/Kindle/documents/My Clippings.txt",
        f"/run/media/{user}/Kindle/documents/My Clippings.txt",
        "dropzone/My Clippings",
    ]

    last_mtimes: dict[str, float] = {}

    while True:
        for raw_path in kindle_paths:
            p = Path(raw_path)
            if p.is_file() and last_mtimes.get(str(p)) != p.stat().st_mtime:
                print("DEBUG: parsing the 'My clippings.txt'")
                clippings = kindle.parse_kindle_clippings(str(p))
                print("DEBUG: importing into the database")
                added = db_helper.import_kindle_batch(db_path, clippings)
                print(f"auto-imported {added} kindle highlights from {p}")
                last_mtimes[str(p)] = p.stat().st_mtime

        time.sleep(5)

if __name__ == "__main__":
    resolved_db = db_helper.make_databaseFile(DB_PATH)
    Path("dropzone").mkdir(exist_ok=True)

    if MODE == "headless":
        print(f"running spa-reader in headless mode using {resolved_db}")
        run_background_service(resolved_db)
    else:
        bg_thread = threading.Thread(
            target=run_background_service, args=(resolved_db, ), daemon=True
        )
        bg_thread.start()

        from UI import GUI
        GUI.UI(db_path=resolved_db, fullscreen=os.getenv("SPA_FULSCREEN", "0") == "1")