'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase/client'
import { Shelf } from '@/lib/types'
import { Plus, Trash2, BookOpen } from 'lucide-react'

export default function ShelvesPage() {
  const [shelves, setShelves] = useState<Shelf[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newShelfName, setNewShelfName] = useState('')
  const [newShelfDesc, setNewShelfDesc] = useState('')
  const [shelfCounts, setShelfCounts] = useState<Record<string, number>>({})
  const router = useRouter()
  const supabase = createClient()

  useEffect(() => {
    const loadShelves = async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) {
          router.push('/auth/login')
          return
        }

        const { data: shelvesData, error: shelvesError } = await supabase
          .from('shelves')
          .select('*')
          .eq('user_id', user.id)

        if (shelvesError) throw shelvesError

        setShelves(shelvesData || [])

        const { data: shelfBooksData, error: booksError } = await supabase
          .from('shelf_books')
          .select('shelf_id')

        if (booksError) throw booksError

        const counts: Record<string, number> = {}
        shelfBooksData?.forEach((sb: any) => {
          counts[sb.shelf_id] = (counts[sb.shelf_id] || 0) + 1
        })
        setShelfCounts(counts)
      } catch (error) {
        console.error('Error loading shelves:', error)
      } finally {
        setLoading(false)
      }
    }

    loadShelves()
  }, [supabase, router])

  const handleCreateShelf = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newShelfName.trim()) return

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser()

      if (!user) return

      const { data, error } = await supabase
        .from('shelves')
        .insert({
          user_id: user.id,
          name: newShelfName,
          description: newShelfDesc || null,
          is_public: false,
        })
        .select()

      if (error) throw error

      setShelves([...shelves, data[0]])
      setNewShelfName('')
      setNewShelfDesc('')
      setShowCreateForm(false)
    } catch (error) {
      console.error('Error creating shelf:', error)
    }
  }

  const handleDeleteShelf = async (shelfId: string) => {
    if (!confirm('Are you sure you want to delete this shelf?')) return

    try {
      const { error: booksError } = await supabase
        .from('shelf_books')
        .delete()
        .eq('shelf_id', shelfId)

      if (booksError) throw booksError

      const { error: shelfError } = await supabase
        .from('shelves')
        .delete()
        .eq('id', shelfId)

      if (shelfError) throw shelfError

      setShelves(shelves.filter((s) => s.id !== shelfId))
    } catch (error) {
      console.error('Error deleting shelf:', error)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="h-24 rounded-lg bg-gray-200 dark:bg-gray-700" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-beige-200 dark:bg-gray-900 py-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold text-light dark:text-dark">My Shelves</h1>
            <p className="text-light-secondary">Organize books into custom shelves</p>
          </div>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus size={20} />
            New Shelf
          </button>
        </div>

        {showCreateForm && (
          <div className="card mb-8 p-6">
            <form onSubmit={handleCreateShelf} className="space-y-4">
              <div>
                <label htmlFor="shelfName" className="mb-2 block text-sm font-medium text-light dark:text-dark">
                  Shelf Name
                </label>
                <input
                  id="shelfName"
                  type="text"
                  value={newShelfName}
                  onChange={(e) => setNewShelfName(e.target.value)}
                  placeholder="e.g., Favorites, Winter Reading..."
                  className="input-field"
                  required
                />
              </div>

              <div>
                <label htmlFor="shelfDesc" className="mb-2 block text-sm font-medium text-light dark:text-dark">
                  Description (optional)
                </label>
                <textarea
                  id="shelfDesc"
                  value={newShelfDesc}
                  onChange={(e) => setNewShelfDesc(e.target.value)}
                  placeholder="Describe what this shelf is for..."
                  rows={3}
                  className="input-field resize-none"
                />
              </div>

              <div className="flex gap-3">
                <button type="submit" className="btn-primary">
                  Create Shelf
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>
        )}

        {shelves.length === 0 ? (
          <div className="card p-12 text-center">
            <BookOpen size={48} className="mx-auto mb-4 text-gray-400" />
            <h3 className="mb-2 text-lg font-semibold text-light dark:text-dark">No shelves yet</h3>
            <p className="text-light-secondary">Create a shelf to organize your books</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {shelves.map((shelf) => (
              <Link key={shelf.id} href={`/shelves/${shelf.id}`}>
                <div className="card p-6 h-full flex flex-col cursor-pointer hover:shadow-lg transition-shadow">
                  <h3 className="text-xl font-semibold text-light dark:text-dark mb-2">
                    {shelf.name}
                  </h3>

                  {shelf.description && (
                    <p className="text-light-secondary text-sm mb-4 line-clamp-2">
                      {shelf.description}
                    </p>
                  )}

                  <div className="mt-auto flex items-center justify-between">
                    <p className="text-sm text-light-secondary">
                      {shelfCounts[shelf.id] || 0} books
                    </p>
                    <button
                      onClick={(e) => {
                        e.preventDefault()
                        handleDeleteShelf(shelf.id)
                      }}
                      className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                      aria-label="Delete shelf"
                    >
                      <Trash2 size={20} />
                    </button>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
