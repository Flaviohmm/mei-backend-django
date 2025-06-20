from django.core.exceptions import ValidationError
import re

def validate_cpf(cpf):
    """Validação de CPF"""
    cpf = re.sub(r'[^\d]', '', cpf)
    
    if len(cpf) != 11 or len(set(cpf)) == 1:
        return False
    
    # Validação dos dígitos verificadores
    for i in range(9, 11):
        value = sum((int(cpf[num]) * ((i+1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(cpf[i]):
            return False
    return True

def validate_cnpj(cnpj):
    """Validação de CNPJ"""
    cnpj = re.sub(r'[^\d]', '', cnpj)
    
    if len(cnpj) != 14 or len(set(cnpj)) == 1:
        return False
    
    # Validação dos dígitos verificadores
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    
    def calculate_digit(cnpj_digits, weights):
        total = sum(int(digit) * weight for digit, weight in zip(cnpj_digits, weights))
        remainder = total % 11
        return 0 if remainder < 2 else 11 - remainder
    
    digit1 = calculate_digit(cnpj[:12], weights1)
    digit2 = calculate_digit(cnpj[:13], weights2)
    
    return int(cnpj[12]) == digit1 and int(cnpj[13]) == digit2

def format_currency(value):
    """Formata valor monetário para Real brasileiro"""
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def format_document(document):
    """Formata CPF/CNPJ para exibição"""
    clean_doc = re.sub(r'[^\d]', '', document)
    
    if len(clean_doc) == 11:  # CPF
        return f"{clean_doc[:3]}.{clean_doc[3:6]}.{clean_doc[6:9]}-{clean_doc[9:]}"
    elif len(clean_doc) == 14:  # CNPJ
        return f"{clean_doc[:2]}.{clean_doc[2:5]}.{clean_doc[5:8]}/{clean_doc[8:12]}-{clean_doc[12:]}"
    
    return document
