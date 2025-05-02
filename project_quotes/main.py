import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from quotes.quotes.application.quotes_controller import quotes_endpoint
from quotes.quotes.infrastructure.QuoteRepository import db_manager
# from fastapi_utilities import repeat_at
# from datetime import datetime, time
# from quotes.quotes.infrastructure.QuoteRepository import Quote
# from contextlib import asynccontextmanager

# @repeat_at("0 18 * * *", db_manager.init_db, run_first=True)

# @repeat_at(cron="3 * * * *")
# async def mark_past_quotes_as_done():
#     """
#     Marca como 'DONE' todas las citas activas cuya fecha ya ha pasado y son anteriores a hoy a las 18:00.
#     """
#     now = datetime.now()
#     # Establecer el umbral de hoy a las 18:00
#     today_18: datetime = datetime.combine(now.date(), time(18, 0))

#     # Buscar todas las citas activas con fecha anterior a hoy a las 18:00
#     past_quotes = db_manager.find(Quote, Quote.type == "active", Quote.date < today_18)

#     for quote in past_quotes:
#         # Si la cita es anterior a hoy a las 18:00, marcarla como 'DONE'
#         db_manager.update(Quote, quote.id, type="done")
    
#     # Si quieres agregar un log para saber cuántas citas se cambiaron:
#     print(f"Se marcaron {len(past_quotes)} citas como 'DONE'.")

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """
#     Lifespan context manager for the FastAPI application.
#     """
#     await mark_past_quotes_as_done()
#     yield


app = FastAPI(title="Quotes API",
              description="API for managing quotes",
            #   lifespan=lifespan,
              docs_url="/docs",
              redoc_url="/redocs",
              root_path="/quotes")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["POST", "GET", "PUT", "DELETE"],
    allow_headers=["*"],
    max_age=3600,
)

app.include_router(quotes_endpoint)

if __name__ == "__main__":
    db_manager.init_db()
    uvicorn.run(app, host="0.0.0.0", port=8001)