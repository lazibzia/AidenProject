from .scraper import BaseScraper
from typing import Dict, List, Any
import requests
import os
from datetime import datetime
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sqlite3
import csv
from io import StringIO

class AustinScraper(BaseScraper):
    def __init__(self, headless=True):
        # API configuration
        self.base_url = "https://data.austintexas.gov/resource/3syk-w9eu.json"
        self.app_token = os.getenv("AUSTIN_DATA_TOKEN")  # Get from environment
        
        # ABC Portal configuration
        self.headless = headless
        self.driver = None
        self.search_url = "https://abc.austintexas.gov/citizenportal/app/public-search"
        self.debug_counter = 0
        
        # Create debug directory
        if not os.path.exists("debug_screenshots"):
            os.makedirs("debug_screenshots")
        
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
        """
        Scrape permits using both API and ABC portal methods
        """
        all_permits = []
        
        # Method 1: Try API scraping first (faster)
        print("🔄 Attempting API scraping...")
        api_permits = self._scrape_via_api(start_date, end_date)
        if api_permits:
            print(f"✅ API scraping successful: {len(api_permits)} permits")
            all_permits.extend(api_permits)
        
        # Method 2: Try ABC portal scraping as additional source (not just fallback)
        print("🔄 Attempting ABC portal scraping for additional data...")
        portal_permits = self._scrape_via_abc_portal(start_date, end_date)
        if portal_permits:
            print(f"✅ ABC portal scraping successful: {len(portal_permits)} permits")
            all_permits.extend(portal_permits)
        
        if not all_permits:
            print("❌ Both API and ABC portal scraping failed")
        
        print(f"🎯 Total Austin permits scraped: {len(all_permits)}")
        return all_permits

    def _scrape_via_api(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Original API scraping method"""
        try:
            # Format dates properly for the API
            start_dt = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m-%dT00:00:00")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y-%m-%dT23:59:59")

            all_permits = []
            
            # 1. Scrape ISSUED permits
            issued_params = {
                "$where": f"issue_date >= '{start_dt}' AND issue_date <= '{end_dt}'",
                "$limit": 500000000000,
                "$order": "issue_date DESC",
                "$select": ",".join([
                    "permit_number",
                    "permit_type_desc",
                    "description",
                    "applieddate",
                    "issue_date",
                    "status_current",
                    "applicant_full_name",
                    "contractor_full_name",
                    "contractor_company_name",
                    "contractor_phone",
                    "permit_class",
                    "work_class"
                ])
            }

            headers = {
                "Accept": "application/json",
                "X-App-Token": self.app_token
            }

            print(f"Fetching Austin ISSUED permits from {start_date} to {end_date}")
            issued_response = requests.get(
                self.base_url,
                params=issued_params,
                headers=headers,
                timeout=30000
            )
            issued_response.raise_for_status()
            
            issued_data = issued_response.json()
            print(f"✅ Received {len(issued_data)} issued permits from Austin API")
            
            # Add status indicator for issued permits
            for permit in issued_data:
                permit['permit_status_type'] = 'issued'
            all_permits.extend(issued_data)

            # 2. Scrape PENDING permits
            pending_params = {
                "$where": f"applieddate >= '{start_dt}' AND applieddate <= '{end_dt}' AND status_current = 'Pending'",
                "$limit": 500000000000,
                "$order": "applieddate DESC",
                "$select": ",".join([
                    "permit_number",
                    "permit_type_desc",
                    "description",
                    "applieddate",
                    "issue_date",
                    "status_current",
                    "applicant_full_name",
                    "contractor_full_name",
                    "contractor_company_name",
                    "contractor_phone",
                    "permit_class",
                    "work_class"
                ])
            }

            print(f"Fetching Austin PENDING permits from {start_date} to {end_date}")
            pending_response = requests.get(
                self.base_url,
                params=pending_params,
                headers=headers,
                timeout=30000
            )
            pending_response.raise_for_status()
            
            pending_data = pending_response.json()
            print(f"✅ Received {len(pending_data)} pending permits from Austin API")
            
            # Add status indicator for pending permits
            for permit in pending_data:
                permit['permit_status_type'] = 'pending'
            all_permits.extend(pending_data)

            return all_permits

        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error ({e.response.status_code}): {e.response.text}")
            return []
        except Exception as e:
            print(f"❌ API scraping error: {str(e)}")
            return []

    def _scrape_via_abc_portal(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """ABC portal scraping method"""
        try:
            if not self._setup_driver():
                print("❌ Failed to setup Chrome driver")
                return []
            
            # Run the step-by-step automation
            success = self._run_abc_automation()
            
            if not success:
                print("❌ ABC portal automation failed")
                return []
            
            # Read the downloaded CSV and convert to permit format
            permits = self._read_downloaded_csv()
            
            return permits
            
        except Exception as e:
            print(f"❌ ABC portal scraping error: {str(e)}")
            return []
        finally:
            self._close_driver()

    def _setup_driver(self):
        """Setup Chrome WebDriver"""
        try:
            chrome_options = Options()
            
            if self.headless:
                chrome_options.add_argument("--headless")
            
            # Essential arguments for stability
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--disable-extensions")
            
            # User agent
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            
            # Disable automation indicators
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                
                # Set timeouts
                self.driver.implicitly_wait(5)
                self.driver.set_page_load_timeout(30000)
                
                print("✅ Chrome WebDriver initialized successfully")
                return True
                
            except Exception as chrome_error:
                print(f"❌ Chrome WebDriver failed: {chrome_error}")
                print("💡 Make sure ChromeDriver is installed and in PATH")
                print("💡 You can download ChromeDriver from: https://chromedriver.chromium.org/")
                return False
                
        except Exception as e:
            print(f"❌ Failed to setup Chrome WebDriver: {e}")
            return False

    def _run_abc_automation(self):
        """Run the ABC portal automation steps"""
        try:
            print("🚀 Starting ABC portal automation...")
            
            # Step 1: Navigate to website
            if not self._navigate_to_website():
                return False
            
            # Step 2: Click property tab
            if not self._click_property_tab():
                return False
            
            # Step 3: Set date range (NEW)
            if not self._set_date_range():
                print("⚠️ Could not set date range, continuing with default search...")
            
            # Step 4: Click search button
            if not self._click_search_button():
                return False
            
            # Step 5: Export and download CSV
            if not self._export_and_download_csv():
                return False
            
            print("✅ ABC portal automation completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ ABC automation error: {e}")
            return False

    def _set_date_range(self):
        """Set the date range for the search"""
        try:
            print("📅 Setting date range...")
            
            # Look for date input fields
            date_selectors = [
                "//input[@type='date']",
                "//input[contains(@placeholder, 'date')]",
                "//input[contains(@name, 'date')]",
                "//input[contains(@id, 'date')]"
            ]
            
            date_inputs = []
            for selector in date_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            date_inputs.append(elem)
                except:
                    continue
            
            if len(date_inputs) >= 2:
                # Try to set start and end dates
                start_date_input = date_inputs[0]
                end_date_input = date_inputs[1]
                
                # Clear and set start date
                start_date_input.clear()
                start_date_input.send_keys("2025-01-01")  # Use a broader date range
                print("✅ Set start date: 2025-01-01")
                
                # Clear and set end date
                end_date_input.clear()
                end_date_input.send_keys("2025-12-31")  # Use a broader date range
                print("✅ Set end date: 2025-12-31")
                
                return True
            else:
                print(f"⚠️ Found {len(date_inputs)} date inputs, expected 2")
                return False
                
        except Exception as e:
            print(f"❌ Error setting date range: {e}")
            return False

    def _navigate_to_website(self):
        """Navigate to the ABC portal website"""
        try:
            print(f"🌐 Navigating to: {self.search_url}")
            self.driver.get(self.search_url)
            time.sleep(10)
            
            current_url = self.driver.current_url
            print(f"📍 Current URL: {current_url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Navigation error: {e}")
            return False

    def _click_property_tab(self):
        """Click on the Property tab"""
        try:
            print("🎯 Looking for Property tab...")
            
            selectors_to_try = [
                "//a[contains(text(), 'Property / Project Name / Types / Date Range')]",
                "//a[@class='nav-link' and contains(text(), 'Property')]",
                "//a[contains(text(), 'Property')]"
            ]
            
            property_tab = None
            for i, selector in enumerate(selectors_to_try):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed():
                            property_tab = elem
                            print(f"✅ Found property tab using selector {i+1}")
                            break
                    if property_tab:
                        break
                except:
                    continue
            
            if not property_tab:
                print("❌ Could not find property tab")
                return False
            
            # Scroll and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", property_tab)
            time.sleep(2)
            self.driver.execute_script("arguments[0].click();", property_tab)
            time.sleep(5)
            
            print("✅ Property tab clicked successfully")
            return True
            
        except Exception as e:
            print(f"❌ Property tab click error: {e}")
            return False

    def _click_search_button(self):
        """Click the search button"""
        try:
            print("⏳ Waiting for search form to load...")
            time.sleep(8)
            
            print("🔍 Looking for Search button...")
            
            search_selectors = [
                "//button[contains(text(), 'Search')]",
                "//button[@class='btn btn-primary btn-fill pull-right']",
                "//input[@type='submit']",
                "//button[contains(@class, 'btn-primary')]"
            ]
            
            search_button = None
            for i, selector in enumerate(search_selectors):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            search_button = elem
                            print(f"✅ Found search button using selector {i+1}")
                            break
                    if search_button:
                        break
                except:
                    continue
            
            if not search_button:
                print("❌ Could not find search button")
                return False
            
            # Scroll and click
            self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
            time.sleep(2)
            self.driver.execute_script("arguments[0].click();", search_button)
            time.sleep(10)
            
            print("✅ Search button clicked successfully")
            return True
            
        except Exception as e:
            print(f"❌ Search button click error: {e}")
            return False

    def _export_and_download_csv(self):
        """Export results and download CSV file"""
        try:
            print("⏳ Waiting for search results to load...")
            time.sleep(15)
            
            print("🔍 Looking for Export/Download button...")
            
            export_selectors = [
                "//button[contains(text(), 'Export')]",
                "//button[contains(text(), 'Download')]",
                "//button[contains(text(), 'CSV')]",
                "//a[contains(text(), 'Export')]",
                "//a[contains(text(), 'Download')]",
                "//a[contains(text(), 'CSV')]",
                "//input[@value='Export']",
                "//input[@value='Download']",
                "//*[contains(@class, 'export')]",
                "//*[contains(@class, 'download')]"
            ]
            
            export_button = None
            for i, selector in enumerate(export_selectors):
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for elem in elements:
                        if elem.is_displayed() and elem.is_enabled():
                            export_button = elem
                            print(f"✅ Found export button using selector {i+1}")
                            break
                    if export_button:
                        break
                except:
                    continue
            
            if not export_button:
                print("❌ Could not find export button")
                return False
            
            # Get download directory
            download_dir = os.path.expanduser("~/Downloads")
            files_before = os.listdir(download_dir)
            csv_files_before = [f for f in files_before if f.endswith('.csv')]
            
            # Click export button
            self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
            time.sleep(2)
            self.driver.execute_script("arguments[0].click();", export_button)
            
            # Wait for download
            print("⏳ Waiting for download to complete...")
            max_wait = 60
            downloaded_file = None
            
            for wait_time in range(0, max_wait, 5):
                try:
                    files_after = os.listdir(download_dir)
                    csv_files_after = [f for f in files_after if f.endswith('.csv')]
                    new_csv_files = [f for f in csv_files_after if f not in csv_files_before]
                    
                    if new_csv_files:
                        downloaded_file = new_csv_files[0]
                        print(f"✅ Found new CSV file: {downloaded_file}")
                        break
                    
                    time.sleep(5)
                    
                except Exception as e:
                    print(f"Error checking files: {e}")
                    time.sleep(5)
            
            if not downloaded_file:
                print("❌ No new CSV file found")
                return False
            
            print("✅ CSV download completed successfully")
            return True
            
        except Exception as e:
            print(f"❌ Export/download error: {e}")
            return False

    def _read_downloaded_csv(self):
        """Read the downloaded CSV and convert to permit format"""
        try:
            download_dir = os.path.expanduser("~/Downloads")
            
            # Find the most recent CSV file
            csv_files = [f for f in os.listdir(download_dir) if f.endswith('.csv')]
            if not csv_files:
                print("❌ No CSV files found in Downloads directory")
                return []
            
            # Sort by modification time
            csv_files_with_time = []
            for csv_file in csv_files:
                file_path = os.path.join(download_dir, csv_file)
                mod_time = os.path.getmtime(file_path)
                csv_files_with_time.append((csv_file, mod_time, file_path))
            
            csv_files_with_time.sort(key=lambda x: x[1], reverse=True)
            most_recent_csv = csv_files_with_time[0]
            csv_file_path = most_recent_csv[2]
            
            print(f"📁 Reading CSV file: {most_recent_csv[0]}")
            
            # Read CSV with different encodings
            encodings_to_try = ['utf-8', 'latin-1', 'cp1252']
            csv_data = None
            
            for encoding in encodings_to_try:
                try:
                    with open(csv_file_path, 'r', encoding=encoding) as f:
                        csv_data = f.read()
                    print(f"✅ Successfully read CSV with {encoding} encoding")
                    break
                except UnicodeDecodeError:
                    continue
            
            if not csv_data:
                print("❌ Failed to read CSV with any encoding")
                return []
            
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(csv_data))
            headers = csv_reader.fieldnames
            rows = list(csv_reader)
            
            print(f"📊 CSV contains {len(rows)} rows with headers: {headers}")
            
            # Flexible column mapping
            column_mapping = {
                'permit_number': ['\ufeffPermit/Case', 'Permit/Case', 'Permit Number', 'permit_number', 'Permit #', 'ID', 'id', 'Permit ID'],
                'permit_type_desc': ['Sub Type / Work Type', 'Permit Type', 'permit_type', 'Type', 'type', 'Permit Type Desc'],
                'description': ['Description', 'description', 'Project Description', 'project_description', 'Comments'],
                'applieddate': ['Applied Date', 'applied_date', 'Application Date', 'Date Applied'],
                'issue_date': ['Issued Date', 'issue_date', 'Date Issued', 'Issue Date'],
                'status_current': ['Status', 'status', 'Current Status', 'Permit Status'],
                'applicant_full_name': ['Project Name', 'Applicant Name', 'applicant_name', 'Applicant', 'Owner Name'],
                'contractor_full_name': ['Contractor Name', 'contractor_name', 'Contractor', 'Contractor Full Name'],
                'contractor_company_name': ['Contractor Company', 'contractor_company', 'Company Name', 'Business Name'],
                'contractor_phone': ['Contractor Phone', 'contractor_phone', 'Phone', 'Contact Phone'],
                'permit_class': ['Sub Type / Work Type', 'Permit Class', 'permit_class', 'Class', 'Category'],
                'work_class': ['Sub Type / Work Type', 'Work Class', 'work_class', 'Work Type', 'Work Category']
            }
            
            # Convert to permit format
            permits = []
            for row in rows:
                try:
                    # Map CSV columns to permit format using flexible mapping
                    permit = {}
                    
                    for field, possible_names in column_mapping.items():
                        value = ""
                        for name in possible_names:
                            if name in row and row[name]:
                                value = row[name]
                                break
                        permit[field] = value
                    
                    # Add status type
                    permit["permit_status_type"] = "pending"  # ABC portal data is typically pending
                    
                    # Only add if we have a permit number
                    if permit["permit_number"]:
                        permits.append(permit)
                        
                except Exception as e:
                    print(f"⚠️ Error processing row: {e}")
                    continue
            
            print(f"✅ Converted {len(permits)} permits from CSV")
            return permits
            
        except Exception as e:
            print(f"❌ Error reading CSV: {e}")
            return []

    def _close_driver(self):
        """Close the browser driver"""
        if self.driver:
            try:
                self.driver.quit()
                print("🔒 Browser driver closed")
            except Exception as e:
                print(f"⚠️ Error closing browser: {e}")

    def validate_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and format scraped data"""
        validated = []
        for permit in data:
            try:
                if not permit.get("permit_number"):
                    continue

                # Optional: process all permit classes or specific ones
                    allowed_classes = ["residential", "commercial", "building", "mechanical", "plumbing", "electrical", "demolition"]

                    permit_class = permit.get("permit_class", "").lower()
                    if permit_class not in [cls.lower() for cls in allowed_classes]:
                       continue

                validated.append({
                    "Permit Num": permit.get("permit_number"),
                    "Permit Type Desc": permit.get("permit_type_desc", ""),
                    "Description": permit.get("description", ""),
                    "Applied Date": permit.get("applieddate", "")[:10] if permit.get("applieddate") else "",
                    "Issued Date": permit.get("issue_date", "")[:10] if permit.get("issue_date") else "",
                    "current_status": permit.get("status_current", ""),
                    "Applicant Name": permit.get("applicant_full_name", ""),
                    "Contractor Name": permit.get("contractor_full_name", ""),
                    "Contractor Company Name": permit.get("contractor_company_name", ""),
                    "Contractor Phone": permit.get("contractor_phone", ""),
                    "Work Class": permit.get("work_class", ""),
                    "Permit Class Mapped": self.permit_class_mapping.get(
                        permit.get("permit_class", ""), 
                        permit.get("permit_class", "")
                    ),
                    "Permit Status Type": permit.get("permit_status_type", "issued")
                })

            except Exception as e:
                print(f"⚠️ Error validating permit: {str(e)}")
                continue

        print(f"Validated {len(validated)} permits")
        return validated