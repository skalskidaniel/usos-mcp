import urllib.parse
import json
import requests
from pathlib import Path

OUTPUT_FILE = Path(__file__).resolve().parents[1] / "usos" / "auth" / "universities.json"

def generate_uni_key(url: str) -> str:
    hostname = urllib.parse.urlparse(url).hostname
    if not hostname: 
        return ""
    
    for prefix in ['usosapps.', 'usosapi.', 'apps.', 'usos.', 'api.', 'usos-apps.']:
        if hostname.startswith(prefix):
            hostname = hostname[len(prefix):]

    for suffix in ['.edu.pl', '.ac.pl', '.edu', '.pl', '.com', '.org']:
        if hostname.endswith(suffix):
            hostname = hostname[:-len(suffix)]
            break
            
    return hostname.replace('.', '_').replace('-', '_').upper()

def main():
    base_url = "https://usosapps.put.poznan.pl/services/apisrv/installations"
    print(f"Fetching installations from {base_url}...")
    
    response = requests.get(base_url)
    response.raise_for_status()
    data = response.json()
    
    print(f"Scanned {len(data)} institutions.")
    
    universities = {}
    
    for item in data:
        uni_url = item.get("base_url")
        uni_key = generate_uni_key(uni_url)
        
        if not uni_key:
            continue
            
        if uni_key in universities:
            print(f"Warning: duplicate key {uni_key} for {uni_url}, overriding...")
            
        universities[uni_key] = {
            "name_pl": item.get("institution_name", {}).get("pl", ""),
            "name_en": item.get("institution_name", {}).get("en", ""),
            "base_url": uni_url
        }
        
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(universities, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully saved {len(universities)} universities to {OUTPUT_FILE}")
    print(f"Example key: USOS_API_{list(universities.keys())[0]}_CONSUMER_KEY")

if __name__ == "__main__":
    main()
