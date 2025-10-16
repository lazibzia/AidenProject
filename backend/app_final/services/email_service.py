import os
import time
import logging
import csv
import io
import sqlite3
import smtplib
import socket
from collections import defaultdict
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import Dict, Any, List

from app_final.core.config import PERMITS_DB_PATH, CLIENTS_DB_PATH, GMAIL_USER, GMAIL_PASSWORD

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.permits_db_path = PERMITS_DB_PATH
        self.clients_db_path = CLIENTS_DB_PATH
        self.gmail_user = GMAIL_USER
        self.gmail_password = GMAIL_PASSWORD

        try:
            # Ensure sent log table exists for deduplication
            conn = self.get_permits_db_connection()
            if conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS sent_permit (
                        client_id INTEGER NOT NULL,
                        permit_id INTEGER NOT NULL,
                        sent_at TEXT NOT NULL,
                        PRIMARY KEY (client_id, permit_id)
                    )
                    """
                )
                conn.commit()
                conn.close()
        except Exception as e:
            logger.warning(f"Could not initialize sent_permit table: {e}")

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

        permit_type_mapping = {
            'Electrical Permit': 'Electrical Permit',
            'Mechanical Permit': 'Mechanical Permit',
            'Plumbing Permit': 'plumbing',
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

    def get_permits_by_type(self, days_back=30):
        """Fetch permits grouped by permit type"""
        conn = self.get_permits_db_connection()
        if not conn:
            return {}

        try:
            cursor = conn.cursor()
            query = '''
                SELECT
                    permit_num,
                    permit_type,
                    issued_date,
                    contractor_address,
                    description,
                    contractor_name,
                    city,
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

            permits_by_type = defaultdict(list)
            for permit in permits:
                original_permit_type = permit[1]
                normalized_type = self.normalize_permit_type(original_permit_type)

                if normalized_type:
                    permits_by_type[normalized_type].append(permit)

            logger.info(f"Retrieved {len(permits)} total permits")
            logger.info(f"Grouped into {len(permits_by_type)} permit types")

            return dict(permits_by_type)

        except Exception as e:
            logger.error(f"Error loading permits: {e}")
            return {}
        finally:
            conn.close()

    def distribute_permits_equally(self, permits_list, clients_list):
        """Distribute permits among clients with 75/25 ratio for exactly 2 clients"""
        if not clients_list or not permits_list:
            return {}

        num_clients = len(clients_list)

        # Special case: if exactly two clients, distribute 75%/25%
        if num_clients == 2:
            total = len(permits_list)
            first_client_count = int(round(total * 0.75))
            second_client_count = total - first_client_count

            distribution = {}
            start_idx = 0

            counts = [first_client_count, second_client_count]
            for i, client in enumerate(clients_list):
                end_idx = start_idx + counts[i]
                distribution[client['email']] = {
                    'client': client,
                    'permits': permits_list[start_idx:end_idx]
                }
                start_idx = end_idx

            logger.info(f"Distributed {len(permits_list)} permits among 2 clients with 75/25 split")
            return distribution

        # Default equal distribution for other cases
        permits_per_client = len(permits_list) // num_clients
        extra_permits = len(permits_list) % num_clients

        distribution = {}
        start_idx = 0

        for i, client in enumerate(clients_list):
            permits_count = permits_per_client + (1 if i < extra_permits else 0)
            end_idx = start_idx + permits_count

            distribution[client['email']] = {
                'client': client,
                'permits': permits_list[start_idx:end_idx]
            }
            start_idx = end_idx

        logger.info(f"Distributed {len(permits_list)} permits among {num_clients} clients")
        return distribution

    def permits_to_csv(self, permits):
        """Convert permits to CSV format"""
        if not permits:
            return None
        return self.fallback_csv(permits)

    def fallback_csv(self, permits):
        """Fallback CSV generation"""
        headers = [
            'Permit Number', 'Permit Type', 'Issued Date', 'Contractor Address',
            'Description', 'Contractor Name', 'City', 'Applied Date', 'Status'
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)

        for row in permits:
            writer.writerow([col if col else '' for col in row])

        return output.getvalue()

    def send_email_to_client(self, server, client_data, permits):
        """Send email to a single client with CSV attachment"""
        client = client_data['client']
        assigned_permits = client_data['permits']

        try:
            sample_types = ", ".join(sorted({str(p[1]) for p in assigned_permits if p[1]})[:3])
        except Exception:
            sample_types = ""
        summary = f"Total leads: {len(assigned_permits)}\nSample permit types: {sample_types}"

        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2 style="color: #333;">Daily Permit Leads - {client['permit_type']}</h2>
            <p>Hello {client['name']},</p>
            <p>You have been assigned <strong>{len(assigned_permits)} permit(s)</strong> of type "{client['permit_type']}" from our database.</p>
            <p>Please find the attached CSV file with enhanced lead information generated by our AI system.</p>

            <h3>LLM-Generated Lead Summary:</h3>
            <div style="background: #f0f0f0; padding: 10px; border-left: 4px solid #00b894;">
                <pre style="white-space: pre-wrap;">{summary}</pre>
            </div>

            <h4>CSV Features:</h4>
            <ul>
                <li>Project Description Summaries</li>
                <li>Lead Quality Scores (1-10)</li>
                <li>Priority Ratings</li>
                <li>Contractor Contact Information</li>
            </ul>

            <hr style="margin: 20px 0;">
            <p style="color: #666; font-size: 12px;">
                <strong>Note:</strong> This data is from our permit database with AI enhancements.
            </p>
            <p>Best regards,<br>Your Permit Distribution System</p>
        </div>
        """

        # Create email message
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = client['email']
        msg[
            'Subject'] = f"AI-Enhanced Permit Leads - {client['permit_type']} ({len(assigned_permits)} permits) - {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(body, 'html'))

        # Add CSV attachment
        csv_data = self.permits_to_csv(assigned_permits)
        if csv_data:
            attachment = MIMEApplication(csv_data, Name=f"enhanced_leads_{datetime.now().strftime('%Y%m%d')}.csv")
            attachment[
                'Content-Disposition'] = f'attachment; filename="enhanced_leads_{datetime.now().strftime("%Y%m%d")}.csv"'
            msg.attach(attachment)

        logger.info(f"Sending email to {client['email']} with {len(assigned_permits)} permits")
        server.send_message(msg)

    def _send_dual_email_with_attachments(self, server, client: Dict, attachments: List[Dict],
                                          keyword_count: int, semantic_count: int):
        """Send email with multiple Excel attachments"""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from datetime import datetime

        client_name = client.get("name", "Client")
        client_email = client.get("email")

        # Create email body
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2>Dumpster Rental Leads - Dual Search Results</h2>
            <p>Dear {client_name},</p>
            <p>Please find your dumpster rental leads attached. We've provided two sets of results:</p>
            <ul>
                <li><strong>Keyword Results:</strong> {keyword_count} leads found using keyword-based search</li>
                <li><strong>Semantic Results:</strong> {semantic_count} leads found using AI semantic search</li>
            </ul>
            <p>Both files contain permits with contractor contact information for your follow-up.</p>
            <p>Best regards,<br>Your Leads Team</p>
        </div>
        """

        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = client_email
        msg['Subject'] = f"Dumpster Rental Leads (Dual Search) - {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(body, 'html'))

        # Attach all Excel files
        for attachment in attachments:
            excel_attachment = MIMEApplication(attachment["bytes"], _subtype='xlsx')
            excel_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=attachment["filename"]
            )
            msg.attach(excel_attachment)
            logger.info(f"   📎 Attached: {attachment['filename']} ({attachment['type']})")

        # Send the email
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
        server = None

        try:
            smtp_host = 'smtp.gmail.com'
            smtp_ip = socket.gethostbyname(smtp_host)
            logger.info(f"Resolved {smtp_host} to IP: {smtp_ip}")

            server = smtplib.SMTP_SSL(smtp_ip, 465)
            server.login(self.gmail_user, self.gmail_password)
            logger.info(f"✅ Connected to SMTP server at {smtp_ip}")

            for email, client_data in distribution_data.items():
                try:
                    self.send_email_to_client(server, client_data, client_data['permits'])
                    logger.info(f"✅ Email sent to {email}")
                    success_count += 1
                    results[email] = {
                        'status': 'success',
                        'permits_count': len(client_data['permits'])
                    }
                    time.sleep(1.5)

                except Exception as e:
                    logger.error(f"❌ Failed to send email to {email}: {e}")
                    fail_count += 1
                    results[email] = {
                        'status': 'failed',
                        'error': str(e)
                    }

        except Exception as e:
            logger.error(f"❌ SMTP connection error: {e}")
            if server:
                try:
                    server.quit()
                except:
                    pass
            return {
                'success_count': 0,
                'fail_count': len(distribution_data),
                'error': str(e)
            }
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'results': results
        }

    def send_rag_emails_for_clients(self, assignments: Dict[int, Dict[str, Any]], dry_run: bool = True):
        """Send emails with Excel attachments for RAG assignments"""
        if dry_run:
            return {
                "success_count": sum(1 for a in assignments.values() if a["rows"]),
                "fail_count": 0,
                "dry_run": True,
                "details": {
                    a["client"].get("email", "unknown"): len(a["rows"])
                    for a in assignments.values()
                }
            }

        success, fail = 0, 0
        results = {}
        server = None

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            logger.info("✅ Connected to smtp.gmail.com")

            for payload in assignments.values():
                client = payload["client"]
                rows = payload["rows"]

                # Filter to only rows that have a contractor phone
                rows = [r for r in rows if self._get_best_phone_from_row(r)]
                if not rows or not client.get("email"):
                    results[client.get("email", "unknown")] = {"status": "skipped", "permits_count": 0}
                    continue

                try:
                    # Create Excel file in memory
                    from app_final.rag_engine.rag_engine_functional2 import RAGIndex
                    from app_final.core.config import RAG_INDEX_DIR

                    rag_idx = RAGIndex(self.permits_db_path, index_dir=RAG_INDEX_DIR)
                    excel_bytes, filename = rag_idx.get_excel_for_download(
                        rows,
                        include_score=True
                    )

                    # Email body
                    body = f"""
                    <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
                        <p>Dumpster Rental Leads attached below</p>
                    </div>
                    """

                    msg = MIMEMultipart()
                    msg['From'] = self.gmail_user
                    msg['To'] = client['email']
                    msg['Subject'] = f"Dumpster Rental Leads - {datetime.now().strftime('%Y-%m-%d')}"
                    msg.attach(MIMEText(body, 'html'))

                    # Attach Excel file
                    excel_attachment = MIMEApplication(excel_bytes, _subtype='xlsx')
                    excel_attachment.add_header(
                        'Content-Disposition',
                        'attachment',
                        filename=filename
                    )
                    msg.attach(excel_attachment)

                    server.send_message(msg)
                    results[client['email']] = {"status": "success", "permits_count": len(rows)}
                    success += 1
                    logger.info(f"✅ Excel report sent to {client['email']}")
                    time.sleep(1.5)

                except Exception as excel_error:
                    logger.error(f"Excel generation failed for {client['email']}: {excel_error}")
                    results[client['email']] = {"status": "failed",
                                                "error": f"Excel generation error: {str(excel_error)}"}
                    fail += 1

        except Exception as e:
            logger.error(f"SMTP error: {e}")
            return {"success_count": 0, "fail_count": len(assignments), "error": str(e)}
        finally:
            try:
                if server:
                    server.quit()
            except:
                pass

        return {"success_count": success, "fail_count": fail, "results": results}

    # Helper methods for RAG email functionality
    def _ensure_sent_table(self, conn):
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS sent_permit (
                client_id INTEGER NOT NULL,
                permit_id INTEGER NOT NULL,
                sent_at TEXT NOT NULL,
                PRIMARY KEY (client_id, permit_id)
            )
            """
        )
        conn.commit()

    def filter_new_assignments(self, assignments: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Return a copy of assignments keeping only rows not sent before to each client."""
        conn = self.get_permits_db_connection()
        if not conn:
            return assignments
        try:
            self._ensure_sent_table(conn)
            cur = conn.cursor()
            filtered: Dict[int, Dict[str, Any]] = {}
            for cid, payload in assignments.items():
                rows = payload.get("rows", []) or []
                if not rows:
                    filtered[cid] = {"client": payload["client"], "rows": []}
                    continue
                permit_ids = [int(r.get("id")) for r in rows if r.get("id") is not None]
                if not permit_ids:
                    filtered[cid] = {"client": payload["client"], "rows": []}
                    continue
                qmarks = ",".join("?" for _ in permit_ids)
                cur.execute(f"SELECT permit_id FROM sent_permit WHERE client_id=? AND permit_id IN ({qmarks})",
                            [int(cid)] + permit_ids)
                already = {int(r[0]) for r in cur.fetchall()}
                new_rows = [r for r in rows if int(r.get("id")) not in already]
                filtered[cid] = {"client": payload["client"], "rows": new_rows}
            return filtered
        except Exception as e:
            logger.warning(f"filter_new_assignments failed, sending all rows: {e}")
            return assignments
        finally:
            try:
                conn.close()
            except:
                pass

    def send_dual_rag_emails_for_clients(self, client_assignments: Dict[int, Dict[str, Any]], dry_run: bool = True):
        """Send emails with both keyword and semantic Excel files attached"""
        logger.info("📧 =================================================================")
        logger.info("📧 STARTING DUAL EMAIL SENDING")
        logger.info("📧 =================================================================")

        if dry_run:
            logger.info("🧪 DRY RUN MODE - No emails will be sent")
            results = {}
            for client_id, assignment in client_assignments.items():
                client = assignment["client"]
                keyword_count = len(assignment["keyword_results"])
                semantic_count = len(assignment["semantic_results"])

                results[client_id] = {
                    "success": True,
                    "keyword_count": keyword_count,
                    "semantic_count": semantic_count,
                    "dry_run": True,
                    "client_email": client.get("email", "unknown")
                }

                logger.info(
                    f"🧪 Would send to {client.get('email', 'unknown')}: {keyword_count} keyword + {semantic_count} semantic leads")

            return {
                "success_count": len([r for r in results.values() if r["success"]]),
                "fail_count": 0,
                "dry_run": True,
                "results": results
            }

        # Real email sending
        success_count = 0
        fail_count = 0
        results = {}
        server = None

        try:
            # Connect to SMTP server
            logger.info("🔌 Connecting to SMTP server...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            logger.info("✅ Connected to smtp.gmail.com")

            # Create RAGIndex instance (like in the working method)
            from app_final.rag_engine.rag_engine_functional2 import RAGIndex
            from app_final.core.config import RAG_INDEX_DIR

            logger.info("🔧 Creating RAG Index instance...")
            rag_idx = RAGIndex(self.permits_db_path, index_dir=RAG_INDEX_DIR)
            logger.info("✅ RAG Index created")

            for client_id, assignment in client_assignments.items():
                client = assignment["client"]
                keyword_results = assignment["keyword_results"]
                semantic_results = assignment["semantic_results"]

                client_email = client.get("email")
                client_name = client.get("name", "client")

                logger.info(f"📧 Processing email for {client_name} ({client_email})")
                logger.info(f"   🔤 Keyword results: {len(keyword_results)}")
                logger.info(f"   🧠 Semantic results: {len(semantic_results)}")

                if not client_email:
                    logger.warning(f"⚠️ No email for client {client_name}, skipping")
                    results[client_id] = {
                        "success": False,
                        "error": "No email address",
                        "keyword_count": len(keyword_results),
                        "semantic_count": len(semantic_results)
                    }
                    fail_count += 1
                    continue

                # Filter results to only those with contractor phone (like in working method)
                keyword_filtered = [r for r in keyword_results if self._get_best_phone_from_row(r)]
                semantic_filtered = [r for r in semantic_results if self._get_best_phone_from_row(r)]

                logger.info(f"   📞 After phone filtering:")
                logger.info(f"      🔤 Keyword: {len(keyword_filtered)} (was {len(keyword_results)})")
                logger.info(f"      🧠 Semantic: {len(semantic_filtered)} (was {len(semantic_results)})")

                if not keyword_filtered and not semantic_filtered:
                    logger.warning(f"⚠️ No permits with contractor phone for {client_name}, skipping")
                    results[client_id] = {
                        "success": False,
                        "error": "No permits with contractor phone",
                        "keyword_count": 0,
                        "semantic_count": 0
                    }
                    fail_count += 1
                    continue

                try:
                    # Create Excel files for both result sets
                    attachments = []

                    if keyword_filtered:
                        logger.info(f"   📊 Creating keyword Excel file...")
                        keyword_excel_bytes, keyword_filename = rag_idx.get_excel_for_download(
                            keyword_filtered,
                            include_score=True
                        )
                        # Rename to indicate keyword results
                        keyword_filename = f"keyword_{keyword_filename}"
                        attachments.append({
                            "bytes": keyword_excel_bytes,
                            "filename": keyword_filename,
                            "type": "keyword"
                        })
                        logger.info(f"   ✅ Keyword Excel created: {keyword_filename}")

                    if semantic_filtered:
                        logger.info(f"   📊 Creating semantic Excel file...")
                        semantic_excel_bytes, semantic_filename = rag_idx.get_excel_for_download(
                            semantic_filtered,
                            include_score=True
                        )
                        # Rename to indicate semantic results
                        semantic_filename = f"semantic_{semantic_filename}"
                        attachments.append({
                            "bytes": semantic_excel_bytes,
                            "filename": semantic_filename,
                            "type": "semantic"
                        })
                        logger.info(f"   ✅ Semantic Excel created: {semantic_filename}")

                    # Create email with dual attachments
                    logger.info(f"   📧 Sending dual email to {client_email}...")
                    self._send_dual_email_with_attachments(
                        server=server,
                        client=client,
                        attachments=attachments,
                        keyword_count=len(keyword_filtered),
                        semantic_count=len(semantic_filtered)
                    )

                    results[client_id] = {
                        "success": True,
                        "keyword_count": len(keyword_filtered),
                        "semantic_count": len(semantic_filtered),
                        "client_email": client_email
                    }
                    success_count += 1
                    logger.info(f"✅ Dual email sent successfully to {client_email}")

                    # Small delay between emails
                    time.sleep(1.5)

                except Exception as email_error:
                    logger.error(f"❌ Email sending failed for {client_name}: {email_error}")
                    results[client_id] = {
                        "success": False,
                        "error": f"Email sending error: {str(email_error)}",
                        "keyword_count": len(keyword_filtered),
                        "semantic_count": len(semantic_filtered)
                    }
                    fail_count += 1

        except Exception as e:
            logger.error(f"❌ SMTP connection error: {e}")
            return {
                "success_count": 0,
                "fail_count": len(client_assignments),
                "error": str(e),
                "results": {}
            }
        finally:
            try:
                if server:
                    server.quit()
                    logger.info("🔌 SMTP connection closed")
            except:
                pass

        logger.info("📊 DUAL EMAIL SENDING SUMMARY:")
        logger.info(f"   ✅ Success: {success_count}")
        logger.info(f"   ❌ Failed: {fail_count}")
        logger.info("📧 DUAL EMAIL SENDING COMPLETED")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    def send_triple_rag_emails_for_clients(self, client_assignments: Dict[int, Dict[str, Any]], dry_run: bool = True):
        """Send emails with three CSV files: inclusion, exclusion, and semantic"""
        logger.info("📧 =================================================================")
        logger.info("📧 STARTING TRIPLE CSV EMAIL SENDING")
        logger.info("📧 =================================================================")

        if dry_run:
            logger.info("🧪 DRY RUN MODE - No emails will be sent")
            results = {}
            for client_id, assignment in client_assignments.items():
                client = assignment["client"]
                inclusion_count = len(assignment["inclusion_results"])
                exclusion_count = len(assignment["exclusion_results"])
                semantic_count = len(assignment["semantic_results"])

                results[client_id] = {
                    "success": True,
                    "inclusion_count": inclusion_count,
                    "exclusion_count": exclusion_count,
                    "semantic_count": semantic_count,
                    "dry_run": True,
                    "client_email": client.get("email", "unknown")
                }

                logger.info(
                    f"🧪 Would send to {client.get('email', 'unknown')}: {inclusion_count} inclusion + {exclusion_count} exclusion + {semantic_count} semantic")

            return {
                "success_count": len([r for r in results.values() if r["success"]]),
                "fail_count": 0,
                "dry_run": True,
                "results": results
            }

        # Real email sending
        success_count = 0
        fail_count = 0
        results = {}
        server = None

        try:
            # Connect to SMTP server
            logger.info("🔌 Connecting to SMTP server...")
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            logger.info("✅ Connected to smtp.gmail.com")

            # Create RAGIndex instance
            from app_final.rag_engine.rag_engine_functional2 import RAGIndex
            from app_final.core.config import RAG_INDEX_DIR

            logger.info("🔧 Creating RAG Index instance...")
            rag_idx = RAGIndex(self.permits_db_path, index_dir=RAG_INDEX_DIR)
            logger.info("✅ RAG Index created")

            for client_id, assignment in client_assignments.items():
                client = assignment["client"]
                inclusion_results = assignment["inclusion_results"]
                exclusion_results = assignment["exclusion_results"]
                semantic_results = assignment["semantic_results"]

                client_email = client.get("email")
                client_name = client.get("name", "client")

                logger.info(f"📧 Processing triple email for {client_name} ({client_email})")
                logger.info(f"   🔍 Inclusion results: {len(inclusion_results)}")
                logger.info(f"   🚫 Exclusion results: {len(exclusion_results)}")
                logger.info(f"   🧠 Semantic results: {len(semantic_results)}")

                if not client_email:
                    logger.warning(f"⚠️ No email for client {client_name}, skipping")
                    results[client_id] = {
                        "success": False,
                        "error": "No email address",
                        "inclusion_count": len(inclusion_results),
                        "exclusion_count": len(exclusion_results),
                        "semantic_count": len(semantic_results)
                    }
                    fail_count += 1
                    continue

                # Filter results to only those with contractor phone
                inclusion_filtered = [r for r in inclusion_results if self._get_best_phone_from_row(r)]
                exclusion_filtered = [r for r in exclusion_results if self._get_best_phone_from_row(r)]
                semantic_filtered = [r for r in semantic_results if self._get_best_phone_from_row(r)]

                logger.info(f"   📞 After phone filtering:")
                logger.info(f"      🔍 Inclusion: {len(inclusion_filtered)} (was {len(inclusion_results)})")
                logger.info(f"      🚫 Exclusion: {len(exclusion_filtered)} (was {len(exclusion_results)})")
                logger.info(f"      🧠 Semantic: {len(semantic_filtered)} (was {len(semantic_results)})")

                if not inclusion_filtered and not exclusion_filtered and not semantic_filtered:
                    logger.warning(f"⚠️ No permits with contractor phone for {client_name}, skipping")
                    results[client_id] = {
                        "success": False,
                        "error": "No permits with contractor phone",
                        "inclusion_count": 0,
                        "exclusion_count": 0,
                        "semantic_count": 0
                    }
                    fail_count += 1
                    continue

                try:
                    # Create Excel files for all three result sets
                    attachments = []

                    if inclusion_filtered:
                        logger.info(f"   📊 Creating inclusion keywords Excel file...")
                        inclusion_excel_bytes, inclusion_filename = rag_idx.get_excel_for_download(
                            inclusion_filtered, include_score=True
                        )
                        inclusion_filename = f"inclusion_keywords_{inclusion_filename}"
                        attachments.append({
                            "bytes": inclusion_excel_bytes,
                            "filename": inclusion_filename,
                            "type": "inclusion"
                        })
                        logger.info(f"   ✅ Inclusion Excel created: {inclusion_filename}")

                    if exclusion_filtered:
                        logger.info(f"   📊 Creating exclusion tracking Excel file...")
                        exclusion_excel_bytes, exclusion_filename = rag_idx.get_excel_for_download(
                            exclusion_filtered, include_score=True
                        )
                        exclusion_filename = f"excluded_keywords_tracking_{exclusion_filename}"
                        attachments.append({
                            "bytes": exclusion_excel_bytes,
                            "filename": exclusion_filename,
                            "type": "exclusion"
                        })
                        logger.info(f"   ✅ Exclusion Excel created: {exclusion_filename}")

                    if semantic_filtered:
                        logger.info(f"   📊 Creating semantic search Excel file...")
                        semantic_excel_bytes, semantic_filename = rag_idx.get_excel_for_download(
                            semantic_filtered, include_score=True
                        )
                        semantic_filename = f"semantic_search_{semantic_filename}"
                        attachments.append({
                            "bytes": semantic_excel_bytes,
                            "filename": semantic_filename,
                            "type": "semantic"
                        })
                        logger.info(f"   ✅ Semantic Excel created: {semantic_filename}")

                    # Send email with triple attachments
                    logger.info(f"   📧 Sending triple email to {client_email}...")
                    self._send_triple_email_with_attachments(
                        server=server,
                        client=client,
                        attachments=attachments,
                        inclusion_count=len(inclusion_filtered),
                        exclusion_count=len(exclusion_filtered),
                        semantic_count=len(semantic_filtered)
                    )

                    results[client_id] = {
                        "success": True,
                        "inclusion_count": len(inclusion_filtered),
                        "exclusion_count": len(exclusion_filtered),
                        "semantic_count": len(semantic_filtered),
                        "client_email": client_email
                    }
                    success_count += 1
                    logger.info(f"✅ Triple email sent successfully to {client_email}")

                    # Small delay between emails
                    time.sleep(1.5)

                except Exception as email_error:
                    logger.error(f"❌ Email sending failed for {client_name}: {email_error}")
                    results[client_id] = {
                        "success": False,
                        "error": f"Email sending error: {str(email_error)}",
                        "inclusion_count": len(inclusion_filtered),
                        "exclusion_count": len(exclusion_filtered),
                        "semantic_count": len(semantic_filtered)
                    }
                    fail_count += 1

        except Exception as e:
            logger.error(f"❌ SMTP connection error: {e}")
            return {
                "success_count": 0,
                "fail_count": len(client_assignments),
                "error": str(e),
                "results": {}
            }
        finally:
            try:
                if server:
                    server.quit()
                    logger.info("🔌 SMTP connection closed")
            except:
                pass

        logger.info("📊 TRIPLE EMAIL SENDING SUMMARY:")
        logger.info(f"   ✅ Success: {success_count}")
        logger.info(f"   ❌ Failed: {fail_count}")
        logger.info("📧 TRIPLE EMAIL SENDING COMPLETED")

        return {
            "success_count": success_count,
            "fail_count": fail_count,
            "results": results
        }

    def _send_triple_email_with_attachments(self, server, client: Dict, attachments: List[Dict],
                                            inclusion_count: int, exclusion_count: int, semantic_count: int):
        """Send email with three Excel attachments"""
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication
        from datetime import datetime

        client_name = client.get("name", "Client")
        client_email = client.get("email")

        # Create email body
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto;">
            <h2>Dumpster Rental Leads - Complete Search Results</h2>
            <p>Dear {client_name},</p>
            <p>Please find your comprehensive dumpster rental leads attached. We've provided three detailed result sets:</p>
            <ul>
                <li><strong>Inclusion Keywords Results:</strong> {inclusion_count} leads matching your specified keywords</li>
                <li><strong>Exclusion Keywords Tracking:</strong> {exclusion_count} leads containing excluded terms (for your reference)</li>
                <li><strong>Semantic Search Results:</strong> {semantic_count} leads found using AI semantic matching</li>
            </ul>
            <p>All files contain permits with contractor contact information for your follow-up.</p>
            <p>Best regards,<br>Your Leads Team</p>
        </div>
        """

        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = client_email
        msg['Subject'] = f"Dumpster Rental Leads (Complete Results) - {datetime.now().strftime('%Y-%m-%d')}"
        msg.attach(MIMEText(body, 'html'))

        # Attach all Excel files
        for attachment in attachments:
            excel_attachment = MIMEApplication(attachment["bytes"], _subtype='xlsx')
            excel_attachment.add_header(
                'Content-Disposition',
                'attachment',
                filename=attachment["filename"]
            )
            msg.attach(excel_attachment)
            logger.info(f"   📎 Attached: {attachment['filename']} ({attachment['type']})")

        # Send the email
        server.send_message(msg)

    def _get_best_phone_from_row(self, row: Dict[str, Any]) -> str:
        """Return formatted phone if available, else empty string."""
        phone_fields = [
            "contractor_phone",
            "applicant_phone",
            "phone",
            "contact_phone",
            "business_phone",
            "company_phone",
            "contractor_company_phone",
        ]

        def _fmt(phone: Any) -> str:
            if phone is None:
                return ""
            digits = "".join(ch for ch in str(phone) if ch.isdigit())
            if len(digits) == 10:
                return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
            if len(digits) == 11 and digits[0] == '1':
                return f"({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
            return digits

        for f in phone_fields:
            val = row.get(f)
            if val is not None and str(val).strip():
                formatted = _fmt(val)
                if formatted:
                    return formatted
        return ""

    def filter_assignments_requiring_phone(self, assignments: Dict[int, Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
        """Keep only rows that have an available contractor phone per client."""
        filtered: Dict[int, Dict[str, Any]] = {}
        for cid, payload in assignments.items():
            rows = payload.get("rows", []) or []
            rows_with_phone = [r for r in rows if self._get_best_phone_from_row(r)]
            filtered[cid] = {"client": payload.get("client", {}), "rows": rows_with_phone}
        return filtered

    def record_sent(self, assignments: Dict[int, Dict[str, Any]]):
        """Record rows as sent for each client."""
        conn = self.get_permits_db_connection()
        if not conn:
            return
        try:
            self._ensure_sent_table(conn)
            cur = conn.cursor()
            now = datetime.now().isoformat()
            for cid, payload in assignments.items():
                rows = payload.get("rows", []) or []
                for r in rows:
                    pid = r.get("id")
                    if pid is None:
                        continue
                    try:
                        cur.execute(
                            "INSERT OR IGNORE INTO sent_permit (client_id, permit_id, sent_at) VALUES (?,?,?)",
                            (int(cid), int(pid), now)
                        )
                    except Exception as ie:
                        logger.debug(f"record_sent skip ({cid},{pid}): {ie}")
            conn.commit()
        except Exception as e:
            logger.warning(f"record_sent failed: {e}")
        finally:
            try:
                conn.close()
            except:
                pass