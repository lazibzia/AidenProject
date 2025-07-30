from typing import Dict, Any

CITY_CONFIGS: Dict[str, Dict[str, Any]] = {
    'denver': {
        'display_name': 'Denver, CO',
        'timezone': 'America/Denver',
        'scraper_class': 'DenverScraper',
        'base_url': 'https://www.denvergov.org/permits',
        'residential_only': True,
        'fields_mapping': {
            'permit_num': 'PERMIT_NUM',
            'address': 'ADDRESS',
            'contractor_name': 'CONTRACTOR_NAME',
            'valuation': 'VALUATION',
            'date_issued': 'DATE_ISSUED',
            'neighborhood': 'NEIGHBORHOOD'
        }
    },
    'austin': {
        'display_name': 'Austin, TX',
        'timezone': 'America/Chicago',
        'scraper_class': 'AustinScraper',
        'base_url': 'https://www.austintexas.gov/permits',
        'residential_only': True,
        'fields_mapping': {
            'permit_num': 'permit_number',
            'address': 'address',
            'contractor_name': 'contractor',
            'valuation': 'valuation',
            'date_issued': 'issued_date',
            'neighborhood': 'district'
        }
    },
    'chicago': {
        'display_name': 'Chicago, IL',
        'timezone': 'America/Chicago',
        'scraper_class': 'ChicagoScraper',
        'base_url': 'https://data.cityofchicago.org/permits',
        'residential_only': True,
        'fields_mapping': {
            'permit_num': 'permit_',
            'address': 'address',
            'contractor_name': 'contractor_name',
            'valuation': 'estimated_cost',
            'date_issued': 'issue_date',
            'neighborhood': 'community_area'
        }
    }
}
