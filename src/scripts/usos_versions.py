import requests


base_url = "https://usosapps.put.poznan.pl/services/apisrv/installations"
data = requests.get(base_url).json()

print(f"Scanned {len(data)} institutions")

all_versions: set[str] = set()

for item in data:
    v = item.get("version")
    if v is not None:
        all_versions.add(v.split(",")[0])

print(sorted(all_versions))

