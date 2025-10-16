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
            'permit_type': 'PERMIT_TYPE',
            'description': 'DESCRIPTION',
            'applied_date': 'APPLICATION_DATE',
            'issued_date': 'DATE_ISSUED',
            'current_status': 'STATUS',
            'applicant_name': 'APPLICANT_NAME',
            'contractor_name': 'CONTRACTOR_NAME',
            'contractor_company_name': 'CONTRACTOR_COMPANY',
            'contractor_phone': 'CONTRACTOR_PHONE',
            'work_class': 'WORK_CLASS',
            'permit_class_mapped': 'PERMIT_CLASS_MAPPED'
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
            'permit_type': 'permit_type_desc',
            'description': 'description',
            'applied_date': 'applieddate',
            'issued_date': 'issue_date',
            'current_status': 'status_current',
            'applicant_name': 'applicant_full_name',
            'contractor_name': 'contractor_full_name',
            'contractor_company_name': 'contractor_company_name',
            'contractor_phone': 'contractor_phone',
            'work_class': 'work_class',
            'permit_class_mapped': 'permit_class_mapped'
        }
    },
    
}
