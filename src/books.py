import requests
import re

class bookData:
    @staticmethod
    def clean_book_title(raw_filename: str) -> str:
        # remove file extensions if present (e.g., .epub, .pdf)
        title = re.sub(r'\.(epub|pdf|mobi|txt)$', '', raw_filename, flags=re.IGNORECASE)
    
        # replace underscores and hyphens used as spaces with actual spaces
        title = title.replace('_', ' ')
    
        # strip out common junk suffixes like "Full book" & "Unabridged"
        title = re.sub(r'(?i)\b(full\s*book|unabridged|audiobook)\b', '', title)
    
        # remove leading numbers and separators typical of series (e.g., "4 - " or "2 -_ ")
        title = re.sub(r'^\d+\s*[-_]+\s*', '', title)
    
        # remove author names or publication years in parentheses or trailing dashes (e.g., " - Frank Herbert (1981)")
        title = re.sub(r'\s*-\s*[A-Z][a-z]+(\s+[A-Z][a-z]+)*\s*(\(\d{4}\))?', '', title)
        title = re.sub(r'\s*\(\d{4}\)', '', title)  # Remove stray years like (1981)
    
        # clean up extra whitespace
        return ' '.join(title.split()).strip()

    @staticmethod
    def getBookOLID(book_title: str):
        base_url_title = "https://openlibrary.org/"

        # making sure the openlibrary api request goes through properly
        headers = {
            "User-Agent": "SpaReader ()"
        }

        try:
            book = bookData.clean_book_title(book_title)
            r = requests.get(f"{base_url_title}search.json?q='{book}'", headers=headers, timeout=5000)

            if r.status_code == 200:
                print("success")
                data = r.json()
                print(data)

                docs = data.get("docs", [])
                if docs:
                    firstbook = docs[0]

                    # open library provides 'cover_i' (Cover ID) if available
                    cover_id = firstbook.get("cover_i")
                    if cover_id:
                        # return the direct image URL (sizes can be 'S' 'M' 'L')
                        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"

                    # Fallback: check for ISBN if cover_i is missing
                    isbns = firstbook.get("isbn", [])
                    if isbns:
                        return f"https://covers.openlibrary.org/b/isbn/{isbns[0]}-L.jpg"
                
            print("No books found in query")
            return None

        except requests.RequestException as e:
            print(f"Network or connection error: {e}")
            return None