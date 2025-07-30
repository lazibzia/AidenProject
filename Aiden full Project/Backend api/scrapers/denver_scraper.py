# # scrapers/denver_scraper.py
# from .scraper import BaseScraper
# from typing import Dict, List, Any
# import pandas as pd
# from denver_scraper import scrape_new_permits  # Your existing scraper
#
# class DenverScraper(BaseScraper):
#     """Denver permits scraper"""
#
#     def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
#         """Scrape Denver permits"""
#         try:
#             # Use your existing scraper
#             df = scrape_new_permits(start_date=start_date, end_date=end_date, save_csv=False)
#
#             # Convert DataFrame to list of dictionaries
#             permits = df.to_dict('records')
#
#             return permits
#
#         except Exception as e:
#             print(f"Error scraping Denver permits: {e}")
#             return []
#
#     def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Validate and clean Denver permit data"""
#         validated = []
#
#         for permit in data:
#             # Skip if no permit number
#             if not permit.get('PERMIT_NUM'):
#                 continue
#
#             # Normalize field names to match database schema
#             normalized = {
#                 'permit_num': permit.get('PERMIT_NUM'),
#                 'address': permit.get('ADDRESS', ''),
#                 'contractor_name': permit.get('CONTRACTOR_NAME', ''),
#                 'valuation': self._parse_float(permit.get('VALUATION', 0)),
#                 'permit_fee': self._parse_float(permit.get('PERMIT_FEE', 0)),
#                 'date_issued': permit.get('DATE_ISSUED', ''),
#                 'neighborhood': permit.get('NEIGHBORHOOD', ''),
#                 'class': permit.get('CLASS', ''),
#                 'units': self._parse_int(permit.get('UNITS', 0)),
#                 'description': permit.get('DESCRIPTION', ''),
#                 'status': permit.get('STATUS', 'Active')
#             }
#
#             validated.append(normalized)
#
#         return validated
#
#     def _parse_float(self, value) -> float:
#         """Safely parse float values"""
#         try:
#             if pd.isna(value) or value == '':
#                 return 0.0
#             return float(value)
#         except (ValueError, TypeError):
#             return 0.0
#
#     def _parse_int(self, value) -> int:
#         """Safely parse integer values"""
#         try:
#             if pd.isna(value) or value == '':
#                 return 0
#             return int(float(value))
#         except (ValueError, TypeError):
#             return 0
from .scraper import BaseScraper
from typing import Dict, List, Any
import requests
from datetime import datetime

class DenverScraper(BaseScraper):
    def __init__(self):
        self.base_url = (
            "https://services1.arcgis.com/zdB7qR0BtYrg0Xpl/arcgis/rest/services/"
            "ODC_DEV_RESIDENTIALCONSTPERMIT_P/FeatureServer/316/query"
        )

    def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            where_clause = f"DATE_ISSUED >= DATE '{start_date}' AND DATE_ISSUED <= DATE '{end_date}'"
            params = {
                "where": where_clause,
                "outFields": "*",
                "f": "json",
                "returnGeometry": False,
                "resultRecordCount": 5000
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()

            features = response.json().get("features", [])
            print(f"✅ Denver API returned {len(features)} permits")
            return [f["attributes"] for f in features]

        except Exception as e:
            print(f"❌ Error scraping Denver permits: {e}")
            return []

    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        validated = []
        for permit in data:
            if not permit.get('PERMIT_NUM'):
                continue

            # Convert timestamps from milliseconds to yyyy-mm-dd
            issued_date = self._convert_date(permit.get("DATE_ISSUED"))
            applied_date = self._convert_date(permit.get("DATE_RECEIVED"))

            validated.append({
                'Permit Num': permit.get('PERMIT_NUM'),
                'Permit Type Desc': permit.get('CLASS', ''),
                'Description': permit.get('DESCRIPTION', ''),
                'Applied Date': applied_date,
                'Issued Date': issued_date,
                'current_status': '',  # Not provided in data
                'Applicant Name': '',  # Not available
                'Applicant Address': self._build_address(
                    permit.get('ADDRESS_NUMBER'),
                    permit.get('ADDRESS_STREETDIR'),
                    permit.get('ADDRESS_STREETNAME'),
                    permit.get('ADDRESS_STREETTYPE'),
                    permit.get('ADDRESS_UNIT')
                ),
                'Contractor Name': permit.get('CONTRACTOR_NAME', ''),
                'Contractor Address': '',  # Not available
            })

        return validated

    def _convert_date(self, ms_timestamp):
        if ms_timestamp:
            try:
                return datetime.utcfromtimestamp(ms_timestamp / 1000).strftime('%Y-%m-%d')
            except Exception:
                return ''
        return ''

    def _build_address(self, number, dir_, name, type_, unit) -> str:
        parts = [str(number or '').strip(), dir_, name, type_]
        base = ' '.join(filter(None, parts))
        if unit:
            return f"{base} #{unit}"
        return base

