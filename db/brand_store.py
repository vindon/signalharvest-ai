from __future__ import annotations

import json
from datetime import datetime

from db.database import db_conn
from schemas.brand import BrandSubscription
from schemas.signal import SignalCategory, SignalTier


def _row_to_brand(r: dict) -> BrandSubscription:
    try:
        cats = [SignalCategory(c) for c in json.loads(r["categories"] or "[]")]
    except (ValueError, KeyError):
        cats = []
    if not cats:
        cats = [SignalCategory.OTHER]
    return BrandSubscription(
        id=r["id"],
        name=r["name"],
        contact_email=r["contact_email"],
        categories=cats,
        geographies=json.loads(r["geographies"] or "[]"),
        min_tier=SignalTier(r["min_tier"]) if r["min_tier"] else SignalTier.WARM,
        keywords_include=json.loads(r["keywords_include"] or "[]"),
        keywords_exclude=json.loads(r["keywords_exclude"] or "[]"),
        competitor_brands=json.loads(r["competitor_brands"] or "[]"),
        digest_frequency=r["digest_frequency"] or "daily",
        approval_required=bool(r["approval_required"]),
        active=bool(r["active"]),
        created_at=datetime.fromisoformat(r["created_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]) if r["updated_at"] else None,
    )


def upsert_brand(brand: BrandSubscription) -> None:
    with db_conn() as conn:
        conn.execute(
            """INSERT OR REPLACE INTO brands
               (id,name,contact_email,categories,geographies,min_tier,
                keywords_include,keywords_exclude,competitor_brands,
                digest_frequency,approval_required,active,created_at,updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                brand.id,
                brand.name,
                brand.contact_email,
                json.dumps([c.value for c in brand.categories]),
                json.dumps(brand.geographies),
                brand.min_tier.value,
                json.dumps(brand.keywords_include),
                json.dumps(brand.keywords_exclude),
                json.dumps(brand.competitor_brands),
                brand.digest_frequency,
                int(brand.approval_required),
                int(brand.active),
                brand.created_at.isoformat(),
                brand.updated_at.isoformat() if brand.updated_at else None,
            ),
        )


def get_active_brands() -> list[BrandSubscription]:
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM brands WHERE active=1 ORDER BY name ASC").fetchall()
    return [_row_to_brand(dict(r)) for r in rows]


def get_brand_by_id(brand_id: str) -> BrandSubscription | None:
    with db_conn() as conn:
        row = conn.execute("SELECT * FROM brands WHERE id=?", (brand_id,)).fetchone()
    return _row_to_brand(dict(row)) if row else None


def get_all_brands() -> list[BrandSubscription]:
    with db_conn() as conn:
        rows = conn.execute("SELECT * FROM brands ORDER BY name ASC").fetchall()
    return [_row_to_brand(dict(r)) for r in rows]


def delete_brand(brand_id: str) -> bool:
    with db_conn() as conn:
        cursor = conn.execute("DELETE FROM brands WHERE id=?", (brand_id,))
        return cursor.rowcount > 0
