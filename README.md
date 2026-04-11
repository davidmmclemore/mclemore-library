# McLemore Library - Personal Book Library Application

A production-ready Next.js 14 full-stack application for managing a personal book library with Supabase backend.

## Features

- **Public Catalog**: Browse 11,306+ books with advanced filtering and search
- **User Authentication**: Sign up, log in, and manage your account
- **Book Tracking**: Add books to custom shelves (To Read, Currently Reading, Read, Loaned Out)
- **Ratings & Notes**: Rate books 1-5 stars and add personal notes
- **Custom Shelves**: Create and organize books into custom collections
- **Reading Statistics**: Track total books, pages read, and category breakdowns
- **Dark Mode**: Full light/dark theme support with localStorage persistence
- **Responsive Design**: Mobile-first design that works on all screen sizes
- **Book Details**: View comprehensive book information including summaries, series info, and external links

## Tech Stack

- **Frontend**: Next.js 14 (App Router), React 18, Tailwind CSS
- **Backend**: Supabase (PostgreSQL, Auth, Realtime)
- **UI Components**: Lucide React icons
- **Utilities**: clsx, TypeScript

## Setup

### Prerequisites

- Node.js 18+ and npm/yarn
- Supabase project with proper schema setup

### Installation

1. Clone the repository:
```bash
cd personal-library
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment variables:
```bash
cp .env.local.example .env.local
```

The `.env.local` file already contains the required credentials.

### Running the Application

Development:
```bash
npm run dev
```

Production:
```bash
npm run build
npm start
```

The application will be available at `http://localhost:3000`

## Project Structure

```
personal-library/
├── app/
│   ├── page.tsx                 # Main catalog page
│   ├── layout.tsx               # Root layout
│   ├── globals.css              # Global styles
│   ├── book/[id]/page.tsx       # Book detail page
│   ├── library/page.tsx         # User library (protected)
│   ├── shelves/
│   │   ├── page.tsx             # Shelves listing (protected)
│   │   └── [id]/page.tsx        # Individual shelf view (protected)
│   └── auth/
│       ├── login/page.tsx       # Login page
│       ├── signup/page.tsx      # Sign up page
│       └── callback/route.ts    # OAuth callback handler
├── components/
│   ├── Navbar.tsx               # Navigation bar
│   ├── BookCard.tsx             # Book card component
│   ├── BookGrid.tsx             # Responsive grid layout
│   ├── BookOfDay.tsx            # Featured book banner
│   ├── FilterPanel.tsx          # Filter sidebar
│   ├── UserBookPanel.tsx        # User interaction panel
│   ├── RatingStars.tsx          # Star rating component
│   ├── Pagination.tsx           # Pagination controls
│   ├── ThemeToggle.tsx          # Dark/light mode toggle
│   └── AuthForm.tsx             # Reusable auth form
├── lib/
│   ├── types.ts                 # TypeScript interfaces
│   └── supabase/
│       ├── client.ts            # Browser client
│       ├── server.ts            # Server client
│       └── middleware.ts        # Session middleware
├── middleware.ts                # Auth middleware
└── tailwind.config.js           # Tailwind configuration
```

## Database Schema

### Books Table
- id: UUID (primary key)
- title: Text
- author: Text
- format: Text
- category: Text
- pages: Integer
- tags: Text array
- location: Text
- summary: Text
- isbn_13, isbn_10: Text
- logos_id, asin: Text
- cover_url, amazon_url: Text
- series_name: Text
- series_volume: Integer

### User Books Table
- id: UUID (primary key)
- user_id: UUID (foreign key to auth.users)
- book_id: UUID (foreign key to books)
- shelf: Text (To Read, Currently Reading, Read, Loaned Out)
- rating: Integer (1-5)
- notes: Text
- date_added: Timestamp
- date_finished: Timestamp

### Shelves Table
- id: UUID (primary key)
- user_id: UUID (foreign key to auth.users)
- name: Text
- description: Text
- is_public: Boolean

### Shelf Books Table
- shelf_id: UUID (foreign key to shelves)
- book_id: UUID (foreign key to books)

### Profiles Table
- id: UUID (primary key, foreign key to auth.users)
- display_name: Text
- avatar_url: Text

## Authentication

The application uses Supabase Authentication with email/password signup and login. Sessions are managed using cookies and HTTP-only tokens for security.

### Protected Routes

- `/library` - User's personal library
- `/shelves` - User's custom shelves
- `/shelves/[id]` - Individual shelf view

Unauthenticated users are redirected to `/auth/login`.

## Color Scheme

- Primary: Indigo (#4f46e5)
- Secondary Background: Beige (#f0f0ee)
- Dark Mode: Gray-900 (#0f172a)
- Accent: Yellow (ratings/stars)

## Performance

- Server-side rendering for public pages
- Client-side filtering and search with URL params
- Image optimization with Next.js Image component
- Remote pattern configuration for Amazon and Supabase images
- Efficient pagination with 50 books per page
- Dark mode implementation without flash

## Security

- Middleware-based authentication
- Protected API routes and database queries
- Secure session management with Supabase
- Environment variables for sensitive data
- No sensitive data in URL parameters

## Development

Run tests:
```bash
npm test
```

Build for production:
```bash
npm run build
```

Deploy to production:
The application is configured for deployment on Vercel or any Node.js-compatible platform.

## License

This project is part of the McLemore Library system.
