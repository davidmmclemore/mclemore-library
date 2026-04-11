'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Search, Menu, X, LogOut, Library, Bookmark } from 'lucide-react'
import { createClient } from '@/lib/supabase/client'
import ThemeToggle from './ThemeToggle'

export default function Navbar() {
  const [user, setUser] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const checkUser = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()
        setUser(user)
      } catch (error) {
        console.error('Error checking user:', error)
      } finally {
        setLoading(false)
      }
    }

    checkUser()

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setUser(session?.user ?? null)
    })

    return () => {
      subscription?.unsubscribe()
    }
  }, [supabase])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchQuery.trim()) {
      router.push(`/?q=${encodeURIComponent(searchQuery)}`)
      setMobileOpen(false)
    }
  }

  const handleLogout = async () => {
    try {
      await supabase.auth.signOut()
      router.push('/')
    } catch (error) {
      console.error('Error logging out:', error)
    }
  }

  return (
    <nav className="sticky top-0 z-50 border-b border-gray-200 bg-white shadow-sm dark:border-gray-800 dark:bg-gray-800">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2 text-2xl font-bold text-indigo-600">
            📚 McLemore Library
          </Link>

          <div className="hidden flex-1 items-center justify-center px-6 md:flex">
            <form onSubmit={handleSearch} className="w-full max-w-md">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search books, authors..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input-field w-full pl-4 pr-10"
                />
                <button
                  type="submit"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-indigo-600"
                  aria-label="Search"
                >
                  <Search size={20} />
                </button>
              </div>
            </form>
          </div>

          <div className="hidden items-center gap-4 md:flex">
            <ThemeToggle />
            {!loading && (
              <>
                {user ? (
                  <div className="flex items-center gap-3">
                    <Link href="/library" className="flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-700">
                      <Library size={18} />
                      Library
                    </Link>
                    <Link href="/shelves" className="flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium hover:bg-gray-100 dark:hover:bg-gray-700">
                      <Bookmark size={18} />
                      Shelves
                    </Link>
                    <button
                      onClick={handleLogout}
                      className="flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                    >
                      <LogOut size={18} />
                      Sign Out
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2">
                    <Link href="/auth/login" className="btn-secondary">
                      Log In
                    </Link>
                    <Link href="/auth/signup" className="btn-primary">
                      Sign Up
                    </Link>
                  </div>
                )}
              </>
            )}
          </div>

          <div className="flex items-center gap-2 md:hidden">
            <ThemeToggle />
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {mobileOpen && (
          <div className="border-t border-gray-200 py-4 dark:border-gray-700">
            <form onSubmit={handleSearch} className="mb-4">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search books..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input-field w-full pl-4 pr-10"
                />
                <button
                  type="submit"
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-indigo-600"
                  aria-label="Search"
                >
                  <Search size={20} />
                </button>
              </div>
            </form>

            <div className="space-y-2">
              {!loading && (
                <>
                  {user ? (
                    <>
                      <Link href="/library" className="block rounded-lg px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">
                        Library
                      </Link>
                      <Link href="/shelves" className="block rounded-lg px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">
                        Shelves
                      </Link>
                      <button
                        onClick={handleLogout}
                        className="w-full rounded-lg px-4 py-2 text-left text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                      >
                        Sign Out
                      </button>
                    </>
                  ) : (
                    <>
                      <Link href="/auth/login" className="block rounded-lg px-4 py-2 hover:bg-gray-100 dark:hover:bg-gray-700">
                        Log In
                      </Link>
                      <Link href="/auth/signup" className="block rounded-lg px-4 py-2 text-center btn-primary">
                        Sign Up
                      </Link>
                    </>
                  )}
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  )
}
