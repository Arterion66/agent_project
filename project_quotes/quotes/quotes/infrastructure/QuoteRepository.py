from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from psycopg2 import connect, sql
import psycopg2
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta, time
from enum import Enum
from fastapi import HTTPException

Base = declarative_base()

class DatabaseManager:
    def __init__(self, db_user, db_password, db_name, db_host="db"):
        self.db_user = db_user
        self.db_password = db_password
        self.db_name = db_name
        self.db_host = db_host
        self.db_url = f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:5432/{self.db_name}"
        self.engine = None
        self.Session = None
        self.session = None

    def init_db(self):
        """Método para inicializar la base de datos y crear la tabla 'Quote'."""
        conn = psycopg2.connect(
            dbname='postgres',
            user=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=5432
        )
        conn.autocommit = True  # Necesario para ejecutar la creación de base de datos
        cursor = conn.cursor()

        # Comprobar si la base de datos existe
        cursor.execute(sql.SQL("SELECT 1 FROM pg_database WHERE datname = %s"), [self.db_name])
        if not cursor.fetchone():
            # Si no existe, crear la base de datos
            cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(self.db_name)))
            print(f"Base de datos '{self.db_name}' creada con éxito.")
        else:
            print(f"La base de datos '{self.db_name}' ya existe.")

        # Cerrar la conexión temporal
        cursor.close()
        conn.close()

        # Ahora que la base de datos existe, conectar a la base de datos 'quotes'
        self.engine = create_engine(self.db_url)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

        # Crear las tablas definidas en los modelos de SQLAlchemy (si no existen)
        Base.metadata.create_all(self.engine)

    # def find(self, model, **filters):
    #     """Método para buscar registros."""
    #     return self.session.query(model).filter_by(**filters).all()
    
    def find_active_quotes_by_date(self, date: datetime):
        """Método para encontrar citas ACTIVAS por fecha."""
        # Convertir la fecha a solo la parte de la fecha (sin hora)
        start_of_day = datetime.combine(date.date(), datetime.min.time())  # 00:00 de esa fecha
        end_of_day = start_of_day + timedelta(days=1)  # 23:59 de esa fecha
        
        # Filtrar por tipo 'ACTIVE' y que la fecha esté dentro de ese día
        return self.session.query(Quote).filter(
            Quote.type == 'active',
            Quote.date >= start_of_day,
            Quote.date < end_of_day
        ).all()

    def insert(self, entity):
        """Método para insertar un nuevo registro."""

        existing_active_quote = self.session.query(Quote).filter(Quote.gmail == entity.gmail, Quote.type == 'active').first()
    
        if existing_active_quote:
            raise HTTPException(status_code=400, detail="Ya existe una cita activa para este correo electrónico.")

        # Convertir el modelo Pydantic en un diccionario excluyendo los valores None
        model_dict = entity.model_dump(exclude_none=True)
        if isinstance(model_dict.get("type"), Enum):
            model_dict["type"] = model_dict["type"].value
        
        # Usar el diccionario para crear una nueva instancia de SQLAlchemy
        new_record = Quote(**model_dict)
        self.session.add(new_record)
        self.session.commit()
        return new_record

    def update(self, gmail: str, new_date: datetime):
        """Método para reprogramar una cita activa (actualizarla con una nueva fecha)."""
        # Buscar la cita activa más reciente asociada al 'gmail'
        quote = self.session.query(Quote).filter(Quote.gmail == gmail, Quote.type == 'active').order_by(Quote.date.desc()).first()
        
        if not quote:
            raise HTTPException(status_code=400, detail="No se encontró una cita activa para reprogramar.")

        # Actualizar la fecha de la cita
        quote.date = new_date
        self.session.commit()
        return True
    
    def cancel(self, gmail: str):
        """Método para cancelar una cita programada."""
        quote = self.session.query(Quote).filter(Quote.gmail == gmail, Quote.type == 'active').first()

        if not quote:
            raise HTTPException(status_code=400, detail="No se encontró la cita para cancelar.")

        self.session.delete(quote)
        self.session.commit()
        return True

    # def delete(self, model, record_id):
    #     """Método para eliminar un registro."""
    #     record = self.session.query(model).get(record_id)
    #     if record:
    #         self.session.delete(record)
    #         self.session.commit()
    #         return True
    #     return False

class Quote(Base):
    __tablename__ = 'quotes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    gmail = Column(String(50), nullable=False)
    date = Column(DateTime, default=datetime.now)
    type = Column(String(50), nullable=False)

db_manager = DatabaseManager(db_user="admin", db_password="admin1234", db_name="quotes")