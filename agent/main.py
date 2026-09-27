import argparse
import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset

from .prompts import SYSTEM_PROMPT


async def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    parser.add_argument("question", nargs="+")
    args = parser.parse_args()

    load_dotenv()
    evidence = json.loads(Path(args.evidence).read_text())

    infrahub = MCPToolset(
        os.getenv("INFRAHUB_MCP_URL", "http://localhost:8001/mcp")
    )

    agent = Agent(
        os.getenv("MODEL", "openai:gpt-5.2"),
        system_prompt=SYSTEM_PROMPT,
        toolsets=[infrahub],
    )

    prompt = (
        "The following is fresh collector evidence for this investigation. "
        "Use Infrahub for infrastructure context and relationships.\n\n"
        + json.dumps({"collector_evidence": evidence}, indent=2)
        + "\n\nQUESTION:\n"
        + " ".join(args.question)
    )

    result = await agent.run(prompt)
    print(result.output)


if __name__ == "__main__":
    asyncio.run(run())
