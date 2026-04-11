import { Suspense } from 'react'
import { createServerComponentClient } from '@/lib/supabase/server'
import BookOfDay from '@/components/BookOfDay'
import FilterPanel from '@/components/FilterPanel'
import BookGrid from '@/components/BookGrid'
import Pagination from '@/components/Pagination'
import { Book } from '@/lib/types'

async function getFilterMetadata(supabase: any) {
  const [categoriesRes, formatsRes, locationsRes, authorsRes, tagsRes] = await Promise.all([
    supabase.from('books').select('category').limit(1),
    supabase.from('books').select('format').limit(1),
    supabase.from('books').select('location').limit(1),
    supabase.from('books').select('author').limit(1),
    supabase.from('books').select('tags').limit(1),
  ])

  const categories = await supabase.rpc('get_distinct_categories')
  const formats = await supabase.rpc('get_distinct_formats')
  const locations = await supabase.rpc('get_distinct_locations')
  const authors = await supabase.rpc('get_distinct_authors')
  const tags = await supabase.rpc('get_distinct_tags')

  return {
    categories: categories.data || [],
    formats: formats.data || [],
    locations: locations.data || [],
    authors: authors.data || [],
    tags: tags.data || [],
  }
}

async function getBooks(
  supabase: any,
  searchQuery?: string,
  category?: string,
  format?: string,
  location?: string,
  author?: string,
  tags?: string[],
  page: number = 1
) {
  const pageSize = 50
  const offset = (page - 1) * pageSize

  let query = supabase.from('books').select('*', { count: 'exact' })

  if (searchQuery) {
    query = query.or(
      `title.ilike.%${searchQuery}%,author.ilike.%${searchQuery}%,summary.ilike.%${searchQuery}%`
    )
  }

  if (category) {
    query = query.eq('category', category)
  }

  if (format) {
    query = query.eq('format', format)
  }

  if (location) {
    query = query.eq('location', location)
  }

  if (author) {
    query = query.ilike('author', `%${author}%`)
  }

  if (tags && tags.length > 0) {
    query = query.contains('tags', tags)
  }

  const { data, count, error } = await query
    .order('title', { ascending: true })
    .range(offset, offset + pageSize - 1)

  if (error) {
    console.error('Error fetching books:', error)
    return { books: [], count: 0 }
  }

  return { books: (data || []) as Book[], count: count || 0 }
}

export default async function CatalogPage({
  searchParams,
}: {
  searchParams: Promise<Record<string, string | string[]>>
}) {
  const params = await searchParams
  const supabase = await createServerComponentClient()

  const searchQuery = typeof params.q === 'string' ? params.q : ''
  const category = typeof params.category === 'string' ? params.category : ''
  const format = typeof params.format === 'string' ? params.format : ''
  const location = typeof params.location === 'string' ? params.location : ''
  const author = typeof params.author === 'string' ? params.author : ''
  const tags = Array.isArray(params.tags) ? params.tags : params.tags ? [params.tags] : []
  const page = typeof params.page === 'string' ? parseInt(params.page, 10) : 1

  const [filterMetadata, { books, count }] = await Promise.all([
    getFilterMetadata(supabase),
    getBooks(supabase, searchQuery, category, format, location, author, tags, page),
  ])

  return (
    <div className="min-h-screen bg-beige-200 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-8">
          <h1 className="mb-2 text-4xl font-bold text-light dark:text-dark">Book Catalog</h1>
          <p className="text-light-secondary">
            Browse {count.toLocaleString()} books in our collection
          </p>
        </div>

        <Suspense fallback={<div className="h-96 animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700" />}>
          <BookOfDay />
        </Suspense>

        <div className="grid gap-8 lg:grid-cols-4">
          <aside className="lg:col-span-1">
            <FilterPanel
              categories={filterMetadata.categories}
              formats={filterMetadata.formats}
              locations={filterMetadata.locations}
              authors={filterMetadata.authors}
              tags={filterMetadata.tags}
            />
          </aside>

          <main className="lg:col-span-3">
            <div className="mb-6 flex items-center justify-between">
              <p className="text-sm text-light-secondary">
                Showing {books.length === 0 ? 0 : (page - 1) * 50 + 1} to{' '}
                {Math.min(page * 50, count)} of {count.toLocaleString()} books
              </p>
            </div>

            <Suspense fallback={<div className="animate-pulse rounded-xl bg-gray-200 dark:bg-gray-700 h-96" />}>
              <BookGrid books={books} />
            </Suspense>

            <Pagination currentPage={page} totalBooks={count} booksPerPage={50} />
          </main>
        </div>
      </div>
    </div>
  )
}
