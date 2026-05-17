"""Persistent memory layer — JSON file on disk."""
import json, os

MEMORY_FILE = "memory.json"


def load_memory() -> dict:
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"user": {}, "goals": [], "commitments": [], "reminders": [], "insights": [], "conversation_history": []}


def save_memory(memory: dict) -> None:
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)


def add_insight(memory: dict, insight: str) -> None:
    memory.setdefault("insights", []).append(insight)


def add_commitment(memory: dict, commitment: str) -> None:
    memory.setdefault("commitments", []).append(commitment)


def add_reminder(memory: dict, reminder: dict) -> None:
    memory.setdefault("reminders", []).append(reminder)


def add_conversation_turn(memory: dict, role: str, content: str, session: int) -> None:
    memory.setdefault("conversation_history", []).append({"session": session, "role": role, "content": content})


def get_memory_context(memory: dict) -> str:
    """Format memory into a string for LLM context."""
    parts = []
    if memory.get("user"):
        parts.append(f"User Profile: {json.dumps(memory['user'])}")
    if memory.get("goals"):
        parts.append(f"Goals: {json.dumps(memory['goals'])}")
    if memory.get("commitments"):
        parts.append(f"Commitments: {'; '.join(memory['commitments'])}")
    if memory.get("reminders"):
        rem_strs = [r["date"] + ": " + r["content"] for r in memory["reminders"]]
        parts.append(f"Active Reminders: {'; '.join(rem_strs)}")
    if memory.get("insights"):
        parts.append(f"Financial Insights: {'; '.join(memory['insights'])}")
    if memory.get("conversation_history"):
        recent = memory["conversation_history"][-6:]
        hist = "\n".join([f"  [{t['role']}] {t['content']}" for t in recent])
        parts.append(f"Recent Conversation:\n{hist}")
    return "\n\n".join(parts) if parts else "No prior context."
