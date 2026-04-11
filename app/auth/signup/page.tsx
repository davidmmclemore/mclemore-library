export const dynamic = 'force-dynamic'

import Link from 'next/link'
import AuthForm from '@/components/AuthForm'

export const metadata = {
  title: 'Sign Up - McLemore Library',
}

export default function SignupPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-beige-200 dark:bg-gray-900 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="text-3xl font-bold text-indigo-600 dark:text-indigo-400 mb-2">
            📚 McLemore Library
          </h1>
        </div>

        <AuthForm type="signup" />

        <p className="mt-6 text-center text-light-secondary">
          Already have an account?{' '}
          <Link
            href="/auth/login"
            className="font-medium text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
          >
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
