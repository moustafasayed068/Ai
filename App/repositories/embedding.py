from sqlalchemy.orm import Session
from App.models.embedding import Embedding
from uuid import UUID

def create_embedding(db: Session, chat_id: UUID, vector: list[float]) -> Embedding:
    emb = db.query(Embedding).filter(Embedding.chat_id == chat_id).first()
    if emb:
        emb.vector = vector
        db.commit()
        db.refresh(emb)
        return emb
    db_emb = Embedding(chat_id=chat_id, vector=vector)
    db.add(db_emb)
    db.commit()
    db.refresh(db_emb)
    return db_emb

def get_embedding(db: Session, chat_id: UUID) -> Embedding | None:
    return db.query(Embedding).filter(Embedding.chat_id == chat_id).first()


def get_all_embeddings(db: Session, chat_id: UUID | None = None) -> list[Embedding]:
    query = db.query(Embedding)
    if chat_id:
        query = query.filter(Embedding.chat_id == chat_id)
    return query.all()