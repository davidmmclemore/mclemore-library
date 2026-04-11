'use client'

import { useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { ChevronDown, X } from 'lucide-react'

interface FilterPanelProps {
  categories: string[]
  formats: string[]
  locations: string[]
  authors: string[]
  tags: string[]
}

export default function FilterPanel({
  categories,
  formats,
  locations,
  authors,
  tags,
}: FilterPanelProps) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    category: true,
    format: true,
  })

  const currentCategory = searchParams.get('category')
  const currentFormat = searchParams.get('format')
  const currentLocation = searchParams.get('location')
  const currentAuthor = searchParams.get('author')
  const currentQuery = searchParams.get('q')
  const currentTags = searchParams.getAll('tags')

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => ({
      ...prev,
      [section]: !prev[section],
    }))
  }

  const updateFilter = (key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (value) {
      params.set(key, value)
    } else {
      params.delete(key)
    }
    params.set('page', '1')
    router.push(`/?${params.toString()}`)
  }

  const toggleTag = (tag: string) => {
    const params = new URLSearchParams(searchParams.toString())
    const tags = params.getAll('tags')

    if (tags.includes(tag)) {
      params.delete('tags')
      tags.filter((t) => t !== tag).forEach((t) => params.append('tags', t))
    } else {
      params.append('tags', tag)
    }
    params.set('page', '1')
    router.push(`/?${params.toString()}`)
  }

  const clearFilters = () => {
    router.push('/')
  }

  const hasActiveFilters =
    currentCategory || currentFormat || currentLocation || currentAuthor || currentTags.length > 0

  return (
    <div className="card max-h-[calc(100vh-200px)] overflow-y-auto p-4 scrollbar-thin">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-semibold text-light dark:text-dark">Filters</h2>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded px-2 py-1 text-xs hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X size={14} />
            Clear
          </button>
        )}
      </div>

      <div className="space-y-4">
        {/* Search doesn't need to be here as it's in Navbar */}

        {/* Category Filter */}
        <div>
          <button
            onClick={() => toggleSection('category')}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <h3 className="font-medium text-sm text-light dark:text-dark">Category</h3>
            <ChevronDown
              size={18}
              className={`transition-transform ${expandedSections.category ? 'rotate-180' : ''}`}
            />
          </button>
          {expandedSections.category && (
            <div className="mt-2 space-y-2 pl-4">
              <select
                value={currentCategory || ''}
                onChange={(e) => updateFilter('category', e.target.value || null)}
                className="input-field w-full text-sm"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Format Filter */}
        <div>
          <button
            onClick={() => toggleSection('format')}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <h3 className="font-medium text-sm text-light dark:text-dark">Format</h3>
            <ChevronDown
              size={18}
              className={`transition-transform ${expandedSections.format ? 'rotate-180' : ''}`}
            />
          </button>
          {expandedSections.format && (
            <div className="mt-2 space-y-2 pl-4">
              <select
                value={currentFormat || ''}
                onChange={(e) => updateFilter('format', e.target.value || null)}
                className="input-field w-full text-sm"
              >
                <option value="">All Formats</option>
                {formats.map((fmt) => (
                  <option key={fmt} value={fmt}>
                    {fmt}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Location Filter */}
        <div>
          <button
            onClick={() => toggleSection('location')}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <h3 className="font-medium text-sm text-light dark:text-dark">Location</h3>
            <ChevronDown
              size={18}
              className={`transition-transform ${expandedSections.location ? 'rotate-180' : ''}`}
            />
          </button>
          {expandedSections.location && (
            <div className="mt-2 space-y-2 pl-4">
              <select
                value={currentLocation || ''}
                onChange={(e) => updateFilter('location', e.target.value || null)}
                className="input-field w-full text-sm"
              >
                <option value="">All Locations</option>
                {locations.map((loc) => (
                  <option key={loc} value={loc}>
                    {loc}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Author Filter */}
        <div>
          <button
            onClick={() => toggleSection('author')}
            className="flex w-full items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <h3 className="font-medium text-sm text-light dark:text-dark">Author</h3>
            <ChevronDown
              size={18}
              className={`transition-transform ${expandedSections.author ? 'rotate-180' : ''}`}
            />
          </button>
          {expandedSections.author && (
            <div className="mt-2 pl-4">
              <input
                type="text"
                placeholder="Filter authors..."
                value={currentAuthor || ''}
                onChange={(e) => updateFilter('author', e.target.value || null)}
                className="input-field w-full text-sm"
              />
            </div>
          )}
        </div>

        {/* Tags Filter */}
        {tags.length > 0 && (
          <div>
            <button
              onClick={() => toggleSection('tags')}
              className="flex w-full items-center justify-between rounded-lg px-3 py-2 hover:bg-gray-100 dark:hover:bg-gray-700"
            >
              <h3 className="font-medium text-sm text-light dark:text-dark">Tags</h3>
              <ChevronDown
                size={18}
                className={`transition-transform ${expandedSections.tags ? 'rotate-180' : ''}`}
              />
            </button>
            {expandedSections.tags && (
              <div className="mt-2 flex flex-wrap gap-2 pl-4">
                {tags.slice(0, 20).map((tag) => (
                  <button
                    key={tag}
                    onClick={() => toggleTag(tag)}
                    className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${
                      currentTags.includes(tag)
                        ? 'bg-indigo-600 text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:hover:bg-gray-600'
                    }`}
                  >
                    {tag}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
