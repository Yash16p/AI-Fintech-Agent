"""
Minimal AI Financial Agent — No frameworks, under 300 lines total.
Uses tool calling for real data, LLM for judgment only, memory persists to disk.
"""

import json
import os
import re
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

from tools import (
    get_recent_transactions,
    get_account_balance,
    get_upcoming_bills,
    set_reminder,
    CURRENT_SESSION,
)
from memory import (
    load_memory,
    save_memory,
    add_insight,
    add_commitment,
    add_reminder,
    add_conversation_turn,
    get_memory_context,
)

# --- LLM Setup ---
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL = "gemini-2.0-flash"

SYSTEM_PROMPT = """You are a personal financial assistant for Priya Sharma, a 28-year-old software engineer in Bangalore.
- Monthly income: ₹1,20,000 (post-tax, credited on the 1st)
- Long-term goal: Save ₹15 lakh for a house down payment

Your job:
1. Use ONLY tool results for numbers — never invent financial data.
2. Be specific with amounts and dates.
3. Connect current questions to past commitments and goals from memory.
4. When the user asks about a purchase, don't just say yes/no — weigh it against their goals, current balance, upcoming bills, and commitments.
5. Be warm but honest. Help them make informed decisions.
6. ALWAYS complete your analysis with a clear recommendation.
7. TRACK PROGRESS on commitments - if she committed to cut food delivery spending, check recent transactions to see how she's doing.

When you need data, respond with a JSON tool call in this exact format:
{"tool": "<tool_name>", "args": {<arguments>}}

Available tools:
- get_recent_transactions(days: int) — returns recent transactions
- get_account_balance() — returns current balances
- get_upcoming_bills(days: int) — returns upcoming bills
- set_reminder(date: str, content: str) — sets a reminder

After getting tool results, ALWAYS provide a complete analysis and recommendation. Don't leave responses incomplete.
Pay special attention to tracking progress on previous commitments (like food delivery reduction goals)."""


TOOL_FUNCTIONS = {
    "get_recent_transactions": get_recent_transactions,
    "get_account_balance": get_account_balance,
    "get_upcoming_bills": get_upcoming_bills,
    "set_reminder": set_reminder,
}


def call_llm(messages: list[dict]) -> str:
    """Call Gemini and return the response text."""
    # Build system instruction from system messages
    system_parts = [m["content"] for m in messages if m["role"] == "system"]
    system_instruction = "\n\n".join(system_parts) if system_parts else None

    # Build contents for Gemini
    contents = []
    for m in messages:
        if m["role"] == "user":
            contents.append({"role": "user", "parts": [{"text": m["content"]}]})
        elif m["role"] == "assistant":
            contents.append({"role": "model", "parts": [{"text": m["content"]}]})

    response = client.models.generate_content(
        model=MODEL,
        contents=contents,
        config={"system_instruction": system_instruction, "temperature": 0.3, "max_output_tokens": 1000},
    )
    return response.text.strip()


def extract_tool_call(response: str) -> dict | None:
    """Extract a tool call JSON from the LLM response, if present."""
    # Look for JSON with "tool" key in various formats
    patterns = [
        r'```tool_code\s*(\{[^`]*\})\s*```',
        r'```json\s*(\{[^`]*\})\s*```',
        r'```\s*(\{[^`]*\})\s*```',
        r'(\{"tool":\s*"[^"]+?".*?\})',  # Fixed: use .*? for non-greedy match
        r'(\{[^{}]*"tool"[^{}]*\{[^}]*\}[^}]*\})',  # Handle nested braces
    ]
    for pattern in patterns:
        match = re.search(pattern, response, re.DOTALL | re.MULTILINE)
        if match:
            try:
                parsed = json.loads(match.group(1))
                if "tool" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
    
    # Look for JSON at the end of the response (common pattern)
    lines = response.strip().split('\n')
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            try:
                parsed = json.loads(line)
                if "tool" in parsed:
                    return parsed
            except json.JSONDecodeError:
                continue
    
    return None


def execute_tool(tool_call: dict) -> str:
    """Execute a tool and return the result as a string."""
    name = tool_call["tool"]
    args = tool_call.get("args", {})

    if name not in TOOL_FUNCTIONS:
        return f"Error: Unknown tool '{name}'"

    try:
        result = TOOL_FUNCTIONS[name](**args)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error calling {name}: {str(e)}"


def update_memory_from_conversation(memory: dict, user_msg: str, assistant_msg: str) -> None:
    """Extract key info from the conversation and update memory."""
    lower_msg = (user_msg + " " + assistant_msg).lower()
    # Detect savings commitments
    if ("30,000" in assistant_msg or "30000" in assistant_msg) and "house" in lower_msg:
        commitment = "Save ₹30,000 for house fund this month (November 2024)"
        if commitment not in memory.get("commitments", []):
            add_commitment(memory, commitment)
    # Detect food delivery insights
    if "food delivery" in lower_msg and any(c.isdigit() for c in assistant_msg):
        for line in assistant_msg.split("\n"):
            if "food" in line.lower() and "₹" in line:
                if not any("food delivery" in i for i in memory.get("insights", [])):
                    add_insight(memory, f"Oct 2024 food delivery: {line.strip()}")
                break
    # Detect cut-in-half commitment
    if "cut" in lower_msg and "half" in lower_msg and "food" in lower_msg:
        commitment = "Cut food delivery spending in half (from ~₹9,000 to ~₹4,500/month)"
        if commitment not in memory.get("commitments", []):
            add_commitment(memory, commitment)


def agent_turn(user_message: str, memory: dict) -> str:
    """Process one user turn: tool loop + LLM judgment."""
    session = CURRENT_SESSION
    memory_context = get_memory_context(memory)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"[MEMORY CONTEXT]\n{memory_context}\n\n[Current Date: 2024-11-0{3 if session == 1 else 6}] [Session: {session}]"},
        {"role": "user", "content": user_message},
    ]

    # Agent loop: call LLM, check for tool calls, execute, repeat
    max_iterations = 5
    for _ in range(max_iterations):
        response = call_llm(messages)
        tool_call = extract_tool_call(response)

        if tool_call is None:
            # No tool call — this is the final response
            break

        # Execute the tool
        tool_result = execute_tool(tool_call)
        messages.append({"role": "assistant", "content": response})
        messages.append({"role": "user", "content": f"[Tool Result for {tool_call['tool']}]:\n{tool_result}"})

    # Update memory
    add_conversation_turn(memory, "user", user_message, session)
    add_conversation_turn(memory, "assistant", response[:200], session)  # summary
    update_memory_from_conversation(memory, user_message, response)

    # Check if a reminder was set in this turn
    for msg in messages:
        content = msg.get("content", "")
        if "Tool Result for set_reminder" in content:
            try:
                # Extract JSON from tool result
                json_start = content.find("{")
                json_end = content.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    rem_data = json.loads(content[json_start:json_end])
                    add_reminder(memory, rem_data)
            except Exception as e:
                pass

    save_memory(memory)
    return response


def run_session(messages: list[str]) -> None:
    """Run a full session with multiple user messages."""
    memory = load_memory()

    # Set user profile on first run
    if not memory.get("user"):
        memory["user"] = {
            "name": "Priya Sharma",
            "age": 28,
            "city": "Bangalore",
            "monthly_income": 120000,
            "goal": "Save ₹15 lakh for house down payment",
        }

    print(f"\n{'='*60}")
    print(f"  SESSION {CURRENT_SESSION} — November {3 if CURRENT_SESSION == 1 else 6}, 2024")
    print(f"  {'Auto-detected' if len(sys.argv) <= 1 else 'Manual override'}")
    print(f"{'='*60}\n")

    for i, msg in enumerate(messages, 1):
        print(f"\n[User Turn {i}]: {msg}\n")
        print("-" * 40)
        response = agent_turn(msg, memory)
        print(f"\n[Agent]: {response}\n")
        print("=" * 60)


# --- Session Scripts ---

SESSION_1_MESSAGES = [
    "I just got my salary credited. Help me figure out how much I can realistically save this month.",
    "I feel like I'm spending too much on food delivery. How much did I actually spend on it last month?",
    "Okay that's worse than I thought. Let's say I want to cut that in half AND put aside ₹30,000 for my house fund this month — is that realistic given my upcoming bills?",
    "Got it. Remind me to actually transfer the ₹30,000 to my house fund on the 25th.",
]

SESSION_2_MESSAGES = [
    "Hey, my colleague is selling his MacBook for ₹80,000, barely used. I've been wanting to upgrade. Should I buy it?",
]


if __name__ == "__main__":
    if CURRENT_SESSION == 1:
        run_session(SESSION_1_MESSAGES)
    else:
        run_session(SESSION_2_MESSAGES)
