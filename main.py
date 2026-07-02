from fastapi import FastAPI, Request
from anthropic import Anthropic
import httpx, json

app = FastAPI()
client = Anthropic()
conversation_history = {}  # En prod: usa Redis/DB

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    
    # Extraer mensaje del usuario (formato Twilio)
    user_phone = data["From"]
    user_message = data["Body"]
    
    # Recuperar historial de conversación
    history = conversation_history.get(user_phone, [])
    history.append({"role": "user", "content": user_message})
    
    # Llamar al LLM
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system="Eres un asistente de atención al cliente amigable. Responde de forma concisa porque estás en WhatsApp.",
        messages=history
    )
    
    reply = response.content[0].text
    history.append({"role": "assistant", "content": reply})
    conversation_history[user_phone] = history[-20:]  # Mantener últimos 20 mensajes
    
    # Enviar respuesta vía Twilio
    await send_whatsapp_message(user_phone, reply)
    return {"status": "ok"}

async def send_whatsapp_message(to: str, body: str):
    async with httpx.AsyncClient() as http:
        await http.post(
            f"https://api.twilio.com/2010-04-01/Accounts/{ACCOUNT_SID}/Messages.json",
            data={"From": "whatsapp:+14155238886", "To": to, "Body": body},
            auth=(ACCOUNT_SID, AUTH_TOKEN)
        )
