from .scraper import BaseScraper
from typing import Dict, List, Any
import requests
import os
from datetime import datetime

class DenverScraper(BaseScraper):
    def __init__(self):
        self.base_url = (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316/query"
        )
        self.permit_class_mapping = {
            'Residential': 'Residential',
            'Commercial': 'Commercial',
            'Electrical': 'Electrical',
            'Plumbing': 'Plumbing',
            'Building': 'Building',
            'Mechanical': 'Mechanical',
            'Demolition': 'Demolition',
        }

    def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            # Denver API uses ArcGIS date queries
            where_clause = f"DATE_ISSUED >= DATE '{start_date}' AND DATE_ISSUED <= DATE '{end_date}'"
            params = {
                "where": where_clause,
                "outFields": "*",
                "f": "json",
                "returnGeometry": False,
                "resultRecordCount": 50000,
            }

            print(f"Fetching Denver permits from {start_date} to {end_date}")
            response = requests.get(self.base_url, params=params, timeout=30000)
            response.raise_for_status()

            features = response.json().get("features", [])
            print(f"✅ Received {len(features)} raw permits from Denver API")
            return [f["attributes"] for f in features]

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error ({e.response.status_code}): {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error: {str(e)}")
            return []

    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        validated = []
        for permit in data:
            try:
                if not permit.get("PERMIT_NUM"):
                    continue

                issued_date = self._convert_date(permit.get("DATE_ISSUED"))
                applied_date = self._convert_date(permit.get("DATE_RECEIVED"))

                validated.append({
                    "Permit Num": permit.get("PERMIT_NUM"),
                    "Permit Type Desc": permit.get("CLASS", ""),
                    "Description": permit.get("DESCRIPTION", ""),
                    "Applied Date": applied_date,
                    "Issued Date": issued_date,
                    "current_status": permit.get("STATUS", ""),  # if available
                    "Applicant Name": "",  # Not available in dataset
                    "Applicant Address": self._build_address(
                        permit.get("ADDRESS_NUMBER"),
                        permit.get("ADDRESS_STREETDIR"),
                        permit.get("ADDRESS_STREETNAME"),
                        permit.get("ADDRESS_STREETTYPE"),
                        permit.get("ADDRESS_UNIT")
                    ),
                    "Contractor Name": permit.get("CONTRACTOR_NAME", ""),
                    "Contractor Company Name": permit.get("contractor_company_name", ""),  # Corrected field name
                    "Contractor Phone": permit.get("contractor_phone", ""),
                    "Work Class": permit.get("WORKCLASS", ""),
                    "Permit Class Mapped": self.permit_class_mapping.get(
                        permit.get("CLASS", ""),
                        permit.get("CLASS", "")
                    )
                })

            except Exception as e:
                print(f"⚠️ Error validating Denver permit: {str(e)}")
                continue

        print(f"Validated {len(validated)} permits")
        return validated

    def _convert_date(self, ms_timestamp):
        if ms_timestamp:
            try:
                return datetime.utcfromtimestamp(ms_timestamp / 1000).strftime('%Y-%m-%d')
            except Exception:
                return ""
        return ""

    def _build_address(self, number, dir_, name, type_, unit) -> str:
        parts = [str(number or '').strip(), dir_, name, type_]
        base = ' '.join(filter(None, parts))
        if unit:
            return f"{base} #{unit}"
        return base
