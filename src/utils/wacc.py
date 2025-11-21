

def calcular_wacc(patrimonio, deuda, costo_patrimonio, costo_deuda, tasa_impuesto):
    """Calcula el Costo Promedio Ponderado de Capital (WACC)"""
    total = patrimonio + deuda
    if total == 0:
        return 0
    wacc = (patrimonio/total * costo_patrimonio/100) + (deuda/total * costo_deuda/100 * (1 - tasa_impuesto/100))
    return wacc * 100