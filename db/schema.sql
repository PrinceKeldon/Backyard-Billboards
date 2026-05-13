-- Example Netlify Database / PostgreSQL schema for Backyard Billboards
-- Create tables expected by db.py

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Venues table
CREATE TABLE IF NOT EXISTS venues (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    name_lower TEXT NOT NULL,
    address TEXT NOT NULL,
    location TEXT NOT NULL,
    owner_id UUID,
    district TEXT,
    deal TEXT,
    votes INTEGER NOT NULL DEFAULT 0,
    is_hidden_gem BOOLEAN NOT NULL DEFAULT FALSE,
    hidden_gem_description TEXT,
    hidden_gem_tips TEXT,
    has_accurate_location BOOLEAN NOT NULL DEFAULT FALSE,
    opening_hours TEXT,
    happy_hour_price TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    description TEXT,
    place_type TEXT,
    rating DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_venues_name_lower ON venues (name_lower);
CREATE INDEX IF NOT EXISTS idx_venues_owner_id ON venues (owner_id);
CREATE INDEX IF NOT EXISTS idx_venues_district ON venues (district);

-- Deals table
CREATE TABLE IF NOT EXISTS deals (
    id UUID PRIMARY KEY,
    venue_id UUID NOT NULL,
    name TEXT,
    days TEXT,
    start_time TEXT,
    end_time TEXT,
    discount INTEGER NOT NULL DEFAULT 0,
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    FOREIGN KEY (venue_id) REFERENCES venues (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_deals_venue_id ON deals (venue_id);
