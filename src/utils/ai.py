
import requests
import streamlit as st
import os


# Función para llamar a la IA (sin await / fetch JS)
def consultar_ia(prompt):
    """Consulta al modelo de IA (requiere ANTHROPIC_API_KEY en variables de entorno).
    Devuelve un mensaje informativo si la key no está configurada o en caso de error."""
    api_key = st.secrets["API_KEY"]
    if not api_key:
        return ("IA no disponible: configure la variable de entorno ANTHROPIC_API_KEY "
                "para habilitar consultas reales. Actualmente se usan respuestas simuladas.")

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 1000,
        "messages": [{"role": "user", "content": prompt}]
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # Manejar distintas formas de respuesta de forma segura
        if isinstance(data, dict):
            if 'content' in data and isinstance(data['content'], list) and len(data['content']) > 0:
                return data['content'][0].get('text', str(data))
            if 'completion' in data:
                return data['completion']
            if 'message' in data:
                return data['message']
        return str(data)
    except Exception as e:
        return f"Error al consultar IA: {e}"


def consultar_groq(prompt, max_tokens: int = 600):
    """Consulta un modelo a través de Groq.

    Requiere configurar la clave en `st.secrets['GROQ_API_KEY']` o la variable de entorno `GROQ_API_KEY`.
    También puede configurarse `st.secrets['GROQ_MODEL']` para usar un modelo específico (por defecto: llama-3.3-70b-versatile).

    Nota: No guardes claves en el código. Pega tu clave en `secrets.toml` o en el panel de Secrets de Streamlit.
    """
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