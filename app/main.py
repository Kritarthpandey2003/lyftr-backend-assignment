import hmac
import hashlib
import time
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Depends, Header, Response, Query
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.models import SessionLocal, init_db
from app import storage, logging_utils, metrics

app = FastAPI()
logger = logging_utils.logger

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup Event
@app.on_event("startup")
def startup_event():
    if not settings.WEBHOOK_SECRET:
        raise RuntimeError("WEBHOOK_SECRET is not set")
    init_db()

# Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000
    
    logger.info("Request processed", extra={
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "status": response.status_code,
        "latency_ms": round(latency_ms, 2)
    })
    metrics.increment_http_request(request.url.path, response.status_code)
    return response

# Routes
@app.post("/webhook")
async def webhook_ingest(
    request: Request, 
    x_signature: Optional[str] = Header(None, alias="X-Signature"),
    db: Session = Depends(get_db)
):
    body_bytes = await request.body()
    
    # 1. Validate Signature
    if not x_signature:
        metrics.increment_webhook_result("invalid_signature")
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})
        
    computed_sig = hmac.new(
        key=settings.WEBHOOK_SECRET.encode(),
        msg=body_bytes,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(computed_sig, x_signature):
        metrics.increment_webhook_result("invalid_signature")
        logger.error("Invalid Signature", extra={"result": "invalid_signature"})
        return JSONResponse(status_code=401, content={"detail": "invalid signature"})

    # 2. Parse Payload
    try:
        json_data = await request.json()
        if 'from' in json_data:
            json_data['from_msisdn'] = json_data.pop('from')
        else:
             raise ValueError("Missing 'from' field")
        
        if 'to' in json_data:
            json_data['to_msisdn'] = json_data.pop('to')
        else:
             raise ValueError("Missing 'to' field")

        if not json_data.get('message_id'):
            raise ValueError("Empty message_id")
            
    except Exception as e:
        metrics.increment_webhook_result("validation_error")
        return JSONResponse(status_code=422, content={"detail": str(e)})

    message_id = json_data['message_id']

    # 3. Idempotency Check
    existing = storage.get_message_by_id(db, message_id)
    if existing:
        metrics.increment_webhook_result("duplicate")
        logger.info("Duplicate message", extra={"message_id": message_id, "dup": True, "result": "duplicate"})
        return {"status": "ok"}

    # 4. Save to DB
    storage.create_message(db, json_data, created_at=datetime.utcnow().isoformat() + "Z")
    
    metrics.increment_webhook_result("created")
    logger.info("Message created", extra={"message_id": message_id, "dup": False, "result": "created"})
    return {"status": "ok"}

@app.get("/messages")
def list_messages(
    limit: int = 50, 
    offset: int = 0, 
    from_: Optional[str] = Query(None, alias="from"),
    since: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db)
):
    items, total = storage.get_messages(db, limit, offset, from_, since, q)
    data = []
    for m in items:
        data.append({
            "message_id": m.message_id,
            "from": m.from_msisdn,
            "to": m.to_msisdn,
            "ts": m.ts,
            "text": m.text
        })
    return {"data": data, "total": total, "limit": limit, "offset": offset}

@app.get("/stats")
def get_stats_endpoint(db: Session = Depends(get_db)):
    return storage.get_stats(db)

@app.get("/health/live")
def health_live():
    return {"status": "alive"}

@app.get("/health/ready")
def health_ready(db: Session = Depends(get_db)):
    try:
        db.execute(storage.func.now()) 
        if not settings.WEBHOOK_SECRET:
            return Response(status_code=503)
        return {"status": "ready"}
    except Exception:
        return Response(status_code=503)

@app.get("/metrics")
def get_metrics():
    return PlainTextResponse(metrics.generate_metrics_text())