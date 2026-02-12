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

def get_data_with_retry(payment_id, order_id=None):
    """Tenta buscar os dados do cliente repetidamente por até 10 minutos"""
    max_attempts = 20
    wait_seconds = 30
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Tentativa {attempt}/{max_attempts} para Pagamento {payment_id}...")
        
        headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
        
        # 1. Tenta buscar no Pagamento
        try:
            resp_p = requests.get(f"https://api.mercadopago.com/v1/payments/{payment_id}", headers=headers)
            if resp_p.status_code == 200:
                p_data = resp_p.json()
                email = p_data.get("payer", {}).get("email")
                if not is_valid_email(email):
                    email = p_data.get("additional_info", {}).get("payer", {}).get("email")
                
                desc = p_data.get("description", "")
                if not desc and p_data.get("additional_info", {}).get("items"):
                    desc = p_data["additional_info"]["items"][0].get("title", "")
                
                if is_valid_email(email) and desc:
                    return email, desc
        except Exception as e:
            logger.error(f"Erro Pagamento: {e}")

        # 2. Tenta buscar na Merchant Order
        if order_id:
            try:
                resp_o = requests.get(f"https://api.mercadopago.com/merchant_orders/{order_id}", headers=headers)
                if resp_o.status_code == 200:
                    o_data = resp_o.json()
                    email_o = o_data.get("payer", {}).get("email")
                    if is_valid_email(email_o):
                        # Se achou o e-mail, tenta pegar a descrição do pagamento de novo
                        return email_o, desc if 'desc' in locals() and desc else "Produto Alva Educação"
            except Exception as e:
                logger.error(f"Erro Ordem: {e}")

        logger.warning(f"Dados ainda não disponíveis. Aguardando {wait_seconds}s...")
        time.sleep(wait_seconds)
    
    return None, None

def background_worker(payment_id, order_id):
    """Função que roda em segundo plano para não travar o servidor"""
    logger.info(f"Iniciando busca em segundo plano para ID {payment_id}")
    email, description = get_data_with_retry(payment_id, order_id)
    
    if email and description:
        norm_desc = normalize_text(description)
        found_product = None
        for key in PRODUCT_FILES:
            if key in norm_desc:
                found_product = key
                break
        
        if found_product:
            send_email_resend(email, description, PRODUCT_FILES[found_product])
        else:
            logger.error(f"Produto não mapeado: {description}")
    else:
        logger.error(f"Desistindo do ID {payment_id} após 10 minutos.")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Webhook recebido: {data}")
    
    if not data: return jsonify({"status": "ok"}), 200

    payment_id = None
    order_id = None

    # Se for notificação de pagamento
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        
    # Se for notificação de ordem (Merchant Order)
    elif data.get("type") in ["merchant_order", "topic_merchant_order_wh"]:
        order_id = data.get("data", {}).get("id") or data.get("id")
        # Busca o pagamento aprovado na ordem
        try:
            resp = requests.get(f"https://api.mercadopago.com/merchant_orders/{order_id}", 
                                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"})
            if resp.status_code == 200:
                o_info = resp.json()
                for p in o_info.get("payments", []):
                    if p.get("status") == "approved":
                        payment_id = p.get("id")
                        break
        except: pass

    if payment_id:
        # LANÇA A TAREFA EM SEGUNDO PLANO E RESPONDE AO MERCADO PAGO NA HORA
        thread = threading.Thread(target=background_worker, args=(payment_id, order_id))
        thread.start()
    elif order_id:
        # Se recebemos uma ordem mas ainda não tem pagamento aprovado, 
        # podemos lançar um worker para vigiar a ordem por um tempo
        logger.info(f"Ordem {order_id} recebida sem pagamento aprovado ainda. Ignorando até o próximo webhook.")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
