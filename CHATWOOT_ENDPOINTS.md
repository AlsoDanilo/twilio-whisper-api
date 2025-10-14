# Endpoints ChatWoot - Documentação Completa

## 🎯 Visão Geral

Dois novos endpoints que processam mensagens e enviam automaticamente para o ChatWoot:

- `/process-and-send-new` - Cria nova conversa
- `/process-and-send` - Envia para conversa existente

---

## 📝 Endpoint 1: Criar Conversa

### POST /process-and-send-new

Cria uma nova conversa no ChatWoot e envia a primeira mensagem processada.

### Tipos de Mensagem Suportados

#### 1. Texto (text)

**Request:**
```json
{
  "message_type": "text",
  "text_content": "Olá, preciso de ajuda",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "Olá, preciso de ajuda",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

---

#### 2. Áudio (audio)

**Request:**
```json
{
  "message_type": "audio",
  "twilio_url": "https://api.twilio.com/.../Media/...",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "Esta mensagem é a transcrição de um áudio que o cliente enviou para você. Responda com naturalidade e se for necessário trate a mensagem como se de fato estivesse recebido o áudio. Mensagem: texto transcrito aqui",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**O que acontece:**
- ✅ Baixa áudio do Twilio
- ✅ Envia arquivo de áudio para ChatWoot
- ✅ Transcreve com Whisper
- ✅ Retorna transcrição + texto fixo

---

#### 3. Imagem (image)

**Request:**
```json
{
  "message_type": "image",
  "twilio_url": "https://api.twilio.com/.../Media/...",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "O cliente enviou uma imagem e o que consta nela segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Imagem: descrição da imagem aqui",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**O que acontece:**
- ✅ Baixa imagem do Twilio
- ✅ Envia imagem para ChatWoot
- ✅ Analisa com GPT-4 Vision
- ✅ Retorna análise + texto fixo

---

#### 4. Documento (document)

**Request:**
```json
{
  "message_type": "document",
  "twilio_url": "https://api.twilio.com/.../Media/...",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "O cliente enviou um documento e o que consta nele segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Documento: texto extraído do PDF",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**O que acontece:**
- ✅ Baixa PDF do Twilio
- ✅ Envia PDF para ChatWoot
- ✅ Extrai texto do PDF
- ✅ Retorna texto + texto fixo

---

#### 5. Vídeo (video)

**Request:**
```json
{
  "message_type": "video",
  "twilio_url": "https://api.twilio.com/.../Media/...",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "O cliente enviou um vídeo e o que consta nele segue abaixo. Siga essas orientações: Caso o cliente não tenha informado o motivo para o envio do vídeo, questione. Caso seja uma reclamação informe que um atentendente humano irá verificar o ocorrido. Caso seja um elogio agradeça com entusiasmo: (Vídeo enviado - processamento de vídeo não disponível)",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**O que acontece:**
- ✅ Baixa vídeo do Twilio
- ✅ Envia vídeo para ChatWoot
- ✅ Retorna texto fixo (não processa vídeo)

---

#### 6. Localização (location)

**Request:**
```json
{
  "message_type": "location",
  "latitude": "-23.550520",
  "longitude": "-46.633308",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "uuid-do-contato"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "Você recebeu uma localização. Caso tenha solicitado o endereço e o cliente está lhe enviando a localização, agradeça pois nos ajudará bastante na entrega, mas reforce a necessidade de envio do endereço por escrito. Se for outra situação, apenas agradeça.",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**O que acontece:**
- ✅ Envia link do Google Maps para ChatWoot
- ✅ Retorna texto fixo

---

## 📝 Endpoint 2: Enviar para Conversa Existente

### POST /process-and-send

Envia mensagem para uma conversa que já existe no ChatWoot.

**Diferença:** Usa `conversation_id` em vez de `source_id` e `inbox_id`.

### Exemplo com Áudio

**Request:**
```json
{
  "message_type": "audio",
  "twilio_url": "https://api.twilio.com/.../Media/...",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "sua_chave",
    "account_id": "137056",
    "conversation_id": "217"
  }
}
```

**Response:**
```json
{
  "success": true,
  "conteudo": "Esta mensagem é a transcrição...",
  "chatwoot_sent": true
}
```

**Todos os tipos funcionam igual ao endpoint anterior!**

---

## 🔄 Fluxo Completo no Fiqon

### Primeira Mensagem (Cria Conversa)

1. Cliente envia mensagem
2. Twilio → Fiqon (webhook)
3. Fiqon busca na planilha → Não tem conversa
4. Fiqon busca `source_id` no ChatWoot
5. Fiqon chama `/process-and-send-new` com `source_id`
6. Sistema cria conversa, processa e retorna `conversation_id`
7. Fiqon salva `conversation_id` na planilha
8. Fiqon usa `conteudo` no fluxo

### Mensagens Seguintes

1. Cliente envia mensagem
2. Twilio → Fiqon (webhook)
3. Fiqon busca na planilha → Tem `conversation_id`
4. Fiqon chama `/process-and-send` com `conversation_id`
5. Sistema processa e envia para conversa existente
6. Fiqon usa `conteudo` no fluxo

---

## ✅ Testado e Funcionando

- ✅ Texto
- ✅ Áudio (transcrição)
- ✅ Imagem (análise)
- ✅ Documento (extração)
- ✅ Vídeo (envio)
- ✅ Localização (Google Maps)

---

## 🚀 Como Atualizar no Render

1. Faça upload do `app.py` atualizado no GitHub
2. Render detecta automaticamente
3. Aguarde 2-3 minutos
4. Teste os novos endpoints!

---

## 💡 Dicas

- Campo `conteudo` sempre retorna texto formatado para o bot
- ChatWoot sempre recebe arquivo original (áudio/imagem/PDF)
- Se `chatwoot_sent` for `false`, houve erro ao enviar
- Localização envia link clicável do Google Maps
