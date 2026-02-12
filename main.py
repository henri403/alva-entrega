import os
import requests
import json
import threading
import time
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)

# Configurações
MERCADO_PAGO_TOKEN = os.getenv('MERCADO_PAGO_TOKEN')
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
ADMIN_EMAIL = 'alvaeducacao@gmail.com'

# Produtos com preços
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

@app.route('/', methods=['GET'])
def home():
    return "Servidor Alva Educação ativo! ✅"

@app.route('/create_preference', methods=['POST'])
def create_preference():
    """Cria uma preferência de pagamento no Mercado Pago"""
    try:
        data = request.get_json()
        email = data.get('email')
        product_id = data.get('product_id')

        if not email or not product_id:
            return add_cors_headers(jsonify({'error': 'E-mail e produto são obrigatórios'})), 400

        # Validar produto
        if product_id not in PRODUCTS:
            return add_cors_headers(jsonify({'error': 'Produto não encontrado'})), 400

        product = PRODUCTS[product_id]
        price = float(product['price'])

        # Criar preferência
        preference_data = {
            'items': [{
                'title': product['name'],
                'unit_price': price,
                'quantity': 1,
                'currency_id': 'BRL'
            }],
            'payer': {
                'email': email,
            },
            'back_urls': {
                'success': 'https://alvaeducacao.com.br',
                'failure': 'https://alvaeducacao.com.br',
                'pending': 'https://alvaeducacao.com.br',
            },
            'notification_url': 'https://alva-entrega.onrender.com/webhook',
            'external_reference': email,
            'auto_return': 'approved',
        }

        headers = {
            'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}',
            'Content-Type': 'application/json',
        }

        response = requests.post(
            'https://api.mercadopago.com/checkout/preferences',
            json=preference_data,
            headers=headers,
            timeout=10
        )

        if response.status_code not in [200, 201]:
            print(f"[ERROR] Mercado Pago {response.status_code}: {response.text}")
            return add_cors_headers(jsonify({'error': 'Falha ao gerar link de pagamento'})), 500

        preference = response.json()
        init_point = preference.get('init_point')

        if not init_point:
            print(f"[ERROR] Sem init_point: {preference}")
            return add_cors_headers(jsonify({'error': 'Link não gerado'})), 500

        print(f"[INFO] Preferência criada: {email} - {product['name']} - R$ {price}")
        return add_cors_headers(jsonify({'init_point': init_point})), 200

    except Exception as e:
        print(f"[ERROR] Erro ao criar preferência: {str(e)}")
        return add_cors_headers(jsonify({'error': str(e)})), 500

def send_pdf_email(customer_email, product_name):
    """Envia o PDF do produto para o cliente"""
    try:
        headers = {
            'Authorization': f'Bearer {RESEND_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        email_body = f"""
        <h2>Parabéns pela sua compra! 🎉</h2>
        <p>Você adquiriu: <strong>{product_name}</strong></p>
        <p>Seu material está pronto para download. Aproveite ao máximo!</p>
        <p>Qualquer dúvida, nos contate.</p>
        <p>Abraços,<br>Alva Educação</p>
        """
        
        payload = {
            'from': 'contato@alvaeducacao.com.br',
            'to': customer_email,
            'subject': f'Seu Material - {product_name}',
            'html': email_body,
        }
        
        response = requests.post(
            'https://api.resend.com/emails',
            json=payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"[INFO] E-mail enviado para {customer_email}")
            return True
        else:
            print(f"[ERROR] Resend retornou {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"[ERROR] Falha ao enviar e-mail: {str(e)}")
        return False

def get_payment_with_retry(payment_id, max_attempts=20):
    """Busca dados do pagamento com retry"""
    headers = {'Authorization': f'Bearer {MERCADO_PAGO_TOKEN}'}
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                f'https://api.mercadopago.com/v1/payments/{payment_id}',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                email = data.get('payer', {}).get('email')
                status = data.get('status')
                
                if email and email != 'None' and status == 'approved':
                    return data
                
                print(f"[INFO] Tentativa {attempt + 1}: Aguardando dados...")
                time.sleep(30)
            else:
                time.sleep(30)
        except Exception as e:
            print(f"[ERROR] Erro na tentativa {attempt + 1}: {str(e)}")
            time.sleep(30)
    
    return None

def process_payment_background(payment_id):
    """Processa o pagamento em segundo plano"""
    print(f"[INFO] Iniciando busca para Payment: {payment_id}")
    
    payment_data = get_payment_with_retry(payment_id)
    
    if not payment_data:
        print(f"[ERROR] Não foi possível obter dados após 10 minutos")
        return
    
    email = payment_data.get('payer', {}).get('email')
    items = payment_data.get('additional_info', {}).get('items', [])
    
    if not items:
        # Fallback para buscar o nome do produto se items estiver vazio
        items = payment_data.get('description', 'Produto')
        product_name = items if isinstance(items, str) else "Produto"
    else:
        product_name = items[0].get('title', 'Produto')
        
    if email:
        print(f"[INFO] Enviando PDF para {email}: {product_name}")
        send_pdf_email(email, product_name)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Recebe notificações do Mercado Pago"""
    try:
        data = request.get_json()
        action = data.get('action')
        
        if action in ['payment.created', 'payment.updated']:
            payment_id = data.get('data', {}).get('id')
            print(f"[INFO] Webhook: {action} - Payment ID: {payment_id}")
            
            # Processar em segundo plano
            threading.Thread(target=process_payment_background, args=(payment_id,)).start()
            return add_cors_headers(jsonify({'status': 'received'})), 200
        
        return add_cors_headers(jsonify({'status': 'received'})), 200
    
    except Exception as e:
        print(f"[ERROR] Erro no webhook: {str(e)}")
        return add_cors_headers(jsonify({'error': str(e)})), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
