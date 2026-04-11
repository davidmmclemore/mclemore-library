'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Image from 'next/image'
import { createClient } from '@/lib/supabase/client'
import { Book, UserBook } from '@/lib/types'
import RatingStars from '@/components/RatingStars'
import { Trash2, BookOpen, Plus } from 'lucide-react'

const SHELVES = ['To Read', 'Currently Reading', 'Read', 'Loaned Out']

export default function LibraryPage() {
  const [selectedShelf, setSelectedShelf] = useState<string>('All')
  const [userBooks, setUserBooks] = useState<(UserBook & { book?: Book })[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ total: 0, pagesRead: 0, byCategory: {} as Record<string, number> })
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const loadLibrary = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) {
          router.push('/auth/login')
          return
        }

        let query = supabase
          .from('user_books')
          .select('*, books(*)')
          .eq('user_id', user.id)
          .order('date_added', { ascending: false })

        if (selectedShelf !== 'All') {
          query = query.eq('shelf', selectedShelf)
        }

        const { data, error } = await query

        if (error) throw error

        setUserBooks(data || [])

        const allQuery = await supabase
          .from('user_books')
          .select('*, books(*)')
          .eq('user_id', user.id)

        const allBooks = allQuery.data || []
        const categoryMap: Record<string, number> = {}

        let pagesRead = 0
        allBooks.forEach((ub: any) => {
          const book = ub.books
          if (book) {
            const cat = book.category
            categoryMap[cat] = (categoryMap[cat] || 0) + 1
            if (ub.shelf === 'Read' && book.pages) {
              pagesRead += book.pages
            }
          }
        })

        setStats({
          total: allBooks.length,
          pagesRead,
          byCategory: categoryMap,
        })
      } catch (error) {
        console.error('Error loading library:', error)
      } finally {
        setLoading(false)
      }
    }

    loadLibrary()
  }, [selectedShelf, supabase, router])

  const handleRemove = async (userBookId: string) => {
    try {
      const { error } = await supabase
        .from('user_books')
        .delete()
        .eq('id', userBookId)

      if (error) throw error

      setUserBooks((prev) => prev.filter((ub) => ub.id !== userBookId))
    } catch (error) {
      console.error('Error removing book:', error)
    }
  }

  const handleUpdateShelf = async (userBookId: string, newShelf: string) => {
    try {
      const { error } = await supabase
        .from('user_books')
        .update({ shelf: newShelf })
        .eq('id', userBookId)

      if (error) throw error

      setUserBooks((prev) =>
        prev.map((ub) => (ub.id === userBookId ? { ...ub, shelf: newShelf as any } : ub))
      )
    } catch (error) {
      console.error('Error updating shelf:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-32 rounded-lg bg-gray-200 dark:bg-gray-700" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-light dark:text-dark mb-2">My Library</h1>
          <p className="text-light-secondary">Track your books and reading progress</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 gap-4 mb-8 md:grid-cols-3">
          <div className="card p-6">
            <p className="text-light-secondary text-sm mb-1">Total Books</p>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">{stats.total}</p>
          </div>
          <div className="card p-6">
            <p className="text-light-secondary text-sm mb-1">Pages Read</p>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {stats.pagesRead.toLocaleString()}
            </p>
          </div>
          <div className="card p-6">
            <p className="text-light-secondary text-sm mb-1">Categories</p>
            <p className="text-3xl font-bold text-indigo-600 dark:text-indigo-400">
              {Object.keys(stats.byCategory).length}
            </p>
          </div>
        </div>

        {/* Shelf Tabs */}
        <div className="mb-8 flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedShelf('All')}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              selectedShelf === 'All'
                ? 'bg-indigo-600 text-white'
                : 'bg-white dark:bg-gray-800 text-light dark:text-dark hover:bg-gray-100 dark:hover:bg-gray-700'
            }`}
          >
            All Books
          </button>
          {SHELVES.map((shelf) => (
            <button
              key={shelf}
              onClick={() => setSelectedShelf(shelf)}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                selectedShelf === shelf
                  ? 'bg-indigo-600 text-white'
                  : 'bg-white dark:bg-gray-800 text-light dark:text-dark hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {shelf}
            </button>
          ))}
        </div>

        {/* Books Grid */}
        {userBooks.length === 0 ? (
          <div className="card p-12 text-center">
            <BookOpen size={48} className="mx-auto mb-4 text-gray-400" />
            <h3 className="mb-2 text-lg font-semibold text-light dark:text-dark">No books yet</h3>
            <p className="text-light-secondary mb-4">
              {selectedShelf === 'All'
                ? "Start adding books to your library!"
                : `You haven't added any books to ${selectedShelf} yet.`}
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {userBooks.map((userBook) => {
              const book = (userBook as any).books || userBook.book
              return (
                <div key={userBook.id} className="card p-4 md:p-6 flex gap-4">
                  <div className="relative w-20 h-32 flex-shrink-0 rounded-lg overflow-hidden bg-gray-200 dark:bg-gray-700">
                    {book?.cover_url ? (
                      <Image
                        src={book.cover_url}
                        alt={book.title}
                        fill
                        className="object-cover"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-full text-2xl">📖</div>
                    )}
                  </div>

                  <div className="flex-1 flex flex-col gap-3">
                    <div>
                      <h3 className="font-semibold text-light dark:text-dark text-lg">
                        {book?.title}
                      </h3>
                      <p className="text-light-secondary">{book?.author}</p>
                    </div>

                    <div className="flex flex-wrap gap-2">
                      <select
                        value={userBook.shelf || ''}
                        onChange={(e) => handleUpdateShelf(userBook.id, e.target.value)}
                        className="input-field text-sm py-1"
                      >
                        {SHELVES.map((shelf) => (
                          <option key={shelf} value={shelf}>
                            {shelf}
                          </option>
                        ))}
                      </select>
                    </div>

                    {userBook.notes && (
                      <p className="text-sm text-light-secondary italic">"{userBook.notes}"</p>
                    )}
                  </div>

                  <div className="flex flex-col items-end justify-between">
                    {userBook.rating ? (
                      <RatingStars value={userBook.rating} disabled size="sm" />
                    ) : (
                      <p className="text-xs text-light-secondary">Not rated</p>
                    )}

                    <button
                      onClick={() => handleRemove(userBook.id)}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      aria-label="Remove book"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
