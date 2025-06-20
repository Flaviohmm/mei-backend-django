from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
from .models import Invoice
from .serializers import (
    InvoiceSerializer,
    InvoiceCreateSerializer,
    InvoiceListSerializer,
    InvoiceUpdateSerializer
)

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet completo para operações CRUD de Notas Fiscais
    """
    queryset = Invoice.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client_type', 'service_type', 'payment_method', 'state', 'is_active']
    search_fields = ['name', 'email', 'document', 'invoice_number', 'service_description']
    ordering_fields = ['created_at', 'issue_date', 'due_date', 'value']
    ordering = ['-created_at']

    def get_serializer_class(self):
        """Retorna o serializer apropriado baseado na action"""
        if self.action == 'create':
            return InvoiceCreateSerializer
        elif self.action == 'list':
            return InvoiceListSerializer
        elif self.action in ['update', 'partial_update']:
            return InvoiceUpdateSerializer
        return InvoiceSerializer
    
    def get_queryset(self):
        """Filtra queryset baseado em parâmetros da query"""
        queryset = Invoice.objects.all()

        # Filtro por período
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)

        if start_date:
            queryset = queryset.filter(issue_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(issue_date__lte=end_date)

        # Filtro por vencimento
        overdue = self.request.query_params.get('overdue', None)
        if overdue == 'true':
            queryset = queryset.filter(
                due_date__lt=timezone.now().date(),
                is_active=True
            )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        """Criar nova nota fiscal"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        
        # Retorna dados completos da nota criada
        response_serializer = InvoiceSerializer(invoice)
        return Response(
            response_serializer.data, 
            status=status.HTTP_201_CREATED
        )
    
    def update(self, request, *args, **kwargs):
        """Atualizar nota fiscal"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        invoice = serializer.save()
        
        # Retorna dados completos da nota atualizada
        response_serializer = InvoiceSerializer(invoice)
        return Response(response_serializer.data)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Ativar nota fiscal"""
        invoice = self.get_object()
        invoice.is_active = True
        invoice.save()
        return Response(
            {'message': 'Nota fiscal ativada com sucesso'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Desativar nota fiscal"""
        invoice = self.get_object()
        invoice.is_active = False
        invoice.save()
        return Response(
            {'message': 'Nota fiscal desativada com sucesso'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Estatísticas das notas fiscais"""
        queryset = self.get_queryset()
        
        total_invoices = queryset.count()
        active_invoices = queryset.filter(is_active=True).count()
        overdue_invoices = queryset.filter(
            due_date__lt=timezone.now().date(),
            is_active=True
        ).count()
        
        total_value = sum(invoice.total_value for invoice in queryset.filter(is_active=True))
        
        # Estatísticas por tipo de cliente
        pf_count = queryset.filter(client_type='pf', is_active=True).count()
        pj_count = queryset.filter(client_type='pj', is_active=True).count()
        
        # Estatísticas por tipo de serviço
        service_stats = {}
        for choice in Invoice.SERVICE_TYPE_CHOICES:
            service_stats[choice[0]] = queryset.filter(
                service_type=choice[0],
                is_active=True
            ).count()
        
        return Response({
            'total_invoices': total_invoices,
            'active_invoices': active_invoices,
            'overdue_invoices': overdue_invoices,
            'total_value': total_value,
            'client_types': {
                'pessoa_fisica': pf_count,
                'pessoa_juridica': pj_count
            },
            'service_types': service_stats
        })
    
    @action(detail=False, methods=['get'])
    def export(self, request):
        """Exportar notas fiscais (dados para relatório)"""
        queryset = self.get_queryset()
        serializer = InvoiceSerializer(queryset, many=True)
        
        return Response({
            'invoices': serializer.data,
            'total_count': queryset.count(),
            'export_date': timezone.now().isoformat()
        })