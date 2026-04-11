'use client'

import { useState, useTransition } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import RatingStars from './RatingStars'
import { Save } from 'lucide-react'

interface UserBookPanelProps {
  bookId: string
  initialShelf?: string
  initialRating?: number
  initialNotes?: string
}

export default function UserBookPanel({
  bookId,
  initialShelf,
  initialRating,
  initialNotes,
}: UserBookPanelProps) {
  const [shelf, setShelf] = useState<string>(initialShelf || '')
  const [rating, setRating] = useState<number>(initialRating || 0)
  const [notes, setNotes] = useState<string>(initialNotes || '')
  const [saved, setSaved] = useState(false)
  const [isPending, startTransition] = useTransition()
  const router = useRouter()
  const supabase = createClient()

  const shelves = ['To Read', 'Currently Reading', 'Read', 'Loaned Out']

  const handleSave = async () => {
    startTransition(async () => {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser()

        if (!user) return

        const { error } = await supabase.from('user_books').upsert(
          {
            user_id: user.id,
            book_id: bookId,
            shelf: shelf || null,
            rating: rating || null,
            notes: notes || null,
            date_added: new Date().toISOString(),
          },
          { onConflict: 'user_id,book_id' }
        )

        if (error) throw error

        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
        router.refresh()
      } catch (error) {
        console.error('Error saving book:', error)
      }
    })
  }

  return (
    <div className="card p-6">
      <h2 className="mb-6 text-2xl font-bold text-light dark:text-dark">Track This Book</h2>

      <div className="space-y-6">
        {/* Shelf Selector */}
        <div>
          <label htmlFor="shelf" className="mb-2 block text-sm font-medium text-light dark:text-dark">
            Shelf
          </label>
          <select
            id="shelf"
            value={shelf}
            onChange={(e) => setShelf(e.target.value)}
            className="input-field w-full"
          >
            <option value="">Select a shelf...</option>
            {shelves.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        {/* Rating */}
        <div>
          <label className="mb-3 block text-sm font-medium text-light dark:text-dark">
            Rating
          </label>
          <RatingStars value={rating} onChange={setRating} size="lg" />
        </div>

        {/* Notes */}
        <div>
          <label htmlFor="notes" className="mb-2 block text-sm font-medium text-light dark:text-dark">
            Notes
          </label>
          <textarea
            id="notes"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add your thoughts about this book..."
            rows={4}
            className="input-field w-full resize-none"
          />
        </div>

        {/* Save Button */}
        <button
          onClick={handleSave}
          disabled={isPending}
          className={`btn-primary flex items-center justify-center gap-2 w-full ${saved ? 'bg-green-600 hover:bg-green-700' : ''}`}
        >
          <Save size={20} />
          {isPending ? 'Saving...' : saved ? 'Saved!' : 'Save'}
        </button>
      </div>
    </div>
  )
}
