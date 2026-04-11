'use client'

import { useState, useEffect } from 'react'
import { useRouter, useParams } from 'next/navigation'
import Link from 'next/link'
import Image from 'next/image'
import { createClient } from '@/lib/supabase/client'
import { Shelf, Book } from '@/lib/types'
import { Trash2, ArrowLeft } from 'lucide-react'

export default function ShelfDetailPage() {
  const [shelf, setShelf] = useState<Shelf | null>(null)
  const [books, setBooks] = useState<Book[]>([])
  const [loading, setLoading] = useState(true)
  const router = useRouter()
  const params = useParams()
  const shelfId = params.id as string
  const supabase = createClient()

  useEffect(() => {
    const loadShelfDetails = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) {
          router.push('/auth/login')
          return
        }

        const { data: shelfData, error: shelfError } = await supabase
          .from('shelves')
          .select('*')
          .eq('id', shelfId)
          .eq('user_id', user.id)
          .single()

        if (shelfError) throw shelfError
        setShelf(shelfData)

        const { data: booksData, error: booksError } = await supabase
          .from('shelf_books')
          .select('books(*)')
          .eq('shelf_id', shelfId)

        if (booksError) throw booksError

        const booksList = booksData?.map((sb: any) => sb.books).filter(Boolean) || []
        setBooks(booksList)
      } catch (error) {
        console.error('Error loading shelf:', error)
      } finally {
        setLoading(false)
      }
    }

    loadShelfDetails()
  }, [shelfId, supabase, router])

  const handleRemoveBook = async (bookId: string) => {
    try {
      const { error } = await supabase
        .from('shelf_books')
        .delete()
        .eq('shelf_id', shelfId)
        .eq('book_id', bookId)

      if (error) throw error

      setBooks(books.filter((b) => b.id !== bookId))
    } catch (error) {
      console.error('Error removing book:', error)
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

  if (!shelf) {
    return (
      <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <p className="text-light-secondary">Shelf not found</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/shelves"
          className="mb-6 inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
        >
          <ArrowLeft size={20} />
          Back to Shelves
        </Link>

        <div className="mb-8">
          <h1 className="text-4xl font-bold text-light dark:text-dark mb-2">{shelf.name}</h1>
          {shelf.description && (
            <p className="text-light-secondary">{shelf.description}</p>
          )}
          <p className="text-sm text-light-secondary mt-2">
            {books.length} {books.length === 1 ? 'book' : 'books'}
          </p>
        </div>

        {books.length === 0 ? (
          <div className="card p-12 text-center">
            <p className="text-light-secondary">This shelf is empty</p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
            {books.map((book) => (
              <div key={book.id} className="card group relative overflow-hidden">
                <Link href={`/book/${book.id}`} className="block">
                  <div className="relative aspect-[2/3] overflow-hidden bg-gray-100 dark:bg-gray-700">
                    {book.cover_url ? (
                      <Image
                        src={book.cover_url}
                        alt={book.title}
                        fill
                        className="object-cover transition-transform duration-300 group-hover:scale-110"
                        sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-indigo-200 to-indigo-100 dark:from-indigo-900 dark:to-indigo-800">
                        <span className="text-4xl">📖</span>
                      </div>
                    )}
                  </div>

                  <div className="p-3">
                    <h3 className="line-clamp-2 font-semibold text-sm leading-tight text-light dark:text-dark">
                      {book.title}
                    </h3>
                    <p className="line-clamp-1 text-xs text-light-secondary">{book.author}</p>
                  </div>
                </Link>

                <button
                  onClick={() => handleRemoveBook(book.id)}
                  className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity bg-red-600 text-white p-2 rounded-lg"
                  aria-label="Remove book from shelf"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
