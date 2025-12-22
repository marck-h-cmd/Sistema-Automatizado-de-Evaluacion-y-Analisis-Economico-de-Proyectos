import numpy as np
from plotly.subplots import make_subplots
import plotly.graph_objects as go


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


# ======================================================
# FUNCIONES DE VISUALIZACIÓN Y GRÁFICOS
# ======================================================

def crear_grafico_evaluacion_completa(flujos, tasa_descuento):
    """
    Crea un gráfico completo con 4 subplots:
    1. Flujos de Caja por Periodo
    2. Flujos Acumulados
    3. Valor Presente de Flujos
    4. Sensibilidad VPN vs Tasa
    
    Returns:
        Figura Plotly con 4 subplots
    """
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Flujos de Caja por Periodo', 'Flujos Acumulados', 
                       'Valor Presente de Flujos', 'Análisis de Sensibilidad'),
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "scatter"}]]
    )
    
    # Flujos nominales
    periodos = list(range(len(flujos)))
    fig.add_trace(
        go.Bar(x=periodos, y=flujos, name="Flujo de Caja",
               marker_color=['red' if f < 0 else 'green' for f in flujos]),
        row=1, col=1
    )
    
    # Flujos acumulados
    flujos_acum = np.cumsum(flujos)
    fig.add_trace(
        go.Scatter(x=periodos, y=flujos_acum, mode='lines+markers', name="Acumulado",
                  line=dict(color='blue', width=3)),
        row=1, col=2
    )
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=2)
    
    # Valor presente de flujos
    vp_flujos = [flujo / (1 + tasa_descuento)**i for i, flujo in enumerate(flujos)]
    fig.add_trace(
        go.Bar(x=periodos, y=vp_flujos, name="Valor Presente",
               marker_color=['red' if f < 0 else 'lightgreen' for f in vp_flujos]),
        row=2, col=1
    )
    
    # Sensibilidad de tasa
    tasas = np.linspace(0, 30, 50)
    vpns = [calcular_vpn(flujos, t/100) for t in tasas]
    fig.add_trace(
        go.Scatter(x=tasas, y=vpns, mode='lines', name="VPN vs Tasa",
                  line=dict(color='purple', width=3)),
        row=2, col=2
    )
    fig.add_hline(y=0, line_dash="dash", line_color="red", row=2, col=2)
    fig.add_vline(x=tasa_descuento*100, line_dash="dash", line_color="green", row=2, col=2)
    
    fig.update_xaxes(title_text="Periodo", row=1, col=1)
    fig.update_xaxes(title_text="Periodo", row=1, col=2)
    fig.update_xaxes(title_text="Periodo", row=2, col=1)
    fig.update_xaxes(title_text="Tasa de Descuento (%)", row=2, col=2)
    
    fig.update_yaxes(title_text="Flujo ($)", row=1, col=1)
    fig.update_yaxes(title_text="Acumulado ($)", row=1, col=2)
    fig.update_yaxes(title_text="VP ($)", row=2, col=1)
    fig.update_yaxes(title_text="VPN ($)", row=2, col=2)
    
    fig.update_layout(height=700, showlegend=True)
    
    return fig

