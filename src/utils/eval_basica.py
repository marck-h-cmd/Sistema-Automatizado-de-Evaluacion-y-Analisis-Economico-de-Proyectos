import numpy as np

# Funciones de cálculo financiero
def calcular_vpn(flujos, tasa_descuento):
    """Calcula el Valor Presente Neto"""
    vpn = sum([flujo / (1 + tasa_descuento)**i for i, flujo in enumerate(flujos)])
    return vpn


def calcular_tir(flujos):
    """Calcula la Tasa Interna de Retorno usando método de Newton-Raphson"""
    try:
        return np.irr(flujos) * 100
    except:
        # Método alternativo si np.irr no está disponible
        def npv_func(rate):
            return sum([flujo / (1 + rate)**i for i, flujo in enumerate(flujos)])
        
        def npv_derivative(rate):
            return sum([-i * flujo / (1 + rate)**(i+1) for i, flujo in enumerate(flujos)])
        
        rate = 0.1
        for _ in range(100):
            npv_val = npv_func(rate)
            if abs(npv_val) < 1e-6:
                return rate * 100
            rate = rate - npv_val / npv_derivative(rate)
            if rate < -0.99:
                return None
        return rate * 100 if rate > -0.99 else None
    
def calcular_bc(flujos, tasa_descuento):
    """Calcula la Relación Beneficio/Costo"""
    inversion_inicial = abs(flujos[0])
    beneficios_vp = sum([max(flujo, 0) / (1 + tasa_descuento)**i for i, flujo in enumerate(flujos[1:])])
    return beneficios_vp / inversion_inicial if inversion_inicial > 0 else 0


def calcular_periodo_recuperacion(flujos):
    """Calcula el periodo de recuperación de la inversión"""
    acumulado = 0
    for i, flujo in enumerate(flujos):
        acumulado += flujo
        if acumulado >= 0:
            return i
    return len(flujos)
