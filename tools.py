"""
Financial tools API — DO NOT MODIFY
Simulates Priya Sharma's bank data for Session 1 (Nov 3) and Session 2 (Nov 6).
"""

import datetime

"""
Financial tools API — DO NOT MODIFY
Simulates Priya Sharma's bank data for Session 1 (Nov 3) and Session 2 (Nov 6).
"""

import datetime
import sys

# Auto-detect session or use command line argument
def get_current_session():
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            pass
    
    # Auto-detect based on memory file existence and content
    try:
        import json
        import os
        if os.path.exists("memory.json"):
            with open("memory.json", "r", encoding="utf-8") as f:
                memory = json.load(f)
                # If we have Session 1 conversation history, we're ready for Session 2
                history = memory.get("conversation_history", [])
                session1_turns = [h for h in history if h.get("session") == 1]
                if len(session1_turns) >= 6:  # Session 1 has 4 user turns = 8 total turns
                    return 2
        return 1
    except:
        return 1

CURRENT_SESSION = get_current_session()


def get_recent_transactions(days: int = 30) -> list[dict]:
    """Get recent transactions. Negative amounts are debits."""
    if CURRENT_SESSION == 1:
        # Session 1: Nov 3 — salary just credited, last month's spending visible
        return [
            {"date": "2024-11-01", "amount": 120000, "category": "salary", "merchant": "TechCorp India"},
            {"date": "2024-10-31", "amount": -1200, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-30", "amount": -450, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-10-28", "amount": -800, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-27", "amount": -350, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-10-25", "amount": -1500, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-23", "amount": -600, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-10-20", "amount": -900, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-18", "amount": -700, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-15", "amount": -1100, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-10-12", "amount": -400, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-10", "amount": -25000, "category": "rent", "merchant": "Landlord UPI"},
            {"date": "2024-10-08", "amount": -5000, "category": "utilities", "merchant": "Bescom Electricity"},
            {"date": "2024-10-05", "amount": -2500, "category": "shopping", "merchant": "Amazon India"},
            {"date": "2024-10-03", "amount": -1200, "category": "transport", "merchant": "Uber India"},
            {"date": "2024-10-02", "amount": -10000, "category": "investment", "merchant": "Groww SIP"},
            {"date": "2024-10-01", "amount": 120000, "category": "salary", "merchant": "TechCorp India"},
        ]
    else:
        # Session 2: Nov 6 — rent paid, some food orders since Nov 3
        return [
            {"date": "2024-11-05", "amount": -25000, "category": "rent", "merchant": "Landlord UPI"},
            {"date": "2024-11-05", "amount": -600, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-11-04", "amount": -450, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-11-03", "amount": -800, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-11-01", "amount": 120000, "category": "salary", "merchant": "TechCorp India"},
            {"date": "2024-10-31", "amount": -1200, "category": "food_delivery", "merchant": "Swiggy"},
            {"date": "2024-10-30", "amount": -450, "category": "food_delivery", "merchant": "Zomato"},
            {"date": "2024-10-28", "amount": -800, "category": "food_delivery", "merchant": "Swiggy"},
        ]


def get_account_balance() -> dict:
    """Get current account balances in INR."""
    if CURRENT_SESSION == 1:
        return {
            "checking": 128000,
            "savings": 45000,
            "house_fund": 180000,
            "mutual_funds": 320000,
        }
    else:
        return {
            "checking": 99800,
            "savings": 45000,
            "house_fund": 180000,
            "mutual_funds": 320000,
        }


def get_upcoming_bills(days: int = 30) -> list[dict]:
    """Get upcoming bills in the next N days."""
    if CURRENT_SESSION == 1:
        return [
            {"date": "2024-11-05", "amount": 25000, "description": "Rent — Landlord UPI"},
            {"date": "2024-11-07", "amount": 10000, "description": "SIP — Groww Mutual Fund"},
            {"date": "2024-11-10", "amount": 5000, "description": "Electricity — Bescom"},
            {"date": "2024-11-15", "amount": 1500, "description": "Internet — ACT Fibernet"},
            {"date": "2024-11-20", "amount": 8500, "description": "Credit Card — HDFC"},
        ]
    else:
        # Nov 6: rent already paid
        return [
            {"date": "2024-11-07", "amount": 10000, "description": "SIP — Groww Mutual Fund"},
            {"date": "2024-11-10", "amount": 5000, "description": "Electricity — Bescom"},
            {"date": "2024-11-15", "amount": 1500, "description": "Internet — ACT Fibernet"},
            {"date": "2024-11-20", "amount": 8500, "description": "Credit Card — HDFC"},
        ]


def set_reminder(date: str, content: str) -> dict:
    """Set a reminder for a future date."""
    return {
        "status": "confirmed",
        "reminder_id": "rem_" + date.replace("-", ""),
        "date": date,
        "content": content,
    }
