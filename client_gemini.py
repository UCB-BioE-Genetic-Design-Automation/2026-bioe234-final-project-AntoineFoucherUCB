"""
Requires a .env file in the project root containing:
    GEMINI_API_KEY="your_key_here"

Get a free key at: https://aistudio.google.com/api-keys
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from dotenv import load_dotenv

from mcp_gemini_engine import MCPGeminiEngine


async def run_chat() -> None:
    load_dotenv()
    engine = MCPGeminiEngine(project_dir=Path(__file__).parent)

    print("\nType a request. Ctrl-C to quit.\n")
    while True:
        try:
            user_text = input("You: ").strip()
        except EOFError:
            print("\nInput stream closed. Exiting chat.\n")
            break
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting chat.\n")
            break
        if not user_text:
            continue
        reply, _ = await engine.send_message(user_text)
        if reply:
            print(f"\nGemini: {reply}\n")


if __name__ == "__main__":
    asyncio.run(run_chat())