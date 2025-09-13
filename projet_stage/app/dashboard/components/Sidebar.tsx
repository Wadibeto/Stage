import Link from "next/link"
import { Home, Image, FileText, FileSpreadsheet, CuboidIcon as Cube, Mic } from "lucide-react"

const navItems = [
    { name: "Home", href: "/dashboard", icon: Home },
    { name: "Generate Image", href: "/dashboard/generate-image", icon: Image },
    { name: "Generate Text", href: "/dashboard/generate-text", icon: FileText },
    { name: "Create PDF", href: "/dashboard/create-pdf", icon: FileSpreadsheet },
    { name: "3D Model", href: "/dashboard/3d-model", icon: Cube },
    { name: "Voice Generation", href: "/dashboard/voice-generation", icon: Mic },
]

export function Sidebar() {
    return (
        <div className="w-64 bg-gray-800 h-full">
            <div className="p-4">
                <h2 className="text-2xl font-bold text-white mb-4">AI Dashboard</h2>
                <nav>
                    <ul>
                        {navItems.map((item) => (
                            <li key={item.name} className="mb-2">
                                <Link
                                    href={item.href}
                                    className="flex items-center text-gray-300 hover:text-white hover:bg-gray-700 px-4 py-2 rounded transition-colors"
                                >
                                    <item.icon className="mr-3 h-5 w-5" />
                                    {item.name}
                                </Link>
                            </li>
                        ))}
                    </ul>
                </nav>
            </div>
        </div>
    )
}

