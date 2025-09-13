# File: MagicLinkProject/app/utils.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD

def send_email(email, code):
    try:
        subject = "Votre Magic Link"
        body = f"Votre code de connexion est : {code}\nOu cliquez ici pour vous connecter : http://localhost:8501"

        msg = MIMEMultipart()
        msg["From"] = SMTP_EMAIL
        msg["To"] = email
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, email, msg.as_string())

    except Exception as e:
        print(f"Erreur lors de l'envoi de l'email : {e}")
        # Vous pourriez vouloir lever une exception ici pour la gérer dans l'appelant