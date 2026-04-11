'use client'

import { useEffect, useState } from 'react'
import { Moon, Sun } from 'lucide-react'

export default function ThemeToggle() {
  const [isDark, setIsDark] = useState(false)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    const isDarkMode = document.documentElement.classList.contains('dark')
    setIsDark(isDarkMode)
  }, [])

  const toggleTheme = () => {
    if (!mounted) return

    const html = document.documentElement
    const newIsDark = !isDark

    if (newIsDark) {
      html.classList.add('dark')
    } else {
      html.classList.remove('dark')
    }

    setIsDark(newIsDark)
    localStorage.setItem('theme', newIsDark ? 'dark' : 'light')
  }

  if (!mounted) {
    return <div className="h-10 w-10" />
  }

  return (
    <button
      onClick={toggleTheme}
      className="rounded-lg p-2 hover:bg-gray-100 dark:hover:bg-gray-700"
      aria-label="Toggle theme"
    >
      {isDark ? <Sun size={20} /> : <Moon size={20} />}
    </button>
  )
}
