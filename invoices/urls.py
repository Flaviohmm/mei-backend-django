from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSet
router = DefaultRouter()
router.register(r'invoices', views.InvoiceViewSet, basename='invoice')

urlpatterns = [
    # API endpoints
    path('api/v1/', include(router.urls)),
]

# URLs disponíveis:
# GET    /api/v1/invoices/                 - Listar todas as notas fiscais
# POST   /api/v1/invoices/                 - Criar nova nota fiscal
# GET    /api/v1/invoices/{id}/            - Detalhar nota fiscal específica
# PUT    /api/v1/invoices/{id}/            - Atualizar nota fiscal completa
# PATCH  /api/v1/invoices/{id}/            - Atualizar nota fiscal parcial
# DELETE /api/v1/invoices/{id}/            - Deletar nota fiscal
# POST   /api/v1/invoices/{id}/activate/   - Ativar nota fiscal
# POST   /api/v1/invoices/{id}/deactivate/ - Desativar nota fiscal
# GET    /api/v1/invoices/statistics/      - Estatísticas das notas fiscais
# GET    /api/v1/invoices/export/          - Exportar dados das notas fiscais

# Exemplos de uso com parâmetros de filtro:
# GET /api/v1/invoices/?client_type=pf
# GET /api/v1/invoices/?service_type=dev
# GET /api/v1/invoices/?payment_method=pix
# GET /api/v1/invoices/?state=SP
# GET /api/v1/invoices/?is_active=true
# GET /api/v1/invoices/?search=joão
# GET /api/v1/invoices/?ordering=-created_at
# GET /api/v1/invoices/?start_date=2024-01-01&end_date=2024-12-31
# GET /api/v1/invoices/?overdue=true
