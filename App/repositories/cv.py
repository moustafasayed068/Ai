import uuid
from sqlalchemy.orm import Session
from sqlalchemy import text
from App.models.cv import CV, CVSkill


# ---------- CV ----------

async def create_cv(
    db: Session,
    owner_id,
    file_url: str,
    full_text: str,
    name: str,
    education: str,
    experience_years: float,
    summary: str,
) -> CV:
    cv = CV(
        id=uuid.uuid4(),
        owner_id=owner_id,
        file_url=file_url,
        full_text=full_text,
        name=name,
        education=education,
        experience_years=experience_years,
        summary=summary,
    )
    db.add(cv)
    db.commit()
    db.refresh(cv)
    return cv


async def get_cv_by_id(db: Session, cv_id) -> CV:
    return db.query(CV).filter(CV.id == cv_id).first()


async def get_all_cvs(db: Session) -> list[CV]:
    return db.query(CV).all()


# ---------- Skills ----------

async def create_skills(db: Session, cv_id, skill_rows: list[dict]):
    """Bulk insert skill rows with embeddings."""
    for row in skill_rows:
        skill = CVSkill(
            id=uuid.uuid4(),
            cv_id=cv_id,
            skill=row["skill"],
            category=row["category"],
            embedding=row["embedding"],
        )
        db.add(skill)
    db.commit()


# ---------- Match Search ----------

async def search_matching_cvs(
    db: Session,
    query_vector: list[float],
    must_have: list[str],
    top_k: int = 5,
) -> list[dict]:
    """
    Search cv_skills by vector similarity.
    Groups results by cv_id, counts matched skills, averages distance.
    Optionally pre-filters by must_have skills (exact, case-insensitive).
    """
    vector_str = "[" + ",".join(str(x) for x in query_vector) + "]"

    # Build optional must_have filter
    # We only return CVs that have ALL must_have skills
    must_have_clause = ""
    must_have_params = {}

    if must_have:
        # Find cv_ids that contain ALL must_have skills
        placeholders = ", ".join(f":skill_{i}" for i in range(len(must_have)))
        must_have_params = {f"skill_{i}": s.lower() for i, s in enumerate(must_have)}
        must_have_clause = f"""
            AND cs.cv_id IN (
                SELECT cv_id FROM cv_skills
                WHERE LOWER(skill) IN ({placeholders})
                GROUP BY cv_id
                HAVING COUNT(DISTINCT LOWER(skill)) = :must_have_count
            )
        """
        must_have_params["must_have_count"] = len(must_have)

    sql = text(f"""
        SELECT
            cs.cv_id,
            COUNT(cs.id)                                                        AS matched_count,
            AVG(cs.embedding <-> CAST(:query_vector AS vector))                 AS avg_distance,
            ARRAY_AGG(cs.skill ORDER BY cs.embedding <-> CAST(:query_vector AS vector)) AS matched_skills
        FROM cv_skills cs
        WHERE cs.embedding IS NOT NULL
        {must_have_clause}
        GROUP BY cs.cv_id
        ORDER BY avg_distance ASC
        LIMIT :top_k
    """)

    params = {"query_vector": vector_str, "top_k": top_k, **must_have_params}
    result = db.execute(sql, params).fetchall()

    if not result:
        return []

    # Hydrate with CV metadata
    cv_ids = [row.cv_id for row in result]
    cvs = db.query(CV).filter(CV.id.in_(cv_ids)).all()
    cv_map = {str(cv.id): cv for cv in cvs}

    output = []
    for row in result:
        cv = cv_map.get(str(row.cv_id))
        if not cv:
            continue
        output.append({
            "cv_id": row.cv_id,
            "name": cv.name,
            "education": cv.education,
            "experience_years": cv.experience_years,
            "summary": cv.summary,
            "file_url": cv.file_url,
            "matched_skills": list(row.matched_skills or [])[:10],  # cap display list
            "match_score": round(float(row.avg_distance), 4),
        })

    return output
