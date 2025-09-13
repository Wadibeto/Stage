package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"io/ioutil"
	"math"
	"math/rand"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type VideoSegment struct {
	Format             string `json:"format"`
	IntroductionEffect string `json:"introductionEffect,omitempty"`
	TimeSpan           string `json:"timespan"`
	Title              string `json:"title,omitempty"`
	Subtitle           string `json:"subtitle,omitempty"`
	IntroText          string `json:"introText,omitempty"`
	CustomText         string `json:"customText,omitempty"`
	AudioEffectPreset  struct {
		Compression string `json:"compression"`
		FadeInOut   string `json:"fadeInOut"`
	} `json:"audioEffectPreset"`
	Effect struct {
		EffectType       string `json:"effectType"`
		TimeSpanRelative string `json:"timespanRelative"`
	} `json:"effect"`
	ImageOverlays []ImageOverlay `json:"imageOverlays,omitempty"`
}

type ImageOverlay struct {
	ImagePath string `json:"imagePath"`
	StartTime string `json:"startTime"`
	Duration  string `json:"duration"`
}

type VideoMetadata struct {
	Segments []VideoSegment `json:"segments"`
}

type TitleTemplate struct {
	Name       string `json:"name"`
	Background string `json:"background"`
	Gradient   struct {
		Start     string `json:"start"`
		End       string `json:"end"`
		Direction string `json:"direction"`
	} `json:"gradient"`
	Title struct {
		Font   string `json:"font"`
		Size   string `json:"size"`
		Weight string `json:"weight"`
		Shadow bool   `json:"shadow"`
	} `json:"title"`
	Subtitle struct {
		Font   string `json:"font"`
		Size   string `json:"size"`
		Weight string `json:"weight"`
	} `json:"subtitle"`
	Animation string `json:"animation"`
}

// Supprime et recrée le dossier de sortie
func resetProcessedVideosFolder(folder string) error {
	if _, err := os.Stat(folder); err == nil {
		fmt.Println("Suppression de l'ancien dossier", folder)
		if err := os.RemoveAll(folder); err != nil {
			return fmt.Errorf("échec de la suppression du dossier: %v", err)
		}
	}
	fmt.Println("Création du dossier", folder)
	return os.MkdirAll(folder, os.ModePerm)
}

// Récupère la durée totale de la vidéo en secondes
func getVideoDuration(input string) (int, error) {
	cmd := exec.Command("ffprobe", "-v", "error", "-select_streams", "v:0",
		"-show_entries", "format=duration", "-of", "csv=p=0", input)
	output, err := cmd.Output()
	if err != nil {
		return 0, fmt.Errorf("erreur lors de la récupération de la durée: %v", err)
	}
	duration, err := strconv.ParseFloat(strings.TrimSpace(string(output)), 64)
	if err != nil {
		return 0, fmt.Errorf("échec de la conversion de la durée: %v", err)
	}
	return int(duration), nil
}

// Récupère les dimensions de la vidéo
func getVideoDimensions(input string) (int, int, error) {
	cmd := exec.Command("ffprobe", "-v", "error", "-select_streams", "v:0",
		"-show_entries", "stream=width,height", "-of", "csv=p=0", input)
	output, err := cmd.Output()
	if err != nil {
		return 0, 0, fmt.Errorf("erreur lors de la récupération des dimensions: %v", err)
	}

	parts := strings.Split(strings.TrimSpace(string(output)), ",")
	if len(parts) != 2 {
		return 0, 0, fmt.Errorf("format de sortie inattendu pour les dimensions: %s", output)
	}

	width, err := strconv.Atoi(parts[0])
	if err != nil {
		return 0, 0, fmt.Errorf("échec de la conversion de la largeur: %v", err)
	}

	height, err := strconv.Atoi(parts[1])
	if err != nil {
		return 0, 0, fmt.Errorf("échec de la conversion de la hauteur: %v", err)
	}

	return width, height, nil
}

// Récupère toutes les images du dossier img/
func getImageFiles(imgFolder string) ([]string, error) {
	files, err := ioutil.ReadDir(imgFolder)
	if err != nil {
		return nil, fmt.Errorf("erreur lors de la lecture du dossier d'images: %v", err)
	}

	var imageFiles []string
	for _, file := range files {
		if !file.IsDir() {
			ext := strings.ToLower(filepath.Ext(file.Name()))
			if ext == ".jpg" || ext == ".jpeg" || ext == ".png" || ext == ".gif" {
				imageFiles = append(imageFiles, filepath.Join(imgFolder, file.Name()))
			}
		}
	}

	if len(imageFiles) == 0 {
		return nil, fmt.Errorf("aucune image trouvée dans le dossier %s", imgFolder)
	}

	return imageFiles, nil
}

// Génère des positions séquentielles avec un peu d'aléatoire pour les images
// Les images ne se chevauchent pas et apparaissent l'une après l'autre
func generateSequentialImagePositions(segmentDuration float64, imageDuration float64, imageCount int) []float64 {
	rand.Seed(time.Now().UnixNano())

	// Calculer le temps disponible pour toutes les images
	availableTime := segmentDuration - 2.0 // Réserver 2 secondes pour les fades

	// Si le temps disponible est insuffisant, réduire le nombre d'images
	maxPossibleImages := int(availableTime / imageDuration)
	if maxPossibleImages < imageCount {
		imageCount = maxPossibleImages
		if imageCount <= 0 {
			return []float64{}
		}
	}

	// Diviser le temps disponible en sections
	sectionDuration := availableTime / float64(imageCount)

	positions := make([]float64, imageCount)

	for i := 0; i < imageCount; i++ {
		// Calculer les limites de cette section
		sectionStart := 1.0 + float64(i)*sectionDuration
		sectionEnd := sectionStart + sectionDuration - imageDuration

		// Si la section est trop petite, utiliser le début
		if sectionEnd <= sectionStart {
			positions[i] = sectionStart
		} else {
			// Sinon, choisir un moment aléatoire dans cette section
			positions[i] = sectionStart + rand.Float64()*(sectionEnd-sectionStart)
		}
	}

	return positions
}

// Sélectionne des images aléatoires parmi celles disponibles
func selectRandomImages(images []string, count int) []string {
	rand.Seed(time.Now().UnixNano())

	// Si count est plus grand que le nombre d'images disponibles
	if count > len(images) {
		count = len(images)
	}

	// Copier le tableau pour éviter de modifier l'original
	imagesCopy := make([]string, len(images))
	copy(imagesCopy, images)

	// Mélanger les images
	rand.Shuffle(len(imagesCopy), func(i, j int) {
		imagesCopy[i], imagesCopy[j] = imagesCopy[j], imagesCopy[i]
	})

	// Prendre les count premières
	return imagesCopy[:count]
}

// Charge un template de titre depuis un fichier JSON
func loadTitleTemplate(templateName string) (TitleTemplate, error) {
	var template TitleTemplate

	// Template par défaut si aucun n'est spécifié
	if templateName == "default" || templateName == "" {
		template.Name = "Default"
		template.Background = "solid"
		template.Title.Font = "Arial"
		template.Title.Size = "large"
		template.Title.Weight = "bold"
		template.Title.Shadow = true
		template.Subtitle.Font = "Arial"
		template.Subtitle.Size = "medium"
		template.Subtitle.Weight = "normal"
		template.Animation = "fade"
		return template, nil
	}

	// Chercher le template dans le dossier titles/
	templatePath := filepath.Join("titles", templateName+".json")
	if _, err := os.Stat(templatePath); os.IsNotExist(err) {
		return template, fmt.Errorf("le template '%s' n'existe pas", templateName)
	}

	// Lire et parser le fichier JSON
	data, err := ioutil.ReadFile(templatePath)
	if err != nil {
		return template, fmt.Errorf("erreur lors de la lecture du template: %v", err)
	}

	if err := json.Unmarshal(data, &template); err != nil {
		return template, fmt.Errorf("erreur lors du parsing du template: %v", err)
	}

	return template, nil
}

// Crée une image avec le texte personnalisé
func createCustomTextImage(outputFolder, text, textColor, bgColor string, textSize int, width, height int, index int) (string, error) {
	textImage := filepath.Join(outputFolder, fmt.Sprintf("custom_text_%d.png", index))

	// Échapper les caractères spéciaux dans le texte de manière plus robuste
	escapedText := strings.ReplaceAll(text, "'", "\\'")
	escapedText = strings.ReplaceAll(escapedText, ":", "\\:")
	escapedText = strings.ReplaceAll(escapedText, "\\", "\\\\")
	escapedText = strings.ReplaceAll(escapedText, ",", "\\,")

	// Vérifier si la couleur de fond est au format correct
	if !strings.HasPrefix(bgColor, "#") && !strings.HasPrefix(bgColor, "0x") {
		bgColor = "#000000AA" // Valeur par défaut avec transparence
	}

	// Construire la commande FFmpeg pour créer l'image avec le texte
	ffmpegArgs := []string{
		"-y",
		"-f", "lavfi",
		"-i", fmt.Sprintf("color=c=%s:s=%dx%d", bgColor, width, height),
		"-vf", fmt.Sprintf("drawtext=text='%s':fontcolor=%s:fontsize=%d:x=(w-text_w)/2:y=(h-text_h)/2:fontname=Arial:box=1:boxcolor=black@0.5:boxborderw=10",
			escapedText, textColor, textSize),
		"-frames:v", "1",
		textImage,
	}

	// Exécuter la commande et capturer la sortie pour le débogage
	cmd := exec.Command("ffmpeg", ffmpegArgs...)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("échec de la création de l'image de texte personnalisé: %v\nSortie: %s", err, string(output))
	}

	// Vérifier que le fichier a bien été créé
	if _, err := os.Stat(textImage); os.IsNotExist(err) {
		return "", fmt.Errorf("l'image de texte n'a pas été créée correctement")
	}

	return textImage, nil
}

// Crée une image de titre stylisée
func createTitleImage(outputFolder, title, subtitle, titleColor, bgColor, templateName string, width, height int, index int) (string, error) {
	titleImage := filepath.Join(outputFolder, fmt.Sprintf("title_%d.png", index))

	// Charger le template
	template, err := loadTitleTemplate(templateName)
	if err != nil {
		fmt.Printf("Avertissement: impossible de charger le template '%s': %v. Utilisation du template par défaut.\n", templateName, err)
		template, _ = loadTitleTemplate("default")
	}

	// Déterminer la taille de police en fonction de la résolution
	titleSize := height / 10
	subtitleSize := height / 20

	// Ajuster en fonction des paramètres du template
	if template.Title.Size == "small" {
		titleSize = height / 15
	} else if template.Title.Size == "large" {
		titleSize = height / 8
	}

	if template.Subtitle.Size == "small" {
		subtitleSize = height / 25
	} else if template.Subtitle.Size == "large" {
		subtitleSize = height / 15
	}

	// Construire la commande ImageMagick
	args := []string{
		"-size", fmt.Sprintf("%dx%d", width, height),
	}

	// Définir l'arrière-plan en fonction du template
	if template.Background == "gradient" && template.Gradient.Start != "" && template.Gradient.End != "" {
		// Créer un gradient
		gradientDirection := "linear-gradient:0"
		if template.Gradient.Direction == "to right" {
			gradientDirection = "linear-gradient:90"
		} else if template.Gradient.Direction == "to left" {
			gradientDirection = "linear-gradient:90"
		} else if template.Gradient.Direction == "to left" {
			gradientDirection = "linear-gradient:270"
		} else if template.Gradient.Direction == "to top" {
			gradientDirection = "linear-gradient:180"
		}
		args = append(args, fmt.Sprintf("%s:%s-%s", gradientDirection, template.Gradient.Start, template.Gradient.End))
	} else {
		// Couleur solide (utiliser celle spécifiée par l'utilisateur si disponible)
		if bgColor != "" {
			args = append(args, "xc:"+bgColor)
		} else {
			args = append(args, "xc:rgba(0,0,0,0.7)")
		}
	}

	// Ajouter les options de texte
	args = append(args,
		"-gravity", "center",
	)

	// Ajouter le titre
	titleWeight := "bold"
	if template.Title.Weight != "" {
		titleWeight = template.Title.Weight
	}

	titleFont := "Arial"
	if template.Title.Font != "" {
		titleFont = template.Title.Font
	}

	// Utiliser la couleur spécifiée par l'utilisateur si disponible
	titleColorValue := "white"
	if titleColor != "" {
		titleColorValue = titleColor
	}

	// Ajouter l'ombre si nécessaire
	if template.Title.Shadow {
		args = append(args,
			"-fill", "rgba(0,0,0,0.5)",
			"-draw", fmt.Sprintf("text 2,2 '%s'", title),
		)
	}

	args = append(args,
		"-fill", titleColorValue,
		"-font", titleFont,
		"-weight", titleWeight,
		"-pointsize", fmt.Sprintf("%d", titleSize),
		"-annotate", "+0-40", title,
	)

	// Ajouter le sous-titre si présent
	if subtitle != "" {
		subtitleWeight := "normal"
		if template.Subtitle.Weight != "" {
			subtitleWeight = template.Subtitle.Weight
		}

		subtitleFont := "Arial"
		if template.Subtitle.Font != "" {
			subtitleFont = template.Subtitle.Font
		}

		args = append(args,
			"-fill", titleColorValue,
			"-font", subtitleFont,
			"-weight", subtitleWeight,
			"-pointsize", fmt.Sprintf("%d", subtitleSize),
			"-annotate", "+0+40", subtitle,
		)
	}

	// Finaliser la commande
	args = append(args, titleImage)
	cmd := exec.Command("convert", args...)

	if err := cmd.Run(); err != nil {
		// Si ImageMagick n'est pas disponible, créer une image vide
		fmt.Printf("Avertissement: impossible de créer l'image de titre avec ImageMagick: %v\n", err)
		fmt.Println("Création d'une image simple à la place.")

		// Utiliser ffmpeg pour créer une image simple avec du texte
		ffmpegArgs := []string{
			"-y",
			"-f", "lavfi",
			"-i", "color=c=black:s=" + fmt.Sprintf("%dx%d", width, height),
			"-vf", fmt.Sprintf("drawtext=text='%s':fontcolor=white:fontsize=%d:x=(w-text_w)/2:y=(h-text_h)/2", title, titleSize),
			"-frames:v", "1",
			titleImage,
		}

		cmd = exec.Command("ffmpeg", ffmpegArgs...)
		if err := cmd.Run(); err != nil {
			return "", fmt.Errorf("échec de la création de l'image de titre: %v", err)
		}
	}

	return titleImage, nil
}

func splitVideo(input, outputFolder, jsonOutput, imgFolder string, imagesPerSegment int, videoFormat string, overlayImage, titleTemplate, videoTitle, videoSubtitle, titleColor, bgColor string, videoSize int, titleDuration float64, customText, textColor, textBgColor string, textSize int, textDuration float64) error {
	// Nettoyer automatiquement les anciennes vidéos avant de commencer
	if err := resetProcessedVideosFolder(outputFolder); err != nil {
		return err
	}

	// Supprimer aussi les anciens fichiers JSON
	if _, err := os.Stat(jsonOutput); err == nil {
		os.Remove(jsonOutput)
	}

	// Vérifier que le fichier d'entrée existe
	if _, err := os.Stat(input); os.IsNotExist(err) {
		return fmt.Errorf("le fichier d'entrée '%s' n'existe pas", input)
	}

	// Vérifier que le fichier d'entrée est lisible
	file, err := os.Open(input)
	if err != nil {
		return fmt.Errorf("impossible d'ouvrir le fichier d'entrée: %v", err)
	}
	file.Close()

	// Vérifier que FFmpeg est installé
	_, err = exec.LookPath("ffmpeg")
	if err != nil {
		return fmt.Errorf("FFmpeg n'est pas installé ou n'est pas dans le PATH: %v", err)
	}

	// Vérifier que FFprobe est installé
	_, err = exec.LookPath("ffprobe")
	if err != nil {
		return fmt.Errorf("FFprobe n'est pas installé ou n'est pas dans le PATH: %v", err)
	}

	duration, err := getVideoDuration(input)
	if err != nil {
		return fmt.Errorf("erreur lors de la récupération de la durée: %v", err)
	}

	if duration <= 0 {
		return fmt.Errorf("la durée de la vidéo est invalide: %d secondes", duration)
	}

	fmt.Printf("Durée de la vidéo: %d secondes\n", duration)

	videoWidth, videoHeight, err := getVideoDimensions(input)
	if err != nil {
		fmt.Printf("Avertissement: impossible de déterminer les dimensions de la vidéo: %v\n", err)
		fmt.Println("Utilisation des dimensions par défaut.")
		videoWidth, videoHeight = 1280, 720
	}

	fmt.Printf("Dimensions originales de la vidéo: %dx%d\n", videoWidth, videoHeight)

	// Déterminer les dimensions finales en fonction du format choisi
	var finalWidth, finalHeight int
	var cropFilter string

	if videoFormat == "vertical" {
		// Format vertical (9:16)
		if float64(videoWidth)/float64(videoHeight) > 9.0/16.0 {
			// La vidéo est trop large, on la recadre
			finalHeight = videoHeight
			finalWidth = int(float64(videoHeight) * 9.0 / 16.0)
			cropX := (videoWidth - finalWidth) / 2
			cropFilter = fmt.Sprintf("crop=%d:%d:%d:0", finalWidth, finalHeight, cropX)
		} else {
			// La vidéo est trop haute ou déjà au bon ratio, on la redimensionne
			finalWidth = videoSize // Utiliser la taille spécifiée
			finalHeight = int(float64(finalWidth) * 16.0 / 9.0)
			cropFilter = fmt.Sprintf("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2",
				finalWidth, finalHeight, finalWidth, finalHeight)
		}
		fmt.Printf("Format vertical sélectionné. Dimensions finales: %dx%d\n", finalWidth, finalHeight)
	} else {
		// Format horizontal (16:9)
		if float64(videoWidth)/float64(videoHeight) < 16.0/9.0 {
			// La vidéo est trop haute, on la recadre
			finalWidth = videoWidth
			finalHeight = int(float64(videoWidth) * 9.0 / 16.0)
			cropY := (videoHeight - finalHeight) / 2
			cropFilter = fmt.Sprintf("crop=%d:%d:0:%d", finalWidth, finalHeight, cropY)
		} else {
			// La vidéo est trop large ou déjà au bon ratio, on la redimensionne
			finalHeight = videoSize // Utiliser la taille spécifiée
			finalWidth = int(float64(finalHeight) * 16.0 / 9.0)
			cropFilter = fmt.Sprintf("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2",
				finalWidth, finalHeight, finalWidth, finalHeight)
		}
		fmt.Printf("Format horizontal sélectionné. Dimensions finales: %dx%d\n", finalWidth, finalHeight)
	}

	var imageFiles []string
	if imgFolder != "" {
		// Vérifier que le dossier d'images existe
		if _, err := os.Stat(imgFolder); os.IsNotExist(err) {
			fmt.Printf("Avertissement: le dossier d'images '%s' n'existe pas. Création du dossier.\n", imgFolder)
			if err := os.MkdirAll(imgFolder, os.ModePerm); err != nil {
				fmt.Printf("Erreur lors de la création du dossier d'images: %v\n", err)
			}
		}

		// Récupérer les images
		var err error
		imageFiles, err = getImageFiles(imgFolder)
		if err != nil {
			fmt.Printf("Avertissement: %v\n", err)
			fmt.Println("Continuation sans images.")
			imageFiles = []string{}
		} else {
			fmt.Printf("Trouvé %d images dans le dossier %s\n", len(imageFiles), imgFolder)
		}
	}

	// Vérifier si un overlay PNG a été spécifié
	hasOverlay := overlayImage != ""
	if hasOverlay {
		// Vérifier que le fichier d'overlay existe
		if _, err := os.Stat(overlayImage); os.IsNotExist(err) {
			fmt.Printf("Avertissement: le fichier d'overlay '%s' n'existe pas. Continuation sans overlay.\n", overlayImage)
			hasOverlay = false
		} else {
			fmt.Printf("Overlay PNG spécifié: %s (sera appliqué sur toute la vidéo)\n", overlayImage)
		}
	}

	// Vérifier si un titre a été spécifié
	hasTitle := videoTitle != ""
	if hasTitle {
		fmt.Printf("Titre spécifié: %s (sera affiché au début de chaque segment)\n", videoTitle)
		if videoSubtitle != "" {
			fmt.Printf("Sous-titre: %s\n", videoSubtitle)
		}
	}

	// Vérifier si un texte personnalisé a été spécifié
	hasCustomText := customText != ""
	if hasCustomText {
		fmt.Printf("Texte personnalisé spécifié: %s (sera affiché au début de la vidéo)\n", customText)
	}

	segmentDuration := 30.0
	imageDuration := 3.0 // Durée fixe de 3 secondes pour chaque image
	startTime := 0.0
	index := 1
	var segments []VideoSegment

	// Si la durée est inférieure à segmentDuration, ajuster pour créer au moins un segment
	if float64(duration) < segmentDuration {
		segmentDuration = float64(duration)
		fmt.Printf("Vidéo courte détectée. Création d'un seul segment de %.2f secondes.\n", segmentDuration)
	}

	for startTime < float64(duration) {
		endTime := math.Min(startTime+segmentDuration, float64(duration))
		actualSegmentDuration := endTime - startTime

		// Si le segment est trop court, ignorer
		if actualSegmentDuration < 1.0 {
			fmt.Printf("Segment %d trop court (%.2f secondes), ignoré.\n", index, actualSegmentDuration)
			break
		}

		tempFile := filepath.Join(outputFolder, fmt.Sprintf("temp_%d.mp4", index))
		formattedFile := filepath.Join(outputFolder, fmt.Sprintf("formatted_%d.mp4", index))
		outputFile := filepath.Join(outputFolder, fmt.Sprintf("segment_%d.mp4", index))

		fmt.Printf("Traitement du segment %d (%.2f à %.2f secondes)...\n", index, startTime, endTime)

		// Extraction du segment
		extractCmd := exec.Command("ffmpeg", "-y", "-i", input, "-ss", fmt.Sprintf("%.2f", startTime), "-to", fmt.Sprintf("%.2f", endTime),
			"-c:v", "copy", "-c:a", "aac", "-b:a", "192k", tempFile)

		// Capturer la sortie pour le débogage
		extractOutput, err := extractCmd.CombinedOutput()
		if err != nil {
			return fmt.Errorf("échec de l'extraction du segment %d: %v\nSortie: %s", index, err, string(extractOutput))
		}

		// Vérifier que le fichier temporaire a bien été créé
		if _, err := os.Stat(tempFile); os.IsNotExist(err) {
			return fmt.Errorf("le fichier temporaire '%s' n'a pas été créé", tempFile)
		}

		// Appliquer le format (horizontal ou vertical)
		formatCmd := exec.Command("ffmpeg", "-y", "-i", tempFile,
			"-vf", cropFilter,
			"-c:v", "libx264", "-preset", "fast", "-crf", "23",
			"-c:a", "copy", formattedFile)

		// Capturer la sortie pour le débogage
		formatOutput, err := formatCmd.CombinedOutput()
		if err != nil {
			return fmt.Errorf("échec de l'application du format pour le segment %d: %v\nSortie: %s", index, err, string(formatOutput))
		}

		// Vérifier que le fichier formaté a bien été créé
		if _, err := os.Stat(formattedFile); os.IsNotExist(err) {
			return fmt.Errorf("le fichier formaté '%s' n'a pas été créé", formattedFile)
		}

		var imageOverlays []ImageOverlay

		// Créer l'image de texte personnalisé si nécessaire (seulement pour le premier segment)
		var customTextImagePath string
		if hasCustomText && index == 1 {
			var err error
			customTextImagePath, err = createCustomTextImage(outputFolder, customText, textColor, textBgColor, textSize, finalWidth, finalHeight, index)
			if err != nil {
				fmt.Printf("Avertissement: échec de la création de l'image de texte personnalisé: %v\n", err)
			} else {
				// Ajouter l'image de texte personnalisé comme overlay
				imageOverlays = append(imageOverlays, ImageOverlay{
					ImagePath: customTextImagePath,
					StartTime: "0.0",                             // Dès le début
					Duration:  fmt.Sprintf("%.2f", textDuration), // Durée spécifiée
				})
			}
		}

		// Créer l'image de titre si nécessaire
		var titleImagePath string
		if hasTitle {
			var err error
			titleImagePath, err = createTitleImage(outputFolder, videoTitle, videoSubtitle, titleColor, bgColor, titleTemplate, finalWidth, finalHeight, index)
			if err != nil {
				fmt.Printf("Avertissement: échec de la création de l'image de titre: %v\n", err)
			} else {
				// Ajouter l'image de titre comme overlay
				startTimeOffset := 0.0
				if hasCustomText && index == 1 {
					startTimeOffset = textDuration // Décaler le titre après le texte personnalisé
				}

				imageOverlays = append(imageOverlays, ImageOverlay{
					ImagePath: titleImagePath,
					StartTime: fmt.Sprintf("%.2f", startTimeOffset), // Après le texte personnalisé si présent
					Duration:  fmt.Sprintf("%.2f", titleDuration),   // Durée spécifiée
				})
			}
		}

		// Sélection des images aléatoires pour ce segment si des images sont disponibles
		var selectedImages []string
		var imagePositions []float64

		if len(imageFiles) > 0 && imagesPerSegment > 0 {
			selectedImages = selectRandomImages(imageFiles, imagesPerSegment)

			// Calculer le décalage total pour les images
			totalOffset := 0.0
			if hasCustomText && index == 1 {
				totalOffset += textDuration
			}
			if hasTitle {
				totalOffset += titleDuration
			}

			// Générer les positions des images en tenant compte du décalage
			if totalOffset > 0 {
				imagePositions = generateSequentialImagePositions(actualSegmentDuration-totalOffset, imageDuration, len(selectedImages))
				// Décaler toutes les positions
				for i := range imagePositions {
					imagePositions[i] += totalOffset
				}
			} else {
				imagePositions = generateSequentialImagePositions(actualSegmentDuration, imageDuration, len(selectedImages))
			}

			for i := 0; i < len(selectedImages); i++ {
				imageOverlays = append(imageOverlays, ImageOverlay{
					ImagePath: selectedImages[i],
					StartTime: fmt.Sprintf("%.2f", imagePositions[i]),
					Duration:  fmt.Sprintf("%.2f", imageDuration),
				})
			}
		}

		// Ajouter l'overlay PNG s'il est spécifié
		if hasOverlay {
			// L'overlay est présent pendant toute la durée du segment (sauf les fades)
			imageOverlays = append(imageOverlays, ImageOverlay{
				ImagePath: overlayImage,
				StartTime: "0.0",                                      // Dès le début
				Duration:  fmt.Sprintf("%.2f", actualSegmentDuration), // Toute la durée
			})
		}

		// Construire le filtre complexe pour ffmpeg de manière plus simple et robuste
		filterComplex := ""

		// Commencer par le fade
		filterComplex += "[0:v]fade=t=in:st=0:d=1,fade=t=out:st=" + fmt.Sprintf("%.2f", actualSegmentDuration-1) + "[faded];"

		// Ajouter les images et overlays
		currentOutput := "faded"
		inputIndex := 1

		// Simplifier le filtre complexe pour éviter les erreurs de syntaxe
		// Ajouter l'image de texte personnalisé si elle existe
		if hasCustomText && index == 1 && customTextImagePath != "" {
			filterComplex += fmt.Sprintf("[%d:v]format=rgba,scale=%d:%d[img_custom_text];", inputIndex, finalWidth, finalHeight)
			filterComplex += fmt.Sprintf("[%s][img_custom_text]overlay=0:0:enable='between(t,0,%.2f)'[v_custom_text];",
				currentOutput, textDuration)
			currentOutput = "v_custom_text"
			inputIndex++
		}

		// Ajouter l'image de titre si elle existe
		if hasTitle && titleImagePath != "" {
			startTimeOffset := 0.0
			if hasCustomText && index == 1 {
				startTimeOffset = textDuration
			}

			filterComplex += fmt.Sprintf("[%d:v]format=rgba,scale=%d:%d[img_title];", inputIndex, finalWidth, finalHeight)
			filterComplex += fmt.Sprintf("[%s][img_title]overlay=0:0:enable='between(t,%.2f,%.2f)'[v_title];",
				currentOutput, startTimeOffset, startTimeOffset+titleDuration)
			currentOutput = "v_title"
			inputIndex++
		}

		// Ajouter les images normales
		for i := 0; i < len(selectedImages); i++ {
			if selectedImages[i] == overlayImage {
				continue
			}

			// Calculer la taille maximale pour les images (80% de la vidéo)
			maxWidth := int(float64(finalWidth) * 0.8)
			maxHeight := int(float64(finalHeight) * 0.8)

			filterComplex += fmt.Sprintf("[%d:v]scale=%d:%d[img%d];",
				inputIndex, maxWidth, maxHeight, i)

			filterComplex += fmt.Sprintf("[%s][img%d]overlay=(W-w)/2:(H-h)/2:enable='between(t,%.2f,%.2f)'[v%d];",
				currentOutput, i, imagePositions[i], imagePositions[i]+imageDuration, i)

			currentOutput = fmt.Sprintf("v%d", i)
			inputIndex++
		}

		// Ajouter l'overlay PNG en dernier pour qu'il soit toujours au-dessus
		if hasOverlay {
			filterComplex += fmt.Sprintf("[%d:v]scale=%d:%d[scaled_overlay];",
				inputIndex, finalWidth, finalHeight)

			filterComplex += fmt.Sprintf("[%s][scaled_overlay]overlay=(W-w)/2:(H-h)/2[final]",
				currentOutput)
			currentOutput = "final"
		} else {
			// Si pas d'overlay, renommer le dernier output en "final"
			if currentOutput != "faded" {
				filterComplex += fmt.Sprintf("[%s]null[final]", currentOutput)
			} else {
				filterComplex += "[faded]null[final]"
			}
		}

		// Afficher la commande complète pour le débogage
		cmdStr := "ffmpeg"
		ffmpegArgs := []string{
			"-y",
			"-i", formattedFile,
		}

		// Ajouter l'image de texte personnalisé comme entrée si elle existe
		if hasCustomText && index == 1 && customTextImagePath != "" {
			ffmpegArgs = append(ffmpegArgs, "-i", customTextImagePath)
		}

		// Ajouter l'image de titre comme entrée si elle existe
		if hasTitle && titleImagePath != "" {
			ffmpegArgs = append(ffmpegArgs, "-i", titleImagePath)
		}

		// Ajouter les images comme entrées
		for _, img := range selectedImages {
			if img != overlayImage {
				ffmpegArgs = append(ffmpegArgs, "-i", img)
			}
		}

		// Ajouter l'overlay en dernier
		if hasOverlay {
			ffmpegArgs = append(ffmpegArgs, "-i", overlayImage)
		}

		// Ajouter le complex filter directement
		ffmpegArgs = append(ffmpegArgs,
			"-filter_complex", filterComplex,
			"-map", "[final]",
			"-map", "0:a?",
			"-c:v", "libx264",
			"-preset", "fast",
			"-crf", "23",
			"-c:a", "aac",
			"-b:a", "192k",
			outputFile,
		)

		for _, arg := range ffmpegArgs {
			cmdStr += " " + arg
		}
		fmt.Println("Commande FFmpeg complète:")
		fmt.Println(cmdStr)

		// Construire la commande ffmpeg
		args := []string{
			"-y",
			"-i", formattedFile,
		}

		// Ajouter l'image de texte personnalisé comme entrée si elle existe
		if hasCustomText && index == 1 && customTextImagePath != "" {
			args = append(args, "-i", customTextImagePath)
		}

		// Ajouter l'image de titre comme entrée si elle existe
		if hasTitle && titleImagePath != "" {
			args = append(args, "-i", titleImagePath)
		}

		// Ajouter les images comme entrées
		for _, img := range selectedImages {
			if img != overlayImage {
				args = append(args, "-i", img)
			}
		}

		// Ajouter l'overlay en dernier
		if hasOverlay {
			args = append(args, "-i", overlayImage)
		}

		// Ajouter le complex filter directement
		args = append(args,
			"-filter_complex", filterComplex,
			"-map", "[final]",
			"-map", "0:a?",
			"-c:v", "libx264",
			"-preset", "fast",
			"-crf", "23",
			"-c:a", "aac",
			"-b:a", "192k",
			outputFile,
		)

		cmd := exec.Command("ffmpeg", args...)

		// Enregistrer les logs dans un fichier
		logFile, err := os.Create(filepath.Join(outputFolder, "ffmpeg_log.txt"))
		if err == nil {
			defer logFile.Close()
			cmd.Stderr = io.MultiWriter(os.Stderr, logFile)
			cmd.Stdout = io.MultiWriter(os.Stdout, logFile)
		} else {
			cmd.Stderr = os.Stderr
			cmd.Stdout = os.Stdout
		}

		fmt.Printf("Exécution de la commande FFmpeg pour le segment %d...\n", index)
		if err := cmd.Run(); err != nil {
			return fmt.Errorf("échec du traitement du segment %d: %v", index, err)
		}

		// Vérifier explicitement si le segment a été créé
		if _, err := os.Stat(outputFile); os.IsNotExist(err) {
			// Si le segment n'a pas été créé, essayer une approche plus simple
			fmt.Printf("Échec de la création du segment avec le filtre complexe. Tentative avec une approche simplifiée...\n")

			// Commande simplifiée sans filtre complexe
			simpleArgs := []string{
				"-y",
				"-i", formattedFile,
				"-c:v", "libx264",
				"-preset", "fast",
				"-crf", "23",
				"-c:a", "aac",
				"-b:a", "192k",
				outputFile,
			}

			simpleCmd := exec.Command("ffmpeg", simpleArgs...)
			simpleCmd.Stdout = os.Stdout
			simpleCmd.Stderr = os.Stderr

			if err := simpleCmd.Run(); err != nil {
				return fmt.Errorf("échec de la création du segment avec l'approche simplifiée: %v", err)
			}

			// Vérifier à nouveau
			if _, err := os.Stat(outputFile); os.IsNotExist(err) {
				return fmt.Errorf("impossible de créer le segment même avec l'approche simplifiée")
			}

			fmt.Printf("Segment %d créé avec succès (approche simplifiée)\n", index)
		} else {
			fmt.Printf("Segment %d créé avec succès\n", index)
		}

		// Vérifier que le fichier de sortie a bien été créé
		if _, err := os.Stat(outputFile); os.IsNotExist(err) {
			return fmt.Errorf("le fichier de sortie '%s' n'a pas été créé", outputFile)
		}

		fmt.Printf("Segment %d créé avec succès: %s\n", index, outputFile)

		// Nettoyer les fichiers temporaires
		os.Remove(tempFile)
		os.Remove(formattedFile)

		// Ajouter le texte personnalisé aux métadonnées du premier segment
		customTextValue := ""
		if hasCustomText && index == 1 {
			customTextValue = customText
		}

		segments = append(segments, VideoSegment{
			Format:     videoFormat,
			TimeSpan:   fmt.Sprintf("%.2f to %.2f", startTime, endTime),
			Title:      videoTitle,
			Subtitle:   videoSubtitle,
			CustomText: customTextValue,
			AudioEffectPreset: struct {
				Compression string `json:"compression"`
				FadeInOut   string `json:"fadeInOut"`
			}{
				Compression: "CompressionPodcast",
				FadeInOut:   "Crescendo",
			},
			Effect: struct {
				EffectType       string `json:"effectType"`
				TimeSpanRelative string `json:"timespanRelative"`
			}{
				EffectType:       "zoomTemp",
				TimeSpanRelative: "0:02",
			},
			ImageOverlays: imageOverlays,
		})
		startTime += segmentDuration
		index++
	}

	// Vérifier qu'au moins un segment a été créé
	if len(segments) == 0 {
		return fmt.Errorf("aucun segment n'a été créé, vérifiez la durée de la vidéo et les paramètres")
	}

	// Sauvegarder les métadonnées
	file, err = os.Create(jsonOutput)
	if err != nil {
		return fmt.Errorf("échec de la création du fichier JSON: %v", err)
	}
	defer file.Close()

	encoder := json.NewEncoder(file)
	encoder.SetIndent("", "  ")
	return encoder.Encode(VideoMetadata{Segments: segments})
}

func main() {
	url := flag.String("url", "", "URL de la vidéo YouTube")
	inputFile := flag.String("input", "", "Fichier vidéo local à traiter")
	outputFolder := flag.String("output", "processed_videos", "Dossier de sortie")
	jsonOutput := flag.String("json", "video_metadata.json", "Nom du fichier JSON")
	imgFolder := flag.String("img", "img", "Dossier contenant les images à superposer")
	imagesPerSegment := flag.Int("images", 3, "Nombre d'images à afficher par segment")
	videoFormat := flag.String("format", "vertical", "Format de la vidéo (vertical ou horizontal)")
	overlayImage := flag.String("overlay", "", "Chemin vers l'image PNG d'overlay (style Twitch)")
	videoSize := flag.Int("size", 480, "Largeur de la vidéo en pixels (pour le format vertical) ou hauteur (pour le format horizontal)")
	videoTitle := flag.String("title", "", "Titre à afficher au début de chaque segment")
	videoSubtitle := flag.String("subtitle", "", "Sous-titre à afficher sous le titre principal")
	titleColor := flag.String("title-color", "#FFFFFF", "Couleur du texte du titre (format HTML)")
	bgColor := flag.String("bg-color", "#000000AA", "Couleur de fond du titre avec transparence (format HTML)")
	titleTemplate := flag.String("title-template", "default", "Template de style pour le titre")
	titleDuration := flag.Float64("title-duration", 5.0, "Durée d'affichage du titre en secondes")

	// Nouveaux paramètres pour le texte personnalisé
	customText := flag.String("custom-text", "", "Texte personnalisé à afficher au début de la vidéo")
	textColor := flag.String("text-color", "#FFFFFF", "Couleur du texte personnalisé (format HTML)")
	textBgColor := flag.String("text-bg-color", "#000000AA", "Couleur de fond du texte personnalisé avec transparence (format HTML)")
	textSize := flag.Int("text-size", 60, "Taille du texte personnalisé en pixels")
	// Removed unused parameter text-position
	textDuration := flag.Float64("text-duration", 5.0, "Durée d'affichage du texte personnalisé en secondes")

	flag.Parse()

	// Valider le format vidéo
	if *videoFormat != "vertical" && *videoFormat != "horizontal" {
		fmt.Println("Format vidéo invalide. Utilisation du format vertical par défaut.")
		*videoFormat = "vertical"
	}

	var videoFile string
	if *url != "" {
		videoFile = "video.mp4"
		fmt.Println("Téléchargement en cours...")
		cmd := exec.Command("yt-dlp", "-f", "best", "-o", videoFile, *url)
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			fmt.Println("Erreur lors du téléchargement:", err)
			return
		}
		fmt.Println("Vidéo téléchargée avec succès :", videoFile)
	} else if *inputFile != "" {
		videoFile = *inputFile
	} else {
		fmt.Println("Veuillez fournir une URL YouTube avec -url ou un fichier vidéo avec -input.")
		return
	}

	fmt.Printf("Découpage en segments au format %s avec ajout d'images aléatoires...\n", *videoFormat)
	if *videoTitle != "" {
		fmt.Printf("Le titre '%s' sera affiché au début de chaque segment\n", *videoTitle)
		if *videoSubtitle != "" {
			fmt.Printf("Avec le sous-titre: '%s'\n", *videoSubtitle)
		}
		fmt.Printf("Durée d'affichage du titre: %.1f secondes\n", *titleDuration)
	}

	// Afficher les informations sur le texte personnalisé
	if *customText != "" {
		fmt.Printf("Le texte personnalisé '%s' sera affiché au début de la vidéo\n", *customText)
		fmt.Printf("Durée d'affichage du texte: %.1f secondes\n", *textDuration)
	}

	if err := splitVideo(videoFile, *outputFolder, *jsonOutput, *imgFolder, *imagesPerSegment, *videoFormat, *overlayImage, *titleTemplate, *videoTitle, *videoSubtitle, *titleColor, *bgColor, *videoSize, *titleDuration, *customText, *textColor, *textBgColor, *textSize, *textDuration); err != nil {
		fmt.Println("Erreur lors du traitement :", err)
		return
	}
	fmt.Println("Segments créés et métadonnées sauvegardées dans", *jsonOutput)
}
