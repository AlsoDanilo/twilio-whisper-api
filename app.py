from flask import Flask, request, jsonify
import requests
import io
import os
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
    """
    Endpoint que recebe uma URL do Twilio, baixa o áudio e transcreve usando OpenAI Whisper
    
    Body esperado:
    {
        "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/..."
    }
    
    Resposta:
    {
        "success": true,
        "transcription": "texto transcrito aqui"
    }
    """
    try:
        # Pega a URL do Twilio do body da requisição
        data = request.get_json()
        
        if not data or 'twilio_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Campo "twilio_url" é obrigatório'
            }), 400
        
        twilio_url = data['twilio_url']
        
        # Baixa o áudio da URL do Twilio
        print(f"Baixando áudio de: {twilio_url}")
        audio_response = requests.get(twilio_url, timeout=30)
        
        if audio_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Erro ao baixar áudio do Twilio: {audio_response.status_code}'
            }), 400
        
        # Cria um buffer BytesIO com o conteúdo do áudio
        audio_buffer = io.BytesIO(audio_response.content)
        audio_buffer.name = "audio.ogg"  # Define o nome com extensão
        
        # Envia para OpenAI Whisper
        print("Enviando áudio para OpenAI Whisper...")
        openai_client = get_openai_client()
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer
        )
        
        # Retorna a transcrição
        return jsonify({
            'success': True,
            'transcription': transcript.text
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao fazer requisição: {str(e)}'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    """
    Endpoint que recebe uma URL do Twilio com imagem e analisa usando GPT-4 Vision
    
    Body esperado:
    {
        "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/...",
        "prompt": "O que tem nesta imagem?" (opcional)
    }
    
    Resposta:
    {
        "success": true,
        "analysis": "descrição da imagem"
    }
    """
    try:
        # Pega a URL do Twilio do body da requisição
        data = request.get_json()
        
        if not data or 'twilio_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Campo "twilio_url" é obrigatório'
            }), 400
        
        twilio_url = data['twilio_url']
        prompt = data.get('prompt', 'Descreva esta imagem em detalhes.')
        
        # Baixa a imagem da URL do Twilio
        print(f"Baixando imagem de: {twilio_url}")
        image_response = requests.get(twilio_url, timeout=30)
        
        if image_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Erro ao baixar imagem do Twilio: {image_response.status_code}'
            }), 400
        
        # Converte a imagem para base64
        import base64
        image_base64 = base64.b64encode(image_response.content).decode('utf-8')
        
        # Detecta o tipo de conteúdo
        content_type = image_response.headers.get('Content-Type', 'image/jpeg')
        
        # Envia para GPT-4 Vision
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
        
        # Retorna a análise
        return jsonify({
            'success': True,
            'analysis': response.choices[0].message.content
        })
    
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': f'Erro ao fazer requisição: {str(e)}'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/extract-document', methods=['POST'])
def extract_document():
    """
    Endpoint que recebe uma URL do Twilio com documento (PDF, Word, etc) e extrai o texto
    
    Body esperado:
    {
        "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/...",
        "analyze": false (opcional - se true, analisa o conteúdo com GPT-4)
    }
    
    Resposta:
    {
        "success": true,
        "text": "texto extraído do documento",
        "analysis": "análise do GPT-4" (se analyze=true)
    }
    """
    try:
        # Pega a URL do Twilio do body da requisição
        data = request.get_json()
        
        if not data or 'twilio_url' not in data:
            return jsonify({
                'success': False,
                'error': 'Campo "twilio_url" é obrigatório'
            }), 400
        
        twilio_url = data['twilio_url']
        should_analyze = data.get('analyze', False)
        
        # Baixa o documento da URL do Twilio
        print(f"Baixando documento de: {twilio_url}")
        doc_response = requests.get(twilio_url, timeout=30)
        
        if doc_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': f'Erro ao baixar documento do Twilio: {doc_response.status_code}'
            }), 400
        
        # Detecta o tipo de documento
        content_type = doc_response.headers.get('Content-Type', '')
        
        extracted_text = ""
        
        # Extrai texto baseado no tipo
        if 'pdf' in content_type.lower() or twilio_url.lower().endswith('.pdf'):
            # Extrai texto de PDF
            import PyPDF2
            pdf_buffer = io.BytesIO(doc_response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        
        elif 'word' in content_type.lower() or twilio_url.lower().endswith(('.doc', '.docx')):
            # Extrai texto de Word
            import docx
            doc_buffer = io.BytesIO(doc_response.content)
            doc = docx.Document(doc_buffer)
            
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        
        else:
            # Tenta como texto simples
            try:
                extracted_text = doc_response.content.decode('utf-8')
            except:
                return jsonify({
                    'success': False,
                    'error': f'Tipo de documento não suportado: {content_type}'
                }), 400
        
        result = {
            'success': True,
            'text': extracted_text.strip()
        }
        
        # Se solicitado, analisa o conteúdo com GPT-4
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
        return jsonify({
            'success': False,
            'error': f'Erro ao fazer requisição: {str(e)}'
        }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Verifica se a chave da OpenAI está configurada
    if not os.getenv('OPENAI_API_KEY'):
        print("AVISO: Variável de ambiente OPENAI_API_KEY não está configurada!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)




# ==================== FUNÇÕES AUXILIARES CHATWOOT ====================

def send_to_chatwoot_new_conversation(chatwoot_config, content, file_data=None):
    """
    Cria uma nova conversa no ChatWoot e envia mensagem
    
    Args:
        chatwoot_config: dict com api_url, api_token, account_id, inbox_id, source_id
        content: conteúdo da mensagem (texto)
        file_data: tuple (filename, file_bytes, content_type) para anexos
    
    Returns:
        dict com conversation_id ou None se falhar
    """
    try:
        url = f"{chatwoot_config['api_url']}/api/v1/accounts/{chatwoot_config['account_id']}/conversations"
        
        headers = {
            'api_access_token': chatwoot_config['api_token']
        }
        
        # Cria conversa com mensagem inicial
        payload = {
            'inbox_id': chatwoot_config['inbox_id'],
            'source_id': chatwoot_config['source_id'],
            'message': {
                'content': content,
                'message_type': 'incoming'
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code not in [200, 201]:
            print(f"Erro ao criar conversa no ChatWoot: {response.status_code} - {response.text}")
            return None
        
        conversation_data = response.json()
        conversation_id = conversation_data.get('id')
        
        # Se tem arquivo, envia como mensagem adicional
        if file_data and conversation_id:
            send_file_to_chatwoot(chatwoot_config, conversation_id, file_data)
        
        return {'conversation_id': conversation_id}
    
    except Exception as e:
        print(f"Erro ao enviar para ChatWoot: {str(e)}")
        return None

def send_to_chatwoot_existing(chatwoot_config, conversation_id, content, file_data=None):
    """
    Envia mensagem para conversa existente no ChatWoot
    
    Args:
        chatwoot_config: dict com api_url, api_token, account_id
        conversation_id: ID da conversa existente
        content: conteúdo da mensagem (texto)
        file_data: tuple (filename, file_bytes, content_type) para anexos
    
    Returns:
        bool indicando sucesso
    """
    try:
        url = f"{chatwoot_config['api_url']}/api/v1/accounts/{chatwoot_config['account_id']}/conversations/{conversation_id}/messages"
        
        headers = {
            'api_access_token': chatwoot_config['api_token']
        }
        
        payload = {
            'content': content,
            'message_type': 'incoming'
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code not in [200, 201]:
            print(f"Erro ao enviar mensagem no ChatWoot: {response.status_code} - {response.text}")
            return False
        
        # Se tem arquivo, envia
        if file_data:
            send_file_to_chatwoot(chatwoot_config, conversation_id, file_data)
        
        return True
    
    except Exception as e:
        print(f"Erro ao enviar para ChatWoot: {str(e)}")
        return False

def send_file_to_chatwoot(chatwoot_config, conversation_id, file_data):
    """
    Envia arquivo para conversa no ChatWoot
    
    Args:
        chatwoot_config: dict com api_url, api_token, account_id
        conversation_id: ID da conversa
        file_data: tuple (filename, file_bytes, content_type)
    """
    try:
        filename, file_bytes, content_type = file_data
        
        url = f"{chatwoot_config['api_url']}/api/v1/accounts/{chatwoot_config['account_id']}/conversations/{conversation_id}/messages"
        
        headers = {
            'api_access_token': chatwoot_config['api_token']
        }
        
        files = {
            'attachments[]': (filename, file_bytes, content_type)
        }
        
        data = {
            'message_type': 'incoming'
        }
        
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        
        if response.status_code not in [200, 201]:
            print(f"Erro ao enviar arquivo no ChatWoot: {response.status_code} - {response.text}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Erro ao enviar arquivo: {str(e)}")
        return False

# ==================== TEXTOS FIXOS ====================

FIXED_TEXTS = {
    'audio': 'Esta mensagem é a transcrição de um áudio que o cliente enviou para você. Responda com naturalidade e se for necessário trate a mensagem como se de fato estivesse recebido o áudio. Mensagem: ',
    'image': 'O cliente enviou uma imagem e o que consta nela segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Imagem: ',
    'document': 'O cliente enviou um documento e o que consta nele segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Documento: ',
    'video': 'O cliente enviou um vídeo e o que consta nele segue abaixo. Siga essas orientações: Caso o cliente não tenha informado o motivo para o envio do vídeo, questione. Caso seja uma reclamação informe que um atentendente humano irá verificar o ocorrido. Caso seja um elogio agradeça com entusiasmo: ',
    'location': 'Você recebeu uma localização. Caso tenha solicitado o endereço e o cliente está lhe enviando a localização, agradeça pois nos ajudará bastante na entrega, mas reforce a necessidade de envio do endereço por escrito. Se for outra situação, apenas agradeça.'
}




# ==================== ENDPOINT: CRIAR CONVERSA E PROCESSAR ====================

@app.route('/process-and-send-new', methods=['POST'])
def process_and_send_new():
    """
    Cria nova conversa no ChatWoot e processa mensagem conforme tipo
    
    Body esperado:
    {
        "twilio_url": "URL_DO_ARQUIVO" (opcional para text e location),
        "message_type": "text|audio|image|document|video|location",
        "text_content": "texto da mensagem" (obrigatório para type=text),
        "latitude": "lat" (obrigatório para type=location),
        "longitude": "lng" (obrigatório para type=location),
        "chatwoot": {
            "api_url": "https://app.chatwoot.com",
            "api_token": "token",
            "account_id": "123",
            "inbox_id": "456",
            "source_id": "uuid"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Body vazio'}), 400
        
        message_type = data.get('message_type', '').lower()
        chatwoot_config = data.get('chatwoot', {})
        
        if not message_type:
            return jsonify({'success': False, 'error': 'Campo "message_type" é obrigatório'}), 400
        
        # Processa conforme tipo de mensagem
        conteudo = ""
        file_data = None
        
        if message_type == 'text':
            # Mensagem de texto simples
            text_content = data.get('text_content', '')
            if not text_content:
                return jsonify({'success': False, 'error': 'Campo "text_content" obrigatório para type=text'}), 400
            
            conteudo = text_content
            
            # Cria conversa no ChatWoot
            result = send_to_chatwoot_new_conversation(chatwoot_config, conteudo)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'conversation_id': result['conversation_id'] if result else None,
                'chatwoot_sent': result is not None
            })
        
        elif message_type == 'location':
            # Localização
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not latitude or not longitude:
                return jsonify({'success': False, 'error': 'Campos "latitude" e "longitude" obrigatórios para type=location'}), 400
            
            conteudo = FIXED_TEXTS['location']
            location_text = f"📍 Localização: https://www.google.com/maps?q={latitude},{longitude}"
            
            # Cria conversa no ChatWoot
            result = send_to_chatwoot_new_conversation(chatwoot_config, location_text)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'conversation_id': result['conversation_id'] if result else None,
                'chatwoot_sent': result is not None
            })
        
        # Para os demais tipos, precisa de twilio_url
        twilio_url = data.get('twilio_url')
        if not twilio_url:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" obrigatório para este tipo'}), 400
        
        # Baixa o arquivo
        print(f"Baixando arquivo de: {twilio_url}")
        file_response = requests.get(twilio_url, timeout=30)
        
        if file_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar arquivo: {file_response.status_code}'}), 400
        
        file_bytes = file_response.content
        content_type = file_response.headers.get('Content-Type', 'application/octet-stream')
        
        if message_type == 'audio':
            # Transcreve áudio
            audio_buffer = io.BytesIO(file_bytes)
            audio_buffer.name = "audio.ogg"
            
            openai_client = get_openai_client()
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer
            )
            
            conteudo = FIXED_TEXTS['audio'] + transcript.text
            file_data = ('audio.ogg', file_bytes, content_type)
        
        elif message_type == 'image':
            # Analisa imagem
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
            # Extrai texto de documento
            import PyPDF2
            pdf_buffer = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            
            conteudo = FIXED_TEXTS['document'] + extracted_text.strip()
            file_data = ('document.pdf', file_bytes, content_type)
        
        elif message_type == 'video':
            # Para vídeo, apenas envia o arquivo (não processa)
            conteudo = FIXED_TEXTS['video'] + "(Vídeo enviado - processamento de vídeo não disponível)"
            file_data = ('video.mp4', file_bytes, content_type)
        
        else:
            return jsonify({'success': False, 'error': f'Tipo de mensagem não suportado: {message_type}'}), 400
        
        # Cria conversa no ChatWoot com o conteúdo processado
        result = send_to_chatwoot_new_conversation(chatwoot_config, conteudo, file_data)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'conversation_id': result['conversation_id'] if result else None,
            'chatwoot_sent': result is not None
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500




# ==================== ENDPOINT: ENVIAR EM CONVERSA EXISTENTE ====================

@app.route('/process-and-send', methods=['POST'])
def process_and_send():
    """
    Envia mensagem para conversa existente no ChatWoot e processa conforme tipo
    
    Body esperado:
    {
        "twilio_url": "URL_DO_ARQUIVO" (opcional para text e location),
        "message_type": "text|audio|image|document|video|location",
        "text_content": "texto da mensagem" (obrigatório para type=text),
        "latitude": "lat" (obrigatório para type=location),
        "longitude": "lng" (obrigatório para type=location),
        "chatwoot": {
            "api_url": "https://app.chatwoot.com",
            "api_token": "token",
            "account_id": "123",
            "conversation_id": "789"
        }
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Body vazio'}), 400
        
        message_type = data.get('message_type', '').lower()
        chatwoot_config = data.get('chatwoot', {})
        conversation_id = chatwoot_config.get('conversation_id')
        
        if not message_type:
            return jsonify({'success': False, 'error': 'Campo "message_type" é obrigatório'}), 400
        
        if not conversation_id:
            return jsonify({'success': False, 'error': 'Campo "conversation_id" é obrigatório no chatwoot'}), 400
        
        # Processa conforme tipo de mensagem
        conteudo = ""
        file_data = None
        
        if message_type == 'text':
            # Mensagem de texto simples
            text_content = data.get('text_content', '')
            if not text_content:
                return jsonify({'success': False, 'error': 'Campo "text_content" obrigatório para type=text'}), 400
            
            conteudo = text_content
            
            # Envia para conversa existente
            success = send_to_chatwoot_existing(chatwoot_config, conversation_id, conteudo)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'chatwoot_sent': success
            })
        
        elif message_type == 'location':
            # Localização
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            
            if not latitude or not longitude:
                return jsonify({'success': False, 'error': 'Campos "latitude" e "longitude" obrigatórios para type=location'}), 400
            
            conteudo = FIXED_TEXTS['location']
            location_text = f"📍 Localização: https://www.google.com/maps?q={latitude},{longitude}"
            
            # Envia para conversa existente
            success = send_to_chatwoot_existing(chatwoot_config, conversation_id, location_text)
            
            return jsonify({
                'success': True,
                'conteudo': conteudo,
                'chatwoot_sent': success
            })
        
        # Para os demais tipos, precisa de twilio_url
        twilio_url = data.get('twilio_url')
        if not twilio_url:
            return jsonify({'success': False, 'error': 'Campo "twilio_url" obrigatório para este tipo'}), 400
        
        # Baixa o arquivo
        print(f"Baixando arquivo de: {twilio_url}")
        file_response = requests.get(twilio_url, timeout=30)
        
        if file_response.status_code != 200:
            return jsonify({'success': False, 'error': f'Erro ao baixar arquivo: {file_response.status_code}'}), 400
        
        file_bytes = file_response.content
        content_type = file_response.headers.get('Content-Type', 'application/octet-stream')
        
        if message_type == 'audio':
            # Transcreve áudio
            audio_buffer = io.BytesIO(file_bytes)
            audio_buffer.name = "audio.ogg"
            
            openai_client = get_openai_client()
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_buffer
            )
            
            conteudo = FIXED_TEXTS['audio'] + transcript.text
            file_data = ('audio.ogg', file_bytes, content_type)
        
        elif message_type == 'image':
            # Analisa imagem
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
            # Extrai texto de documento
            import PyPDF2
            pdf_buffer = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            
            conteudo = FIXED_TEXTS['document'] + extracted_text.strip()
            file_data = ('document.pdf', file_bytes, content_type)
        
        elif message_type == 'video':
            # Para vídeo, apenas envia o arquivo (não processa)
            conteudo = FIXED_TEXTS['video'] + "(Vídeo enviado - processamento de vídeo não disponível)"
            file_data = ('video.mp4', file_bytes, content_type)
        
        else:
            return jsonify({'success': False, 'error': f'Tipo de mensagem não suportado: {message_type}'}), 400
        
        # Envia para conversa existente
        success = send_to_chatwoot_existing(chatwoot_config, conversation_id, conteudo, file_data)
        
        return jsonify({
            'success': True,
            'conteudo': conteudo,
            'chatwoot_sent': success
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Erro interno: {str(e)}'
        }), 500

