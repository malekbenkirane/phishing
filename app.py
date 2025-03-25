from flask import Flask, render_template, request, redirect, send_file, session
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
from email.mime.text import MIMEText
from fpdf import FPDF

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
    event_type = db.Column(db.String(50), nullable=False)  # reçu, ouvert, cliqué, soumis
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

# Création des tables
db.create_all()

# Identifiants admin
ADMIN_USERNAME = "Reg"
ADMIN_PASSWORD = "Saouda2025!!"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "regence.informatique@gmail.com"
SENDER_PASSWORD = "skju prcn iisd ginx"

def send_email(recipient_email, phishing_link):
    email_content = f"""
    Bonjour,

    Nous avons constaté une activité inhabituelle sur votre compte Microsoft. Afin de protéger vos informations personnelles, nous vous prions de vérifier votre identité dès que possible en suivant le lien ci-dessous :
    
    👉 <a href="{phishing_link}">Vérifiez maintenant votre compte Microsoft</a>
    
    Si vous avez des questions, n'hésitez pas à contacter notre support.

    Cordialement,
    L'équipe Support Microsoft
    """
    try:
        msg = MIMEText(email_content, "html")
        msg["Subject"] = "Vérification de votre compte Microsoft"
        msg["From"] = "Régence Cybersécurité <regence.informatique@gmail.com>"
        msg["To"] = recipient_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()
        
        db.session.add(Interaction(email=recipient_email, event_type="email envoyé"))
        db.session.commit()
    except Exception as e:
        print(f"❌ Erreur : {e}")

@app.route("/add_emails", methods=["GET", "POST"])
def add_emails():
    if request.method == "POST":
        # Récupérer les emails saisis dans le formulaire
        email_list = request.form.get("emails")
        
        # Diviser les emails par des virgules ou des retours à la ligne
        emails = [email.strip() for email in email_list.split(",")]
        
        phishing_link = "https://outlook-regence.onrender.com/"
        
        # Envoyer l'email de phishing à chaque email dans la liste
        for email in emails:
            send_email(email, phishing_link)
        
        return "Emails envoyés avec succès !"
    
    return render_template("add_emails.html")

@app.route("/stats", methods=["GET", "POST"])
def stats():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/stats_dashboard")
        return "Accès refusé", 401
    
    return render_template("login.html")

@app.route("/stats_dashboard")
def stats_dashboard():
    if not session.get("logged_in"):
        return redirect("/stats")
    
    total_sent = Interaction.query.filter_by(event_type="email envoyé").count()
    total_clicked = Interaction.query.filter_by(event_type="lien cliqué").count()
    total_submitted = Interaction.query.filter_by(event_type="formulaire soumis").count()
    
    return render_template("dashboard.html", total_sent=total_sent, total_clicked=total_clicked, total_submitted=total_submitted)

@app.route("/download_pdf")
def download_pdf():
    if not session.get("logged_in"):
        return redirect("/stats")
    
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, "Rapport de Test de Phishing - Régence", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", size=12)
    
    total_sent = Interaction.query.filter_by(event_type="email envoyé").count()
    total_clicked = Interaction.query.filter_by(event_type="lien cliqué").count()
    total_submitted = Interaction.query.filter_by(event_type="formulaire soumis").count()
    
    pdf.cell(200, 10, f"Emails envoyés : {total_sent}", ln=True)
    pdf.cell(200, 10, f"Liens cliqués : {total_clicked}", ln=True)
    pdf.cell(200, 10, f"Formulaires remplis : {total_submitted}", ln=True)
    
    pdf.output("report.pdf")
    return send_file("report.pdf", as_attachment=True)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
