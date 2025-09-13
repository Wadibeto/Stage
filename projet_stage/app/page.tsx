import Image from "next/image";
import Link from "next/link";

export default function Home() {
return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
        <header className="container mx-auto px-4 py-8">
            <nav className="flex justify-between items-center">
                <Image src="/logo.svg" alt="Logo" width={120} height={40} />
                <Link
                    href="/dashboard"
                    className="bg-blue-600 text-white px-6 py-2 rounded-full hover:bg-blue-700 transition-colors"
                >
                    Dashboard
                </Link>
            </nav>
        </header>

        <main className="container mx-auto px-4 py-16">
            <div className="flex flex-col md:flex-row items-center gap-12">
                <div className="md:w-1/2">
                    <h1 className="text-4xl md:text-6xl font-bold text-gray-800 mb-6">AI-Powered Creativity Hub</h1>
                    <p className="text-xl text-gray-600 mb-8">
                        Unleash your creativity with our all-in-one AI platform. Generate images, text, 3D models, and even
                        realistic voices with ease.
                    </p>
                    <Link
                        href="/dashboard"
                        className="bg-blue-600 text-white px-8 py-3 rounded-full text-lg hover:bg-blue-700 transition-colors inline-block"
                    >
                        Get Started
                    </Link>
                </div>
                <div className="md:w-1/2">
                    <Image
                        src="/placeholder.svg?height=400&width=600"
                        alt="AI-generated visual"
                        width={600}
                        height={400}
                        className="rounded-lg shadow-lg"
                    />
                </div>
            </div>
        </main>
    </div>
);
}
