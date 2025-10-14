# Twilio to Whisper Transcription API

Serviço intermediário que recebe URLs de áudio do Twilio, baixa o arquivo e transcreve usando OpenAI Whisper.

## Como funciona

1. Recebe uma URL de mídia do Twilio via POST
2. Baixa o arquivo de áudio
3. Envia para OpenAI Whisper API
4. Retorna a transcrição

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

Configure a variável de ambiente com sua chave da OpenAI:

```bash
export OPENAI_API_KEY="sua-chave-aqui"
```

## Executar localmente

```bash
python app.py
```

O servidor estará disponível em `http://localhost:5000`

## Uso

### Endpoint: POST /transcribe

**Request:**
```json
{
  "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/AC.../Messages/MM.../Media/ME..."
}
```

**Response (sucesso):**
```json
{
  "success": true,
  "transcription": "Texto transcrito do áudio"
}
```

**Response (erro):**
```json
{
  "success": false,
  "error": "Descrição do erro"
}
```

### Exemplo com cURL

```bash
curl -X POST http://localhost:5000/transcribe \
  -H "Content-Type: application/json" \
  -d '{"twilio_url": "https://api.twilio.com/2010-04-01/Accounts/AC.../Messages/MM.../Media/ME..."}'
```

### Exemplo no Fiqon

**HTTP Requester:**
- **Método:** POST
- **URL:** `https://seu-dominio.com/transcribe`
- **Headers:**
  - `Content-Type: application/json`
- **Body:**
```json
{
  "twilio_url": "{{url_do_twilio}}"
}
```

## Health Check

```bash
curl http://localhost:5000/health
```

## Deploy

Você pode fazer deploy deste serviço em:
- Render.com (gratuito)
- Railway.app (gratuito)
- Heroku
- Vercel
- Qualquer servidor com Python

## Limitações

- Arquivos de áudio devem ter no máximo 25MB (limitação da OpenAI Whisper API)
- A URL do Twilio deve estar acessível publicamente

