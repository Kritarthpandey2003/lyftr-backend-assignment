from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Message
from typing import Optional

def get_message_by_id(db: Session, message_id: str):
    return db.query(Message).filter(Message.message_id == message_id).first()

def create_message(db: Session, msg_data: dict, created_at: str):
    db_msg = Message(
        message_id=msg_data['message_id'],
        from_msisdn=msg_data['from_msisdn'],
        to_msisdn=msg_data['to_msisdn'],
        ts=msg_data['ts'],
        text=msg_data.get('text'),
        created_at=created_at
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg

def get_messages(db: Session, limit: int, offset: int, 
                 from_filter: Optional[str], since_filter: Optional[str], q_filter: Optional[str]):
    query = db.query(Message)
    
    if from_filter:
        query = query.filter(Message.from_msisdn == from_filter)
    if since_filter:
        query = query.filter(Message.ts >= since_filter)
    if q_filter:
        query = query.filter(Message.text.contains(q_filter))
        
    total = query.count()
    items = query.order_by(Message.ts.asc(), Message.message_id.asc()).offset(offset).limit(limit).all()
    
    return items, total

def get_stats(db: Session):
    total_messages = db.query(Message).count()
    senders_count = db.query(Message.from_msisdn).distinct().count()
    
    top_senders = db.query(Message.from_msisdn, func.count(Message.message_id).label('count'))\
        .group_by(Message.from_msisdn)\
        .order_by(func.count(Message.message_id).desc())\
        .limit(10).all()
        
    min_ts = db.query(func.min(Message.ts)).scalar()
    max_ts = db.query(func.max(Message.ts)).scalar()
    
    return {
        "total_messages": total_messages,
        "senders_count": senders_count,
        "messages_per_sender": [{"from": r[0], "count": r[1]} for r in top_senders],
        "first_message_ts": min_ts,
        "last_message_ts": max_ts
    }