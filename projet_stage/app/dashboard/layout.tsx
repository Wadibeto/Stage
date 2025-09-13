import type React from "react"
import Link from "next/link"
import { Sidebar } from "./components/Sidebar"

export default function DashboardLayout({
                                            children,
                                        }: {
    children: React.ReactNode
}) {
    return (
        <div className="flex h-screen bg-gray-900 text-white">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <header className="bg-gray-800 p-4">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-semibold">Dashboard</h1>
                        <Link href="/" className="text-blue-400 hover:text-blue-300">
                            Back to Home
                        </Link>
                    </div>
                </header>
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-900 p-6">{children}</main>
            </div>
        </div>
    )
}

