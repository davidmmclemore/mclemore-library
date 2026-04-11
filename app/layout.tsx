import type { Metadata } from 'next'
import './globals.css'
import Navbar from '@/components/Navbar'

export const metadata: Metadata = {
  title: 'McLemore Library - Personal Book Collection',
  description: 'Organize, track, and discover books in your personal library',
  icons: {
    icon: 'data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">📚</text></svg>',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body className="bg-beige-200 text-light dark:bg-gray-900 dark:text-dark">
        <div className="min-h-screen flex flex-col">
          <Navbar />
          <main className="flex-1">{children}</main>
          <footer className="border-t border-gray-200 bg-white py-8 dark:border-gray-800 dark:bg-gray-800">
            <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-light-secondary">
                © 2026 McLemore Library. Built with Next.js and Supabase.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
