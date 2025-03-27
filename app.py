from flask import Flask, render_template, request, redirect, session, send_file
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

# Fonction pour envoyer un email de phishing avec un problème lié à Outlook
def send_email(recipient_email, recipient_name, phishing_link):
    email_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <p>Bonjour <strong>{recipient_name}</strong>,</p>

        <p>Nous rencontrons actuellement un problème technique affectant certains comptes Outlook au sein de notre organisation. En raison d’une mise à jour récente, 
        certains utilisateurs pourraient rencontrer des difficultés d'accès à leurs emails ou voir des erreurs de synchronisation.</p>

        <p><strong>Action requise :</strong><br>
        Afin d’éviter toute interruption de service, nous vous invitons à réauthentifier votre compte Microsoft en suivant la procédure ci-dessous.</p>

        <p style="text-align: center;">
            <a href="{phishing_link}" style="background-color: #0078D4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-size: 16px;">
                Réauthentifier mon compte
            </a>
        </p>

        <p>Cette opération ne prendra que quelques instants et permettra de restaurer l’accès normal à votre boîte mail.</p>

        <p>Si vous avez des questions ou rencontrez des difficultés, n’hésitez pas à contacter notre support technique.</p>

        <hr>
        <p><strong>Département Informatique - Régence</strong><br>
        ?? Assistance IT Régence<br>
        ?? www.regence.com<br>
        ?? 655 Rue de l'Argon, Québec, QC G2N 2G7</p>
    </body>
    </html>
    """
    try:
        msg = MIMEText(email_content, "html")
        msg["Subject"] = "Problème d'accès à Outlook - Action requise"
        msg["From"] = f"Département Informatique <{SENDER_EMAIL}>"
        msg["To"] = recipient_email

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
        server.quit()

        db.session.add(Interaction(email=recipient_email, event_type="email envoyé"))
        db.session.commit()
        print(f"? Email envoyé à {recipient_email}")

    except Exception as e:
        print(f"? Erreur lors de l'envoi de l'email : {e}")

@app.route("/")
def home():
    return render_template("index.html")  # Page d'accueil

# Route pour afficher le formulaire de login pour accéder à l'envoi d'email
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/send_email")  # Si l'utilisateur est authentifié, rediriger vers la page d'envoi d'email
        return "Accès refusé", 401  # Si les identifiants sont incorrects
    
    return render_template("login.html")  # Page de connexion

# Route pour envoyer un email de phishing
import csv
from werkzeug.utils import secure_filename

@app.route("/send_email", methods=["GET", "POST"])
def send_email_route():
    if not session.get("logged_in"):  # Vérifier si l'utilisateur est connecté
        return redirect("/login")  # Rediriger vers la page de login si non connecté

    if request.method == "POST":
        # Vérifier si un fichier CSV est téléchargé
        file = request.files.get("csv_file")
        if file and file.filename.endswith('.csv'):
            # Sauvegarder le fichier CSV
            filename = secure_filename(file.filename)
            file_path = os.path.join("uploads", filename)
            file.save(file_path)

            # Lire les emails et noms depuis le fichier CSV
            try:
                with open(file_path, mode="r", newline="") as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)  # Ignorer l'entête du fichier CSV

                    # Envoi des emails de phishing à chaque destinataire
                    phishing_link = "https://outlook-regence.onrender.com"  # Lien de phishing
                    for row in reader:
                        if len(row) >= 2:  # Vérifier qu'il y a au moins un email et un nom
                            recipient_email = row[0].strip()
                            recipient_name = row[1].strip()
                            send_email(recipient_email, recipient_name, phishing_link)

                    return f"Emails envoyés avec succès à tous les destinataires du fichier CSV."
            except Exception as e:
                return f"Erreur lors du traitement du fichier CSV : {e}", 500
        
        # Sinon, envoyer un email à un seul destinataire
        recipient_email = request.form.get("recipient_email")
        recipient_name = request.form.get("recipient_name")
        
        if recipient_email and recipient_name:
            phishing_link = "https://outlook-regence.onrender.com"  # Lien de phishing
            send_email(recipient_email, recipient_name, phishing_link)
            return f"Email envoyé à {recipient_name} ({recipient_email}) avec succès !"

        return "Erreur : Email ou Nom manquant.", 400

    return render_template("send_email.html")  # Page pour envoyer un email


# Route pour afficher le formulaire de login pour accéder aux statistiques
@app.route("/stats", methods=["GET", "POST"])
def stats():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/stats_dashboard")
        return "Accès refusé", 401
    
    return render_template("login.html")  # Page de connexion admin

# Route pour afficher le tableau de bord des statistiques
@app.route("/stats_dashboard")
def stats_dashboard():
    if not session.get("logged_in"):
        return redirect("/stats")
    
    # Calcul des statistiques sans vérifier NaN, car SQLAlchemy retourne des entiers
    total_sent = db.session.query(db.func.coalesce(db.func.count(Interaction.id), 0)).filter_by(event_type="email envoyé").scalar()
    total_clicked = db.session.query(db.func.coalesce(db.func.count(Interaction.id), 0)).filter_by(event_type="lien cliqué").scalar()
    total_submitted = db.session.query(db.func.coalesce(db.func.count(Interaction.id), 0)).filter_by(event_type="formulaire soumis").scalar()

    # Gestion des valeurs non valides ou nulles
    total_sent = 0 if total_sent is None or total_sent < 0 else int(total_sent)
    total_clicked = 0 if total_clicked is None or total_clicked < 0 else int(total_clicked)
    total_submitted = 0 if total_submitted is None or total_submitted < 0 else int(total_submitted)

    # Liste des valeurs à afficher dans le graphique
    values = [total_sent, total_clicked, total_submitted]

    # Vérification que toutes les valeurs sont des entiers non négatifs
    values = [max(0, value) for value in values]

    labels = ["Emails envoyés", "Liens cliqués", "Formulaires remplis"]
    
    # Générer les statistiques sous forme de graphique (par exemple, un graphique en camembert)
    try:
        plt.figure(figsize=(6,6))
        plt.pie(values, labels=labels, autopct="%1.1f%%", colors=["blue", "orange", "red"])
        plt.title("Statistiques du test de phishing")
        plt.savefig("static/stats.png")
        plt.close()
    except Exception as e:
        print(f"Erreur lors de la génération du graphique : {e}")

    # Explication à afficher sur le tableau de bord
    explanation = "Les graphiques ci-dessus montrent les résultats du test de phishing réalisé. " \
                  "Les emails envoyés sont suivis des liens cliqués et des formulaires soumis. " \
                  "Utilisez ces données pour évaluer les vulnérabilités."

    # Afficher le tableau de bord avec les valeurs calculées
    return render_template("dashboard.html", 
                           total_sent=total_sent, 
                           total_clicked=total_clicked, 
                           total_submitted=total_submitted,
                           explanation=explanation)

# Route pour télécharger le rapport au format PDF
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
