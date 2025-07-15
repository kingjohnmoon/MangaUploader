# MangaUploader
Will try to automate a TikTok account that publishes chapters of manga in order to fund my expenses

# Manga Downloader
manga_downloader.py contains a class which takes in the name of a manga and attempts to download all chapters of that manga from Mangadex into a local folder with structure downloads/{manga name}/{chapter number}/{chapter page}.jpg

Chapters are downloaded in ascending order using the Mangadex API (Very grateful for them for providing this free and very easy to use service)

# Manga Uploader
manga_uploader.py contains a class which is supposed to access TikTok using Selenium and upload manga files to your account before posting them. Unfortunately, I have discovered that image posting is only available on the TikTok App and not from the browser, which has grinded this project down to a halt. 

Currently, the project is on hiatus as I think about ways to circumvent the current issues, and also explore other stuff to do.