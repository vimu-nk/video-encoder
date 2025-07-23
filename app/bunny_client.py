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
    if not all([SRC_KEY, SRC_ZONE, SRC_HOST]):
        raise ValueError("Missing source Bunny CDN configuration. Check your .env file.")
    
    url = f"https://{SRC_HOST}/{SRC_ZONE}/"
    headers = {"AccessKey": SRC_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as res:
            if res.status != 200:
                raise Exception(f"Failed to list files: HTTP {res.status}")
            return await res.json()

def download_file(filename, dest):
    if not all([SRC_KEY, SRC_ZONE, SRC_HOST]):
        raise ValueError("Missing source Bunny CDN configuration. Check your .env file.")
    
    url = f"https://{SRC_HOST}/{SRC_ZONE}/{filename}"
    headers = {"AccessKey": SRC_KEY}
    
    # Ensure destination directory exists
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    
    try:
        with requests.get(url, headers=headers, stream=True) as r:
            r.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to download file '{filename}': {str(e)}")

def upload_file(path, dest_name):
    if not all([DST_KEY, DST_ZONE, DST_HOST]):
        raise ValueError("Missing destination Bunny CDN configuration. Check your .env file.")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File to upload not found: {path}")
    
    url = f"https://{DST_HOST}/{DST_ZONE}/{dest_name}"
    headers = {"AccessKey": DST_KEY}
    
    try:
        with open(path, "rb") as f:
            resp = requests.put(url, headers=headers, data=f)
            resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to upload file '{dest_name}': {str(e)}")
