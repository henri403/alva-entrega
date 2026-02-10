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

# --- Mapeamento de Arquivos PDF ---
PRODUCT_FILES = {
    "Alva - Módulo 0: Segredo das Vendas": ["modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf"],
    "Alva - Módulo 1: Relacionamentos": ["modulo_1_construcao_relacionamentos_final_v7_final.pdf"],
    "Alva - Módulo 2: Geração de Leads": ["modulo_2_prospeccao_e_geracao_de_leads.pdf"],
    "Alva - Módulo 3: Qualificação Leads": ["modulo_3_qualificacao_e_necessidades.pdf"],
    "Alva - Módulo 4: Propostas de Valor": ["modulo_4_propostas_de_valor_v2.pdf"],
    "Alva - Módulo 5: Persuasão e Influência": ["modulo_5_persuasao_e_influencia_v3.pdf"],
    "Alva - Módulo 6: Apresentação Soluções": ["modulo_6_apresentacao_e_demonstracoes.pdf"],
    "Alva - Módulo 7: Superação Objeções": ["modulo_7_superacao_de_objecoes.pdf"],
    "Alva - Módulo 8: Técnicas Fechamento": ["modulo_8_tecnicas_de_fechamento.pdf"],
    "Alva - Módulo 9: Negociação Contratos": ["modulo_9_negociacao_e_gestao_de_contratos.pdf"],
    "Alva - Módulo 10: Follow-up Pós-venda": ["modulo_10_follow_up_e_pos_venda.pdf"],
    "Alva - Módulo 11: Gestão CRM": ["modulo_11_gestao_de_pipeline_e_crm_v2.pdf"],
    "Alva - Módulo 12: Vendas Digitais": ["modulo_12_vendas_digitais_e_redes_sociais_revisado.pdf"],
    "Alva - Módulo 13: Análise de Dados": ["modulo_13_analise_de_dados_e_metricas_revisado.pdf"],
    "Alva - Módulo 14: Liderança Vendas": ["modulo_14_lideranca_em_vendas_revisado.pdf"],
    "Alva - Módulo 15: Tendências e IA": ["modulo_15_tendencias_futuras_e_inovacao.pdf"],
    "Alva - Pacote Completo (16 Módulos)": ["Alva_Educacao_Pacote_Completo.pdf"],
    "Alva - Guia IA para Negócios": ["guia_ia_negocios.pdf"]
}

def send_email(customer_email, product_name, pdf_paths):
    try:
        logger.info(f"Iniciando envio de e-mail para {customer_email} - Produto: {product_name}")
        msg = MIMEMultipart()
        msg['From'] = f"Alva Educação <{SMTP_USER}>"
        msg['To'] = customer_email
        msg['Subject'] = f"Seu acesso ao curso: {product_name}"

        # MENSAGEM PERSONALIZADA PELO USUÁRIO
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
                logger.error(f"Arquivo NÃO encontrado: {path}")

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
                        product_name = payment_info.get("description")
                        if not product_name and payment_info.get("additional_info", {}).get("items"):
                            product_name = payment_info["additional_info"]["items"][0].get("title")
                        
                        if customer_email and product_name in PRODUCT_FILES:
                            pdf_paths = PRODUCT_FILES[product_name]
                            send_email(customer_email, product_name, pdf_paths)
            except Exception as e:
                logger.error(f"Erro no processamento do webhook: {e}")
                        
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
