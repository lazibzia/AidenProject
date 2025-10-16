from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from app_final.core.scheduler import scheduler
from app_final.services.automation_service import run_automated_workflow
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/automation/start")
async def start_automation():
    """Start the 4-hour automation cycle"""
    try:
        # Remove existing automation job if it exists
        try:
            scheduler.remove_job("automated_workflow")
        except:
            pass

        # Add new automation job - runs every 4 hours
        scheduler.add_job(
            run_automated_workflow,
            'interval',
            hours=4,
            id="automated_workflow",
            replace_existing=True,
            next_run_time=datetime.now() + timedelta(minutes=1)  # Start in 1 minute
        )

        logger.info("🤖 AUTOMATION: 4-hour automation cycle started")
        return {
            "success": True,
            "message": "4-hour automation cycle started. Next run in 1 minute, then every 4 hours.",
            "job_id": "automated_workflow",
            "interval": "4 hours"
        }

    except Exception as e:
        logger.error(f"🤖 AUTOMATION: Failed to start - {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start automation: {str(e)}")


@router.post("/automation/stop")
async def stop_automation():
    """Stop the 4-hour automation cycle"""
    try:
        scheduler.remove_job("automated_workflow")
        logger.info("🤖 AUTOMATION: 4-hour automation cycle stopped")
        return {
            "success": True,
            "message": "4-hour automation cycle stopped",
            "job_id": "automated_workflow"
        }
    except Exception as e:
        logger.error(f"🤖 AUTOMATION: Failed to stop - {e}")
        return {
            "success": False,
            "message": f"Failed to stop automation: {str(e)}"
        }


@router.get("/automation/status")
async def get_automation_status():
    """Get current automation status"""
    try:
        job = scheduler.get_job("automated_workflow")
        if job:
            return {
                "active": True,
                "job_id": job.id,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "interval": "4 hours",
                "message": "4-hour automation is running"
            }
        else:
            return {
                "active": False,
                "job_id": None,
                "next_run_time": None,
                "interval": None,
                "message": "4-hour automation is not running"
            }
    except Exception as e:
        logger.error(f"🤖 AUTOMATION: Status check failed - {e}")
        return {
            "active": False,
            "error": str(e),
            "message": "Error checking automation status"
        }


@router.post("/automation/run-now")
async def run_automation_now():
    """Manually trigger the automation workflow immediately"""
    try:
        logger.info("🤖 AUTOMATION: Manual trigger requested")

        # Run the workflow in background
        run_automated_workflow()

        return {
            "success": True,
            "message": "Automation workflow triggered manually. Check logs for progress.",
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"🤖 AUTOMATION: Manual trigger failed - {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger automation: {str(e)}")