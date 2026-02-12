import os
import requests
import json
import threading
import time
from flask import Flask, request, jsonify, make_response, send_from_directory

app = Flask(__name__, static_folder='.')

# Configurações
MERCADO_PAGO_TOKEN = os.getenv('MERCADO_PAGO_TOKEN')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

# Produtos com preços
PRODUCTS = {
    'modulo_0': {'name': 'O Segredo das Vendas de Alto Impacto', 'price': 19.90},
    'modulo_1': {'name': 'Construção de Relacionamentos', 'price': 19.90},
    'modulo_2': {'name': 'Prospecção e Geração de Leads', 'price': 19.90},
    'modulo_3': {'name': 'Qualificação de Leads', 'price': 19.90},
    'modulo_4': {'name': 'Construção de Propostas de Valor', 'price': 19.90},
    'modulo_5': {'name': 'Técnicas de Persuasão', 'price': 19.90},
    'modulo_6': {'name': 'Apresentação de Soluções', 'price': 19.90},
    'modulo_7': {'name': 'Superação de Objeções', 'price': 19.90},
    'modulo_8': {'name': 'Técnicas de Fechamento', 'price': 19.90},
    'modulo_9': {'name': 'Negociação e Contratos', 'price': 19.90},
    'modulo_10': {'name': 'Follow-up e Pós-venda', 'price': 19.90},
    'modulo_11': {'name': 'Gestão de Pipeline e CRM', 'price': 19.90},
    'modulo_12': {'name': 'Vendas Digitais', 'price': 19.90},
    'modulo_13': {'name': 'Análise de Dados', 'price': 19.90},
    'modulo_14': {'name': 'Liderança em Vendas', 'price': 19.90},
    'modulo_15': {'name': 'Tendências e Inovação', 'price': 19.90},
    'pacote_completo': {'name': 'Pacote Completo (16 Módulos)', 'price': 46.40},
    'guia_ia': {'name': 'Guia de IA para Negócios', 'price': 34.90},
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
        response = requests.post('https://api.mercadopago.com/checkout/preferences', json=preference_data, headers=headers, timeout=10)
        
        if response.status_code in [200, 201]:
            return add_cors_headers(jsonify({'init_point': response.json().get('init_point')})), 200
        return add_cors_headers(jsonify({'error': 'Erro no Mercado Pago'})), 500
    except Exception as e:
        return add_cors_headers(jsonify({'error': str(e)})), 500

def send_pdf_email(customer_email, product_name):
    try:
        headers = {'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'}
        payload = {
            'from': 'contato@alvaeducacao.com.br',
            'to': customer_email,
            'subject': f'Seu Material - {product_name}',
            'html': f'<h2>Obrigado!</h2><p>Você adquiriu: {product_name}. Seu material está sendo processado.</p>'
        }
        requests.post('https://api.resend.com/emails', json=payload, headers=headers, timeout=10)
    except: pass

def process_payment_background(payment_id):
    headers = {'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}'}
    for _ in range(10):
        try:
            res = requests.get(f'https://api.mercadopago.com/v1/payments/{payment_id}', headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                if data.get('status') == 'approved':
                    email = data.get('payer', {}).get('email')
                    items = data.get('additional_info', {}).get('items', [])
                    name = items[0].get('title', 'Produto') if items else 'Produto'
                    send_pdf_email(email, name)
                    break
            time.sleep(30)
        except: time.sleep(30)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        if data.get('action') in ['payment.created', 'payment.updated']:
            pid = data.get('data', {}).get('id')
            threading.Thread(target=process_payment_background, args=(pid,)).start()
    except: pass
    return add_cors_headers(jsonify({'status': 'received'})), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
