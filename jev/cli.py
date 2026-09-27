import json,sys
from pathlib import Path
from .evaluator import evaluate
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: python -m jev.cli <evidence.json>")
    print(json.dumps([x.to_dict() for x in evaluate(json.loads(Path(sys.argv[1]).read_text()))],indent=2))
