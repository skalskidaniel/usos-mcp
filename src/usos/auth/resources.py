from fastmcp.resources import resource
import requests
import json

@resource(
    "usos://universities/supported",
    name="supported-universities",
    description="Get a JSON list of supported universities along with their base_url. Use this to lookup the user's university API endpoint."
)
def supported_universities() -> str:
    base_url = "https://usosapps.put.poznan.pl/services/apisrv/installations"
    try:
        data = requests.get(base_url, timeout=10).json()
        universities = []
        for item in data:
            universities.append({
                "name_pl": item.get("institution_name", {}).get("pl"),
                "name_en": item.get("institution_name", {}).get("en"),
                "base_url": item.get("base_url")
            })
        return json.dumps(universities, indent=2)
    except Exception as e:
        return f"Error fetching universities: {str(e)}"
