# invoices/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from decimal import Decimal, InvalidOperation
from .models import Invoice

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    # Campos para exibir na lista
    list_display = (
        'invoice_number', 
        'name', 
        'client_type', 
        'service_type',
        'value', 
        'tax', 
        'display_total',
        'due_date',
        'issue_date',
        'is_active'
    )
    
    # Filtros na barra lateral
    list_filter = (
        'client_type',
        'service_type', 
        'payment_method',
        'state',
        'is_active',
        'issue_date',
        'due_date'
    )
    
    # Campos de busca
    search_fields = (
        'invoice_number',
        'name',
        'document',
        'email',
        'city'
    )
    
    # Campos somente leitura
    readonly_fields = (
        'id',
        'invoice_number',
        'created_at',
        'updated_at',
        'display_total_detail',
        'display_tax_amount'
    )
    
    # Ordenação padrão
    ordering = ('-created_at',)
    
    # Campos editáveis na lista
    list_editable = ('is_active',)
    
    # Paginação
    list_per_page = 25
    
    # Organização dos campos no formulário
    fieldsets = (
        ('Identificação', {
            'fields': ('id', 'invoice_number')
        }),
        ('Dados do Cliente', {
            'fields': (
                'client_type',
                'document',
                'name',
                'email',
                'phone'
            )
        }),
        ('Endereço', {
            'fields': (
                'address',
                'neighborhood',
                'city',
                'state',
                'zip_code'
            ),
            'classes': ('collapse',)
        }),
        ('Serviços', {
            'fields': (
                'service_type',
                'service_description',
                'value',
                'tax',
                'display_tax_amount',
                'display_total_detail'
            )
        }),
        ('Pagamento', {
            'fields': (
                'payment_method',
                'due_date',
                'issue_date'
            )
        }),
        ('Informações Adicionais', {
            'fields': ('additional_info',),
            'classes': ('collapse',)
        }),
        ('Controle', {
            'fields': (
                'is_active',
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    # Métodos para exibição customizada
    def display_total(self, obj):
        """Exibe o total na lista"""
        try:
            total = obj.total_value
            # Garantir que total é um Decimal e converter para float
            if not isinstance(total, Decimal):
                total = Decimal(str(total))
            
            return format_html(
                '<strong style="color: #28a745;">R$ {}</strong>', 
                f"{float(total):.2f}"
            )
        except (ValueError, TypeError, InvalidOperation) as e:
            return format_html(
                '<span style="color: #dc3545;">Erro</span>'
            )
    display_total.short_description = 'Total'
    display_total.admin_order_field = 'value'
    
    def display_total_detail(self, obj):
        """Exibe detalhes do total no formulário"""
        try:
            # Obter valores de forma segura, convertendo para Decimal primeiro
            value = obj.value if obj.value is not None else Decimal('0.00')
            tax_rate = obj.tax if obj.tax is not None else Decimal('0.00')
            
            # Garantir que são Decimal
            if not isinstance(value, Decimal):
                value = Decimal(str(value))
            if not isinstance(tax_rate, Decimal):
                tax_rate = Decimal(str(tax_rate))
            
            # Calcular valores
            tax_amount = obj.tax_amount
            total = obj.total_value
            
            # Garantir que tax_amount e total são Decimal
            if not isinstance(tax_amount, Decimal):
                tax_amount = Decimal(str(tax_amount))
            if not isinstance(total, Decimal):
                total = Decimal(str(total))
            
            # Converter para float apenas no momento da formatação
            return format_html(
                '''
                <div style="background: #1f2937; padding: 10px; border-radius: 5px;">
                    <strong>Cálculo do Total:</strong><br>
                    Valor: R$ {}<br>
                    Imposto ({}%): R$ {}<br>
                    <hr style="margin: 5px 0;">
                    <strong>Total: R$ {}</strong>
                </div>
                ''',
                f"{float(value):.2f}",
                f"{float(tax_rate):.2f}",
                f"{float(tax_amount):.2f}",
                f"{float(total):.2f}"
            )
        except (ValueError, TypeError, InvalidOperation) as e:
            return format_html(
                '<span style="color: #dc3545;">Erro no cálculo: {}</span>',
                str(e)
            )
    display_total_detail.short_description = 'Total Calculado'
    
    def display_tax_amount(self, obj):
        """Exibe o valor do imposto"""
        try:
            tax_amount = obj.tax_amount
            if not isinstance(tax_amount, Decimal):
                tax_amount = Decimal(str(tax_amount))
            return f"R$ {float(tax_amount):.2f}"
        except (ValueError, TypeError, InvalidOperation):
            return "R$ 0,00"
    display_tax_amount.short_description = 'Valor do Imposto'
    
    # Ações personalizadas
    actions = ['mark_as_active', 'mark_as_inactive']
    
    def mark_as_active(self, request, queryset):
        """Marca faturas como ativas"""
        updated = queryset.update(is_active=True)
        self.message_user(
            request,
            f'{updated} fatura(s) marcada(s) como ativa(s).'
        )
    mark_as_active.short_description = 'Marcar como ativas'
    
    def mark_as_inactive(self, request, queryset):
        """Marca faturas como inativas"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'{updated} fatura(s) marcada(s) como inativa(s).'
        )
    mark_as_inactive.short_description = 'Marcar como inativas'