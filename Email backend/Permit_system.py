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
PERMITS_DB_PATH = 'E:\Aiden full Project\Email backend\permits.db'
CLIENTS_DB_PATH = 'E:\Aiden full Project\Email backend\database_new.db'
GMAIL_USER = 'rajalazibzia32@gmail.com'
GMAIL_PASSWORD = 'mxar qjrh dobm stfq'  # REMOVE BEFORE COMMITTING TO GIT

# Pydantic models for request/response
class EmailRequest(BaseModel):
    days_back: Optional[int] = 30
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
    def __init__(self):  # Fixed: Correct constructor syntax
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
            return dict(clients_by_type)

        except Exception as e:
            logger.error(f"Error loading clients: {e}")
            return {}
        finally:
            conn.close()

    def get_permits_by_type(self, days_back=3650):
        """Fetch permits grouped by permit type"""
        conn = self.get_permits_db_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            # since = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d %H:%M:%S')
            since = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.000')

            query = '''
                SELECT
                    permit_num,
                    permit_type,
                    contractor_address,
                    description,
                    contractor_name,
                    city,
                    issued_date,
                    applied_date,
                    current_status
                FROM permits
                WHERE issued_date >= ?
                ORDER BY permit_type, issued_date DESC
            '''

            cursor.execute(query, (since,))
            permits = cursor.fetchall()

            # Group permits by permit type
            permits_by_type = defaultdict(list)
            for permit in permits:
                permit_type = permit[1]  # permit_type is at index 1
                permits_by_type[permit_type].append(permit)

            logger.info(f"Retrieved {len(permits)} permits across {len(permits_by_type)} permit types")
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

        return distribution

    def format_permits_html(self, permits):
        """Format permits as HTML table"""
        if not permits:
            return '<p>No new permits assigned to you.</p>'

        headers = [
            'Permit number', 'Permit Type', 'Issued Date', 'Address',
            'Description', 'Contractor Full Name', 'Contractor Phone',
             'Current Status', 'City'
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
        print("**********************************************************")
        client = client_data['client']
        assigned_permits = client_data['permits']

        # Get unique cities from permits
        cities = {p[8] for p in assigned_permits if len(p) > 8 and p[8]}
        city_str = ', '.join(cities) if cities else 'N/A'

        # Create email content
        if not assigned_permits:
            body = f"""
            <p>Hello {client['name']},</p>
            <p>No new permits of type "{client['permit_type']}" were found in the last 24 hours.</p>
            <p>Best regards,<br>Your Permit System</p>
            """
        else:
            body = f"""
            <p>Hello {client['name']},</p>
            <p>You have been assigned {len(assigned_permits)} new permit(s) of type "{client['permit_type']}":</p>
            {self.format_permits_html(assigned_permits)}
            <p>Best regards,<br>Your Permit System</p>
            """

        # Send email
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = client['email']
        msg['Subject'] = f"Daily Leads - {client['permit_type']}, {city_str}, {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(body, 'html'))

        logger.info(f"Sending email to {client['email']} with {len(assigned_permits)} permits")
        print(f"Sending email to {client['email']} with {len(assigned_permits)} permits")
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

        success_count = 0
        fail_count = 0
        results = {}

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                server.login(self.gmail_user, self.gmail_password)
                print("**********************************************************")
                print(distribution_data)
                for email, client_data in distribution_data.items():
                    try:
                        print("**********************************************************")
                        self.send_email_to_client(server, client_data, client_data['permits'])
                        logger.info(f"Email sent to {email}")
                        success_count += 1
                        results[email] = {
                            'status': 'success',
                            'permits_count': len(client_data['permits'])
                        }
                    except Exception as e:
                        logger.error(f"Failed to send email to {email}: {e}")
                        fail_count += 1
                        results[email] = {
                            'status': 'failed',
                            'error': str(e)
                        }

        except Exception as e:
            logger.error(f"SMTP connection error: {e}")
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
        permits_by_type = email_service.get_permits_by_type(days_back=30)
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

    uvicorn.run(app, host="127.0.0.1", port=5001)