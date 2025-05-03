from pydantic import BaseModel
from quotes.quotes.models.quote_entity import QuoteEntity
from quotes.quotes.infrastructure.QuoteRepository import db_manager, DatabaseManager
from datetime import datetime, timedelta, time
from fastapi import HTTPException

class QuotesService(BaseModel):
    """
    Service class for managing quotes.
    """
    db_manager: DatabaseManager = db_manager

    async def schedule_quote(self, name, gmail, date):
        """
        Schedule a quote for a specific date.
        """
        start_time = datetime.combine(date.date(), time(8, 0))  # 08:00 del día
        end_time = datetime.combine(date.date(), time(17, 0))   # 17:00 del día

        now = datetime.now()

        if date < now:
            raise HTTPException(status_code=400, detail="No se puede agendar una cita en el pasado.")

        if date.minute not in [0, 30]:
            raise HTTPException(status_code=400, detail="La hora de la cita debe ser en múltiplos de 30 minutos, como 08:00, 08:30, 09:00, etc.")

        if not (start_time <= date < end_time):
            raise HTTPException(status_code=400, detail= "La cita debe estar entre las 08:00 y las 17:00.")
        
        available_slots = await self.check_availability(date)
        if date not in available_slots:
            raise HTTPException(status_code=400, detail= "Ya hay citas programadas para esa fecha y hora.")
        
        entity = QuoteEntity(
            name=name,
            gmail=gmail,
            date=date
        )

        self.db_manager.insert(entity)
        return "Quote scheduled successfully"

    async def check_availability(self, date: datetime):
        """
        Check availability for a given date and time range.
        """

        now = datetime.now()

        if date.date() < now.date():
            raise HTTPException(status_code=400, detail="No se puede revisar disponibilidad pasada.")
        
        slots = await self.generate_daily_slots(date)
        booked_slots = self.db_manager.find_active_quotes_by_date(date)
        booked_slots = [slot.date for slot in booked_slots]
        available_slots = [slot for slot in slots if slot not in booked_slots]

        if date.date() == now.date():
            available_slots = [slot for slot in available_slots if slot > now]
        
        if not available_slots:
            raise HTTPException(status_code=400, detail="No quedan horarios disponibles para ese día.")
        
        return available_slots

    async def generate_daily_slots(self, date: datetime, start="08:00", end="17:00", duration_minutes=30):
        start_time = datetime.combine(date.date(), datetime.strptime(start, "%H:%M").time())
        end_time = datetime.combine(date.date(), datetime.strptime(end, "%H:%M").time())
        
        slots = []
        while start_time < end_time:
            slots.append(start_time)
            start_time += timedelta(minutes=duration_minutes)
        
        return slots
    
    async def reschedule_quote(self, gmail: str, new_date: datetime):
        """
        Reschedule a quote to a new date.
        """
        now = datetime.now()

        if new_date < now:
            raise HTTPException(status_code=400, detail="No se puede agendar una cita en el pasado.")

        if new_date.minute not in [0, 30]:
            raise HTTPException(status_code=400, detail="La hora de la cita debe ser en múltiplos de 30 minutos, como 08:00, 08:30, 09:00, etc.")

        if not (datetime.combine(new_date.date(), time(8, 0)) <= new_date < datetime.combine(new_date.date(), time(17, 0))):
            raise HTTPException(status_code=400, detail="La cita debe estar entre las 08:00 y las 17:00.")
        
        available_slots = await self.check_availability(new_date)
        if new_date not in available_slots:
            raise HTTPException(status_code=400, detail="Ya hay citas programadas para esa fecha y hora.")

        result = self.db_manager.update(gmail=gmail, new_date=new_date)
        if result:
            return True
        raise HTTPException(status_code=400, detail="No se encontró la cita para reprogramar.")
    
    async def cancel_quote(self, gmail: str):
        """
        Cancel a scheduled quote.
        """

        result = self.db_manager.cancel(gmail=gmail)
        if result:
            return True
        raise HTTPException(status_code=400, detail="No se encontró la cita para cancelar.")
    
    class Config:
        arbitrary_types_allowed = True