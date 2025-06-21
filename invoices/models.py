from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from decimal import Decimal, InvalidOperation
import uuid

class Invoice(models.Model):
    CLIENT_TYPE_CHOICES = [
        ('pf', 'Pessoa Física'),
        ('pj', 'Pessoa Jurídica'),
    ]
    
    SERVICE_TYPE_CHOICES = [
        ('dev', 'Desenvolvimento de Software'),
        ('design', 'Design Gráfico'),
        ('consulting', 'Consultoria'),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('pix', 'PIX'),
        ('credit', 'Cartão de Crédito'),
        ('transfer', 'Transferência Bancária'),
        ('cash', 'Dinheiro'),
    ]
    
    STATE_CHOICES = [
        ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'), ('AM', 'Amazonas'),
        ('BA', 'Bahia'), ('CE', 'Ceará'), ('DF', 'Distrito Federal'),
        ('ES', 'Espírito Santo'), ('GO', 'Goiás'), ('MA', 'Maranhão'),
        ('MT', 'Mato Grosso'), ('MS', 'Mato Grosso do Sul'),
        ('MG', 'Minas Gerais'), ('PA', 'Pará'), ('PB', 'Paraíba'),
        ('PR', 'Paraná'), ('PE', 'Pernambuco'), ('PI', 'Piauí'),
        ('RJ', 'Rio de Janeiro'), ('RN', 'Rio Grande do Norte'),
        ('RS', 'Rio Grande do Sul'), ('RO', 'Rondônia'), ('RR', 'Roraima'),
        ('SC', 'Santa Catarina'), ('SP', 'São Paulo'), ('SE', 'Sergipe'),
        ('TO', 'Tocantins'),
    ]
    
    # Identificação
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=50, unique=True, blank=True)
    
    # Dados do Cliente
    client_type = models.CharField(
        max_length=2, 
        choices=CLIENT_TYPE_CHOICES,
        verbose_name="Tipo de Cliente"
    )
    document = models.CharField(
        max_length=18,
        validators=[
            RegexValidator(
                regex=r'^\d{3}\.\d{3}\.\d{3}-\d{2}$|^\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}$|\d{11}|\d{14}',
                message="CPF deve ter formato XXX.XXX.XXX-XX ou CNPJ XX.XXX.XXX/XXXX-XX"
            )
        ],
        verbose_name="CPF/CNPJ"
    )
    name = models.CharField(max_length=200, verbose_name="Nome/Razão Social")
    email = models.EmailField(validators=[EmailValidator()], verbose_name="Email")
    phone = models.CharField(
        max_length=15,
        validators=[
            RegexValidator(
                regex=r'^\(\d{2}\)\s\d{4,5}-\d{4}$',
                message="Telefone deve ter formato (XX) XXXXX-XXXX"
            )
        ],
        verbose_name="Telefone"
    )
    
    # Endereço
    address = models.CharField(max_length=200, verbose_name="Endereço")
    neighborhood = models.CharField(max_length=100, verbose_name="Bairro")
    city = models.CharField(max_length=100, verbose_name="Cidade")
    state = models.CharField(
        max_length=2, 
        choices=STATE_CHOICES,
        verbose_name="Estado"
    )
    zip_code = models.CharField(
        max_length=9,
        validators=[
            RegexValidator(
                regex=r'^\d{5}-\d{3}$',
                message="CEP deve ter formato XXXXX-XXX"
            )
        ],
        verbose_name="CEP"
    )
    
    # Serviços
    service_description = models.TextField(verbose_name="Descrição do Serviço")
    service_type = models.CharField(
        max_length=20,
        choices=SERVICE_TYPE_CHOICES,
        verbose_name="Tipo de Serviço"
    )
    value = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('0.00'), 
        verbose_name="Valor"
    )
    tax = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        null=True,
        blank=True,
        default=Decimal('0.00'),
        verbose_name="Imposto (%)"
    )
    
    # Informações Adicionais
    additional_info = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Informações Adicionais"
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Forma de Pagamento"
    )
    due_date = models.DateField(verbose_name="Data de Vencimento")
    issue_date = models.DateField(verbose_name="Data de Emissão")
    
    # Campos de Controle
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'invoices'
        verbose_name = 'Nota Fiscal'
        verbose_name_plural = 'Notas Fiscais'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"NF {self.invoice_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Gerar número da nota fiscal automaticamente
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=timezone.now().strftime('%Y')
            ).order_by('invoice_number').last()
            
            if last_invoice:
                last_number = int(last_invoice.invoice_number.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1
                
            self.invoice_number = f"{timezone.now().strftime('%Y')}-{new_number:06d}"
        
        super().save(*args, **kwargs)
    
    @property
    def total_value(self):
        """Calcula o valor total com impostos"""
        # Verifica se os valores não são None antes de calcular
        if self.value is None or self.tax is None:
            return Decimal('0.00')
        
        try: 
            # Garantir que value e tax são Decimal
            value = Decimal(str(self.value)) if not isinstance(self.value, Decimal) else self.value
            tax = Decimal(str(self.tax)) if not isinstance(self.tax, Decimal) else self.tax
            
            tax_amount = value * tax
            return value + tax_amount
        except (TypeError, ValueError, InvalidOperation):
            return Decimal('0.00')

    @property
    def tax_amount(self):
        """Calcula o valor do imposto"""
        # Tratamento seguro para valores None
        if self.value is None or self.tax is None:
            return Decimal('0.00')
        
        try:
            # Garantir que value e tax são Decimal
            value = Decimal(str(self.value)) if not isinstance(self.value, Decimal) else self.value
            tax = Decimal(str(self.tax)) if not isinstance(self.tax, Decimal) else self.tax
            
            return value * tax
        except (TypeError, ValueError, InvalidOperation):
            return Decimal('0.00')
