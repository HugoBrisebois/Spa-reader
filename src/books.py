import requests
from kindle import kindle

class bookData:


    @staticmethod
    def getBookOLID(book_title: str):
        base_url_title = "https://openlibrary.org/"

        # making sure the openlibrary api request goes through properly
        headers = {
            "User-Agent": "SpaReader ()"
        }

        try:
            r = requests.get(f"{base_url_title}search.json?q={book_title}", headers=headers, timeout=5000)

            if r.status_code == 200:
                print("success")
                data = r.json()

                docs = data.get("docs", [])
                if docs:
                    firstbook = docs[0]

                    work_key = firstbook.get("key", "")
                    if work_key:
                        olid = work_key.split("/")[-1]
                        print(olid)
                        return olid
                else:
                    print("No books found in query")
                    return None
            
            else:
                print(f"Error: {r.status_code}")

        except requests.RequestException as e:
            print(f"Network or connection error: {e}")