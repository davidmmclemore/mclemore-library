-- McLemore Personal Library — Supabase Schema
-- Run this entire file in the Supabase SQL Editor
-- (supabase.com → your project → SQL Editor → New query → paste → Run)

-- ─────────────────────────────────────────────
-- 0. Clean up old public tables (safe to run even if they don't exist)
-- ─────────────────────────────────────────────
drop table if exists public.shelf_books  cascade;
drop table if exists public.shelves      cascade;
drop table if exists public.user_books   cascade;
drop table if exists public.profiles     cascade;
drop table if exists public.books        cascade;

-- ─────────────────────────────────────────────
-- 1. Create custom schema
-- ─────────────────────────────────────────────
create schema if not exists mclemorepersonallibrary;

-- Extensions (needed for uuid_generate_v4)
create extension if not exists "uuid-ossp" schema extensions;

-- ─────────────────────────────────────────────
-- 2. BOOKS  (public catalog, ~11,304 rows)
-- ─────────────────────────────────────────────
create table if not exists mclemorepersonallibrary.books (
  id            text primary key,          -- BOOK-XXXX
  title         text not null,
  author        text,
  format        text,                      -- Print | eBook | Logos Book
  category      text,
  pages         integer,
  tags          jsonb   default '[]',      -- ["tag1","tag2",...]
  location      text,
  summary       text,
  isbn_13       text,
  isbn_10       text,
  logos_id      text,
  cover_url     text,
  amazon_url    text,
  asin          text,
  series_name   text,
  series_volume numeric,
  created_at    timestamptz default now()
);

create index if not exists books_author_idx    on mclemorepersonallibrary.books(author);
create index if not exists books_category_idx  on mclemorepersonallibrary.books(category);
create index if not exists books_format_idx    on mclemorepersonallibrary.books(format);
create index if not exists books_location_idx  on mclemorepersonallibrary.books(location);
create index if not exists books_series_idx    on mclemorepersonallibrary.books(series_name);
create index if not exists books_tags_idx      on mclemorepersonallibrary.books using gin(tags);
create index if not exists books_fts_idx
  on mclemorepersonallibrary.books
  using gin(to_tsvector('english', coalesce(title,'') || ' ' || coalesce(author,'')));

-- ─────────────────────────────────────────────
-- 3. PROFILES  (one per auth user, auto-created)
-- ─────────────────────────────────────────────
create table if not exists mclemorepersonallibrary.profiles (
  id           uuid primary key references auth.users(id) on delete cascade,
  display_name text,
  avatar_url   text,
  created_at   timestamptz default now(),
  updated_at   timestamptz default now()
);

-- ─────────────────────────────────────────────
-- 4. USER_BOOKS  (per-user state for each book)
-- ─────────────────────────────────────────────
create table if not exists mclemorepersonallibrary.user_books (
  id            uuid primary key default extensions.uuid_generate_v4(),
  user_id       uuid not null references mclemorepersonallibrary.profiles(id) on delete cascade,
  book_id       text not null references mclemorepersonallibrary.books(id) on delete cascade,
  shelf         text check (shelf in ('To Read', 'Currently Reading', 'Read', 'Loaned Out')),
  rating        integer check (rating >= 1 and rating <= 5),
  notes         text,
  date_added    timestamptz default now(),
  date_finished date,
  unique(user_id, book_id)
);

create index if not exists user_books_user_idx  on mclemorepersonallibrary.user_books(user_id);
create index if not exists user_books_book_idx  on mclemorepersonallibrary.user_books(book_id);
create index if not exists user_books_shelf_idx on mclemorepersonallibrary.user_books(shelf);

-- ─────────────────────────────────────────────
-- 5. SHELVES  (custom user-created collections)
-- ─────────────────────────────────────────────
create table if not exists mclemorepersonallibrary.shelves (
  id          uuid primary key default extensions.uuid_generate_v4(),
  user_id     uuid not null references mclemorepersonallibrary.profiles(id) on delete cascade,
  name        text not null,
  description text,
  is_public   boolean default false,
  created_at  timestamptz default now(),
  updated_at  timestamptz default now()
);

create index if not exists shelves_user_idx on mclemorepersonallibrary.shelves(user_id);

-- ─────────────────────────────────────────────
-- 6. SHELF_BOOKS  (books inside a custom shelf)
-- ─────────────────────────────────────────────
create table if not exists mclemorepersonallibrary.shelf_books (
  id        uuid primary key default extensions.uuid_generate_v4(),
  shelf_id  uuid not null references mclemorepersonallibrary.shelves(id) on delete cascade,
  book_id   text not null references mclemorepersonallibrary.books(id) on delete cascade,
  added_at  timestamptz default now(),
  unique(shelf_id, book_id)
);

create index if not exists shelf_books_shelf_idx on mclemorepersonallibrary.shelf_books(shelf_id);
create index if not exists shelf_books_book_idx  on mclemorepersonallibrary.shelf_books(book_id);

-- ─────────────────────────────────────────────
-- 7. ROW LEVEL SECURITY
-- ─────────────────────────────────────────────

-- Books: publicly readable
alter table mclemorepersonallibrary.books enable row level security;
create policy "Books are publicly readable"
  on mclemorepersonallibrary.books for select using (true);

-- Profiles
alter table mclemorepersonallibrary.profiles enable row level security;
create policy "Profiles are publicly readable"
  on mclemorepersonallibrary.profiles for select using (true);
create policy "Users can insert own profile"
  on mclemorepersonallibrary.profiles for insert with check (auth.uid() = id);
create policy "Users can update own profile"
  on mclemorepersonallibrary.profiles for update using (auth.uid() = id);

-- User books
alter table mclemorepersonallibrary.user_books enable row level security;
create policy "Users can view own user_books"
  on mclemorepersonallibrary.user_books for select using (auth.uid() = user_id);
create policy "Users can insert own user_books"
  on mclemorepersonallibrary.user_books for insert with check (auth.uid() = user_id);
create policy "Users can update own user_books"
  on mclemorepersonallibrary.user_books for update using (auth.uid() = user_id);
create policy "Users can delete own user_books"
  on mclemorepersonallibrary.user_books for delete using (auth.uid() = user_id);

-- Shelves
alter table mclemorepersonallibrary.shelves enable row level security;
create policy "Users can view own or public shelves"
  on mclemorepersonallibrary.shelves for select using (auth.uid() = user_id or is_public = true);
create policy "Users can insert own shelves"
  on mclemorepersonallibrary.shelves for insert with check (auth.uid() = user_id);
create policy "Users can update own shelves"
  on mclemorepersonallibrary.shelves for update using (auth.uid() = user_id);
create policy "Users can delete own shelves"
  on mclemorepersonallibrary.shelves for delete using (auth.uid() = user_id);

-- Shelf books
alter table mclemorepersonallibrary.shelf_books enable row level security;
create policy "Shelf books visible with shelf"
  on mclemorepersonallibrary.shelf_books for select using (
    exists (
      select 1 from mclemorepersonallibrary.shelves
      where shelves.id = shelf_id
        and (shelves.user_id = auth.uid() or shelves.is_public = true)
    )
  );
create policy "Users can add to own shelves"
  on mclemorepersonallibrary.shelf_books for insert with check (
    exists (
      select 1 from mclemorepersonallibrary.shelves
      where shelves.id = shelf_id and shelves.user_id = auth.uid()
    )
  );
create policy "Users can remove from own shelves"
  on mclemorepersonallibrary.shelf_books for delete using (
    exists (
      select 1 from mclemorepersonallibrary.shelves
      where shelves.id = shelf_id and shelves.user_id = auth.uid()
    )
  );

-- ─────────────────────────────────────────────
-- 8. Auto-create profile on signup
-- ─────────────────────────────────────────────
create or replace function mclemorepersonallibrary.handle_new_user()
returns trigger as $$
begin
  insert into mclemorepersonallibrary.profiles (id, display_name)
  values (
    new.id,
    coalesce(new.raw_user_meta_data->>'full_name', new.email)
  );
  return new;
end;
$$ language plpgsql security definer;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure mclemorepersonallibrary.handle_new_user();
