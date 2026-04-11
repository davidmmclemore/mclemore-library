'use client'

import { Star } from 'lucide-react'
import { useState } from 'react'

interface RatingStarsProps {
  value?: number
  onChange?: (rating: number) => void
  disabled?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function RatingStars({
  value = 0,
  onChange,
  disabled = false,
  size = 'md',
}: RatingStarsProps) {
  const [hoverRating, setHoverRating] = useState(0)

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  }

  return (
    <div className="flex gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          onClick={() => !disabled && onChange?.(star)}
          onMouseEnter={() => !disabled && setHoverRating(star)}
          onMouseLeave={() => setHoverRating(0)}
          disabled={disabled}
          className={`transition-colors ${disabled ? 'cursor-default' : 'cursor-pointer hover:text-yellow-500'}`}
        >
          <Star
            className={sizeClasses[size]}
            fill={star <= (hoverRating || value) ? 'currentColor' : 'none'}
            color={star <= (hoverRating || value) ? '#eab308' : '#d1d5db'}
          />
        </button>
      ))}
    </div>
  )
}
