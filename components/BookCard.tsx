'use client'

import Link from 'next/link'
import Image from 'next/image'
import { Book } from '@/lib/types'
import { Plus } from 'lucide-react'
import { useState } from 'react'

interface BookCardProps {
  book: Book
  onQuickAdd?: (bookId: string, shelf: string) => void
  showQuickAdd?: boolean
}

export default function BookCard({ book, onQuickAdd, showQuickAdd = false }: BookCardProps) {
  const [showShelfMenu, setShowShelfMenu] = useState(false)

  const shelves = ['To Read', 'Currently Reading', 'Read', 'Loaned Out']

  return (
    <Link href={`/book/${book.id}`}>
      <div className="card group h-full overflow-hidden">
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

          {showQuickAdd && (
            <div className="absolute inset-0 flex items-end justify-center bg-black/0 transition-all duration-200 group-hover:bg-black/40">
              <div className="mb-2 opacity-0 transition-opacity duration-200 group-hover:opacity-100">
                <button
                  onClick={(e) => {
                    e.preventDefault()
                    setShowShelfMenu(!showShelfMenu)
                  }}
                  className="flex items-center gap-2 rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700"
                >
                  <Plus size={16} />
                  Add to Shelf
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="flex flex-col gap-2 p-4">
          <h3 className="line-clamp-2 font-semibold leading-tight text-light dark:text-dark">
            {book.title}
          </h3>
          <p className="line-clamp-1 text-sm text-light-secondary">{book.author}</p>

          <div className="flex flex-wrap gap-1 pt-2">
            <span className="badge text-xs">{book.format}</span>
            <span className="badge text-xs">{book.category}</span>
          </div>

          {book.series_name && (
            <p className="text-xs text-light-secondary">
              {book.series_name}
              {book.series_volume && ` #${book.series_volume}`}
            </p>
          )}
        </div>

        {showShelfMenu && (
          <div
            className="absolute bottom-full left-0 right-0 mb-2 rounded-lg border border-gray-200 bg-white p-2 shadow-lg dark:border-gray-700 dark:bg-gray-800"
            onClick={(e) => e.preventDefault()}
          >
            {shelves.map((shelf) => (
              <button
                key={shelf}
                onClick={(e) => {
                  e.preventDefault()
                  onQuickAdd?.(book.id, shelf)
                  setShowShelfMenu(false)
                }}
                className="block w-full rounded px-3 py-2 text-left text-sm hover:bg-indigo-100 dark:hover:bg-indigo-900"
              >
                {shelf}
              </button>
            ))}
          </div>
        )}
      </div>
    </Link>
  )
}
