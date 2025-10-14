from flask import Flask, request, jsonify
import requests
import io
import os
import json
from openai import OpenAI

app = Flask(__name__)

# Cliente OpenAI será inicializado quando necessário
client = None

def get_openai_client():
    global client
    if client is None:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    return client

@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        data = request.get_json()
        if not data or 'twilio_url' not in data:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" é obrigatório'}), 400
        
        twilio_url = data['twilio_url']
        print(f"Baixando áudio de: {twilio_url}")
        audio_response = requests.get(twilio_url, timeout=30)
        if audio_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar áudio do Twilio: {audio_response.status_code}'}), 400
        
        audio_buffer = io.BytesIO(audio_response.content)
        audio_buffer.name = "audio.ogg"
        print("Enviando áudio para OpenAI Whisper...")
        openai_client = get_openai_client()
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer
        )
        
        return jsonify({'success': True, 'transcription': transcript.text})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Erro ao fazer requisição: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        data = request.get_json()
        if not data or 'twilio_url' not in data:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" é obrigatório'}), 400
        
        twilio_url = data['twilio_url']
        prompt = data.get('prompt', 'Descreva esta imagem em detalhes.')
        print(f"Baixando imagem de: {twilio_url}")
        image_response = requests.get(twilio_url, timeout=30)
        if image_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar imagem do Twilio: {image_response.status_code}'}), 400
        
        import base64
        image_base64 = base64.b64encode(image_response.content).decode('utf-8')
        content_type = image_response.headers.get('Content-Type', 'image/jpeg')
        print("Enviando imagem para GPT-4 Vision...")
        openai_client = get_openai_client()
        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{content_type};base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return jsonify({'success': True, 'analysis': response.choices[0].message.content})
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Erro ao fazer requisição: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/extract-document', methods=['POST'])
def extract_document():
    try:
        data = request.get_json()
        if not data or 'twilio_url' not in data:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" é obrigatório'}), 400
        
        twilio_url = data['twilio_url']
        should_analyze = data.get('analyze', False)
        print(f"Baixando documento de: {twilio_url}")
        doc_response = requests.get(twilio_url, timeout=30)
        if doc_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar documento do Twilio: {doc_response.status_code}'}), 400
        
        content_type = doc_response.headers.get('Content-Type', '')
        extracted_text = ""
        
        if 'pdf' in content_type.lower() or twilio_url.lower().endswith('.pdf'):
            import PyPDF2
            pdf_buffer = io.BytesIO(doc_response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif 'word' in content_type.lower() or twilio_url.lower().endswith(('.doc', '.docx')):
            import docx
            doc_buffer = io.BytesIO(doc_response.content)
            doc = docx.Document(doc_buffer)
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        else:
            try:
                extracted_text = doc_response.content.decode('utf-8')
            except:
                return jsonify({'success': False, 'error': f'Tipo de documento não suportado: {content_type}'}), 400
        
        result = {'success': True, 'text': extracted_text.strip()}
        if should_analyze and extracted_text.strip():
            print("Analisando documento com GPT-4...")
            openai_client = get_openai_client()
            analysis_response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "user",
                        "content": f"Analise e resuma o seguinte documento:\n\n{extracted_text[:4000]}"
                    }
                ],
                max_tokens=1000
            )
            result['analysis'] = analysis_response.choices[0].message.content
        
        return jsonify(result)
    except requests.exceptions.RequestException as e:
        return jsonify({'success': False, 'error': f'Erro ao fazer requisição: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# ==================== FUNÇÕES AUXILIARES CHATWOOT ====================

def send_to_chatwoot_new(config, content, file_data=None):
    headers = {
        'Content-Type': 'application/json',
        'api_access_token': config['api_token']
    }
    data = {
        'inbox_id': config['inbox_id'],
        'source_id': config['source_id'],
        'message': {
            'content': content,
            'message_type': 'incoming'
        }
    }
    url = f"{config['api_url']}/api/v1/accounts/{config['account_id']}/conversations"

    # Logs de depuração
    print("🚀 Enviando para Chatwoot (nova conversa):")
    print(f"🔗 URL: {url}")
    print(f"📦 Headers: {headers}")
    print(f"📝 Body:\n{json.dumps(data, indent=2)}")

    try:
        response = requests.post(url, headers=headers, json=data)
        print("📡 Status da resposta:", response.status_code)
        print("📨 Corpo da resposta:", response.text)

        if response.status_code in (200, 201):
            # Retornar a conversa criada
            resp_json = response.json()
            # Dependendo de como a resposta vem, pode ser "id" ou dentro de outro objeto
            conversation_id = resp_json.get('id') or resp_json.get('conversation', {}).get('id')
            return conversation_id
        else:
            return None
    except Exception as e:
        print("💥 Erro ao enviar para Chatwoot:", str(e))
        return None

def send_to_chatwoot_existing(config, conversation_id, content, file_data=None):
    headers = {
        'Content-Type': 'application/json',
        'api_access_token': config['api_token']
    }
    data = {
        'content': content,
        'message_type': 'incoming'
    }
    url = f"{config['api_url']}/api/v1/accounts/{config['account_id']}/conversations/{conversation_id}/messages"

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code in (200, 201):
            return True
        else:
            print(f"Erro ao enviar mensagem existente: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print("💥 Erro ao enviar mensagem existente:", str(e))
        return False

FIXED_TEXTS = {
    'audio': 'Esta mensagem é a transcrição de um áudio que o cliente enviou para você. Responda com naturalidade e se for necessário trate a mensagem como se de fato estivesse recebido o áudio. Mensagem: ',
    'image': 'O cliente enviou uma imagem e o que consta nela segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Imagem: ',
    'document': 'O cliente enviou um documento e o que consta nele segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Documento: ',
    'video': 'O cliente enviou um vídeo e o que consta nele segue abaixo. Siga essas orientações: Caso o cliente não tenha informado o motivo para o envio do vídeo, questione. Caso seja uma reclamação informe que um atentendente humano irá verificar o ocorrido. Caso seja um elogio agradeça com entusiasmo: ',
    'location': 'Você recebeu uma localização. Caso tenha solicitado o endereço e o cliente está lhe enviando a localização, agradeça pois nos ajudará bastante na entrega, mas reforce a necessidade de envio do endereço por escrito. Se for outra situação, apenas agradeça.'
}

@app.route('/process-and-send-new', methods=['POST'])
def process_and_send_new():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Body vazio'}), 400

        message_type = data.get('message_type', '').lower()
        chatwoot_config = data.get('chatwoot', {})

        if not message_type:
            return jsonify({'success': False, 'error': 'Campo "message_type" é obrigatório'}), 400

        conteudo = ""
        file_data = None

        if message_type == 'text':
            text_content = data.get('text_content', '')
            if not text_content:
                return jsonify({'success': False, 'error': 'Campo "text_content" obrigatório para type=text'}), 400

            conteudo = text_content
            conversation_id = send_to_chatwoot_new(chatwoot_config, conteudo)
            return jsonify({'success': True, 'conteudo': conteudo, 'conversation_id': conversation_id, 'chatwoot_sent': conversation_id is not None})

        elif message_type == 'location':
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            if not latitude or not longitude:
                return jsonify({'success': False, 'error': 'Campos "latitude" e "longitude" obrigatórios para type=location'}), 400

            conteudo = FIXED_TEXTS['location']
            location_text = f"📍 Localização: https://www.google.com/maps?q={latitude},{longitude}"
            conversation_id = send_to_chatwoot_new(chatwoot_config, location_text)
            return jsonify({'success': True, 'conteudo': conteudo, 'conversation_id': conversation_id, 'chatwoot_sent': conversation_id is not None})

        twilio_url = data.get('twilio_url')
        if not twilio_url:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" obrigatório para este tipo'}), 400

        print(f"Baixando arquivo de: {twilio_url}")
        file_response = requests.get(twilio_url, timeout=30)
        if file_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar arquivo: {file_response.status_code}'}), 400

        file_bytes = file_response.content
        content_type = file_response.headers.get('Content-Type', 'application/octet-stream')

        if message_type == 'audio':
            audio_buffer = io.BytesIO(file_bytes)
            audio_buffer.name = "audio.ogg"
            openai_client = get_openai_client()
            transcript = openai_client.audio.transcriptions.create(model="whisper-1", file=audio_buffer)
            conteudo = FIXED_TEXTS['audio'] + transcript.text
            file_data = ('audio.ogg', file_bytes, content_type)

        elif message_type == 'image':
            import base64
            image_base64 = base64.b64encode(file_bytes).decode('utf-8')
            openai_client = get_openai_client()
            response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Descreva esta imagem em detalhes."},
                        {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{image_base64}"}}
                    ]
                }],
                max_tokens=1000
            )
            conteudo = FIXED_TEXTS['image'] + response.choices[0].message.content
            file_data = ('image.jpg', file_bytes, content_type)

        elif message_type == 'document':
            import PyPDF2
            pdf_buffer = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            conteudo = FIXED_TEXTS['document
