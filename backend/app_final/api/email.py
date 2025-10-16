from fastapi import APIRouter, HTTPException
import time
from datetime import datetime
from app_final.services.email_service import EmailService
from app_final.models.email_models import EmailRequest, EmailResponse, PreviewResponse
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize email service
email_service = EmailService()


@router.post("/send-all-emails", response_model=EmailResponse)
async def send_all_emails():
    """
    Simple endpoint to send emails to ALL clients - Perfect for frontend button
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

        # Get permits grouped by permit type
        permits_by_type = email_service.get_permits_by_type(days_back=30)

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


@router.post("/send-emails", response_model=EmailResponse)
async def send_emails(request: EmailRequest):
    """Send emails to clients with permits distributed equally by permit type"""
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


@router.get("/preview", response_model=PreviewResponse)
async def preview_distribution(days_back: int = 1):
    """Preview how permits would be distributed without sending emails"""
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