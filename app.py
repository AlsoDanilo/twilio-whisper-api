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

@app.route('/health', methods=['GET'])
def health():
    """Endpoint de health check"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    # Verifica se a chave da OpenAI está configurada
    if not os.getenv('OPENAI_API_KEY'):
        print("AVISO: Variável de ambiente OPENAI_API_KEY não está configurada!")
    
    app.run(host='0.0.0.0', port=5000, debug=True)

