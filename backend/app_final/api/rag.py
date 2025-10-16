from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
import logging
from app_final.services.rag_service import RAGService
from app_final.services.email_service import EmailService
from app_final.models.rag_models import (
    RAGSearchRequest, RAGSearchResponse, RAGStatusResponse,
    ClientRAGRequest, ClientRAGPreviewResponse, ClientRAGSendResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
rag_service = RAGService()
email_service = EmailService()


@router.post("/rag/reindex")
def rag_reindex():
    """Build the persistent RAG index from the entire permits table"""
    try:
        res = rag_service.build_index(full_reindex=True, batch_size=256)
        return {"success": True, "summary": res}
    except Exception as e:
        logger.error(f"RAG reindex error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/reindex-incremental")
def rag_reindex_incremental():
    """Incrementally rebuild RAG index for only new permits"""
    try:
        res = rag_service.incremental_reindex()
        return {"success": True, "summary": res}
    except Exception as e:
        logger.error(f"RAG incremental reindex error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.get("/rag/status", response_model=RAGStatusResponse)
def rag_status():
    """Get RAG index status"""
    st = rag_service.get_status()
    return RAGStatusResponse(
        loaded=st["loaded"],
        vectors=st["vectors"],
        dim=st["dim"],
        index_path=st["index_path"],
    )


@router.post("/rag/search", response_model=RAGSearchResponse)
def rag_search(req: RAGSearchRequest):
    """Search permits using RAG"""
    try:
        rows = rag_service.search_fixed(query=req.query, top_k=req.top_k or 20, filters=req.filters or {},
                                        oversample=req.oversample or 5)
        return RAGSearchResponse(success=True, count=len(rows), results=rows)
    except Exception as e:
        logger.error(f"RAG search error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/search-description-only", response_model=RAGSearchResponse)
def rag_search_description_only(req: RAGSearchRequest):
    """Search ONLY in permit descriptions using keywords"""
    try:
        rows = rag_service.search_description_only(
            query=req.query,
            top_k=req.top_k or 20,
            filters=req.filters or {},
            oversample=req.oversample or 5
        )
        return RAGSearchResponse(success=True, count=len(rows), results=rows)
    except Exception as e:
        logger.error(f"RAG description-only search error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/search-keywords", response_model=RAGSearchResponse)
def rag_search_keywords(req: RAGSearchRequest):
    """Simple keyword search in permit descriptions using SQL LIKE"""
    try:
        rows = rag_service.search_keywords(
            keywords=req.query,
            top_k=req.top_k or 20,
            filters=req.filters or {}
        )
        return RAGSearchResponse(success=True, count=len(rows), results=rows)
    except Exception as e:
        logger.error(f"RAG keyword search error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/distribute/preview", response_model=ClientRAGPreviewResponse)
def rag_distribute_preview(req: ClientRAGRequest):
    """Build per-client RAG assignments; return counts and samples without emailing"""
    try:
        raw, final = rag_service.build_client_assignments(req)

        preview = {}
        for cid, payload in final.items():
            c = payload["client"]
            rows = payload["rows"]
            email = c.get("email", "unknown")
            preview[email] = {
                "client": {"id": c.get("id"), "name": c.get("name"), "company": c.get("company")},
                "count": len(rows),
                "samples": rows[:3]  # first 3 rows as sample
            }

        summary = {
            "clients_considered": len(final),
            "total_rows": sum(len(v["rows"]) for v in final.values()),
            "exclusive": req.exclusive
        }

        return ClientRAGPreviewResponse(success=True, summary=summary, assignments=preview)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Preview distribute error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# @router.post("/rag/distribute/send", response_model=ClientRAGSendResponse)
# def rag_distribute_send(req: ClientRAGRequest):
#     """Build per-client RAG assignments and send emails (or dry_run)"""
#     try:
#         raw, final = rag_service.build_client_assignments(req)
#
#         # Send emails
#         results = email_service.send_rag_emails_for_clients(final, dry_run=req.dry_run)
#
#         # Record sent permits if not dry run
#         if not req.dry_run:
#             try:
#                 email_service.record_sent(final)
#             except Exception as rec_err:
#                 logger.warning(f"record_sent failed - {rec_err}")
#
#         summary = {
#             "clients_processed": len(final),
#             "dry_run": req.dry_run,
#             "exclusive": req.exclusive,
#             "total_rows": sum(len(v["rows"]) for v in final.values())
#         }
#
#         return ClientRAGSendResponse(success=True, summary=summary, results=results)
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Send distribute error: {e}")
#         raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/distribute/send", response_model=ClientRAGSendResponse)
def rag_distribute_send(req: ClientRAGRequest):
    """Build per-client RAG assignments and send emails (or dry_run)"""
    logger.info("🚀 =================================================================")
    logger.info("🚀 STARTING DISTRIBUTE_SEND API")
    logger.info("🚀 =================================================================")

    # Log incoming request details
    logger.info(f"📥 INCOMING REQUEST:")
    logger.info(f"   🔍 Query: '{req.query}'")
    logger.info(f"   🎛️ Filters: {req.filters}")
    logger.info(f"   👥 Selection: {req.selection}")
    logger.info(f"   ⚙️ Settings:")
    logger.info(f"      - use_client_prefs: {req.use_client_prefs}")
    logger.info(f"      - exclusive: {req.exclusive}")
    logger.info(f"      - dry_run: {req.dry_run}")
    logger.info(f"      - per_client_top_k: {req.per_client_top_k}")
    logger.info(f"      - oversample: {req.oversample}")

    try:
        logger.info("📞 CALLING rag_service.build_client_assignments()...")
        raw, final = rag_service.build_client_assignments(req)

        logger.info("✅ CLIENT ASSIGNMENTS COMPLETED")
        logger.info(f"   📊 Raw assignments: {len(raw)} clients")
        logger.info(f"   📊 Final assignments: {len(final)} clients")

        # Log detailed assignment results
        for client_id, assignment in final.items():
            client_name = assignment["client"].get("name", "Unknown")
            rows_count = len(assignment["rows"])
            logger.info(f"      👤 {client_name} (ID: {client_id}): {rows_count} permits")

        # Send emails
        logger.info("📧 CALLING email_service.send_rag_emails_for_clients()...")
        logger.info(f"   📋 Sending to {len(final)} clients")
        logger.info(f"   🧪 Dry run: {req.dry_run}")

        results = email_service.send_rag_emails_for_clients(final, dry_run=req.dry_run)

        logger.info("✅ EMAIL SENDING COMPLETED")
        logger.info(f"   📧 Email results: {len(results) if results else 0} responses")

        # Record sent permits if not dry run
        if not req.dry_run:
            logger.info("💾 RECORDING SENT PERMITS...")
            try:
                email_service.record_sent(final)
                logger.info("✅ RECORDING COMPLETED")
            except Exception as rec_err:
                logger.warning(f"❌ RECORDING FAILED: {rec_err}")
        else:
            logger.info("🧪 SKIPPING RECORDING (dry run)")

        # Build summary
        total_rows = sum(len(v["rows"]) for v in final.values())
        summary = {
            "clients_processed": len(final),
            "dry_run": req.dry_run,
            "exclusive": req.exclusive,
            "total_rows": total_rows
        }

        logger.info("📊 FINAL SUMMARY:")
        logger.info(f"   👥 Clients processed: {summary['clients_processed']}")
        logger.info(f"   📄 Total permits: {summary['total_rows']}")
        logger.info(f"   🧪 Dry run: {summary['dry_run']}")
        logger.info(f"   ⚖️ Exclusive: {summary['exclusive']}")

        response = ClientRAGSendResponse(success=True, summary=summary, results=results)
        logger.info("🎉 DISTRIBUTE_SEND API COMPLETED SUCCESSFULLY")
        return response

    except HTTPException as he:
        logger.error(f"❌ HTTP EXCEPTION in distribute_send: {he}")
        raise
    except Exception as e:
        logger.error(f"❌ UNEXPECTED ERROR in distribute_send: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/search-dual", response_model=Dict[str, Any])
def rag_search_dual(req: RAGSearchRequest):
    """Perform both keyword and semantic search, return both result sets"""
    try:
        keyword_results, semantic_results = rag_service.search_dual(
            query=req.query,
            top_k=req.top_k or 20,
            filters=req.filters or {},
            oversample=req.oversample or 5
        )

        return {
            "success": True,
            "keyword_results": {
                "count": len(keyword_results),
                "results": keyword_results
            },
            "semantic_results": {
                "count": len(semantic_results),
                "results": semantic_results
            }
        }
    except Exception as e:
        logger.error(f"Dual RAG search error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


@router.post("/rag/distribute/dual-preview", response_model=Dict[str, Any])
def rag_distribute_dual_preview(req: ClientRAGRequest):
    """Build dual client RAG assignments; return counts and samples without emailing"""
    try:
        raw, final = rag_service.build_client_assignments_dual(req)

        preview = {}
        for cid, payload in final.items():
            c = payload["client"]
            keyword_results = payload["keyword_results"]
            semantic_results = payload["semantic_results"]
            email = c.get("email", "unknown")

            preview[email] = {
                "client": {"id": c.get("id"), "name": c.get("name"), "company": c.get("company")},
                "keyword_results": {
                    "count": len(keyword_results),
                    "samples": keyword_results[:3]
                },
                "semantic_results": {
                    "count": len(semantic_results),
                    "samples": semantic_results[:3]
                }
            }

        summary = {
            "clients_considered": len(final),
            "total_keyword_results": sum(len(v["keyword_results"]) for v in final.values()),
            "total_semantic_results": sum(len(v["semantic_results"]) for v in final.values()),
            "exclusive": req.exclusive
        }

        return {"success": True, "summary": summary, "assignments": preview}

    except Exception as e:
        logger.error(f"Dual preview distribute error: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})


# @router.post("/rag/distribute/dual-send", response_model=Dict[str, Any])
# def rag_distribute_dual_send(req: ClientRAGRequest):
#     """Build dual client RAG assignments and send emails with both CSVs"""
#     try:
#         raw, final = rag_service.build_client_assignments_dual(req)
#
#         # Send emails with both keyword and semantic CSVs
#         results = email_service.send_dual_rag_emails_for_clients(final, dry_run=req.dry_run)
#
#         if not req.dry_run:
#             try:
#                 # Convert dual results for existing record_sent method
#                 for client_id, assignment in final.items():
#                     combined_results = assignment["keyword_results"] + assignment["semantic_results"]
#                     single_assignment = {client_id: {"client": assignment["client"], "rows": combined_results}}
#                     email_service.record_sent(single_assignment)
#             except Exception as rec_err:
#                 logger.warning(f"record_sent failed - {rec_err}")
#
#         summary = {
#             "clients_processed": len(final),
#             "dry_run": req.dry_run,
#             "exclusive": req.exclusive,
#             "total_keyword_results": sum(len(v["keyword_results"]) for v in final.values()),
#             "total_semantic_results": sum(len(v["semantic_results"]) for v in final.values())
#         }
#
#         return {"success": True, "summary": summary, "results": results}
#
#     except Exception as e:
#         logger.error(f"Dual send distribute error: {e}")
#         raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})

@router.post("/rag/distribute/dual-send", response_model=Dict[str, Any])
def rag_distribute_dual_send(req: ClientRAGRequest):
    """Build dual client RAG assignments and send emails with both CSVs"""
    logger.info("🔄 =================================================================")
    logger.info("🔄 STARTING DISTRIBUTE_DUAL_SEND API")
    logger.info("🔄 =================================================================")

    # Log incoming request details
    logger.info(f"📥 INCOMING REQUEST:")
    logger.info(f"   🔍 Query: '{req.query}'")
    logger.info(f"   🎛️ Filters: {req.filters}")
    logger.info(f"   👥 Selection: {req.selection}")
    logger.info(f"   ⚙️ Settings:")
    logger.info(f"      - use_client_prefs: {req.use_client_prefs}")
    logger.info(f"      - exclusive: {req.exclusive}")
    logger.info(f"      - dry_run: {req.dry_run}")
    logger.info(f"      - per_client_top_k: {req.per_client_top_k}")
    logger.info(f"      - oversample: {req.oversample}")

    try:
        logger.info("📞 CALLING rag_service.build_client_assignments_dual()...")
        raw, final = rag_service.build_client_assignments_dual(req)
        #results_new = rag_service.process_clients_optimized(req)
        # raw={}
        # final={}
        logger.info("✅ DUAL CLIENT ASSIGNMENTS COMPLETED")
        logger.info(f"   📊 Raw assignments: {len(raw)} clients")
        logger.info(f"   📊 Final assignments: {len(final)} clients")

        # Log detailed dual assignment results
        total_keyword = 0
        total_semantic = 0
        for client_id, assignment in final.items():
            client_name = assignment["client"].get("name", "Unknown")
            keyword_count = len(assignment["keyword_results"])
            semantic_count = len(assignment["semantic_results"])
            total_keyword += keyword_count
            total_semantic += semantic_count
            logger.info(f"      👤 {client_name} (ID: {client_id}):")
            logger.info(f"         🔤 Keyword results: {keyword_count}")
            logger.info(f"         🧠 Semantic results: {semantic_count}")

        # Send emails with both keyword and semantic CSVs
        logger.info("📧 CALLING email_service.send_dual_rag_emails_for_clients()...")
        logger.info(f"   📋 Sending to {len(final)} clients")
        logger.info(f"   🧪 Dry run: {req.dry_run}")
        logger.info(f"   📊 Total keyword results: {total_keyword}")
        logger.info(f"   📊 Total semantic results: {total_semantic}")

        results = email_service.send_dual_rag_emails_for_clients(final, dry_run=req.dry_run)

        logger.info("✅ DUAL EMAIL SENDING COMPLETED")
        logger.info(f"   📧 Email results: {len(results) if results else 0} responses")

        # Record sent permits if not dry run
        if not req.dry_run:
            logger.info("💾 RECORDING SENT PERMITS (DUAL MODE)...")
            try:
                # Convert dual results for existing record_sent method
                for client_id, assignment in final.items():
                    client_name = assignment["client"].get("name", "Unknown")
                    keyword_results = assignment["keyword_results"]
                    semantic_results = assignment["semantic_results"]
                    combined_results = keyword_results + semantic_results

                    logger.info(f"   💾 Recording for {client_name} (ID: {client_id}):")
                    logger.info(f"      🔤 Keyword: {len(keyword_results)} permits")
                    logger.info(f"      🧠 Semantic: {len(semantic_results)} permits")
                    logger.info(f"      🔗 Combined: {len(combined_results)} permits")

                    single_assignment = {client_id: {"client": assignment["client"], "rows": combined_results}}
                    email_service.record_sent(single_assignment)

                logger.info("✅ DUAL RECORDING COMPLETED")
            except Exception as rec_err:
                logger.warning(f"❌ DUAL RECORDING FAILED: {rec_err}")
        else:
            logger.info("🧪 SKIPPING RECORDING (dry run)")

        # Build summary
        summary = {
            "clients_processed": len(final),
            "dry_run": req.dry_run,
            "exclusive": req.exclusive,
            "total_keyword_results": sum(len(v["keyword_results"]) for v in final.values()),
            "total_semantic_results": sum(len(v["semantic_results"]) for v in final.values())
        }

        logger.info("📊 DUAL FINAL SUMMARY:")
        logger.info(f"   👥 Clients processed: {summary['clients_processed']}")
        logger.info(f"   🔤 Total keyword results: {summary['total_keyword_results']}")
        logger.info(f"   🧠 Total semantic results: {summary['total_semantic_results']}")
        logger.info(f"   📄 Total permits: {summary['total_keyword_results'] + summary['total_semantic_results']}")
        logger.info(f"   🧪 Dry run: {summary['dry_run']}")
        logger.info(f"   ⚖️ Exclusive: {summary['exclusive']}")

        response = {"success": True, "summary": summary, "results": results}
        logger.info("🎉 DISTRIBUTE_DUAL_SEND API COMPLETED SUCCESSFULLY")
        return response

    except Exception as e:
        logger.error(f"❌ ERROR in dual send distribute: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})
@router.post("/rag/distribute/triple-send", response_model=Dict[str, Any])
def rag_distribute_triple_send(req: ClientRAGRequest):
    """Build triple client RAG assignments and send emails with three CSVs"""
    logger.info("🔄 =================================================================")
    logger.info("🔄 STARTING DISTRIBUTE_TRIPLE_SEND API")
    logger.info("🔄 =================================================================")

    try:
        logger.info("📞 CALLING rag_service.build_client_assignments_dual() for triple...")
        raw, final = rag_service.build_client_assignments_dual(req)

        logger.info("✅ TRIPLE CLIENT ASSIGNMENTS COMPLETED")

        # Send emails with triple CSVs
        logger.info("📧 CALLING email_service.send_triple_rag_emails_for_clients()...")
        results = email_service.send_triple_rag_emails_for_clients(final, dry_run=req.dry_run)

        logger.info("✅ TRIPLE EMAIL SENDING COMPLETED")

        # Build summary
        summary = {
            "clients_processed": len(final),
            "dry_run": req.dry_run,
            "exclusive": req.exclusive,
            "total_inclusion_results": sum(len(v["inclusion_results"]) for v in final.values()),
            "total_exclusion_results": sum(len(v["exclusion_results"]) for v in final.values()),
            "total_semantic_results": sum(len(v["semantic_results"]) for v in final.values())
        }

        logger.info("📊 TRIPLE FINAL SUMMARY:")
        logger.info(f"   👥 Clients processed: {summary['clients_processed']}")
        logger.info(f"   🔍 Total inclusion results: {summary['total_inclusion_results']}")
        logger.info(f"   🚫 Total exclusion results: {summary['total_exclusion_results']}")
        logger.info(f"   🧠 Total semantic results: {summary['total_semantic_results']}")

        return {"success": True, "summary": summary, "results": results}

    except Exception as e:
        logger.error(f"❌ ERROR in triple send distribute: {e}")
        raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})



#helpers
# @router.post("/clients/{client_id}/update-rag")
# def update_client_rag(client_id: int, rag_query: str = None, rag_filters: str = None):
#     """Update client RAG settings for testing"""
#     try:
#         result = rag_service.update_client_rag_settings(client_id, rag_query, rag_filters)
#         return result
#     except Exception as e:
#         logger.error(f"Update client RAG error: {e}")
#         raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})
#
#
# # Debug endpoints
# @router.get("/debug/clients")
# def debug_clients():
#     """Debug endpoint to check client data and RAG settings"""
#     try:
#         return rag_service.debug_clients()
#     except Exception as e:
#         logger.error(f"Debug clients error: {e}")
#         raise HTTPException(status_code=500, detail={"success": False, "error": str(e)})
#
#
# @router.post("/debug/rag-full-test")
# def debug_rag_full_test():
#     """Comprehensive RAG debug test"""
#     try:
#         return rag_service.full_debug_test()
#     except Exception as e:
#         logger.error(f"Full RAG debug test failed: {e}")
#         return {"success": False, "error": str(e)}
#
#
# @router.post("/debug/test-filters")
# def debug_test_filters(
#         query: str = "construction",
#         city: Optional[str] = None,
#         permit_type: Optional[str] = None,
#         permit_class: Optional[str] = None,
#         work_class: Optional[str] = None,  # NEW: Added work_class filter
#         top_k: int = 10
# ):
#     """Test specific filter combinations directly against RAG engine"""
#     try:
#         return rag_service.test_filters(query, city, permit_type, permit_class, work_class, top_k)
#     except Exception as e:
#         logger.error(f"Filter test failed: {e}")
#         return {"success": False, "error": str(e)}
#
# @router.get("/debug/database-sample")
# def debug_database_sample(limit: int = 10):
#     """Check what data is actually in the permits database"""
#     try:
#         return rag_service.debug_database_sample(limit)
#     except Exception as e:
#         logger.error(f"DB debug failed: {e}")
#         return {"success": False, "error": str(e)}
#
#
# @router.get("/debug/filter-values")
# def debug_filter_values():
#     """Get actual filterable values from the database"""
#     try:
#         return rag_service.get_filter_values()
#     except Exception as e:
#         logger.error(f"Filter values debug failed: {e}")
#         return {"success": False, "error": str(e)}
