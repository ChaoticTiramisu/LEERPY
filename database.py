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

theorie_vak_association = Table(
    'theorie_vak_association', Base.metadata,
    Column('theorie_id', String, ForeignKey('theorie.theorie_nummer')),
    Column('vak_id', Integer, ForeignKey('vakken.id'))
)

class Gebruiker(Base):
    __tablename__ = "gebruikers"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam = mapped_column(String, nullable=False)
    achternaam = mapped_column(String, nullable=False)
    email = mapped_column(String, nullable=False, unique=True, index=True)
    paswoord = mapped_column(String, nullable=False)
    vak_list = [
        ('fysica', 'Fysica'),
        ('nederlands', 'Nederlands'),
        ('engels', 'Engels'),
        ('frans', 'Frans')
    ]
    vak = mapped_column(ChoiceType(vak_list, impl=String()), nullable=True)
    actief = mapped_column(Boolean, default=True)
    rol_list = [
        ('leerkracht', 'Leerkracht'),
        ('leerling', 'Leerling'),
    ]
    rol = mapped_column(ChoiceType(rol_list, impl=String()), nullable=True)

    def __repr__(self):
        return f"<Gebruiker(id={self.id}, naam={self.naam}, email={self.email}, rol={self.rol}, vak={self.vak})>"

class Theorie(Base):
    __tablename__ = "theorie"

    theorie_nummer = mapped_column(String, primary_key=True)
    vak = mapped_column(String)
    titel = mapped_column(String)

    def __repr__(self):
        return f"<Theorie(id={self.theorie_nummer}, naam={self.naam}, vak={self.vak} )>"

    vakken = relationship('Vak', secondary=theorie_vak_association, back_populates='theorie', lazy="select")
class Vak(Base):
    __tablename__ = "vakken"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    naam = mapped_column(String, nullable=False, unique=True)

    def __repr__(self):
        return f"<Vak(id={self.id}, naam={self.naam})>"

    theorie = relationship('Theorie', secondary=theorie_vak_association, back_populates='vakken', lazy="select")

Base.metadata.create_all(engine)

@click.command("create-admin")
def admin_account():
    admin_email = "admin@example.com"
    admin_password = "admin123"  # Default password
    with Session(engine) as session:
        admin = session.query(Gebruiker).filter_by(email=admin_email).first()
        if not admin:
            admin = Gebruiker(
                naam="Admin",
                achternaam="User",
                email=admin_email,
                paswoord=admin_password,  # Store password in plain text
                rol="leerkracht",
                actief=True
            )
            session.add(admin)
            session.commit()
            print(f"Admin account created:\nEmail: {admin_email}\nPassword: {admin_password}")
        else:
            print(f"Admin account already exists:\nEmail: {admin_email}")

if __name__ == "__main__":
    admin_account()