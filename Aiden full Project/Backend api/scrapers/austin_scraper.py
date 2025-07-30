# from .scraper import BaseScraper
# from typing import Dict, List, Any
# import requests
# import pandas as pd
#
# class AustinScraper(BaseScraper):
#     """Austin permits scraper"""
#
#     def __init__(self):
#         self.base_url = "https://data.austintexas.gov/resource/3syk-w9eu.json"
#
#     def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
#         """Scrape Austin permits"""
#         try:
#             # Austin uses Socrata API
#             params = {
#                 '$where': f"issued_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'",
#                 '$limit': 10000,
#                 'permit_type': 'Residential'
#             }
#
#             response = requests.get(self.base_url, params=params)
#             response.raise_for_status()
#
#             permits = response.json()
#             return permits
#
#         except Exception as e:
#             print(f"Error scraping Austin permits: {e}")
#             return []
#
#     def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Validate and clean Austin permit data"""
#         validated = []
#
#         for permit in data:
#             if not permit.get('permit_number'):
#                 continue
#
#             normalized = {
#                 'permit_num': permit.get('permit_number'),
#                 'address': permit.get('address', ''),
#                 'contractor_name': permit.get('contractor', ''),
#                 'valuation': self._parse_float(permit.get('valuation', 0)),
#                 'permit_fee': self._parse_float(permit.get('permit_fee', 0)),
#                 'date_issued': permit.get('issued_date', ''),
#                 'neighborhood': permit.get('district', ''),
#                 'class': permit.get('permit_class', ''),
#                 'units': self._parse_int(permit.get('units', 0)),
#                 'description': permit.get('description', ''),
#                 'status': permit.get('status', 'Active')
#             }
#
#             validated.append(normalized)
#
#         return validated
#
#     def _parse_float(self, value) -> float:
#         try:
#             return float(value) if value else 0.0
#         except (ValueError, TypeError):
#             return 0.0
#
#     def _parse_int(self, value) -> int:
#         try:
#             return int(float(value)) if value else 0
#         except (ValueError, TypeError):
#             return 0

# from .scraper import BaseScraper
# from typing import Dict, List, Any
# import requests
#
# class AustinScraper(BaseScraper):
#     """Austin permits scraper"""
#
#     def __init__(self):
#         self.base_url = "https://data.austintexas.gov/resource/3syk-w9eu.json"
#
#     def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
#         """Scrape Austin permits"""
#         try:
#             where = f"issue_date between '{start_date}T00:00:00' and '{end_date}T23:59:59' AND permit_class = 'Residential'"
#             params = {
#                 '$where': where,
#                 '$limit': 10000
#             }
#
#             response = requests.get(self.base_url, params=params)
#             response.raise_for_status()
#
#             permits = response.json()
#             print(f"✅ Austin API returned {len(permits)} permits")
#             return permits
#
#         except Exception as e:
#             print(f"❌ Error scraping Austin permits: {e}")
#             return []
#
#     def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
#         """Validate and normalize Austin permit data"""
#         validated = []
#
#         for permit in data:
#             if not permit.get('permit_number'):
#                 continue
#
#             normalized = {
#                 'permit_num': permit.get('Permit Num'),
#                 'permit_type': permit.get('Permit Type Desc', ''),
#                 'description': permit.get('Description', ''),
#                 'applied_date': permit.get('AppliedDate', ''),
#                 'issued_date': permit.get('Issue_Date', ''),
#                 'address': permit.get('Address', ''),
#                 #'applicant_name': permit.get('Applicant_Full_Name', ''),
#                 'applicant_address': self._combine_address(
#                     permit.get('Applicant Address 1', ''),
#                     permit.get('Applicant Address 2', '')
#                 ),
#                 'contractor_name': permit.get('Contractor_Full_Name', ''),
#                 'contractor_address': self._combine_address(
#                     permit.get('Contractor Address 1', ''),
#                     permit.get('Contractor Address 2', '')
#                 )
#             }
#
#             validated.append(normalized)
#
#         return validated
#
#     def _combine_address(self, line1: str, line2: str) -> str:
#         if line1 and line2:
#             return f"{line1}, {line2}"
#         return line1 or line2 or ''
from .scraper import BaseScraper
from typing import Dict, List, Any
import requests

class AustinScraper(BaseScraper):
    def __init__(self):
        self.base_url = "https://data.austintexas.gov/resource/3syk-w9eu.json"

    def scrape(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        try:
            where = (
                f"issue_date between '{start_date}T00:00:00' and '{end_date}T23:59:59'"
                " AND permit_class = 'Residential'"
            )
            params = {
                '$where': where,
                '$limit': 10000
            }

            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            permits = response.json()
            print(f"✅ Austin API returned {len(permits)} permits")
            return permits

        except Exception as e:
            print(f"❌ Error scraping Austin permits: {e}")
            return []

    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        validated = []
        for permit in data:
            if not permit.get('permit_number'):
                continue

            validated.append({
                'Permit Num': permit.get('permit_number'),
                'Permit Type Desc': permit.get('permit_type_desc', ''),
                'Description': permit.get('description', ''),
                'Applied Date': permit.get('applieddate', ''),
                'Issued Date': permit.get('issue_date', ''),
                'current_status': permit.get('status_current', ''),
                'Applicant Name': permit.get('applicant_full_name', ''),
                'Applicant Address': self._combine_address(
                    permit.get('applicant_address1', ''),
                    permit.get('applicant_address2', '')
                ),
                'Contractor Name': permit.get('contractor_full_name', ''),
                'Contractor Address': self._combine_address(
                    permit.get('contractor_address1', ''),
                    permit.get('contractor_address2', '')
                )
            })

        return validated

    def _combine_address(self, line1: str, line2: str) -> str:
        return f"{line1}, {line2}" if line1 and line2 else line1 or line2 or ''
