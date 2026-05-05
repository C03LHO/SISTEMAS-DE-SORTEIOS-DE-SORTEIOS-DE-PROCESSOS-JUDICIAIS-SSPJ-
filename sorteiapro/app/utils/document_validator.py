"""
Validador de CPF e CNPJ conforme algoritmo oficial da Receita Federal.

CPF:  11 dígitos — valida os 2 dígitos verificadores
CNPJ: 14 dígitos — valida os 2 dígitos verificadores

Ambas as funções aceitam documentos com ou sem formatação
(pontos, traços e barras são removidos automaticamente).
"""

import re


# ─── CPF ──────────────────────────────────────────────────────────────────────

def _clean_document(doc: str) -> str:
    """Remove qualquer caractere que não seja dígito."""
    return re.sub(r"\D", "", doc)


def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF conforme o algoritmo oficial da Receita Federal.

    Algoritmo:
      1. Remove formatação e verifica 11 dígitos
      2. Rejeita sequências iguais (ex: 111.111.111-11)
      3. Calcula o 1º dígito verificador (pesos 10 a 2)
      4. Calcula o 2º dígito verificador (pesos 11 a 2)

    Retorna True se válido, False caso contrário.
    """
    cpf = _clean_document(cpf)

    # Deve ter exatamente 11 dígitos
    if len(cpf) != 11:
        return False

    # Rejeita sequências repetidas (ex: 00000000000, 11111111111...)
    if cpf == cpf[0] * 11:
        return False

    # ── Cálculo do 1º dígito verificador ──────────────────────────────────────
    # Soma os 9 primeiros dígitos, cada um multiplicado pelo seu peso (10 a 2)
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    resto = (soma * 10) % 11
    primeiro_digito = 0 if resto >= 10 else resto

    if primeiro_digito != int(cpf[9]):
        return False

    # ── Cálculo do 2º dígito verificador ──────────────────────────────────────
    # Soma os 10 primeiros dígitos, cada um multiplicado pelo seu peso (11 a 2)
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    resto = (soma * 10) % 11
    segundo_digito = 0 if resto >= 10 else resto

    return segundo_digito == int(cpf[10])


# ─── CNPJ ─────────────────────────────────────────────────────────────────────

def validate_cnpj(cnpj: str) -> bool:
    """
    Valida um CNPJ conforme o algoritmo oficial da Receita Federal.

    Algoritmo:
      1. Remove formatação e verifica 14 dígitos
      2. Rejeita sequências iguais (ex: 11.111.111/1111-11)
      3. Calcula o 1º dígito verificador (pesos 5,4,3,2,9,8,7,6,5,4,3,2)
      4. Calcula o 2º dígito verificador (pesos 6,5,4,3,2,9,8,7,6,5,4,3,2)

    Retorna True se válido, False caso contrário.
    """
    cnpj = _clean_document(cnpj)

    # Deve ter exatamente 14 dígitos
    if len(cnpj) != 14:
        return False

    # Rejeita sequências repetidas
    if cnpj == cnpj[0] * 14:
        return False

    # ── Cálculo do 1º dígito verificador ──────────────────────────────────────
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    primeiro_digito = 0 if resto < 2 else 11 - resto

    if primeiro_digito != int(cnpj[12]):
        return False

    # ── Cálculo do 2º dígito verificador ──────────────────────────────────────
    pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    segundo_digito = 0 if resto < 2 else 11 - resto

    return segundo_digito == int(cnpj[13])


def validate_document(document: str, document_type: str) -> bool:
    """
    Valida um documento de acordo com o tipo informado.

    Args:
        document: número do documento (com ou sem formatação)
        document_type: "CPF" ou "CNPJ"

    Returns:
        True se o documento for válido para o tipo informado.
    """
    if document_type == "CPF":
        return validate_cpf(document)
    elif document_type == "CNPJ":
        return validate_cnpj(document)
    return False
