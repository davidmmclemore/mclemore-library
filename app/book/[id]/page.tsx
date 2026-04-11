import { notFound } from 'next/navigation'
import Image from 'next/image'
import Link from 'next/link'
import { createServerComponentClient } from '@/lib/supabase/server'
import UserBookPanel from '@/components/UserBookPanel'
import RatingStars from '@/components/RatingStars'
import { Book, UserBook } from '@/lib/types'
import { ExternalLink, MapPin } from 'lucide-react'

async function getBook(id: string, supabase: any) {
  const { data, error } = await supabase
    .from('books')
    .select('*')
    .eq('id', id)
    .single()

  if (error || !data) {
    return null
  }

  return data as Book
}

async function getUserBook(bookId: string, userId: string, supabase: any) {
  const { data } = await supabase
    .from('user_books')
    .select('*')
    .eq('book_id', bookId)
    .eq('user_id', userId)
    .single()

  return data as UserBook | null
}

async function getUser(supabase: any) {
  const {
    data: { user },
  } = await supabase.auth.getUser()
  return user
}

export async function generateMetadata({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = await createServerComponentClient()
  const book = await getBook(id, supabase)

  if (!book) {
    return {}
  }

  return {
    title: `${book.title} by ${book.author} - McLemore Library`,
    description: book.summary || `Read about ${book.title}`,
  }
}

export default async function BookDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const supabase = await createServerComponentClient()

  const book = await getBook(id, supabase)
  if (!book) {
    notFound()
  }

  const user = await getUser(supabase)
  let userBook: UserBook | null = null

  if (user) {
    userBook = await getUserBook(id, user.id, supabase)
  }

  return (
    <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <Link
          href="/"
          className="mb-6 inline-flex items-center gap-2 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
        >
          ← Back to Catalog
        </Link>

        <div className="grid gap-8 lg:grid-cols-3">
          {/* Cover and Basic Info */}
          <div className="lg:col-span-1">
            <div className="card overflow-hidden sticky top-20">
              <div className="relative aspect-[2/3] overflow-hidden bg-gray-100 dark:bg-gray-700">
                {book.cover_url ? (
                  <Image
                    src={book.cover_url}
                    alt={book.title}
                    fill
                    className="object-cover"
                    sizes="(max-width: 768px) 100vw, 33vw"
                    priority
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-indigo-200 to-indigo-100 dark:from-indigo-900 dark:to-indigo-800">
                    <span className="text-6xl">📖</span>
                  </div>
                )}
              </div>

              <div className="p-6 space-y-4">
                {book.amazon_url && (
                  <a
                    href={book.amazon_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-primary flex items-center justify-center gap-2 w-full"
                  >
                    <ExternalLink size={20} />
                    View on Amazon
                  </a>
                )}

                {book.location && (
                  <div className="flex items-start gap-2 text-sm">
                    <MapPin size={18} className="text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-medium text-light dark:text-dark">Location</p>
                      <p className="text-light-secondary">{book.location}</p>
                    </div>
                  </div>
                )}

                {book.isbn_13 && (
                  <div>
                    <p className="text-xs font-medium text-light-secondary">ISBN-13</p>
                    <p className="font-mono text-sm text-light dark:text-dark">{book.isbn_13}</p>
                  </div>
                )}

                {book.isbn_10 && (
                  <div>
                    <p className="text-xs font-medium text-light-secondary">ISBN-10</p>
                    <p className="font-mono text-sm text-light dark:text-dark">{book.isbn_10}</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Book Details */}
            <div className="card p-8">
              <h1 className="mb-2 text-4xl font-bold text-light dark:text-dark">{book.title}</h1>
              <p className="mb-6 text-2xl text-indigo-600 dark:text-indigo-400">{book.author}</p>

              <div className="mb-8 flex flex-wrap gap-3">
                <span className="badge text-lg px-4 py-2">{book.format}</span>
                <span className="badge text-lg px-4 py-2">{book.category}</span>
                {book.pages && <span className="badge text-lg px-4 py-2">{book.pages} pages</span>}
              </div>

              {book.series_name && (
                <div className="mb-6 rounded-lg bg-indigo-50 p-4 dark:bg-indigo-900/20">
                  <p className="text-sm font-medium text-indigo-900 dark:text-indigo-300">
                    Part of: <span className="font-bold">{book.series_name}</span>
                    {book.series_volume && ` (Book #${book.series_volume})`}
                  </p>
                </div>
              )}

              {book.summary && (
                <div>
                  <h2 className="mb-3 text-lg font-semibold text-light dark:text-dark">Summary</h2>
                  <p className="text-light dark:text-dark-secondary leading-relaxed whitespace-pre-wrap">
                    {book.summary}
                  </p>
                </div>
              )}
            </div>

            {/* Tags */}
            {book.tags && book.tags.length > 0 && (
              <div className="card p-8">
                <h2 className="mb-4 text-lg font-semibold text-light dark:text-dark">Tags</h2>
                <div className="flex flex-wrap gap-2">
                  {book.tags.map((tag) => (
                    <Link
                      key={tag}
                      href={`/?tags=${encodeURIComponent(tag)}`}
                      className="badge hover:bg-indigo-700 hover:text-white transition-colors"
                    >
                      {tag}
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* User Book Panel */}
            {user ? (
              <UserBookPanel
                bookId={book.id}
                initialShelf={userBook?.shelf}
                initialRating={userBook?.rating || undefined}
                initialNotes={userBook?.notes || undefined}
              />
            ) : (
              <div className="card p-8 text-center">
                <p className="mb-4 text-light-secondary">Sign in to track this book in your library</p>
                <div className="flex gap-3 justify-center">
                  <Link href="/auth/login" className="btn-secondary">
                    Log In
                  </Link>
                  <Link href="/auth/signup" className="btn-primary">
                    Sign Up
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
