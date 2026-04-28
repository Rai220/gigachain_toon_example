from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_gigachat import GigaChat
from pydantic import BaseModel, Field
from toon import encode as toon_encode


class InventoryInsight(BaseModel):
    """Structured answer returned by the model."""

    summary: str = Field(description="One sentence summary of the inventory state.")
    top_sku: str = Field(description="SKU that should be restocked first.")
    reasons: list[str] = Field(description="Short reasons based only on the TOON data.")


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


def main() -> None:
    example_dir = Path(__file__).resolve().parent
    load_dotenv(example_dir / ".env")

    data = build_inventory_context()
    toon_context = toon_encode(data)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an operations analyst. Use only the supplied TOON data. "
                "Return a concise structured answer.",
            ),
            (
                "human",
                "Inventory data in TOON:\n\n{toon_context}\n\n"
                "Which SKU should be restocked first and why?",
            ),
        ]
    )

    llm = GigaChat(temperature=0.1)
    structured_llm = llm.with_structured_output(InventoryInsight)
    chain = prompt | structured_llm

    result = chain.invoke({"toon_context": toon_context})

    print("TOON context sent to the model:")
    print(toon_context)
    print("\nStructured model result:")
    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
