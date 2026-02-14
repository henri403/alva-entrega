import os
import requests
import json
import threading
import time
import logging
from flask import Flask, request, jsonify, make_response, send_from_directory

# Configuração de Logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# Configurações
MERCADO_PAGO_TOKEN = os.getenv('MERCADO_PAGO_TOKEN')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

# Mapeamento de Produtos, Preços e Links de Download
PRODUCTS = {
    'modulo_0': {
        'name': 'O Segredo das Vendas de Alto Impacto', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/qbjOgyxFzhkYfJdU.pdf'
    },
    'modulo_1': {
        'name': 'Construção de Relacionamentos', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/TTKPrCbXJVRIsQtP.pdf'
    },
    'modulo_2': {
        'name': 'Prospecção e Geração de Leads', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/BGRZwllgyzWvlNzV.pdf'
    },
    'modulo_3': {
        'name': 'Qualificação de Leads e Identificação de Necessidades', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/EpSjmFJROBBJlbBg.pdf'
    },
    'modulo_4': {
        'name': 'Construção de Propostas de Valor', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/iHwQTRKAwtmSxXcp.pdf'
    },
    'modulo_5': {
        'name': 'Técnicas de Persuasão e Influência', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/DrYHWDMMJBIsHfOI.pdf'
    },
    'modulo_6': {
        'name': 'Apresentação de Soluções e Demonstrações', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/UcCubsDVGMEAThJS.pdf'
    },
    'modulo_7': {
        'name': 'Superação de Objeções', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/kGGLiXDDhPtVPnNC.pdf'
    },
    'modulo_8': {
        'name': 'Técnicas de Fechamento', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/dinTwgWlzjRcnAxs.pdf'
    },
    'modulo_9': {
        'name': 'Negociação e Gestão de Contratos', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/HWmhsCUcQoRluIoO.pdf'
    },
    'modulo_10': {
        'name': 'Follow-up e Pós-venda', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/HULBATwQDwiXWTrq.pdf'
    },
    'modulo_11': {
        'name': 'Gestão de Pipeline e CRM', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/qTrfXmQNGnIvTFsq.pdf'
    },
    'modulo_12': {
        'name': 'Vendas Digitais e Redes Sociais', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/aygypsoqZrJeyFtX.pdf'
    },
    'modulo_13': {
        'name': 'Análise de Dados e Métricas', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/kVciHLBFOiTzYxlQ.pdf'
    },
    'modulo_14': {
        'name': 'Liderança em Vendas', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/nCRACCiByAgNZRYP.pdf'
    },
    'modulo_15': {
        'name': 'Tendências Futuras e Inovação', 
        'price': 19.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/dlKNblRzjVqRQTVR.pdf'
    },
    'pacote_completo': {
        'name': 'Pacote Completo (16 Módulos)', 
        'price': 46.40,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/MGUhnWUmNgPDHqrM.pdf'
    },
    'guia_ia': {
        'name': 'Guia de IA para Negócios', 
        'price': 34.90,
        'download_url': 'https://files.manuscdn.com/user_upload_by_module/session_file/310519663109138853/FQFEKqILnOtaOepZ.pdf'
    },
}

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = make_response()
        return add_cors_headers(response)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/create_preference', methods=['POST'])
def create_preference():
    try:
        data = request.get_json()
        email = data.get('email')
        product_id = data.get('product_id')
        
        if not email or product_id not in PRODUCTS:
            return add_cors_headers(jsonify({'error': 'Dados inválidos'})), 400
        
        product = PRODUCTS[product_id]
        preference_data = {
            'items': [{'title': product['name'], 'unit_price': float(product['price']), 'quantity': 1, 'currency_id': 'BRL'}],
            'payer': {'email': email},
            'back_urls': {'success': 'https://alvaeducacao.com.br', 'failure': 'https://alvaeducacao.com.br'},
            'notification_url': 'https://alva-entrega.onrender.com/webhook',
            'external_reference': email,
            'auto_return': 'approved',
        }
        headers = {'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}', 'Content-Type': 'application/json'}
        response = requests.post('https://api.mercadopago.com/checkout/preferences', json=preference_data, headers=headers, timeout=15)
        
        if response.status_code in [200, 201]:
            return add_cors_headers(jsonify({'init_point': response.json().get('init_point')})), 200
        return add_cors_headers(jsonify({'error': 'Erro MP'})), 500
    except Exception as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500

def send_delivery_email(customer_email, product_name, download_url):
    """Envia o e-mail de entrega com o link de download"""
    if not RESEND_API_KEY:
        logger.error("RESEND_API_KEY não configurada!")
        return
    
    try:
        headers = {'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'}
        
        from_email = "Alva Educação <contato@alvaeducacao.com.br>"
        
        html_content = f"""
        <div style="font-family: sans-serif; max-width: 600px; margin: 0 auto; border: 1px solid #eee; padding: 30px; border-radius: 15px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #7c3aed; margin-bottom: 10px;">Seu Material Chegou! 🎉</h1>
                <p style="color: #666; font-size: 16px;">Obrigado por confiar na Alva Educação.</p>
            </div>
            
            <div style="background-color: #f9f7ff; padding: 20px; border-radius: 10px; margin-bottom: 25px; border-left: 5px solid #7c3aed;">
                <p style="margin: 0; color: #444;"><strong>Produto:</strong> {product_name}</p>
            </div>
            
            <p style="color: #444; line-height: 1.6;">Clique no botão abaixo para baixar o seu material agora mesmo:</p>
            
            <div style="text-align: center; margin: 35px 0;">
                <a href="{download_url}" style="background-color: #7c3aed; color: white; padding: 15px 35px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 18px; display: inline-block; box-shadow: 0 4px 6px rgba(124, 58, 237, 0.2);">
                    BAIXAR MEU PDF
                </a>
            </div>
            
            <p style="color: #888; font-size: 13px; text-align: center;">Se o botão não funcionar, copie e cole este link no seu navegador:<br>
            <a href="{download_url}" style="color: #7c3aed;">{download_url}</a></p>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="font-size: 12px; color: #999; text-align: center;">
                Este é um envio automático da Alva Educação.<br>
                Dúvidas? Responda a este e-mail ou entre em contato conosco.
            </p>
        </div>
        """
        
        payload = {
            'from': from_email,
            'to': customer_email,
            'subject': f'📥 Entrega: {product_name}',
            'html': html_content
        }
        
        res = requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=15)
        if res.status_code != 200:
            logger.warning(f"Falha ao enviar com domínio próprio. Tentando onboarding@resend.dev...")
            payload['from'] = "Alva Educação <onboarding@resend.dev>"
            requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=15)
        
        logger.info(f"E-mail de entrega enviado para {customer_email} com o link do produto {product_name}")
    except Exception as e:
        logger.error(f"Erro ao enviar e-mail: {str(e)}")

def process_payment(payment_id):
    """Busca detalhes do pagamento e dispara entrega"""
    headers = {'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}'}
    for _ in range(10):
        try:
            res = requests.get(f'https://api.mercadopago.com/v1/payments/{payment_id}', headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == 'approved':
                    email = data.get('external_reference') or data.get('payer', {}).get('email')
                    items = data.get('additional_info', {}).get('items', [])
                    
                    # Tenta encontrar o produto pelo título ou ID
                    product_name = 'Produto Alva Educação'
                    download_url = ''
                    
                    if items:
                        title = items[0].get('title')
                        # Busca o produto correspondente no nosso dicionário
                        for pid, pinfo in PRODUCTS.items():
                            if pinfo['name'] == title:
                                product_name = pinfo['name']
                                download_url = pinfo['download_url']
                                break
                    
                    if email and email != 'None' and download_url:
                        send_delivery_email(email, product_name, download_url)
                        break
            time.sleep(30)
        except:
            time.sleep(30)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data.get('type') == 'payment' or data.get('action') in ['payment.created', 'payment.updated']:
            payment_id = data.get('data', {}).get('id') or data.get('id')
            if payment_id:
                logger.info(f"Processando pagamento aprovado: {payment_id}")
                threading.Thread(target=process_payment, args=(payment_id,)).start()
    except Exception as e:
        logger.error(f"Erro no Webhook: {str(e)}")
    
    return add_cors_headers(jsonify({'status': 'received'})), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
