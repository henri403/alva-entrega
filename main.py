import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from flask import Flask, request, jsonify

# Configurações do Flask
app = Flask(__name__)

# Variáveis de Ambiente
EMAIL_USER = os.environ.get('EMAIL_USER')
EMAIL_PASS = os.environ.get('EMAIL_PASS')
SENDER_EMAIL = EMAIL_USER
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587

# Mapeamento de ID do produto para nome do arquivo PDF
# O Mercado Pago envia o ID do item comprado.
# O nome do arquivo deve ser module_XX.pdf
PRODUCT_MAP = {
    # Módulos Individuais (R$ 19,90)
    "ID_PRODUTO_MODULO_00": "modules/module_00.pdf",
    "ID_PRODUTO_MODULO_01": "modules/module_01.pdf",
    "ID_PRODUTO_MODULO_02": "modules/module_02.pdf",
    "ID_PRODUTO_MODULO_03": "modules/module_03.pdf",
    "ID_PRODUTO_MODULO_04": "modules/module_04.pdf",
    "ID_PRODUTO_MODULO_05": "modules/module_05.pdf",
    "ID_PRODUTO_MODULO_06": "modules/module_06.pdf",
    "ID_PRODUTO_MODULO_07": "modules/module_07.pdf",
    "ID_PRODUTO_MODULO_08": "modules/module_08.pdf",
    "ID_PRODUTO_MODULO_09": "modules/module_09.pdf",
    "ID_PRODUTO_MODULO_10": "modules/module_10.pdf",
    "ID_PRODUTO_MODULO_11": "modules/module_11.pdf",
    "ID_PRODUTO_MODULO_12": "modules/module_12.pdf",
    "ID_PRODUTO_MODULO_13": "modules/module_13.pdf",
    "ID_PRODUTO_MODULO_14": "modules/module_14.pdf",
    "ID_PRODUTO_MODULO_15": "modules/module_15.pdf",
    
    # Pacote Completo (R$ 29,90) - Este ID deve ser o ID do item do Mercado Pago
    "ID_PRODUTO_PACOTE_COMPLETO": [
        "modules/module_00.pdf", "modules/module_01.pdf", "modules/module_02.pdf", "modules/module_03.pdf",
        "modules/module_04.pdf", "modules/module_05.pdf", "modules/module_06.pdf", "modules/module_07.pdf",
        "modules/module_08.pdf", "modules/module_09.pdf", "modules/module_10.pdf", "modules/module_11.pdf",
        "modules/module_12.pdf", "modules/module_13.pdf", "modules/module_14.pdf", "modules/module_15.pdf"
    ]
}

def send_email_with_attachments(recipient_email, subject, body, file_paths):
    """Envia um e-mail com anexos PDF."""
    if not EMAIL_USER or not EMAIL_PASS:
        print("Erro: Variáveis de ambiente EMAIL_USER ou EMAIL_PASS não configuradas.")
        return False

    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'html'))

    for file_path in file_paths:
        # Ajusta o caminho para o Render
        render_path = os.path.join(os.getcwd(), file_path)
        
        try:
            with open(render_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=os.path.basename(file_path))
                msg.attach(attach)
        except FileNotFoundError:
            print(f"Erro: Arquivo não encontrado: {render_path}")
            return False

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False

@app.route('/', methods=['GET'])
def home():
    """Rota de teste para verificar se o servidor está online."""
    return "Servidor de Entrega de PDFs da Alva Educação está online.", 200

@app.route('/test', methods=['GET'])
def test_route():
    """Rota de teste para verificar se o servidor está online."""
    return "Servidor de Entrega de PDFs da Alva Educação está online e rotas funcionando.", 200

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe notificações do Mercado Pago."""
    try:
        data = request.json
    except Exception as e:
        print(f"Erro ao ler JSON: {e}")
        return jsonify({"status": "error", "message": "Invalid JSON"}), 400

    # 1. Verifica se é uma notificação de pagamento
    if data.get('topic') != 'payment':
        return jsonify({"status": "ok", "message": "Not a payment notification"}), 200

    # 2. Verifica se o pagamento foi aprovado
    if data.get('data', {}).get('status') != 'approved':
        return jsonify({"status": "ok", "message": "Payment not approved"}), 200

    # 3. Obtém o ID do pagamento para buscar detalhes
    payment_id = data.get('data', {}).get('id')
    if not payment_id:
        return jsonify({"status": "error", "message": "Payment ID not found"}), 400

    # --- SIMULAÇÃO DE BUSCA DE DETALHES DO PAGAMENTO ---
    # Em um ambiente real, você faria uma requisição à API do Mercado Pago
    # para obter os detalhes do pagamento (itens, e-mail do comprador).
    # Como não temos as credenciais da API, vamos simular os dados que precisamos.
    
    # Simulação de dados do pagamento (Você deve substituir pelos dados reais)
    # IMPORTANTE: O ID do item (item_id) é o que você precisa mapear no PRODUCT_MAP
    
    # Exemplo de um item individual
    # item_id = "ID_PRODUTO_MODULO_00" 
    # buyer_email = "comprador@exemplo.com"
    
    # Exemplo de um pacote completo
    item_id = "ID_PRODUTO_PACOTE_COMPLETO" 
    buyer_email = "comprador@exemplo.com" # Substitua pelo e-mail real do comprador
    
    # --- FIM DA SIMULAÇÃO ---

    # 4. Mapeia o ID do produto para o(s) arquivo(s) PDF
    file_info = PRODUCT_MAP.get(item_id)
    
    if not file_info:
        print(f"Erro: ID do produto não mapeado: {item_id}")
        return jsonify({"status": "error", "message": "Product ID not mapped"}), 200

    # Garante que file_info seja uma lista
    file_paths = file_info if isinstance(file_info, list) else [file_info]
    
    # 5. Envia o e-mail
    subject = "Seu Módulo(s) da Alva Educação Chegou!"
    body = f"""
    <html>
    <body>
        <p>Olá,</p>
        <p>Parabéns pela sua compra! Seu(s) módulo(s) da Alva Educação está(ão) anexo(s) a este e-mail.</p>
        <p>Qualquer dúvida, entre em contato.</p>
        <p>Atenciosamente,</p>
        <p>Equipe Alva Educação</p>
    </body>
    </html>
    """
    
    email_sent = send_email_with_attachments(buyer_email, subject, body, file_paths)

    if email_sent:
        return jsonify({"status": "ok", "message": "Email sent successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Failed to send email"}), 500

if __name__ == '__main__':
    # Apenas para testes locais. No Render, o gunicorn executa o app.
    app.run(debug=True)
