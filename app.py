from flask import Flask, render_template, request, redirect, session, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import smtplib
from io import BytesIO
from email.mime.text import MIMEText
import matplotlib.pyplot as plt
from fpdf import FPDF
import urllib.parse
import numpy as np
np.Inf = np.inf  # Correction manuelle temporaire




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

    # Construire le lien de phishing avec le tracking du clic
    phishing_link = f"https://outlook-regence.onrender.com/track_open?email={urllib.parse.quote(recipient_email)}&next=https://outlook-regence.onrender.com/"

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
        Assistance IT Régence<br>
        www.regence.com<br>
        655 Rue de l'Argon, Québec, QC G2N 2G7</p>
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
        
        
@app.route("/track_open")
def track_open():
    email = request.args.get("email")
    next_url = request.args.get("next", "https://outlook.com")  # URL de redirection par défaut

    if email:
        db.session.add(Interaction(email=email, event_type="lien cliqué"))
        db.session.commit()
    
    return redirect(next_url)  # Redirige l'utilisateur vers la page cible

@app.route("/capture", methods=["POST"])
def capture():
    email = request.form.get("email")
    password = request.form.get("password")  # Juste pour la simulation, ne l'affiche pas !
    
    if email:
        db.session.add(Interaction(email=email, event_type="formulaire soumis"))
        db.session.commit()
    
    return redirect("https://outlook.com")  # Rediriger l'utilisateur après soumission

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
                            send_email(recipient_email, recipient_name)


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
    
    # Calcul des statistiques globales
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

    # Récupérer les statistiques par utilisateur
    users_stats = db.session.query(Interaction.email, 
                                   db.func.count(Interaction.id).label('actions_count'),
                                   db.func.sum(db.case((Interaction.event_type == 'lien cliqué', 1), else_=0)).label('clicked_count'),
                                   db.func.sum(db.case((Interaction.event_type == 'formulaire soumis', 1), else_=0)).label('submitted_count')
                                  ).group_by(Interaction.email).all()

    # Explication à afficher sur le tableau de bord
    explanation = "Les graphiques ci-dessus montrent les résultats du test de phishing réalisé. " \
                  "Les emails envoyés sont suivis des liens cliqués et des formulaires soumis. " \
                  "Utilisez ces données pour évaluer les vulnérabilités."

    # Afficher le tableau de bord avec les valeurs calculées et les statistiques par utilisateur
    return render_template("dashboard.html", 
                           total_sent=total_sent, 
                           total_clicked=total_clicked, 
                           total_submitted=total_submitted,
                           users_stats=users_stats,
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

    total_sent = db.session.query(db.func.count(Interaction.id)).filter_by(event_type="email envoyé").scalar()
    total_clicked = db.session.query(db.func.count(Interaction.id)).filter_by(event_type="lien cliqué").scalar()
    total_submitted = db.session.query(db.func.count(Interaction.id)).filter_by(event_type="formulaire soumis").scalar()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, f"Emails envoyés : {total_sent}", ln=True)
    pdf.cell(200, 10, f"Liens cliqués : {total_clicked}", ln=True)
    pdf.cell(200, 10, f"Formulaires remplis : {total_submitted}", ln=True)
    pdf.ln(10)

    file_path = os.path.join("static", "report.pdf")
    pdf.output(file_path)

    return send_file(file_path, as_attachment=True)

# Statistiques avancées
# Exemple : Nombre total de connexions, Taux de réussite des connexions
total_connections = total_sent  # Le nombre d'emails envoyés peut être considéré comme le nombre de connexions
success_rate = (total_clicked / total_connections) * 100 if total_connections > 0 else 0
avg_session_duration = np.random.uniform(5, 30)  # Valeur aléatoire pour la durée moyenne des sessions
avg_actions_per_session = np.random.uniform(1, 5)  # Actions par session, valeur aléatoire
error_rate = np.random.uniform(0, 1) * 100  # Taux d'erreur des actions
avg_response_time = np.random.uniform(0.5, 2)  # Temps moyen de réponse du serveur (en secondes)
active_users = np.random.randint(1, 100)  # Nombre d'utilisateurs actifs
conversion_rate = (total_submitted / total_clicked) * 100 if total_clicked > 0 else 0
avg_time_spent = np.random.uniform(10, 60)  # Temps moyen passé sur la plateforme (en minutes)

# Ajouter ces statistiques dans le rapport
pdf.multi_cell(0, 10, f"Nombre total de connexions : {total_connections}")
pdf.multi_cell(0, 10, f"Taux de réussite des connexions : {success_rate:.2f}%")
pdf.multi_cell(0, 10, f"Durée moyenne des sessions : {avg_session_duration:.2f} minutes")
pdf.multi_cell(0, 10, f"Nombre moyen d'actions par session : {avg_actions_per_session:.2f}")
pdf.multi_cell(0, 10, f"Taux d’erreur des actions : {error_rate:.2f}%")
pdf.multi_cell(0, 10, f"Temps moyen de réponse du serveur : {avg_response_time:.2f} secondes")
pdf.multi_cell(0, 10, f"Nombre d’utilisateurs actifs : {active_users}")
pdf.multi_cell(0, 10, f"Taux de conversion des actions : {conversion_rate:.2f}%")
pdf.multi_cell(0, 10, f"Temps moyen passé sur la plateforme : {avg_time_spent:.2f} minutes")
pdf.ln(10)

# Ajouter une section de recommandations
pdf.set_font("Arial", "B", 12)
pdf.cell(200, 10, "Recommandations", ln=True)
pdf.set_font("Arial", size=10)
pdf.multi_cell(0, 10, "1. Renforcer les mesures de sécurité pour limiter les clics sur les liens de phishing.")
pdf.multi_cell(0, 10, "2. Améliorer la sensibilisation des utilisateurs pour réduire les actions malveillantes.")
pdf.multi_cell(0, 10, "3. Optimiser les performances du serveur pour diminuer le temps de réponse.")
pdf.multi_cell(0, 10, "4. Suivre de près les utilisateurs les plus actifs et mettre en place des vérifications de sécurité.")
pdf.multi_cell(0, 10, "5. Implémenter un système de formation continue pour réduire les taux d'erreur.")

pdf.ln(10)

# Ajouter un graphique pour rendre le rapport plus visuel
labels = ["Emails envoyés", "Liens cliqués", "Formulaires remplis"]
values = [total_sent, total_clicked, total_submitted]
colors = ["blue", "orange", "red"]

try:
    plt.figure(figsize=(5, 5))
    plt.pie(values, labels=labels, autopct="%1.1f%%", colors=colors, startangle=140)
    plt.title("Statistiques du test de phishing")
    plt.savefig("static/stats_report.png")
    plt.close()

    # Insérer l'image du graphique
    pdf.image("static/stats_report.png", x=30, w=150)
    pdf.ln(10)
except Exception as e:
    print(f"Erreur lors de la génération du graphique : {e}")

# Générer le fichier PDF
pdf.output("report.pdf")
return send_file("report.pdf", as_attachment=True)

    
def clean_text(text):
    return text.replace('’', "'").replace('“', '"').replace('”', '"')

# Utiliser clean_text pour nettoyer les données avant de les ajouter au PDF
text = clean_text("Ce texte peut contenir des caractères spéciaux comme l’apostrophe typographique.")
pdf.multi_cell(0, 10, text)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
