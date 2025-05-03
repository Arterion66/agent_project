from pydantic import BaseModel
from quotes.quotes.models.quote_entity import QuoteEntity
from quotes.quotes.infrastructure.QuoteRepository import db_manager, DatabaseManager
from datetime import datetime, timedelta, time
from fastapi import HTTPException
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

email_emisor = 'quotestest123@gmail.com'
contraseña = 'gczo vnzc jwhk ppzm'

class EmailsService(BaseModel):
    """
    Service class for managing quotes.
    """
    db_manager: DatabaseManager = db_manager

    async def send_email(self, gmail):
        """
        Schedule a quote for a specific date.
        """

        quote = self.db_manager.find(gmail=gmail)
        if not quote:
            raise HTTPException(status_code=404, detail="No se encontró la cita.")
        email_receptor = gmail
        message = MIMEMultipart()
        message['From'] = email_emisor
        message['To'] = email_receptor
        message['Subject'] = 'Cita programada'
        body = f"""Hola {quote[0].name},

Tu cita está programada para el {quote[0].date}.

Saludos."""
        message.attach(MIMEText(body, 'plain'))
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(email_emisor, contraseña)
                server.sendmail(email_emisor, email_receptor, message.as_string())
                server.quit()
            return "Email sent successfully"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")
    
    class Config:
        arbitrary_types_allowed = True

