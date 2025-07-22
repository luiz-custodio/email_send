from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import time

# Carrega variaveis do .env
load_dotenv()

# Cria aplicação FastAPI
app = FastAPI(title="Email Sender Api")

# Configuração Cors - conecta back com o front
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Padroniza os dados das variaveis
class EmailRequest(BaseModel):
    recipients: List[EmailStr]
    subject: str
    body: str
    is_html: bool=False

# Rota raiz da api
@app.get("/")
def read_root() -> dict:
    return{
        "message" : "Api de envio de emails funcionando"
    }

# Rota para enviar emails
@app.post("/send-emails")
async def send_emails(email_data: EmailRequest):
    
    # Pega informações do arquivo .env
    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    # Verifica se há algo no .env
    if not sender_email or not sender_password:
        raise HTTPException(
            status_code=500,
            detail="Credenciais de email não configuradas"
        )

    # Resultado de envio
    results = {
        "successful": [],
        "failed": []
    }

    #Configuração do servidor SMTP do Outlook
    smtp_server = "smtp-mail.outlook.com"
    smtp_port = 587

    try:
        # Conecta ao servidor do Email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls() # Ativa segurança
        server.login(sender_email, sender_password)

        # Envia email para cada destinatario individualmente
        for recipient in email_data.recipients:
            try:
                # Cria a mensagem
                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = recipient
                message["Subject"] = email_data.subject

                # Define o tipo de conteudo (HTML ou texto)
                content_type = "html" if email_data.is_html else "plain"
                message.attach(MIMEText(email_data.body, content_type))

                # Envia o email
                server.send_message(message)
                results["successful"].append(recipient)

                #Pausa entre os envios
                time.sleep(1)
            except Exception as e:
                results["failed"].append({
                    "email": recipient,
                    "error": str(e)
                })
        # Encerra a conexão com o server
        server.quit()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao conectar com servidor de email: {str(e)}"
        )
    return{
        "message": "Processo de envio concluído",
        "results": results,
        "total_sent": len(results["successful"]),
        "total_failed": len(results["failed"])
    }    

@app.get("/test-connection")
async def test_connection():

    sender_email = os.getenv("EMAIL_ADDRESS")
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_email or not sender_password:
        return{"status": "error", "message": "Credenciais não configuradas"}
    try:
        server = smtplib.SMTP("smtp-mail.outlook.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.quit()
        return {"status": "success", "message": "Conexão bem-sucedida!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}