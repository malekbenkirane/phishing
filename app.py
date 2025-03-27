from flask import Flask, render_template, request, redirect, session, send_file, url_for
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
from fpdf import FPDF
import csv
from werkzeug.utils import secure_filename
from datetime import timedelta

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Configuration de la base de données SQLite
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///phishing_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# Modèle pour stocker les interactions des utilisateurs
class Interaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    event_type = db.Column(db.String(50), nullable=False)  # "email envoyé", "lien cliqué", "formulaire soumis"
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Créer toutes les tables dans le bon contexte
with app.app_context():
    db.create_all()

# Identifiants admin
ADMIN_USERNAME = "Reg"
ADMIN_PASSWORD = "Saouda2025!!"

# Configuration SMTP
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = "regence.informatique@liquidationtravail.com"
SENDER_PASSWORD = "Saouda2025!!"

def send_email(recipient_email, recipient_name, phishing_link):
    email_content = f"""
    <html>
    <body>
        <p>Bonjour {recipient_name},</p>
        <p>Nous rencontrons un problème technique affectant certains comptes Outlook...</p>
        <p><a href='{phishing_link}'>Réauthentifier mon compte</a></p>
    </body>
    </html>
    """
    try:
        msg = MIMEText(email_content, "html")
        msg["Subject"] = "Problème d'accès à Outlook - Action requise"
        msg["From"] = SENDER_EMAIL
        msg["To"] = recipient_email
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        
        db.session.add(Interaction(email=recipient_email, event_type="email envoyé"))
        db.session.commit()
    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")

@app.route("/track_open")
def track_open():
    email = request.args.get("email")
    if email:
        db.session.add(Interaction(email=email, event_type="lien cliqué"))
        db.session.commit()
    return "", 204

@app.route("/capture", methods=["POST"])
def capture():
    email = request.form.get("email")
    if email:
        db.session.add(Interaction(email=email, event_type="formulaire soumis"))
        db.session.commit()
    return redirect("https://outlook.com")

@app.route("/home")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Si l'utilisateur tente d'accéder à une page protégée, on redirige vers la page de connexion avec le paramètre 'next'
    next_page = request.args.get("next")
    
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            if next_page:
                # Vérification que next_page ne contient pas une URL malveillante avant la redirection
                if next_page.startswith("/") or next_page.startswith("http"):
                    return redirect(next_page)  # Rediriger vers la page initiale demandée après la connexion
                else:
                    return redirect("/stats_dashboard")  # Si 'next' est invalide, rediriger vers le tableau de bord
            return redirect("/stats_dashboard")  # Si aucun 'next' n'est présent, rediriger vers le tableau de bord par défaut

    return render_template("login.html")

@app.route("/send_email", methods=["GET", "POST"])
def send_email_route():
    if not session.get("logged_in"):
        return redirect(url_for("login", next=request.url))  # Ajouter 'next' dans l'URL pour rediriger après la connexion
    if request.method == "POST":
        file = request.files.get("csv_file")
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            file_path = os.path.join("uploads", filename)
            file.save(file_path)
            try:
                with open(file_path, "r") as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)
                    phishing_link = "https://outlook-regence.onrender.com"
                    for row in reader:
                        if len(row) >= 2:
                            send_email(row[0].strip(), row[1].strip(), phishing_link)
                return "Emails envoyés avec succès."
            except Exception as e:
                return f"Erreur : {e}", 500
        recipient_email = request.form.get("recipient_email")
        recipient_name = request.form.get("recipient_name")
        if recipient_email and recipient_name:
            phishing_link = "https://outlook-regence.onrender.com"
            send_email(recipient_email, recipient_name, phishing_link)
            return f"Email envoyé à {recipient_name} ({recipient_email}) !"
    return render_template("send_email.html")

@app.route("/stats_dashboard")
def stats_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("login", next=request.url))  # Ajouter 'next' dans l'URL pour rediriger après la connexion
    total_sent = Interaction.query.filter_by(event_type="email envoyé").count()
    total_clicked = Interaction.query.filter_by(event_type="lien cliqué").count()
    total_submitted = Interaction.query.filter_by(event_type="formulaire soumis").count()
    values = [total_sent, total_clicked, total_submitted]
    labels = ["Emails envoyés", "Liens cliqués", "Formulaires remplis"]
    try:
        plt.figure(figsize=(6,6))
        plt.pie(values, labels=labels, autopct="%1.1f%%", colors=["blue", "orange", "red"])
        plt.title("Statistiques du test de phishing")
        plt.savefig("static/stats.png")
        plt.close()
    except Exception as e:
        print(f"Erreur graphique : {e}")
    return render_template("dashboard.html", total_sent=total_sent, total_clicked=total_clicked, total_submitted=total_submitted)

@app.route("/download_pdf")
def download_pdf():
    if not session.get("logged_in"):
        return redirect(url_for("login", next=request.url))  # Ajouter 'next' dans l'URL pour rediriger après la connexion
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Rapport de Test de Phishing - Régence", ln=True, align='C')
    pdf.ln(10)
    total_sent = Interaction.query.filter_by(event_type="email envoyé").count()
    total_clicked = Interaction.query.filter_by(event_type="lien cliqué").count()
    total_submitted = Interaction.query.filter_by(event_type="formulaire soumis").count()
    pdf.cell(200, 10, f"Emails envoyés : {total_sent}", ln=True)
    pdf.cell(200, 10, f"Liens cliqués : {total_clicked}", ln=True)
    pdf.cell(200, 10, f"Formulaires remplis : {total_submitted}", ln=True)
    pdf.output("report.pdf")
    return send_file("report.pdf", as_attachment=True)

# Gérer la déconnexion et forcer la demande de mot de passe à chaque fois
@app.before_request
def before_request():
    session.permanent = False  # Désactive les cookies persistants pour la session
    app.permanent_session_lifetime = timedelta(seconds=60)  # Session expirée après 60 secondes d'inactivité

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
