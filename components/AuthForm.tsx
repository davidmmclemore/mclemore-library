'use client'

import { useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import { Mail, Lock, User } from 'lucide-react'

interface AuthFormProps {
  type: 'login' | 'signup'
  onSubmit?: (email: string, password: string, displayName?: string) => Promise<void>
}

export default function AuthForm({ type, onSubmit }: AuthFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [error, setError] = useState<string>('')
  const [isPending, startTransition] = useTransition()
  const router = useRouter()
  const supabase = createClient()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    startTransition(async () => {
      try {
        if (type === 'signup') {
          const { data, error: signUpError } = await supabase.auth.signUp({
            email,
            password,
            options: {
              data: {
                display_name: displayName,
              },
            },
          })

          if (signUpError) {
            setError(signUpError.message)
            return
          }

          if (data.user) {
            await supabase.from('profiles').insert({
              id: data.user.id,
              display_name: displayName,
            })
          }

          router.push('/')
        } else {
          const { error: signInError } = await supabase.auth.signInWithPassword({
            email,
            password,
          })

          if (signInError) {
            setError(signInError.message)
            return
          }

          router.push('/')
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred')
      }
    })
  }

  return (
    <form onSubmit={handleSubmit} className="card w-full max-w-md space-y-6 p-8">
      <div>
        <h2 className="mb-2 text-2xl font-bold text-light dark:text-dark">
          {type === 'login' ? 'Welcome Back' : 'Create Account'}
        </h2>
        <p className="text-light-secondary">
          {type === 'login'
            ? 'Sign in to your library account'
            : 'Join McLemore Library to track your books'}
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          {error}
        </div>
      )}

      {type === 'signup' && (
        <div>
          <label htmlFor="displayName" className="mb-2 block text-sm font-medium text-light dark:text-dark">
            Display Name
          </label>
          <div className="relative">
            <User className="absolute left-3 top-3 text-gray-400" size={20} />
            <input
              id="displayName"
              type="text"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              placeholder="Your name"
              className="input-field pl-10"
              required
            />
          </div>
        </div>
      )}

      <div>
        <label htmlFor="email" className="mb-2 block text-sm font-medium text-light dark:text-dark">
          Email
        </label>
        <div className="relative">
          <Mail className="absolute left-3 top-3 text-gray-400" size={20} />
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className="input-field pl-10"
            required
          />
        </div>
      </div>

      <div>
        <label htmlFor="password" className="mb-2 block text-sm font-medium text-light dark:text-dark">
          Password
        </label>
        <div className="relative">
          <Lock className="absolute left-3 top-3 text-gray-400" size={20} />
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            className="input-field pl-10"
            required
            minLength={6}
          />
        </div>
      </div>

      <button type="submit" disabled={isPending} className="btn-primary w-full">
        {isPending ? 'Loading...' : type === 'login' ? 'Sign In' : 'Create Account'}
      </button>
    </form>
  )
}
