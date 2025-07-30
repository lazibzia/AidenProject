from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
import os
import time
import logging
from collections import defaultdict
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)  # Fixed: Correct Python special variable

app = FastAPI(
    title="Permit Email API",
    description="API for sending permit emails to clients with equal distribution",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Configuration - Consider using environment variables for production
PERMITS_DB_PATH = 'C:\\Users\\Sheikh Daniyal Ahmed\\Desktop\\New folder (15)\\Email backend\\permits.db'
CLIENTS_DB_PATH = 'C:\\Users\\Sheikh Daniyal Ahmed\\Desktop\\New folder (15)\\Aiden full Project\\Client backend\\database.db'
GMAIL_USER = 'rajalazibzia32@gmail.com'
GMAIL_PASSWORD = 'mxar qjrh dobm stfq'  # REMOVE BEFORE COMMITTING TO GIT

# Pydantic models for request/response
class EmailRequest(BaseModel):
    days_back: Optional[int] = 1
    dry_run: Optional[bool] = False

class EmailResponse(BaseModel):
    success: bool
    message: str
    summary: Dict[str, Any]
    performance: Dict[str, float]
    timestamp: str

class PreviewResponse(BaseModel):
    success: bool
    preview: Dict[str, Any]


class EmailService:
    def __init__(self):
        self.permits_db_path = PERMITS_DB_PATH
        self.clients_db_path = CLIENTS_DB_PATH
        self.gmail_user = GMAIL_USER
        self.gmail_password = GMAIL_PASSWORD

    def get_permits_db_connection(self):
        """Connect to permits database"""
        if not os.path.exists(self.permits_db_path):
            logger.error(f"Permits database not found: {self.permits_db_path}")
            return None
        return sqlite3.connect(self.permits_db_path)

    def get_clients_db_connection(self):
        """Connect to clients database"""
        if not os.path.exists(self.clients_db_path):
            logger.error(f"Clients database not found: {self.clients_db_path}")
            return None
        return sqlite3.connect(self.clients_db_path)

    def normalize_permit_type(self, permit_type):
        """Normalize permit types to match between permits and clients databases"""
        if not permit_type:
            return None

        # Mapping from permits database to clients database format
        permit_type_mapping = {
            'Electrical Permit': 'Electrical Permit',
            'Mechanical Permit': 'Mechanical Permit',
            'Plumbing Permit': 'plumbing',  # Your client DB uses lowercase
            'Building Permit': 'Building Permit',
            'ALTERATION/TENANT FINISH': 'ALTERATION/TENANT FINISH',
            'NEW BUILDING': 'NEW BUILDING',
            'ADDITION': 'ADDITION',
            'REPAIR/REPLACE': 'REPAIR/REPLACE',
        }

        return permit_type_mapping.get(permit_type, permit_type)

    def get_clients_by_permit_type(self):
        """Fetch clients grouped by permit type"""
        conn = self.get_clients_db_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            query = '''
                SELECT name, email, permit_type
                FROM client
                WHERE email IS NOT NULL AND email != ''
                ORDER BY permit_type, name
            '''
            cursor.execute(query)
            clients = cursor.fetchall()

            # Group clients by permit type
            clients_by_type = defaultdict(list)
            for name, email, permit_type in clients:
                clients_by_type[permit_type].append({
                    'name': name,
                    'email': email,
                    'permit_type': permit_type
                })

            logger.info(f"Retrieved {len(clients)} clients across {len(clients_by_type)} permit types")
            logger.info(f"Client permit types: {list(clients_by_type.keys())}")
            return dict(clients_by_type)

        except Exception as e:
            logger.error(f"Error loading clients: {e}")
            return {}
        finally:
            conn.close()

    def get_permits_by_type(self, days_back=1):
        """Fetch permits grouped by permit type - FIXED for your historical data"""
        conn = self.get_permits_db_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()

            # Since your data is historical (2002-2017), get the most recent permits
            # You can adjust LIMIT based on how many permits you want to distribute daily
            query = '''
                SELECT
                    permit_num,
                    permit_type,
                    description,
                    contractor_name,
                    contractor_address,
                    city,
                    issued_date,
                    applied_date,
                    current_status
                FROM permits
                WHERE permit_type IS NOT NULL 
                AND permit_type != 'None'
                ORDER BY issued_date DESC, id DESC
                LIMIT 200
            '''

            cursor.execute(query)
            permits = cursor.fetchall()

            # Group permits by normalized permit type
            permits_by_type = defaultdict(list)

            for permit in permits:
                original_permit_type = permit[1]
                normalized_type = self.normalize_permit_type(original_permit_type)

                # Only include permits that have matching clients
                if normalized_type:
                    permits_by_type[normalized_type].append(permit)

            logger.info(f"Retrieved {len(permits)} total permits")
            logger.info(
                f"Grouped into {len(permits_by_type)} permit types: {dict((k, len(v)) for k, v in permits_by_type.items())}")

            return dict(permits_by_type)

        except Exception as e:
            logger.error(f"Error loading permits: {e}")
            return {}
        finally:
            conn.close()

    def distribute_permits_equally(self, permits_list, clients_list):
        """Distribute permits equally among clients"""
        if not clients_list or not permits_list:
            return {}

        num_clients = len(clients_list)
        permits_per_client = len(permits_list) // num_clients
        extra_permits = len(permits_list) % num_clients

        distribution = {}
        start_idx = 0

        for i, client in enumerate(clients_list):
            # Some clients get one extra permit if there's a remainder
            permits_count = permits_per_client + (1 if i < extra_permits else 0)
            end_idx = start_idx + permits_count

            distribution[client['email']] = {
                'client': client,
                'permits': permits_list[start_idx:end_idx]
            }
            start_idx = end_idx

        logger.info(f"Distributed {len(permits_list)} permits among {num_clients} clients")
        return distribution

    def format_permits_html(self, permits):
        """Format permits as HTML table"""
        if not permits:
            return '<p>No permits assigned to you in this batch.</p>'

        headers = [
            'Permit Number', 'Permit Type', 'Description', 
            'Contractor Name', 'Contractor Address', 'City','Issued Date', 'Applied Date', 'Status'
        ]

        html = '''
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; font-family: Arial, sans-serif;">
            <thead style="background-color: #f2f2f2;">
        '''
        html += '<tr>' + ''.join(f'<th style="text-align: left; padding: 8px;">{h}</th>' for h in headers) + '</tr>'
        html += '</thead><tbody>'

        for i, row in enumerate(permits):
            bg_color = '#f9f9f9' if i % 2 == 0 else '#ffffff'
            html += f'<tr style="background-color: {bg_color};">'
            for col in row:
                html += f'<td style="padding: 8px; border: 1px solid #ddd;">{col if col else "N/A"}</td>'
            html += '</tr>'

        html += '</tbody></table>'
        return html

    def send_email_to_client(self, server, client_data, permits):
        """Send email to a single client"""
        client = client_data['client']
        assigned_permits = client_data['permits']

        # Get unique cities from permits
        cities = {p[5] for p in assigned_permits if len(p) > 5 and p[5]}  # city is at index 5
        city_str = ', '.join(cities) if cities else 'Multiple Cities'

        # Create email content
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2 style="color: #333;">Daily Permit Leads - {client['permit_type']}</h2>
            <p>Hello {client['name']},</p>
            <p>You have been assigned <strong>{len(assigned_permits)} permit(s)</strong> of type "{client['permit_type']}" from our database:</p>
            {self.format_permits_html(assigned_permits)}
            <hr style="margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                <strong>Note:</strong> This data is from our historical permit database (2002-2017). 
                This is a demonstration of the permit distribution system.
            </p>
            <p>Best regards,<br>Your Permit Distribution System</p>
        </div>
        """

        # Send email
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = client['email']
        msg[
            'Subject'] = f"Permit Leads - {client['permit_type']} ({len(assigned_permits)} permits) - {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(body, 'html'))

        logger.info(f"Sending email to {client['email']} with {len(assigned_permits)} permits")
        server.send_message(msg)

    def send_bulk_emails(self, distribution_data, dry_run=False):
        """Send emails to all clients with their assigned permits"""

        if dry_run:
            logger.info("DRY RUN MODE - No emails will be sent")
            return {
                'success_count': len(distribution_data),
                'fail_count': 0,
                'dry_run': True,
                'details': {email: len(data['permits']) for email, data in distribution_data.items()}
            }

        if not distribution_data:
            logger.warning("No distribution data provided")
            return {'success_count': 0, 'fail_count': 0, 'results': {}}

        success_count = 0
        fail_count = 0
        results = {}

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_password)

                for email, client_data in distribution_data.items():
                    try:
                        self.send_email_to_client(server, client_data, client_data['permits'])
                        logger.info(f"✅ Email sent to {email}")
                        success_count += 1
                        results[email] = {
                            'status': 'success',
                            'permits_count': len(client_data['permits'])
                        }

                        # Small delay between emails to avoid being flagged as spam
                        time.sleep(1)

                    except Exception as e:
                        logger.error(f"❌ Failed to send email to {email}: {e}")
                        fail_count += 1
                        results[email] = {
                            'status': 'failed',
                            'error': str(e)
                        }

        except Exception as e:
            logger.error(f"❌ SMTP connection error: {e}")
            return {
                'success_count': 0,
                'fail_count': len(distribution_data),
                'error': str(e)
            }

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        }

# Initialize email service
email_service = EmailService()

@app.post("/api/send-all-emails", response_model=EmailResponse)
async def send_all_emails():
    """
    Simple endpoint to send emails to ALL clients - Perfect for frontend button

    This endpoint:
    1. Gets all clients grouped by permit type
    2. Gets all recent permits grouped by permit type
    3. Distributes permits equally among clients of same type
    4. Sends emails to everyone

    No request body needed - just click and send!
    """
    try:
        start_time = time.time()

        logger.info("🚀 Send All Emails button clicked - Starting process...")

        # Get clients grouped by permit type
        clients_by_type = email_service.get_clients_by_permit_type()
        if not clients_by_type:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': 'No clients found in database',
                    'message': 'Please check your client database connection'
                }
            )

        # Get permits from last 24 hours grouped by permit type
        permits_by_type = email_service.get_permits_by_type(days_back=1)
        print("****************************************#")
        print(f"Permits grouped by type: { {k: len(v) for k, v in permits_by_type.items()} }")
        # Process and distribute permits for each permit type
        all_distributions = {}
        summary = {
            'permit_types_processed': 0,
            'total_clients': 0,
            'total_permits_found': 0,
            'emails_to_send': 0
        }

        for permit_type in clients_by_type.keys():
            clients = clients_by_type[permit_type]
            permits = permits_by_type.get(permit_type, [])

            # Distribute permits equally among clients of this type
            distribution = email_service.distribute_permits_equally(permits, clients)
            all_distributions.update(distribution)

            # Update summary
            summary['permit_types_processed'] += 1
            summary['total_clients'] += len(clients)
            summary['total_permits_found'] += len(permits)
            summary['emails_to_send'] += len(clients)

            logger.info(f"✓ Processed {permit_type}: {len(clients)} clients, {len(permits)} permits")

        # Send emails to everyone
        logger.info(f"📧 Sending emails to {summary['emails_to_send']} clients...")
        email_results = email_service.send_bulk_emails(all_distributions, dry_run=False)

        # Calculate performance metrics
        end_time = time.time()
        total_time = end_time - start_time

        # Prepare response
        response_data = {
            'success': True,
            'message': f"Successfully processed {summary['emails_to_send']} clients across {summary['permit_types_processed']} permit types",
            'summary': {
                'clients_emailed': summary['emails_to_send'],
                'permit_types': summary['permit_types_processed'],
                'total_permits_distributed': summary['total_permits_found'],
                'successful_emails': email_results['success_count'],
                'failed_emails': email_results['fail_count']
            },
            'performance': {
                'total_time_seconds': round(total_time, 2),
                'emails_per_second': round(email_results['success_count'] / total_time, 2) if total_time > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

        print("API Response:", response_data)  # Print response to console
        # Log final results
        logger.info(f"✅ Email sending completed!")
        logger.info(f"✅ Success: {email_results['success_count']} emails")
        logger.info(f"❌ Failed: {email_results['fail_count']} emails")
        logger.info(f"⏱ Total time: {total_time:.2f} seconds")

        return EmailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Send All Emails error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e),
                'message': 'Failed to send emails. Please check logs and database connections.'
            }
        )

@app.post("/api/send-emails", response_model=EmailResponse)
async def send_emails(request: EmailRequest):
    """
    Send emails to clients with permits distributed equally by permit type

    Request body:
    {
        "days_back": 1,  // Optional: days to look back for permits (default: 1)
        "dry_run": false  // Optional: if true, don't actually send emails
    }
    """
    try:
        start_time = time.time()

        logger.info(f"Starting email sending process (days_back: {request.days_back}, dry_run: {request.dry_run})")

        # Get clients grouped by permit type
        clients_by_type = email_service.get_clients_by_permit_type()
        if not clients_by_type:
            raise HTTPException(
                status_code=400,
                detail={
                    'success': False,
                    'error': 'No clients found in database'
                }
            )

        # Get permits grouped by permit type
        permits_by_type = email_service.get_permits_by_type(request.days_back)

        # Process each permit type
        all_distributions = {}
        summary = {
            'permit_types_processed': 0,
            'total_clients': 0,
            'total_permits': 0,
            'distributions': {}
        }

        for permit_type in clients_by_type.keys():
            clients = clients_by_type[permit_type]
            permits = permits_by_type.get(permit_type, [])

            # Distribute permits equally among clients of this type
            distribution = email_service.distribute_permits_equally(permits, clients)
            all_distributions.update(distribution)

            summary['permit_types_processed'] += 1
            summary['total_clients'] += len(clients)
            summary['total_permits'] += len(permits)
            summary['distributions'][permit_type] = {
                'clients_count': len(clients),
                'permits_count': len(permits),
                'permits_per_client': len(permits) // len(clients) if clients else 0
            }

        # Send emails
        email_results = email_service.send_bulk_emails(all_distributions, request.dry_run)

        # Calculate performance
        end_time = time.time()
        total_time = end_time - start_time

        response_data = {
            'success': True,
            'message': f"Processed {summary['total_clients']} clients across {summary['permit_types_processed']} permit types",
            'summary': {
                **summary,
                'email_results': email_results
            },
            'performance': {
                'total_time_seconds': round(total_time, 2),
                'emails_per_second': round(email_results['success_count'] / total_time, 2) if total_time > 0 else 0
            },
            'timestamp': datetime.now().isoformat()
        }

        print("API Response:", response_data)  # Print response to console
        return EmailResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e)
            }
        )

@app.get("/api/preview", response_model=PreviewResponse)
async def preview_distribution(days_back: int = 1):
    """
    Preview how permits would be distributed without sending emails
    """
    try:
        # Get clients and permits
        clients_by_type = email_service.get_clients_by_permit_type()
        permits_by_type = email_service.get_permits_by_type(days_back)

        preview = {}

        for permit_type in clients_by_type.keys():
            clients = clients_by_type[permit_type]
            permits = permits_by_type.get(permit_type, [])

            distribution = email_service.distribute_permits_equally(permits, clients)

            preview[permit_type] = {
                'total_clients': len(clients),
                'total_permits': len(permits),
                'permits_per_client': len(permits) // len(clients) if clients else 0,
                'clients': [
                    {
                        'name': data['client']['name'],
                        'email': data['client']['email'],
                        'assigned_permits': len(data['permits'])
                    }
                    for email, data in distribution.items()
                ]
            }

        print("API Preview Response:", preview)  # Print preview to console
        return PreviewResponse(
            success=True,
            preview=preview
        )

    except Exception as e:
        logger.error(f"Preview error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                'success': False,
                'error': str(e)
            }
        )

if __name__ == '__main__':  # Fixed: Correct Python main block syntax
    print("🚀 Starting Permit Email FastAPI Server...")
    print("📊 Available endpoints:")
    print("  POST /api/send-all-emails - 🔥 SEND EMAILS TO ALL CLIENTS (for your button)")
    print("  POST /api/send-emails     - Send emails with custom options")
    print("  GET  /api/preview         - Preview distribution without sending")
    print("\n🔥 FOR YOUR FRONTEND BUTTON:")
    print("  Just call: POST http://localhost:8000/api/send-all-emails")
    print("  No request body needed - it handles everything automatically!")
    print("\n📖 Example usage:")
    print("  Frontend Button: fetch('http://localhost:8000/api/send-all-emails', { method: 'POST' })")
    print("  Command Line: curl -X POST http://localhost:8000/api/send-all-emails")
    print("\n📚 Interactive API docs: http://localhost:8000/docs")

    uvicorn.run(app, host="127.0.0.1", port=5003)