import base64
from uuid import UUID
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Session as SessionModel, Batch, Product
from app.workers.pdf_worker import process_pdf

router = APIRouter()


@router.post("/")
async def create_session(
    file: UploadFile = File(...),
    supplier_name: str = Form(...),
    tax_rate: float = Form(4.0),
    db: AsyncSession = Depends(get_db),
):
    """Recebe o PDF do catálogo, cria a sessão e enfileira o processamento."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são aceitos.")

    pdf_bytes = await file.read()
    if len(pdf_bytes) > 50 * 1024 * 1024:  # 50MB
        raise HTTPException(status_code=400, detail="PDF deve ter no máximo 50MB.")

    session = SessionModel(
        supplier_name=supplier_name,
        pdf_filename=file.filename,
        tax_rate=tax_rate,
        status="pending",
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    # Enfileira o processamento do PDF como task Celery
    pdf_b64 = base64.b64encode(pdf_bytes).decode()
    process_pdf.apply_async(
        args=[str(session.id), pdf_b64],
        queue="pdf",
    )

    return {
        "id": str(session.id),
        "supplier_name": session.supplier_name,
        "status": session.status,
        "created_at": session.created_at,
    }


@router.get("/")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """Lista todas as sessões ordenadas da mais recente para a mais antiga."""
    result = await db.execute(
        select(SessionModel).order_by(desc(SessionModel.created_at))
    )
    sessions = result.scalars().all()
    return [
        {
            "id": str(s.id),
            "supplier_name": s.supplier_name,
            "pdf_filename": s.pdf_filename,
            "tax_rate": float(s.tax_rate),
            "status": s.status,
            "created_at": s.created_at,
            "finished_at": s.finished_at,
        }
        for s in sessions
    ]


@router.get("/{session_id}")
async def get_session(session_id: UUID, db: AsyncSession = Depends(get_db)):
    """Retorna detalhes de uma sessão com contagem de produtos por status."""
    session = await db.get(SessionModel, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    # Contagem de produtos por status
    products_result = await db.execute(
        select(Product).where(Product.session_id == session_id)
    )
    products = products_result.scalars().all()
    status_counts = {}
    for p in products:
        status_counts[p.status] = status_counts.get(p.status, 0) + 1

    # Lotes
    batches_result = await db.execute(
        select(Batch)
        .where(Batch.session_id == session_id)
        .order_by(Batch.batch_number.asc())
    )
    batches = batches_result.scalars().all()

    return {
        "id": str(session.id),
        "supplier_name": session.supplier_name,
        "pdf_filename": session.pdf_filename,
        "tax_rate": float(session.tax_rate),
        "status": session.status,
        "created_at": session.created_at,
        "finished_at": session.finished_at,
        "product_count": len(products),
        "product_status_counts": status_counts,
        "batches": [
            {
                "id": str(b.id),
                "batch_number": b.batch_number,
                "status": b.status,
                "scheduled_at": b.scheduled_at,
                "started_at": b.started_at,
                "finished_at": b.finished_at,
            }
            for b in batches
        ],
    }
