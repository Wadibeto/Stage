// File: app\dashboard\page.tsx
import { Card } from "./components/Card"

export default function Dashboard() {
    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card title="Generate Image" description="Create stunning visuals using AI" link="/dashboard/generate_image" />
            <Card
                title="Generate Text"
                description="Produce high-quality content with Gemini API"
                link="/dashboard/generate_text"
            />
            <Card title="Create PDF" description="Generate professional PDFs effortlessly" link="/dashboard/create-pdf" />
            <Card title="3D Model Viewer" description="Interact with 3D models in real-time" link="/dashboard/3d-model" />
            <Card
                title="Voice Generation"
                description="Convert text to realistic speech"
                link="/dashboard/generate_voice"
            />
        </div>
    )
}
