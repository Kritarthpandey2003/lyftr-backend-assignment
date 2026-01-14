# Lyftr AI Backend Assignment

## Setup Used
VSCode + Python 3.9 + Docker + Copilot/AI Assistant

## Design Decisions
1. **HMAC Verification**: Implemented using Python's standard `hmac` library. The raw request body bytes are hashed against the secret to verify the `X-Signature` header before any processing occurs.
2. **Idempotency**: Handled by checking if `message_id` exists in the SQLite database before insertion. If it exists, we return 200 OK immediately without re-inserting, ensuring "exactly once" processing.
3. **Metrics**: Custom in-memory counters implementation to satisfy the requirements without adding heavy external dependencies like Prometheus servers.

## How to Run
1. Ensure Docker is installed.
2. Run:
   ```bash
   docker compose up --build