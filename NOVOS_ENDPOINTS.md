# Novos Endpoints Adicionados

## 📸 Análise de Imagens

### Endpoint: POST /analyze-image

Analisa imagens usando GPT-4 Vision.

**Request:**
```json
{
  "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/...",
  "prompt": "O que tem nesta imagem?" 
}
```

**Response:**
```json
{
  "success": true,
  "analysis": "Descrição detalhada da imagem"
}
```

**Exemplo no Fiqon:**
- **Método:** POST
- **URL:** `https://sua-url.onrender.com/analyze-image`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "twilio_url": "{{url_da_imagem}}",
  "prompt": "Descreva esta imagem"
}
```

---

## 📄 Extração de Documentos

### Endpoint: POST /extract-document

Extrai texto de documentos (PDF, Word, TXT).

**Request:**
```json
{
  "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/...",
  "analyze": false
}
```

**Response:**
```json
{
  "success": true,
  "text": "Texto extraído do documento",
  "analysis": "Resumo do GPT-4 (se analyze=true)"
}
```

**Exemplo no Fiqon:**
- **Método:** POST
- **URL:** `https://sua-url.onrender.com/extract-document`
- **Headers:** `Content-Type: application/json`
- **Body:**
```json
{
  "twilio_url": "{{url_do_documento}}",
  "analyze": true
}
```

---

## 🎤 Transcrição de Áudio (já existente)

### Endpoint: POST /transcribe

**Request:**
```json
{
  "twilio_url": "https://api.twilio.com/2010-04-01/Accounts/.../Media/..."
}
```

**Response:**
```json
{
  "success": true,
  "transcription": "Texto transcrito"
}
```

---

## 💰 Custos OpenAI

- **Whisper (áudio):** $0.006/minuto
- **GPT-4.1-mini (imagem):** ~$0.03 por imagem
- **GPT-4.1-mini (texto):** ~$0.15 por 1M tokens

---

## 📦 Formatos Suportados

### Imagens
- JPG, JPEG
- PNG
- GIF
- WEBP

### Documentos
- PDF
- Word (DOC, DOCX)
- TXT

### Áudio
- OGG (WhatsApp)
- MP3
- WAV
- M4A

---

## ✅ Como Atualizar no Render

1. Faça upload dos novos arquivos no GitHub:
   - `app.py` (atualizado)
   - `requirements.txt` (atualizado)
   
2. No Render, o deploy automático vai detectar as mudanças

3. Aguarde 2-3 minutos para o deploy completar

4. Teste os novos endpoints!

