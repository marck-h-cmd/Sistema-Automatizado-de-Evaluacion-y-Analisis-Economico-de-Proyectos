
import requests
import streamlit as st
import os

def consultar_groq(prompt, max_tokens: int = 600):
 
    api_key = st.secrets.get('GROQ_API_KEY') or os.environ.get('GROQ_API_KEY')
    if not api_key:
        return ("IA (Groq) no disponible: configure la clave `GROQ_API_KEY` en `st.secrets` "
                "o como variable de entorno para habilitar consultas reales.")

    # URL de la API de Groq (formato compatible con OpenAI)
    url = "https://api.groq.com/openai/v1/chat/completions"

    # Modelo configurable (por defecto llama-3.3-70b-versatile)
    model = st.secrets.get('GROQ_MODEL') or os.environ.get('GROQ_MODEL', 'llama-3.3-70b-versatile')

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        # Extraer respuesta en formato OpenAI (usado por Groq)
        if isinstance(data, dict) and 'choices' in data:
            choices = data['choices']
            if isinstance(choices, list) and len(choices) > 0:
                first_choice = choices[0]
                if isinstance(first_choice, dict) and 'message' in first_choice:
                    message = first_choice['message']
                    if isinstance(message, dict) and 'content' in message:
                        return message['content']

        # Fallback: devolver la respuesta serializada
        return str(data)
    except Exception as e:
        return f"Error al consultar Groq: {e}"
    

def project_context(proyecto, vpn, tir, bc, consulta_ia):
    contexto = f"""
                    Proyecto: {proyecto['nombre']}
                    Inversión: ${proyecto['inversion']:,.2f}
                    Periodos: {proyecto['periodos']} años
                    VPN: ${vpn:,.2f}
                    TIR: {tir:.2f}%
                    B/C: {bc:.2f}
                    Tasa de descuento: {proyecto['tasa_descuento']}%
                    TMAR: {proyecto['tmar']}%
                    
                    Consulta del usuario: {consulta_ia}
                    """
    return contexto