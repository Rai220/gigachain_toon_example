# GigaChain TOON Example

This directory contains a small Python example that:

- loads GigaChat credentials from `.env`;
- encodes tabular data to TOON with `python-toon`;
- sends that compact context through a LangChain prompt;
- calls GigaChat through `langchain-gigachat`;
- asks LangChain/GigaChat for a Pydantic structured result.

## Why these packages

- `langchain-gigachat` is the current dedicated LangChain integration for GigaChat.
- `python-toon` provides `from toon import encode` and aims for compatibility with the TypeScript TOON implementation.
- `python-dotenv` loads local credentials from `.env`.
- `pydantic` is used by LangChain structured output.

Other Python TOON libraries worth knowing about:

- `py-toon-format`: has helpers such as `compare_sizes()` and validation.
- `toons`: Rust-backed parser/serializer exposed to Python.

## Run

```bash
cd gigachain_toon_example
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

The local `.env` is ignored by git. If it is missing, copy `.env.example` to `.env`
and fill either `GIGACHAT_CREDENTIALS` or `GIGACHAT_USER`/`GIGACHAT_PASSWORD`.
