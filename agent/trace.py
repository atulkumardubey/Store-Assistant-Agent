import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class TraceStep:
    step_number: int
    type: str        # "thought" | "action" | "observation" | "error"
    content: str
    tool: str | None = None
    args: dict | None = None
    result: dict | None = None


@dataclass
class Trace:
    query: str
    steps: list[TraceStep] = field(default_factory=list)
    final_answer: str = ""
    total_api_calls: int = 0
    tools_called: list[str] = field(default_factory=list)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


def save_trace(trace: Trace, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(trace), f, indent=2, ensure_ascii=False)


def print_trace(trace: Trace) -> None:
    print(f"\n{'=' * 60}")
    print(f"QUERY : {trace.query}")
    print(f"RUN ID: {trace.run_id[:8]}...")
    print(f"{'─' * 60}")
    for step in trace.steps:
        icon = {"thought": "💭", "action": "🔧", "observation": "👁", "error": "❌"}.get(step.type, "·")
        tool_tag = f" [{step.tool}]" if step.tool else ""
        print(f"  Step {step.step_number:02d} {icon} {step.type.upper()}{tool_tag}")
        if step.args:
            print(f"         args: {json.dumps(step.args)}")
        if step.result:
            print(f"         result: {json.dumps(step.result)}")
        elif step.content and step.type == "thought":
            snippet = step.content[:120].replace("\n", " ")
            print(f"         {snippet}{'...' if len(step.content) > 120 else ''}")
    print(f"{'─' * 60}")
    print(f"ANSWER: {trace.final_answer}")
    print(f"API calls: {trace.total_api_calls}  |  Tools: {trace.tools_called}")
    print(f"{'=' * 60}\n")
