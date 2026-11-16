import re
from pathlib import Path

META_PATTERN = re.compile(
    r"^- Your (?P<type>\w+) on (?:page (?P<page>[\w-]+) \| )?Location (?P<location>[\d-]+) \| Added on (?P<date>.+)$"
)

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
        if len(lines) < 3:
            continue

        title_line = lines[0]
        meta_line = lines[1]
        content = "\n".join(lines[2:]) # join remaining lines in case the highlight has multiple paragraphs

        # match the metadata line against the custom regex
        match = META_PATTERN.match(meta_line)
        if match:
            record = match.groupdict()
            record["book"] = title_line
            record["content"] = content
            clippings.append(record)
        else:
            print(f"Skipped unreconized format: {meta_line}")

    return clippings

output = parse_kindle_clippings("My Clippings.txt")
print("output")