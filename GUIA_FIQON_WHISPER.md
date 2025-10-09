# Guia: Transcrição de Áudio Twilio + OpenAI Whisper para Fiqon

## O que foi criado?

Um serviço que recebe URLs de áudio do Twilio e retorna a transcrição usando OpenAI Whisper.

## Como usar no Fiqon

### HTTP Requester
- **Método:** POST
- **URL:** https://sua-url-do-deploy.com/transcribe
- **Header:** Content-Type: application/json
- **Body:**
```json
{
  "twilio_url": "URL_DO_AUDIO_DO_TWILIO"
}
```

### Resposta
```json
{
  "success": true,
  "transcription": "texto transcrito"
}
```

## Deploy Gratuito no Render.com

1. Acesse https://render.com e crie conta
2. New + → Web Service
3. Conecte GitHub ou faça upload
4. Configure:
   - Build: pip install -r requirements.txt
   - Start: gunicorn -w 1 -b 0.0.0.0:$PORT app:app
5. Adicione variável: OPENAI_API_KEY = sua_chave
6. Aguarde deploy e copie a URL

## Testado e funcionando!
Exemplo real: "Teste de envio de voz."
