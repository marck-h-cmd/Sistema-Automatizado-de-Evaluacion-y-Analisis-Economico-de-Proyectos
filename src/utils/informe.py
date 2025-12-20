from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, white, green, red, orange
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import io
import pandas as pd
from datetime import datetime
import base64
from plotly import graph_objects as go
import plotly.io as pio
import numpy as np

def crear_informe_pdf(proyecto_data, fecha_analisis, analista, buffer=None):
    """
    Genera un informe PDF completo del proyecto con análisis, gráficas y resultados.
    
    Args:
        proyecto_data: Dictionary con datos del proyecto
        fecha_analisis: datetime objeto
        analista: Nombre del analista
        buffer: BytesIO objeto para guardar el PDF. Si es None, se crea uno nuevo.
    
    Returns:
        BytesIO objeto con el PDF generado
    """
    if buffer is None:
        buffer = io.BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )
    
    # Estilos
    styles = getSampleStyleSheet()
    # Estilos adicionales
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=Color(0.31, 0.31, 0.31),  # RGB normalizado (80/255)
        spaceAfter=6,
        alignment=TA_LEFT,
        fontName='Helvetica',
        leading=14  # Espaciado entre líneas
    )

    caption_style = ParagraphStyle(
        'Caption',
        parent=styles['Normal'],
        fontSize=8,
        textColor=Color(0.35, 0.35, 0.35),  # RGB normalizado (90/255)
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica',
        leading=10
    )
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=Color(102, 126, 234),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=Color(102, 126, 234),
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    normal_style = styles['Normal']
    normal_style.fontSize = 10
    
    # Lista de elementos para el PDF
    elements = []
    
    # ============ PORTADA ============
    elements.append(Spacer(1, 0.3*inch))
    
    title = Paragraph(f"<b>INFORME DE EVALUACIÓN</b>", title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.1*inch))
    
    subtitle = Paragraph(f"<b>{proyecto_data['nombre']}</b>", heading_style)
    elements.append(subtitle)
    elements.append(Spacer(1, 0.1*inch))
    
    # Información general
    info_data = [
        ['Fecha de Análisis:', fecha_analisis.strftime('%d/%m/%Y')],
        ['Analista:', analista],
        ['Periodo de Evaluación:', f"{proyecto_data['periodos']} años"],
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONT', (0, 0), (0, -1), 'Helvetica-Bold', 10),
        ('FONT', (1, 0), (1, -1), 'Helvetica', 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    
    elements.append(info_table)
    elements.append(Spacer(1, 0.3*inch))
    
    # ============ RESUMEN EJECUTIVO ============
    elements.append(Paragraph("<b>📌 RESUMEN EJECUTIVO</b>", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    vpn = proyecto_data['vpn']
    tir = proyecto_data['tir']
    bc = proyecto_data['bc']
    
    decision = "ACEPTAR" if vpn > 0 and tir and tir > proyecto_data['tmar'] and bc > 1 else \
               "RECHAZAR" if vpn < 0 else "REVISAR"
    
    # Recomendación
    decision_text = f"<b>RECOMENDACIÓN: {decision} EL PROYECTO</b>"
    elements.append(Paragraph(decision_text, ParagraphStyle(
        'Decision',
        parent=styles['Normal'],
        fontSize=12,
        textColor=white,
        alignment=TA_CENTER,
        backColor=Color(76, 175, 80) if decision == "ACEPTAR" else Color(244, 67, 54) if decision == "RECHAZAR" else Color(255, 152, 0),
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # ============ INDICADORES PRINCIPALES ============
    elements.append(Paragraph("<b>📊 INDICADORES FINANCIEROS PRINCIPALES</b>", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "Tabla resumen de los indicadores clave para evaluar la viabilidad del proyecto: inversión requerida, valor presente neto (VPN), tasa interna de retorno (TIR), relación beneficio-costo y tasa de descuento aplicada. Estos indicadores determinan si el proyecto es financieramente viable.",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))
    
    indicators_data = [
        ['Indicador', 'Valor', 'Interpretación'],
        ['Inversión Total', f"${proyecto_data['inversion']:,.2f}", 'Capital requerido'],
        ['VPN', f"${vpn:,.2f}", '✓ Positivo' if vpn > 0 else '✗ Negativo'],
        ['TIR', f"{tir:.2f}%" if tir else "N/A", f"vs TMAR: {proyecto_data['tmar']}%"],
        ['Relación B/C', f"{bc:.2f}", '✓ Rentable (>1)' if bc > 1 else '✗ No Rentable (<1)'],
        ['Tasa de Descuento', f"{proyecto_data['tasa_descuento']}%", 'WACC'],
    ]
    
    indicators_table = Table(indicators_data, colWidths=[2*inch, 2*inch, 2*inch])
    indicators_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), Color(102, 126, 234)),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), Color(240, 240, 240)),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, Color(245, 245, 245)]),
    ]))
    
    elements.append(indicators_table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Tabla 1: <b>Indicadores Financieros Clave.</b> Resumen de Inversión, VPN, TIR, B/C y WACC con interpretación inmediata. El VPN positivo y TIR superior a TMAR son señales de viabilidad.", caption_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # ============ GRÁFICA DE FLUJOS DE CAJA ============
    elements.append(PageBreak())
    elements.append(Paragraph("<b>📈 ANÁLISIS DETALLADO - FLUJOS DE CAJA</b>", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "Esta sección presenta un análisis detallado de todos los flujos de caja del proyecto. La gráfica muestra los flujos nominales (invertidos vs generados) y el impacto del descuento financiero. La tabla desglosa periodo a periodo el comportamiento acumulado y el valor presente, permitiendo identificar el punto de recuperación de la inversión.",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))
    
    # Crear gráfica de flujos
    try:
        fig_flujos = _crear_grafica_flujos(proyecto_data)
        img_flujos = _plotly_a_imagen(fig_flujos)
        if img_flujos:
            elements.append(img_flujos)
            elements.append(Spacer(1, 0.12*inch))
            elements.append(Paragraph("Figura 1: <b>Comparación de Flujos Nominales vs Valor Presente.</b> Las barras muestran flujos nominales (rojo=inversión, azul=generación). La línea verde representa el valor presente descontado, mostrando cómo disminuye el valor temporal del dinero.", caption_style))
            elements.append(Spacer(1, 0.12*inch))
    except Exception as e:
        elements.append(Paragraph(f"<i>Nota: No se pudo generar la gráfica de flujos. ({str(e)})</i>", styles['Normal']))
        elements.append(Spacer(1, 0.1*inch))
    
    # Tabla de flujos
    elements.append(Paragraph(
        "Desglose detallado por periodo: muestra el Flujo de Caja anual, Flujo Acumulado (suma acumulativa para identificar payback), Valor Presente individual (flujo descontado) y VP Acumulado (suma de VPs que indica el VPN progresivo). El punto donde VP Acumulado se vuelve positivo marca la recuperación de la inversión.",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))
    periodos = list(range(len(proyecto_data['flujos'])))
    tasa = proyecto_data['tasa_descuento'] / 100
    
    flujos_data = [['Periodo', 'Flujo de Caja', 'Flujo Acum.', 'Valor Presente', 'VP Acumulado']]
    
    for i in periodos:
        flujo_acum = sum(proyecto_data['flujos'][:i+1])
        vp = proyecto_data['flujos'][i] / (1 + tasa)**i
        vp_acum = sum([proyecto_data['flujos'][j] / (1 + tasa)**j for j in range(i+1)])
        
        flujos_data.append([
            str(i),
            f"${proyecto_data['flujos'][i]:,.2f}",
            f"${flujo_acum:,.2f}",
            f"${vp:,.2f}",
            f"${vp_acum:,.2f}"
        ])
    
    flujos_table = Table(flujos_data, colWidths=[0.8*inch, 1.4*inch, 1.4*inch, 1.4*inch, 1.4*inch])
    flujos_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), Color(102, 126, 234)),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, Color(245, 245, 245)]),
    ]))
    
    elements.append(flujos_table)
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph("Tabla 2: <b>Flujos de Caja Detallados.</b> Desglose por periodo (FC anual, FC Acumulado, VP individual, VP Acumulado). Cuando VP Acumulado sea positivo, se habrá recuperado la inversión inicial.", caption_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # ============ ANÁLISIS DE RIESGO ============
    elements.append(PageBreak())
    elements.append(Paragraph("<b>⚠️ ANÁLISIS DE RIESGO Y SENSIBILIDAD</b>", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    elements.append(Paragraph(
        "Esta sección presenta escenarios de estrés y un análisis de sensibilidad sobre los indicadores principales. Primero se muestran los escenarios para entender el comportamiento bajo distintas condiciones.",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))

    # Escenarios de estrés (poner antes para contexto)
    elements.append(Paragraph("<b>🎯 Escenarios de Estrés</b>", ParagraphStyle(
        'Subheading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=Color(102, 126, 234),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )))
    elements.append(Paragraph(
        "Simulaciones que reducen o aumentan los flujos de caja futuros para evaluar cómo reacciona el proyecto ante cambios en las condiciones del mercado. Escenarios: Pesimista (70% de los flujos), Moderado (85%) u Optimista (115%).",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))

    escenarios_estres = {
        'Pesimista': 0.7,
        'Moderado': 0.85,
        'Optimista': 1.15
    }

    estres_data = [['Escenario', 'Factor', 'VPN', 'TIR', 'Estado']]

    for nombre, factor in escenarios_estres.items():
        flujos_mod = [proyecto_data['flujos'][0]] + [f * factor for f in proyecto_data['flujos'][1:]]
        from src.utils.eval_basica import calcular_vpn, calcular_tir
        vpn_mod = calcular_vpn(flujos_mod, tasa)
        tir_mod = calcular_tir(flujos_mod)
        estado = '✓' if vpn_mod > 0 else '✗'

        estres_data.append([
            nombre,
            f"{factor*100:.0f}%",
            f"${vpn_mod:,.2f}",
            f"{tir_mod:.2f}%" if tir_mod else "N/A",
            estado
        ])

    estres_table = Table(estres_data, colWidths=[1.2*inch, 1.2*inch, 1.5*inch, 1.2*inch, 0.8*inch])
    estres_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), Color(102, 126, 234)),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, Color(245, 245, 245)]),
    ]))

    elements.append(estres_table)
    elements.append(Spacer(1, 0.12*inch))
    elements.append(Paragraph("Tabla 3: <b>Escenarios de Estrés.</b> Evaluación del proyecto bajo tres escenarios (Pesimista 70%, Moderado 85%, Optimista 115%). Muestra VPN y TIR resultantes. El símbolo ✓ indica viabilidad; ✗ indica rechazo. Determina la robustez del proyecto ante variaciones.", caption_style))
    elements.append(Spacer(1, 0.18*inch))

    # Factores de riesgo - sensibilidad
    elements.append(Paragraph("<b>Análisis de Sensibilidad</b>", ParagraphStyle(
        'Subheading2',
        parent=styles['Normal'],
        fontSize=11,
        textColor=Color(102, 126, 234),
        spaceAfter=6,
        fontName='Helvetica-Bold'
    )))
    elements.append(Paragraph(
        "Identifica qué variables tienen mayor impacto en el VPN del proyecto. Evalúa el cambio en VPN cuando varían: Flujos de Caja (-20%), Tasa de Descuento (+20%) e Inversión Inicial (+20%). Útil para enfocar el monitoreo en las variables críticas.",
        subtitle_style
    ))
    elements.append(Spacer(1, 0.05*inch))

    variables_riesgo = ['Flujos de Caja', 'Tasa de Descuento', 'Inversión Inicial']
    impactos = []

    for var in variables_riesgo:
        if var == "Flujos de Caja":
            flujos_mod = [proyecto_data['flujos'][0]] + [f * 0.8 for f in proyecto_data['flujos'][1:]]
            from src.utils.eval_basica import calcular_vpn
            vpn_modificado = calcular_vpn(flujos_mod, tasa)
        elif var == "Tasa de Descuento":
            from src.utils.eval_basica import calcular_vpn
            vpn_modificado = calcular_vpn(proyecto_data['flujos'], (proyecto_data['tasa_descuento'] * 1.2) / 100)
        else:
            flujos_mod = [proyecto_data['flujos'][0] * 1.2] + proyecto_data['flujos'][1:]
            from src.utils.eval_basica import calcular_vpn
            vpn_modificado = calcular_vpn(flujos_mod, tasa)

        impacto = abs(vpn_modificado - vpn)
        impactos.append(impacto)

    riesgo_data = [['Variable', 'Impacto en VPN', 'Nivel de Riesgo']]
    for var, imp in zip(variables_riesgo, impactos):
        nivel = '🔴 ALTO' if imp > abs(vpn) * 0.5 else '🟡 MEDIO' if imp > abs(vpn) * 0.2 else '🟢 BAJO'
        riesgo_data.append([var, f"${imp:,.2f}", nivel])

    riesgo_table = Table(riesgo_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
    riesgo_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), Color(102, 126, 234)),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, Color(245, 245, 245)]),
    ]))

    elements.append(riesgo_table)
    elements.append(Spacer(1, 0.12*inch))
    elements.append(Paragraph("Tabla 4: <b>Análisis de Sensibilidad.</b> Muestra el impacto en VPN al variar Flujos de Caja, Tasa de Descuento e Inversión Inicial. Nivel de Riesgo (ALTO/MEDIO/BAJO) indica qué variable requiere mayor control. Las críticas (ALTO) deben monitorearse constantemente durante la ejecución.", caption_style))
    elements.append(Spacer(1, 0.2*inch))
    
    # ============ CONCLUSIONES Y RECOMENDACIONES ============
    elements.append(PageBreak())
    elements.append(Paragraph("<b>📋 CONCLUSIONES Y RECOMENDACIONES</b>", heading_style))
    elements.append(Spacer(1, 0.1*inch))
    
    # Fortalezas
    elements.append(Paragraph("<b>✅ Fortalezas del Proyecto</b>", ParagraphStyle(
        'Subheading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=green,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )))
    
    fortalezas = []
    if vpn > 0:
        fortalezas.append(f"VPN positivo de ${vpn:,.2f}, que indica creación de valor económico")
    if tir and tir > proyecto_data['tmar']:
        fortalezas.append(f"TIR de {tir:.2f}% supera la tasa mínima requerida de {proyecto_data['tmar']}%")
    if bc > 1:
        fortalezas.append(f"Relación Beneficio/Costo de {bc:.2f} demuestra rentabilidad del proyecto")
    if proyecto_data.get('pr', 999) < proyecto_data['periodos']:
        fortalezas.append(f"Recuperación de inversión en {proyecto_data.get('pr', 'N/A')} años")
    
    for fortaleza in fortalezas:
        elements.append(Paragraph(f"• {fortaleza}", styles['Normal']))
    
    elements.append(Spacer(1, 0.1*inch))
    
    # Debilidades
    elements.append(Paragraph("<b>⚠️ Aspectos a Considerar</b>", ParagraphStyle(
        'Subheading',
        parent=styles['Normal'],
        fontSize=11,
        textColor=red,
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )))
    
    debilidades = []
    if vpn < proyecto_data['inversion'] * 0.2:
        debilidades.append("VPN relativamente bajo respecto a la inversión realizada")
    if tir and abs(tir - proyecto_data['tmar']) < 5:
        debilidades.append("Margen limitado entre TIR y TMAR (menos de 5 puntos porcentuales)")
    if proyecto_data.get('pr', 0) > proyecto_data['periodos'] / 2:
        debilidades.append("Periodo de recuperación largo comparado con la vida útil del proyecto")
    
    if debilidades:
        for debilidad in debilidades:
            elements.append(Paragraph(f"• {debilidad}", styles['Normal']))
    else:
        elements.append(Paragraph("No se identificaron debilidades significativas en los indicadores principales", styles['Normal']))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Recomendación Final
    elements.append(Paragraph("<b>🎯 Recomendación Final</b>", heading_style))
    
    if decision == "ACEPTAR":
        recom_text = f"""
        <b>SE RECOMIENDA ACEPTAR EL PROYECTO</b><br/><br/>
        El proyecto {proyecto_data['nombre']} presenta indicadores financieros favorables:
        <br/>• VPN positivo: ${vpn:,.2f}
        <br/>• TIR superior a TMAR: {tir:.2f}% vs {proyecto_data['tmar']}%
        <br/>• Relación B/C rentable: {bc:.2f}
        <br/><br/>
        El proyecto genera valor económico y cumple con los criterios de rentabilidad establecidos.
        Se sugiere proceder con la implementación bajo monitoreo continuo de las variables críticas.
        """
    elif decision == "RECHAZAR":
        recom_text = f"""
        <b>SE RECOMIENDA RECHAZAR EL PROYECTO</b><br/><br/>
        El proyecto {proyecto_data['nombre']} no cumple con los criterios mínimos de rentabilidad:
        <br/>• VPN: ${vpn:,.2f}
        <br/>• TIR: {tir:.2f}% {'(inferior a TMAR)' if tir and tir < proyecto_data['tmar'] else ''}
        <br/>• B/C: {bc:.2f}
        <br/><br/>
        El proyecto no genera valor suficiente o no supera el costo de oportunidad del capital.
        Se recomienda buscar alternativas de inversión más rentables.
        """
    else:
        recom_text = f"""
        <b>SE RECOMIENDA REVISAR EL PROYECTO</b><br/><br/>
        El proyecto {proyecto_data['nombre']} presenta indicadores mixtos que requieren análisis adicional:
        <br/>• VPN: ${vpn:,.2f}
        <br/>• TIR: {tir:.2f}%
        <br/>• B/C: {bc:.2f}
        <br/><br/>
        Se sugiere:
        <br/>1. Realizar análisis de sensibilidad más profundo
        <br/>2. Evaluar opciones de mejora en los flujos de caja
        <br/>3. Considerar escenarios alternativos de implementación
        <br/>4. Revisar supuestos y proyecciones
        """
    
    elements.append(Paragraph(recom_text, styles['Normal']))
    
    # ============ PIE DE PÁGINA ============
    elements.append(Spacer(1, 0.3*inch))
    elements.append(Paragraph(
        f"Informe generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')} | Analista: {analista}",
        ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=Color(128, 128, 128),
            alignment=TA_CENTER
        )
    ))
    
    # Construir PDF
    doc.build(elements)
    buffer.seek(0)
    
    return buffer


def _crear_grafica_flujos(proyecto_data):
    """Crea una gráfica de flujos de caja."""
    periodos = list(range(len(proyecto_data['flujos'])))
    tasa = proyecto_data['tasa_descuento'] / 100
    vp_flujos = [proyecto_data['flujos'][i] / (1 + tasa)**i for i in periodos]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=periodos,
        y=proyecto_data['flujos'],
        name='Flujo Nominal',
        marker_color=['red' if f < 0 else 'lightblue' for f in proyecto_data['flujos']],
        showlegend=True
    ))
    
    fig.add_trace(go.Scatter(
        x=periodos,
        y=vp_flujos,
        name='Valor Presente',
        mode='lines+markers',
        line=dict(color='green', width=2),
        marker=dict(size=6),
        showlegend=True
    ))
    
    fig.update_layout(
        title="Flujos de Caja: Nominal vs Valor Presente",
        xaxis_title="Periodo",
        yaxis_title="Monto ($)",
        height=400,
        width=900,
        hovermode='x unified',
        font=dict(size=10)
    )
    
    return fig


def _plotly_a_imagen(fig, width=900, height=400):
    """Convierte una gráfica Plotly a una imagen para incluir en el PDF.
    
    Si kaleido no está disponible, intenta usar otros métodos o retorna None.
    """
    try:
        # Intentar con kaleido primero
        img_bytes = pio.to_image(fig, format='png', width=width, height=height)
        img_stream = io.BytesIO(img_bytes)
        img = Image(img_stream, width=6.5*inch, height=3.2*inch)
        return img
    except Exception as e:
        print(f"Advertencia: No se pudo generar imagen PNG: {e}")
        print("Asegúrate de tener 'kaleido' instalado: pip install kaleido")
        return None


def generar_nombre_archivo_pdf(nombre_proyecto):
    """Genera un nombre de archivo PDF basado en el nombre del proyecto."""
    fecha = datetime.now().strftime('%Y%m%d_%H%M%S')
    nombre_limpio = nombre_proyecto.replace(' ', '_').replace('/', '_')
    return f"Informe_{nombre_limpio}_{fecha}.pdf"
