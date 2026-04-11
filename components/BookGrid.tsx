'use client'

import { Book } from '@/lib/types'
import BookCard from './BookCard'
import { useTransition } from 'react'

interface BookGridProps {
  books: Book[]
  loading?: boolean
  onQuickAdd?: (bookId: string, shelf: string) => Promise<void>
  showQuickAdd?: boolean
}

export default function BookGrid({ books, loading = false, onQuickAdd, showQuickAdd = false }: BookGridProps) {
  const [isPending, startTransition] = useTransition()

  if (loading || isPending) {
    return (
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
        {Array.from({ length: 12 }).map((_, i) => (
          <div key={i} className="card aspect-[2/3] animate-pulse bg-gray-200 dark:bg-gray-700" />
        ))}
      </div>
    )
  }

  if (books.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-gray-300 py-16 dark:border-gray-700">
        <span className="text-5xl mb-4">📚</span>
        <h3 className="text-lg font-semibold text-light dark:text-dark">No books found</h3>
        <p className="text-light-secondary">Try adjusting your filters or search terms</p>
      </div>
    )
  }

  return (
    <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
      {books.map((book) => (
        <BookCard
          key={book.id}
          book={book}
          showQuickAdd={showQuickAdd}
          onQuickAdd={
            onQuickAdd
              ? (bookId, shelf) => {
                  startTransition(() => onQuickAdd(bookId, shelf))
                }
              : undefined
          }
        />
      ))}
    </div>
  )
}
