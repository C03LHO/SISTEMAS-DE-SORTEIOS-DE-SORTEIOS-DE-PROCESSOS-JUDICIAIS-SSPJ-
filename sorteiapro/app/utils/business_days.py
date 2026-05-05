"""
Utilitário para cálculo de dias úteis.

Regra de negócio:
  - O sorteio ocorre no próximo dia útil às 10:00
  - Se a solicitação chegar num dia útil ANTES das 10:00, o sorteio é HOJE às 10:00
  - Sábado (5) e Domingo (6) são pulados
  - Feriados não são considerados nesta versão
"""

from datetime import date, datetime, timedelta


def next_business_day(from_date: datetime) -> datetime:
    """
    Calcula a data/hora do próximo sorteio (dia útil às 10:00).

    Exemplos:
      - Segunda 08:00 → Segunda 10:00 (mesmo dia, antes das 10h)
      - Segunda 11:00 → Terça 10:00 (passou das 10h, avança para amanhã)
      - Sexta 15:00   → Segunda 10:00 (pula sábado e domingo)
      - Sábado 09:00  → Segunda 10:00 (fim de semana sempre avança)

    Args:
        from_date: data/hora de referência (normalmente datetime.utcnow())

    Returns:
        datetime com o próximo dia útil às 10:00:00
    """
    d = from_date.date()

    # Se hoje é dia útil (seg–sex) E ainda não passou das 10:00 → sorteio hoje
    if d.weekday() < 5 and from_date.hour < 10:
        return datetime(d.year, d.month, d.day, 10, 0, 0)

    # Caso contrário, avança para o dia seguinte e pula fins de semana
    d += timedelta(days=1)
    while d.weekday() >= 5:  # 5 = sábado, 6 = domingo
        d += timedelta(days=1)

    return datetime(d.year, d.month, d.day, 10, 0, 0)


def is_business_day(d: date) -> bool:
    """Retorna True se a data for um dia útil (segunda a sexta)."""
    return d.weekday() < 5
