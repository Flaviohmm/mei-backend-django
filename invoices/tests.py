from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from decimal import Decimal
from datetime import date, timedelta
from .models import Invoice

# Get the custom user model
User = get_user_model()

class InvoiceModelTest(TestCase):
    def setUp(self):
        self.invoice_data = {
            'client_type': 'pf',
            'document': '123.456.789-00',
            'name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '(11) 99999-1234',
            'address': 'Rua Teste, 123',
            'neighborhood': 'Centro',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01234-567',
            'service_description': 'Desenvolvimento de sistema',
            'service_type': 'dev',
            'value': Decimal('1000.00'),
            'tax': Decimal('15.00'),
            'payment_method': 'pix',
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30),
        }
    
    def test_invoice_creation(self):
        """Test invoice creation"""
        invoice = Invoice.objects.create(**self.invoice_data)
        self.assertEqual(invoice.name, 'João Silva')
        self.assertEqual(invoice.value, Decimal('1000.00'))
        self.assertIsNotNone(invoice.invoice_number)
        self.assertTrue(invoice.is_active)
    
    def test_invoice_total_value_calculation(self):
        """Test total value calculation"""
        invoice = Invoice.objects.create(**self.invoice_data)
        expected_total = Decimal('1150.00')  # 1000 + 15% tax
        self.assertEqual(invoice.total_value, expected_total)
    
    def test_invoice_tax_amount_calculation(self):
        """Test tax amount calculation"""
        invoice = Invoice.objects.create(**self.invoice_data)
        expected_tax = Decimal('150.00')  # 15% of 1000
        self.assertEqual(invoice.tax_amount, expected_tax)
    
    def test_invoice_number_generation(self):
        """Test automatic invoice number generation"""
        invoice1 = Invoice.objects.create(**self.invoice_data)
        invoice2 = Invoice.objects.create(**self.invoice_data)
        
        self.assertNotEqual(invoice1.invoice_number, invoice2.invoice_number)
        self.assertTrue(invoice1.invoice_number.startswith('2025'))
        self.assertTrue(invoice2.invoice_number.startswith('2025'))

class InvoiceAPITest(APITestCase):
    def setUp(self):
        # Use the custom user model
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)
        
        self.invoice_data = {
            'client_type': 'pf',
            'document': '123.456.789-00',
            'name': 'João Silva',
            'email': 'joao@email.com',
            'phone': '(11) 99999-1234',
            'address': 'Rua Teste, 123',
            'neighborhood': 'Centro',
            'city': 'São Paulo',
            'state': 'SP',
            'zip_code': '01234-567',
            'service_description': 'Desenvolvimento de sistema',
            'service_type': 'dev',
            'value': '1000.00',
            'tax': '15.00',
            'payment_method': 'pix',
            'issue_date': date.today().isoformat(),
            'due_date': (date.today() + timedelta(days=30)).isoformat(),
        }
    
    def test_create_invoice(self):
        """Test invoice creation via API"""
        url = reverse('invoice-list')
        response = self.client.post(url, self.invoice_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Invoice.objects.count(), 1)
        self.assertEqual(response.data['name'], 'João Silva')
        self.assertIsNotNone(response.data['invoice_number'])
    
    def test_list_invoices(self):
        """Test invoice listing via API"""
        Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)
    
    def test_get_invoice_detail(self):
        """Test invoice detail retrieval"""
        invoice = Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-detail', kwargs={'pk': invoice.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'João Silva')
    
    def test_update_invoice(self):
        """Test invoice update via API"""
        invoice = Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-detail', kwargs={'pk': invoice.pk})
        updated_data = self.invoice_data.copy()
        updated_data['name'] = 'João Silva Santos'
        
        response = self.client.put(url, updated_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        invoice.refresh_from_db()
        self.assertEqual(invoice.name, 'João Silva Santos')
    
    def test_delete_invoice(self):
        """Test invoice deletion via API"""
        invoice = Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-detail', kwargs={'pk': invoice.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Invoice.objects.count(), 0)
    
    def test_invoice_statistics(self):
        """Test invoice statistics endpoint"""
        Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-statistics')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_invoices', response.data)
        self.assertIn('active_invoices', response.data)
        self.assertIn('total_value', response.data)
    
    def test_filter_invoices_by_client_type(self):
        """Test filtering invoices by client type"""
        Invoice.objects.create(**{
            k: v for k, v in self.invoice_data.items() 
            if k not in ['issue_date', 'due_date']
        } | {
            'issue_date': date.today(),
            'due_date': date.today() + timedelta(days=30)
        })
        
        url = reverse('invoice-list')
        response = self.client.get(url, {'client_type': 'pf'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Handle both paginated and non-paginated responses
        if isinstance(response.data, dict) and 'results' in response.data:
            self.assertEqual(len(response.data['results']), 1)
        else:
            self.assertEqual(len(response.data), 1)
    
    def test_unauthenticated_access(self):
        """Test that unauthenticated users cannot access the API"""
        self.client.credentials()  # Remove authentication
        url = reverse('invoice-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)