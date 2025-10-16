import logging
import json
import sqlite3
import time
from typing import Dict, Any, Optional, List, Tuple
from app_final.core.config import PERMITS_DB_PATH, RAG_INDEX_DIR
from app_final.rag_engine.rag_engine_functional2 import RAGIndex
from app_final.models.rag_models import ClientRAGRequest, ClientSelection

logger = logging.getLogger(__name__)


class RAGService:
    def __init__(self):
        self.rag_index = RAGIndex(PERMITS_DB_PATH, index_dir=RAG_INDEX_DIR)
        self.permits_db_path = PERMITS_DB_PATH

    def build_index(self, full_reindex: bool = True, batch_size: int = 256):
        """Build the RAG index"""
        return self.rag_index.build(full_reindex=full_reindex, batch_size=batch_size)



    def get_status(self):
        """Get RAG index status"""
        return self.rag_index.status()

    def search_fixed(self, query: str, top_k: int = 20, filters: Dict[str, Any] = None, oversample: int = 5):
        """Search permits using RAG with filter-first approach"""
        logger.info(f"🔍 RAG SERVICE SEARCH: query='{query}', filters={filters}, top_k={top_k}")

        return self.rag_index.search_fixed_debug(
            query=query,
            top_k=top_k,
            filters=filters or {},
            oversample=oversample,
            return_scores=True
        )

    def search_description_only(self, query: str, top_k: int = 20, filters: Dict[str, Any] = None, oversample: int = 5):
        """Search only in permit descriptions with filter-first approach"""
        logger.info(f"🔍 RAG SERVICE DESCRIPTION SEARCH: query='{query}', filters={filters}, top_k={top_k}")

        return self.rag_index.search_description_only(
            query=query,
            top_k=top_k,
            filters=filters or {},
            oversample=oversample,
            return_scores=True
        )

    def search_keywords(self, keywords: str, top_k: int = 20, filters: Dict[str, Any] = None):
        """Search keywords in descriptions using SQL LIKE with filter-first approach"""
        logger.info(f"🔍 RAG SERVICE KEYWORD SEARCH: keywords='{keywords}', filters={filters}, top_k={top_k}")

        return self.rag_index.search_keywords_in_description(
            keywords=keywords,
            top_k=top_k,
            filters=filters or {},
            return_scores=True
        )

    def build_client_assignments(self, req: ClientRAGRequest) -> Tuple[
        Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
        """
        Build client assignments based on RAG search with simplified filter-first logic.
        """
        logger.info("🎯 =================================================================")
        logger.info("🎯 STARTING BUILD_CLIENT_ASSIGNMENTS")
        logger.info("🎯 =================================================================")

        logger.info(f"📋 INPUT REQUEST ANALYSIS:")
        logger.info(f"   🔍 Query: '{req.query}' (length: {len(req.query) if req.query else 0})")
        logger.info(f"   🎛️ Filters: {req.filters} (count: {len(req.filters) if req.filters else 0})")
        logger.info(f"   ⚙️ Settings:")
        logger.info(f"      - use_client_prefs: {req.use_client_prefs}")
        logger.info(f"      - exclusive: {req.exclusive}")
        logger.info(f"   📊 Limits:")
        logger.info(f"      - per_client_top_k: {req.per_client_top_k}")
        logger.info(f"      - oversample: {req.oversample}")
        logger.info(f"   👥 Selection:")
        logger.info(f"      - client_ids: {req.selection.client_ids}")
        logger.info(f"      - status: {req.selection.status}")

        logger.info("🔌 CONNECTING TO DATABASE...")
        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            logger.error("❌ CLIENT DB CONNECTION FAILED")
            raise Exception("Client DB not found")
        logger.info("✅ DATABASE CONNECTION ESTABLISHED")

        try:
            logger.info("👥 FETCHING CLIENTS...")
            clients = self._get_clients(conn, ids=req.selection.client_ids, status=req.selection.status)
            logger.info(f"✅ FOUND {len(clients)} CLIENTS")

            # Log each client
            for i, client in enumerate(clients, 1):
                logger.info(f"   👤 Client {i}: {client.get('name', 'Unknown')} (ID: {client.get('id', 'N/A')})")
                logger.info(f"      📧 Email: {client.get('email', 'N/A')}")
                logger.info(f"      🏙️ City: {client.get('city', 'N/A')}")
                logger.info(f"      🏗️ Permit Type: {client.get('permit_type', 'N/A')}")
                logger.info(f"      🏷️ Permit Class: {client.get('permit_class_mapped', 'N/A')}")
                logger.info(f"      ⚒️ Work Classes: {client.get('work_classes', 'N/A')}")
                logger.info(f"      🔍 RAG Query: {client.get('rag_query', 'N/A')}")

            # Decision point: 2 clients + exclusive = special case
            if len(clients) == 2 and req.exclusive:
                logger.info("⚖️ SPECIAL CASE DETECTED: 2 clients + exclusive")
                logger.info("⚖️ Routing to 75/25 distribution logic")
                result = self._handle_75_25_distribution(clients, req)
                logger.info("✅ 75/25 DISTRIBUTION COMPLETED")
                return result

            # Regular individual processing
            logger.info("👤 STANDARD CASE: Using individual client processing")
            result = self._handle_individual_assignments(clients, req)
            logger.info("✅ INDIVIDUAL ASSIGNMENTS COMPLETED")
            return result

        except Exception as e:
            logger.error(f"❌ ERROR in build_client_assignments: {e}")
            raise
        finally:
            logger.info("🔌 CLOSING DATABASE CONNECTION")
            conn.close()

    def _get_client_work_classes(self, client: Dict[str, Any]) -> List[str]:
        """Extract work class names from client's work_classes array"""
        try:
            # Get work_classes from client (this is a relationship, so we need to fetch it)
            conn = sqlite3.connect(self.permits_db_path)
            cur = conn.cursor()

            # Query the workclass table for this client
            cur.execute("SELECT name FROM workclass WHERE client_id = ?", (client["id"],))
            rows = cur.fetchall()

            work_class_names = [row[0] for row in rows if row[0] and row[0].strip()]
            conn.close()

            if work_class_names:
                logger.info(f"         📝 Found work classes from database: {work_class_names}")
                return work_class_names
            else:
                logger.info(f"         ⚠️ No work classes found for client {client['id']}")
                return []

        except Exception as e:
            logger.error(f"         ❌ Error getting work classes: {e}")
            return []

    def _handle_75_25_distribution(self, clients: List[Dict], req: ClientRAGRequest):
        """Handle 75/25 distribution for exactly 2 clients with improved debug logging"""
        logger.info("🔄 75/25 DISTRIBUTION PROCESS:")
        client1, client2 = clients[0], clients[1]

        # Log client info
        logger.info(f"   👤 Client 1: {client1.get('name')} (ID: {client1.get('id')})")
        logger.info(f"   👤 Client 2: {client2.get('name')} (ID: {client2.get('id')})")

        # Determine query
        query = self._determine_query(client1, req)
        logger.info(f"   🔎 Final query: '{query}'")

        # Build filters with debug logging
        filters = self._build_filters_for_client(client1, req)
        logger.info(f"   🔧 Final filters: {filters}")

        # Use RAG engine's 75/25 distribution method
        logger.info("   🚀 Executing 75/25 search and distribute...")
        client1_permits, client2_permits = self.rag_index.search_and_distribute_75_25(
            query=query,
            top_k=req.per_client_top_k or 20,
            filters=filters,
            oversample=req.oversample or 10,
            return_scores=True
        )

        logger.info(f"   ✅ Distribution complete:")
        logger.info(f"      Client 1 ({client1.get('name')}): {len(client1_permits)} permits")
        logger.info(f"      Client 2 ({client2.get('name')}): {len(client2_permits)} permits")

        # Create assignments
        final_assignments = {
            int(client1["id"]): {"client": client1, "rows": client1_permits},
            int(client2["id"]): {"client": client2, "rows": client2_permits}
        }

        raw_assignments = {
            int(client1["id"]): {"client": client1, "rows": client1_permits, "query": query, "filters": filters},
            int(client2["id"]): {"client": client2, "rows": client2_permits, "query": query, "filters": filters}
        }

        return raw_assignments, final_assignments

    def _handle_individual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
        """Handle individual client assignments with improved debug logging"""
        logger.info("🔄 =================================================================")
        logger.info("🔄 STARTING INDIVIDUAL ASSIGNMENTS PROCESS")
        logger.info("🔄 =================================================================")

        raw_assignments = {}
        logger.info(f"📊 Processing {len(clients)} clients individually")

        for i, c in enumerate(clients, 1):
            logger.info(f"👤 ===============================================")
            logger.info(f"👤 PROCESSING CLIENT {i}/{len(clients)}")
            logger.info(f"👤 ===============================================")

            cid = int(c["id"])
            client_name = c.get("name", "Unknown")
            logger.info(f"   📇 Client Details:")
            logger.info(f"      - Name: {client_name}")
            logger.info(f"      - ID: {cid}")
            logger.info(f"      - Email: {c.get('email', 'N/A')}")

            # Determine query with debug logging
            logger.info(f"   🔍 DETERMINING QUERY...")
            query = self._determine_query(c, req)
            logger.info(f"   ✅ Query determined: '{query}'")

            # Build filters with debug logging
            logger.info(f"   🔧 BUILDING FILTERS...")
            filters = self._build_filters_for_client(c, req)
            logger.info(f"   ✅ Filters built: {filters}")

            # Search - use the new filter-first approach
            logger.info(f"   🚀 EXECUTING SEARCH...")
            search_start_time = time.time()

            if query and query.strip():
                logger.info(f"      🔍 Using description-focused search")
                logger.info(f"      📊 Parameters:")
                logger.info(f"         - query: '{query}'")
                logger.info(f"         - top_k: {req.per_client_top_k or 20}")
                logger.info(f"         - filters: {filters}")
                logger.info(f"         - oversample: {req.oversample or 5}")

                rows = self.rag_index.search_description_only(
                    query=query,
                    top_k=req.per_client_top_k or 20,
                    filters=filters,
                    oversample=req.oversample or 5,
                    return_scores=True
                )
            else:
                logger.info(f"      📋 Using filter-only retrieval (no query)")
                logger.info(f"      📊 Parameters:")
                logger.info(f"         - top_k: {req.per_client_top_k or 20}")
                logger.info(f"         - filters: {filters}")
                logger.info(f"         - oversample: {req.oversample or 5}")

                rows = self.rag_index.search_fixed(
                    query="",  # Empty query triggers filter-only mode
                    top_k=req.per_client_top_k or 20,
                    filters=filters,
                    oversample=req.oversample or 5,
                    return_scores=True
                )

            search_end_time = time.time()
            search_duration = search_end_time - search_start_time

            logger.info(f"   ✅ SEARCH COMPLETED")
            logger.info(f"      📊 Results: {len(rows)} permits")
            logger.info(f"      ⏱️ Duration: {search_duration:.2f} seconds")

            # Log sample results
            if rows:
                logger.info(f"      📄 Sample results:")
                for j, row in enumerate(rows[:3], 1):  # Show first 3
                    permit_id = row.get('id', 'N/A')
                    address = row.get('address', 'N/A')
                    description = row.get('description', 'N/A')[:50] + "..." if row.get('description') else 'N/A'
                    score = row.get('score', 'N/A')
                    logger.info(f"         {j}. ID: {permit_id}, Address: {address}")
                    logger.info(f"            Description: {description}")
                    logger.info(f"            Score: {score}")

            raw_assignments[cid] = {
                "client": c,
                "rows": rows,
                "query": query,
                "filters": filters,
                "search_duration": search_duration
            }

        logger.info("📊 RAW ASSIGNMENTS SUMMARY:")
        for cid, data in raw_assignments.items():
            client_name = data["client"].get("name", "Unknown")
            row_count = len(data["rows"])
            duration = data.get("search_duration", 0)
            logger.info(f"   👤 {client_name}: {row_count} permits ({duration:.2f}s)")

        # Apply exclusive distribution if requested
        if req.exclusive:
            logger.info("⚖️ ===============================================")
            logger.info("⚖️ APPLYING EXCLUSIVE DISTRIBUTION")
            logger.info("⚖️ ===============================================")

            exclusive_start_time = time.time()
            final_assignments = self._distribute_exclusive(raw_assignments)
            exclusive_end_time = time.time()
            exclusive_duration = exclusive_end_time - exclusive_start_time

            logger.info(f"✅ EXCLUSIVE DISTRIBUTION COMPLETED ({exclusive_duration:.2f}s)")
            logger.info("📊 FINAL DISTRIBUTION:")
            for cid, data in final_assignments.items():
                client_name = data["client"].get("name", "Unknown")
                final_count = len(data['rows'])
                original_count = len(raw_assignments[cid]['rows'])
                logger.info(f"   👤 {client_name}: {final_count} permits (was {original_count})")
        else:
            logger.info("📋 NO EXCLUSIVE DISTRIBUTION REQUESTED")
            final_assignments = {
                cid: {
                    "client": payload["client"],
                    "rows": list(payload["rows"])
                }
                for cid, payload in raw_assignments.items()
            }

        logger.info("🎉 INDIVIDUAL ASSIGNMENTS PROCESS COMPLETED")
        return raw_assignments, final_assignments

    def _determine_query(self, client: Dict[str, Any], req: ClientRAGRequest) -> str:
        """Determine the query for a client with debug logging"""
        logger.info(f"      🔍 QUERY DETERMINATION LOGIC:")

        if req.query and req.query.strip():
            final_query = req.query.strip()
            logger.info(f"         📝 Using request query: '{final_query}'")
            logger.info(f"         📏 Query length: {len(final_query)} characters")
            return final_query
        elif req.use_client_prefs and client.get("rag_query"):
            saved_query = str(client["rag_query"]).strip()
            logger.info(f"         💾 Using saved client query: '{saved_query}'")
            logger.info(f"         📏 Query length: {len(saved_query)} characters")
            return saved_query
        else:
            logger.info(f"         🔮 No query provided, inferring from client data...")
            inferred = self._inferred_query_from_client(client)
            logger.info(f"         🔮 Inferred query: '{inferred}'")
            logger.info(f"         📏 Query length: {len(inferred)} characters")
            return inferred

    def _apply_keyword_filtering(self, permits: List[Dict[str, Any]],
                                 keywords_include: Optional[List[str]] = None,
                                 keywords_exclude: Optional[List[str]] = None) -> Tuple[
        List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Apply keyword include/exclude filtering to permits.

        Returns:
            Tuple of (filtered_permits, excluded_permits)
        """
        logger.info("🔤 APPLYING KEYWORD FILTERING:")
        logger.info(f"   📊 Input: {len(permits)} permits")
        logger.info(f"   🔍 Include keywords: {keywords_include}")
        logger.info(f"   🚫 Exclude keywords: {keywords_exclude}")

        if not keywords_include and not keywords_exclude:
            logger.info("   📋 No keyword filtering requested")
            return permits, []

        filtered_permits = []
        excluded_permits = []

        for permit in permits:
            description = str(permit.get('description', '')).lower()
            permit_id = permit.get('id', 'N/A')
            address = permit.get('address', 'N/A')

            # Check exclude keywords first (OR logic)
            excluded = False
            if keywords_exclude:
                for keyword in keywords_exclude:
                    if self._whole_word_match(description, keyword.lower()):
                        excluded_permits.append({
                            "id": permit_id,
                            "address": address,
                            "reason": f"contained keyword '{keyword}'"
                        })
                        excluded = True
                        logger.info(f"      🚫 Excluded permit {permit_id}: contains '{keyword}'")
                        break

            if excluded:
                continue

            # Check include keywords (OR logic - must contain at least one)
            included = True
            if keywords_include:
                included = False
                for keyword in keywords_include:
                    if self._whole_word_match(description, keyword.lower()):
                        included = True
                        logger.info(f"      ✅ Included permit {permit_id}: contains '{keyword}'")
                        break

                if not included:
                    logger.info(f"      ❌ Filtered out permit {permit_id}: no include keywords found")

            if included:
                filtered_permits.append(permit)

        logger.info(f"   📊 RESULTS: {len(filtered_permits)} kept, {len(excluded_permits)} excluded")
        return filtered_permits, excluded_permits

    def _whole_word_match(self, text: str, keyword: str) -> bool:
        """Check if keyword appears as whole word in text (case-insensitive)."""
        import re
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def _determine_keywords(self, client: Dict[str, Any], req: ClientRAGRequest) -> Tuple[
        Optional[List[str]], Optional[List[str]]]:
        """Determine include/exclude keywords for a client"""
        logger.info(f"      🔤 KEYWORD DETERMINATION:")

        # Priority: Request keywords > Client saved keywords
        if req.keywords_include or req.keywords_exclude:
            include_kw = req.keywords_include
            exclude_kw = req.keywords_exclude
            logger.info(f"         📝 Using request keywords:")
            logger.info(f"            Include: {include_kw}")
            logger.info(f"            Exclude: {exclude_kw}")
            return include_kw, exclude_kw
        elif req.use_client_prefs:
            include_kw = client.get("keywords_include")
            exclude_kw = client.get("keywords_exclude")
            logger.info(f"         💾 Using client saved keywords:")
            logger.info(f"            Include: {include_kw}")
            logger.info(f"            Exclude: {exclude_kw}")
            return include_kw, exclude_kw
        else:
            logger.info(f"         📋 No keywords specified")
            return None, None



    def _build_filters_for_client(self, client: Dict[str, Any], req: ClientRAGRequest) -> Dict[str, Any]:
        """Build filters for a client - FIXED to handle work_classes properly"""
        logger.info(f"      🔧 FILTER BUILDING PROCESS:")

        # Start with global filters from request
        filters = dict(req.filters) if req.filters else {}
        logger.info(f"         📋 Starting with global request filters: {filters}")

        # Add client's structural filters (from client columns) - CONVERT TO LISTS
        if client.get("city") and str(client["city"]).strip():
            city_value = str(client["city"]).strip()
            filters["city"] = [city_value]
            logger.info(f"         📍 Added client city filter: {filters['city']}")
        else:
            logger.info(f"         📍 No city filter (value: {client.get('city', 'None')})")

        if client.get("permit_type") and str(client["permit_type"]).strip():
            permit_type_value = str(client["permit_type"]).strip()
            filters["permit_type"] = [permit_type_value]
            logger.info(f"         🏗️ Added client permit_type filter: {filters['permit_type']}")
        else:
            logger.info(f"         🏗️ No permit_type filter (value: {client.get('permit_type', 'None')})")

        if client.get("permit_class_mapped") and str(client["permit_class_mapped"]).strip():
            permit_class_value = str(client["permit_class_mapped"]).strip()
            filters["permit_class_mapped"] = [permit_class_value]
            logger.info(f"         🏷️ Added client permit_class_mapped filter: {filters['permit_class_mapped']}")
        else:
            logger.info(
                f"         🏷️ No permit_class_mapped filter (value: {client.get('permit_class_mapped', 'None')})")

        # FIXED: Handle work_classes array from client profile
        logger.info(f"         ⚒️ Processing work_classes...")
        work_classes = self._get_client_work_classes(client)
        if work_classes:
            filters["work_class"] = work_classes  # Use 'work_class' to match database field
            logger.info(f"         ⚒️ Added client work_class filter: {filters['work_class']}")
        else:
            logger.info(f"         ⚒️ No work_class filter (raw value: {client.get('work_classes', 'None')})")

        # Remove empty values
        logger.info(f"         🧹 Cleaning empty filters...")
        original_filter_count = len(filters)
        final_filters = {k: v for k, v in filters.items() if v and len(v) > 0}
        removed_count = original_filter_count - len(final_filters)

        if removed_count > 0:
            logger.info(f"         🧹 Removed {removed_count} empty filters")

        logger.info(f"         🎯 FINAL FILTERS: {final_filters}")
        logger.info(f"         📊 Filter count: {len(final_filters)}")

        return final_filters

    # def _get_clients(self, conn: sqlite3.Connection, ids: Optional[List[int]] = None, status: Optional[str] = None):
    #     """Get clients from database with optional RAG settings - ENHANCED DEBUG VERSION"""
    #     logger.info("🔍 =================================================================")
    #     logger.info("🔍 STARTING _GET_CLIENTS DATABASE QUERY")
    #     logger.info("🔍 =================================================================")
    #
    #     logger.info(f"📊 INPUT PARAMETERS:")
    #     logger.info(f"   🆔 client_ids: {ids}")
    #     logger.info(f"   📋 status filter: '{status}'")
    #
    #     try:
    #         # First, let's see what's in the client table (singular, not plural!)
    #         logger.info("🔍 INSPECTING CLIENT TABLE...")
    #
    #         # Get table schema
    #         cursor = conn.cursor()
    #         cursor.execute("PRAGMA table_info(client)")
    #         columns = cursor.fetchall()
    #         logger.info(f"📋 CLIENT TABLE SCHEMA:")
    #         for col in columns:
    #             logger.info(
    #                 f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")
    #
    #         # Count total rows
    #         cursor.execute("SELECT COUNT(*) FROM client")
    #         total_count = cursor.fetchone()[0]
    #         logger.info(f"📊 TOTAL ROWS IN CLIENT TABLE: {total_count}")
    #
    #         if total_count == 0:
    #             logger.warning("⚠️ CLIENT TABLE IS EMPTY!")
    #             return []
    #
    #         # Check status values
    #         cursor.execute("SELECT DISTINCT status FROM client")
    #         statuses = cursor.fetchall()
    #         logger.info(f"📋 DISTINCT STATUS VALUES IN CLIENT TABLE:")
    #         for status_row in statuses:
    #             logger.info(f"   - '{status_row[0]}'")
    #
    #         # Count by status (using case-insensitive comparison like your original code)
    #         if status:
    #             cursor.execute("SELECT COUNT(*) FROM client WHERE LOWER(status) = LOWER(?)", (status,))
    #             status_count = cursor.fetchone()[0]
    #             logger.info(f"📊 CLIENTS WITH STATUS '{status}' (case-insensitive): {status_count}")
    #
    #         # Build the query using your original logic
    #         logger.info("🔨 BUILDING QUERY (using your original logic)...")
    #
    #         q = "SELECT id, name, company, email, phone, address, city, state, zip_code, country, permit_type, permit_class_mapped, status FROM client"
    #         conds = []
    #         params = []
    #
    #         if status:
    #             conds.append("LOWER(status)=LOWER(?)")
    #             params.append(status)
    #             logger.info(f"   ✅ Added status condition: LOWER(status)=LOWER('{status}')")
    #
    #         if ids:
    #             conds.append(f"id IN ({','.join('?' for _ in ids)})")
    #             params.extend(ids)
    #             logger.info(f"   ✅ Added ID condition: id IN ({ids})")
    #
    #         if conds:
    #             q += " WHERE " + " AND ".join(conds)
    #
    #         q += " ORDER BY id"
    #
    #         logger.info(f"📝 FINAL SQL QUERY: {q}")
    #         logger.info(f"📝 PARAMETERS: {params}")
    #
    #         # Execute the query
    #         logger.info("⚡ EXECUTING QUERY...")
    #         cursor.execute(q, params)
    #         cols = [d[0] for d in cursor.description]
    #         raw_clients = cursor.fetchall()
    #         clients = [dict(zip(cols, row)) for row in raw_clients]
    #
    #         logger.info(f"✅ QUERY COMPLETED: {len(clients)} clients returned")
    #
    #         if len(clients) == 0:
    #             logger.warning("⚠️ NO CLIENTS FOUND WITH CURRENT FILTERS!")
    #             # Let's see all clients regardless of filters
    #             logger.info("🔍 SHOWING ALL CLIENTS (NO FILTERS):")
    #             cursor.execute("SELECT id, name, company, email, status FROM client")
    #             all_clients = cursor.fetchall()
    #             for client_row in all_clients:
    #                 logger.info(
    #                     f"   - ID: {client_row[0]}, Name: {client_row[1]}, Company: {client_row[2]}, Email: {client_row[3]}, Status: '{client_row[4]}'")
    #             return []
    #
    #         # Log each found client
    #         for i, client in enumerate(clients, 1):
    #             logger.info(f"👤 CLIENT {i} (before RAG enhancement):")
    #             logger.info(f"   🆔 ID: {client.get('id', 'N/A')}")
    #             logger.info(f"   📛 Name: {client.get('name', 'N/A')}")
    #             logger.info(f"   🏢 Company: {client.get('company', 'N/A')}")
    #             logger.info(f"   📧 Email: {client.get('email', 'N/A')}")
    #             logger.info(f"   📋 Status: '{client.get('status', 'N/A')}'")
    #             logger.info(f"   🏙️ City: {client.get('city', 'N/A')}")
    #             logger.info(f"   🏗️ Permit Type: {client.get('permit_type', 'N/A')}")
    #             logger.info(f"   🏷️ Permit Class: {client.get('permit_class_mapped', 'N/A')}")
    #
    #         # Check for RAG columns (using your original logic)
    #         logger.info("🔍 CHECKING FOR RAG COLUMNS...")
    #         has_rag_query = self._table_has_column(conn, "client", "rag_query")
    #         has_rag_filters = self._table_has_column(conn, "client", "rag_filter_json")
    #
    #         logger.info(f"   📊 has_rag_query: {has_rag_query}")
    #         logger.info(f"   📊 has_rag_filters: {has_rag_filters}")
    #
    #         # Enhance clients with RAG data
    #         for c in clients:
    #             client_id = c["id"]
    #             client_name = c.get("name", "Unknown")
    #
    #             if has_rag_query:
    #                 try:
    #                     cursor.execute("SELECT rag_query FROM client WHERE id=?", (client_id,))
    #                     result = cursor.fetchone()
    #                     c["rag_query"] = result[0] if result else None
    #                     logger.info(f"   👤 {client_name}: rag_query = '{c['rag_query']}'")
    #                 except Exception as e:
    #                     logger.error(f"❌ Error getting rag_query for client {client_name}: {e}")
    #                     c["rag_query"] = None
    #             else:
    #                 c["rag_query"] = None
    #
    #             if has_rag_filters:
    #                 try:
    #                     cursor.execute("SELECT rag_filter_json FROM client WHERE id=?", (client_id,))
    #                     result = cursor.fetchone()
    #                     raw = result[0] if result else None
    #                     c["rag_filters"] = json.loads(raw) if raw else None
    #                     logger.info(f"   👤 {client_name}: rag_filters = {c['rag_filters']}")
    #                 except Exception as e:
    #                     logger.error(f"❌ Error getting rag_filters for client {client_name}: {e}")
    #                     c["rag_filters"] = None
    #             else:
    #                 c["rag_filters"] = None
    #
    #         logger.info(f"🎉 _GET_CLIENTS COMPLETED: {len(clients)} clients found and enhanced")
    #         return clients
    #
    #     except Exception as e:
    #         logger.error(f"❌ ERROR in _get_clients: {e}")
    #         logger.error(f"❌ Error type: {type(e).__name__}")
    #         import traceback
    #         logger.error(f"❌ Traceback: {traceback.format_exc()}")
    #         raise
    def _get_clients(self, conn: sqlite3.Connection, ids: Optional[List[int]] = None, status: Optional[str] = None):
        """Get clients from database with optional RAG settings - ENHANCED WITH KEYWORDS"""
        logger.info("🔍 =================================================================")
        logger.info("🔍 STARTING _GET_CLIENTS DATABASE QUERY (ENHANCED)")
        logger.info("🔍 =================================================================")

        logger.info(f"📊 INPUT PARAMETERS:")
        logger.info(f"   🆔 client_ids: {ids}")
        logger.info(f"   📋 status filter: '{status}'")

        try:
            # First, let's see what's in the client table
            logger.info("🔍 INSPECTING CLIENT TABLE...")

            # Get table schema
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(client)")
            columns = cursor.fetchall()
            logger.info(f"📋 CLIENT TABLE SCHEMA:")
            for col in columns:
                logger.info(
                    f"   - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'DEFAULT: ' + str(col[4]) if col[4] else ''}")

            # Count total rows
            cursor.execute("SELECT COUNT(*) FROM client")
            total_count = cursor.fetchone()[0]
            logger.info(f"📊 TOTAL ROWS IN CLIENT TABLE: {total_count}")

            if total_count == 0:
                logger.warning("⚠️ CLIENT TABLE IS EMPTY!")
                return []

            # Check status values
            cursor.execute("SELECT DISTINCT status FROM client")
            statuses = cursor.fetchall()
            logger.info(f"📋 DISTINCT STATUS VALUES IN CLIENT TABLE:")
            for status_row in statuses:
                logger.info(f"   - '{status_row[0]}'")

            # Count by status
            if status:
                cursor.execute("SELECT COUNT(*) FROM client WHERE LOWER(status) = LOWER(?)", (status,))
                status_count = cursor.fetchone()[0]
                logger.info(f"📊 CLIENTS WITH STATUS '{status}' (case-insensitive): {status_count}")

            # Build the query using your original logic
            logger.info("🔨 BUILDING QUERY...")

            q = "SELECT id, name, company, email, phone, address, city, state, zip_code, country, permit_type, permit_class_mapped, status FROM client"
            conds = []
            params = []

            if status:
                conds.append("LOWER(status)=LOWER(?)")
                params.append(status)
                logger.info(f"   ✅ Added status condition: LOWER(status)=LOWER('{status}')")

            if ids:
                conds.append(f"id IN ({','.join('?' for _ in ids)})")
                params.extend(ids)
                logger.info(f"   ✅ Added ID condition: id IN ({ids})")

            if conds:
                q += " WHERE " + " AND ".join(conds)

            q += " ORDER BY id"

            logger.info(f"📝 FINAL SQL QUERY: {q}")
            logger.info(f"📝 PARAMETERS: {params}")

            # Execute the query
            logger.info("⚡ EXECUTING QUERY...")
            cursor.execute(q, params)
            cols = [d[0] for d in cursor.description]
            raw_clients = cursor.fetchall()
            clients = [dict(zip(cols, row)) for row in raw_clients]

            logger.info(f"✅ QUERY COMPLETED: {len(clients)} clients returned")

            if len(clients) == 0:
                logger.warning("⚠️ NO CLIENTS FOUND WITH CURRENT FILTERS!")
                # Let's see all clients regardless of filters
                logger.info("🔍 SHOWING ALL CLIENTS (NO FILTERS):")
                cursor.execute("SELECT id, name, company, email, status FROM client")
                all_clients = cursor.fetchall()
                for client_row in all_clients:
                    logger.info(
                        f"   - ID: {client_row[0]}, Name: {client_row[1]}, Company: {client_row[2]}, Email: {client_row[3]}, Status: '{client_row[4]}'")
                return []

            # Log each found client
            for i, client in enumerate(clients, 1):
                logger.info(f"👤 CLIENT {i} (before RAG enhancement):")
                logger.info(f"   🆔 ID: {client.get('id', 'N/A')}")
                logger.info(f"   📛 Name: {client.get('name', 'N/A')}")
                logger.info(f"   🏢 Company: {client.get('company', 'N/A')}")
                logger.info(f"   📧 Email: {client.get('email', 'N/A')}")
                logger.info(f"   📋 Status: '{client.get('status', 'N/A')}'")
                logger.info(f"   🏙️ City: {client.get('city', 'N/A')}")
                logger.info(f"   🏗️ Permit Type: {client.get('permit_type', 'N/A')}")
                logger.info(f"   🏷️ Permit Class: {client.get('permit_class_mapped', 'N/A')}")

            # Check for RAG columns (including new keyword columns)
            logger.info("🔍 CHECKING FOR RAG COLUMNS...")
            has_rag_query = self._table_has_column(conn, "client", "rag_query")
            has_rag_filters = self._table_has_column(conn, "client", "rag_filter_json")
            has_keywords_include = self._table_has_column(conn, "client", "keywords_include")
            has_keywords_exclude = self._table_has_column(conn, "client", "keywords_exclude")

            logger.info(f"   📊 has_rag_query: {has_rag_query}")
            logger.info(f"   📊 has_rag_filters: {has_rag_filters}")
            logger.info(f"   📊 has_keywords_include: {has_keywords_include}")
            logger.info(f"   📊 has_keywords_exclude: {has_keywords_exclude}")

            # Enhance clients with RAG data
            for c in clients:
                client_id = c["id"]
                client_name = c.get("name", "Unknown")

                # Existing rag_query logic
                if has_rag_query:
                    try:
                        cursor.execute("SELECT rag_query FROM client WHERE id=?", (client_id,))
                        result = cursor.fetchone()
                        c["rag_query"] = result[0] if result else None
                        logger.info(f"   👤 {client_name}: rag_query = '{c['rag_query']}'")
                    except Exception as e:
                        logger.error(f"❌ Error getting rag_query for client {client_name}: {e}")
                        c["rag_query"] = None
                else:
                    c["rag_query"] = None

                # Existing rag_filters logic
                if has_rag_filters:
                    try:
                        cursor.execute("SELECT rag_filter_json FROM client WHERE id=?", (client_id,))
                        result = cursor.fetchone()
                        raw = result[0] if result else None
                        c["rag_filters"] = json.loads(raw) if raw else None
                        logger.info(f"   👤 {client_name}: rag_filters = {c['rag_filters']}")
                    except Exception as e:
                        logger.error(f"❌ Error getting rag_filters for client {client_name}: {e}")
                        c["rag_filters"] = None
                else:
                    c["rag_filters"] = None

                # NEW: keywords_include logic
                if has_keywords_include:
                    try:
                        cursor.execute("SELECT keywords_include FROM client WHERE id=?", (client_id,))
                        result = cursor.fetchone()
                        raw = result[0] if result else None
                        c["keywords_include"] = json.loads(raw) if raw else None
                        logger.info(f"   👤 {client_name}: keywords_include = {c['keywords_include']}")
                    except Exception as e:
                        logger.error(f"❌ Error getting keywords_include for client {client_name}: {e}")
                        c["keywords_include"] = None
                else:
                    c["keywords_include"] = None

                # NEW: keywords_exclude logic
                if has_keywords_exclude:
                    try:
                        cursor.execute("SELECT keywords_exclude FROM client WHERE id=?", (client_id,))
                        result = cursor.fetchone()
                        raw = result[0] if result else None
                        c["keywords_exclude"] = json.loads(raw) if raw else None
                        logger.info(f"   👤 {client_name}: keywords_exclude = {c['keywords_exclude']}")
                    except Exception as e:
                        logger.error(f"❌ Error getting keywords_exclude for client {client_name}: {e}")
                        c["keywords_exclude"] = None
                else:
                    c["keywords_exclude"] = None

            logger.info(f"🎉 _GET_CLIENTS COMPLETED: {len(clients)} clients found and enhanced")
            return clients

        except Exception as e:
            logger.error(f"❌ ERROR in _get_clients: {e}")
            logger.error(f"❌ Error type: {type(e).__name__}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            raise



    def _table_has_column(self, conn, table: str, col: str) -> bool:
        """Check if table has column"""
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        return col in cols

    def _inferred_query_from_client(self, c: Dict[str, Any]) -> str:
        """Fallback query if client has no rag_query"""
        parts = []
        if c.get("permit_class_mapped"):
            parts.append(str(c["permit_class_mapped"]))
        if c.get("permit_type"):
            parts.append(str(c["permit_type"]))
        if c.get("city"):
            parts.append(str(c["city"]))
        q = " ".join(parts).strip()
        return q if q else "construction permit"

    def _distribute_exclusive(self, assignments_by_client: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """
        Distribute permits exclusively (each permit to only one client) with debug logging.
        """
        logger.info("   ⚖️ EXCLUSIVE DISTRIBUTION PROCESS:")

        def key_fn(r):
            s = r.get("_rag_score", 0.0)
            d = (r.get("issued_date") or "")[:10]
            return (s, d)

        queues = {}
        total_permits_by_client = {}

        for cid, payload in assignments_by_client.items():
            client_name = payload["client"].get("name", "Unknown")
            rows = payload.get("rows", [])
            rows_sorted = sorted(rows, key=key_fn, reverse=True)
            queues[cid] = rows_sorted
            total_permits_by_client[cid] = len(rows)
            logger.info(f"      👤 {client_name}: {len(rows)} permits in queue")

        assigned_permit_ids = set()
        results = {cid: {"client": payload["client"], "rows": []} for cid, payload in assignments_by_client.items()}

        # If exactly two clients, aim for a 75/25 split
        desired_counts: Optional[Dict[int, int]] = None
        if len(queues) == 2:
            all_unique_permit_ids = set()
            for q in queues.values():
                for r in q:
                    try:
                        all_unique_permit_ids.add(int(r["id"]))
                    except Exception:
                        pass
            total_unique = len(all_unique_permit_ids)
            first_target = int(round(total_unique * 0.75))
            second_target = total_unique - first_target
            cids = list(queues.keys())
            desired_counts = {cids[0]: first_target, cids[1]: second_target}
            logger.info(f"      🎯 Target distribution: {first_target} / {second_target} permits")

        # Continue while at least one client still has candidates
        round_num = 1
        while any(queues.values()):
            logger.info(f"      🔄 Distribution round {round_num}")

            for cid in list(queues.keys()):
                client_name = results[cid]["client"].get("name", "Unknown")

                if desired_counts is not None and len(results[cid]["rows"]) >= desired_counts.get(cid, 0):
                    continue

                q = queues[cid]
                while q and int(q[0]["id"]) in assigned_permit_ids:
                    q.pop(0)
                if not q:
                    continue

                row = q.pop(0)
                pid = int(row["id"])
                if pid in assigned_permit_ids:
                    continue

                assigned_permit_ids.add(pid)
                results[cid]["rows"].append(row)

                logger.info(f"         ✅ Assigned permit {pid} to {client_name}")

            if desired_counts is not None and all(
                    len(results[c]["rows"]) >= desired_counts.get(c, 0) for c in results.keys()):
                logger.info("      🎯 Target distribution achieved")
                break

            round_num += 1
            if round_num > 100:  # Safety break
                logger.warning("      ⚠️ Distribution stopped after 100 rounds")
                break

        # Log final distribution
        logger.info("   ✅ EXCLUSIVE DISTRIBUTION COMPLETE:")
        for cid, data in results.items():
            client_name = data["client"].get("name", "Unknown")
            original_count = total_permits_by_client.get(cid, 0)
            final_count = len(data["rows"])
            logger.info(f"      👤 {client_name}: {final_count} permits (was {original_count})")

        return results

    def update_client_rag_settings(self, client_id: int, rag_query: str = None, rag_filters: str = None):
        """Update client RAG settings"""
        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            raise Exception("Client DB not found")

        try:
            cursor = conn.cursor()

            # Check if columns exist
            has_rag_query = self._table_has_column(conn, "client", "rag_query")
            has_rag_filters = self._table_has_column(conn, "client", "rag_filter_json")

            if not has_rag_query or not has_rag_filters:
                if not has_rag_query:
                    cursor.execute("ALTER TABLE client ADD COLUMN rag_query TEXT")
                if not has_rag_filters:
                    cursor.execute("ALTER TABLE client ADD COLUMN rag_filter_json TEXT")
                conn.commit()

            # Update client RAG settings
            updates = []
            params = []

            if rag_query is not None:
                updates.append("rag_query = ?")
                params.append(rag_query)

            if rag_filters is not None:
                updates.append("rag_filter_json = ?")
                params.append(rag_filters)

            if updates:
                params.append(client_id)
                query = f"UPDATE client SET {', '.join(updates)} WHERE id = ?"
                cursor.execute(query, params)
                conn.commit()

            return {"success": True, "message": f"Updated client {client_id} RAG settings"}
        finally:
            conn.close()

    # Debug methods with enhanced logging
    def debug_clients(self):
        """Debug client data and RAG settings"""
        logger.info("🐛 DEBUG: Analyzing client data...")

        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            raise Exception("Client DB not found")

        try:
            has_rag_query = self._table_has_column(conn, "client", "rag_query")
            has_rag_filters = self._table_has_column(conn, "client", "rag_filter_json")

            logger.info(f"   📊 RAG columns: rag_query={has_rag_query}, rag_filters={has_rag_filters}")

            clients = self._get_clients(conn, ids=None, status="active")
            logger.info(f"   👥 Found {len(clients)} active clients")

            client_info = []
            for c in clients:
                info = {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "email": c.get("email"),
                    "permit_type": c.get("permit_type"),
                    "permit_class_mapped": c.get("permit_class_mapped"),
                    "city": c.get("city"),
                    "rag_query": c.get("rag_query"),
                    "rag_filters": c.get("rag_filters"),
                    "status": c.get("status")
                }
                client_info.append(info)
                logger.info(f"      👤 {info['name']}: city={info['city']}, type={info['permit_type']}")

            return {
                "success": True,
                "has_rag_query_column": has_rag_query,
                "has_rag_filters_column": has_rag_filters,
                "total_clients": len(clients),
                "clients": client_info
            }
        finally:
            conn.close()

    def full_debug_test(self):
        """Comprehensive RAG debug test"""
        logger.info("🐛 FULL DEBUG TEST STARTING...")

        try:
            # Test 1: Index status
            status = self.get_status()
            logger.info(f"   📊 Index status: {status}")

            # Test 2: Simple search without filters
            logger.info("   🧪 Test 1: Simple search without filters")
            simple_results = self.search_fixed("construction", top_k=5)
            logger.info(f"      Found {len(simple_results)} results")

            # Test 3: Search with city filter
            logger.info("   🧪 Test 2: Search with city filter")
            city_results = self.search_fixed("construction", top_k=5, filters={"city": "austin"})
            logger.info(f"      Found {len(city_results)} results for Austin")

            # Test 4: Search with multiple filters
            logger.info("   🧪 Test 3: Search with multiple filters")
            multi_results = self.search_fixed("construction", top_k=5, filters={
                "city": "austin",
                "permit_type": "Building Permit"
            })
            logger.info(f"      Found {len(multi_results)} results for Austin + Building Permit")

            return {
                "success": True,
                "message": "Debug test completed successfully",
                "results": {
                    "index_status": status,
                    "simple_search_count": len(simple_results),
                    "city_filter_count": len(city_results),
                    "multi_filter_count": len(multi_results)
                }
            }

        except Exception as e:
            logger.error(f"   ❌ Debug test failed: {e}")
            return {"success": False, "error": str(e)}

    def test_filters(self, query: str, city: Optional[str], permit_type: Optional[str],
                     permit_class: Optional[str], work_class: Optional[str], top_k: int):
        """Test specific filter combinations with enhanced logging"""
        logger.info(
            f"🧪 FILTER TEST: query='{query}', city={city}, type={permit_type}, class={permit_class}, work_class={work_class}")

        test_filters = {}
        if city:
            test_filters["city"] = city
        if permit_type:
            test_filters["permit_type"] = permit_type
        if permit_class:
            test_filters["permit_class_mapped"] = permit_class
        if work_class:
            test_filters["work_class"] = work_class

        logger.info(f"   🔧 Applying filters: {test_filters}")

        results_with_filters = self.search_fixed(query=query, top_k=top_k, filters=test_filters)
        results_no_filters = self.search_fixed(query=query, top_k=top_k, filters={})

        logger.info(f"   📊 Results: {len(results_with_filters)} with filters, {len(results_no_filters)} without")

        # Log some sample data to verify filtering
        if results_with_filters:
            sample = results_with_filters[0]
            logger.info(
                f"   📋 Sample filtered result: city={sample.get('city')}, type={sample.get('permit_type')}, class={sample.get('permit_class_mapped')}, work_class={sample.get('work_class')}")

        return {
            "success": True,
            "test_parameters": {
                "query": query,
                "filters_applied": test_filters,
                "top_k": top_k
            },
            "results": {
                "with_filters_count": len(results_with_filters),
                "without_filters_count": len(results_no_filters),
                "sample_with_filters": results_with_filters[:3] if results_with_filters else [],
                "sample_without_filters": results_no_filters[:3] if results_no_filters else []
            }
        }

    def debug_database_sample(self, limit: int = 10):
        """Check database contents with logging"""
        logger.info(f"🐛 DATABASE SAMPLE: Getting {limit} sample records")

        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            return {"success": False, "error": "Cannot connect to permits DB"}

        try:
            cur = conn.cursor()

            # Get table schema
            cur.execute("PRAGMA table_info(permits)")
            columns = [row[1] for row in cur.fetchall()]
            logger.info(f"   📋 Database columns: {len(columns)} total")

            # Get sample data
            cur.execute(f"SELECT * FROM permits ORDER BY id DESC LIMIT {limit}")
            rows = cur.fetchall()
            logger.info(f"   📊 Retrieved {len(rows)} sample records")

            # Get statistics
            cur.execute("SELECT COUNT(*) FROM permits")
            total_count = cur.fetchone()[0]

            cur.execute("SELECT DISTINCT city FROM permits WHERE city IS NOT NULL ORDER BY city")
            cities = [row[0] for row in cur.fetchall()]

            cur.execute("SELECT DISTINCT permit_type FROM permits WHERE permit_type IS NOT NULL ORDER BY permit_type")
            permit_types = [row[0] for row in cur.fetchall()]

            logger.info(
                f"   📈 Stats: {total_count} total permits, {len(cities)} cities, {len(permit_types)} permit types")

            return {
                "success": True,
                "database_info": {
                    "total_permits": total_count,
                    "columns": columns,
                    "available_cities": cities,
                    "available_permit_types": permit_types,
                    "sample_data": [dict(zip(columns, row)) for row in rows]
                }
            }
        finally:
            conn.close()

    def force_full_rebuild(self):
        """Force a complete rebuild of the index with new description-only format"""
        try:
            logger.info("🔄 FORCE REBUILD: Starting complete index rebuild...")

            # Delete existing index files to force complete rebuild
            import os
            if os.path.exists(self.rag_index.index_path):
                os.remove(self.rag_index.index_path)
            if os.path.exists(self.rag_index.idmap_path):
                os.remove(self.rag_index.idmap_path)
            if os.path.exists(self.rag_index.hashes_path):
                os.remove(self.rag_index.hashes_path)

            # Reset index in memory
            self.rag_index.index = None
            self.rag_index.id_map = None

            # Build fresh index
            result = self.rag_index.build(full_reindex=True, batch_size=256)
            logger.info(f"✅ FORCE REBUILD COMPLETE: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ FORCE REBUILD FAILED: {e}")
            raise e

    def incremental_reindex(self):
        """Incrementally rebuild RAG index - FIXED VERSION"""
        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            raise Exception("Cannot connect to permits DB")

        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM permits")
            total_permits = cur.fetchone()[0]

            # Check existing index
            index_status = self.rag_index.status()
            current_vectors = index_status.get("vectors", 0)

            if current_vectors == 0:
                # No existing index, do full rebuild
                logger.info("🔄 No existing index, doing full rebuild...")
                res = self.force_full_rebuild()
                return {"type": "full_rebuild", "summary": res}

            # ALWAYS do a full rebuild during automation to ensure description-only index
            # This is temporary until we confirm the index format is correct
            logger.info("🔄 AUTOMATION: Forcing full rebuild to ensure description-only index...")
            res = self.force_full_rebuild()
            return {"type": "forced_full_rebuild", "summary": res}

            # TODO: Uncomment this incremental logic once index format is verified
            # if total_permits <= current_vectors:
            #     return {"type": "no_new_data", "summary": "No new permits to index"}
            #
            # # Get new permit IDs
            # new_permits_count = total_permits - current_vectors
            # cur.execute("""
            #     SELECT id FROM permits
            #     ORDER BY id DESC
            #     LIMIT ?
            # """, (new_permits_count,))
            #
            # new_permit_ids = [row[0] for row in cur.fetchall()]
            #
            # # Do incremental rebuild
            # res = self.rag_index.build_incremental(permit_ids=new_permit_ids, batch_size=256)
            # return {"type": "incremental", "summary": res}

        finally:
            conn.close()

    def search_dual(self, query: str, top_k: int = 20, filters: Dict[str, Any] = None,
                    oversample: int = 5) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Perform both keyword and semantic search, return both result sets.

        Returns:
            Tuple of (keyword_results, semantic_results)
        """
        logger.info(f"🔍 DUAL SEARCH: query='{query}', filters={filters}, top_k={top_k}")

        filters = filters or {}

        # 1. Keyword search in descriptions
        logger.info("   📝 Performing keyword search...")
        keyword_results = self.rag_index.search_keywords_in_description(
            keywords=query,
            top_k=top_k * 2,  # Get more keyword results
            filters=filters,
            return_scores=True
        )
        logger.info(f"   📝 Keyword search: {len(keyword_results)} results")

        # 2. Semantic search
        logger.info("   🧠 Performing semantic search...")
        semantic_results = self.rag_index.search_fixed(
            query=query,
            top_k=top_k,
            filters=filters,
            oversample=oversample,
            return_scores=True
        )
        logger.info(f"   🧠 Semantic search: {len(semantic_results)} results")

        return keyword_results, semantic_results

    # def _get_clients_single_query(self, conn, ids=None, status=None):
    #     """Get everything in ONE query - no redundancy"""
    #     sql = """SELECT id, name, company, email, phone, address, city, state, zip_code,
    #              country, permit_type, permit_class_mapped, status,
    #              rag_query, rag_filter_json, keywords_include, keywords_exclude,
    #              work_classes FROM client WHERE 1=1"""
    #
    #     params = []
    #     if status:
    #         sql += " AND LOWER(status) = LOWER(?)"
    #         params.append(status)
    #     if ids:
    #         sql += f" AND id IN ({','.join('?' for _ in ids)})"
    #         params.extend(ids)
    #
    #     cursor = conn.cursor()
    #     cursor.execute(sql, params)
    #     columns = [desc[0] for desc in cursor.description]
    #     return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _get_clients_single_query(self, conn, ids=None, status=None):
        """Get everything in ONE query - including slider_percentage and priority"""
        sql = """SELECT id, name, company, email, phone, address, city, state, zip_code, 
                 country, permit_type, permit_class_mapped, status, 
                 rag_query, rag_filter_json, keywords_include, keywords_exclude,
                 slider_percentage, priority FROM client WHERE 1=1"""

        params = []
        if status:
            sql += " AND LOWER(status) = LOWER(?)"
            params.append(status)
        if ids:
            sql += f" AND id IN ({','.join('?' for _ in ids)})"
            params.extend(ids)

        sql += " ORDER BY priority ASC, id ASC"  # Order by priority first

        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        clients = [dict(zip(columns, row)) for row in cursor.fetchall()]

        # Parse JSON fields and get work_classes
        for client in clients:
            # Parse keywords
            if client.get('keywords_include'):
                try:
                    client['keywords_include'] = json.loads(client['keywords_include'])
                except:
                    client['keywords_include'] = []
            else:
                client['keywords_include'] = []

            if client.get('keywords_exclude'):
                try:
                    client['keywords_exclude'] = json.loads(client['keywords_exclude'])
                except:
                    client['keywords_exclude'] = []
            else:
                client['keywords_exclude'] = []

            # Get work_classes for this client
            client['work_classes'] = self._get_client_work_classes(client)

            # Ensure defaults for new fields
            client['slider_percentage'] = client.get('slider_percentage', 100)
            client['priority'] = client.get('priority', 999)

        return clients

    # def _remove_exclusion_keywords(self, permits, keywords_exclude):
    #     """Remove permits containing exclusion keywords"""
    #     if not keywords_exclude:
    #         return permits
    #
    #     clean_permits = []
    #     excluded_count = 0
    #
    #     for permit in permits:
    #         description = str(permit.get('description', '')).lower()
    #
    #         # Check if contains any exclusion keyword
    #         contains_excluded = False
    #         for keyword in keywords_exclude:
    #             if self._whole_word_match(description, keyword.lower()):
    #                 excluded_count += 1
    #                 contains_excluded = True
    #                 break
    #
    #         if not contains_excluded:
    #             clean_permits.append(permit)
    #
    #     logger.info(f"      🚫 Excluded {excluded_count} permits, {len(clean_permits)} remaining")
    #     return clean_permits

    def _remove_exclusion_keywords(self, permits, keywords_exclude):
        """Remove permits containing exclusion keywords"""
        if not keywords_exclude:
            return permits

        clean_permits = []
        excluded_count = 0

        for permit in permits:
            description = str(permit.get('description', '')).lower()

            # Check if contains any exclusion keyword
            contains_excluded = False
            for keyword in keywords_exclude:
                if self._whole_word_match(description, keyword.lower()):
                    excluded_count += 1
                    contains_excluded = True
                    break

            if not contains_excluded:
                clean_permits.append(permit)

        logger.info(f"      🚫 Excluded {excluded_count} permits, {len(clean_permits)} remaining")
        return clean_permits

    def _apply_distribution_limits(self, raw_assignments: Dict[int, Dict]) -> Dict[int, Dict]:
        """Apply slider_percentage limits and resolve overlaps"""
        logger.info("⚖️ =================================================================")
        logger.info("⚖️ APPLYING DISTRIBUTION LIMITS AND RESOLVING OVERLAPS")
        logger.info("⚖️ =================================================================")

        # Step 1: Apply percentage limits to each client
        limited_assignments = {}
        for client_id, data in raw_assignments.items():
            client = data['client']
            slider_percentage = client.get('slider_percentage', 100)
            priority = client.get('priority', 999)
            semantic_results = data['semantic_results']

            # Calculate how many permits this client should get
            max_permits = len(semantic_results)
            allowed_permits = int((slider_percentage / 100) * max_permits)

            logger.info(f"   👤 {client.get('name')}:")
            logger.info(f"      📊 Slider: {slider_percentage}% of {max_permits} = {allowed_permits} permits")
            logger.info(f"      🎯 Priority: {priority}")

            limited_assignments[client_id] = {
                'client': client,
                'inclusion_results': data['inclusion_results'],
                'exclusion_results': data['exclusion_results'],
                'semantic_results': semantic_results[:allowed_permits],  # Apply percentage limit
                'priority': priority,
                'original_count': max_permits,
                'limited_count': allowed_permits
            }

        # Step 2: Resolve overlaps (no permit to multiple clients)
        final_assignments = self._resolve_permit_overlaps(limited_assignments)

        logger.info("✅ DISTRIBUTION LIMITS AND OVERLAPS RESOLVED")
        return final_assignments

    def _resolve_permit_overlaps(self, assignments: Dict[int, Dict]) -> Dict[int, Dict]:
        """Ensure no permit goes to multiple clients - priority-based allocation"""
        logger.info("🔄 RESOLVING PERMIT OVERLAPS...")

        # Track which permits have been assigned
        assigned_permits = set()
        final_assignments = {}

        # Sort clients by priority (lower number = higher priority)
        sorted_clients = sorted(assignments.items(), key=lambda x: x[1]['priority'])

        logger.info(f"   📋 Processing {len(sorted_clients)} clients in priority order:")
        for client_id, data in sorted_clients:
            client_name = data['client'].get('name')
            priority = data['priority']
            logger.info(f"      {priority}: {client_name}")

        for client_id, data in sorted_clients:
            client_name = data['client'].get('name')
            priority = data['priority']
            semantic_results = data['semantic_results']
            original_count = len(semantic_results)

            logger.info(f"   👤 Processing {client_name} (priority: {priority})")
            logger.info(f"      📊 Requested: {original_count} permits")

            # Filter out already assigned permits
            unique_permits = []
            conflicts = 0

            for permit in semantic_results:
                permit_id = permit.get('id')
                if permit_id not in assigned_permits:
                    unique_permits.append(permit)
                    assigned_permits.add(permit_id)
                else:
                    conflicts += 1

            logger.info(f"      ✅ Assigned: {len(unique_permits)} permits")
            logger.info(f"      🔄 Conflicts resolved: {conflicts} permits")

            final_assignments[client_id] = {
                'client': data['client'],
                'inclusion_results': data['inclusion_results'],
                'exclusion_results': data['exclusion_results'],
                'semantic_results': unique_permits,
                'conflicts_resolved': conflicts,
                'fulfillment_rate': len(unique_permits) / original_count * 100 if original_count > 0 else 100
            }

            fulfillment_rate = final_assignments[client_id]['fulfillment_rate']
            logger.info(f"      📊 Fulfillment rate: {fulfillment_rate:.1f}%")

        return final_assignments
    def _process_single_client(self, conn, client, req):
        """Sequential filtering: Column → Include → Exclude → Semantic"""

        # Step 1: Basic column filtering
        filters = self._build_simple_filters(client)
        base_permits = self._filter_permits_simple(conn, filters)

        # Step 2: Apply inclusion keywords
        keywords_include = client.get('keywords_include', [])
        if keywords_include:
            inclusion_filtered = self._search_inclusion_keywords(base_permits, keywords_include)
        else:
            inclusion_filtered = base_permits

        # Step 3: Apply exclusion keywords (remove unwanted permits)
        keywords_exclude = client.get('keywords_exclude', [])
        if keywords_exclude:
            final_filtered = self._remove_exclusion_keywords(inclusion_filtered, keywords_exclude)
            excluded_csv = self._search_exclusion_keywords(base_permits, keywords_exclude)  # For tracking
        else:
            final_filtered = inclusion_filtered
            excluded_csv = []

        # Step 4: Semantic search on fully filtered permits
        query = client.get('rag_query') or self._determine_query(client)
        semantic_csv = self.rag_index._semantic_search_within_permits(final_filtered, query, 20, True)  # ✅ Correct!

        return {
            'keywords_csv': inclusion_filtered,  # All permits that matched inclusion
            'excluded_csv': excluded_csv,  # All permits that matched exclusion (for tracking)
            'semantic_csv': semantic_csv  # Top 20 semantic matches from clean permits
        }



    def process_clients_optimized(self, req: ClientRAGRequest):
        """Clean, optimized version - no redundancy"""

        # Single DB connection for everything
        conn = sqlite3.connect(self.permits_db_path)
        try:
            # Get ALL client data in ONE query (no schema checking, no separate queries)
            clients = self._get_clients_single_query(conn, req.selection.client_ids, req.selection.status)

            results = {}
            for client in clients:
                # Three-step filtering for each client
                results[client['id']] = self._process_single_client(conn, client, req)

            return results

        finally:
            conn.close()

    def _build_simple_filters(self, client):
        """Build filters without over-engineering"""
        filters = {}

        if client.get('city'):
            filters['city'] = [client['city']]
        if client.get('permit_type'):
            filters['permit_type'] = [client['permit_type']]
        if client.get('permit_class_mapped'):
            filters['permit_class_mapped'] = [client['permit_class_mapped']]
        if client.get('work_classes'):
            filters['work_class'] = [wc['name'] for wc in client['work_classes']]

        return filters

    def _filter_permits_simple(self, conn, filters):
        """Simple filtering without over-normalization"""
        sql = "SELECT * FROM permits WHERE 1=1"
        params = []

        for key, values in filters.items():
            if values:
                placeholders = ','.join('?' for _ in values)
                sql += f" AND LOWER({key}) IN ({placeholders})"
                params.extend([v.lower() for v in values])

        sql += " ORDER BY issued_date DESC LIMIT 1000"

        cursor = conn.cursor()
        cursor.execute(sql, params)
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
    # NEW: Client assignment method with dual search
    def build_client_assignments_dual(self, req: ClientRAGRequest) -> Tuple[
        Dict[int, Dict[str, Any]], Dict[int, Dict[str, Any]]]:
        """
        Build client assignments using dual search (keyword + semantic).
        Returns assignments with both keyword and semantic results.
        """
        logger.info("🔄 =================================================================")
        logger.info("🔄 STARTING BUILD_CLIENT_ASSIGNMENTS_DUAL")
        logger.info("🔄 =================================================================")

        logger.info(f"📋 DUAL INPUT REQUEST ANALYSIS:")
        logger.info(f"   🔍 Query: '{req.query}' (length: {len(req.query) if req.query else 0})")
        logger.info(f"   🎛️ Filters: {req.filters} (count: {len(req.filters) if req.filters else 0})")
        logger.info(f"   ⚙️ Settings:")
        logger.info(f"      - use_client_prefs: {req.use_client_prefs}")
        logger.info(f"      - exclusive: {req.exclusive}")
        logger.info(f"   📊 Limits:")
        logger.info(f"      - per_client_top_k: {req.per_client_top_k}")
        logger.info(f"      - oversample: {req.oversample}")

        logger.info("🔌 CONNECTING TO DATABASE (DUAL)...")
        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            logger.error("❌ CLIENT DB CONNECTION FAILED (DUAL)")
            raise Exception("Client DB not found")
        logger.info("✅ DATABASE CONNECTION ESTABLISHED (DUAL)")

        try:
            logger.info("👥 FETCHING CLIENTS (DUAL)...")
            print("***********************see the status*******************************")
            print(req.selection.status)
            clients = self._get_clients_single_query(conn, ids=req.selection.client_ids, status=req.selection.status)
            logger.info(f"✅ FOUND {len(clients)} CLIENTS (DUAL)")

            # Decision point: 2 clients + exclusive = special case
            if len(clients) == 2 and req.exclusive:
                logger.info("⚖️ DUAL SPECIAL CASE: 2 clients + exclusive")
                logger.info("⚖️ Routing to 75/25 dual distribution logic")
                result = self._handle_75_25_dual_distribution(clients, req)
                logger.info("✅ 75/25 DUAL DISTRIBUTION COMPLETED")
                return result

            # Individual client processing with dual search
            logger.info("👤 DUAL STANDARD CASE: Using individual dual client processing")
            result = self._handle_individual_dual_assignments(clients, req)
            logger.info("✅ INDIVIDUAL DUAL ASSIGNMENTS COMPLETED")
            return result

        except Exception as e:
            logger.error(f"❌ ERROR in build_client_assignments_dual: {e}")
            raise
        finally:
            logger.info("🔌 CLOSING DATABASE CONNECTION (DUAL)")
            conn.close()

    # def _handle_individual_dual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
    #     """Handle individual client assignments with dual search"""
    #     logger.info("🔄 =================================================================")
    #     logger.info("🔄 STARTING INDIVIDUAL DUAL ASSIGNMENTS")
    #     logger.info("🔄 =================================================================")
    #
    #     raw_assignments = {}
    #     logger.info(f"📊 Processing {len(clients)} clients with dual search")
    #
    #     for i, c in enumerate(clients, 1):
    #         logger.info(f"👤 ===============================================")
    #         logger.info(f"👤 DUAL PROCESSING CLIENT {i}/{len(clients)}")
    #         logger.info(f"👤 ===============================================")
    #
    #         cid = int(c["id"])
    #         client_name = c.get("name", "Unknown")
    #         logger.info(f"   📇 Client Details:")
    #         logger.info(f"      - Name: {client_name}")
    #         logger.info(f"      - ID: {cid}")
    #
    #         # Determine query and filters
    #         logger.info(f"   🔍 DETERMINING QUERY (DUAL)...")
    #         query = self._determine_query(c, req)
    #         logger.info(f"   ✅ Query: '{query}'")
    #
    #         logger.info(f"   🔧 BUILDING FILTERS (DUAL)...")
    #         filters = self._build_filters_for_client(c, req)
    #         logger.info(f"   ✅ Filters: {filters}")
    #
    #         # Perform dual search
    #         if query and query.strip():
    #             logger.info(f"   🔄 EXECUTING DUAL SEARCH...")
    #             logger.info(f"      📊 Parameters:")
    #             logger.info(f"         - query: '{query}'")
    #             logger.info(f"         - top_k: {req.per_client_top_k or 20}")
    #             logger.info(f"         - filters: {filters}")
    #
    #             dual_start_time = time.time()
    #             keyword_results, semantic_results = self.search_dual(
    #                 query=query,
    #                 top_k=req.per_client_top_k or 20,
    #                 filters=filters
    #             )
    #             dual_end_time = time.time()
    #             dual_duration = dual_end_time - dual_start_time
    #
    #             logger.info(f"   ✅ DUAL SEARCH COMPLETED ({dual_duration:.2f}s)")
    #         else:
    #             logger.info(f"   📋 NO QUERY - USING FILTER-ONLY RETRIEVAL...")
    #
    #             filter_start_time = time.time()
    #             keyword_results = self.rag_index.search_keywords_in_description(
    #                 keywords="",
    #                 top_k=req.per_client_top_k or 20,
    #                 filters=filters
    #             )
    #             semantic_results = []
    #             filter_end_time = time.time()
    #             dual_duration = filter_end_time - filter_start_time
    #
    #             logger.info(f"   ✅ FILTER-ONLY RETRIEVAL COMPLETED ({dual_duration:.2f}s)")
    #
    #         logger.info(f"   📊 DUAL RESULTS SUMMARY:")
    #         logger.info(f"      🔤 Keyword results: {len(keyword_results)}")
    #         logger.info(f"      🧠 Semantic results: {len(semantic_results)}")
    #         logger.info(f"      📄 Total results: {len(keyword_results) + len(semantic_results)}")
    #
    #         # Log sample results for each type
    #         if keyword_results:
    #             logger.info(f"      🔤 Sample keyword results:")
    #             for j, row in enumerate(keyword_results[:2], 1):
    #                 permit_id = row.get('id', 'N/A')
    #                 address = row.get('address', 'N/A')
    #                 logger.info(f"         {j}. ID: {permit_id}, Address: {address}")
    #
    #         if semantic_results:
    #             logger.info(f"      🧠 Sample semantic results:")
    #             for j, row in enumerate(semantic_results[:2], 1):
    #                 permit_id = row.get('id', 'N/A')
    #                 address = row.get('address', 'N/A')
    #                 logger.info(f"         {j}. ID: {permit_id}, Address: {address}")
    #
    #         # Store both result sets
    #         raw_assignments[cid] = {
    #             "client": c,
    #             "keyword_results": keyword_results,
    #             "semantic_results": semantic_results,
    #             "query": query,
    #             "filters": filters,
    #             "search_duration": dual_duration
    #         }
    #
    #     logger.info("📊 DUAL RAW ASSIGNMENTS SUMMARY:")
    #     total_keyword = 0
    #     total_semantic = 0
    #     for cid, data in raw_assignments.items():
    #         client_name = data["client"].get("name", "Unknown")
    #         keyword_count = len(data["keyword_results"])
    #         semantic_count = len(data["semantic_results"])
    #         duration = data.get("search_duration", 0)
    #         total_keyword += keyword_count
    #         total_semantic += semantic_count
    #         logger.info(f"   👤 {client_name}:")
    #         logger.info(f"      🔤 Keyword: {keyword_count}, 🧠 Semantic: {semantic_count} ({duration:.2f}s)")
    #
    #     logger.info(f"📊 TOTALS: 🔤 {total_keyword} keyword, 🧠 {total_semantic} semantic")
    #
    #     # Apply exclusive distribution if requested
    #     if req.exclusive:
    #         logger.info("⚖️ ===============================================")
    #         logger.info("⚖️ APPLYING EXCLUSIVE DISTRIBUTION (DUAL)")
    #         logger.info("⚖️ ===============================================")
    #
    #         exclusive_start_time = time.time()
    #         final_assignments = self._distribute_exclusive_dual(raw_assignments)
    #         exclusive_end_time = time.time()
    #         exclusive_duration = exclusive_end_time - exclusive_start_time
    #
    #         logger.info(f"✅ DUAL EXCLUSIVE DISTRIBUTION COMPLETED ({exclusive_duration:.2f}s)")
    #     else:
    #         logger.info("📋 NO EXCLUSIVE DISTRIBUTION REQUESTED (DUAL)")
    #         final_assignments = {
    #             cid: {
    #                 "client": payload["client"],
    #                 "keyword_results": list(payload["keyword_results"]),
    #                 "semantic_results": list(payload["semantic_results"])
    #             }
    #             for cid, payload in raw_assignments.items()
    #         }
    #
    #     logger.info("🎉 INDIVIDUAL DUAL ASSIGNMENTS PROCESS COMPLETED")
    #     return raw_assignments, final_assignments

    # def _handle_individual_dual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
    #     """Handle individual client assignments with 3-CSV independent search system"""
    #     logger.info("🔄 =================================================================")
    #     logger.info("🔄 STARTING 3-CSV INDEPENDENT SEARCH SYSTEM")
    #     logger.info("🔄 =================================================================")
    #
    #     raw_assignments = {}
    #     logger.info(f"📊 Processing {len(clients)} clients with 3-CSV system")
    #
    #     for i, c in enumerate(clients, 1):
    #         logger.info(f"👤 ===============================================")
    #         logger.info(f"👤 3-CSV PROCESSING CLIENT {i}/{len(clients)}")
    #         logger.info(f"👤 ===============================================")
    #
    #         cid = int(c["id"])
    #         client_name = c.get("name", "Unknown")
    #         logger.info(f"   📇 Client Details:")
    #         logger.info(f"      - Name: {client_name}")
    #         logger.info(f"      - ID: {cid}")
    #
    #         # Determine query, keywords, and filters
    #         logger.info(f"   🔍 DETERMINING QUERY...")
    #         query = self._determine_query(c, req)
    #         logger.info(f"   ✅ Query: '{query}'")
    #
    #         logger.info(f"   🔤 DETERMINING KEYWORDS...")
    #         keywords_include, keywords_exclude = self._determine_keywords(c, req)
    #         logger.info(f"   ✅ Include keywords: {keywords_include}")
    #         logger.info(f"   ✅ Exclude keywords: {keywords_exclude}")
    #
    #         logger.info(f"   🔧 BUILDING FILTERS...")
    #         filters = self._build_filters_for_client(c, req)
    #         logger.info(f"   ✅ Filters: {filters}")
    #
    #         # STEP 1: Get base filtered permits (using existing filter logic)
    #         logger.info(f"   📊 STEP 1: Getting base filtered permits...")
    #         dual_start_time = time.time()
    #
    #         if filters and any(filters.values()):
    #             db_limit = max((req.per_client_top_k or 20) * (req.oversample or 5), 1000)
    #             base_permits = self.rag_index._get_filtered_permits_from_db_simple(filters, db_limit)
    #             logger.info(f"      📊 Base filtered permits: {len(base_permits)}")
    #         else:
    #             db_limit = max((req.per_client_top_k or 20) * 3, 500)
    #             base_permits = self.rag_index._get_recent_permits_simple(db_limit)
    #             logger.info(f"      📊 Base recent permits: {len(base_permits)}")
    #
    #         if not base_permits:
    #             logger.warning("      ⚠️ No base permits found")
    #             raw_assignments[cid] = {
    #                 "client": c,
    #                 "inclusion_results": [],
    #                 "exclusion_results": [],
    #                 "semantic_results": [],
    #                 "query": query,
    #                 "keywords_include": keywords_include,
    #                 "keywords_exclude": keywords_exclude,
    #                 "filters": filters,
    #                 "search_duration": 0
    #             }
    #             continue
    #
    #         # STEP 2: Independent CSV #1 - Inclusion Keywords Search
    #         logger.info(f"   🔍 STEP 2: Inclusion Keywords Search (CSV #1)...")
    #         inclusion_results = []
    #         if keywords_include:
    #             inclusion_results = self._search_inclusion_keywords(base_permits, keywords_include)
    #             logger.info(f"      ✅ Inclusion results: {len(inclusion_results)} permits")
    #         else:
    #             logger.info(f"      📋 No inclusion keywords specified")
    #
    #         # STEP 3: Independent CSV #2 - Exclusion Keywords Search (for tracking)
    #         logger.info(f"   🚫 STEP 3: Exclusion Keywords Search (CSV #2)...")
    #         exclusion_results = []
    #         if keywords_exclude:
    #             exclusion_results = self._search_exclusion_keywords(base_permits, keywords_exclude)
    #             logger.info(f"      📊 Exclusion tracking results: {len(exclusion_results)} permits")
    #         else:
    #             logger.info(f"      📋 No exclusion keywords specified")
    #
    #         # STEP 4: Independent CSV #3 - Semantic Search
    #         logger.info(f"   🧠 STEP 4: Semantic Search (CSV #3)...")
    #         semantic_results = []
    #         if query and query.strip():
    #             semantic_results = self.rag_index._semantic_search_within_permits(
    #                 base_permits, query, req.per_client_top_k or 20, return_scores=True
    #             )
    #             logger.info(f"      🧠 Semantic results: {len(semantic_results)} permits")
    #         else:
    #             logger.info(f"      📋 No query provided for semantic search")
    #
    #         dual_end_time = time.time()
    #         dual_duration = dual_end_time - dual_start_time
    #
    #         logger.info(f"   ✅ 3-CSV SEARCH COMPLETED ({dual_duration:.2f}s)")
    #         logger.info(f"   📊 FINAL RESULTS SUMMARY:")
    #         logger.info(f"      🔍 Inclusion CSV: {len(inclusion_results)} permits")
    #         logger.info(f"      🚫 Exclusion CSV: {len(exclusion_results)} permits")
    #         logger.info(f"      🧠 Semantic CSV: {len(semantic_results)} permits")
    #
    #         # Store all three result sets
    #         raw_assignments[cid] = {
    #             "client": c,
    #             "inclusion_results": inclusion_results,
    #             "exclusion_results": exclusion_results,
    #             "semantic_results": semantic_results,
    #             "query": query,
    #             "keywords_include": keywords_include,
    #             "keywords_exclude": keywords_exclude,
    #             "filters": filters,
    #             "search_duration": dual_duration
    #         }
    #
    #     # Log summary
    #     logger.info("📊 3-CSV RAW ASSIGNMENTS SUMMARY:")
    #     total_inclusion = 0
    #     total_exclusion = 0
    #     total_semantic = 0
    #     for cid, data in raw_assignments.items():
    #         client_name = data["client"].get("name", "Unknown")
    #         inclusion_count = len(data["inclusion_results"])
    #         exclusion_count = len(data["exclusion_results"])
    #         semantic_count = len(data["semantic_results"])
    #         duration = data.get("search_duration", 0)
    #         total_inclusion += inclusion_count
    #         total_exclusion += exclusion_count
    #         total_semantic += semantic_count
    #         logger.info(f"   👤 {client_name}:")
    #         logger.info(
    #             f"      🔍 Inclusion: {inclusion_count}, 🚫 Exclusion: {exclusion_count}, 🧠 Semantic: {semantic_count} ({duration:.2f}s)")
    #
    #     logger.info(
    #         f"📊 TOTALS: 🔍 {total_inclusion} inclusion, 🚫 {total_exclusion} exclusion, 🧠 {total_semantic} semantic")
    #
    #     # Apply exclusive distribution if requested (distribute each CSV type separately)
    #     if req.exclusive:
    #         logger.info("⚖️ ===============================================")
    #         logger.info("⚖️ APPLYING EXCLUSIVE DISTRIBUTION (3-CSV)")
    #         logger.info("⚖️ ===============================================")
    #
    #         exclusive_start_time = time.time()
    #         final_assignments = self._distribute_exclusive_three_csv(raw_assignments)
    #         exclusive_end_time = time.time()
    #         exclusive_duration = exclusive_end_time - exclusive_start_time
    #
    #         logger.info(f"✅ 3-CSV EXCLUSIVE DISTRIBUTION COMPLETED ({exclusive_duration:.2f}s)")
    #     else:
    #         logger.info("📋 NO EXCLUSIVE DISTRIBUTION REQUESTED")
    #         final_assignments = {
    #             cid: {
    #                 "client": payload["client"],
    #                 "inclusion_results": list(payload["inclusion_results"]),
    #                 "exclusion_results": list(payload["exclusion_results"]),
    #                 "semantic_results": list(payload["semantic_results"])
    #             }
    #             for cid, payload in raw_assignments.items()
    #         }
    #
    #     logger.info("🎉 3-CSV INDEPENDENT SEARCH SYSTEM COMPLETED")
    #     return raw_assignments, final_assignments

    # def _handle_individual_dual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
    #     """FIXED: Sequential filtering instead of parallel"""
    #     logger.info("🔄 STARTING SEQUENTIAL FILTERING SYSTEM")
    #
    #     raw_assignments = {}
    #
    #     for i, c in enumerate(clients, 1):
    #         logger.info(f"👤 PROCESSING CLIENT {i}/{len(clients)}: {c.get('name')}")
    #
    #         cid = int(c["id"])
    #         query = self._determine_query(c, req)
    #         keywords_include, keywords_exclude = self._determine_keywords(c, req)
    #         filters = self._build_filters_for_client(c, req)
    #
    #         # STEP 1: Basic column filtering
    #         logger.info("📊 STEP 1: Column filtering...")
    #         base_permits = self.rag_index._get_filtered_permits_from_db_simple(filters, 1000)
    #         logger.info(f"   📊 Base permits: {len(base_permits)}")
    #
    #         # STEP 2: Apply inclusion keywords
    #         logger.info("🔍 STEP 2: Inclusion filtering...")
    #         if keywords_include:
    #             inclusion_filtered = self._search_inclusion_keywords(base_permits, keywords_include)
    #         else:
    #             inclusion_filtered = base_permits
    #         logger.info(f"   📊 After inclusion: {len(inclusion_filtered)}")
    #
    #         # STEP 3: Remove exclusion keywords
    #         logger.info("🚫 STEP 3: Exclusion removal...")
    #         if keywords_exclude:
    #             clean_permits = self._remove_exclusion_keywords(inclusion_filtered, keywords_exclude)
    #             excluded_csv = self._search_exclusion_keywords(base_permits, keywords_exclude)  # For tracking
    #         else:
    #             clean_permits = inclusion_filtered
    #             excluded_csv = []
    #         logger.info(f"   📊 After exclusion removal: {len(clean_permits)}")
    #
    #         # STEP 4: Semantic search on CLEAN permits
    #         logger.info("🧠 STEP 4: Semantic search on clean permits...")
    #         if query and query.strip():
    #             semantic_results = self.rag_index._semantic_search_within_permits(
    #                 clean_permits, query, 20, return_scores=True  # ← Clean permits, not base_permits!
    #             )
    #         else:
    #             semantic_results = clean_permits[:20]
    #         logger.info(f"   📊 Semantic results: {len(semantic_results)}")
    #
    #         raw_assignments[cid] = {
    #             "client": c,
    #             "inclusion_results": inclusion_filtered,
    #             "exclusion_results": excluded_csv,
    #             "semantic_results": semantic_results,
    #         }
    #
    #     return raw_assignments, raw_assignments
    #above one final one
    # def _handle_individual_dual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
    #     """Sequential filtering with distribution limits"""
    #     logger.info("🔄 STARTING SEQUENTIAL FILTERING SYSTEM")
    #
    #     raw_assignments = {}
    #
    #     # Step 1-4: Sequential filtering for each client
    #     for i, c in enumerate(clients, 1):
    #         logger.info(f"👤 PROCESSING CLIENT {i}/{len(clients)}: {c.get('name')}")
    #
    #         cid = int(c["id"])
    #         query = self._determine_query(c, req)
    #         keywords_include, keywords_exclude = self._determine_keywords(c, req)
    #         filters = self._build_filters_for_client(c, req)
    #
    #         # STEP 1: Basic column filtering
    #         logger.info("📊 STEP 1: Column filtering...")
    #         base_permits = self.rag_index._get_filtered_permits_from_db_simple(filters, 1000)
    #         logger.info(f"   📊 Base permits: {len(base_permits)}")
    #
    #         # STEP 2: Apply inclusion keywords
    #         logger.info("🔍 STEP 2: Inclusion filtering...")
    #         if keywords_include:
    #             inclusion_filtered = self._search_inclusion_keywords(base_permits, keywords_include)
    #         else:
    #             inclusion_filtered = base_permits
    #         logger.info(f"   📊 After inclusion: {len(inclusion_filtered)}")
    #
    #         # STEP 3: Remove exclusion keywords
    #         logger.info("🚫 STEP 3: Exclusion removal...")
    #         if keywords_exclude:
    #             clean_permits = self._remove_exclusion_keywords(inclusion_filtered, keywords_exclude)
    #             excluded_csv = self._search_exclusion_keywords(base_permits, keywords_exclude)  # For tracking
    #         else:
    #             clean_permits = inclusion_filtered
    #             excluded_csv = []
    #         logger.info(f"   📊 After exclusion removal: {len(clean_permits)}")
    #
    #         # STEP 4: Semantic search on CLEAN permits
    #         logger.info("🧠 STEP 4: Semantic search on clean permits...")
    #         if query and query.strip():
    #             semantic_results = self._semantic_search_within_permits_improved(
    #                 clean_permits, query, 100, True  # Get more results before distribution limits
    #             )
    #         else:
    #             semantic_results = clean_permits[:100]
    #         logger.info(f"   📊 Semantic results: {len(semantic_results)}")
    #
    #         raw_assignments[cid] = {
    #             "client": c,
    #             "inclusion_results": inclusion_filtered,
    #             "exclusion_results": excluded_csv,
    #             "semantic_results": semantic_results,
    #         }
    #
    #     # Step 5: Apply distribution limits and resolve overlaps
    #     if len(clients) > 1 or any(c.get('slider_percentage', 100) < 100 for c in clients):
    #         logger.info("⚖️ APPLYING DISTRIBUTION SYSTEM...")
    #         final_assignments = self._apply_distribution_limits(raw_assignments)
    #     else:
    #         logger.info("📋 NO DISTRIBUTION NEEDED (single client, 100%)")
    #         final_assignments = raw_assignments
    #
    #     return raw_assignments, final_assignments

    def _handle_individual_dual_assignments(self, clients: List[Dict], req: ClientRAGRequest):
        """Sequential filtering with proportional group distribution"""
        logger.info("🔄 STARTING SEQUENTIAL FILTERING SYSTEM")

        raw_assignments = {}

        # Step 1-4: Sequential filtering for each client
        for i, c in enumerate(clients, 1):
            logger.info(f"👤 PROCESSING CLIENT {i}/{len(clients)}: {c.get('name')}")

            cid = int(c["id"])
            query = self._determine_query(c, req)
            keywords_include, keywords_exclude = self._determine_keywords(c, req)
            filters = self._build_filters_for_client(c, req)

            # STEP 1: Basic column filtering
            logger.info("📊 STEP 1: Column filtering...")
            base_permits = self.rag_index._get_filtered_permits_from_db_simple(filters, 1000)
            logger.info(f"   📊 Base permits: {len(base_permits)}")

            # STEP 2: Apply inclusion keywords
            logger.info("🔍 STEP 2: Inclusion filtering...")
            if keywords_include:
                inclusion_filtered = self._search_inclusion_keywords(base_permits, keywords_include)
            else:
                inclusion_filtered = base_permits
            logger.info(f"   📊 After inclusion: {len(inclusion_filtered)}")

            # STEP 3: Remove exclusion keywords
            logger.info("🚫 STEP 3: Exclusion removal...")
            if keywords_exclude:
                clean_permits = self._remove_exclusion_keywords(inclusion_filtered, keywords_exclude)
                excluded_csv = self._search_exclusion_keywords(base_permits, keywords_exclude)  # For tracking
            else:
                clean_permits = inclusion_filtered
                excluded_csv = []
            logger.info(f"   📊 After exclusion removal: {len(clean_permits)}")

            # STEP 4: Semantic search on CLEAN permits
            logger.info("🧠 STEP 4: Semantic search on clean permits...")
            if query and query.strip():
                semantic_results = self._semantic_search_within_permits_improved(
                    clean_permits, query, 200, True  # Get more results before group distribution
                )
            else:
                semantic_results = clean_permits[:200]
            logger.info(f"   📊 Semantic results: {len(semantic_results)}")

            raw_assignments[cid] = {
                "client": c,
                "inclusion_results": inclusion_filtered,
                "exclusion_results": excluded_csv,
                "semantic_results": semantic_results,
            }

        # Step 5: Apply proportional group distribution
        logger.info("📊 APPLYING PROPORTIONAL GROUP DISTRIBUTION...")
        final_assignments = self._apply_proportional_group_distribution(raw_assignments)

        return raw_assignments, final_assignments

    def _group_clients_by_filters(self, clients):
        """Group clients who compete for same permits based on basic filters"""
        groups = {}

        logger.info(f"📊 Grouping {len(clients)} clients")

        for i, client in enumerate(clients):
            logger.info(f"📊 Processing client {i}: {type(client)}")

            if not isinstance(client, dict):
                logger.error(f"❌ Client {i} is not a dict: {client}")
                continue

            # Debug client structure
            logger.info(f"📊 Client {i} keys: {list(client.keys()) if isinstance(client, dict) else 'Not a dict'}")

            # Create group key based on competing criteria
            try:
                work_classes_raw = client.get('work_classes', [])
                logger.info(f"📊 Client {i} work_classes: {work_classes_raw} (type: {type(work_classes_raw)})")

                if isinstance(work_classes_raw, list):
                    work_classes = tuple(
                        sorted([wc['name'] if isinstance(wc, dict) else str(wc) for wc in work_classes_raw]))
                else:
                    work_classes = ()

                group_key = (
                    client.get('permit_type', ''),
                    client.get('permit_class_mapped', ''),
                    client.get('city', ''),
                    work_classes
                )

                logger.info(f"📊 Client {i} group_key: {group_key}")

                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(client)

            except Exception as e:
                logger.error(f"❌ Error processing client {i}: {e}")
                logger.error(f"❌ Client data: {client}")

        logger.info(f"📊 Created {len(groups)} groups")
        return groups

    def _apply_proportional_group_distribution(self, raw_assignments):
        """Apply proportional distribution within competing groups"""
        logger.info("📊 =================================================================")
        logger.info("📊 APPLYING PROPORTIONAL GROUP DISTRIBUTION")
        logger.info("📊 =================================================================")

        # Debug: Check the structure of raw_assignments
        logger.info(f"📊 Raw assignments keys: {list(raw_assignments.keys())}")
        for key, value in raw_assignments.items():
            logger.info(f"📊 Assignment {key} structure: {type(value)}")
            if isinstance(value, dict):
                logger.info(f"📊 Assignment {key} client type: {type(value.get('client'))}")

        # Extract clients safely
        clients = []
        for client_id, data in raw_assignments.items():
            if isinstance(data, dict) and 'client' in data:
                client = data['client']
                if isinstance(client, dict):
                    clients.append(client)
                else:
                    logger.error(f"❌ Client data for {client_id} is not a dict: {type(client)}")
            else:
                logger.error(f"❌ Invalid data structure for {client_id}: {type(data)}")

        logger.info(f"📊 Extracted {len(clients)} valid clients")

        # Group clients by their filter criteria
        clients_by_group = self._group_clients_by_filters(clients)

        final_assignments = {}
        global_assigned_permits = set()

        for group_key, group_clients in clients_by_group.items():
            logger.info(f"📊 Processing group: {group_key}")
            logger.info(
                "   👥 Clients in group: "
                + str([f"{c['name']}(ID:{c['id']})" for c in group_clients])
            )

            if len(group_clients) == 1:
                # No competition - single client gets their allocation
                logger.info("   📋 Single client - no competition")
                client = group_clients[0]
                client_id = client['id']
                data = raw_assignments.get(client_id, {})

                # Apply slider percentage
                slider_percentage = client.get('slider_percentage', 100)
                semantic_results = data.get('semantic_results', [])
                allowed_count = int((slider_percentage / 100) * len(semantic_results))

                # Filter out globally assigned permits
                unique_permits = []
                for permit in semantic_results[:allowed_count]:
                    if permit['id'] not in global_assigned_permits:
                        unique_permits.append(permit)
                        global_assigned_permits.add(permit['id'])

                logger.info(f"   ✅ {client['name']}: {len(unique_permits)} permits")

                final_assignments[client_id] = {
                    'client': client,
                    'inclusion_results': data.get('inclusion_results', []),
                    'exclusion_results': data.get('exclusion_results', []),
                    'semantic_results': unique_permits,
                }
            else:
                # Competition - apply proportional distribution
                logger.info("   ⚖️ Multiple clients - applying proportional distribution")
                self._distribute_competing_group(
                    group_clients,
                    raw_assignments,
                    final_assignments,
                    global_assigned_permits
                )

        logger.info("✅ PROPORTIONAL GROUP DISTRIBUTION COMPLETED")
        return final_assignments

    def _distribute_competing_group(self, group_clients, raw_assignments, final_assignments, global_assigned_permits):
        """Distribute permits proportionally within a competing group"""

        # Collect all unique permits from this group
        group_permits_pool = {}  # permit_id -> permit_data
        client_permit_scores = {}  # client_id -> {permit_id -> score}

        for client in group_clients:
            client_id = client['id']
            data = raw_assignments[client_id]
            client_permit_scores[client_id] = {}

            for permit in data['semantic_results']:
                permit_id = permit['id']
                if permit_id not in global_assigned_permits:
                    group_permits_pool[permit_id] = permit
                    # Store the score this client gave this permit
                    score = permit.get('_rag_score', 0.5)
                    client_permit_scores[client_id][permit_id] = score

        total_permits = len(group_permits_pool)
        logger.info(f"   📊 Total unique permits in group: {total_permits}")

        if total_permits == 0:
            # No permits available
            for client in group_clients:
                client_id = client['id']
                data = raw_assignments[client_id]
                final_assignments[client_id] = {
                    'client': client,
                    'inclusion_results': data['inclusion_results'],
                    'exclusion_results': data['exclusion_results'],
                    'semantic_results': []
                }
            return

        # Calculate proportional allocation
        total_demand = sum(client.get('slider_percentage', 100) for client in group_clients)
        logger.info(f"   📊 Total demand: {total_demand}%")

        # Calculate each client's allocation
        allocations = {}
        for client in group_clients:
            client_id = client['id']
            client_percentage = client.get('slider_percentage', 100)

            if total_demand > 0:
                proportion = client_percentage / total_demand
                allocated_count = max(1, int(proportion * total_permits))  # At least 1 permit if they want any
            else:
                allocated_count = 0

            allocations[client_id] = allocated_count
            logger.info(f"   👤 {client['name']}: {client_percentage}% → {allocated_count} permits")

        # Rank permits by average score across all clients
        permit_rankings = []
        for permit_id, permit_data in group_permits_pool.items():
            scores = [client_permit_scores[cid].get(permit_id, 0) for cid in client_permit_scores.keys()]
            avg_score = sum(scores) / len(scores) if scores else 0
            permit_rankings.append((avg_score, permit_id, permit_data))

        # Sort by score (highest first)
        permit_rankings.sort(key=lambda x: x[0], reverse=True)

        # Distribute permits using round-robin with priorities
        sorted_clients = sorted(group_clients, key=lambda x: x.get('priority', 999))
        client_assignments = {c['id']: [] for c in group_clients}
        permit_index = 0

        # Round-robin distribution
        while permit_index < len(permit_rankings) and any(
                len(client_assignments[c['id']]) < allocations[c['id']] for c in group_clients):
            for client in sorted_clients:
                client_id = client['id']
                if len(client_assignments[client_id]) < allocations[client_id] and permit_index < len(permit_rankings):
                    score, permit_id, permit_data = permit_rankings[permit_index]
                    client_assignments[client_id].append(permit_data)
                    global_assigned_permits.add(permit_id)
                    permit_index += 1

        # Create final assignments
        for client in group_clients:
            client_id = client['id']
            data = raw_assignments[client_id]
            assigned_permits = client_assignments[client_id]

            logger.info(f"   ✅ {client['name']}: {len(assigned_permits)} permits assigned")

            final_assignments[client_id] = {
                'client': client,
                'inclusion_results': data['inclusion_results'],
                'exclusion_results': data['exclusion_results'],
                'semantic_results': assigned_permits
            }


    def _search_inclusion_keywords(self, permits: List[Dict[str, Any]], keywords_include: List[str]) -> List[
        Dict[str, Any]]:
        """Find all permits that contain any of the inclusion keywords"""
        logger.info(f"      🔍 INCLUSION KEYWORD SEARCH:")
        logger.info(f"         Keywords: {keywords_include}")

        inclusion_results = []

        for permit in permits:
            description = str(permit.get('description', '')).lower()
            permit_id = permit.get('id', 'N/A')

            # Check if contains any inclusion keyword (OR logic)
            for keyword in keywords_include:
                if self._whole_word_match(description, keyword.lower()):
                    inclusion_results.append(permit)
                    logger.info(f"         ✅ Found permit {permit_id}: contains '{keyword}'")
                    break  # Found one keyword, add permit and move to next

        logger.info(f"      📊 Total inclusion matches: {len(inclusion_results)}")
        return inclusion_results

    def _semantic_search_within_permits_improved(self, permits: List[Dict[str, Any]], query: str, top_k: int,
                                                 return_scores: bool):
        """Improved semantic search that ranks the given permits"""

        if not permits:
            logger.info(f"   ⚠️ No permits to search within")
            return []

        if not query or not query.strip():
            logger.info(f"   ⚠️ No query provided, returning first {top_k} permits")
            return permits[:top_k]

        try:
            logger.info(f"   🧠 SEMANTIC RANKING: {len(permits)} permits")
            logger.info(f"      🔎 Query: '{query}'")

            # Create query embedding
            query_embedding = self._encode([query.strip()])[0]

            # Score each permit by semantic similarity
            permit_scores = []
            for permit in permits:
                description = str(permit.get('description', ''))
                if description.strip():
                    # Get embedding for this permit's description
                    permit_embedding = self._encode([description])[0]

                    # Calculate cosine similarity
                    import numpy as np
                    score = np.dot(query_embedding, permit_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(permit_embedding)
                    )

                    if return_scores:
                        permit_copy = permit.copy()
                        permit_copy['_rag_score'] = float(score)
                        permit_scores.append((score, permit_copy))
                    else:
                        permit_scores.append((score, permit))
                else:
                    # No description, give it lowest score
                    permit_scores.append((-1.0, permit))

            # Sort by score (highest first) and take top_k
            permit_scores.sort(key=lambda x: x[0], reverse=True)
            results = [permit for score, permit in permit_scores[:top_k]]

            logger.info(f"   🎯 Semantic ranking complete: {len(results)} permits")
            if permit_scores:
                top_score = permit_scores[0][0]
                logger.info(f"      📊 Top score: {top_score:.3f}")

            return results

        except Exception as e:
            logger.error(f"   ❌ Semantic ranking error: {e}")
            logger.info(f"   ↳ Falling back to original order")
            return permits[:top_k]
    def _search_exclusion_keywords(self, permits: List[Dict[str, Any]], keywords_exclude: List[str]) -> List[
        Dict[str, Any]]:
        """Find all permits that contain any of the exclusion keywords (for tracking)"""
        logger.info(f"      🚫 EXCLUSION KEYWORD SEARCH:")
        logger.info(f"         Keywords: {keywords_exclude}")

        exclusion_results = []

        for permit in permits:
            description = str(permit.get('description', '')).lower()
            permit_id = permit.get('id', 'N/A')

            # Check if contains any exclusion keyword (OR logic)
            for keyword in keywords_exclude:
                if self._whole_word_match(description, keyword.lower()):
                    # Add reason field for tracking
                    permit_copy = permit.copy()
                    permit_copy['exclusion_reason'] = f"contained keyword '{keyword}'"
                    exclusion_results.append(permit_copy)
                    logger.info(f"         🚫 Found permit {permit_id}: contains '{keyword}'")
                    break  # Found one keyword, add permit and move to next

        logger.info(f"      📊 Total exclusion matches: {len(exclusion_results)}")
        return exclusion_results

    def _distribute_exclusive_dual(self, assignments_by_client: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Distribute both keyword and semantic results exclusively"""
        logger.info("   ⚖️ DUAL EXCLUSIVE DISTRIBUTION:")

        # Distribute keyword results
        keyword_assignments = {}
        semantic_assignments = {}

        for cid, payload in assignments_by_client.items():
            keyword_assignments[cid] = {
                "client": payload["client"],
                "rows": payload["keyword_results"]
            }
            semantic_assignments[cid] = {
                "client": payload["client"],
                "rows": payload["semantic_results"]
            }

        # Apply exclusive distribution to both sets
        final_keyword = self._distribute_exclusive(keyword_assignments)
        final_semantic = self._distribute_exclusive(semantic_assignments)

        # Combine results
        final_assignments = {}
        for cid in assignments_by_client.keys():
            final_assignments[cid] = {
                "client": assignments_by_client[cid]["client"],
                "keyword_results": final_keyword.get(cid, {}).get("rows", []),
                "semantic_results": final_semantic.get(cid, {}).get("rows", [])
            }

            client_name = final_assignments[cid]["client"].get("name", "Unknown")
            keyword_count = len(final_assignments[cid]["keyword_results"])
            semantic_count = len(final_assignments[cid]["semantic_results"])
            logger.info(f"      👤 {client_name}: {keyword_count} keyword + {semantic_count} semantic")

        return final_assignments

    def get_filter_values(self):
        """Get filterable values from database with enhanced logging"""
        logger.info("🐛 GETTING FILTER VALUES...")

        conn = sqlite3.connect(self.permits_db_path)
        if not conn:
            return {"success": False, "error": "Cannot connect to permits DB"}

        try:
            cur = conn.cursor()
            filter_values = {}

            # Cities with counts
            cur.execute(
                "SELECT city, COUNT(*) FROM permits WHERE city IS NOT NULL GROUP BY city ORDER BY COUNT(*) DESC")
            cities = [{"value": row[0], "count": row[1]} for row in cur.fetchall()]
            filter_values["cities"] = cities
            logger.info(f"   📍 Found {len(cities)} unique cities")

            # Permit types with counts
            cur.execute(
                "SELECT permit_type, COUNT(*) FROM permits WHERE permit_type IS NOT NULL GROUP BY permit_type ORDER BY COUNT(*) DESC")
            permit_types = [{"value": row[0], "count": row[1]} for row in cur.fetchall()]
            filter_values["permit_types"] = permit_types
            logger.info(f"   🏗️ Found {len(permit_types)} unique permit types")

            # Permit classes with counts
            cur.execute(
                "SELECT permit_class_mapped, COUNT(*) FROM permits WHERE permit_class_mapped IS NOT NULL GROUP BY permit_class_mapped ORDER BY COUNT(*) DESC")
            permit_classes = [{"value": row[0], "count": row[1]} for row in cur.fetchall()]
            filter_values["permit_classes"] = permit_classes
            logger.info(f"   🏷️ Found {len(permit_classes)} unique permit classes")

            return {"success": True, "filter_values": filter_values}
        finally:
            conn.close()