import requests
from typing import List, Dict, Any

class DenverScraper:
    def __init__(self):
        self.base_url = "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316/query"

    def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            params = {
                "where": f"ISSUEDATE >= DATE '{start_date}' AND ISSUEDATE <= DATE '{end_date}'",
                "outFields": "*",
                "f": "json",
                "returnGeometry": "false",
                "resultRecordCount": 1000
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            features = response.json().get("features", [])
            print(f"✅ Denver API returned {len(features)} permits")

            return [f["attributes"] for f in features]

        except Exception as e:
            print(f"❌ Error scraping Denver permits: {e}")
            return []

# Test it
scraper = DenverScraper()
permits = scraper.scrape("2000-01-01", "2024-01-31")

# Print one sample
if permits:
    print("\n🔍 Sample permit fields:")
    for k, v in permits[0].items():
        print(f"{k}: {v}")
