import base64
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
import streamlit as st

def crear_template_email(nombre_usuario):
    """Crea template HTML profesional para el email"""
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f4f4f4;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 30px auto;
                background-color: #ffffff;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 30px;
                text-align: center;
                color: white;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
            }}
            .content {{
                padding: 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: #333;
                margin-bottom: 20px;
            }}
            .info-box {{
                background-color: #f8f9fa;
                border-left: 4px solid #667eea;
                padding: 15px;
                margin: 20px 0;
                border-radius: 5px;
            }}
            
            .footer {{
                background-color: #f8f9fa;
                padding: 20px;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>💰 Sistema de Evaluación Económica de Proyectos</h1>
                <p>Universidad Nacional de Trujillo</p>
            </div>
            
            <div class="content">
                <p class="greeting">Hola <strong>{nombre_usuario}</strong>,</p>
                
                <p>Tu reporte de <strong>El archivo</strong> ha sido generado exitosamente.</p>
                
             
                
                <p>Encuentra adjunto  del reporte completo con todos los detalles y análisis.</p>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    Este reporte fue generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Sistema de Evaluación Económica de Proyectos</strong></p>
                <p>Universidad Nacional de Trujillo</p>
                <p style="margin-top: 10px;">© 2025 Todos los derechos reservados</p>
            </div>
        </div>
    </body>
    </html>
    """
    return html_template


def enviar_email_con_attachment(email_destino, nombre_usuario, file_buffer, filename , mime_main='application', mime_sub='octet-stream'):
    """

    Args:
        email_destino: str
        nombre_usuario: str
        file_buffer: BytesIO o bytes
        filename: nombre del archivo adjunto
        mime_main: parte principal del MIME (default 'application')
        mime_sub: subtipo MIME (default 'octet-stream')
    Returns:
        (bool, mensaje)
    """
    try:
        gmail_user = st.secrets["gmail"]["user"]
        gmail_password = st.secrets["gmail"]["password"]

        mensaje = MIMEMultipart('alternative')
        mensaje['From'] = f"Evaluador de proyectos <{gmail_user}>"
        mensaje['To'] = email_destino
        mensaje['Subject'] = f"📊 Tu Reporte de evaluación de proyectos"

        html_content = crear_template_email(nombre_usuario)
        parte_html = MIMEText(html_content, 'html')
        mensaje.attach(parte_html)

        # Preparar el adjunto
        if hasattr(file_buffer, 'getvalue'):
            file_buffer.seek(0)
            file_bytes = file_buffer.read()
        else:
            file_bytes = file_buffer

        parte = MIMEBase(mime_main, mime_sub)
        parte.set_payload(file_bytes)
        encoders.encode_base64(parte)
        parte.add_header('Content-Disposition', f'attachment; filename="{filename}"')
        mensaje.attach(parte)

        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(gmail_user, gmail_password)
            server.send_message(mensaje)

        return True, f"Email enviado exitosamente a {email_destino}"
    except KeyError as e:
        return False, f"Error de configuración: Falta la clave {str(e)} en secrets.toml"
    except smtplib.SMTPAuthenticationError:
        return False, "Error de autenticación. Verifica tus credenciales de Gmail"
    except smtplib.SMTPException as e:
        return False, f"Error SMTP: {str(e)}"
    except Exception as e:
        return False, f"Error inesperado: {str(e)}"