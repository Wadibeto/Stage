import streamlit as st
import os
import shutil
import glob
import uuid
from PIL import Image
import re
import json
import subprocess
import time

TEMP_DIR = "processed_videos"
DEFAULT_IMG_DIR = "img"
OVERLAY_DIR = "overlays"
TITLE_DIR = "titles"
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(DEFAULT_IMG_DIR, exist_ok=True)
os.makedirs(OVERLAY_DIR, exist_ok=True)
os.makedirs(TITLE_DIR, exist_ok=True)

def get_video_segments():
    """Récupère les segments de vidéo triés."""
    segments = sorted(glob.glob(os.path.join(TEMP_DIR, "segment_*.mp4")))
    return segments if segments else None

def cleanup_old_videos():
    """Supprime les anciennes vidéos pour éviter les conflits."""
    try:
        # Supprimer tous les fichiers dans le dossier TEMP_DIR
        if os.path.exists(TEMP_DIR):
            for file in os.listdir(TEMP_DIR):
                file_path = os.path.join(TEMP_DIR, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    st.error(f"Erreur lors de la suppression de {file_path}: {e}")
            
            # Recréer le dossier pour s'assurer qu'il est vide
            shutil.rmtree(TEMP_DIR)
            os.makedirs(TEMP_DIR, exist_ok=True)
        else:
            os.makedirs(TEMP_DIR, exist_ok=True)
        
        # Supprimer les fichiers JSON
        json_files = glob.glob("*.json")
        for f in json_files:
            if os.path.exists(f):
                os.remove(f)
        
        # Supprimer la vidéo téléchargée
        if os.path.exists("video.mp4"):
            os.remove("video.mp4")
            
        st.success("Nettoyage réussi : tous les anciens fichiers ont été supprimés.")
    except Exception as e:
        st.error(f"Erreur lors du nettoyage des anciennes vidéos : {e}")
        
def check_ffmpeg_installation():
    """Vérifie que FFmpeg est correctement installé."""
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
        if result.returncode == 0:
            st.success("FFmpeg est correctement installé.")
            return True
        else:
            st.error("FFmpeg semble être installé mais ne fonctionne pas correctement.")
            return False
    except Exception as e:
        st.error(f"Erreur lors de la vérification de FFmpeg : {e}")
        st.error("FFmpeg n'est pas installé ou n'est pas dans le PATH.")
        return False

def get_image_count(img_dir):
    """Compte le nombre d'images dans le dossier."""
    image_files = glob.glob(os.path.join(img_dir, "*.jpg")) + \
                 glob.glob(os.path.join(img_dir, "*.jpeg")) + \
                 glob.glob(os.path.join(img_dir, "*.png")) + \
                 glob.glob(os.path.join(img_dir, "*.gif"))
    return len(image_files)

def get_overlay_images():
    """Récupère les images d'overlay PNG."""
    overlay_files = glob.glob(os.path.join(OVERLAY_DIR, "*.png"))
    return overlay_files

def get_title_templates():
    """Récupère les templates de titre disponibles."""
    template_files = glob.glob(os.path.join(TITLE_DIR, "*.json"))
    templates = []
    
    # Ajouter le template par défaut
    templates.append({
        "name": "Simple (par défaut)",
        "id": "default",
        "preview": None
    })
    
    # Ajouter les templates personnalisés
    for template_file in template_files:
        try:
            with open(template_file, 'r') as f:
                template = json.load(f)
                template_name = os.path.splitext(os.path.basename(template_file))[0]
                preview_path = os.path.join(TITLE_DIR, f"{template_name}.png")
                
                templates.append({
                    "name": template.get("name", template_name),
                    "id": template_name,
                    "preview": preview_path if os.path.exists(preview_path) else None,
                    "config": template
                })
        except Exception as e:
            st.error(f"Erreur lors du chargement du template {template_file}: {e}")
    
    return templates

def clean_youtube_url(url):
    """Nettoie l'URL YouTube pour éviter les problèmes de parsing."""
    # Extraire l'ID de la vidéo YouTube
    video_id = None
    
    # Format standard: https://www.youtube.com/watch?v=VIDEO_ID
    match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url)
    if match:
        video_id = match.group(1)
    
    if video_id:
        return f"https://www.youtube.com/watch?v={video_id}"
    return url

def remove_processed_content():
    """Supprime les vidéos et segments convertis."""
    try:
        # Supprimer les segments
        segments = glob.glob(os.path.join(TEMP_DIR, "segment_*.mp4"))
        for segment in segments:
            os.remove(segment)
        
        # Supprimer les fichiers temporaires
        temp_files = glob.glob(os.path.join(TEMP_DIR, "temp_*.mp4")) + \
                    glob.glob(os.path.join(TEMP_DIR, "formatted_*.mp4")) + \
                    glob.glob(os.path.join(TEMP_DIR, "filter_script_*.txt")) + \
                    glob.glob(os.path.join(TEMP_DIR, "title_*.png"))
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        
        # Supprimer le fichier JSON de métadonnées
        json_file = os.path.join(os.getcwd(), "video_metadata.json")
        if os.path.exists(json_file):
            os.remove(json_file)
            
        # Supprimer la vidéo uploadée
        uploaded_video = os.path.join(TEMP_DIR, "uploaded.mp4")
        if os.path.exists(uploaded_video):
            os.remove(uploaded_video)
            
        st.success("Tous les fichiers traités ont été supprimés avec succès.")
    except Exception as e:
        st.error(f"Erreur lors de la suppression des fichiers : {e}")

# Interface Streamlit
st.title("Convertisseur de vidéos en format vertical 📱")

# Section pour le texte d'introduction
st.subheader("Texte d'introduction")
intro_text = st.text_input("Texte à afficher au début de la vidéo", 
                        placeholder="Entrez votre texte ici", 
                        help="Ce texte sera affiché en grand au début de chaque segment de vidéo")

# Options de style pour le texte d'introduction
with st.expander("Style du texte d'introduction", expanded=False):
    intro_text_size = st.slider("Taille du texte", 30, 100, 60)
    intro_text_color = st.color_picker("Couleur du texte", "#FFFFFF")
    intro_text_bg = st.checkbox("Ajouter un fond au texte", value=True)
    intro_text_bg_opacity = st.slider("Opacité du fond", 0.0, 1.0, 0.5, 0.1) if intro_text_bg else 0.0
    intro_text_duration = st.slider("Durée d'affichage (secondes)", 2.0, 10.0, 5.0, 0.5)
    
    # Prévisualisation du texte
    if intro_text:
        st.markdown("### Prévisualisation:")
        bg_color = "rgba(0,0,0,{})".format(intro_text_bg_opacity) if intro_text_bg else "transparent"
        preview_html = f"""
        <div style="background-color: {bg_color}; 
                    padding: 20px; 
                    text-align: center; 
                    border-radius: 10px;">
            <p style="color: {intro_text_color}; 
                      font-size: {intro_text_size}px; 
                      font-weight: bold; 
                      margin: 0;">
                {intro_text}
            </p>
        </div>
        """
        st.markdown(preview_html, unsafe_allow_html=True)

# Section pour les overlays PNG
with st.expander("Overlay PNG pour la vidéo", expanded=True):
    st.write("Ajoutez une image PNG qui sera superposée sur toute la durée de votre vidéo (comme un overlay Twitch).")
    
    # Affichage des overlays existants
    overlay_files = get_overlay_images()
    selected_overlay = None
    
    if overlay_files:
        st.success(f"{len(overlay_files)} overlays PNG disponibles")
        
        # Créer une grille pour afficher les overlays
        cols = st.columns(3)
        for i, overlay_file in enumerate(overlay_files):
            with cols[i % 3]:
                img = Image.open(overlay_file)
                st.image(overlay_file, caption=os.path.basename(overlay_file), use_column_width=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Utiliser", key=f"use_{i}"):
                        selected_overlay = overlay_file
                        st.session_state.selected_overlay = overlay_file
                with col2:
                    if st.button(f"Supprimer", key=f"del_{i}"):
                        os.remove(overlay_file)
                        if 'selected_overlay' in st.session_state and st.session_state.selected_overlay == overlay_file:
                            st.session_state.selected_overlay = None
                        st.experimental_rerun()
    else:
        st.info("Aucun overlay PNG trouvé. Ajoutez-en ci-dessous.")
    
    # Upload de nouveaux overlays PNG
    uploaded_overlay = st.file_uploader("Ajouter un nouvel overlay PNG", type=["png"], accept_multiple_files=False)
    if uploaded_overlay:
        # Générer un nom de fichier unique
        file_extension = os.path.splitext(uploaded_overlay.name)[1]
        unique_filename = f"overlay_{uuid.uuid4().hex[:8]}{file_extension}"
        file_path = os.path.join(OVERLAY_DIR, unique_filename)
        
        # Sauvegarder le fichier
        with open(file_path, "wb") as f:
            f.write(uploaded_overlay.getvalue())
        
        # Afficher l'aperçu
        st.success(f"Overlay '{unique_filename}' ajouté avec succès!")
        st.image(file_path, caption=unique_filename, width=300)
        
        # Utiliser automatiquement ce nouvel overlay
        st.session_state.selected_overlay = file_path
        st.info("Cet overlay sera utilisé pour la prochaine conversion.")

    # Afficher l'overlay actuellement sélectionné
    if 'selected_overlay' in st.session_state and st.session_state.selected_overlay:
        st.success(f"Overlay sélectionné : {os.path.basename(st.session_state.selected_overlay)}")
        st.image(st.session_state.selected_overlay, width=200)
    else:
        st.warning("Aucun overlay sélectionné. Veuillez en choisir un pour l'appliquer à votre vidéo.")

# Paramètres avancés dans une section dépliable
with st.expander("Paramètres avancés"):
    col1, col2 = st.columns(2)
    
    with col1:
        img_dir = st.text_input("Dossier d'images", DEFAULT_IMG_DIR)
        
        # Vérifier si le dossier existe et contient des images
        if not os.path.exists(img_dir):
            st.warning(f"Le dossier {img_dir} n'existe pas. Le dossier par défaut sera utilisé.")
            img_dir = DEFAULT_IMG_DIR
        
        image_count = get_image_count(img_dir)
        if image_count == 0:
            st.warning(f"Aucune image trouvée dans {img_dir}. Veuillez ajouter des images (jpg, jpeg, png, gif).")
        else:
            st.success(f"{image_count} images trouvées dans {img_dir}")
        
        images_per_segment = st.slider("Nombre d'images par segment", 1, 10, 3)
    
    with col2:
        video_format = st.radio("Format de la vidéo", ["vertical", "horizontal"], index=0)
        
        if video_format == "vertical":
            video_size = st.slider("Largeur de la vidéo (pixels)", 320, 720, 480, step=80)
            st.info(f"Hauteur calculée: {int(video_size * 16/9)} pixels")
        else:
            video_size = st.slider("Hauteur de la vidéo (pixels)", 360, 1080, 720, step=90)
            st.info(f"Largeur calculée: {int(video_size * 16/9)} pixels")

# Définir des valeurs par défaut pour les paramètres
if 'video_format' not in locals():
    video_format = "vertical"
if 'video_size' not in locals():
    video_size = 480

option = st.radio("Choisissez votre méthode :", ("Lien YouTube", "Upload de fichier"))

# Préparation des paramètres d'overlay pour la commande Go
overlay_params = ""
if hasattr(st.session_state, 'selected_overlay') and st.session_state.selected_overlay:
    overlay_params = f" -overlay \"{st.session_state.selected_overlay}\""

# Modifiez la section qui prépare les paramètres de texte pour la commande Go
# Remplacez cette partie dans votre code:

# Préparation du paramètre de texte d'introduction pour la commande Go
intro_params = ""
if intro_text:
    # Échapper les caractères spéciaux dans le texte pour éviter les problèmes de commande
    escaped_intro_text = intro_text.replace('"', '\\"').replace("'", "\\'").replace("\\", "\\\\")
    
    # Vérifier que les couleurs sont au bon format
    if not intro_text_color.startswith('#'):
        intro_text_color = "#FFFFFF"  # Valeur par défaut
    
    # S'assurer que la couleur de fond a le bon format
    bg_color_param = "#000000AA"  # Valeur par défaut avec transparence
    if intro_text_bg:
        bg_opacity_hex = f"{int(intro_text_bg_opacity*255):02x}"
        bg_color_param = f"#000000{bg_opacity_hex}"
    
    # Utiliser les paramètres corrects qui correspondent à ceux définis dans main.go
    intro_params = f" -custom-text \"{escaped_intro_text}\" -text-color \"{intro_text_color}\" -text-size {intro_text_size} -text-duration {intro_text_duration}"
    
    # Ajouter les paramètres de fond si nécessaire
    if intro_text_bg:
        intro_params += f" -text-bg-color \"{bg_color_param}\""

# Ajoutez une fonction de débogage pour vérifier la commande Go
def debug_go_command(cmd):
    """Affiche et vérifie la commande Go avant de l'exécuter."""
    st.code(cmd, language="bash")
    st.info("Vérifiez la commande ci-dessus. Si elle semble correcte, cliquez sur 'Exécuter'.")
    return st.button("Exécuter")

# Modifiez la partie qui exécute la commande Go pour ajouter plus de vérifications
# Dans la section où vous exécutez la commande Go, ajoutez:

# Modifier la partie qui exécute la commande Go pour ajouter plus de vérifications
if option == "Lien YouTube":
    youtube_url = st.text_input("Entrez l'URL de la vidéo YouTube :")
    if st.button("Convertir") and youtube_url:
        # Vérifier que FFmpeg est installé
        if not check_ffmpeg_installation():
            st.error("FFmpeg est requis pour le traitement des vidéos.")
            st.info("Veuillez installer FFmpeg : https://ffmpeg.org/download.html")
        else:
            # Nettoyage automatique avant la conversion
            cleanup_old_videos()
            
            # Nettoyer l'URL YouTube
            cleaned_url = clean_youtube_url(youtube_url)
            
            # Commande avec les nouveaux paramètres
            cmd = f'go run main.go -url "{cleaned_url}" -output {TEMP_DIR} -img {img_dir} -images {images_per_segment} -format {video_format} -size {video_size}{overlay_params}{intro_params}'

            # Afficher la commande pour débogage
            st.info("Commande qui sera exécutée:")
            st.code(cmd)

            # Option pour voir les détails de la commande
            with st.expander("Détails des paramètres"):
                st.write("Paramètres de texte:")
                if intro_text:
                    st.write(f"- Texte: {intro_text}")
                    st.write(f"- Couleur: {intro_text_color}")
                    st.write(f"- Taille: {intro_text_size}")
                    st.write(f"- Durée: {intro_text_duration}s")
                    if intro_text_bg:
                        st.write(f"- Fond: Activé (opacité: {intro_text_bg_opacity})")
                else:
                    st.write("Aucun texte personnalisé")
            
            # Exécuter la commande avec plus de détails sur les erreurs
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Afficher un message de chargement
            with st.spinner("Traitement de la vidéo en cours..."):
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    st.error(f"Erreur lors de l'exécution de la commande Go :")
                    st.code(stderr)
                    # Afficher les logs FFmpeg s'ils existent
                    ffmpeg_log = os.path.join(TEMP_DIR, "ffmpeg_log.txt")
                    if os.path.exists(ffmpeg_log):
                        with open(ffmpeg_log, "r") as f:
                            st.error("Logs FFmpeg:")
                            st.code(f.read())
                else:
                    st.success("Commande exécutée avec succès!")
                    
                    # Attendre un peu pour s'assurer que les fichiers sont bien créés
                    time.sleep(1)
            
            # Vérifier si les segments ont été créés
            segments = get_video_segments()
            if segments:
                st.success(f"{len(segments)} segments créés avec succès!")
                for segment in segments:
                    st.video(segment)
            else:
                st.error("Erreur : Aucun segment trouvé.")
                st.error("Vérifiez les messages d'erreur ci-dessus pour plus de détails.")
                
                # Vérifier si le dossier existe et s'il contient des fichiers
                if os.path.exists(TEMP_DIR):
                    files = os.listdir(TEMP_DIR)
                    if files:
                        st.info(f"Le dossier {TEMP_DIR} contient {len(files)} fichiers : {', '.join(files)}")
                    else:
                        st.warning(f"Le dossier {TEMP_DIR} existe mais est vide.")
                else:
                    st.warning(f"Le dossier {TEMP_DIR} n'existe pas.")

elif option == "Upload de fichier":
    uploaded_file = st.file_uploader("Chargez votre vidéo (.mp4)", type=["mp4"])
    
    # Option pour uploader des images
    with st.expander("Uploader des images (optionnel)"):
        uploaded_images = st.file_uploader("Ajoutez des images pour les superposer", 
                                          type=["jpg", "jpeg", "png", "gif"], 
                                          accept_multiple_files=True)
        
        if uploaded_images:
            # Sauvegarder les images uploadées
            for img in uploaded_images:
                with open(os.path.join(img_dir, img.name), "wb") as f:
                    f.write(img.getvalue())
            st.success(f"{len(uploaded_images)} images uploadées avec succès!")
    
    if uploaded_file and st.button("Convertir"):
        # Vérifier que FFmpeg est installé
        if not check_ffmpeg_installation():
            st.error("FFmpeg est requis pour le traitement des vidéos.")
            st.info("Veuillez installer FFmpeg : https://ffmpeg.org/download.html")
        else:
            # Nettoyage automatique avant la conversion
            cleanup_old_videos()
            
            # S'assurer que le dossier existe
            os.makedirs(TEMP_DIR, exist_ok=True)
            
            input_file = os.path.join(TEMP_DIR, "uploaded.mp4")
            with open(input_file, "wb") as f:
                f.write(uploaded_file.read())
            
            # Commande avec les nouveaux paramètres
            cmd = f'go run main.go -input "{input_file}" -output {TEMP_DIR} -img {img_dir} -images {images_per_segment} -format {video_format} -size {video_size}{overlay_params}{intro_params}'
            
            # Afficher la commande pour débogage
            st.info("Commande qui sera exécutée:")
            st.code(cmd)

            # Option pour voir les détails de la commande
            with st.expander("Détails des paramètres"):
                st.write("Paramètres de texte:")
                if intro_text:
                    st.write(f"- Texte: {intro_text}")
                    st.write(f"- Couleur: {intro_text_color}")
                    st.write(f"- Taille: {intro_text_size}")
                    st.write(f"- Durée: {intro_text_duration}s")
                    if intro_text_bg:
                        st.write(f"- Fond: Activé (opacité: {intro_text_bg_opacity})")
                else:
                    st.write("Aucun texte personnalisé")
            
            # Exécuter la commande avec plus de détails sur les erreurs
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Afficher un message de chargement
            with st.spinner("Traitement de la vidéo en cours..."):
                stdout, stderr = process.communicate()
                
                if process.returncode != 0:
                    st.error(f"Erreur lors de l'exécution de la commande Go :")
                    st.code(stderr)
                    # Afficher les logs FFmpeg s'ils existent
                    ffmpeg_log = os.path.join(TEMP_DIR, "ffmpeg_log.txt")
                    if os.path.exists(ffmpeg_log):
                        with open(ffmpeg_log, "r") as f:
                            st.error("Logs FFmpeg:")
                            st.code(f.read())
                else:
                    st.success("Commande exécutée avec succès!")
                    
                    # Attendre un peu pour s'assurer que les fichiers sont bien créés
                    time.sleep(1)
            
            # Vérifier si les segments ont été créés
            segments = get_video_segments()
            if segments:
                st.success(f"{len(segments)} segments créés avec succès!")
                for segment in segments:
                    st.video(segment)
            else:
                st.error("Erreur : Aucun segment trouvé.")
                st.error("Vérifiez les messages d'erreur ci-dessus pour plus de détails.")
                
                # Vérifier si le dossier existe et s'il contient des fichiers
                if os.path.exists(TEMP_DIR):
                    files = os.listdir(TEMP_DIR)
                    if files:
                        st.info(f"Le dossier {TEMP_DIR} contient {len(files)} fichiers : {', '.join(files)}")
                    else:
                        st.warning(f"Le dossier {TEMP_DIR} existe mais est vide.")
                else:
                    st.warning(f"Le dossier {TEMP_DIR} n'existe pas.")

# Bouton pour supprimer les vidéos et segments traités
st.subheader("Nettoyage")
if st.button("Supprimer les vidéos et segments traités"):
    remove_processed_content()