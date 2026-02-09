import os
import smtplib
import requests
from flask import Flask, request, jsonify, send_from_directory
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = Flask(__name__, static_folder='.')

# --- Configurações do Mercado Pago ---
MP_ACCESS_TOKEN = "APP_USR-1698378827686338-020918-3eb43b92c8f40920f12aa6a2671b8c15-3187010530"

# --- Configuração de E-mail ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "henrifavila@gmail.com"
SMTP_PASSWORD = "iqdo mtbg vvmz pvuu"

# --- Mapeamento de Arquivos PDF ---
PRODUCT_FILES = {
    "Alva - Módulo 0: Segredo das Vendas": ["modules/modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf"],
    "Alva - Módulo 1: Relacionamentos": ["modules/modulo_1_construcao_relacionamentos_final_v7_final.pdf"],
    "Alva - Módulo 2: Geração de Leads": ["modules/modulo_2_prospeccao_e_geracao_de_leads.pdf"],
    "Alva - Módulo 3: Qualificação Leads": ["modules/modulo_3_qualificacao_e_necessidades.pdf"],
    "Alva - Módulo 4: Propostas de Valor": ["modules/modulo_4_propostas_de_valor_v2.pdf"],
    "Alva - Módulo 5: Persuasão e Influência": ["modules/modulo_5_persuasao_e_influencia_v3.pdf"],
    "Alva - Módulo 6: Apresentação Soluções": ["modules/modulo_6_apresentacao_e_demonstracoes.pdf"],
    "Alva - Módulo 7: Superação Objeções": ["modules/modulo_7_superacao_de_objecoes.pdf"],
    "Alva - Módulo 8: Técnicas Fechamento": ["modules/modulo_8_tecnicas_de_fechamento.pdf"],
    "Alva - Módulo 9: Negociação Contratos": ["modules/modulo_9_negociacao_e_gestao_de_contratos.pdf"],
    "Alva - Módulo 10: Follow-up Pós-venda": ["modules/modulo_10_follow_up_e_pos_venda.pdf"],
    "Alva - Módulo 11: Gestão CRM": ["modules/modulo_11_gestao_de_pipeline_e_crm_v2.pdf"],
    "Alva - Módulo 12: Vendas Digitais": ["modules/modulo_12_vendas_digitais_e_redes_sociais_revisado.pdf"],
    "Alva - Módulo 13: Análise de Dados": ["modules/modulo_13_analise_de_dados_e_metricas_revisado.pdf"],
    "Alva - Módulo 14: Liderança Vendas": ["modules/modulo_14_lideranca_em_vendas_revisado.pdf"],
    "Alva - Módulo 15: Tendências e IA": ["modules/modulo_15_tendencias_futuras_e_inovacao.pdf"],
    "Alva - Pacote Completo (16 Módulos)": [
        "modules/modulo_00_o_segredo_das_vendas_de_alto_impacto_revisado.pdf",
        "modules/modulo_1_construcao_relacionamentos_final_v7_final.pdf",
        "modules/modulo_2_prospeccao_e_geracao_de_leads.pdf",
        "modules/modulo_3_qualificacao_e_necessidades.pdf",
        "modules/modulo_4_propostas_de_valor_v2.pdf",
        "modules/modulo_5_persuasao_e_influencia_v3.pdf",
        "modules/modulo_6_apresentacao_e_demonstracoes.pdf",
        "modules/modulo_7_superacao_de_objecoes.pdf",
        "modules/modulo_8_tecnicas_de_fechamento.pdf",
        "modules/modulo_9_negociacao_e_gestao_de_contratos.pdf",
        "modules/modulo_10_follow_up_e_pos_venda.pdf",
        "modules/modulo_11_gestao_de_pipeline_e_crm_v2.pdf",
        "modules/modulo_12_vendas_digitais_e_redes_sociais_revisado.pdf",
        "modules/modulo_13_analise_de_dados_e_metricas_revisado.pdf",
        "modules/modulo_14_lideranca_em_vendas_revisado.pdf",
        "modules/modulo_15_tendencias_futuras_e_inovacao.pdf"
    ],
    "Alva - Guia IA para Negócios": ["modules/guia_ia_negocios.pdf"]
}

def send_email(customer_email, product_name, pdf_paths):
    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = customer_email
        msg['Subject'] = f"Seu acesso ao curso: {product_name}"

        body = f"Olá!\n\nObrigado por adquirir o {product_name} da Alva Educação.\n\nEm anexo, você encontrará o seu material em PDF.\n\nBons estudos!\nEquipe Alva Educação"
        msg.attach(MIMEText(body, 'plain'))

        for path in pdf_paths:
            if os.path.exists(path):
                with open(path, "rb") as f:
                    filename = os.path.basename(path)
                    part = MIMEApplication(f.read(), Name=filename)
                    part['Content-Disposition'] = f'attachment; filename="{filename}"'
                    msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

# Rota principal
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Rota para arquivos na pasta assets (Logos, etc)
@app.route('/assets/<path:filename>')
def serve_assets(filename):
    return send_from_directory('assets', filename)

# Rota para outros arquivos na raiz
@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('.', path)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    if data and data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        if payment_id:
            # Consultar o pagamento no Mercado Pago
            url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
            headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                payment_info = response.json()
                status = payment_info.get("status")
                
                if status == "approved":
                    customer_email = payment_info.get("payer", {}).get("email")
                    # Tentar pegar o nome do produto da descrição ou dos itens
                    product_name = payment_info.get("description")
                    if not product_name and payment_info.get("additional_info", {}).get("items"):
                        product_name = payment_info["additional_info"]["items"][0].get("title")
                    
                    if customer_email and product_name in PRODUCT_FILES:
                        pdf_paths = PRODUCT_FILES[product_name]
                        send_email(customer_email, product_name, pdf_paths)
                        
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
