# Quick Start Guide

Get McLemore Library running in 5 minutes.

## Prerequisites

- Node.js 18 or higher
- npm or yarn
- A modern web browser
- Internet connection

## Installation

### 1. Navigate to the project directory

```bash
cd "/sessions/quirky-sharp-brahmagupta/mnt/McLemore Library/personal-library"
```

### 2. Install dependencies

```bash
npm install
```

This will install all required packages from package.json:
- Next.js 14
- React 18
- Supabase client libraries
- Tailwind CSS
- Lucide React icons

### 3. Start the development server

```bash
npm run dev
```

You should see:
```
> personal-library@1.0.0 dev
> next dev

  ▲ Next.js 14.x.x
  - Local:        http://localhost:3000
```

### 4. Open in your browser

Visit `http://localhost:3000`

You should see the McLemore Library homepage with:
- Navigation bar with search
- "Book of the Day" featured book
- Filter sidebar
- Grid of books from the catalog

## First Steps

### Browsing Books

1. The main page shows all 11,306 books in the catalog
2. Use the search bar to find books by title, author, or summary
3. Click on any book card to view full details
4. Use filters on the left to narrow results by:
   - Category
   - Format
   - Location
   - Author
   - Tags

### Creating an Account

1. Click "Sign Up" in the top right
2. Enter your email and password (minimum 6 characters)
3. Enter your display name
4. Click "Create Account"
5. You'll be redirected to the home page (now logged in)

### Logging In

1. Click "Log In" in the top right
2. Enter your email and password
3. Click "Sign In"
4. You'll be redirected to the home page

### Tracking Books

Once logged in, you can track books:

1. **Add to Shelf**: On the catalog, hover over a book and click "Add to Shelf"
2. **View Book Details**: Click any book to see full information
3. **Add to Library**: On book detail page, use "Track This Book" panel to:
   - Select a shelf (To Read, Currently Reading, Read, Loaned Out)
   - Rate with stars (1-5)
   - Add personal notes
   - Click "Save"

### Managing Your Library

1. Click "Library" in the navigation (top right, after logging in)
2. See your books organized by shelf
3. View statistics:
   - Total books tracked
   - Pages read
   - Categories in your library
4. Switch between shelves using the tabs
5. Update a book's shelf or delete from library

### Creating Custom Shelves

1. Click "Shelves" in the navigation
2. Click "New Shelf" button
3. Enter shelf name and optional description
4. Click "Create Shelf"
5. Click on a shelf to view books in it
6. Add books from catalog by using "Add to Shelf" quick menu

## Features Overview

### Public Features (No Login Required)

- Browse 11,306 books
- Search by title, author, or summary
- Filter by category, format, location, author, tags
- View book details including:
  - Cover image
  - Summary
  - Series information
  - ISBN numbers
  - Links to Amazon
  - Physical location in library
  - Tags

### Personal Features (Login Required)

- Track books across custom shelves:
  - To Read (wishlist)
  - Currently Reading (in progress)
  - Read (completed)
  - Loaned Out (given to friends)
- Rate books 1-5 stars
- Add personal notes to books
- Create unlimited custom shelves
- View reading statistics:
  - Total books tracked
  - Pages read
  - Books by category
- Manage your entire book collection

## Theme Toggle

The app supports dark mode:
1. Click the sun/moon icon in the top right
2. Dark mode preference is saved to browser storage
3. Switch between light and dark themes anytime

## Search Tips

### Effective Searching

- **By Title**: Search for exact titles or partial matches
  - "Harry Potter" finds all Harry Potter books
  - "Song of" finds "A Song of Ice and Fire"

- **By Author**: Search author names
  - "Stephen King" finds all Stephen King books
  - "J.K." finds J.K. Rowling

- **By Topic**: Search summary text
  - "fantasy" finds books with fantasy themes
  - "mystery" finds mystery novels

### Using Filters

Combine multiple filters for precise results:
1. Select Category (Fiction, Non-Fiction, etc.)
2. Select Format (Hardcover, Paperback, eBook, etc.)
3. Type Author name (partial match works)
4. Select Location (shelf location in library)
5. Select Tags (multiple can be selected)

## Troubleshooting

### Page Not Loading

1. Clear browser cache: `Ctrl+Shift+Delete` (or `Cmd+Shift+Delete` on Mac)
2. Hard refresh: `Ctrl+F5` (or `Cmd+Shift+R` on Mac)
3. Check that `npm run dev` is still running

### Can't Log In

1. Verify your email and password are correct
2. Check that caps lock is off
3. Ensure cookies are enabled in your browser

### Books Not Appearing

1. Wait a moment for the page to load (first load may take 5-10 seconds)
2. Check that you have an internet connection
3. Try refreshing the page
4. Check browser console for errors (F12)

### Search Not Working

1. Make sure you pressed Enter or clicked the search button
2. Try a different search term
3. Clear filters and try again

## Development Commands

```bash
# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run ESLint (code quality)
npm run lint
```

## Project Structure Overview

```
personal-library/
├── app/              # Next.js App Router pages and layouts
├── components/       # Reusable React components
├── lib/              # Utilities and helpers
│   └── supabase/     # Supabase client configuration
├── package.json      # Dependencies and scripts
├── tsconfig.json     # TypeScript configuration
├── tailwind.config.js # Tailwind CSS customization
└── README.md         # Full documentation
```

## Important Notes

### Supabase Connection

The app is pre-configured to connect to a live Supabase instance with:
- 11,306 books
- User authentication
- Book tracking database
- Custom shelves system

Environment variables are already set in `.env.local`:
```
NEXT_PUBLIC_SUPABASE_URL=https://zfhbetdwmbvuuvwqmnqu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<provided-key>
```

### Browser Compatibility

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)
- Mobile browsers (iOS Safari, Chrome Mobile)

### Performance

- Initial load: 2-5 seconds
- Book search: instant (client-side filtering)
- Page navigation: <1 second
- Image loading: optimized with Next.js Image component

## Next Steps

1. **Explore the catalog**: Browse books and use filters
2. **Create an account**: Sign up to start tracking books
3. **Add books**: Build your personal library
4. **Create shelves**: Organize books into custom collections
5. **Read more**: See README.md for full documentation

## Need Help?

Check these resources:
1. **README.md** - Full project documentation
2. **DEPLOYMENT.md** - Setup and deployment instructions
3. **Browser Console** - Press F12 to see any errors
4. **Network Tab** - Check API calls and responses

## Tips for Best Experience

1. **Organize by Shelves**: Create shelves for different reading goals
   - "Sci-Fi Favorites"
   - "Books to Read This Year"
   - "Borrowed from Friends"

2. **Use Ratings**: Rate books to track what you liked
   - 5 stars: Love it, recommend to everyone
   - 4 stars: Really good, worth reading
   - 3 stars: Good, worth the time
   - 2 stars: Okay, has some issues
   - 1 star: Not for me

3. **Add Notes**: Document your thoughts
   - "Read with book club in June"
   - "Compare with movie version"
   - "Plot twists in chapter 12!"

4. **Track Series**: Filter by series name to see all books in a series

Happy reading!
