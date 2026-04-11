import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-beige-200 dark:bg-gray-900 px-4">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-indigo-600 dark:text-indigo-400 mb-4">404</h1>
        <h2 className="text-3xl font-bold text-light dark:text-dark mb-4">Page Not Found</h2>
        <p className="text-light-secondary mb-8">The page you're looking for doesn't exist.</p>
        <Link href="/" className="btn-primary">
          Return Home
        </Link>
      </div>
    </div>
  )
}
