# de nodige zaken importeren
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Column, Integer, String, ForeignKey, DateTime  # Add DateTime here
from sqlalchemy.sql.expression import or_
import os
from database import Gebruiker, Boek, Genre, Auteur, Thema,Reservatie
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from sqlalchemy.orm import relationship, mapped_column
from datetime import datetime, timedelta

from sqlalchemy_utils import ChoiceType
from flask import jsonify, make_response


# dirname, is de weg naar dit bestand. 
dirname = os.path.abspath('instance')
app = Flask(__name__, instance_path=dirname)

# configugeren van de sessie
from werkzeug.middleware.proxy_fix import ProxyFix

app.wsgi_app = ProxyFix(app.wsgi_app)

app.config["SESSION_PERMANENT"] = False
# je hebt verschillende soort databases dus vandaar het type nog eens toelichten.
app.config["SESSION_TYPE"] = "sqlalchemy"
# het pad configugeren van de route naar de database
basedir = os.path.abspath(os.path.dirname(__file__)) 
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'bib.db')}"
app.config['UPLOAD_FOLDER'] = 'static/upload'

# de beveillingssleutel voor rededenen
app.secret_key = "Arno_augu_Cairo"
# een variabel weer korter maken voor sneller gebruik
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# hier worden alle tabellen aangemaakt

# definitie om te checken als een bepaalde waarde in een tabel zit in een bepaalde kolom
def checkContains(table_naam,column_naam,item):
 # getattr een string waarde omvormen naar een databasesyntax
    column = getattr(table_naam, column_naam)
    # het resultaat, query is dat hij gaat zoeken in de database. scalar = voor output terug naar string terug te brengen anders wordt het niet leesbaar voor de mens
    result = db.session.query(db.session.query(table_naam).filter(column == item).exists()).scalar()

    print(result)
    return result

# haalt een waarde uit een kolom
def getValue(table, column, item):
    result = db.session.query(table).filter(column == item).first()

    return result

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.context_processor
def inject_gebruiker():
    gebruiker = None
    if 'gebruiker_id' in session:
        gebruiker = db.session.query(Gebruiker).get(session.get("gebruiker_id"))

    return {
        'gebruiker': gebruiker,
        'email': getattr(gebruiker, 'email', None),
        'naam': getattr(gebruiker, 'naam', None),
        'achternaam': getattr(gebruiker, 'achternaam', None),
        'rol': getattr(gebruiker, 'rol', None)
    }


@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        email = request.form["login_email"]
        password = request.form["login_paswoord"]
        user = db.session.query(Gebruiker).filter_by(email=email).first()
        
        if user and user.paswoord == password:
            session['gebruiker_id'] = user.id
            session['email'] = user.email
            flash("Login succesvol", "success")  # Add a category
            return redirect(url_for("index"))
        else:
            flash("Paswoord incorrect of de gebruiker bestaat nog niet.", "error")  # Add a category
            return redirect(url_for("login"))
    
    # Only flash this message if it's a GET request and not a redirect
    return render_template("login.html", messages=get_flashed_messages(with_categories=True))
