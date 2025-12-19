import streamlit as st
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
from src.utils.ai import consultar_groq
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def show_escenarios_form():
    st.header("🎯 Análisis de Escenarios")
    st.markdown("Evalúa el proyecto bajo diferentes situaciones considerando la incertidumbre del futuro.")
    
    if st.session_state.proyecto_data is None:
        st.warning("⚠️ Primero completa la Evaluación Básica en la pestaña anterior.")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader("📊 Configuración de Escenarios")
            
            # Escenario Pesimista
            with st.expander("📉 Escenario Pesimista", expanded=True):
                prob_pesimista = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_pes', 20.0)),
                    step=0.1,
                    key="prob_pes"
                )
                factor_pesimista = st.slider("Factor de Reducción", 0.3, 0.9, 0.7, 0.05, key="factor_pes")
                st.info(f"Los flujos se reducen al {factor_pesimista*100:.0f}% del escenario base")
            
            # Escenario Base
            with st.expander("📊 Escenario Base", expanded=True):
                prob_base = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_base', 50.0)),
                    step=0.1,
                    key="prob_base"
                )
                st.info("Se utilizan los flujos del escenario base sin modificación")
            
            # Escenario Optimista
            with st.expander("📈 Escenario Optimista", expanded=True):
                prob_optimista = st.slider(
                    "Probabilidad (%)",
                    0.0,
                    100.0,
                    value=float(st.session_state.get('prob_opt', 30.0)),
                    step=0.1,
                    key="prob_opt"
                )
                factor_optimista = st.slider("Factor de Incremento", 1.1, 2.0, 1.3, 0.05, key="factor_opt")
                st.info(f"Los flujos se incrementan al {factor_optimista*100:.0f}% del escenario base")
            
            # Validar probabilidades
            suma_prob = prob_pesimista + prob_base + prob_optimista
            if abs(suma_prob - 100.0) > 0.05:
                st.error(f"⚠️ La suma de probabilidades debe ser 100%. Actual: {suma_prob}%")
        
        with col2:
            st.subheader("🎲 Probabilidades")
            
            fig_prob = go.Figure(data=[go.Pie(
                labels=['Pesimista', 'Base', 'Optimista'],
                values=[prob_pesimista, prob_base, prob_optimista],
                hole=0.4,
                marker_colors=['#ff6b6b', '#ffd93d', '#6bcf7f']
            )])
            fig_prob.update_layout(height=300)
            st.plotly_chart(fig_prob, use_container_width=True)
            
            # Preparar petición IA: marcador para procesar después de calcular resultados
            def _request_ia():
                st.session_state['ask_ia_escenarios'] = True

            st.button("🤖 Analizar Escenarios con IA", use_container_width=True, key="btn_ia", on_click=_request_ia)

            # Callback seguro para normalizar probabilidades (actualiza session_state antes de recrear widgets)
            def _normalize_callback():
                suma = st.session_state.get('prob_pes', 0) + st.session_state.get('prob_base', 0) + st.session_state.get('prob_opt', 0)
                if suma > 0:
                    npes = round(st.session_state.get('prob_pes', 0) / suma * 100.0, 1)
                    nbase = round(st.session_state.get('prob_base', 0) / suma * 100.0, 1)
                    nopt = round(st.session_state.get('prob_opt', 0) / suma * 100.0, 1)
                    diff = round(100.0 - (npes + nbase + nopt), 1)
                    vals = [st.session_state.get('prob_pes', 0), st.session_state.get('prob_base', 0), st.session_state.get('prob_opt', 0)]
                    max_idx = int(np.argmax(vals))
                    if max_idx == 0:
                        npes += diff
                    elif max_idx == 1:
                        nbase += diff
                    else:
                        nopt += diff

                    st.session_state['prob_pes'] = float(npes)
                    st.session_state['prob_base'] = float(nbase)
                    st.session_state['prob_opt'] = float(nopt)
                    st.session_state['normalizado_msg'] = f"Probabilidades normalizadas: Pes {npes}%, Base {nbase}%, Opt {nopt}%"
                else:
                    st.session_state['normalizado_msg'] = "No se puede normalizar: la suma de probabilidades es 0."

            # Botón que usa callback
            st.button("🔄 Normalizar Probabilidades", use_container_width=True, key="btn_normalizar", on_click=_normalize_callback)

            # Mostrar mensaje resultante (si existe)
            if 'normalizado_msg' in st.session_state:
                msg = st.session_state.pop('normalizado_msg')
                if msg.startswith('Probabilidades normalizadas'):
                    st.success(msg)
                else:
                    st.warning(msg)
        
        if suma_prob == 100:
            # Calcular escenarios
            flujos_base = st.session_state.proyecto_data['flujos']
            tasa = st.session_state.proyecto_data['tasa_descuento'] / 100
            
            # Pesimista
            flujos_pes = [flujos_base[0]] + [f * factor_pesimista for f in flujos_base[1:]]
            vpn_pes = calcular_vpn(flujos_pes, tasa)
            tir_pes = calcular_tir(flujos_pes)
            bc_pes = calcular_bc(flujos_pes, tasa)
            
            # Base
            vpn_base = st.session_state.proyecto_data['vpn']
            tir_base = st.session_state.proyecto_data['tir']
            bc_base = st.session_state.proyecto_data['bc']
            
            # Optimista
            flujos_opt = [flujos_base[0]] + [f * factor_optimista for f in flujos_base[1:]]
            vpn_opt = calcular_vpn(flujos_opt, tasa)
            tir_opt = calcular_tir(flujos_opt)
            bc_opt = calcular_bc(flujos_opt, tasa)
            
            # VPN Esperado
            vpn_esperado = (vpn_pes * prob_pesimista + vpn_base * prob_base + vpn_opt * prob_optimista) / 100
            
            # Estadísticas
            vpns = [vpn_pes, vpn_base, vpn_opt]
            probs = [prob_pesimista/100, prob_base/100, prob_optimista/100]
            desv_std = np.sqrt(sum([p * (v - vpn_esperado)**2 for v, p in zip(vpns, probs)]))
            rango = vpn_opt - vpn_pes
            prob_exito = (prob_base + prob_optimista) if vpn_base > 0 else prob_optimista
            
            st.markdown("---")
            st.subheader("📊 Resultados por Escenario")
            
            # Tabla comparativa
            df_escenarios = pd.DataFrame({
                'Escenario': ['Pesimista', 'Base', 'Optimista'],
                'Probabilidad': [f"{prob_pesimista}%", f"{prob_base}%", f"{prob_optimista}%"],
                'VPN': [f"${vpn_pes:,.2f}", f"${vpn_base:,.2f}", f"${vpn_opt:,.2f}"],
                'TIR': [f"{tir_pes:.2f}%" if tir_pes else "N/A", 
                       f"{tir_base:.2f}%" if tir_base else "N/A",
                       f"{tir_opt:.2f}%" if tir_opt else "N/A"],
                'B/C': [f"{bc_pes:.2f}", f"{bc_base:.2f}", f"{bc_opt:.2f}"]
            })
            
            st.dataframe(df_escenarios, use_container_width=True, hide_index=True)

            # Si el usuario solicitó análisis por IA, mostrar aquí (debajo de la tabla)
            if st.session_state.get('ask_ia_escenarios'):
                with st.spinner("🤖 Generando análisis profundo con IA (Groq)... Esto puede tomar unos momentos..."):
                    # Construir un prompt muy detallado y completo para análisis profundo
                    prompt = (
                        "Eres un analista financiero senior especializado en evaluación de proyectos de inversión y gestión de riesgos. "
                        "Tu tarea es proporcionar un análisis ejecutivo COMPLETO y PROFUNDO del siguiente análisis de escenarios.\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "📊 DATOS DEL PROYECTO - ANÁLISIS DE ESCENARIOS\n"
                        "═══════════════════════════════════════════════════════════════\n\n"

                        f"**MÉTRICAS PRINCIPALES:**\n"
                        f"• VPN Esperado (ponderado): ${vpn_esperado:,.2f}\n"
                        f"• Tasa de Descuento: {st.session_state.proyecto_data['tasa_descuento']}%\n"
                        f"• Inversión Inicial: ${abs(flujos_base[0]):,.2f}\n"
                        f"• Horizonte del Proyecto: {len(flujos_base)-1} períodos\n\n"

                        f"**ESCENARIO PESIMISTA (Probabilidad: {prob_pesimista}%):**\n"
                        f"• VPN: ${vpn_pes:,.2f}\n"
                        f"• TIR: {tir_pes:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_pes:.2f}\n"
                        f"• Factor de reducción aplicado: {factor_pesimista*100:.0f}% de los flujos base\n\n"

                        f"**ESCENARIO BASE (Probabilidad: {prob_base}%):**\n"
                        f"• VPN: ${vpn_base:,.2f}\n"
                        f"• TIR: {tir_base:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_base:.2f}\n"
                        f"• Flujos sin modificación (escenario más probable)\n\n"

                        f"**ESCENARIO OPTIMISTA (Probabilidad: {prob_optimista}%):**\n"
                        f"• VPN: ${vpn_opt:,.2f}\n"
                        f"• TIR: {tir_opt:.2f}%\n"
                        f"• Relación Beneficio/Costo: {bc_opt:.2f}\n"
                        f"• Factor de incremento aplicado: {factor_optimista*100:.0f}% de los flujos base\n\n"

                        f"**ANÁLISIS DE RIESGO:**\n"
                        f"• Desviación Estándar del VPN: ${desv_std:,.2f}\n"
                        f"• Coeficiente de Variación: {(desv_std/abs(vpn_esperado)*100):.2f}%\n"
                        f"• Rango Total de VPN: ${rango:,.2f}\n"
                        f"• Spread: desde ${vpn_pes:,.2f} hasta ${vpn_opt:,.2f}\n"
                        f"• Probabilidad de Éxito (VPN > 0): {prob_exito}%\n"
                        f"• Probabilidad de Fracaso (VPN < 0): {100-prob_exito}%\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "📝 ANÁLISIS REQUERIDO (RESPONDE DE FORMA EXHAUSTIVA)\n"
                        "═══════════════════════════════════════════════════════════════\n\n"

                        "**1. DIAGNÓSTICO GENERAL DEL PROYECTO:**\n"
                        "   - Evalúa la viabilidad financiera del proyecto considerando todos los escenarios\n"
                        "   - ¿Es un proyecto atractivo desde el punto de vista de riesgo-retorno?\n"
                        "   - Compara el VPN esperado con la inversión inicial\n\n"

                        "**2. ANÁLISIS DETALLADO DE CADA ESCENARIO:**\n"
                        "   - Interpreta qué significa cada escenario y su probabilidad asignada\n"
                        "   - Analiza las diferencias entre escenarios (magnitud de variación)\n"
                        "   - ¿Qué escenario tiene más peso en la decisión y por qué?\n"
                        "   - Evalúa si la distribución de probabilidades es equilibrada o sesgada\n\n"

                        "**3. EVALUACIÓN PROFUNDA DEL RIESGO:**\n"
                        "   - Interpreta la desviación estándar y el coeficiente de variación\n"
                        "   - ¿El proyecto es de alto, medio o bajo riesgo?\n"
                        "   - Analiza el rango de VPN y qué implica para la toma de decisiones\n"
                        "   - Evalúa la probabilidad de éxito: ¿es suficientemente alta?\n"
                        "   - ¿Existe exposición significativa a pérdidas?\n\n"

                        "**4. ANÁLISIS DE SENSIBILIDAD:**\n"
                        "   - ¿Qué tan sensible es el VPN a cambios en los flujos?\n"
                        "   - ¿El proyecto es robusto ante cambios adversos?\n"
                        "   - Identifica variables críticas que podrían afectar los resultados\n\n"

                        "**5. RECOMENDACIONES ESTRATÉGICAS CONCRETAS:**\n"
                        "   - ¿Deberías APROBAR, RECHAZAR o REVISAR el proyecto? (da una recomendación clara)\n"
                        "   - ¿Qué condiciones o ajustes mejorarían la viabilidad?\n"
                        "   - ¿Se necesitan garantías, cobertura de riesgos o planes de contingencia?\n"
                        "   - ¿Hay aspectos del proyecto que deberían renegociarse?\n\n"

                        "**6. IDENTIFICACIÓN DE RIESGOS PRINCIPALES:**\n"
                        "   - Lista los 3-5 riesgos más críticos que podrían llevar al escenario pesimista\n"
                        "   - ¿Qué eventos o factores externos podrían impactar negativamente?\n"
                        "   - ¿Hay riesgos de mercado, operacionales, financieros o regulatorios?\n\n"

                        "**7. OPORTUNIDADES Y UPSIDE POTENTIAL:**\n"
                        "   - ¿Qué factores podrían llevar al escenario optimista?\n"
                        "   - ¿Existen oportunidades de mejora o potencial no aprovechado?\n"
                        "   - ¿Cómo se podría maximizar el valor del proyecto?\n\n"

                        "**8. ESTRATEGIAS DE MITIGACIÓN:**\n"
                        "   - Propone 3-5 estrategias concretas para reducir riesgos\n"
                        "   - ¿Se podría implementar el proyecto en fases?\n"
                        "   - ¿Hay opciones de flexibilidad operativa o real options?\n\n"

                        "**9. COMPARACIÓN CON CRITERIOS DE ACEPTACIÓN:**\n"
                        "   - Evalúa si el proyecto cumple con estándares típicos de la industria\n"
                        "   - ¿La TIR supera la tasa de descuento en todos los escenarios?\n"
                        "   - ¿La relación B/C es aceptable?\n\n"

                        "**10. CONCLUSIÓN Y SIGUIENTE PASO:**\n"
                        "   - Resume tu posición sobre el proyecto en 2-3 oraciones\n"
                        "   - ¿Cuál debe ser el siguiente paso inmediato?\n"
                        "   - ¿Se requiere información adicional o análisis complementarios?\n\n"

                        "═══════════════════════════════════════════════════════════════\n"
                        "⚠️ IMPORTANTE: Proporciona un análisis extenso, profesional y accionable.\n"
                        "Usa formato markdown con títulos (##), subtítulos (###), bullets (-) y negritas (**) para facilitar la lectura.\n"
                        "NO uses cursivas (*texto*) ni texto en itálicas porque causa problemas de formato.\n"
                        "Usa saltos de línea dobles entre secciones para mejor legibilidad.\n"
                        "Tu respuesta debe ser de aproximadamente 25-35 líneas de análisis profundo.\n"
                        "Sé específico con los números y proporciona insights valiosos para la toma de decisiones.\n"
                        "═══════════════════════════════════════════════════════════════"
                    )
                    resp = consultar_groq(prompt, max_tokens=2500)
                    st.session_state['analisis_ia_principal'] = resp
                    st.session_state.pop('ask_ia_escenarios', None)

                with st.expander("🤖 Análisis Ejecutivo Completo - Generado por IA", expanded=True):
                    st.info(resp)

            # Métricas del análisis
            st.markdown("### 🎯 Análisis Estadístico")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("VPN Esperado", f"${vpn_esperado:,.2f}",
                         delta="Ponderado por probabilidades")
            
            with col2:
                st.metric("Desviación Estándar", f"${desv_std:,.2f}",
                         delta="Medida de riesgo")
            
            with col3:
                st.metric("Rango", f"${rango:,.2f}",
                         delta=f"${vpn_pes:,.0f} a ${vpn_opt:,.0f}")
            
            with col4:
                st.metric("Probabilidad de Éxito", f"{prob_exito}%",
                         delta="VPN > 0")
            
            # Gráficos
            col1, col2 = st.columns(2)

            with col1:
                # Gráfico de barras comparativo
                fig1 = go.Figure()
                fig1.add_trace(go.Bar(
                    x=['Pesimista', 'Base', 'Optimista'],
                    y=[vpn_pes, vpn_base, vpn_opt],
                    marker_color=['#ff6b6b', '#ffd93d', '#6bcf7f'],
                    text=[f"${v:,.0f}" for v in [vpn_pes, vpn_base, vpn_opt]],
                    textposition='auto'
                ))
                fig1.add_hline(y=0, line_dash="dash", line_color="red")
                fig1.add_hline(y=vpn_esperado, line_dash="dash", line_color="blue",
                              annotation_text=f"VPN Esperado: ${vpn_esperado:,.0f}")
                fig1.update_layout(title="VPN por Escenario", yaxis_title="VPN ($)", height=400)
                st.plotly_chart(fig1, use_container_width=True)

                # Análisis de IA para gráfico de barras
                if st.session_state.get('analisis_ia_principal'):
                    with st.spinner("🤖 Analizando gráfico de barras..."):
                        prompt_barras = (
                            "Eres un analista financiero experto. Interpreta el siguiente gráfico de barras de VPN por escenario:\n\n"
                            f"**Datos del Gráfico de Barras:**\n"
                            f"• Escenario Pesimista (barra roja): VPN = ${vpn_pes:,.2f}\n"
                            f"• Escenario Base (barra amarilla): VPN = ${vpn_base:,.2f}\n"
                            f"• Escenario Optimista (barra verde): VPN = ${vpn_opt:,.2f}\n"
                            f"• Línea roja horizontal (línea de quiebre): VPN = $0 (punto donde el proyecto ni gana ni pierde)\n"
                            f"• Línea azul horizontal (VPN Esperado): ${vpn_esperado:,.2f}\n\n"
                            f"**Contexto adicional:**\n"
                            f"• Diferencia entre escenarios: ${vpn_opt - vpn_pes:,.2f}\n"
                            f"• Distancia del escenario base al VPN esperado: ${abs(vpn_base - vpn_esperado):,.2f}\n"
                            f"• ¿Algún escenario está por debajo de cero? {'Sí' if vpn_pes < 0 else 'No'}\n\n"
                            "**Análisis requerido:**\n"
                            "1. ¿Qué patrón visual muestra el gráfico? (crecimiento uniforme, saltos abruptos, asimetría, etc.)\n"
                            "2. ¿Qué tan cerca o lejos están las barras entre sí? ¿Qué implica esto sobre la variabilidad?\n"
                            "3. ¿Cuál es la posición relativa del VPN esperado respecto a las tres barras?\n"
                            "4. ¿Hay alguna barra que cruce la línea de $0? ¿Qué significa esto?\n"
                            "5. ¿El gráfico sugiere un proyecto con alta volatilidad o estable?\n"
                            "6. ¿Qué insights clave deberían extraer los tomadores de decisión de este gráfico?\n\n"
                            "Proporciona un análisis visual conciso y práctico en 6-8 líneas.\n"
                            "NO uses cursivas (*texto*). Usa negritas (**) y saltos de línea para separar ideas."
                        )
                        analisis_barras = consultar_groq(prompt_barras, max_tokens=600)

                    with st.expander("🤖 Interpretación del Gráfico de Barras (IA)", expanded=False):
                        st.info(analisis_barras)

            with col2:
                # Distribución de probabilidad
                fig2 = go.Figure()
                fig2.add_trace(go.Scatter(
                    x=[vpn_pes, vpn_base, vpn_opt],
                    y=[prob_pesimista, prob_base, prob_optimista],
                    mode='markers+lines',
                    marker=dict(size=[prob_pesimista*2, prob_base*2, prob_optimista*2],
                               color=['#ff6b6b', '#ffd93d', '#6bcf7f']),
                    line=dict(color='gray', dash='dot')
                ))
                fig2.add_vline(x=vpn_esperado, line_dash="dash", line_color="blue",
                              annotation_text="VPN Esperado")
                fig2.update_layout(title="Distribución de Probabilidad",
                                  xaxis_title="VPN ($)", yaxis_title="Probabilidad (%)",
                                  height=400)
                st.plotly_chart(fig2, use_container_width=True)

                # Análisis de IA para gráfico de distribución
                if st.session_state.get('analisis_ia_principal'):
                    with st.spinner("🤖 Analizando distribución de probabilidad..."):
                        prompt_distribucion = (
                            "Eres un analista de riesgos experto. Interpreta el siguiente gráfico de distribución de probabilidad:\n\n"
                            f"**Datos del Gráfico de Distribución:**\n"
                            f"• Punto 1 (rojo): VPN ${vpn_pes:,.2f} con probabilidad {prob_pesimista}% (tamaño del marcador proporcional)\n"
                            f"• Punto 2 (amarillo): VPN ${vpn_base:,.2f} con probabilidad {prob_base}%\n"
                            f"• Punto 3 (verde): VPN ${vpn_opt:,.2f} con probabilidad {prob_optimista}%\n"
                            f"• Los puntos están conectados con línea punteada gris\n"
                            f"• Línea vertical azul marca el VPN Esperado: ${vpn_esperado:,.2f}\n\n"
                            f"**Métricas de distribución:**\n"
                            f"• Suma de probabilidades: {prob_pesimista + prob_base + prob_optimista}%\n"
                            f"• Escenario con mayor probabilidad: {max([('Pesimista', prob_pesimista), ('Base', prob_base), ('Optimista', prob_optimista)], key=lambda x: x[1])[0]}\n"
                            f"• Rango de VPN: ${rango:,.2f}\n"
                            f"• Desviación estándar: ${desv_std:,.2f}\n\n"
                            "**Análisis requerido:**\n"
                            "1. ¿Qué forma tiene la distribución? (simétrica, sesgada a la izquierda/derecha, uniforme, concentrada)\n"
                            "2. ¿Dónde está concentrada la mayor probabilidad? ¿Qué implica esto?\n"
                            "3. ¿Cómo se relaciona la línea del VPN esperado con los puntos de la distribución?\n"
                            "4. ¿La distribución sugiere un perfil de riesgo equilibrado o hay sesgo hacia el upside/downside?\n"
                            "5. ¿Qué tan dispersos están los puntos? ¿Alta o baja dispersión de resultados?\n"
                            "6. ¿Este patrón de distribución favorece la inversión en el proyecto? ¿Por qué?\n\n"
                            "Proporciona un análisis estadístico conciso y práctico en 6-8 líneas.\n"
                            "NO uses cursivas (*texto*). Usa negritas (**) y saltos de línea para separar ideas."
                        )
                        analisis_distribucion = consultar_groq(prompt_distribucion, max_tokens=600)

                    with st.expander("🤖 Interpretación de la Distribución (IA)", expanded=False):
                        st.info(analisis_distribucion)
            
            # Interpretación
            st.markdown("### 📋 Interpretación del Análisis")
            
            if vpn_esperado > 0:
                st.success(f"""
                **✅ PROYECTO VIABLE BAJO INCERTIDUMBRE**
                
                - El VPN esperado es positivo: ${vpn_esperado:,.2f}
                - Probabilidad de éxito (VPN > 0): {prob_exito}%
                - El proyecto mantiene valor incluso considerando escenarios adversos
                - Desviación estándar: ${desv_std:,.2f} indica el nivel de riesgo
                """)
            else:
                st.warning(f"""
                **⚠️ PROYECTO CON RIESGO ELEVADO**
                
                - El VPN esperado es: ${vpn_esperado:,.2f}
                - Probabilidad de éxito: {prob_exito}%
                - Se recomienda analizar estrategias de mitigación de riesgo
                - Considerar opciones reales o flexibilidad en la implementación
                """)
