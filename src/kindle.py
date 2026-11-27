import re
import time
from pathlib import Path
from sqlite import db_helper


class kindle:
    
    META_PATTERN = re.compile(
        r"^- Your (?P<type>\w+) on "
        r"(?:page (?P<page>[\w-]+))?"
        r"(?: \| )?"
        r"(?:Location (?P<location>[\d-]+))?"
        r" \| Added on (?P<date>.+)$"
    )

    @staticmethod
    def watch_kindle_paths(db: str, watch_paths: list[str], interval: int = 5):
        """Polls common Kindle USB mount paths and local drop folders for changes."""
        last_mtimes: dict[str, float] = {}

        while True:
            for raw_path in watch_paths:
                p = Path(raw_path)
                if p.is_file():
                    mtime = p.stat().st_mtime
                    if last_mtimes.get(str(p)) != mtime:
                        print(f"DEBUG: Detected updated Kindle file at {p}")
                        clippings = kindle.parse_kindle_clippings(str(p))
                        added = db_helper.import_kindle_batch(db, clippings)
                        print(f"DEBUG: Auto-imported {added} new highlights")
                        last_mtimes[str(p)] = mtime
            time.sleep(interval)


    @staticmethod
    def parse_kindle_clippings(file_path):
        # use utf-sig to automatically remove the invisible BOM characters Kindle adds to the start of their file
        text = Path(file_path).read_text(encoding="utf-8-sig")

        # split the files with the "=========" string used to separate thedifferent parts of the file
        raw_blocks = text.split("==========")
        clippings = []

        for block in raw_blocks:
            # clean whitespace and split the blocks into individual lines
            lines = [line.strip() for line in block.strip().splitlines() if line.strip()]

            # a valid highlight/note needs at least 3 non-empty lines (title, metadata, content)
            if len(lines) < 2:
                continue

            title_line = lines[0]
            meta_line = lines[1]
            # bookmarks only have 2 lines, so content will be and empty sting ""
            content = "\n".join(lines[2:]) if len(lines) >=3 else ""

            # match the metadata line against the custom regex
            match = kindle.META_PATTERN.match(meta_line)
            if match:
                record = match.groupdict()
                record["book"] = title_line
                record["content"] = content
                clippings.append(record)
            else:
                print(f"Skipped unreconized format: {meta_line}")

        return clippings

    # function to calculate the amount of time spent between the  note made that says "start" and the note that says "end" 
    # to calculate the sample time spent reading
    @staticmethod
    def get_time_read():
        pass