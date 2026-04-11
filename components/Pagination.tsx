'use client'

import { useRouter, useSearchParams } from 'next/navigation'
import { ChevronLeft, ChevronRight } from 'lucide-react'

interface PaginationProps {
  currentPage: number
  totalBooks: number
  booksPerPage: number
}

export default function Pagination({ currentPage, totalBooks, booksPerPage }: PaginationProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const totalPages = Math.ceil(totalBooks / booksPerPage)

  const handlePageChange = (newPage: number) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', newPage.toString())
    router.push(`/?${params.toString()}`)
  }

  if (totalPages <= 1) {
    return null
  }

  return (
    <div className="flex items-center justify-center gap-4 py-8">
      <button
        onClick={() => handlePageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="btn-secondary flex items-center gap-2 disabled:opacity-50"
      >
        <ChevronLeft size={20} />
        Previous
      </button>

      <div className="flex items-center gap-2">
        {Array.from({ length: Math.min(5, totalPages) }).map((_, i) => {
          let pageNum = currentPage - 2 + i
          if (pageNum < 1) pageNum = 1
          if (pageNum > totalPages) pageNum = totalPages

          return (
            <button
              key={pageNum}
              onClick={() => handlePageChange(pageNum)}
              className={`min-w-[40px] rounded-lg px-3 py-2 font-medium transition-colors ${
                pageNum === currentPage
                  ? 'bg-indigo-600 text-white'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              {pageNum}
            </button>
          )
        })}
      </div>

      <button
        onClick={() => handlePageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="btn-secondary flex items-center gap-2 disabled:opacity-50"
      >
        Next
        <ChevronRight size={20} />
      </button>
    </div>
  )
}
