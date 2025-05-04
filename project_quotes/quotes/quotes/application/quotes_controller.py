from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from quotes.quotes.domain.quotes_service import QuotesService
from datetime import datetime
from quotes.quotes.application.dto.quotes_dto import QuoteDTO

endpoint_quotes = "/quotes"

quotes_endpoint = APIRouter()

Quotes_service = QuotesService()

@quotes_endpoint.post("/schedule",tags=["quotes"])
async def schedule_quote(data: QuoteDTO):
    """
    Schedule a quote for a specific date.
    """
    response = await Quotes_service.schedule_quote(**data.model_dump())
    return response

@quotes_endpoint.get("/schedule",tags=["quotes"])
async def check_availability(date: datetime):
    """
    Check availability for a given date and time range.
    """
    response = await Quotes_service.check_availability(date)
    
    return response

@quotes_endpoint.put("/reschedule", tags=["quotes"])
async def reschedule_quote(gmail: str, new_date: datetime):
    """
    Reschedule a quote to a new date.
    """
    result = await Quotes_service.reschedule_quote(gmail, new_date)
    if result is True:
        return "Cita reprogramada con éxito"
    raise HTTPException(status_code=404, detail=result)

@quotes_endpoint.put("/cancel", tags=["quotes"])
async def cancel_quote(gmail: str):
    """
    Cancel a scheduled quote.
    """
    result = await Quotes_service.cancel_quote(gmail)
    if result is True:
        return "Cita cancelada con éxito"
    raise HTTPException(status_code=404, detail=result)