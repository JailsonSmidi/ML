from uuid import UUID
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Batch, Product

router = APIRouter()


@router.get("/sessions/{session_id}/batches")
async def get_batches(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retorna todos os lotes de uma sessão com contagem de produtos."""
    result = await db.execute(
        select(Batch)
        .where(Batch.session_id == session_id)
        .order_by(Batch.batch_number.asc())
    )
    batches = result.scalars().all()

    output = []
    for b in batches:
        products_result = await db.execute(
            select(Product).where(Product.batch_id == b.id)
        )
        products = products_result.scalars().all()
        status_counts = {}
        for p in products:
            status_counts[p.status] = status_counts.get(p.status, 0) + 1

        output.append({
            "id": str(b.id),
            "batch_number": b.batch_number,
            "status": b.status,
            "product_count": len(products),
            "product_status_counts": status_counts,
            "scheduled_at": b.scheduled_at,
            "started_at": b.started_at,
            "finished_at": b.finished_at,
        })

    return output
