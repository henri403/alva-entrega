import os
import smtplib
import requests
import logging
from flask import Flask, request, jsonify, send_from_directory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

# Configuração de Logs para facilitar o diagnóstico no Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# --- Configurações do Mercado Pago ---
MP_ACCESS_TOKEN = "APP_USR-1698378827686338-020918-3eb43b92c8f40920f12aa6a2671b8c15-3187010530"

# --- Configuração de E-mail ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "alvaeducacao@gmail.com"
SMTP_PASSWORD = "mwed wyhf xqbo dlyy"

# --- Mapeamento de Arquivos PDF (Busca Flexível) ---
PRODUCT_FILES = {
    "Módulo 0": ["modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf"],
    "Módulo 1": ["modulo_1_construcao_relacionamentos_final_v7_final.pdf"],
    "Módulo 2": ["modulo_2_prospeccao_e_geracao_de_leads.pdf"],
    "Módulo 3": ["modulo_3_qualificacao_e_necessidades.pdf"],
    "Módulo 4": ["modulo_4_propostas_de_valor_v2.pdf"],
    "Módulo 5": ["modulo_5_persuasao_e_influencia_v3.pdf"],
    "Módulo 6": ["modulo_6_apresentacao_e_demonstracoes.pdf"],
    "Módulo 7": ["modulo_7_superacao_de_objecoes.pdf"],
    "Módulo 8": ["modulo_8_tecnicas_de_fechamento.pdf"],
    "Módulo 9": ["modulo_9_negociacao_e_gestao_de_contratos.pdf"],
    "Módulo 10": ["modulo_10_follow_up_e_pos_venda.pdf"],
    "Módulo 11": ["modulo_11_gestao_de_pipeline_e_crm_v2.pdf"],
    "Módulo 12": ["modulo_12_vendas_digitais_e_redes_sociais_revisado.pdf"],
    "Módulo 13": ["modulo_13_analise_de_dados_e_metricas_revisado.pdf"],
    "Módulo 14": ["modulo_14_lideranca_em_vendas_revisado.pdf"],
    "Módulo 15": ["modulo_15_tendencias_futuras_e_inovacao.pdf"],
    "Pacote Completo": ["Alva_Educacao_Pacote_Completo.pdf"],
    "Guia IA": ["guia_ia_negocios.pdf"]
}

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
            # Tenta encontrar o arquivo na raiz ou na pasta modules
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

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info(f"E-mail enviado com sucesso para {customer_email}")
        return True
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {e}")
        return False

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
    
    if data and data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if payment_id:
            url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    payment_info = response.json()
                    status = payment_info.get("status")
                    
                    if status == "approved":
                        customer_email = payment_info.get("payer", {}).get("email")
                        # Pega a descrição do Mercado Pago
                        mp_description = payment_info.get("description", "")
                        if not mp_description and payment_info.get("additional_info", {}).get("items"):
                            mp_description = payment_info["additional_info"]["items"][0].get("title", "")
                        
                        logger.info(f"Pagamento aprovado. Cliente: {customer_email}, Descrição MP: {mp_description}")
                        
                        # Busca flexível: verifica se algum termo do nosso dicionário está na descrição do MP
                        found_product = None
                        for key in PRODUCT_FILES:
                            if key.lower() in mp_description.lower():
                                found_product = key
                                break
                        
                        if customer_email and found_product:
                            pdf_paths = PRODUCT_FILES[found_product]
                            send_email(customer_email, mp_description, pdf_paths)
                        else:
                            logger.warning(f"Nenhum produto correspondente encontrado para: {mp_description}")
                else:
                    logger.error(f"Erro ao consultar Mercado Pago: {response.status_code}")
            except Exception as e:
                logger.error(f"Erro no processamento do webhook: {e}")
                        
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
