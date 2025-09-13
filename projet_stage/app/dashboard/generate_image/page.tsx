"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Loader2, ImageIcon } from "lucide-react"

export default function GenerateImage() {
  const [prompt, setPrompt] = useState("")
  const [image, setImage] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const generateImage = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch("/api/generate-image", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      })

      const data = await response.json()
      if (response.ok) {
        setImage(data.image)
      } else {
        setError(data.error || "Une erreur est survenue.")
      }
    } catch (err) {
      setError("Erreur lors de la génération d'image.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="container mx-auto py-10">
      <Card className="w-full max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle>Générateur d'images IA</CardTitle>
          <CardDescription>Utilisez l'IA pour générer des images uniques basées sur votre description.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid w-full items-center gap-4">
            <div className="flex flex-col space-y-1.5">
              <Label htmlFor="prompt">Description de l'image</Label>
              <Input
                id="prompt"
                placeholder="Décrivez l'image que vous souhaitez générer..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
              />
            </div>
          </div>
        </CardContent>
        <CardFooter className="flex justify-between">
          <Button onClick={generateImage} disabled={loading || !prompt.trim()}>
            {loading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Génération en cours...
              </>
            ) : (
              <>
                <ImageIcon className="mr-2 h-4 w-4" />
                Générer l'image
              </>
            )}
          </Button>
        </CardFooter>
      </Card>

      {error && (
        <Card className="mt-6 w-full max-w-2xl mx-auto border-red-500">
          <CardContent className="pt-6">
            <p className="text-red-500">{error}</p>
          </CardContent>
        </Card>
      )}

      {image && !loading && (
        <Card className="mt-6 w-full max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle>Image générée</CardTitle>
          </CardHeader>
          <CardContent>
            <img
              src={image || "/placeholder.svg"}
              alt="Image générée par IA"
              className="w-full h-auto rounded-lg shadow-lg"
            />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

