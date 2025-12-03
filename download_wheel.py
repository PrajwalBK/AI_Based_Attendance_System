import requests
import os

url = "https://github.com/Gourieff/Assets/raw/main/Insightface/insightface-0.7.3-cp310-cp310-win_amd64.whl"
filename = "insightface-0.7.3-cp310-cp310-win_amd64.whl"

print(f"Downloading {filename} from {url}...")

try:
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    with open(filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
            
    print(f"Successfully downloaded {filename}")
except Exception as e:
    print(f"Failed to download: {e}")
