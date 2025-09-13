// File: app/dashboard/generate_text/page.tsx
"use client";
import { useState } from "react";

export default function GenerateTextPage() {
    const [prompt, setPrompt] = useState("");
    const [generatedText, setGeneratedText] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const handleGenerateText = async () => {
        setLoading(true);
        setGeneratedText("");
        setError("");

        try {
            const response = await fetch("/api/generate-text", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ prompt }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Une erreur est survenue");
            }

            setGeneratedText(data.text);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-2xl mx-auto p-6">
            <h1 className="text-2xl font-bold mb-4">Générateur de texte avec Gemini</h1>
            <textarea
                className="w-full p-2 border rounded-lg mb-4"
                placeholder="Entrez un prompt..."
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
            />
            <button
                onClick={handleGenerateText}
                disabled={loading}
                className="bg-blue-500 text-white px-4 py-2 rounded-md disabled:opacity-50"
            >
                {loading ? "Génération en cours..." : "Générer"}
            </button>

            {error && <p className="text-red-500 mt-4">{error}</p>}

            {generatedText && (
                <div className="mt-6 p-4 bg-gray-100 border rounded-lg">
                    <h2 className="text-lg font-semibold">Texte généré :</h2>
                    <p className="mt-2">{generatedText}</p>
                </div>
            )}
        </div>
    );
}
