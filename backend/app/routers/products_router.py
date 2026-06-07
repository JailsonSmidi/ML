from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Product, Batch

# ─── Products ─────────────────────────────────────────────────────────────────

router = APIRouter()


@router.get("/{product_id}")
async def get_product(product_id: UUID, db: AsyncSession = Depends(get_db)):
    product = await db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    return {
        "id": str(product.id),
        "session_id": str(product.session_id),
        "batch_id": str(product.batch_id) if product.batch_id else None,
        "catalog_name": product.catalog_name,
        "description": product.description,
        "cost_price": float(product.cost_price),
        "units_per_box": product.units_per_box,
        "weight_kg": float(product.weight_kg) if product.weight_kg else None,
        "dimensions_cm": product.dimensions_cm,
        "search_terms": product.search_terms,
        "best_search_term": product.best_search_term,
        "status": product.status,
        "batch_number": product.batch_number,
        "error_message": product.error_message,
        "created_at": product.created_at,
        "updated_at": product.updated_at,
    }
