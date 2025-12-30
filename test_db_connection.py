#!/usr/bin/env python3
"""Test script to verify Supabase database connection"""

import sys
from database import DatabaseManager

def test_connection():
    print("Testing Supabase connection...")

    db = DatabaseManager()

    if db.supabase is None:
        print("❌ Database connection failed")
        print("   Check .env file and credentials")
        return False

    print("✅ Database connection successful")

    try:
        session_id = db.create_session("test.pdf", "application/pdf")
        if session_id:
            print(f"✅ Created test session: {session_id}")

            db.update_session(session_id, "completed", processing_time_ms=1000)
            print("✅ Updated test session")

            session = db.get_session(session_id)
            if session:
                print(f"✅ Retrieved session: status={session['status']}")

            recent = db.get_recent_sessions(limit=5)
            if recent:
                print(f"✅ Retrieved {len(recent)} recent sessions")

            return True
        else:
            print("⚠️  Could not create session (check RLS policies)")
            return False

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
