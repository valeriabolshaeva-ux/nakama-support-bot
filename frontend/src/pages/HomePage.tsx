import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ThemeToggle } from "@/shared/components/ThemeToggle"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className="container flex h-14 items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold">Customer Support</span>
          </div>
          <ThemeToggle />
        </div>
      </header>

      {/* Main Content */}
      <main className="container py-10">
        <div className="mx-auto max-w-4xl space-y-8">
          {/* Hero Section */}
          <div className="text-center space-y-4">
            <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
              Welcome to Customer Support
            </h1>
            <p className="text-xl text-muted-foreground">
              Universal project template with FastAPI backend and React frontend
            </p>
          </div>

          {/* Cards Grid */}
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            <Card>
              <CardHeader>
                <CardTitle>Backend</CardTitle>
                <CardDescription>FastAPI + PostgreSQL</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Python backend with async support, SQLAlchemy ORM, and Pydantic validation.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Frontend</CardTitle>
                <CardDescription>React + TypeScript</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Modern frontend with Vite, Tailwind CSS, and shadcn/ui components.
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>DevOps</CardTitle>
                <CardDescription>Docker + CI/CD</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Containerized deployment with Docker Compose for development and production.
                </p>
              </CardContent>
            </Card>
          </div>

          {/* CTA Section */}
          <div className="flex justify-center gap-4">
            <Button size="lg">
              Get Started
            </Button>
            <Button variant="outline" size="lg">
              View Documentation
            </Button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t py-6">
        <div className="container text-center text-sm text-muted-foreground">
          Built with Cursor IDE and AI agents
        </div>
      </footer>
    </div>
  )
}
