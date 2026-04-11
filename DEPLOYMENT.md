# Deployment Guide - McLemore Library

## Quick Start for Local Development

1. **Install dependencies:**
```bash
npm install
```

2. **Start development server:**
```bash
npm run dev
```

The app will be available at `http://localhost:3000`

## Supabase Setup Required

Before deploying, ensure your Supabase database has the following schema:

### SQL Setup Script

Run this in the Supabase SQL Editor to create all required tables:

```sql
-- Create profiles table
create table if not exists profiles (
  id uuid primary key references auth.users on delete cascade,
  display_name text,
  avatar_url text,
  created_at timestamp default now()
);

-- Create books table
create table if not exists books (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  author text not null,
  format text,
  category text,
  pages integer,
  tags text[],
  location text,
  summary text,
  isbn_13 text,
  isbn_10 text,
  logos_id text,
  cover_url text,
  amazon_url text,
  asin text,
  series_name text,
  series_volume integer,
  created_at timestamp default now()
);

-- Create user_books table
create table if not exists user_books (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  book_id uuid not null references books on delete cascade,
  shelf text,
  rating integer check (rating >= 1 and rating <= 5),
  notes text,
  date_added timestamp default now(),
  date_finished timestamp,
  created_at timestamp default now(),
  unique(user_id, book_id)
);

-- Create shelves table
create table if not exists shelves (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users on delete cascade,
  name text not null,
  description text,
  is_public boolean default false,
  created_at timestamp default now()
);

-- Create shelf_books table
create table if not exists shelf_books (
  shelf_id uuid not null references shelves on delete cascade,
  book_id uuid not null references books on delete cascade,
  primary key (shelf_id, book_id)
);

-- Create helpful functions for filtering
create or replace function get_distinct_categories()
returns table(category text) as $$
  select distinct category from books where category is not null order by category;
$$ language sql;

create or replace function get_distinct_formats()
returns table(format text) as $$
  select distinct format from books where format is not null order by format;
$$ language sql;

create or replace function get_distinct_locations()
returns table(location text) as $$
  select distinct location from books where location is not null order by location;
$$ language sql;

create or replace function get_distinct_authors()
returns table(author text) as $$
  select distinct author from books where author is not null order by author limit 100;
$$ language sql;

create or replace function get_distinct_tags()
returns table(tag text) as $$
  select distinct unnest(tags) as tag from books where tags is not null order by tag;
$$ language sql;

-- Set up Row Level Security (RLS) policies
alter table profiles enable row level security;
alter table user_books enable row level security;
alter table shelves enable row level security;
alter table shelf_books enable row level security;

-- Profiles policies
create policy "Public profiles are viewable by everyone" on profiles
  for select using (true);

create policy "Users can update own profile" on profiles
  for update using (auth.uid() = id);

-- User books policies
create policy "Users can view their own books" on user_books
  for select using (auth.uid() = user_id);

create policy "Users can insert their own books" on user_books
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own books" on user_books
  for update using (auth.uid() = user_id);

create policy "Users can delete their own books" on user_books
  for delete using (auth.uid() = user_id);

-- Shelves policies
create policy "Users can view their own shelves" on shelves
  for select using (auth.uid() = user_id);

create policy "Users can insert their own shelves" on shelves
  for insert with check (auth.uid() = user_id);

create policy "Users can update their own shelves" on shelves
  for update using (auth.uid() = user_id);

create policy "Users can delete their own shelves" on shelves
  for delete using (auth.uid() = user_id);

-- Shelf books policies
create policy "Users can manage their shelf books" on shelf_books
  for all using (exists (
    select 1 from shelves where shelves.id = shelf_books.shelf_id and shelves.user_id = auth.uid()
  ));

-- Books table is public read-only
alter table books disable row level security;
```

### Import Book Data

If you have 11,306 books to import, use the Supabase data import feature or a bulk insert script.

## Deployment Platforms

### Vercel (Recommended)

1. **Push to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

2. **Connect to Vercel:**
   - Visit vercel.com and import the GitHub repository
   - Add environment variables in Vercel dashboard:
     - `NEXT_PUBLIC_SUPABASE_URL`
     - `NEXT_PUBLIC_SUPABASE_ANON_KEY`

3. **Deploy:**
   - Vercel will automatically build and deploy on every push to main

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

Build and run:
```bash
docker build -t personal-library .
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_SUPABASE_URL=<your-url> \
  -e NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-key> \
  personal-library
```

### Node.js Server

1. **Build for production:**
```bash
npm run build
```

2. **Start production server:**
```bash
npm start
```

3. **Use a process manager (PM2):**
```bash
npm install -g pm2
pm2 start npm --name "personal-library" -- start
pm2 save
pm2 startup
```

## Environment Variables

Ensure these are set in your deployment environment:

```
NEXT_PUBLIC_SUPABASE_URL=https://zfhbetdwmbvuuvwqmnqu.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<your-anon-key>
```

## Security Checklist

- [ ] Supabase RLS policies are properly configured
- [ ] Environment variables are set in production
- [ ] CORS settings are configured in Supabase
- [ ] API rate limiting is enabled
- [ ] Database backups are configured
- [ ] Authentication tokens are secure (HTTP-only cookies)
- [ ] No sensitive data in logs or error messages
- [ ] Image URLs are configured for remote patterns
- [ ] SSL/TLS is enabled on your domain

## Performance Optimization

### Production Build

The production build includes:
- Code splitting
- Image optimization
- CSS minification
- JavaScript minification
- Automatic gzip compression

### Caching Strategy

- Static pages are cached at the CDN level
- User-specific pages use dynamic rendering
- Client-side caching with Next.js

### Database Optimization

- Add indexes on frequently queried columns:

```sql
create index idx_books_category on books(category);
create index idx_books_author on books(author);
create index idx_books_tags on books using gin(tags);
create index idx_user_books_user_id on user_books(user_id);
create index idx_user_books_shelf on user_books(user_id, shelf);
create index idx_shelves_user_id on shelves(user_id);
```

## Monitoring & Maintenance

### Logs

Check Next.js logs:
```bash
npm run build  # Check for build errors
npm start      # Check for runtime errors
```

### Health Checks

Implement health check endpoint (optional):

```typescript
// app/api/health/route.ts
export async function GET() {
  return Response.json({ status: 'ok' })
}
```

### Database Maintenance

- Monitor database size in Supabase dashboard
- Set up automated backups
- Review slow queries
- Monitor connection counts

## Scaling Considerations

- **Caching**: Implement Redis caching for frequently accessed data
- **CDN**: Use a CDN for static assets (Vercel handles this automatically)
- **Database**: Upgrade Supabase plan for higher concurrency
- **Load Testing**: Test with realistic concurrent users before going live

## Rollback Procedure

If issues occur:

1. **Vercel**: Click "Revert" in the Deployments tab
2. **Manual**: Rebuild from previous git commit and redeploy
3. **Database**: Restore from backup if needed

## Support & Troubleshooting

### Common Issues

1. **Build Fails:**
   - Check TypeScript errors: `npm run build`
   - Verify all imports are correct
   - Ensure environment variables are set

2. **Runtime Errors:**
   - Check browser console for client errors
   - Check server logs for API errors
   - Verify Supabase connection

3. **Slow Performance:**
   - Check database query performance
   - Verify image optimization is working
   - Monitor API response times

### Debug Mode

Enable verbose logging:
```bash
DEBUG=* npm run dev
```

## Next Steps

1. Configure your domain
2. Set up SSL certificate
3. Enable analytics
4. Set up monitoring/alerting
5. Configure backups
6. Plan scaling strategy
