import os
import requests
import logging
import unicodedata
import base64
import re
import time
import threading
from flask import Flask, request, jsonify, send_from_directory

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# --- Configurações do Mercado Pago ---
MP_ACCESS_TOKEN = "APP_USR-1698378827686338-020918-3eb43b92c8f40920f12aa6a2671b8c15-3187010530"

# --- Configuração do Resend ---
RESEND_API_KEY = "re_YcNaqCdZ_JEcKbM9gJx7fa9uoHqPbsKq4"
EMAIL_FROM = "Alva Educação <contato@alvaeducacao.com.br>" 
EMAIL_TO_ADMIN = "alvaeducacao@gmail.com"

# --- Mapeamento de Produtos e Preços ---
PRODUCTS = {
    "modulo_0": {"title": "Alva - Módulo 0: Segredo das Vendas", "price": 10.00, "files": ["modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf"]},
    "modulo_1": {"title": "Alva - Módulo 1: Construção de Relacionamentos", "price": 10.00, "files": ["modulo_1_construcao_relacionamentos_final_v7_final.pdf"]},
    "pacote_completo": {"title": "Alva Educação - Pacote Completo", "price": 100.00, "files": ["Alva_Educacao_Pacote_Completo.pdf"]}
}

def normalize_text(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text.lower()

def send_email_resend(to_email, subject, product_title, pdf_paths):
    try:
        attachments = []
        for path in pdf_paths:
            actual_path = path if os.path.exists(path) else os.path.join("modules", path)
            if os.path.exists(actual_path):
                with open(actual_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode()
                    attachments.append({"content": content, "filename": os.path.basename(actual_path)})

        email_body = f"<h2>Olá!</h2><p>Obrigado por comprar na Alva Educação. Seu material <b>{product_title}</b> está em anexo.</p>"
        
        payload = {
            "from": EMAIL_FROM,
            "to": to_email,
            "subject": subject,
            "html": email_body,
            "reply_to": EMAIL_TO_ADMIN,
            "attachments": attachments
        }

        headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
        requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        return True
    except Exception as e:
        logger.error(f"Erro envio: {e}")
        return False

@app.route('/create_preference', methods=['POST'])
def create_preference():
    """Cria o link de pagamento travando o e-mail do cliente"""
    data = request.json
    email = data.get("email")
    product_id = data.get("product_id")

    if not email or product_id not in PRODUCTS:
        return jsonify({"error": "Dados inválidos"}), 400

    product = PRODUCTS[product_id]
    
    preference_data = {
        "items": [{
            "title": product["title"],
            "quantity": 1,
            "unit_price": product["price"],
            "currency_id": "BRL"
        }],
        "payer": {"email": email},
        "notification_url": "https://alva-entrega.onrender.com/webhook",
        "external_reference": email # Guardamos o e-mail aqui também por segurança
    }

    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}", "Content-Type": "application/json"}
    resp = requests.post("https://api.mercadopago.com/checkout/preferences", json=preference_data, headers=headers)
    
    if resp.status_code in [200, 201]:
        return jsonify({"init_point": resp.json().get("init_point")})
    return jsonify({"error": "Erro ao criar preferência"}), 500

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Webhook recebido: {data}")
    
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        threading.Thread(target=process_payment, args=(payment_id,)).start()

    return jsonify({"status": "ok"}), 200

def process_payment(payment_id):
    """Processa o pagamento e envia o e-mail"""
    time.sleep(5) # Espera o MP processar
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    resp = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
    
    if resp.status_code == 200:
        p_data = resp.json()
        if p_data.get("status") == "approved":
            # O e-mail agora virá obrigatoriamente aqui ou no external_reference
            email = p_data.get("payer", {}).get("email") or p_data.get("external_reference")
            description = p_data.get("description", "")
            
            logger.info(f"Pagamento aprovado! Enviando para {email}")
            
            # Busca o produto pelo título
            for pid, info in PRODUCTS.items():
                if info["title"] in description:
                    send_email_resend(email, f"Seu material: {info['title']}", info["title"], info["files"])
                    break

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
