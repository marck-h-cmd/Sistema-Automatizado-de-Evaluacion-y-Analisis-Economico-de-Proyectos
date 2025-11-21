
import streamlit as st
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from plotly.subplots import make_subplots

def show_sensibilidad_form():
    st.header("⚠️ Análisis de Sensibilidad y Riesgo")
    st.markdown("Identifica las variables críticas que más impactan la rentabilidad del proyecto.")
    
    if st.session_state.proyecto_data is None:
        st.warning("⚠️ Primero completa la Evaluación Básica.")
    else:
        tipo_analisis = st.radio("Selecciona el tipo de análisis:", 
                                 ["Sensibilidad Univariada", "Sensibilidad Bivariada", "Análisis Tornado"],
                                 horizontal=True)
        
        if tipo_analisis == "Sensibilidad Univariada":
            st.subheader("📊 Análisis de Sensibilidad Univariada")
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                variable = st.selectbox("Variable a analizar:", 
                                       ["Flujos de Caja", "Tasa de Descuento", "Inversión Inicial"])
                rango_var = st.slider("Rango de variación (%)", 10, 50, 30, 5)
            
            with col2:
                if st.button("🤖 Interpretar con IA", use_container_width=True):
                    st.info("💬 Interpretación de IA disponible en versión completa")
            
            flujos_base = st.session_state.proyecto_data['flujos']
            tasa_base = st.session_state.proyecto_data['tasa_descuento']
            
            # Generar variaciones
            variaciones = np.linspace(-rango_var, rango_var, 20)
            vpns = []
            tirs = []
            bcs = []
            
            for var in variaciones:
                if variable == "Flujos de Caja":
                    factor = 1 + var/100
                    flujos_mod = [flujos_base[0]] + [f * factor for f in flujos_base[1:]]
                    vpn = calcular_vpn(flujos_mod, tasa_base/100)
                    tir = calcular_tir(flujos_mod)
                    bc = calcular_bc(flujos_mod, tasa_base/100)
                elif variable == "Tasa de Descuento":
                    tasa_mod = tasa_base * (1 + var/100)
                    vpn = calcular_vpn(flujos_base, tasa_mod/100)
                    tir = calcular_tir(flujos_base)
                    bc = calcular_bc(flujos_base, tasa_mod/100)
                else:  # Inversión Inicial
                    factor = 1 + var/100
                    flujos_mod = [flujos_base[0] * factor] + flujos_base[1:]
                    vpn = calcular_vpn(flujos_mod, tasa_base/100)
                    tir = calcular_tir(flujos_mod)
                    bc = calcular_bc(flujos_mod, tasa_base/100)
                
                vpns.append(vpn)
                tirs.append(tir if tir else 0)
                bcs.append(bc)
            
            # Encontrar punto de equilibrio
            vpn_positivos = [i for i, v in enumerate(vpns) if v > 0]
            if vpn_positivos:
                idx_equilibrio = min(vpn_positivos, key=lambda i: abs(vpns[i]))
                punto_equilibrio = variaciones[idx_equilibrio]
            else:
                punto_equilibrio = None
            
            # Gráficos
            fig = make_subplots(
                rows=1, cols=3,
                subplot_titles=('Sensibilidad VPN', 'Sensibilidad TIR', 'Sensibilidad B/C')
            )
            
            fig.add_trace(
                go.Scatter(x=variaciones, y=vpns, mode='lines+markers', 
                          name='VPN', line=dict(color='blue', width=3)),
                row=1, col=1
            )
            fig.add_hline(y=0, line_dash="dash", line_color="red", row=1, col=1)
            
            fig.add_trace(
                go.Scatter(x=variaciones, y=tirs, mode='lines+markers',
                          name='TIR', line=dict(color='green', width=3)),
                row=1, col=2
            )
            fig.add_hline(y=st.session_state.proyecto_data['tmar'], 
                         line_dash="dash", line_color="red", row=1, col=2)
            
            fig.add_trace(
                go.Scatter(x=variaciones, y=bcs, mode='lines+markers',
                          name='B/C', line=dict(color='purple', width=3)),
                row=1, col=3
            )
            fig.add_hline(y=1, line_dash="dash", line_color="red", row=1, col=3)
            
            fig.update_xaxes(title_text=f"Variación de {variable} (%)", row=1, col=1)
            fig.update_xaxes(title_text=f"Variación de {variable} (%)", row=1, col=2)
            fig.update_xaxes(title_text=f"Variación de {variable} (%)", row=1, col=3)
            
            fig.update_yaxes(title_text="VPN ($)", row=1, col=1)
            fig.update_yaxes(title_text="TIR (%)", row=1, col=2)
            fig.update_yaxes(title_text="B/C", row=1, col=3)
            
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
            
            # Resultados
            col1, col2, col3 = st.columns(3)
            
            with col1:
                vpn_min = min(vpns)
                vpn_max = max(vpns)
                st.metric("VPN Mínimo", f"${vpn_min:,.2f}", delta=f"{-rango_var}%")
            
            with col2:
                vpn_base = st.session_state.proyecto_data['vpn']
                st.metric("VPN Base", f"${vpn_base:,.2f}", delta="0%")
            
            with col3:
                st.metric("VPN Máximo", f"${vpn_max:,.2f}", delta=f"+{rango_var}%")
            
            if punto_equilibrio is not None:
                st.info(f"""
                📍 **Punto de Equilibrio**: La variable puede variar hasta **{punto_equilibrio:+.1f}%** 
                antes de que el VPN se vuelva negativo.
                """)
            else:
                st.warning("⚠️ El VPN es negativo en todo el rango analizado.")
        
        elif tipo_analisis == "Sensibilidad Bivariada":
            st.subheader("🎯 Análisis de Sensibilidad Bivariada")
            st.markdown("Analiza el impacto simultáneo de dos variables en el VPN.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                var1 = st.selectbox("Primera Variable:", 
                                   ["Flujos de Caja", "Tasa de Descuento", "Inversión Inicial"],
                                   key="var1")
                rango1 = st.slider("Rango Variable 1 (%)", 10, 50, 30, 5, key="rango1")
            
            with col2:
                var2 = st.selectbox("Segunda Variable:", 
                                   ["Tasa de Descuento", "Flujos de Caja", "Inversión Inicial"],
                                   key="var2")
                rango2 = st.slider("Rango Variable 2 (%)", 10, 50, 30, 5, key="rango2")
            
            if var1 == var2:
                st.error("⚠️ Selecciona dos variables diferentes.")
            else:
                flujos_base = st.session_state.proyecto_data['flujos']
                tasa_base = st.session_state.proyecto_data['tasa_descuento']
                
                # Crear matriz de VPNs
                vars1 = np.linspace(-rango1, rango1, 15)
                vars2 = np.linspace(-rango2, rango2, 15)
                vpn_matrix = np.zeros((len(vars1), len(vars2)))
                
                for i, v1 in enumerate(vars1):
                    for j, v2 in enumerate(vars2):
                        flujos_mod = flujos_base.copy()
                        tasa_mod = tasa_base
                        
                        # Aplicar variación 1
                        if var1 == "Flujos de Caja":
                            flujos_mod = [flujos_mod[0]] + [f * (1 + v1/100) for f in flujos_mod[1:]]
                        elif var1 == "Tasa de Descuento":
                            tasa_mod = tasa_base * (1 + v1/100)
                        else:
                            flujos_mod[0] = flujos_mod[0] * (1 + v1/100)
                        
                        # Aplicar variación 2
                        if var2 == "Flujos de Caja":
                            flujos_mod = [flujos_mod[0]] + [f * (1 + v2/100) for f in flujos_mod[1:]]
                        elif var2 == "Tasa de Descuento":
                            tasa_mod = tasa_mod * (1 + v2/100)
                        else:
                            flujos_mod[0] = flujos_mod[0] * (1 + v2/100)
                        
                        vpn_matrix[i, j] = calcular_vpn(flujos_mod, tasa_mod/100)
                
                # Gráfico de contorno
                fig = go.Figure(data=go.Contour(
                    z=vpn_matrix,
                    x=vars2,
                    y=vars1,
                    colorscale='RdYlGn',
                    contours=dict(
                        start=vpn_matrix.min(),
                        end=vpn_matrix.max(),
                        size=(vpn_matrix.max()-vpn_matrix.min())/20,
                        showlabels=True
                    ),
                    colorbar=dict(title="VPN ($)")
                ))
                
                fig.add_contour(
                    z=vpn_matrix,
                    x=vars2,
                    y=vars1,
                    showscale=False,
                    contours=dict(
                        start=0,
                        end=0,
                        size=1,
                        coloring='lines'
                    ),
                    line=dict(color='red', width=3)
                )
                
                fig.update_layout(
                    title="Mapa de Sensibilidad (Línea roja: VPN = 0)",
                    xaxis_title=f"Variación {var2} (%)",
                    yaxis_title=f"Variación {var1} (%)",
                    height=600
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análisis de resultados
                vpn_min = vpn_matrix.min()
                vpn_max = vpn_matrix.max()
                pct_positivo = (vpn_matrix > 0).sum() / vpn_matrix.size * 100
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("VPN Mínimo", f"${vpn_min:,.2f}")
                
                with col2:
                    st.metric("VPN Máximo", f"${vpn_max:,.2f}")
                
                with col3:
                    st.metric("Área VPN > 0", f"{pct_positivo:.1f}%")
                
                st.info(f"""
                📊 **Interpretación**: La línea roja muestra la combinación de valores donde VPN = 0.
                - Zona verde: Combinaciones que generan VPN positivo
                - Zona roja: Combinaciones que generan VPN negativo
                - {pct_positivo:.1f}% de las combinaciones analizadas resultan en VPN positivo
                """)
        
        else:  # Análisis Tornado
            st.subheader("🌪️ Diagrama Tornado")
            st.markdown("Identifica las variables con mayor impacto en el VPN del proyecto.")
            
            rango_tornado = st.slider("Rango de variación para análisis (%)", 10, 50, 20, 5)
            
            flujos_base = st.session_state.proyecto_data['flujos']
            tasa_base = st.session_state.proyecto_data['tasa_descuento']
            vpn_base = st.session_state.proyecto_data['vpn']
            
            variables = {
                'Flujos de Caja': [],
                'Tasa de Descuento': [],
                'Inversión Inicial': []
            }
            
            # Calcular impacto de cada variable
            for var_name in variables.keys():
                # Variación negativa
                if var_name == "Flujos de Caja":
                    flujos_mod = [flujos_base[0]] + [f * (1 - rango_tornado/100) for f in flujos_base[1:]]
                    vpn_min = calcular_vpn(flujos_mod, tasa_base/100)
                    flujos_mod = [flujos_base[0]] + [f * (1 + rango_tornado/100) for f in flujos_base[1:]]
                    vpn_max = calcular_vpn(flujos_mod, tasa_base/100)
                elif var_name == "Tasa de Descuento":
                    tasa_min = tasa_base * (1 - rango_tornado/100)
                    tasa_max = tasa_base * (1 + rango_tornado/100)
                    vpn_min = calcular_vpn(flujos_base, tasa_max/100)
                    vpn_max = calcular_vpn(flujos_base, tasa_min/100)
                else:  # Inversión Inicial
                    flujos_mod = [flujos_base[0] * (1 + rango_tornado/100)] + flujos_base[1:]
                    vpn_min = calcular_vpn(flujos_mod, tasa_base/100)
                    flujos_mod = [flujos_base[0] * (1 - rango_tornado/100)] + flujos_base[1:]
                    vpn_max = calcular_vpn(flujos_mod, tasa_base/100)
                
                variables[var_name] = {
                    'min': vpn_min,
                    'max': vpn_max,
                    'rango': abs(vpn_max - vpn_min)
                }
            
            # Ordenar por impacto
            vars_ordenadas = sorted(variables.items(), key=lambda x: x[1]['rango'], reverse=True)
            
            # Crear diagrama tornado
            fig = go.Figure()
            
            y_pos = list(range(len(vars_ordenadas)))
            
            for i, (var_name, datos) in enumerate(vars_ordenadas):
                # Barra izquierda (negativa)
                fig.add_trace(go.Bar(
                    y=[var_name],
                    x=[datos['min'] - vpn_base],
                    orientation='h',
                    name=f"-{rango_tornado}%",
                    marker_color='#ff6b6b',
                    showlegend=(i==0),
                    text=f"${datos['min']:,.0f}",
                    textposition='inside'
                ))
                
                # Barra derecha (positiva)
                fig.add_trace(go.Bar(
                    y=[var_name],
                    x=[datos['max'] - vpn_base],
                    orientation='h',
                    name=f"+{rango_tornado}%",
                    marker_color='#6bcf7f',
                    showlegend=(i==0),
                    text=f"${datos['max']:,.0f}",
                    textposition='inside'
                ))
            
            fig.add_vline(x=0, line_dash="dash", line_color="black", line_width=2)
            
            fig.update_layout(
                title=f"Diagrama Tornado - Variación del VPN (±{rango_tornado}%)",
                xaxis_title="Variación del VPN respecto al caso base ($)",
                yaxis_title="Variables",
                barmode='overlay',
                height=400,
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de impactos
            st.markdown("### 📊 Ranking de Impacto de Variables")
            
            df_tornado = pd.DataFrame([
                {
                    'Variable': var_name,
                    'VPN Mínimo': f"${datos['min']:,.2f}",
                    'VPN Máximo': f"${datos['max']:,.2f}",
                    'Rango': f"${datos['rango']:,.2f}",
                    'Sensibilidad': '🔴' * int(datos['rango'] / max([v['rango'] for v in variables.values()]) * 5)
                }
                for var_name, datos in vars_ordenadas
            ])
            
            st.dataframe(df_tornado, use_container_width=True, hide_index=True)
            
            # Interpretación
            var_critica = vars_ordenadas[0][0]
            impacto_critico = vars_ordenadas[0][1]['rango']
            
            st.success(f"""
            🎯 **Variable Más Crítica**: **{var_critica}**
            
            - Esta variable tiene el mayor impacto en el VPN del proyecto
            - Una variación de ±{rango_tornado}% genera un cambio de ${impacto_critico:,.2f} en el VPN
            - Se recomienda monitorear y gestionar activamente esta variable
            - Considerar estrategias de cobertura o mitigación de riesgo
            """)