# Architecture Overview - McLemore Library

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (Browser)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Next.js 14 App (React 18 Components)               │  │
│  │  ├─ Public Pages (Catalog, Book Detail)             │  │
│  │  ├─ Protected Pages (Library, Shelves)              │  │
│  │  └─ Auth Pages (Login, Signup)                      │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  Middleware │
                    │  (Auth Check)│
                    └──────┬──────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Supabase Backend                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication (Email/Password)                     │  │
│  │  ├─ Session Management (Cookies)                    │  │
│  │  └─ OAuth Callbacks                                 │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  PostgreSQL Database                                 │  │
│  │  ├─ books (11,306 records)                          │  │
│  │  ├─ user_books (user tracking)                      │  │
│  │  ├─ shelves (custom shelves)                        │  │
│  │  ├─ shelf_books (shelf contents)                    │  │
│  │  └─ profiles (user profiles)                        │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Row Level Security (RLS) Policies                   │  │
│  │  ├─ Books: Public Read-Only                         │  │
│  │  ├─ User Books: User-Only Access                    │  │
│  │  ├─ Shelves: User-Only Access                       │  │
│  │  └─ Profiles: Public Read, User Update              │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### Catalog Page (Public)
```
User visits / 
    ↓
Page.tsx (Server Component)
    ├─ Fetch books with filters
    ├─ Fetch filter metadata (categories, formats, etc.)
    └─ Render with BookGrid + FilterPanel
        ↓
User interacts with filters
    ├─ Update URL search params
    ├─ Page re-renders with new data
    └─ Display filtered results
```

### Book Detail Page
```
User clicks book
    ↓
book/[id]/page.tsx (Server Component)
    ├─ Fetch book data from Supabase
    ├─ If user logged in: fetch user_book record
    └─ Render BookDetail + UserBookPanel (conditional)
        ↓
If logged in, user can:
    ├─ Select shelf
    ├─ Rate book
    ├─ Add notes
    └─ Click Save → Upsert to user_books table
```

### Authentication Flow
```
User clicks Sign Up/Login
    ↓
/auth/signup or /auth/login (Client Component)
    ├─ AuthForm component
    ├─ User enters credentials
    └─ Submit form
        ↓
API Call to Supabase Auth
    ├─ signUp() or signInWithPassword()
    ├─ Returns session
    └─ Store in cookies (HTTP-only)
        ↓
Redirect to home page
    ├─ Middleware verifies session
    └─ User is now authenticated
```

### Middleware Flow
```
Every request
    ↓
middleware.ts
    ├─ Extract cookies
    ├─ Call supabase.auth.getUser()
    ├─ Check route protection
    ├─ If protected route + no user
    │   └─ Redirect to /auth/login
    ├─ If auth route + user logged in
    │   └─ Redirect to /
    └─ If valid, refresh session
        └─ Continue to page
```

## Component Hierarchy

```
RootLayout
├─ Navbar
│   ├─ Logo / Search
│   ├─ ThemeToggle
│   └─ Auth Links / User Menu
└─ Page Content
    ├─ Home Page (/)
    │   ├─ BookOfDay (Server)
    │   ├─ FilterPanel
    │   └─ BookGrid
    │       └─ BookCard (multiple)
    │           └─ RatingStars (optional)
    ├─ Book Detail (/book/[id])
    │   ├─ Book Cover
    │   ├─ Book Info
    │   ├─ Tags
    │   └─ UserBookPanel
    │       ├─ Shelf Selector
    │       ├─ RatingStars
    │       └─ Notes Textarea
    ├─ Library Page (/library)
    │   ├─ Stats Cards
    │   ├─ Shelf Tabs
    │   └─ Book List
    └─ Shelves Page (/shelves)
        ├─ Create Shelf Form
        └─ Shelf Cards
```

## State Management

### Server State
- Book catalog (fetched on each request with filters)
- Book details (fetched per book)
- User profile (from Supabase Auth session)

### Client State
- Theme preference (localStorage)
- UI interactions (component useState)
- Form inputs (AuthForm, CreateShelfForm)

### Database State (Supabase)
- User sessions (auth.sessions)
- User profiles (public.profiles)
- User books (public.user_books)
- Custom shelves (public.shelves)
- Shelf books (public.shelf_books)

## Type System

### Core Types (lib/types.ts)

```typescript
Book {
  id, title, author, format, category
  pages, tags, location, summary
  isbn_13, isbn_10, logos_id
  cover_url, amazon_url, asin
  series_name, series_volume
}

UserBook {
  id, user_id, book_id
  shelf ('To Read' | 'Currently Reading' | 'Read' | 'Loaned Out')
  rating (1-5), notes
  date_added, date_finished
}

Shelf {
  id, user_id, name
  description, is_public
}

ShelfBook {
  shelf_id, book_id
}

Profile {
  id, display_name, avatar_url
}
```

## Routing Strategy

### Public Routes (No Auth Required)
- `/` - Catalog page
- `/book/[id]` - Book detail
- `/auth/login` - Login page
- `/auth/signup` - Signup page
- `/auth/callback` - OAuth callback

### Protected Routes (Auth Required)
- `/library` - User's library
- `/shelves` - User's shelves
- `/shelves/[id]` - Shelf details

### Fallback
- `/not-found` - 404 page

Protection is handled by middleware redirecting unauthenticated users to `/auth/login`.

## Database Relationships

```
auth.users (Supabase built-in)
├─ 1 ──→ ∞ profiles (user profile)
├─ 1 ──→ ∞ user_books (tracked books)
└─ 1 ──→ ∞ shelves (custom shelves)

profiles
└─ 1:1 auth.users

books (11,306 records)
├─ ∞ ──→ 1 user_books (who has this book)
├─ ∞ ──→ 1 shelf_books (in which shelves)
└─ (self: series relationship)

user_books
├─ ∞ ──→ 1 auth.users (who tracked it)
└─ ∞ ──→ 1 books (which book)

shelves
├─ 1 ──→ 1 auth.users (owner)
└─ 1 ──→ ∞ shelf_books (contents)

shelf_books
├─ ∞ ──→ 1 shelves (which shelf)
└─ ∞ ──→ 1 books (which books)
```

## Security Model

### Row Level Security (RLS)

**Books Table**: Public read-only
- Anyone can SELECT
- No UPDATE, INSERT, or DELETE

**User Books Table**: User-only
- SELECT: Own records only
- INSERT: Own records only
- UPDATE: Own records only
- DELETE: Own records only

**Shelves Table**: User-only
- SELECT: Own shelves only
- INSERT: Own shelves only
- UPDATE: Own shelves only
- DELETE: Own shelves only

**Shelf Books Table**: Shelf owner only
- Managed through shelves owner check

**Profiles Table**: Public read, user update
- SELECT: Public
- UPDATE: Own profile only

### Authentication Flow
1. User signs up/logs in
2. Supabase creates session with JWT
3. JWT stored in HTTP-only cookie
4. Middleware verifies JWT on each request
5. Server uses JWT for authenticated requests
6. RLS policies enforce data isolation

## Performance Optimizations

### Server-Side
- Static generation where possible
- Efficient database queries with indexes
- Pagination (50 books per page)
- Query result caching

### Client-Side
- Next.js Image component with optimization
- CSS-in-JS with Tailwind (minimal bundle)
- Code splitting by route
- Component-level memoization

### Network
- HTTP/2 server push
- Gzip compression
- CDN caching (via Vercel)
- Efficient JSON payloads

## Error Handling

### Database Errors
- Try-catch blocks in server components
- Graceful fallback UI
- User-friendly error messages

### Authentication Errors
- Invalid credentials → specific error message
- Session expired → redirect to login
- Missing permissions → 404 or error page

### Client Errors
- Form validation before submission
- Toast/alert notifications
- Console error logging

## Scalability Considerations

### Current Architecture
- Supports 10,000+ concurrent users (Supabase Pro)
- 11,306 books with efficient querying
- Per-user RLS policies

### Scaling Strategies
1. **Database**: Upgrade Supabase plan for more connections
2. **Caching**: Add Redis for frequently accessed data
3. **CDN**: Vercel automatic CDN caching
4. **Load Distribution**: Horizontal scaling with Next.js

## Development Workflow

```
Development
    ↓
npm install (dependencies)
npm run dev (start dev server on port 3000)
    ├─ Hot reload on file changes
    └─ Access at http://localhost:3000
    ↓
Testing
    ├─ Manual browser testing
    ├─ TypeScript checking (npm run build)
    └─ ESLint for code quality (npm run lint)
    ↓
Production
    npm run build (optimize & compile)
    npm start (start production server)
        ↓
    Deployed on Vercel / Docker / Node.js
```

## Key Design Decisions

1. **Next.js 14 App Router**
   - Server components for data fetching
   - Client components for interactivity
   - File-based routing

2. **Supabase Backend**
   - Managed PostgreSQL
   - Built-in authentication
   - RLS for data security
   - Real-time subscriptions ready

3. **Tailwind CSS**
   - Utility-first approach
   - Custom theme with indigo/beige
   - Dark mode with CSS class strategy

4. **TypeScript Throughout**
   - Type safety across codebase
   - Better IDE support
   - Fewer runtime errors

5. **Server-First Data Fetching**
   - Security (credentials never exposed)
   - Performance (no client hydration delay)
   - SEO friendly

This architecture provides a robust, scalable, and maintainable foundation for a personal book library application.
