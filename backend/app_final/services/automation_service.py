import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from app_final.database.db_manager import DatabaseManager
from app_final.scrapers.scraper import ScraperManager
from app_final.services.email_service import EmailService
from app_final.services.rag_service import RAGService
from app_final.models.rag_models import ClientRAGRequest, ClientSelection
from config.cities import CITY_CONFIGS

logger = logging.getLogger(__name__)


class AutomationService:
    def __init__(self):
        self.email_service = EmailService()
        self.rag_service = RAGService()

    async def automated_scrape_all(self):
        """Automated function to scrape all cities"""
        try:
            logger.info("🤖 AUTOMATED: Starting scrape-all process...")

            db_manager = DatabaseManager()
            scraper_manager = ScraperManager()

            results = {}

            for city_name in CITY_CONFIGS.keys():
                try:
                    # Use daily mode for automation (current day)
                    today = datetime.today().date()
                    # For Austin and Denver, widen to 30 days to avoid zero results
                    city_key = str(city_name).lower()
                    if city_key in {"austin", "denver"}:
                        start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
                        end_date = today.strftime('%Y-%m-%d')
                    else:
                        start_date = end_date = today.strftime('%Y-%m-%d')

                    # Scrape and insert
                    permits_data = scraper_manager.scrape_city(city_name, start_date, end_date)
                    inserted_count = db_manager.insert_permits(city_name, permits_data)

                    results[city_name] = {
                        "success": True,
                        "fetched": len(permits_data),
                        "inserted": inserted_count
                    }

                    logger.info(f"🤖 AUTOMATED: {city_name} - {inserted_count} new permits")

                except Exception as e:
                    logger.error(f"🤖 AUTOMATED: {city_name} failed - {e}")
                    results[city_name] = {
                        "success": False,
                        "error": str(e)
                    }

            logger.info(f"🤖 AUTOMATED: Scrape-all completed - {results}")
            return results

        except Exception as e:
            logger.error(f"🤖 AUTOMATED: Scrape-all process failed - {e}")
            return {"error": str(e)}

    async def automated_rag_reindex(self):
        """Automated function to rebuild RAG index - only for new permits"""
        try:
            logger.info("🤖 AUTOMATED: Starting incremental RAG reindex...")

            result = self.rag_service.incremental_reindex()
            logger.info(f"🤖 AUTOMATED: RAG reindex completed - {result}")
            return {"success": True, "summary": result}

        except Exception as e:
            logger.error(f"🤖 AUTOMATED: RAG reindex failed - {e}")
            return {"success": False, "error": str(e)}

    async def automated_distribute_send(self):
        """Automated function to distribute and send emails using RAG"""
        try:
            logger.info("🤖 AUTOMATED: Starting distribute and send...")

            # Create default request for automation
            auto_request = ClientRAGRequest(
                query=None,  # Use client preferences
                use_client_prefs=True,
                selection=ClientSelection(client_ids=None, status=None),
                filters=None,
                per_client_top_k=20,
                oversample=10,
                exclusive=True,
                dry_run=False  # Actually send emails in automation
            )

            #raw, final = self.rag_service.build_client_assignments(auto_request)
            raw, final = self.rag_service.build_client_assignments_dual(auto_request)

            # Filter out permits previously sent to each client
            final_new = self.email_service.filter_new_assignments(final)
            # Also require rows to have a contractor phone
            final_new = self.email_service.filter_assignments_requiring_phone(final_new)

            # If zero rows after dedupe, relax constraints and try again
            total_rows = sum(len(v["rows"]) for v in final_new.values())
            if total_rows == 0:
                logger.info("🤖 AUTOMATED: No new rows after dedupe. Relaxing search...")
                # Build a relaxed request: empty query, no exclusivity, larger top_k
                relaxed_req = ClientRAGRequest(
                    query="",
                    use_client_prefs=False,
                    selection=auto_request.selection,
                    filters=None,
                    per_client_top_k=50,
                    oversample=10,
                    exclusive=False,
                    dry_run=False
                )
                raw_relaxed, final_relaxed = self.rag_service.build_client_assignments_dual(relaxed_req)
                # Apply phone requirement on relaxed results
                final_new = self.email_service.filter_assignments_requiring_phone(final_relaxed)

            # Send emails for new/relaxed rows
            #results = self.email_service.send_dual_rag_emails_for_clients(final_new, dry_run=False)
            results = self.email_service.send_triple_rag_emails_for_clients(final_new, dry_run=False)

            # Record sent permits
            try:
                self.email_service.record_sent(final_new)
            except Exception as rec_err:
                logger.warning(f"🤖 AUTOMATED: record_sent failed - {rec_err}")

            summary = {
                "clients_processed": len(final_new),
                "dry_run": False,
                "exclusive": True,
                "total_rows": sum(len(v["rows"]) for v in final_new.values())
            }

            logger.info(f"🤖 AUTOMATED: Distribute and send completed - {results}")
            return {"success": True, "summary": summary, "results": results}

        except Exception as e:
            logger.error(f"🤖 AUTOMATED: Distribute and send failed - {e}")
            return {"success": False, "error": str(e)}


# Global automation service instance
automation_service = AutomationService()


def run_automated_workflow():
    """
    Main automation workflow that runs every 4 hours
    Executes: scrape-all -> rag-reindex -> distribute-send
    """
    try:
        logger.info("🤖 AUTOMATED WORKFLOW: Starting 4-hour automation cycle...")

        # Create new event loop for the background task
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            # Step 1: Scrape all cities
            logger.info("🤖 AUTOMATED WORKFLOW: Step 1 - Scraping all cities...")
            scrape_results = loop.run_until_complete(automation_service.automated_scrape_all())

            # Step 2: Rebuild RAG index
            logger.info("🤖 AUTOMATED WORKFLOW: Step 2 - Rebuilding RAG index...")
            reindex_results = loop.run_until_complete(automation_service.automated_rag_reindex())

            # Step 3: Distribute and send emails
            logger.info("🤖 AUTOMATED WORKFLOW: Step 3 - Distributing and sending emails...")
            distribute_results = loop.run_until_complete(automation_service.automated_distribute_send())

            # Log summary
            workflow_summary = {
                "timestamp": datetime.now().isoformat(),
                "scrape_results": scrape_results,
                "reindex_results": reindex_results,
                "distribute_results": distribute_results
            }

            logger.info(f"🤖 AUTOMATED WORKFLOW: Completed successfully! Summary: {workflow_summary}")

        finally:
            loop.close()

    except Exception as e:
        logger.error(f"🤖 AUTOMATED WORKFLOW: Failed - {e}")