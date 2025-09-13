// File: app/api/generate-text/route.ts
export async function POST(req: Request) {
    try {
        const { prompt } = await req.json();

        if (!prompt || prompt.trim() === "") {
            return new Response(JSON.stringify({ error: "Le prompt ne peut pas être vide" }), { status: 400 });
        }

        if (!process.env.GEMINI_API_KEY) {
            console.error("La clé API Gemini n'est pas définie");
            return new Response(JSON.stringify({ error: "Configuration du serveur incorrecte" }), { status: 500 });
        }

        const response = await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateText", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${process.env.GEMINI_API_KEY}`,
            },
            body: JSON.stringify({
                prompt: { text: prompt },
                temperature: 0.7,
                max_tokens: 200,
            }),
        });

        if (!response.ok) {
            const error = await response.json();
            console.error("Erreur Gemini:", error);
            return new Response(JSON.stringify({ error: "Erreur lors de la génération du texte" }), { status: 500 });
        }

        const result = await response.json();
        const generatedText = result.candidates?.[0]?.output || "Aucune réponse générée.";

        return new Response(JSON.stringify({ text: generatedText }), { status: 200 });

    } catch (error) {
        console.error("Erreur:", error);
        return new Response(JSON.stringify({ error: "Erreur lors de la génération du texte" }), { status: 500 });
    }
}
