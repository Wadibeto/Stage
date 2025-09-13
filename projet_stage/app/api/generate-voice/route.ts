import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  try {
    const { text, voiceId = 'pNInz6obpgDQGcFmaJgB' } = await req.json();

    if (!text) {
      return NextResponse.json(
        { error: 'Le texte est requis' },
        { status: 400 }
      );
    }

    // Appel à l'API ElevenLabs
    const response = await fetch(
      `https://api.elevenlabs.io/v1/text-to-speech/${voiceId}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'xi-api-key': process.env.ELEVENLABS_API_KEY || '',
        },
        body: JSON.stringify({
          text,
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability: 0.5,
            similarity_boost: 0.75,
          },
        }),
      }
    );

    if (!response.ok) {
      const errorData = await response.json();
      return NextResponse.json(
        { error: 'Erreur lors de la génération de la voix', details: errorData },
        { status: response.status }
      );
    }

    // Récupérer le fichier audio
    const audioBuffer = await response.arrayBuffer();
    
    // Retourner le fichier audio
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.byteLength.toString(),
      },
    });
  } catch (error) {
    console.error('Erreur:', error);
    return NextResponse.json(
      { error: 'Une erreur est survenue lors de la génération de la voix' },
      { status: 500 }
    );
  }
}