import os
import requests
import logging
import unicodedata
import base64
import re
import time
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
EMAIL_TO_REPLY = "alvaeducacao@gmail.com"

# --- Mapeamento de Arquivos PDF ---
PRODUCT_FILES = {
    "modulo 0": ["modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf"],
    "modulo 1": ["modulo_1_construcao_relacionamentos_final_v7_final.pdf"],
    "modulo 2": ["modulo_2_prospeccao_e_geracao_de_leads.pdf"],
    "modulo 3": ["modulo_3_qualificacao_e_necessidades.pdf"],
    "modulo 4": ["modulo_4_propostas_de_valor_v2.pdf"],
    "modulo 5": ["modulo_5_persuasao_e_influencia_v3.pdf"],
    "modulo 6": ["modulo_6_apresentacao_e_demonstracoes.pdf"],
    "modulo 7": ["modulo_7_superacao_de_objecoes.pdf"],
    "modulo 8": ["modulo_8_tecnicas_de_fechamento.pdf"],
    "modulo 9": ["modulo_9_negociacao_e_gestao_de_contratos.pdf"],
    "modulo 10": ["modulo_10_follow_up_e_pos_venda.pdf"],
    "modulo 11": ["modulo_11_gestao_de_pipeline_e_crm_v2.pdf"],
    "modulo 12": ["modulo_12_vendas_digitais_e_redes_sociais_revisado.pdf"],
    "modulo 13": ["modulo_13_analise_de_dados_e_metricas_revisado.pdf"],
    "modulo 14": ["modulo_14_lideranca_em_vendas_revisado.pdf"],
    "modulo 15": ["modulo_15_tendencias_futuras_e_inovacao.pdf"],
    "pacote completo": ["Alva_Educacao_Pacote_Completo.pdf"],
    "guia ia": ["guia_ia_negocios.pdf"]
}

def normalize_text(text):
    if not text: return ""
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode("utf-8")
    return text.lower()

def is_valid_email(email):
    if not email or not isinstance(email, str): return False
    if "XXXXXXXXXXX" in email or "test_user" in email or "@testuser.com" in email:
        return False
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

def send_email_resend(customer_email, product_name, pdf_paths):
    try:
        if not is_valid_email(customer_email):
            logger.error(f"E-mail inválido: {customer_email}. Abortando.")
            return False

        logger.info(f"Enviando via Resend para {customer_email} - Produto: {product_name}")
        
        attachments = []
        for path in pdf_paths:
            actual_path = path if os.path.exists(path) else os.path.join("modules", path)
            if os.path.exists(actual_path):
                with open(actual_path, "rb") as f:
                    content = base64.b64encode(f.read()).decode()
                    attachments.append({"content": content, "filename": os.path.basename(actual_path)})
            else:
                logger.error(f"Arquivo não encontrado: {actual_path}")

        if not attachments: return False

        email_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                <h2 style="color: #2c3e50;">Olá!</h2>
                <p>Obrigado pela sua compra na <strong>Alva Educação</strong>!</p>
                <p>Seu material <strong>{product_name}</strong> está em anexo.</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="font-size: 0.9em;">Dúvidas? Responda a este e-mail ou escreva para <strong>{EMAIL_TO_REPLY}</strong>.</p>
                <p>Atenciosamente,<br><strong>Equipe Alva Educação</strong></p>
            </div>
        </body>
        </html>
        """

        payload = {
            "from": EMAIL_FROM,
            "to": customer_email,
            "subject": f"Seu acesso ao curso: {product_name}",
            "html": email_body,
            "reply_to": EMAIL_TO_REPLY,
            "attachments": attachments
        }

        headers = {"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"}
        response = requests.post("https://api.resend.com/emails", json=payload, headers=headers)
        return response.status_code in [200, 201]
    except Exception as e:
        logger.error(f"Erro envio: {e}")
        return False

def get_email_from_merchant_order(order_id):
    """Tenta buscar o e-mail do cliente na Ordem de Venda (Merchant Order)"""
    url = f"https://api.mercadopago.com/merchant_orders/{order_id}"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            order_data = response.json()
            # Tenta pegar o e-mail do comprador na ordem
            email = order_data.get("payer", {}).get("email")
            if is_valid_email(email):
                return email
            # Se não tiver, tenta ver se tem algum e-mail nos pagamentos vinculados
            for payment in order_data.get("payments", []):
                p_email = payment.get("payer", {}).get("email")
                if is_valid_email(p_email):
                    return p_email
    except Exception as e:
        logger.error(f"Erro ao buscar Merchant Order {order_id}: {e}")
    return None

def process_payment(payment_id, order_id=None):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            payment_info = response.json()
            if payment_info.get("status") == "approved":
                # 1. Tenta pegar e-mail do pagamento
                customer_email = payment_info.get("payer", {}).get("email")
                
                # 2. Se falhar e tivermos o order_id, tenta na Merchant Order
                if not is_valid_email(customer_email) and order_id:
                    logger.info(f"E-mail não encontrado no pagamento {payment_id}. Buscando na Ordem {order_id}...")
                    customer_email = get_email_from_merchant_order(order_id)
                
                # 3. Tenta pegar a descrição
                description = payment_info.get("description", "")
                if not description and payment_info.get("additional_info", {}).get("items"):
                    description = payment_info["additional_info"]["items"][0].get("title", "")
                
                logger.info(f"Processando: ID={payment_id}, E-mail={customer_email}, Produto={description}")
                
                norm_desc = normalize_text(description)
                found_product = None
                for key in PRODUCT_FILES:
                    if key in norm_desc:
                        found_product = key
                        break
                
                if is_valid_email(customer_email) and found_product:
                    send_email_resend(customer_email, description, PRODUCT_FILES[found_product])
                else:
                    logger.warning(f"DADOS INCOMPLETOS: E-mail={customer_email}, Produto={found_product}")
    except Exception as e:
        logger.error(f"Erro process_payment: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Webhook recebido: {data}")
    
    if not data: return jsonify({"status": "ok"}), 200

    # Se for notificação de pagamento
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if payment_id:
            process_payment(payment_id)
            
    # Se for notificação de ordem (Merchant Order)
    elif data.get("type") in ["merchant_order", "topic_merchant_order_wh"]:
        order_id = data.get("data", {}).get("id") or data.get("id")
        if order_id:
            # Pequena espera para o MP processar tudo
            time.sleep(2)
            url = f"https://api.mercadopago.com/merchant_orders/{order_id}"
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    order_info = response.json()
                    for payment in order_info.get("payments", []):
                        if payment.get("status") == "approved":
                            process_payment(payment.get("id"), order_id)
            except Exception as e:
                logger.error(f"Erro webhook merchant_order: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
