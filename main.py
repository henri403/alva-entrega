import os
import smtplib
import requests
import logging
import unicodedata
from flask import Flask, request, jsonify, send_from_directory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# --- Configurações do Mercado Pago ---
MP_ACCESS_TOKEN = "APP_USR-1698378827686338-020918-3eb43b92c8f40920f12aa6a2671b8c15-3187010530"

# --- Configuração de E-mail (USANDO SSL PORTA 465) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = "alvaeducacao@gmail.com"
SMTP_PASSWORD = "pdgq tean mhrk dtjw"

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

def send_email(customer_email, product_name, pdf_paths):
    try:
        logger.info(f"Iniciando envio de e-mail para {customer_email} - Produto: {product_name}")
        msg = MIMEMultipart()
        msg['From'] = f"Alva Educação <{SMTP_USER}>"
        msg['To'] = customer_email
        msg['Subject'] = f"Seu acesso ao curso: {product_name}"

        body = f"Olá,\n\nMuito obrigado pela sua compra na Alva Educação! Estamos muito felizes em ter você conosco.\n\nSeu acesso ao curso {product_name} está disponível. Anexado a este e-mail, você encontrará o material completo em formato PDF.\n\nEsperamos que este conteúdo seja um diferencial em sua jornada e traga resultados incríveis para você.\n\nSe tiver qualquer dúvida ou precisar de suporte, não hesite em nos contatar. Estamos à disposição para ajudar!\n\nAtenciosamente,\nEquipe Alva Educação\nwww.alvaeducacao.com.br"
        
        msg.attach(MIMEText(body, 'plain'))

        files_attached = 0
        for path in pdf_paths:
            actual_path = path
            if not os.path.exists(actual_path):
                actual_path = os.path.join("modules", path)
            
            if os.path.exists(actual_path):
                with open(actual_path, "rb") as f:
                    filename = os.path.basename(actual_path)
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)
                    files_attached += 1
                    logger.info(f"Arquivo anexado: {filename}")
            else:
                logger.error(f"Arquivo NÃO encontrado: {actual_path}")

        if files_attached == 0:
            logger.error("Nenhum arquivo foi anexado. O e-mail não será enviado.")
            return False

        logger.info("Conectando ao servidor SMTP via SSL...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"E-mail enviado com sucesso para {customer_email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False

def process_payment(payment_id):
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            payment_info = response.json()
            if payment_info.get("status") == "approved":
                customer_email = payment_info.get("payer", {}).get("email")
                description = payment_info.get("description", "")
                if not description and payment_info.get("additional_info", {}).get("items"):
                    description = payment_info["additional_info"]["items"][0].get("title", "")
                
                logger.info(f"Pagamento aprovado. Cliente: {customer_email}, Descrição: {description}")
                
                norm_desc = normalize_text(description)
                found_product = None
                for key in PRODUCT_FILES:
                    if key in norm_desc:
                        found_product = key
                        break
                
                if customer_email and found_product:
                    send_email(customer_email, description, PRODUCT_FILES[found_product])
                else:
                    logger.warning(f"Produto não mapeado: {description}")
        else:
            logger.error(f"Erro MP {payment_id}: {response.status_code}")
    except Exception as e:
        logger.error(f"Erro process_payment: {e}")

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    logger.info(f"Webhook recebido: {data}")
    
    if not data:
        return jsonify({"status": "error"}), 400

    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if payment_id:
            process_payment(payment_id)
    elif data.get("type") in ["merchant_order", "topic_merchant_order_wh"]:
        order_id = data.get("data", {}).get("id") or data.get("id")
        if order_id:
            url = f"https://api.mercadopago.com/merchant_orders/{order_id}"
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    order_info = response.json()
                    for payment in order_info.get("payments", []):
                        if payment.get("status") == "approved":
                            process_payment(payment.get("id"))
            except Exception as e:
                logger.error(f"Erro merchant_order: {e}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
