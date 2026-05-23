from pydantic import BaseModel, AnyHttpUrl

import requests

class UniversityConfig(BaseModel):
    name_pl: str
    name_en: str
    base_url: AnyHttpUrl


base_url = "https://usosapps.put.poznan.pl/services/apisrv/installations"
data = requests.get(base_url).json()

print(f"Scanned {len(data)} institutions")

universities: list[UniversityConfig] = []

for item in data:
    uni = UniversityConfig(
        name_pl=item.get("institution_name").get("pl"),
        name_en=item.get("institution_name").get("en"),
        base_url = item.get("base_url")
    )
    universities.append(uni)


print(universities)