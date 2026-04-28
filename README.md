# GigaChain TOON Example

This directory contains a small Python example that:

- loads GigaChat credentials from `.env`;
- encodes tabular data to TOON with `python-toon`;
- sends that compact context through a LangChain prompt;
- calls GigaChat through `langchain-gigachat`;
- asks GigaChat to return TOON;
- decodes the TOON response and validates it with Pydantic.

## Why these packages

- `langchain-gigachat` is the current dedicated LangChain integration for GigaChat.
- `python-toon` provides `from toon import encode` and aims for compatibility with the TypeScript TOON implementation.
- `python-dotenv` loads local credentials from `.env`.
- `pydantic` validates the dict decoded from the TOON response.

Other Python TOON libraries worth knowing about:

- `py-toon-format`: has helpers such as `compare_sizes()` and validation.
- `toons`: Rust-backed parser/serializer exposed to Python.

## What is actually sent to the API

The example really sends TOON to GigaChat. `build_inventory_context()` creates a
Python dict, then `toon.encode()` turns it into this compact text:

```toon
store:
  name: Demo electronics store
  currency: RUB
  analysis_date: 2026-04-28
products[3,]{sku,category,stock,weekly_sales,margin_pct}:
  KB-101,keyboard,4,19,21
  MS-204,mouse,18,14,18
  MN-330,monitor,2,8,26
```

LangChain builds a chat request with two messages:

```text
system:
You are an operations analyst. Use only the supplied TOON data.

TOON means Token-Oriented Object Notation. It is a compact, line-based text
format for JSON-like data:
- object fields are written as "key: value";
- nested objects are indented under their key;
- arrays can be written as "key[n]: item1,item2" or tabular rows such as
  "items[2,]{field_a,field_b}:" followed by rows.

Return exactly one TOON document and nothing else. Do not wrap it in Markdown.
Use this response schema:
summary: one sentence summary of the inventory state
top_sku: SKU that should be restocked first
reasons[2]: first reason,second reason

human:
Inventory data in TOON:

store:
  name: Demo electronics store
  currency: RUB
  analysis_date: 2026-04-28
products[3,]{sku,category,stock,weekly_sales,margin_pct}:
  KB-101,keyboard,4,19,21
  MS-204,mouse,18,14,18
  MN-330,monitor,2,8,26

Which SKU should be restocked first and why?
```

`langchain-gigachat` converts those chat messages to the GigaChat API request.
The TOON string is not parsed by LangChain before the API call; it is sent as
plain message text.

## What comes back

The model is instructed to return a plain TOON document, for example:

```toon
summary: KB-101 should be restocked first because its stock is low compared with weekly sales.
top_sku: KB-101
reasons[2]: stock is 4 units while weekly sales are 19,highest immediate sales pressure among listed SKUs
```

The code then:

1. reads the raw chat response text;
2. accepts either bare TOON or a fenced `toon` code block;
3. decodes it with `toon.decode()`;
4. validates the decoded dict as `InventoryInsight`.

The parsed result printed by the script is JSON from the Pydantic model:

```json
{
  "summary": "KB-101 should be restocked first because its stock is low compared with weekly sales.",
  "top_sku": "KB-101",
  "reasons": [
    "stock is 4 units while weekly sales are 19",
    "highest immediate sales pressure among listed SKUs"
  ]
}
```

## Run

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The local `.env` is ignored by git. If it is missing, copy `.env.example` to `.env`
and fill either `GIGACHAT_CREDENTIALS` or `GIGACHAT_USER`/`GIGACHAT_PASSWORD`.
