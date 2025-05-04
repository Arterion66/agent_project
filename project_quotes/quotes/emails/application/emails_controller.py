from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from quotes.emails.domain.emails_service import EmailsService
from datetime import datetime

endpoint_emails = "/emails"

emails_endpoint = APIRouter()

Emails_service = EmailsService()

@emails_endpoint.post("/send",tags=["emails"])
async def send_email( gmail: str):
    """
    Schedule a quote for a specific date.
    """
    response = await Emails_service.send_email(gmail=gmail)
    return response