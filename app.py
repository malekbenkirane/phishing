from flask import Flask, render_template, request, redirect, Response, send_file, session
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
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
with app.app_context():
    db.create_all()

# Identifiants admin
ADMIN_USERNAME = "Reg"
ADMIN_PASSWORD = "Saouda2025!!"

# Configuration SMTP Office365
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
SENDER_EMAIL = "regence.informatique@liquidationtravail.com"
SENDER_PASSWORD = "Saouda2025!!"

def send_email(recipient_email, recipient_name, phishing_link):
    email_content = f"""
    Bonjour {recipient_name},
    
    Votre compte Microsoft nécessite une vérification urgente pour éviter une interruption de service.
    Veuillez confirmer votre identité dès maintenant :
    
    👉 <a href=\"{phishing_link}\">Cliquez ici pour valider votre compte</a>
    
    Merci de votre coopération.
    L'équipe Microsoft Sécurité
    """
    try:
        msg = MIMEText(email_content, "html")
        msg["Subject"] = "Action requise : Vérification de votre compte Microsoft"
        msg["From"] = f"Microsoft Support <{SENDER_EMAIL}>"
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

@app.route("/send_email", methods=["POST"])
def send_email_route():
    recipient_email = request.form.get("recipient_email")
    recipient_name = request.form.get("recipient_name")
    phishing_link = "https://outlook-regence.onrender.com/login"  # Redirection vers la page de phishing
    
    if recipient_email and recipient_name:
        send_email(recipient_email, recipient_name, phishing_link)
        return f"Email envoyé à {recipient_name} ({recipient_email}) avec succès !"
    
    return "Erreur : Email ou Nom manquant.", 400

@app.route("/", methods=["GET", "POST"])
def home():
    # Redirige vers la page de phishing (login)
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        # Enregistrez les identifiants dans la base de données ou traitez les données comme vous le souhaitez
        db.session.add(Interaction(email=email, event_type="formulaire soumis"))
        db.session.commit()
        return "Merci de vous être connecté. Vos informations ont été reçues."
    
    return render_template("login.html")

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
    
    labels = ["Emails envoyés", "Liens cliqués", "Formulaires remplis"]
    values = [total_sent, total_clicked, total_submitted]
    plt.figure(figsize=(6,6))
    plt.pie(values, labels=labels, autopct="%1.1f%%", colors=["blue", "orange", "red"])
    plt.title("Statistiques du test de phishing")
    plt.savefig("static/stats.png")
    
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
