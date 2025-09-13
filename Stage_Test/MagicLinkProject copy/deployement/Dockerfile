# Utiliser une image de base Python
FROM python:3.9-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers requirements.txt (à créer) et installer les dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier l'ensemble du projet
COPY . .

# Exposer le port (Streamlit par défaut sur 8501)
EXPOSE 8501

# Lancer l'application Streamlit
CMD ["bash", "-c", "streamlit run app.py --server.enableCORS=false --server.port ${PORT:-8080}"]