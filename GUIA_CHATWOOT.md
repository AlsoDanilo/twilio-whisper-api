# Guia Completo - Integração ChatWoot

## Novos Endpoints

### 1. `/process-and-send-new` - Criar Conversa
### 2. `/process-and-send` - Conversa Existente

---

## Como Usar no Fiqon

### Primeira Mensagem (Criar Conversa)

**Endpoint:** `POST https://sua-url.onrender.com/process-and-send-new`

**Body para TEXTO:**
```json
{
  "message_type": "text",
  "text_content": "{{texto_da_mensagem}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Body para ÁUDIO:**
```json
{
  "message_type": "audio",
  "twilio_url": "{{MediaUrl0}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Body para IMAGEM:**
```json
{
  "message_type": "image",
  "twilio_url": "{{MediaUrl0}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Body para DOCUMENTO (PDF):**
```json
{
  "message_type": "document",
  "twilio_url": "{{MediaUrl0}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Body para VÍDEO:**
```json
{
  "message_type": "video",
  "twilio_url": "{{MediaUrl0}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Body para LOCALIZAÇÃO:**
```json
{
  "message_type": "location",
  "latitude": "{{Latitude}}",
  "longitude": "{{Longitude}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "inbox_id": "79665",
    "source_id": "{{source_id_do_cliente}}"
  }
}
```

**Resposta:**
```json
{
  "success": true,
  "conteudo": "texto processado aqui",
  "conversation_id": 217,
  "chatwoot_sent": true
}
```

**Use a variável `conteudo` no fluxo do bot!**

---

### Mensagens Seguintes (Conversa Existente)

**Endpoint:** `POST https://sua-url.onrender.com/process-and-send`

**Body (exemplo com áudio):**
```json
{
  "message_type": "audio",
  "twilio_url": "{{MediaUrl0}}",
  "chatwoot": {
    "api_url": "https://app.chatwoot.com",
    "api_token": "eohCeM5aw5nNuEfpZMD9Vw5s",
    "account_id": "137056",
    "conversation_id": "{{conversation_id_da_planilha}}"
  }
}
```

**Diferença:** Usa `conversation_id` em vez de `source_id` e `inbox_id`.

**Todos os tipos funcionam igual!**

---

## O que Cada Tipo Retorna

### TEXT
- **ChatWoot recebe:** Texto
- **Variável `conteudo`:** Mesmo texto

### AUDIO
- **ChatWoot recebe:** Arquivo de áudio
- **Variável `conteudo`:** "Esta mensagem é a transcrição de um áudio que o cliente enviou para você. Responda com naturalidade e se for necessário trate a mensagem como se de fato estivesse recebido o áudio. Mensagem: [transcrição]"

### IMAGE
- **ChatWoot recebe:** Imagem
- **Variável `conteudo`:** "O cliente enviou uma imagem e o que consta nela segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Imagem: [análise da imagem]"

### DOCUMENT
- **ChatWoot recebe:** PDF
- **Variável `conteudo`:** "O cliente enviou um documento e o que consta nele segue abaixo. Siga essas orientações: Se for informações de um pedido, proceda conforme já orientado em seu prompt. Se for informações de uma comanda confirme com o cliente se ele quer que seja lançado um pedido com esses produtos. Caso seja informações de um comprovante de pagamento confirme se o pagamento foi efetivado conforme dados do mesmo exponha esses dados e se confirmado, informe que irá verificar junto o departamento responsável. Caso seja outro tipo de conteúdo confirme com o cliente do que se trata e qual é a intenção do cliente. Documento: [texto extraído]"

### VIDEO
- **ChatWoot recebe:** Vídeo
- **Variável `conteudo`:** "O cliente enviou um vídeo e o que consta nele segue abaixo. Siga essas orientações: Caso o cliente não tenha informado o motivo para o envio do vídeo, questione. Caso seja uma reclamação informe que um atentendente humano irá verificar o ocorrido. Caso seja um elogio agradeça com entusiasmo: (Vídeo enviado - processamento de vídeo não disponível)"

### LOCATION
- **ChatWoot recebe:** Link do Google Maps
- **Variável `conteudo`:** "Você recebeu uma localização. Caso tenha solicitado o endereço e o cliente está lhe enviando a localização, agradeça pois nos ajudará bastante na entrega, mas reforce a necessidade de envio do endereço por escrito. Se for outra situação, apenas agradeça."

---

## Fluxo Completo no Fiqon

```
1. Cliente envia mensagem
2. Twilio → Fiqon (webhook)
3. Fiqon busca na planilha
   
   SE NÃO TEM CONVERSA:
   4a. Busca source_id no ChatWoot
   5a. Chama /process-and-send-new
   6a. Recebe conversation_id
   7a. Salva conversation_id na planilha
   
   SE TEM CONVERSA:
   4b. Pega conversation_id da planilha
   5b. Chama /process-and-send
   
8. Usa variável "conteudo" no fluxo
9. Envia para bot ou humano conforme regras
```

---

## Testado e Funcionando ✅

- ✅ Texto
- ✅ Áudio (transcrição Whisper)
- ✅ Imagem (análise GPT-4 Vision)
- ✅ Documento PDF (extração de texto)
- ✅ Vídeo (envio do arquivo)
- ✅ Localização (Google Maps)

---

## Como Atualizar no Render

1. Acesse seu repositório no GitHub
2. Substitua o arquivo `app.py`
3. Faça commit
4. Render detecta e faz deploy automático
5. Aguarde 2-3 minutos
6. Teste!

---

## Variáveis do Twilio

No Fiqon, você recebe estas variáveis do Twilio:

- `{{Body}}` - Texto da mensagem
- `{{MediaUrl0}}` - URL do arquivo (áudio/imagem/PDF/vídeo)
- `{{MediaContentType0}}` - Tipo do arquivo
- `{{Latitude}}` - Latitude (localização)
- `{{Longitude}}` - Longitude (localização)
- `{{From}}` - Número do cliente

Use essas variáveis nos bodies acima!

---

## Custos Estimados

| Tipo | Custo OpenAI |
|------|--------------|
| Texto | $0 |
| Áudio | $0.006/minuto |
| Imagem | ~$0.03/imagem |
| Documento | $0 (só extração) |
| Vídeo | $0 (não processa) |
| Localização | $0 |

**Muito barato para uso moderado!**

