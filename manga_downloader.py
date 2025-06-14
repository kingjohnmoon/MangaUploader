import os
import requests
import time

class MangaDownloader:
    def __init__(self, manga_name, quality='data'):
        """
        :param manga_name: Name of the manga to download
        :param quality: 'data' (original) or 'data-saver' (compressed)
        :param output_dir: Directory to save downloaded chapters
        """
        self.base_url = "https://api.mangadex.org"
        self.manga_name = manga_name
        self.quality = quality  # 'data' or 'data-saver'
        self.output_dir = os.path.join("downloads", manga_name.replace(" ", "_").lower())
        os.makedirs(self.output_dir, exist_ok=True)

    def search_manga(self):
        """Search for manga and return its ID."""
        r = requests.get(
            f"{self.base_url}/manga",
            params={
                "title": self.manga_name, 
                "limit": 1,
            }
        )
        return r.json()["data"][0]["id"]
    
    def get_chapter_ids(self, manga_id):
        """Get all chapters of the manga."""
        r = requests.get(
            f"{self.base_url}/manga/{manga_id}/feed",
            params={
                "limit": 100,
                "translatedLanguage[]": "en",
                "order[chapter]": "asc",
            }
        )
        return [chapter["id"] for chapter in r.json()["data"]]
    
    def download_chapters(self, chapter_ids):
        """Download all chapters."""
        for i, chapter_id in enumerate(chapter_ids, 1):
            self.download_chapter(chapter_id, i)

    def download_chapter(self, chapter_id, chapter_number):
        """Download a single chapter."""
        r = requests.get(
            f"{self.base_url}/at-home/server/{chapter_id}",
            params={"quality": self.quality}
        )
        data = r.json()
        chapter_dir = os.path.join(self.output_dir, str(chapter_number))
        os.makedirs(chapter_dir, exist_ok=True)

        for i, page in enumerate(data["chapter"]["data"], 1):
            image_url = f"{data['baseUrl']}/{self.quality}/{data["chapter"]["hash"]}/{page}"
            image_data = requests.get(image_url).content
            with open(os.path.join(chapter_dir, f"{i}.jpg"), 'wb') as img_file:
                img_file.write(image_data)
            
    def run(self):
        """Run the downloader."""
        manga_id = self.search_manga()
        chapter_ids = self.get_chapter_ids(manga_id)
        self.download_chapters(chapter_ids)
        print(f"Downloaded {len(chapter_ids)} chapters of '{self.manga_name}'.")

if __name__ == "__main__":
    manga_name = "Terrarium in Drawer"

    downloader = MangaDownloader(manga_name)
    downloader.run()
    
