

## Requirements

    postgresql with deployed arm2-gateway databases. No schema here
    redis

## Install

    python3 -m venv venv
    venv/bin/pip install -r requirements.txt

## Tests

    PYTHONPATH=src venv/bin/py.test -s tests/

## Docs

Docs in [docs](/docs) directory.

[Design docs](/docs/design.md)

[WebSocket protocol docs](/docs/chat-protocol.md)
