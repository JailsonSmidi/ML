#!/bin/bash

# ============================================================
# reorganize.sh — ML Market Research Automator
# Reorganiza os arquivos soltos para a estrutura correta
# Rode na RAIZ do repositório: bash reorganize.sh
# ============================================================

set -e  # Para imediatamente se qualquer comando falhar

echo ""
echo "================================================"
echo " ML Market Research — Reorganização de arquivos"
echo "================================================"
echo ""

# ─── Verificação de segurança ─────────────────────────────
if [ ! -d "backend" ] || [ ! -d "frontend" ]; then
  echo "❌ ERRO: Execute este script na raiz do repositório."
  echo "   Você deve ver as pastas 'backend' e 'frontend' aqui."
  exit 1
fi

echo "✓ Pastas backend/ e frontend/ encontradas."
echo ""

# ─── BACKEND ─────────────────────────────────────────────
echo "[ Backend ] Criando subpastas..."

mkdir -p backend/app/models
mkdir -p backend/app/routers
mkdir -p backend/app/workers
mkdir -p backend/app/services
mkdir -p backend/app/migrations/versions

echo "✓ Subpastas criadas."
echo ""

# ── Models ───────────────────────────────────────────────
echo "[ Backend ] Movendo models..."

for f in session.py batch.py product.py listing.py analysis.py; do
  if [ -f "backend/$f" ]; then
    mv "backend/$f" "backend/app/models/$f"
    echo "  ✓ $f → app/models/"
  else
    echo "  ⚠ $f não encontrado em backend/ — pulando"
  fi
done

# ── App core ─────────────────────────────────────────────
echo ""
echo "[ Backend ] Movendo arquivos core do app..."

for f in main.py config.py database.py; do
  if [ -f "backend/$f" ]; then
    mv "backend/$f" "backend/app/$f"
    echo "  ✓ $f → app/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# ── Routers ──────────────────────────────────────────────
echo ""
echo "[ Backend ] Movendo routers..."

for f in sessions.py batches_router.py products_router.py; do
  if [ -f "backend/$f" ]; then
    mv "backend/$f" "backend/app/routers/$f"
    echo "  ✓ $f → app/routers/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# Arquivo combinado de routers (listings, analyses, notifications)
if [ -f "backend/_combined.py" ]; then
  mv "backend/_combined.py" "backend/app/routers/_combined.py"
  echo "  ✓ _combined.py → app/routers/"
fi

# ── Workers ──────────────────────────────────────────────
echo ""
echo "[ Backend ] Movendo workers..."

for f in celery_app.py pdf_worker.py scraper_worker.py table_sync_worker.py; do
  if [ -f "backend/$f" ]; then
    mv "backend/$f" "backend/app/workers/$f"
    echo "  ✓ $f → app/workers/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# ── Services ─────────────────────────────────────────────
echo ""
echo "[ Backend ] Movendo services..."

for f in scraper.py pdf_parser.py margin_engine.py ml_table_scraper.py \
          notification_service.py term_validator.py visit_estimator.py; do
  if [ -f "backend/$f" ]; then
    mv "backend/$f" "backend/app/services/$f"
    echo "  ✓ $f → app/services/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# ── __init__.py dos models ───────────────────────────────
echo ""
echo "[ Backend ] Criando __init__.py..."

if [ -f "backend/__init__.py" ]; then
  mv "backend/__init__.py" "backend/app/models/__init__.py"
  echo "  ✓ __init__.py → app/models/"
else
  # Cria um __init__.py básico se não existir
  cat > backend/app/models/__init__.py << 'EOF'
from app.models.session import Session
from app.models.batch import Batch
from app.models.product import Product
from app.models.listing import Listing
from app.models.analysis import Analysis, MLShippingRate, MLCommissionRate, MLTableSyncLog, Notification

__all__ = [
    "Session", "Batch", "Product", "Listing",
    "Analysis", "MLShippingRate", "MLCommissionRate",
    "MLTableSyncLog", "Notification",
]
EOF
  echo "  ✓ __init__.py criado em app/models/"
fi

# __init__.py para os outros módulos
touch backend/app/__init__.py
touch backend/app/routers/__init__.py
touch backend/app/workers/__init__.py
touch backend/app/services/__init__.py
echo "  ✓ __init__.py criados para todos os módulos"

# ─── FRONTEND ────────────────────────────────────────────
echo ""
echo "[ Frontend ] Criando subpastas..."

mkdir -p frontend/src/pages
mkdir -p frontend/src/components
mkdir -p frontend/src/api
mkdir -p frontend/src/hooks
mkdir -p frontend/src/types

echo "✓ Subpastas criadas."
echo ""

# ── Páginas ──────────────────────────────────────────────
echo "[ Frontend ] Movendo páginas..."

for f in Upload.tsx Session.tsx BatchReview.tsx History.tsx; do
  if [ -f "frontend/$f" ]; then
    mv "frontend/$f" "frontend/src/pages/$f"
    echo "  ✓ $f → src/pages/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# ── Componentes ──────────────────────────────────────────
echo ""
echo "[ Frontend ] Movendo componentes..."

for f in Shell.tsx BatchStatusBar.tsx ListingCard.tsx MarginSimulator.tsx; do
  if [ -f "frontend/$f" ]; then
    mv "frontend/$f" "frontend/src/components/$f"
    echo "  ✓ $f → src/components/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# ── App e CSS (raiz do src/) ──────────────────────────────
echo ""
echo "[ Frontend ] Movendo arquivos raiz do src/..."

for f in App.tsx index.css; do
  if [ -f "frontend/$f" ]; then
    mv "frontend/$f" "frontend/src/$f"
    echo "  ✓ $f → src/"
  else
    echo "  ⚠ $f não encontrado — pulando"
  fi
done

# main.tsx (entry point)
if [ -f "frontend/main.tsx" ]; then
  mv "frontend/main.tsx" "frontend/src/main.tsx"
  echo "  ✓ main.tsx → src/"
fi

# ── API client ───────────────────────────────────────────
echo ""
echo "[ Frontend ] Movendo api e hooks..."

if [ -f "frontend/api.ts" ]; then
  mv "frontend/api.ts" "frontend/src/api/index.ts"
  echo "  ✓ api.ts → src/api/index.ts"
elif [ -f "frontend/index.ts" ]; then
  # pode ter sido salvo como index.ts direto
  mv "frontend/index.ts" "frontend/src/api/index.ts"
  echo "  ✓ index.ts → src/api/index.ts"
fi

if [ -f "frontend/hooks.ts" ]; then
  mv "frontend/hooks.ts" "frontend/src/hooks/index.ts"
  echo "  ✓ hooks.ts → src/hooks/index.ts"
fi

if [ -f "frontend/types.ts" ]; then
  mv "frontend/types.ts" "frontend/src/types/index.ts"
  echo "  ✓ types.ts → src/types/index.ts"
fi

# ── index.html fica na raiz do frontend/ (não em src/) ───
if [ -f "frontend/src/index.html" ]; then
  mv "frontend/src/index.html" "frontend/index.html"
  echo "  ✓ index.html movido para raiz do frontend/"
fi

# ─── Verificação final ───────────────────────────────────
echo ""
echo "================================================"
echo " Verificação da estrutura final"
echo "================================================"
echo ""
echo "Backend:"
find backend/app -type f -name "*.py" | sort | sed 's/^/  /'
echo ""
echo "Frontend src/:"
find frontend/src -type f | sort | sed 's/^/  /'
echo ""
echo "================================================"
echo " ✅ Reorganização concluída!"
echo ""
echo " Próximos passos:"
echo " 1. git add ."
echo " 2. git commit -m 'refactor: reorganize project structure'"
echo " 3. git push"
echo "================================================"
echo ""
