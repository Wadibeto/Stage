export async function POST(req: Request) {
    try {
      const { prompt } = await req.json()
  
      if (!prompt || prompt.trim() === "") {
        return new Response(JSON.stringify({ error: "Le prompt ne peut pas être vide" }), { status: 400 })
      }
  
      // Vérifier que la clé API est définie
      if (!process.env.REPLICATE_API_TOKEN) {
        console.error("La clé API Replicate n'est pas définie")
        return new Response(JSON.stringify({ error: "Configuration du serveur incorrecte" }), { status: 500 })
      }
  
      // Appel à l'API Replicate (Black Forest)
      const response = await fetch("https://api.replicate.com/v1/predictions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Token ${process.env.REPLICATE_API_TOKEN}`,
        },
        body: JSON.stringify({
          version: "2f779eb9b23b34c5e3f3ae4fe9d4a0b1e2c9cf7e1a9f3e4a7d3f3e4a7d3f3e4a", // Dernière version de Black Forest
          input: {
            prompt: prompt,
            negative_prompt: "ugly, disfigured, low quality, blurry, nsfw",
            num_inference_steps: 50,
            guidance_scale: 7.5,
            scheduler: "DPMSolverMultistep",
          },
        }),
      })
  
      if (!response.ok) {
        const error = await response.json()
        console.error("Erreur Replicate:", error)
        return new Response(JSON.stringify({ error: "Erreur lors de la génération d'image" }), { status: 500 })
      }
  
      const prediction = await response.json()
  
      // Replicate renvoie un ID de prédiction, nous devons vérifier l'état jusqu'à ce qu'il soit terminé
      let imageResult
      let attempts = 0
      const maxAttempts = 30
  
      while (attempts < maxAttempts) {
        const statusResponse = await fetch(`https://api.replicate.com/v1/predictions/${prediction.id}`, {
          headers: {
            Authorization: `Token ${process.env.REPLICATE_API_TOKEN}`,
            "Content-Type": "application/json",
          },
        })
  
        if (!statusResponse.ok) {
          break
        }
  
        const statusData = await statusResponse.json()
  
        if (statusData.status === "succeeded") {
          imageResult = statusData.output[0] // Le premier élément est l'URL de l'image
          break
        } else if (statusData.status === "failed") {
          return new Response(JSON.stringify({ error: "La génération d'image a échoué" }), { status: 500 })
        }
  
        // Attendre avant de vérifier à nouveau
        await new Promise((resolve) => setTimeout(resolve, 2000))
        attempts++
      }
  
      if (!imageResult) {
        return new Response(JSON.stringify({ error: "Délai d'attente dépassé pour la génération d'image" }), {
          status: 500,
        })
      }
  
      return new Response(JSON.stringify({ image: imageResult }), { status: 200 })
    } catch (error) {
      console.error("Erreur:", error)
      return new Response(JSON.stringify({ error: "Erreur lors de la génération d'image" }), { status: 500 })
    }
  }
  
  