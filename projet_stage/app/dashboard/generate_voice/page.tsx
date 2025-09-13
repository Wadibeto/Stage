'use client';

import { useState, useRef, useEffect } from 'react';
import { Mic, Play, Pause, Download, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';

const voiceOptions = [
  { id: 'pNInz6obpgDQGcFmaJgB', name: 'Rachel' },
  { id: 'EXAVITQu4vr4xnSDxMaL', name: 'Antoine' },
  { id: 'ODq5zmih8GrVes37Dizd', name: 'Josh' },
  { id: 'yoZ06aMxZJJ28mfd3POQ', name: 'Elli' },
];

export default function GenerateVoicePage() {
  const [text, setText] = useState('');
  const [voiceId, setVoiceId] = useState('pNInz6obpgDQGcFmaJgB');
  const [isGenerating, setIsGenerating] = useState(false);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [stability, setStability] = useState(0.5);
  const [similarityBoost, setSimilarityBoost] = useState(0.75);
  
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.addEventListener('ended', () => setIsPlaying(false));
      return () => {
        audioRef.current?.removeEventListener('ended', () => setIsPlaying(false));
      };
    }
  }, []);

  const handleGenerate = async () => {
    if (!text.trim()) return;
    
    setIsGenerating(true);
    setAudioBlob(null);
    
    try {
      const response = await fetch('/api/generate-voice', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          text, 
          voiceId,
          stability,
          similarityBoost
        }),
      });
      
      if (!response.ok) {
        throw new Error('Erreur lors de la génération de la voix');
      }
      
      const blob = await response.blob();
      setAudioBlob(blob);
      
      if (audioRef.current) {
        audioRef.current.src = URL.createObjectURL(blob);
      }
    } catch (error) {
      console.error('Erreur:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const togglePlayPause = () => {
    if (!audioRef.current || !audioBlob) return;
    
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play().catch(e => console.error("Erreur de lecture:", e));
    }
    
    setIsPlaying(!isPlaying);
  };

  const handleDownload = () => {
    if (!audioBlob) return;
    
    const url = URL.createObjectURL(audioBlob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `voice-generation-${new Date().toISOString()}.mp3`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container mx-auto py-6">
      <h1 className="text-3xl font-bold mb-6">Génération de Voix</h1>
      
      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Texte à convertir</CardTitle>
            <CardDescription>
              Entrez le texte que vous souhaitez convertir en voix
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Textarea
              placeholder="Entrez votre texte ici..."
              value={text}
              onChange={(e) => setText(e.target.value)}
              className="min-h-[200px]"
            />
          </CardContent>
          <CardFooter className="flex justify-between">
            <div className="w-full space-y-4">
              <div className="space-y-2">
                <Label htmlFor="voice">Voix</Label>
                <Select value={voiceId} onValueChange={setVoiceId}>
                  <SelectTrigger id="voice">
                    <SelectValue placeholder="Sélectionnez une voix" />
                  </SelectTrigger>
                  <SelectContent>
                    {voiceOptions.map((voice) => (
                      <SelectItem key={voice.id} value={voice.id}>
                        {voice.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div className="space-y-2">
                <Label>Stabilité: {stability}</Label>
                <Slider 
                  value={[stability]} 
                  min={0} 
                  max={1} 
                  step={0.01} 
                  onValueChange={(value) => setStability(value[0])} 
                />
              </div>
              
              <div className="space-y-2">
                <Label>Similarité: {similarityBoost}</Label>
                <Slider 
                  value={[similarityBoost]} 
                  min={0} 
                  max={1} 
                  step={0.01} 
                  onValueChange={(value) => setSimilarityBoost(value[0])} 
                />
              </div>
              
              <Button 
                onClick={handleGenerate} 
                disabled={isGenerating || !text.trim()} 
                className="w-full"
              >
                {isGenerating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Génération en cours...
                  </>
                ) : (
                  <>
                    <Mic className="mr-2 h-4 w-4" />
                    Générer la voix
                  </>
                )}
              </Button>
            </div>
          </CardFooter>
        </Card>
        
        <Card>
          <CardHeader>
            <CardTitle>Résultat</CardTitle>
            <CardDescription>
              Écoutez et téléchargez l'audio généré
            </CardDescription>
          </CardHeader>
          <CardContent className="flex items-center justify-center min-h-[200px]">
            {isGenerating ? (
              <div className="flex flex-col items-center">
                <Loader2 className="h-12 w-12 animate-spin text-primary" />
                <p className="mt-4 text-muted-foreground">Génération en cours...</p>
              </div>
            ) : audioBlob ? (
              <div className="w-full">
                <div className="flex justify-center mb-4">
                  <Button 
                    variant="outline" 
                    size="icon" 
                    className="h-16 w-16 rounded-full"
                    onClick={togglePlayPause}
                  >
                    {isPlaying ? (
                      <Pause className="h-8 w-8" />
                    ) : (
                      <Play className="h-8 w-8" />
                    )}
                  </Button>
                </div>
                <audio 
                  ref={audioRef} 
                  className="w-full"
                  controls
                />
              </div>
            ) : (
              <div className="text-center text-muted-foreground">
                <Mic className="h-12 w-12 mx-auto mb-4 opacity-20" />
                <p>Aucun audio généré</p>
                <p className="text-sm">Entrez du texte et cliquez sur "Générer la voix"</p>
              </div>
            )}
          </CardContent>
          <CardFooter>
            <Button 
              onClick={handleDownload} 
              disabled={!audioBlob} 
              variant="outline" 
              className="w-full"
            >
              <Download className="mr-2 h-4 w-4" />
              Télécharger l'audio
            </Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
}