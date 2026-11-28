import io
import re
import requests
from PIL import Image, ImageTk

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
    def getBookOLID(book_title: str) -> str | None:
        base_url = "https://openlibrary.org"
        headers = {
            "User-Agent": "SpaReader (your-email@example.com)"
        }
        
        try:
            # Query Open Library with our cleaned title
            r = requests.get(f"{base_url}/search.json?q={book_title}", headers=headers, timeout=10)
            
            if r.status_code == 200:
                data = r.json()
                docs = data.get("docs", [])
                
                if docs:
                    first_book = docs[0]
                    
                    # Open Library provides a 'cover_i' (Cover ID) if available
                    cover_id = first_book.get("cover_i")
                    
                    if cover_id:
                        # Return the direct image URL (sizes can be 'S', 'M', 'L')
                        return f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
                    
                    # Fallback: check for ISBN if cover_i is missing
                    isbns = first_book.get("isbn", [])
                    if isbns:
                        return f"https://covers.openlibrary.org/b/isbn/{isbns[0]}-L.jpg"
                        
            print("No cover found for this title.")
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Network error fetching cover: {e}")
            return None

    @staticmethod
    def fetch_cover_image(url: str,width: int = 120, height: int = 180):
        # downloads an image from a URL and returns a Tkinter PhotoImage
        print("getting cover image to display")
        try: 
            headers = {"User-Agent": "SpaReader ()"}
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                print("DEBUG: fetching successful")
                # read bytes into a stream and open with Pillow
                image_stream = io.BytesIO(response.content)
                pil_image = Image.open(image_stream)

                # resize the cover to fit neatly inside the UI
                pil_image = pil_image.resize((width, height), Image.Resampling.LANCZOS)

                # convert to a tkinter compatible image
                return ImageTk.PhotoImage(pil_image)
        except Exception as e:
            print(f"Failed to load cover image: {e}")

        return None