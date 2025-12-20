import streamlit as st
import json
import io
from datetime import datetime
from src.utils.eval_basica import calcular_vpn, calcular_tir, calcular_bc, calcular_periodo_recuperacion
from src.utils.informe import crear_informe_pdf, generar_nombre_archivo_pdf
import pandas as pd 
from plotly import graph_objects as go
from src.utils.ai import consultar_groq, project_context

def show_informe_form(fecha_analisis,analista):
    st.header("📋 Informe Ejecutivo Completo")
    
    if st.session_state.proyecto_data is None:
        st.warning("⚠️ Primero completa la evaluación en las pestañas anteriores.")
    else:
        # Generar informe
        proyecto = st.session_state.proyecto_data
        
        # Header del informe
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; color: white; margin-bottom: 2rem;">
            <h1 style="margin: 0;">📊 {proyecto['nombre']}</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
                Informe de Evaluación Económica y Financiera
            </p>
            <p style="margin: 0.5rem 0 0 0;">
                Fecha: {fecha_analisis.strftime('%d/%m/%Y')} | Analista: {analista}
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # Resumen Ejecutivo
        st.markdown("## 📌 Resumen Ejecutivo")
        
        vpn = proyecto['vpn']
        tir = proyecto['tir']
        bc = proyecto['bc']
        
        decision = "ACEPTAR" if vpn > 0 and tir and tir > proyecto['tmar'] and bc > 1 else "RECHAZAR" if vpn < 0 else "REVISAR"
        color = "green" if decision == "ACEPTAR" else "red" if decision == "RECHAZAR" else "orange"
        
        st.markdown(f"""
        <div style="background-color: {color}; padding: 1.5rem; border-radius: 10px; 
                    color: white; text-align: center; font-size: 1.5rem; font-weight: bold;">
            RECOMENDACIÓN: {decision} EL PROYECTO
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Indicadores Principales
        st.markdown("## 📊 Indicadores Financieros Principales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Inversión Total", f"${proyecto['inversion']:,.2f}")
        
        with col2:
            st.metric("VPN", f"${vpn:,.2f}",
                     delta="✅ Positivo" if vpn > 0 else "❌ Negativo")
        
        with col3:
            st.metric("TIR", f"{tir:.2f}%" if tir else "N/A",
                     delta=f"TMAR: {proyecto['tmar']}%")
        
        with col4:
            st.metric("B/C", f"{bc:.2f}",
                     delta="✅ Rentable" if bc > 1 else "❌ No Rentable")
        
        st.markdown("---")
        
        # Análisis Detallado
        st.markdown("## 📈 Análisis Detallado")
        
        tab_a, tab_b, tab_c = st.tabs(["Flujos de Caja", "Análisis de Riesgo", "Conclusiones"])
        
        with tab_a:
            # Tabla de flujos
            periodos = list(range(len(proyecto['flujos'])))
            tasa = proyecto['tasa_descuento'] / 100
            
            df_flujos = pd.DataFrame({
                'Periodo': periodos,
                'Flujo de Caja': [f"${f:,.2f}" for f in proyecto['flujos']],
                'Flujo Acumulado': [f"${sum(proyecto['flujos'][:i+1]):,.2f}" for i in periodos],
                'Valor Presente': [f"${proyecto['flujos'][i] / (1 + tasa)**i:,.2f}" for i in periodos],
                'VP Acumulado': [f"${sum([proyecto['flujos'][j] / (1 + tasa)**j for j in range(i+1)]):,.2f}" for i in periodos]
            })
            
            st.dataframe(df_flujos, use_container_width=True, hide_index=True)
            
            # Gráfico de flujos
            fig_flujos = go.Figure()
            
            fig_flujos.add_trace(go.Bar(
                x=periodos,
                y=proyecto['flujos'],
                name='Flujo Nominal',
                marker_color=['red' if f < 0 else 'lightblue' for f in proyecto['flujos']]
            ))
            
            vp_flujos = [proyecto['flujos'][i] / (1 + tasa)**i for i in periodos]
            fig_flujos.add_trace(go.Scatter(
                x=periodos,
                y=vp_flujos,
                name='Valor Presente',
                mode='lines+markers',
                line=dict(color='green', width=3)
            ))
            
            fig_flujos.update_layout(
                title="Flujos de Caja: Nominal vs Valor Presente",
                xaxis_title="Periodo",
                yaxis_title="Monto ($)",
                height=400
            )
            
            st.plotly_chart(fig_flujos, use_container_width=True)
        
        with tab_b:
            st.markdown("### ⚠️ Factores de Riesgo Identificados")
            
            # Análisis de sensibilidad simplificado
            variables_riesgo = ['Flujos de Caja', 'Tasa de Descuento', 'Inversión Inicial']
            impactos = []
            
            for var in variables_riesgo:
                if var == "Flujos de Caja":
                    flujos_mod = [proyecto['flujos'][0]] + [f * 0.8 for f in proyecto['flujos'][1:]]
                    vpn_modificado = calcular_vpn(flujos_mod, tasa)
                elif var == "Tasa de Descuento":
                    vpn_modificado = calcular_vpn(proyecto['flujos'], (proyecto['tasa_descuento'] * 1.2) / 100)
                else:
                    flujos_mod = [proyecto['flujos'][0] * 1.2] + proyecto['flujos'][1:]
                    vpn_modificado = calcular_vpn(flujos_mod, tasa)
                
                impacto = abs(vpn_modificado - vpn)
                impactos.append(impacto)
            
            df_riesgo = pd.DataFrame({
                'Variable': variables_riesgo,
                'Impacto en VPN': [f"${imp:,.2f}" for imp in impactos],
                'Nivel de Riesgo': ['🔴 Alto' if imp > abs(vpn) * 0.5 else '🟡 Medio' if imp > abs(vpn) * 0.2 else '🟢 Bajo' for imp in impactos]
            })
            
            st.dataframe(df_riesgo, use_container_width=True, hide_index=True)
            
            st.markdown("### 🎯 Escenarios de Estrés")
            
            escenarios_estres = {
                'Pesimista': 0.7,
                'Moderado': 0.85,
                'Optimista': 1.15
            }
            
            resultados_estres = []
            for nombre, factor in escenarios_estres.items():
                flujos_mod = [proyecto['flujos'][0]] + [f * factor for f in proyecto['flujos'][1:]]
                vpn_mod = calcular_vpn(flujos_mod, tasa)
                tir_mod = calcular_tir(flujos_mod)
                
                resultados_estres.append({
                    'Escenario': nombre,
                    'Factor': f"{factor*100:.0f}%",
                    'VPN': f"${vpn_mod:,.2f}",
                    'TIR': f"{tir_mod:.2f}%" if tir_mod else "N/A",
                    'Estado': '✅' if vpn_mod > 0 else '❌'
                })
            
            df_estres = pd.DataFrame(resultados_estres)
            st.dataframe(df_estres, use_container_width=True, hide_index=True)
        
        with tab_c:
            st.markdown("### 🎯 Conclusiones y Recomendaciones")
            
            # Fortalezas
            st.markdown("#### ✅ Fortalezas del Proyecto")
            fortalezas = []
            
            if vpn > 0:
                fortalezas.append(f"VPN positivo de ${vpn:,.2f}, indica creación de valor")
            if tir and tir > proyecto['tmar']:
                fortalezas.append(f"TIR ({tir:.2f}%) supera la tasa mínima requerida ({proyecto['tmar']}%)")
            if bc > 1:
                fortalezas.append(f"Relación Beneficio/Costo de {bc:.2f} indica rentabilidad")
            if proyecto['pr'] < proyecto['periodos']:
                fortalezas.append(f"Recuperación de inversión en {proyecto['pr']} años")
            
            for i, fortaleza in enumerate(fortalezas, 1):
                st.success(f"{i}. {fortaleza}")
            
            # Debilidades
            st.markdown("#### ⚠️ Aspectos a Considerar")
            debilidades = []
            
            if vpn < proyecto['inversion'] * 0.2:
                debilidades.append("VPN relativamente bajo respecto a la inversión")
            if tir and abs(tir - proyecto['tmar']) < 5:
                debilidades.append("Margen limitado entre TIR y TMAR")
            if proyecto['pr'] > proyecto['periodos'] / 2:
                debilidades.append("Periodo de recuperación largo")
            
            if debilidades:
                for i, debilidad in enumerate(debilidades, 1):
                    st.warning(f"{i}. {debilidad}")
            else:
                st.info("No se identificaron debilidades significativas en los indicadores principales")
            
            # Recomendación final
            st.markdown("#### 📌 Recomendación Final")
            
            if decision == "ACEPTAR":
                st.success(f"""
                **SE RECOMIENDA ACEPTAR EL PROYECTO**
                
                El proyecto {proyecto['nombre']} presenta indicadores financieros favorables:
                
                - VPN positivo: ${vpn:,.2f}
                - TIR superior a TMAR: {tir:.2f}% vs {proyecto['tmar']}%
                - Relación B/C rentable: {bc:.2f}
                
                El proyecto genera valor económico y cumple con los criterios de rentabilidad establecidos.
                Se sugiere proceder con la implementación bajo monitoreo continuo de las variables críticas.
                """)
            elif decision == "RECHAZAR":
                st.error(f"""
                **SE RECOMIENDA RECHAZAR EL PROYECTO**
                
                El proyecto {proyecto['nombre']} no cumple con los criterios mínimos de rentabilidad:
                
                - VPN: ${vpn:,.2f}
                - TIR: {tir:.2f}% {'< TMAR' if tir and tir < proyecto['tmar'] else ''}
                - B/C: {bc:.2f}
                
                El proyecto no genera valor suficiente o no supera el costo de oportunidad del capital.
                Se recomienda buscar alternativas de inversión más rentables.
                """)
            else:
                st.warning(f"""
                **SE RECOMIENDA REVISAR EL PROYECTO**
                
                El proyecto {proyecto['nombre']} presenta indicadores mixtos que requieren análisis adicional:
                
                - VPN: ${vpn:,.2f}
                - TIR: {tir:.2f}%
                - B/C: {bc:.2f}
                
                Se sugiere:
                1. Realizar análisis de sensibilidad más profundo
                2. Evaluar opciones de mejora en los flujos de caja
                3. Considerar escenarios alternativos de implementación
                4. Revisar supuestos y proyecciones
                """)
        
        st.markdown("---")
        
        # Sección de Asistente IA
        st.markdown("## 🤖 Consulta al Asistente de IA")
        st.markdown("Obtén análisis personalizado y recomendaciones basadas en tu proyecto.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            consulta_ia = st.text_area(
                "¿Qué te gustaría saber sobre tu proyecto?",
                placeholder="Ejemplo: ¿Cuáles son los principales riesgos de este proyecto? ¿Cómo puedo mejorar la rentabilidad?",
                height=100
            )
        
        with col2:
            st.markdown("### Consultas Sugeridas")
            if st.button("💡 Analizar Riesgos", use_container_width=True):
                st.session_state['consulta_ia_activa'] = "Analiza los principales riesgos de este proyecto de inversión"
                
            if st.button("📈 Mejorar Rentabilidad", use_container_width=True):
                st.session_state['consulta_ia_activa'] = "¿Cómo puedo mejorar la rentabilidad del proyecto?"
            
            if st.button("🎯 Estrategias", use_container_width=True):
                st.session_state['consulta_ia_activa'] = "Sugiere estrategias de implementación"
        
        if st.button("🚀 Consultar a la IA", type="primary", use_container_width=True):
            if consulta_ia or 'consulta_ia_activa' in st.session_state:
                consulta_final = st.session_state.get('consulta_ia_activa', consulta_ia)
                if consulta_final:
                    st.session_state['consulta_ia_activa'] = consulta_final
        
        # Contenedor para mostrar respuestas de IA
        if 'consulta_ia_activa' in st.session_state and st.session_state['consulta_ia_activa']:
            st.markdown("---")
            st.markdown("### 📊 Respuesta del Asistente de IA")
            
            with st.spinner("🤖 El asistente de IA está analizando tu proyecto..."):
                consulta_final = st.session_state['consulta_ia_activa']
                context = project_context(proyecto, vpn, tir, bc, consulta_final)
                response = consultar_groq(context)
                st.info(response)
                
                # Limpiar la variable para la siguiente consulta
                if st.button("🔄 Nueva Consulta", use_container_width=False):
                    del st.session_state['consulta_ia_activa']
                    st.rerun()
        
        # Exportar informe
        st.markdown("---")
        st.markdown("## 📥 Exportar Informe")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Exportar a PDF", use_container_width=True):
                with st.spinner("⏳ Generando PDF..."):
                    try:
                        # Generar PDF
                        pdf_buffer = crear_informe_pdf(proyecto, fecha_analisis, analista)
                        nombre_archivo = generar_nombre_archivo_pdf(proyecto['nombre'])
                        
                        st.download_button(
                            label="✅ Descargar PDF",
                            data=pdf_buffer,
                            file_name=nombre_archivo,
                            mime="application/pdf",
                            key="download_pdf"
                        )
                        st.success("✅ PDF generado exitosamente")
                    except Exception as e:
                        st.error(f"❌ Error al generar PDF: {str(e)}")
        
        with col2:
            if st.button("📊 Exportar a Excel", use_container_width=True):
                with st.spinner("⏳ Generando Excel..."):
                    try:
                        # Preparar datos para Excel
                        periodos = list(range(len(proyecto['flujos'])))
                        tasa = proyecto['tasa_descuento'] / 100
                        
                        # Crear DataFrame con flujos
                        df_flujos = pd.DataFrame({
                            'Periodo': periodos,
                            'Flujo de Caja': proyecto['flujos'],
                            'Flujo Acumulado': [sum(proyecto['flujos'][:i+1]) for i in periodos],
                            'Valor Presente': [proyecto['flujos'][i] / (1 + tasa)**i for i in periodos],
                            'VP Acumulado': [sum([proyecto['flujos'][j] / (1 + tasa)**j for j in range(i+1)]) for i in periodos]
                        })
                        
                        # Crear archivo Excel en memoria
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            # Hoja 1: Resumen Ejecutivo
                            df_resumen = pd.DataFrame({
                                'Indicador': ['Inversión Total', 'VPN', 'TIR', 'B/C', 'Tasa Descuento', 'TMAR', 'Periodo Recuperación', 'Decisión'],
                                'Valor': [
                                    f"${proyecto['inversion']:,.2f}",
                                    f"${vpn:,.2f}",
                                    f"{tir:.2f}%" if tir else "N/A",
                                    f"{bc:.2f}",
                                    f"{proyecto['tasa_descuento']}%",
                                    f"{proyecto['tmar']}%",
                                    str(proyecto.get('pr', 'N/A')),
                                    decision
                                ]
                            })
                            df_resumen.to_excel(writer, sheet_name='Resumen', index=False)
                            
                            # Hoja 2: Flujos de Caja
                            df_flujos.to_excel(writer, sheet_name='Flujos de Caja', index=False)
                        
                        output.seek(0)
                        
                        # Generar nombre de archivo
                        fecha_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                        nombre_archivo_excel = f"Informe_{proyecto['nombre'].replace(' ', '_')}_{fecha_str}.xlsx"
                        
                        st.download_button(
                            label="✅ Descargar Excel",
                            data=output,
                            file_name=nombre_archivo_excel,
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key="download_excel"
                        )
                        st.success("✅ Excel generado exitosamente")
                    except Exception as e:
                        st.error(f"❌ Error al generar Excel: {str(e)}")
        
        with col3:
            # Generar JSON con datos del proyecto
            if st.button("💾 Exportar a JSON", use_container_width=True):
                try:
                    datos_proyecto = {
                        'proyecto': proyecto['nombre'],
                        'fecha_analisis': fecha_analisis.strftime('%Y-%m-%d'),
                        'analista': analista,
                        'inversion': proyecto['inversion'],
                        'periodos': proyecto['periodos'],
                        'flujos': proyecto['flujos'],
                        'tasa_descuento': proyecto['tasa_descuento'],
                        'tmar': proyecto['tmar'],
                        'indicadores': {
                            'vpn': vpn,
                            'tir': tir,
                            'bc': bc,
                            'periodo_recuperacion': proyecto['pr']
                        },
                        'decision': decision
                    }
                    
                    json_str = json.dumps(datos_proyecto, indent=2)
                    
                    st.download_button(
                        label="✅ Descargar JSON",
                        data=json_str,
                        file_name=f"proyecto_{proyecto['nombre'].replace(' ', '_')}.json",
                        mime="application/json",
                        key="download_json"
                    )
                    st.success("✅ JSON generado exitosamente")
                except Exception as e:
                    st.error(f"❌ Error al generar JSON: {str(e)}")
