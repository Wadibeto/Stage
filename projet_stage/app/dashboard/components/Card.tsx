import Link from "next/link"

interface CardProps {
    title: string
    description: string
    link: string
}

export function Card({ title, description, link }: CardProps) {
    return (
        <div className="bg-gray-800 rounded-lg shadow-lg p-6 hover:bg-gray-700 transition-colors">
            <h3 className="text-xl font-semibold mb-2">{title}</h3>
            <p className="text-gray-400 mb-4">{description}</p>
            <Link href={link} className="text-blue-400 hover:text-blue-300 font-medium">
                Get Started →
            </Link>
        </div>
    )
}

