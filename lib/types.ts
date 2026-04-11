export interface Book {
  id: string
  title: string
  author: string
  format: string
  category: string
  pages: number
  tags: string[]
  location: string
  summary: string | null
  isbn_13: string | null
  isbn_10: string | null
  logos_id: string | null
  cover_url: string | null
  amazon_url: string | null
  asin: string | null
  series_name: string | null
  series_volume: number | null
}

export interface UserBook {
  id: string
  user_id: string
  book_id: string
  shelf: 'To Read' | 'Currently Reading' | 'Read' | 'Loaned Out'
  rating: number | null
  notes: string | null
  date_added: string
  date_finished: string | null
}

export interface Shelf {
  id: string
  user_id: string
  name: string
  description: string | null
  is_public: boolean
}

export interface ShelfBook {
  shelf_id: string
  book_id: string
}

export interface Profile {
  id: string
  display_name: string | null
  avatar_url: string | null
}

export interface BookWithUserData extends Book {
  user_book?: UserBook
}
