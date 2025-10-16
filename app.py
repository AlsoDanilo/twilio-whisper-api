from flask import Flask, request, jsonify
import requests
import io
import os
from openai import OpenAI

app = Flask(__name__)

# Textos fixos para diferentes tipos de mídia
FIXED_TEXTS = {
    "audio": "Áudio recebido. Transcrição: ",
    "image": "Imagem recebida. Análise: ",
    "document": "Documento recebido. Conteúdo extraído: ",
    "video": "Vídeo recebido. ",
    "location": "Localização recebida."
}

# Cliente OpenAI será inicializado quando necessário
client = None

def get_openai_client():
    global client
    if client is None:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return client

@app.route("/transcribe", methods=["POST"])
def transcribe():
    """
    Endpoint que recebe uma URL do Twilio, baixa o áudio e transcreve usando OpenAI Whisper
    """
    try:
        data = request.get_json()
        if not data or "twilio_url" not in data:
            return jsonify({"success": False, "error": "Campo \"twilio_url\" é obrigatório"}), 400
        
        twilio_url = data["twilio_url"]
        audio_response = requests.get(twilio_url, timeout=30)
        
        if audio_response.status_code != 200:
            return jsonify({"success": False, "error": f"Erro ao baixar áudio do Twilio: {audio_response.status_code}"}), 400
        
        audio_buffer = io.BytesIO(audio_response.content)
        audio_buffer.name = "audio.ogg"
        
        openai_client = get_openai_client()
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_buffer
        )
        
        return jsonify({"success": True, "transcription": transcript.text})
    
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Erro ao fazer requisição: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500

@app.route("/analyze-image", methods=["POST"])
def analyze_image():
    """
    Endpoint que recebe uma URL do Twilio com imagem e analisa usando GPT-4 Vision
    """
    try:
        data = request.get_json()
        if not data or "twilio_url" not in data:
            return jsonify({"success": False, "error": "Campo \"twilio_url\" é obrigatório"}), 400
        
        twilio_url = data["twilio_url"]
        prompt = data.get("prompt", "Descreva esta imagem em detalhes.")
        
        image_response = requests.get(twilio_url, timeout=30)
        
        if image_response.status_code != 200:
            return jsonify({"success": False, "error": f"Erro ao baixar imagem do Twilio: {image_response.status_code}"}), 400
        
        import base64
        image_base64 = base64.b64encode(image_response.content).decode("utf-8")
        content_type = image_response.headers.get("Content-Type", "image/jpeg")
        
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
        
        return jsonify({"success": True, "analysis": response.choices[0].message.content})
    
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Erro ao fazer requisição: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500

@app.route("/extract-document", methods=["POST"])
def extract_document():
    """
    Endpoint que recebe uma URL do Twilio com documento (PDF, Word, etc) e extrai o texto
    """
    try:
        data = request.get_json()
        if not data or "twilio_url" not in data:
            return jsonify({"success": False, "error": "Campo \"twilio_url\" é obrigatório"}), 400
        
        twilio_url = data["twilio_url"]
        should_analyze = data.get("analyze", False)
        
        doc_response = requests.get(twilio_url, timeout=30)
        
        if doc_response.status_code != 200:
            return jsonify({"success": False, "error": f"Erro ao baixar documento do Twilio: {doc_response.status_code}"}), 400
        
        content_type = doc_response.headers.get("Content-Type", "")
        extracted_text = ""
        
        if "pdf" in content_type.lower() or twilio_url.lower().endswith(".pdf"):
            import PyPDF2
            pdf_buffer = io.BytesIO(doc_response.content)
            pdf_reader = PyPDF2.PdfReader(pdf_buffer)
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        
        elif "word" in content_type.lower() or twilio_url.lower().endswith((".doc", ".docx")):
            import docx
            doc_buffer = io.BytesIO(doc_response.content)
            doc = docx.Document(doc_buffer)
            for paragraph in doc.paragraphs:
                extracted_text += paragraph.text + "\n"
        
        else:
            try:
                extracted_text = doc_response.content.decode("utf-8")
            except:
                return jsonify({"success": False, "error": f"Tipo de documento não suportado: {content_type}"}), 400
        
        result = {"success": True, "text": extracted_text.strip()}
        
        if should_analyze and extracted_text.strip():
            openai_client = get_openai_client()
            analysis_response = openai_client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": f"Analise e resuma o seguinte documento:\n\n{extracted_text[:4000]}"}],
                max_tokens=1000
            )
            result["analysis"] = analysis_response.choices[0].message.content
        
        return jsonify(result)
    
    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Erro ao fazer requisição: {str(e)}"}), 500
    
    except Exception as e:
        return jsonify({"success": False, "error": f"Erro interno: {str(e)}"}), 500

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

# ==================== FUNÇÕES AUXILIARES CHATWOOT ====================

def send_original_media_to_chatwoot(chatwoot_config, original_media_url=None, location_data=None, message_type="text", text_content=None, conversation_id=None, file_data=None):
    try:
        api_url = chatwoot_config.get("api_url")
        account_id = chatwoot_config.get("account_id")
        api_token = chatwoot_config.get("api_token")
        inbox_id = chatwoot_config.get("inbox_id")
        source_id = chatwoot_config.get("source_id")

        if conversation_id:
            url = f"{api_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        else:
            url = f"{api_url}/api/v1/accounts/{account_id}/conversations"

        headers = {"api_access_token": api_token}
        payload = {"message_type": "incoming"}

        if not conversation_id:
            payload["inbox_id"] = inbox_id
            payload["source_id"] = source_id

        if text_content:
            payload["content"] = text_content
        elif location_data:
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            payload["content"] = f"📍 Localização: https://www.google.com/maps?q={latitude},{longitude}"
        elif original_media_url:
            payload["content"] = f"Mídia original: {original_media_url}"
        else:
            payload["content"] = "Mensagem sem conteúdo original específico."

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code not in [200, 201]:
            print(f"Erro ao enviar mensagem/criar conversa no ChatWoot: {response.status_code} - {response.text}")
            return None

        if not conversation_id:
            conversation_data = response.json()
            conversation_id = conversation_data.get("id")

        if file_data and conversation_id:
            send_file_to_chatwoot(chatwoot_config, conversation_id, file_data)

        return {"conversation_id": conversation_id}
    except Exception as e:
        print(f"Erro ao enviar para ChatWoot: {str(e)}")
        return None

def send_to_chatwoot_existing(chatwoot_config, conversation_id, content=None, file_data=None):
    try:
        api_url = chatwoot_config.get("api_url")
        account_id = chatwoot_config.get("account_id")
        api_token = chatwoot_config.get("api_token")

        url = f"{api_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        headers = {"api_access_token": api_token}
        payload = {"message_type": "incoming"}
        if content:
            payload["content"] = content

        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code not in [200, 201]:
            print(f"Erro ao enviar mensagem no ChatWoot: {response.status_code} - {response.text}")
            return False

        if file_data:
            send_file_to_chatwoot(chatwoot_config, conversation_id, file_data)

        return True

    except Exception as e:
        print(f"Erro ao enviar para ChatWoot: {str(e)}")
        return False

def send_file_to_chatwoot(chatwoot_config, conversation_id, file_data):
    try:
        filename, file_bytes, content_type = file_data
        api_url = chatwoot_config.get("api_url")
        account_id = chatwoot_config.get("account_id")
        api_token = chatwoot_config.get("api_token")

        url = f"{api_url}/api/v1/accounts/{account_id}/conversations/{conversation_id}/messages"
        headers = {"api_access_token": api_token}
        files = {"attachments[]": (filename, file_bytes, content_type)}
        data = {"message_type": "incoming"}
        response = requests.post(url, headers=headers, files=files, data=data, timeout=30)
        if response.status_code not in [200, 201]:
            print(f"Erro ao enviar arquivo no ChatWoot: {response.status_code} - {response.text}")
            return False
        return True
    except Exception as e:
        print(f"Erro ao enviar arquivo: {str(e)}")
        return False

# ==================== ENDPOINT: CRIAR CONVERSA E PROCESSAR ====================

@app.route("/process-and-send-new", methods=["POST"])
def process_and_send_new():
    try:
        data = request.form.to_dict()
        chatwoot_config = {
            "api_url": data.get("chatwoot_api_url"),
            "api_token": data.get("chatwoot_api_token"),
            "account_id": data.get("chatwoot_account_id"),
            "inbox_id": data.get("chatwoot_inbox_id"),
            "source_id": data.get("chatwoot_source_id")
        }
        
        original_media_url = data.get("original_media_url")
        message_type = data.get("message_type", "text")
        text_content = data.get("text_content")
        location_data = None
        if data.get("latitude") and data.get("longitude"):
            location_data = {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            }

        file_data = None
        if "file" in request.files:
            file = request.files["file"]
            file_bytes = file.read()
            file_data = (file.filename, file_bytes, file.content_type)

        chatwoot_response = send_original_media_to_chatwoot(
            chatwoot_config,
            original_media_url=original_media_url,
            location_data=location_data,
            message_type=message_type,
            text_content=text_content,
            file_data=file_data
        )

        if not chatwoot_response or not chatwoot_response.get("conversation_id"):
            return jsonify({"success": False, "error": "Falha ao enviar para o Chatwoot."}), 500

        conversation_id = chatwoot_response["conversation_id"]

        processed_text = ""
        if message_type == "audio" and original_media_url:
            transcribe_response = requests.post(f"http://localhost:5000/transcribe", json={"twilio_url": original_media_url}).json()
            if transcribe_response.get("success"):
                processed_text = FIXED_TEXTS["audio"] + transcribe_response["transcription"]
            else:
                processed_text = "Não foi possível transcrever o áudio."
        elif message_type == "image" and original_media_url:
            analyze_response = requests.post(f"http://localhost:5000/analyze-image", json={"twilio_url": original_media_url}).json()
            if analyze_response.get("success"):
                processed_text = FIXED_TEXTS["image"] + analyze_response["analysis"]
            else:
                processed_text = "Não foi possível analisar a imagem."
        elif message_type == "document" and original_media_url:
            extract_response = requests.post(f"http://localhost:5000/extract-document", json={"twilio_url": original_media_url, "analyze": True}).json()
            if extract_response.get("success"):
                processed_text = FIXED_TEXTS["document"] + extract_response.get("analysis", extract_response.get("text", ""))
            else:
                processed_text = "Não foi possível extrair/analisar o documento."
        elif message_type == "location" and location_data:
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            processed_text = FIXED_TEXTS["location"] + f"Latitude: {latitude}, Longitude: {longitude}"
        elif text_content:
            processed_text = text_content
        else:
            processed_text = "Conteúdo não processado."

        print(f"Conteúdo processado para o bot: {processed_text}")

        return jsonify({"success": True, "conversation_id": conversation_id, "processed_content": processed_text})

    except Exception as e:
        print(f"Erro no endpoint /process-and-send-new: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/process-and-send-existing", methods=["POST"])
def process_and_send_existing():
    try:
        data = request.form.to_dict()
        chatwoot_config = {
            "api_url": data.get("chatwoot_api_url"),
            "api_token": data.get("chatwoot_api_token"),
            "account_id": data.get("chatwoot_account_id")
        }
        conversation_id = data.get("conversation_id")
        
        if not conversation_id:
            return jsonify({"success": False, "error": "conversation_id é obrigatório."}), 400

        original_media_url = data.get("original_media_url")
        message_type = data.get("message_type", "text")
        text_content = data.get("text_content")
        location_data = None
        if data.get("latitude") and data.get("longitude"):
            location_data = {
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude")
            }

        file_data = None
        if "file" in request.files:
            file = request.files["file"]
            file_bytes = file.read()
            file_data = (file.filename, file_bytes, file.content_type)

        chatwoot_success = send_original_media_to_chatwoot(
            chatwoot_config,
            original_media_url=original_media_url,
            location_data=location_data,
            message_type=message_type,
            text_content=text_content,
            conversation_id=conversation_id,
            file_data=file_data
        )

        if not chatwoot_success:
            return jsonify({"success": False, "error": "Falha ao enviar para o Chatwoot."}), 500

        processed_text = ""
        if message_type == "audio" and original_media_url:
            transcribe_response = requests.post(f"http://localhost:5000/transcribe", json={"twilio_url": original_media_url}).json()
            if transcribe_response.get("success"):
                processed_text = FIXED_TEXTS["audio"] + transcribe_response["transcription"]
            else:
                processed_text = "Não foi possível transcrever o áudio."
        elif message_type == "image" and original_media_url:
            analyze_response = requests.post(f"http://localhost:5000/analyze-image", json={"twilio_url": original_media_url}).json()
            if analyze_response.get("success"):
                processed_text = FIXED_TEXTS["image"] + analyze_response["analysis"]
            else:
                processed_text = "Não foi possível analisar a imagem."
        elif message_type == "document" and original_media_url:
            extract_response = requests.post(f"http://localhost:5000/extract-document", json={"twilio_url": original_media_url, "analyze": True}).json()
            if extract_response.get("success"):
                processed_text = FIXED_TEXTS["document"] + extract_response.get("analysis", extract_response.get("text", ""))
            else:
                processed_text = "Não foi possível extrair/analisar o documento."
        elif message_type == "location" and location_data:
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")
            processed_text = FIXED_TEXTS["location"] + f"Latitude: {latitude}, Longitude: {longitude}"
        elif text_content:
            processed_text = text_content
        else:
            processed_text = "Conteúdo não processado."

        print(f"Conteúdo processado para o bot: {processed_text}")

        return jsonify({"success": True, "conversation_id": conversation_id, "processed_content": processed_text})

    except Exception as e:
        print(f"Erro no endpoint /process-and-send-existing: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    if not os.getenv("OPENAI_API_KEY"):
        print("AVISO: Variável de ambiente OPENAI_API_KEY não está configurada!")
    app.run(host="0.0.0.0", port=5000, debug=False)

