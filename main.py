from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_gigachat import GigaChat
from pydantic import BaseModel, Field
from toon import decode as toon_decode
from toon import encode as toon_encode


class InventoryInsight(BaseModel):
    """Structured answer returned by the model."""

    summary: str = Field(description="One sentence summary of the inventory state.")
    top_sku: str = Field(description="SKU that should be restocked first.")
    reasons: list[str] = Field(description="Short reasons based only on the TOON data.")


SYSTEM_PROMPT = """You are an operations analyst. Use only the supplied TOON data.

TOON means Token-Oriented Object Notation. It is a compact, line-based text
format for JSON-like data:
- object fields are written as "key: value";
- nested objects are indented under their key;
- arrays can be written as "key[n]: item1,item2" or tabular rows such as
  "items[2,]{{field_a,field_b}}:" followed by rows.

Return exactly one TOON document and nothing else. Do not wrap it in Markdown.
Use this response schema:
summary: one sentence summary of the inventory state
top_sku: SKU that should be restocked first
reasons[2]: first reason,second reason
"""


def build_inventory_context() -> dict[str, Any]:
    return {
        "store": {
            "name": "Demo electronics store",
            "currency": "RUB",
            "analysis_date": "2026-04-28",
        },
        "products": [
            {
                "sku": "KB-101",
                "category": "keyboard",
                "stock": 4,
                "weekly_sales": 19,
                "margin_pct": 21,
            },
            {
                "sku": "MS-204",
                "category": "mouse",
                "stock": 18,
                "weekly_sales": 14,
                "margin_pct": 18,
            },
            {
                "sku": "MN-330",
                "category": "monitor",
                "stock": 2,
                "weekly_sales": 8,
                "margin_pct": 26,
            },
        ],
    }


def response_content_to_text(response: Any) -> str:
    """Normalize a LangChain chat response or raw value to plain text."""
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text") or item.get("content")
                if text is not None:
                    parts.append(str(text))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def extract_toon_document(text: str) -> str:
    """Accept bare TOON or a fenced ```toon block from a model response."""
    stripped = text.strip()
    fenced_match = re.search(r"```(?:toon)?\s*(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        return fenced_match.group(1).strip()
    return stripped


def parse_toon_response(response: Any) -> InventoryInsight:
    toon_text = extract_toon_document(response_content_to_text(response))
    decoded = toon_decode(toon_text)
    if isinstance(decoded, dict) and isinstance(decoded.get("reasons"), str):
        decoded = {
            **decoded,
            "reasons": [
                reason.strip()
                for reason in re.split(r"[,;\n]+", decoded["reasons"])
                if reason.strip()
            ],
        }
    return InventoryInsight.model_validate(decoded)


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    load_dotenv(example_dir / ".env")

    data = build_inventory_context()
    toon_context = toon_encode(data)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            (
                "human",
                "Inventory data in TOON:\n\n{toon_context}\n\n"
                "Which SKU should be restocked first and why?",
            ),
        ]
    )

    llm = GigaChat(temperature=0.1)
    chain = prompt | llm

    raw_response = chain.invoke({"toon_context": toon_context})
    raw_toon_response = response_content_to_text(raw_response)
    result = parse_toon_response(raw_response)

    print("TOON context sent to the model:")
    print(toon_context)
    print("\nRaw TOON model response:")
    print(raw_toon_response)
    print("\nParsed model result:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
