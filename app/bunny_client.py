import os
import aiohttp
import requests
from dotenv import load_dotenv
load_dotenv()

SRC_KEY = os.getenv("SOURCE_BUNNY_API_KEY")
SRC_ZONE = os.getenv("SOURCE_BUNNY_STORAGE_ZONE")
SRC_HOST = os.getenv("SOURCE_BUNNY_STORAGE_HOST")

DST_KEY = os.getenv("DEST_BUNNY_API_KEY")
DST_ZONE = os.getenv("DEST_BUNNY_STORAGE_ZONE")
DST_HOST = os.getenv("DEST_BUNNY_STORAGE_HOST")

async def list_files():
    url = f"https://{SRC_HOST}/{SRC_ZONE}/"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"AccessKey": SRC_KEY}) as res:
            return await res.json()

def download_file(filename, dest):
    url = f"https://{SRC_HOST}/{SRC_ZONE}/{filename}"
    headers = {"AccessKey": SRC_KEY}
    with requests.get(url, headers=headers, stream=True) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

def upload_file(path, dest_name):
    url = f"https://{DST_HOST}/{DST_ZONE}/{dest_name}"
    headers = {"AccessKey": DST_KEY}
    with open(path, "rb") as f:
        resp = requests.put(url, headers=headers, data=f)
        resp.raise_for_status()
