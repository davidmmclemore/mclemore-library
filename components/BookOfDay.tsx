import Link from 'next/link'
import Image from 'next/image'
import { Book } from '@/lib/types'
import { createServerComponentClient } from '@/lib/supabase/server'

export default async function BookOfDay() {
  const supabase = await createServerComponentClient()

  try {
    const seed = new Date().toISOString().split('T')[0]
    const seedHash = Array.from(seed).reduce((acc, char) => acc + char.charCodeAt(0), 0)

    const { data, error } = await supabase
      .from('books')
      .select('*')
      .limit(1)
      .offset(seedHash % 11306)
      .single()

    if (error || !data) {
      return null
    }

    const book = data as Book

    return (
      <Link href={`/book/${book.id}`}>
        <div className="card group mb-8 cursor-pointer overflow-hidden">
          <div className="grid grid-cols-1 gap-6 p-6 md:grid-cols-4">
            <div className="md:col-span-1">
              <div className="relative aspect-[2/3] overflow-hidden rounded-lg">
                {book.cover_url ? (
                  <Image
                    src={book.cover_url}
                    alt={book.title}
                    fill
                    className="object-cover transition-transform duration-300 group-hover:scale-110"
                    sizes="(max-width: 768px) 100vw, 25vw"
                  />
                ) : (
                  <div className="flex h-full w-full items-center justify-center bg-gradient-to-br from-indigo-200 to-indigo-100 dark:from-indigo-900 dark:to-indigo-800">
                    <span className="text-5xl">📖</span>
                  </div>
                )}
              </div>
            </div>

            <div className="md:col-span-3 flex flex-col justify-center">
              <div className="badge mb-3 w-fit">Book of the Day</div>
              <h2 className="mb-2 text-3xl font-bold text-indigo-600 dark:text-indigo-400">
                {book.title}
              </h2>
              <p className="mb-4 text-lg text-light-secondary">{book.author}</p>

              {book.summary && (
                <p className="mb-4 line-clamp-3 text-light dark:text-dark-secondary">
                  {book.summary}
                </p>
              )}

              <div className="flex flex-wrap gap-2">
                <span className="badge text-sm">{book.format}</span>
                <span className="badge text-sm">{book.category}</span>
                {book.pages && (
                  <span className="badge text-sm">{book.pages} pages</span>
                )}
              </div>

              <div className="mt-4 inline-flex items-center rounded-lg bg-indigo-600 px-4 py-2 font-medium text-white transition-colors group-hover:bg-indigo-700 w-fit">
                Explore →
              </div>
            </div>
          </div>
        </div>
      </Link>
    )
  } catch (error) {
    console.error('Error fetching book of day:', error)
    return null
  }
}
