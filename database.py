from flask import app
from sqlalchemy import Table, Column, String, Integer, ForeignKey, create_engine, Boolean, Date, DateTime
from sqlalchemy.orm import relationship, declarative_base, mapped_column, Session
from sqlalchemy_utils import database_exists, create_database, ChoiceType
from datetime import datetime
import click

# Initialize the database engine
engine = create_engine("sqlite:///instance/LEER.db", echo=True)

# Create the database if it doesn't exist
if not database_exists(engine.url):
    create_database(engine.url)

# Base class for all models
Base = declarative_base()

class Gebruiker(Base):
    __tablename__ = "gebruikers"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam = mapped_column(String, nullable=False)
    achternaam = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False, unique=True, index=True)
    paswoord = mapped_column(String, nullable=False)
    actief = mapped_column(Boolean, default=True)
    rol_list = [
        ('leerkracht', 'Leerkracht'),
        ('leerling', 'Leerling'),
    ]
    rol = mapped_column(ChoiceType(rol_list, impl=String()), nullable=True)

    def __repr__(self):
        return f"<Gebruiker(id={self.id}, naam={self.naam}, email={self.email})>"

Base.metadata.create_all(engine)