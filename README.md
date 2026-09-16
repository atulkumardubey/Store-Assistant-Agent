# Store Assistant Agent — Project 4

A ReAct agent that decides which tools to call, chains them autonomously, and answers store queries without being told the step order.

## What it does

Given a customer request like *"2 blue shirts, size M, delivered to 560001"*, the agent:

1. **Reasons** about what information it needs
2. **Acts** by calling the right tool
3. **Observes** the result, then reasons again

It produces: stock status · price after discount · estimated delivery date — plus a full trace log of every step.

## Tools

| Tool | Data file | Purpose |
|---|---|---|
| `check_stock` | `data/inventory.json` | Verify product/size/quantity availability |
| `price_order` | `data/discounts.json` | Calculate total with tiered bulk discount |
| `delivery_eta` | `data/shipping.json` | Estimate delivery date by pincode zone |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your NVIDIA API key:

```
NVIDIA_API_KEY=nvapi-...
NVIDIA_LLM_MODEL=nvidia/nemotron-3.5-lightning-30b-a3b
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
```

## Run

```bash
python main.py
```

Runs 15 test queries across 5 scenarios and saves trace files to `traces/`.

## Test scenarios

| # | Theme | Expected tool chain |
|---|---|---|
| S1 | Happy path | `check_stock → price_order → delivery_eta` |
| S2 | Out of stock | `check_stock` only |
| S3 | Bulk discount (≥5 units) | `check_stock → price_order (discounted) → delivery_eta` |
| S4 | Unknown pincode | `check_stock → price_order → delivery_eta (error)` |
| S5 | Unknown product | `check_stock (error)` only |

## Reading the traces

Each `traces/trace_NN_SX-y.json` contains:
- `steps[]` — every thought, action, and observation in order
- `tools_called` — the sequence of tools the agent chose
- `final_answer` — the agent's response to the customer
- `total_api_calls` — LLM calls made to complete the task
