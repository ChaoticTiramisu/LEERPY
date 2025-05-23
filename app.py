# de nodige zaken importeren
from flask import Flask, render_template, redirect, url_for, request, flash, session, abort, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Column, Integer, String, ForeignKey, DateTime  # Add DateTime here
from sqlalchemy.sql.expression import or_
import os
from database import Gebruiker, Theorie, Vak
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
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(basedir, 'instance', 'LEER.db')}"
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

@app.route("/")
def index():
    # hier word de email uit de sessie gehaald
    email = session.get('email')
    #indien er geen email is, wordt je terug gestuurd naar de inlog pagina
    if email == None:
        return redirect(url_for("login"))
    else:
    # zoeken op basis van email, welke gebruikers naam je hebt om nadien op de hoofdpagina weer te geven.
        user = db.session.query(Gebruiker).filter_by(email=email).first()
        if user is None:
            return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/register", methods=["POST", "GET"])
def register():
    rol_choices = [(value, label) for value, label in Gebruiker.rol_list]
    #als de methode post is runt hij onderstaande commando's
    if request.method == "POST":
        register_email = request.form["register_email"]
        if checkContains(Gebruiker,"email",register_email) == False:

    # alle velden die de gebruiker heeft ingevuld eruit halen (post)
            register_name = request.form["name"]
            register_achternaam = request.form["achternaam"]
            register_email = request.form["register_email"]
            register_password = request.form["register_paswoord"]
            #rol = request.form["recht"]

            if "@" not in register_email:
                flash("Deze email bestaat niet","error")
            else:                
            # een nieuwe gebruiker toevoegen aan de database met volgende velden.
                new_gebruiker = Gebruiker(naam=register_name,achternaam = register_achternaam, email = register_email, paswoord = register_password)
            #database voert dit uit
                db.session.add(new_gebruiker)
            # het opslaan van de veranderingen
                db.session.commit()

            flash("Registratie succesvol","success")
            return redirect(url_for("login"))
        else:
             flash("Deze email adress is al in gebruik.")
             return render_template("register.html",rol_choices=rol_choices)
    else:
        #als het geen post is maar een get, steekt hij de rollen die hij uit de database haalt in een variabele en dan geeft hij deze weer in de rendertemplate om weer te geven.
        
        return render_template("register.html",rol_choices=rol_choices)



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

@app.route("/admin/gebruikers", methods=["GET"])
def leerkracht():
    # Haal alle gebruikers op uit de database
    gebruikers = db.session.query(Gebruiker).all()
    if not gebruikers:
        flash("Geen gebruikers gevonden.")
        return redirect(url_for("index"))
    return render_template("leerkracht.html", gebruikers=gebruikers)

@app.route('/bewerk_gebruiker/<int:gebruiker_id>', methods=['GET', 'POST'])
def bewerk_leerling(gebruiker_id):
    gebruiker = db.session.query(Gebruiker).get(gebruiker_id)
    rol_choices = [
        ('leerkracht', 'Leerkracht'),
        ('leerling', 'Leerling'),
    ]
    vak_choices = [
        ('fysica', 'Fysica'),
        ('nederlands', 'Nederlands'),
        ('engels', 'Engels'),
        ('frans', 'Frans')
    ]
    if request.method == 'POST':
        gebruiker.naam = request.form['naam']
        gebruiker.achternaam = request.form['achternaam']
        gebruiker.email = request.form['email']
        gebruiker.rol = request.form.get('recht')
        gebruiker.actief = request.form.get('actief') == "on"
        
        db.session.commit()
        return redirect(url_for('leerkracht'))  # Terug naar de gebruikerslijst

    return render_template('bewerk_leerling.html', gebruiker=gebruiker, rol_choices=rol_choices, vak_choices=vak_choices, def_actief=gebruiker.actief)

@app.route("/adminworkspace", methods=["GET"])
def adminworkspace():
    if session.get('email') is None:
        return redirect(url_for("login"))
    
    # Fetch the logged-in user
    gebruiker = db.session.query(Gebruiker).filter_by(email=session.get('email')).first()
    if gebruiker and gebruiker.rol in ["leerkracht"]:
        # Haal alle genres, themas en auteurs uit de database
        vakken = db.session.query(Vak.naam).all()

        
        return render_template("theorie_beheer.html", vakken=vakken)
    else:
        abort(404)

@app.route("/adminworkspace/tools/add", methods=["POST"])
def add():
    if session.get('email') is None:
        flash("Je moet ingelogd zijn om deze actie uit te voeren.", "error")
        return redirect(url_for("login"))
        
    test = db.session.query(Gebruiker).filter_by(email=session.get('email')).first()
    if str(test.rol).lower() not in ["leerkracht"]:
        flash("Je hebt geen toestemming om deze actie uit te voeren.", "error")
        abort(403)
    
    # Handle genre addition
    if "vak" in request.form and "theorie_nummer" not in request.form:
        vak_naam = request.form["vak"].lower()
        if not checkContains(Vak, "naam", vak_naam):
            new_vak = Vak(naam=vak_naam)
            db.session.add(new_vak)
            db.session.commit()
            vakken = db.session.query(Vak.naam).all()
            response = make_response(render_template("partials/vakken.html", vakken=vakken))
            response.headers['HX-Trigger'] = jsonify({"showMessage": f"Vak '{vak_naam}' succesvol toegevoegd."})
            return response
        else:
            vakken = db.session.query(Vak.naam).all()
            response = make_response(render_template("partials/vakken.html", vakken=vakken))
            response.headers['HX-Trigger'] = jsonify({"showMessage": f"Vak '{vak_naam}' zit al in de database."})
            return response
        
    # Handle book addition
    elif "theorie_nummer" in request.form:
        theorie_nummer_nr = request.form["theorie_nummer"].lower()
        if not checkContains(Theorie, "theorie_nummer", theorie_nummer_nr):
            theorie_nummer = request.form["theorie_nummer"]
            titel = request.form["titel"]
            
            file = request.files['file']
            if file and allowed_file(file.filename):
                filename = f"{theorie_nummer}{os.path.splitext(file.filename)[1]}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
            
            selected_vakken = request.form.getlist("vakken")

            vakken = [db.session.query(Vak).filter_by(naam=vak_name).first() or Vak(naam=vak_name) 
                      for vak_name in selected_vakken]

            theorie = Theorie(
                titel=titel,
                theorie_nummer=theorie_nummer,
            )
            
            theorie.vakken.extend(vakken)

            db.session.add(theorie)
            db.session.commit()
            
            flash(f"theorie '{titel}' succesvol toegevoegd.", "success")
            return redirect(url_for("adminworkspace"))
        else:
            flash(f"Boek met theorie_nummer '{theorie_nummer_nr}' zit al in de database.", "error")
            return redirect(url_for("adminworkspace"))
    else:
        flash("Onbekende fout opgetreden.", "error")
        abort(404)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Ensures that the database session is properly closed after each request.
    This prevents issues like stale connections or locked tables.
    """
    db.session.remove()

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)