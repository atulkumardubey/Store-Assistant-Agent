import json

import agent.llm_client as _llm
from agent.llm_client import get_client, CALL_KWARGS
from agent.trace import Trace, TraceStep
from tools import TOOL_SCHEMAS, check_stock, price_order, delivery_eta

MAX_ITERATIONS = 10

SYSTEM_PROMPT = """You are a store assistant agent. A customer will give you a product order request.
Your job is to gather all necessary information using the available tools, then give a clear final answer.

Rules you must follow:
- Always call check_stock first to verify availability before doing anything else.
- Only call price_order if check_stock confirmed the item is in stock (in_stock = true).
- Only call delivery_eta if check_stock confirmed the item is in stock (in_stock = true).
- If check_stock returns in_stock = false, stop tool calls immediately and inform the customer.
  Do NOT call price_order or delivery_eta when the item is out of stock or unavailable.
- If a tool returns an error field, report it clearly in your final response.
- Your final response must include: stock status, price with any discount (if in stock),
  and estimated delivery date (if in stock).
- Be concise and friendly in your final answer."""

TOOL_DISPATCH = {
    "check_stock": check_stock,
    "price_order": price_order,
    "delivery_eta": delivery_eta,
}


def stream_react_agent(query: str):
    """Generator that yields step dicts as they occur — used by the API for SSE streaming."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    step_num = 0
    api_calls = 0
    tools_called = []

    yield {"type": "start", "query": query}

    for _ in range(MAX_ITERATIONS):
        response = get_client().chat.completions.create(
            model=_llm.MODEL_ID,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            **CALL_KWARGS,
        )
        api_calls += 1
        choice = response.choices[0]
        assistant_msg = choice.message

        if assistant_msg.content:
            step_num += 1
            yield {"type": "thought", "step": step_num, "content": assistant_msg.content}

        if choice.finish_reason == "stop":
            yield {"type": "final", "answer": assistant_msg.content or "", "tools_called": tools_called, "api_calls": api_calls}
            return

        if choice.finish_reason == "tool_calls" and assistant_msg.tool_calls:
            messages.append(assistant_msg)

            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as exc:
                    args = {}
                    result = {"error": "invalid_arguments", "message": str(exc)}
                else:
                    fn = TOOL_DISPATCH.get(name)
                    if fn is None:
                        result = {"error": "unknown_tool", "message": f"No tool named '{name}'"}
                    else:
                        try:
                            result = fn(**args)
                        except Exception as exc:
                            result = {"error": "tool_execution_error", "message": str(exc)}

                step_num += 1
                yield {"type": "action", "step": step_num, "tool": name, "args": args}

                step_num += 1
                yield {"type": "observation", "step": step_num, "tool": name, "result": result}
                tools_called.append(name)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })
        else:
            yield {"type": "final", "answer": assistant_msg.content or f"[stopped: {choice.finish_reason}]", "tools_called": tools_called, "api_calls": api_calls}
            return

    yield {"type": "final", "answer": "[Agent reached iteration limit]", "tools_called": tools_called, "api_calls": api_calls}


def run_react_agent(query: str) -> Trace:
    trace = Trace(query=query)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    step_num = 0

    for _ in range(MAX_ITERATIONS):
        response = get_client().chat.completions.create(
            model=_llm.MODEL_ID,
            messages=messages,
            tools=TOOL_SCHEMAS,
            tool_choice="auto",
            **CALL_KWARGS,
        )
        trace.total_api_calls += 1
        choice = response.choices[0]
        assistant_msg = choice.message

        if assistant_msg.content:
            step_num += 1
            trace.steps.append(TraceStep(
                step_number=step_num,
                type="thought",
                content=assistant_msg.content,
            ))

        if choice.finish_reason == "stop":
            trace.final_answer = assistant_msg.content or ""
            break

        if choice.finish_reason == "tool_calls" and assistant_msg.tool_calls:
            messages.append(assistant_msg)

            for tool_call in assistant_msg.tool_calls:
                name = tool_call.function.name

                try:
                    args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError as exc:
                    args = {}
                    result = {"error": "invalid_arguments", "message": str(exc)}
                else:
                    fn = TOOL_DISPATCH.get(name)
                    if fn is None:
                        result = {"error": "unknown_tool", "message": f"No tool named '{name}'"}
                    else:
                        try:
                            result = fn(**args)
                        except Exception as exc:
                            result = {"error": "tool_execution_error", "message": str(exc)}

                step_num += 1
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    type="action",
                    content=f"Calling {name}",
                    tool=name,
                    args=args,
                ))

                step_num += 1
                trace.steps.append(TraceStep(
                    step_number=step_num,
                    type="observation",
                    content=json.dumps(result),
                    tool=name,
                    result=result,
                ))

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                })
        else:
            # Unexpected finish reason — treat as terminal
            trace.final_answer = assistant_msg.content or f"[stopped: {choice.finish_reason}]"
            break
    else:
        trace.final_answer = "[Agent reached iteration limit without completing the task]"

    trace.tools_called = [s.tool for s in trace.steps if s.type == "action" and s.tool]
    return trace
