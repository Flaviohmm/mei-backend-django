from rest_framework import serializers
from .models import Invoice
from django.utils import timezone
import re

class InvoiceSerializer(serializers.ModelSerializer):
    total_value = serializers.ReadOnlyField()
    tax_amount = serializers.ReadOnlyField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'client_type', 'document', 'name',
            'email', 'phone', 'address', 'neighborhood', 'city', 'state',
            'zip_code', 'service_description', 'service_type', 'value',
            'tax', 'additional_info', 'payment_method', 'due_date',
            'issue_date', 'created_at', 'updated_at', 'is_active',
            'total_value', 'tax_amount'
        ]
        read_only_fields = ['id', 'invoice_number', 'created_at', 'updated_at']
    
    def validate_document(self, value):
        """Validação customizada para CPF/CNPJ"""
        # Remove caracteres especiais
        clean_doc = re.sub(r'[^\d]', '', value)
        
        if len(clean_doc) == 11:
            # Validação básica CPF
            if len(set(clean_doc)) == 1:
                raise serializers.ValidationError("CPF inválido")
        elif len(clean_doc) == 14:
            # Validação básica CNPJ
            if len(set(clean_doc)) == 1:
                raise serializers.ValidationError("CNPJ inválido")
        else:
            raise serializers.ValidationError("Documento deve ter 11 (CPF) ou 14 (CNPJ) dígitos")
        
        return value
    
    def validate_phone(self, value):
        """Validação para telefone brasileiro"""
        phone_pattern = r'^\(\d{2}\)\s\d{4,5}-\d{4}$'
        if not re.match(phone_pattern, value):
            raise serializers.ValidationError(
                "Telefone deve ter formato (XX) XXXXX-XXXX"
            )
        return value
    
    def validate_zip_code(self, value):
        """Validação para CEP brasileiro"""
        cep_pattern = r'^\d{5}-\d{3}$'
        if not re.match(cep_pattern, value):
            raise serializers.ValidationError(
                "CEP deve ter formato XXXXX-XXX"
            )
        return value
    
    def validate_value(self, value):
        """Validação para valor"""
        if value <= 0:
            raise serializers.ValidationError(
                "O valor deve ser maior que zero"
            )
        return value
    
    def validate_tax(self, value):
        """Validação para taxa de imposto"""
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "A taxa de imposto deve estar entre 0% e 100%"
            )
        return value
    
    def validate_due_date(self, value):
        """Validação para data de vencimento"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "A data de vencimento não pode ser anterior à data atual"
            )
        return value
    
    def validate(self, data):
        """Validações que dependem de múltiplos fields"""
        if data.get('due_date') and data.get('issue_date'):
            if data['due_date'] < data['issue_date']:
                raise serializers.ValidationError(
                    "A data de vencimento deve ser posterior à data de emissão"
                )
        return data

class InvoiceCreateSerializer(InvoiceSerializer):
    """Serializer específico para criação de notas fiscais"""
    
    def create(self, validated_data):
        # Se não foi fornecida data de emissão, usa a data atual
        if not validated_data.get('issue_date'):
            validated_data['issue_date'] = timezone.now().date()
        
        return super().create(validated_data)

class InvoiceListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listagem de notas fiscais"""
    total_value = serializers.ReadOnlyField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'name', 'service_type', 'value',
            'total_value', 'due_date', 'issue_date', 'created_at',
            'is_active'
        ]

class InvoiceUpdateSerializer(serializers.ModelSerializer):
    """Serializer para atualização de notas fiscais"""
    
    class Meta:
        model = Invoice
        fields = [
            'client_type', 'document', 'name', 'email', 'phone',
            'address', 'neighborhood', 'city', 'state', 'zip_code',
            'service_description', 'service_type', 'value', 'tax',
            'additional_info', 'payment_method', 'due_date', 'issue_date'
        ]
    
    def validate_due_date(self, value):
        """Validação para data de vencimento na atualização"""
        if value < timezone.now().date():
            raise serializers.ValidationError(
                "A data de vencimento não pode ser anterior à data atual"
            )
        return value