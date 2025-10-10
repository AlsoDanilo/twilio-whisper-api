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

