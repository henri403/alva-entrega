import os
import requests
import json
import threading
import time
import logging
from flask import Flask, request, jsonify, make_response, send_from_directory

# Configuração de Logs para ver o erro real no Render
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='.')

# Configurações
MERCADO_PAGO_TOKEN = os.getenv('MERCADO_PAGO_TOKEN')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')

# Produtos com preços (Verifique se os IDs batem com o index.html)
PRODUCTS = {
    'modulo_0': {'name': 'O Segredo das Vendas de Alto Impacto', 'price': 19.90},
    'modulo_1': {'name': 'Construção de Relacionamentos', 'price': 19.90},
    'modulo_2': {'name': 'Prospecção e Geração de Leads', 'price': 19.90},
    'modulo_3': {'name': 'Qualificação de Leads e Identificação de Necessidades', 'price': 19.90},
    'modulo_4': {'name': 'Construção de Propostas de Valor', 'price': 19.90},
    'modulo_5': {'name': 'Técnicas de Persuasão e Influência', 'price': 19.90},
    'modulo_6': {'name': 'Apresentação de Soluções e Demonstrações', 'price': 19.90},
    'modulo_7': {'name': 'Superação de Objeções', 'price': 19.90},
    'modulo_8': {'name': 'Técnicas de Fechamento', 'price': 19.90},
    'modulo_9': {'name': 'Negociação e Gestão de Contratos', 'price': 19.90},
    'modulo_10': {'name': 'Follow-up e Pós-venda', 'price': 19.90},
    'modulo_11': {'name': 'Gestão de Pipeline e CRM', 'price': 19.90},
    'modulo_12': {'name': 'Vendas Digitais e Redes Sociais', 'price': 19.90},
    'modulo_13': {'name': 'Análise de Dados e Métricas', 'price': 19.90},
    'modulo_14': {'name': 'Liderança em Vendas', 'price': 19.90},
    'modulo_15': {'name': 'Tendências Futuras e Inovação', 'price': 19.90},
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
        
        logger.info(f"Tentativa de compra: Email={email}, Produto={product_id}")

        if not email or product_id not in PRODUCTS:
            logger.error(f"Dados inválidos recebidos: {data}")
            return add_cors_headers(jsonify({'error': 'Dados inválidos'})), 400
        
        if not MERCADO_PAGO_TOKEN:
            logger.error("ERRO CRÍTICO: MERCADO_PAGO_TOKEN não configurado no Render!")
            return add_cors_headers(jsonify({'error': 'Configuração do servidor incompleta'})), 500

        product = PRODUCTS[product_id]
        
        preference_data = {
            'items': [{
                'title': product['name'],
                'unit_price': float(product['price']),
                'quantity': 1,
                'currency_id': 'BRL'
            }],
            'payer': {'email': email},
            'back_urls': {
                'success': 'https://alvaeducacao.com.br',
                'failure': 'https://alvaeducacao.com.br'
            },
            'notification_url': 'https://alva-entrega.onrender.com/webhook',
            'external_reference': email,
            'auto_return': 'approved',
        }
        
        headers = {
            'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        logger.info("Enviando requisição para o Mercado Pago...")
        response = requests.post(
            'https://api.mercadopago.com/checkout/preferences',
            json=preference_data,
            headers=headers,
            timeout=15
        )
        
        if response.status_code in [200, 201]:
            init_point = response.json().get('init_point')
            logger.info(f"Sucesso! Link gerado: {init_point}")
            return add_cors_headers(jsonify({'init_point': init_point})), 200
        else:
            logger.error(f"Erro do Mercado Pago (Status {response.status_code}): {response.text}")
            return add_cors_headers(jsonify({'error': f'Erro MP: {response.status_code}'})), 500
            
    except Exception as e:
        logger.exception(f"Erro interno ao criar preferência: {str(e)}")
        return add_cors_headers(jsonify({'error': str(e)})), 500

# Webhook e Envio de E-mail simplificados para estabilidade
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        logger.info(f"Webhook recebido: {data}")
        return add_cors_headers(jsonify({'status': 'received'})), 200
    except:
        return add_cors_headers(jsonify({'status': 'received'})), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
