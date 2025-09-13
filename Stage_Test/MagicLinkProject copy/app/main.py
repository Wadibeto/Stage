from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import firebase_admin
from firebase_admin import credentials, firestore
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone

app = FastAPI()

# Initialisation de Firebase
cred = credentials.Certificate("../backend/credentials/eternal-sylph-449610-r3-eb8969081109.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Configuration SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "wadi.belkacemi@gmail.com"
SMTP_PASSWORD = "prwq zrmf nafp uknm"

class EmailRequest(BaseModel):
    email: str

class MagicLinkRequest(BaseModel):
    email: str
    code: str

@app.post("/send-magic-link")
async def send_magic_link(request: EmailRequest):
    email = request.email

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    magic_code = secrets.token_hex(16)
    db.collection("users").document(email).set({"magic_code": magic_code}, merge=True)
    send_email(email, magic_code)

    return {"message": "Magic Link sent!"}

@app.post("/validate-magic-link")
async def validate_magic_link(request: MagicLinkRequest):
    email = request.email
    code = request.code

    if not email or not code:
        raise HTTPException(status_code=400, detail="Email et code sont requis")

    user_ref = db.collection("users").document(email)
    user_data = user_ref.get()

    if user_data.exists:
        stored_code = user_data.to_dict().get("magic_code")
        if stored_code == code:
            session_expiry = datetime.utcnow() + timedelta(seconds=30)
            user_ref.update({"session_expiry": session_expiry.timestamp()})
            return {"message": "Authentication successful", "session_expiry": session_expiry.timestamp()}
        else:
            raise HTTPException(status_code=401, detail="Invalid code")
    else:
        raise HTTPException(status_code=404, detail="Email not found")

@app.post("/check-session")
async def check_session(request: EmailRequest):
    email = request.email

    if not email:
        raise HTTPException(status_code=400, detail="Email requis")

    user_ref = db.collection("users").document(email)
    user_data = user_ref.get()

    if user_data.exists:
        user_info = user_data.to_dict()
        session_expiry = user_info.get("session_expiry")

        if session_expiry and datetime.now(timezone.utc).timestamp() < session_expiry:
            return {"message": "Session active"}
        else:
            user_ref.update({"session_expiry": None})
            raise HTTPException(status_code=401, detail="Session expirée")
    else:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")

@app.post("/update-activity")
async def update_activity(request: EmailRequest):
    email = request.email

    if not email:
        raise HTTPException(status_code=400, detail="Email requis")

    user_ref = db.collection("users").document(email)
    session_expiry = datetime.now(timezone.utc) + timedelta(seconds=30)
    user_ref.update({"session_expiry": session_expiry.timestamp()})

    return {"message": "Activité mise à jour"}

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)