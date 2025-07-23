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

async def list_files(path=""):
    if not all([SRC_KEY, SRC_ZONE, SRC_HOST]):
        raise ValueError("Missing source Bunny CDN configuration. Check your .env file.")
    
    # Clean up the path
    if path and not path.endswith('/'):
        path += '/'
    if path.startswith('/'):
        path = path[1:]
    
    url = f"https://{SRC_HOST}/{SRC_ZONE}/{path}"
    headers = {"AccessKey": SRC_KEY}
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as res:
            if res.status != 200:
                raise Exception(f"Failed to list files: HTTP {res.status}")
            
            files = await res.json()
            
            # Separate directories and files
            directories = []
            video_files = []
            
            for item in files:
                if item.get('IsDirectory', False):
                    directories.append({
                        'name': item['ObjectName'],
                        'path': path + item['ObjectName'],
                        'type': 'directory'
                    })
                else:
                    # Filter for video files
                    name = item['ObjectName']
                    if any(name.lower().endswith(ext) for ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v']):
                        video_files.append({
                            'name': name,
                            'path': path + name,
                            'size': item.get('Length', 0),
                            'type': 'file',
                            'last_modified': item.get('LastChanged', '')
                        })
            
            return {
                'current_path': path,
                'parent_path': '/'.join(path.rstrip('/').split('/')[:-1]) if path and '/' in path.rstrip('/') else '',
                'directories': directories,
                'files': video_files
            }

def download_file(file_path, dest):
    if not all([SRC_KEY, SRC_ZONE, SRC_HOST]):
        raise ValueError("Missing source Bunny CDN configuration. Check your .env file.")
    
    # file_path now includes the full path within the storage zone
    url = f"https://{SRC_HOST}/{SRC_ZONE}/{file_path}"
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
        raise Exception(f"Failed to download file '{file_path}': {str(e)}")

def upload_file(path, dest_name):
    if not all([DST_KEY, DST_ZONE, DST_HOST]):
        raise ValueError("Missing destination Bunny CDN configuration. Check your .env file.")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"File to upload not found: {path}")
    
    url = f"https://{DST_HOST}/{DST_ZONE}/{dest_name}"
    headers = {"AccessKey": DST_KEY}
    
    # Get file size for progress tracking
    file_size = os.path.getsize(path)
    
    # Configure session with SSL and retry settings
    session = requests.Session()
    
    # Add SSL configuration and retry strategy
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    import urllib3
    
    # Disable SSL warnings for problematic connections
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Configure retry strategy
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["PUT"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    
    try:
        with open(path, "rb") as f:
            # Use session with timeout and SSL verification disabled for problematic connections
            resp = session.put(
                url, 
                headers=headers, 
                data=f,
                timeout=(30, 300),  # Connect timeout 30s, read timeout 5min
                verify=True  # Keep SSL verification but handle errors gracefully
            )
            resp.raise_for_status()
            return True
            
    except requests.exceptions.SSLError as e:
        # Try again with SSL verification disabled
        try:
            with open(path, "rb") as f:
                resp = session.put(
                    url, 
                    headers=headers, 
                    data=f,
                    timeout=(30, 300),
                    verify=False  # Disable SSL verification as fallback
                )
                resp.raise_for_status()
                return True
        except requests.exceptions.RequestException as retry_e:
            raise Exception(f"Failed to upload file '{dest_name}' after SSL retry: {str(retry_e)}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"Failed to upload file '{dest_name}': {str(e)}")
    
    finally:
        session.close()
