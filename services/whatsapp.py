import requests
import json
import os
from flask import url_for

# Placeholder credentials - User should replace these via env vars or direct edit
# In a real scenario, we'd load these from os.environ
WA_PHONE_ID = os.environ.get('WA_PHONE_ID', 'YOUR_PHONE_ID')
WA_TOKEN = os.environ.get('WA_TOKEN', 'YOUR_ACCESS_TOKEN')

def send_whatsapp_message(to_number, template_name='hello_world', components=None):
    """
    Sends a message via WhatsApp Cloud API.
    
    Args:
        to_number (str): The recipient's phone number (international format, e.g., 5511999999999).
        template_name (str): The name of the template to use (if using templates).
        components (list): List of components for the template (header, body parameters, etc.).
    """
    pass

def send_welcome_message(collaborator, raw_password):
    """
    Sends the welcome message with login credentials.
    
    Args:
        collaborator (Collaborator): The collaborator model instance.
        raw_password (str): The unhashed password to send vertically.
    """
    
    # Clean phone number (remove +, spaces, dashes)
    phone = "".join(filter(str.isdigit, collaborator.phone))
    
    # Build the message text
    # Note: To use templates properly in WA Business API, you must create a template in the Meta Manager.
    # For now, we will try to use a 'text' message if permitted (has 24h window limits) 
    # OR we assume a template exists. 
    # Since we can't create a template for the user, we will fallback to a standard text message 
    # but warn that it might fail if outside the 24h customer service window 
    # (unless it's a template).
    
    # Ideally, this should be a template:
    # "welcome_collab" with params: [name, link, user, password]
    
    login_url = url_for('main.magic_login', token=collaborator.token, _external=True)
    
    message_body = (
        f"Olá, {collaborator.name} 👋\n\n"
        f"Você foi cadastrado no sistema da Barbearia Joe Felipe.\n\n"
        f"🔐 Acesso ao seu painel:\n{login_url}\n\n"
        f"👤 Usuário: {collaborator.phone}\n"
        f"🔑 Senha: {raw_password}\n\n"
        f"Qualquer dúvida, fale com a gestão."
    )
    
    url = f"https://graph.facebook.com/v17.0/{WA_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WA_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message_body}
    }
    
    print(f"--- MOCK SENDING WHATSAPP TO {phone} ---")
    print(message_body)
    print("------------------------------------------")
    
    # Se este bloco falhar, não queremos quebrar o salvamento do admin
    try:
        # Verifica se as credenciais são reais
        if WA_TOKEN == 'YOUR_ACCESS_TOKEN' or WA_PHONE_ID == 'YOUR_PHONE_ID':
            print("Credenciais do WhatsApp não definidas. Pulando envio real.")
            return {"status": "mock_sent_no_creds", "body": message_body}

        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar WhatsApp: {e}")
        return None
