import streamlit as st
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
from src.utils.ai import consultar_groq, project_context
import numpy as np

def show_eval_basica_form(nombre_proyecto):
    st.header("📈 Evaluación Básica del Proyecto (VPN, TIR, B/C)")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("💵 Configuración de Flujos de Caja")
        
        inversion_inicial = st.number_input("Inversión Inicial ($)", min_value=0.0, value=100000.0, step=1000.0)
        num_periodos = st.slider("Número de Periodos (años)", min_value=1, max_value=20, value=5)
        tasa_descuento = st.slider("Tasa de Descuento (%)", min_value=0.0, max_value=50.0, value=10.0, step=0.5)
        
        st.markdown("#### Flujos de Caja por Periodo")
        flujos = [-inversion_inicial]
        
        cols = st.columns(min(num_periodos, 5))
        for i in range(num_periodos):
            col_idx = i % 5
            with cols[col_idx]:
                flujo = st.number_input(f"Año {i+1}", value=30000.0, step=1000.0, key=f"flujo_{i}")
                flujos.append(flujo)
    
    with col2:
        st.subheader("🎯 Tasa de Referencia")
        tmar = st.number_input("TMAR - Tasa Mínima Atractiva (%)", min_value=0.0, value=12.0, step=0.5)
    
    # Cálculos
    vpn = calcular_vpn(flujos, tasa_descuento/100)
    tir = calcular_tir(flujos)
    bc = calcular_bc(flujos, tasa_descuento/100)
    pr = calcular_periodo_recuperacion(flujos)
    
    # Guardar en sesión
    st.session_state.proyecto_data = {
        'nombre': nombre_proyecto,
        'inversion': inversion_inicial,
        'periodos': num_periodos,
        'flujos': flujos,
        'tasa_descuento': tasa_descuento,
        'tmar': tmar,
        'vpn': vpn,
        'tir': tir,
        'bc': bc,
        'pr': pr
    }
    
    st.markdown("---")
    st.subheader("📊 Resultados de la Evaluación")
    
    # Métricas principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("VPN", f"${vpn:,.2f}", 
                 delta="Viable" if vpn > 0 else "No Viable",
                 delta_color="normal" if vpn > 0 else "inverse")
    
    with col2:
        tir_display = f"{tir:.2f}%" if tir is not None else "N/A"
        st.metric("TIR", tir_display,
                 delta=f"TMAR: {tmar}%",
                 delta_color="normal" if tir and tir > tmar else "inverse")
    
    with col3:
        st.metric("B/C", f"{bc:.2f}",
                 delta="Rentable" if bc > 1 else "No Rentable",
                 delta_color="normal" if bc > 1 else "inverse")
    
    with col4:
        st.metric("Periodo Recuperación", f"{pr} años",
                 delta=f"de {num_periodos} años")
    
    # Botón de análisis IA
    st.markdown("---")
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 2])
    with col_btn2:
        if st.button("🤖 Analizar con IA", key="ia_basico", use_container_width=True):
            with st.spinner("Consultando al asistente de IA..."):
                consulta_usuario = "Analiza estos resultados financieros y proporciona una interpretación profesional sobre la viabilidad del proyecto, riesgos potenciales y recomendaciones estratégicas."
                contexto = project_context(st.session_state.proyecto_data, vpn, tir if tir else 0, bc, consulta_usuario)
                respuesta_ia = consultar_groq(contexto, max_tokens=800)
                st.session_state.respuesta_ia_basico = respuesta_ia
    
    # Mostrar análisis de IA si existe
    if 'respuesta_ia_basico' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 Análisis Inteligente")
        st.info(st.session_state.respuesta_ia_basico)
    
    # Interpretación
    st.markdown("---")
    st.markdown("### 📋 Interpretación de Resultados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if vpn > 0:
            st.success(f"""
            **✅ VPN POSITIVO: ${vpn:,.2f}**
            
            El proyecto genera valor económico. Por cada dólar invertido, el proyecto crea ${abs(vpn/inversion_inicial):.2f} de valor presente.
            """)
        else:
            st.error(f"""
            **❌ VPN NEGATIVO: ${vpn:,.2f}**
            
            El proyecto destruye valor. Se recomienda rechazar la inversión o reevaluar los supuestos.
            """)
    
    with col2:
        if tir and tir > tmar:
            st.success(f"""
            **✅ TIR SUPERIOR A TMAR**
            
            TIR ({tir:.2f}%) > TMAR ({tmar}%)
            
            El proyecto supera la rentabilidad mínima requerida por {tir-tmar:.2f} puntos porcentuales.
            """)
        elif tir:
            st.error(f"""
            **❌ TIR INFERIOR A TMAR**
            
            TIR ({tir:.2f}%) < TMAR ({tmar}%)
            
            El proyecto no alcanza la rentabilidad mínima esperada.
            """)
    
    # Gráfico de flujos de caja
    st.markdown("### 📈 Visualización de Flujos de Caja")
    
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
    vp_flujos = [flujo / (1 + tasa_descuento/100)**i for i, flujo in enumerate(flujos)]
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
    fig.add_vline(x=tasa_descuento, line_dash="dash", line_color="green", row=2, col=2)
    
    fig.update_xaxes(title_text="Periodo", row=1, col=1)
    fig.update_xaxes(title_text="Periodo", row=1, col=2)
    fig.update_xaxes(title_text="Periodo", row=2, col=1)
    fig.update_xaxes(title_text="Tasa de Descuento (%)", row=2, col=2)
    
    fig.update_yaxes(title_text="Flujo ($)", row=1, col=1)
    fig.update_yaxes(title_text="Acumulado ($)", row=1, col=2)
    fig.update_yaxes(title_text="VP ($)", row=2, col=1)
    fig.update_yaxes(title_text="VPN ($)", row=2, col=2)
    
    fig.update_layout(height=700, showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
