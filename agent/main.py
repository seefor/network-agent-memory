import argparse,asyncio,json,os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPToolset
from jev import evaluate
from .prompts import SYSTEM_PROMPT
async def run():
    p=argparse.ArgumentParser(); p.add_argument("--evidence",required=True); p.add_argument("question",nargs="+"); a=p.parse_args()
    load_dotenv(); ev=json.loads(Path(a.evidence).read_text()); findings=[x.to_dict() for x in evaluate(ev)]
    agent=Agent(os.getenv("MODEL","openai:gpt-5.2"),system_prompt=SYSTEM_PROMPT,toolsets=[MCPToolset(os.getenv("INFRAHUB_MCP_URL","http://localhost:8001/mcp"))])
    result=await agent.run(json.dumps({"collector_evidence":ev,"jev_validated_findings":findings},indent=2)+"\nQUESTION:\n"+" ".join(a.question))
    print(result.output)
if __name__=="__main__": asyncio.run(run())
