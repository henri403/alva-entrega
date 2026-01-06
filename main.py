from flask import Flask, request, jsonify
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

app = Flask(__name__)

# --- Configuração de E-mail (substitua com seus dados) ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "henrifavila@gmail.com"
SMTP_PASSWORD = "iqdo mtbg vvmz pvuu"

# --- Mapeamento de Módulos ---
MODULES = {
    0: {
        "name": "Módulo 0: O Segredo das Vendas de Alto Impacto",
        "path": "/home/ubuntu/modules/module_00.pdf"
    },
    1: {
        "name": "Módulo 1: Prospecção e Geração de Leads",
        "path": "/home/ubuntu/modules/module_01.pdf"
    },
    2: {
        "name": "Módulo 2: Abordagem e Primeiro Contato",
        "path": "/home/ubuntu/modules/module_02.pdf"
    },
    3: {
        "name": "Módulo 3: Qualificação de Leads e Identificação de Necessidades",
        "path": "/home/ubuntu/modules/module_03.pdf"
    },
    4: {
        "name": "Módulo 4: Construção de Propostas de Valor",
        "path": "/home/ubuntu/modules/module_04.pdf"
    },
    5: {
        "name": "Módulo 5: Técnicas de Persuasão e Influência",
        "path": "/home/ubuntu/modules/module_05.pdf"
    },
    6: {
        "name": "Módulo 6: Apresentação de Soluções e Demonstrações",
        "path": "/home/ubuntu/modules/module_06.pdf"
    },
    7: {
        "name": "Módulo 7: Superação de Objeções",
        "path": "/home/ubuntu/modules/module_07.pdf"
    },
    8: {
        "name": "Módulo 8: Técnicas de Fechamento",
        "path": "/home/ubuntu/modules/module_08.pdf"
    },
    9: {
        "name": "Módulo 9: Negociação e Gestão de Contratos",
        "path": "/home/ubuntu/modules/module_09.pdf"
    },
    10: {
        "name": "Módulo 10: Follow-up e Pós-Venda",
        "path": "/home/ubuntu/modules/module_10.pdf"
    },
    11: {
        "name": "Módulo 11: Gestão de Pipeline e CRM",
        "path": "/home/ubuntu/modules/module_11.pdf"
    },
    12: {
        "name": "Módulo 12: Vendas Digitais e Redes Sociais",
        "path": "/home/ubuntu/modules/module_12.pdf"
    },
    13: {
        "name": "Módulo 13: Análise de Dados e Métricas",
        "path": "/home/ubuntu/modules/module_13.pdf"
    },
    14: {
        "name": "Módulo 14: Liderança em Vendas",
        "path": "/home/ubuntu/modules/module_14.pdf"
    },
    15: {
        "name": "Módulo 15: Tendências Futuras e Inovação",
        "path": "/home/ubuntu/modules/module_15.pdf"
    }
}

def send_module_email(customer_email, module_id):
    module_info = MODULES.get(module_id)
    if not module_info:
        return False, "Módulo não encontrado."

    try:
        msg = MIMEMultipart()
        msg['From'] = SMTP_USER
        msg['To'] = customer_email
        msg['Subject'] = f"Seu Módulo de Vendas: {module_info['name']}"

        body = f"Olá,\n\nObrigado por sua compra!\n\nEm anexo, você encontrará o seu {module_info['name']}.\n\nBons estudos!\n\nAtenciosamente,\nEquipe de Vendas de Alto Impacto"
        msg.attach(MIMEText(body, 'plain'))

        with open(module_info['path'], "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            "Content-Disposition",
            f"attachment; filename= {module_info['name']}.pdf",
        )
        msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        text = msg.as_string()
        server.sendmail(SMTP_USER, customer_email, text)
        server.quit()
        return True, "E-mail enviado com sucesso!"
    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")
        return False, "Erro ao enviar e-mail."

@app.route('/purchase', methods=['POST'])
def purchase_module():
    data = request.get_json()
    customer_email = data.get('email')
    module_id = data.get('module_id')

    if not customer_email or module_id is None:
        return jsonify({"error": "E-mail e ID do módulo são obrigatórios."}), 400

    success, message = send_module_email(customer_email, module_id)

    if success:
        return jsonify({"message": message}), 200
    else:
        return jsonify({"error": message}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
