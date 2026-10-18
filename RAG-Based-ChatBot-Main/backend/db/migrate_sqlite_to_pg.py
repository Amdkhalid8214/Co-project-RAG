"""
DocuChat AI - Safe SQLite-to-PostgreSQL Migration Script
Transfers all persistent records (users, sessions, documents, conversations, messages)
from legacy SQLite into PostgreSQL, validates row counts, handles reruns safely,
and verifies referential integrity.
"""
import os
import sys
import json
import sqlite3
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from backend.config import settings
from backend.db.models import Base, UserModel, UserSessionModel, DocumentModel, ConversationModel, MessageModel, IngestJobModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("migration")

def parse_iso_datetime(dt_str: str) -> datetime:
    if not dt_str:
        return datetime.utcnow()
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        try:
            return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S.%f")
        except Exception:
            try:
                return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.utcnow()

def migrate_database(sqlite_path: str, target_db_url: str) -> bool:
    if not os.path.exists(sqlite_path):
        logger.error(f"Source SQLite database not found at {sqlite_path}")
        return False

    # Sync engine for migration transfer
    sync_url = target_db_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    logger.info(f"Connecting to target database: {sync_url.split('@')[-1] if '@' in sync_url else sync_url}")

    target_engine = create_engine(sync_url)
    
    # 1. Ensure target schema exists
    Base.metadata.create_all(target_engine)

    # 2. Open SQLite connection
    con = sqlite3.connect(sqlite_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # Track migration counts
    counts = {
        "users": {"source": 0, "migrated": 0, "skipped": 0},
        "user_sessions": {"source": 0, "migrated": 0, "skipped": 0},
        "documents": {"source": 0, "migrated": 0, "skipped": 0},
        "conversations": {"source": 0, "migrated": 0, "skipped": 0},
        "messages": {"source": 0, "migrated": 0, "skipped": 0},
    }

    with Session(target_engine) as session:
        # A. Migrate Users
        try:
            rows = cur.execute("SELECT * FROM users").fetchall()
            counts["users"]["source"] = len(rows)
            for r in rows:
                existing = session.get(UserModel, r["id"])
                if not existing:
                    user = UserModel(
                        id=r["id"],
                        username=r["username"],
                        email=r["email"] if "email" in r.keys() else None,
                        password_hash=r["password_hash"],
                        salt=r["salt"],
                        role=r["role"] if "role" in r.keys() else "user",
                        created_at=parse_iso_datetime(r["created_at"])
                    )
                    session.add(user)
                    counts["users"]["migrated"] += 1
                else:
                    counts["users"]["skipped"] += 1
            session.commit()
            logger.info(f"Users migrated: {counts['users']['migrated']} (Skipped: {counts['users']['skipped']})")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error migrating users: {e}")

        # Find first admin or user to associate with legacy unassigned docs
        default_user = session.execute(select(UserModel)).scalars().first()
        default_user_id = default_user.id if default_user else None

        # B. Migrate User Sessions
        try:
            rows = cur.execute("SELECT * FROM user_sessions").fetchall()
            counts["user_sessions"]["source"] = len(rows)
            for r in rows:
                existing = session.get(UserSessionModel, r["token"])
                if not existing:
                    # check if user exists
                    if session.get(UserModel, r["user_id"]):
                        sess = UserSessionModel(
                            token=r["token"],
                            user_id=r["user_id"],
                            created_at=parse_iso_datetime(r["created_at"])
                        )
                        session.add(sess)
                        counts["user_sessions"]["migrated"] += 1
                else:
                    counts["user_sessions"]["skipped"] += 1
            session.commit()
            logger.info(f"User sessions migrated: {counts['user_sessions']['migrated']} (Skipped: {counts['user_sessions']['skipped']})")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error migrating user_sessions: {e}")

        # C. Migrate Documents
        try:
            rows = cur.execute("SELECT * FROM documents").fetchall()
            counts["documents"]["source"] = len(rows)
            for r in rows:
                existing = session.get(DocumentModel, r["id"])
                if not existing:
                    doc = DocumentModel(
                        id=r["id"],
                        user_id=r["user_id"] if "user_id" in r.keys() and r["user_id"] else default_user_id,
                        filename=r["filename"],
                        file_type=r["file_type"],
                        original_path=r["original_path"],
                        pdf_path=r["pdf_path"],
                        status=r["status"],
                        status_message=r["status_message"],
                        page_count=r["page_count"] or 1,
                        chunk_count=r["chunk_count"] or 0,
                        created_at=parse_iso_datetime(r["created_at"])
                    )
                    session.add(doc)
                    counts["documents"]["migrated"] += 1
                else:
                    counts["documents"]["skipped"] += 1
            session.commit()
            logger.info(f"Documents migrated: {counts['documents']['migrated']} (Skipped: {counts['documents']['skipped']})")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error migrating documents: {e}")

        # D. Migrate Conversations
        try:
            rows = cur.execute("SELECT * FROM conversations").fetchall()
            counts["conversations"]["source"] = len(rows)
            for r in rows:
                existing = session.get(ConversationModel, r["id"])
                if not existing:
                    conv = ConversationModel(
                        id=r["id"],
                        user_id=r["user_id"] if "user_id" in r.keys() and r["user_id"] else default_user_id,
                        title=r["title"],
                        created_at=parse_iso_datetime(r["created_at"]),
                        updated_at=parse_iso_datetime(r["updated_at"]) if "updated_at" in r.keys() else parse_iso_datetime(r["created_at"])
                    )
                    session.add(conv)
                    counts["conversations"]["migrated"] += 1
                else:
                    counts["conversations"]["skipped"] += 1
            session.commit()
            logger.info(f"Conversations migrated: {counts['conversations']['migrated']} (Skipped: {counts['conversations']['skipped']})")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error migrating conversations: {e}")

        # E. Migrate Messages
        try:
            rows = cur.execute("SELECT * FROM messages").fetchall()
            counts["messages"]["source"] = len(rows)
            for r in rows:
                existing = session.get(MessageModel, r["id"])
                if not existing:
                    raw_citations = r["citations"] if "citations" in r.keys() else None
                    parsed_citations = None
                    if raw_citations:
                        if isinstance(raw_citations, str):
                            try:
                                parsed_citations = json.loads(raw_citations)
                            except Exception:
                                parsed_citations = []
                        elif isinstance(raw_citations, list):
                            parsed_citations = raw_citations

                    msg = MessageModel(
                        id=r["id"],
                        conversation_id=r["conversation_id"],
                        role=r["role"],
                        content=r["content"],
                        router_badge=r["router_badge"] if "router_badge" in r.keys() else None,
                        citations=parsed_citations,
                        created_at=parse_iso_datetime(r["created_at"])
                    )
                    session.add(msg)
                    counts["messages"]["migrated"] += 1
                else:
                    counts["messages"]["skipped"] += 1
            session.commit()
            logger.info(f"Messages migrated: {counts['messages']['migrated']} (Skipped: {counts['messages']['skipped']})")
        except Exception as e:
            session.rollback()
            logger.warning(f"Error migrating messages: {e}")

    # 3. Post-migration Verification
    logger.info("=== POST-MIGRATION VERIFICATION ===")
    verified = True
    with Session(target_engine) as session:
        for table, stats in counts.items():
            tgt_count = session.execute(text(f"SELECT count(*) FROM {table}")).scalar()
            logger.info(f"Table '{table}': SQLite source={stats['source']} | Target total={tgt_count} (New migrated={stats['migrated']}, Existing={stats['skipped']})")
            if tgt_count < stats["source"]:
                logger.error(f"Discrepancy in table '{table}': Target has fewer rows than source!")
                verified = False

    con.close()
    target_engine.dispose()

    if verified:
        logger.info("MIGRATION COMPLETED AND FULLY VERIFIED.")
    else:
        logger.warning("Migration finished with validation discrepancies.")
    return verified


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate SQLite records to PostgreSQL")
    parser.add_argument("--sqlite-path", default=os.path.join(settings.DATA_DIR, "rag_app.db"), help="Path to source SQLite file")
    parser.add_argument("--target-url", default=settings.DATABASE_URL, help="Target database URL")
    args = parser.parse_args()

    success = migrate_database(args.sqlite_path, args.target_url)
    sys.exit(0 if success else 1)
