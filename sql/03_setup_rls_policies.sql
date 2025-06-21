-- Database Setup for NailedIt Quote AI
-- Step 3: Row Level Security (RLS) Policies

-- Enable RLS on tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to avoid conflicts
DROP POLICY IF EXISTS "Users can view their own profile" ON users;
DROP POLICY IF EXISTS "Users can update their own profile" ON users;
DROP POLICY IF EXISTS "Users can view company members" ON users;
DROP POLICY IF EXISTS "Users can insert their own profile" ON users;
DROP POLICY IF EXISTS "Users can view their company" ON companies;
DROP POLICY IF EXISTS "Users can update their company" ON companies;
DROP POLICY IF EXISTS "Authenticated users can create companies" ON companies;
DROP POLICY IF EXISTS "Users can delete their company" ON companies;
DROP POLICY IF EXISTS "Authenticated users can view companies" ON companies;
DROP POLICY IF EXISTS "Authenticated users can update companies" ON companies;
DROP POLICY IF EXISTS "Authenticated users can delete companies" ON companies;

-- Users table policies (simplified to avoid recursion)
-- Users can read their own profile
CREATE POLICY "Users can view their own profile" ON users
    FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile  
CREATE POLICY "Users can update their own profile" ON users
    FOR UPDATE USING (auth.uid() = id);

-- Allow authenticated users to insert their own user record
CREATE POLICY "Users can insert their own profile" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Companies table policies
-- Authenticated users can view any company (simplified for now)
CREATE POLICY "Authenticated users can view companies" ON companies
    FOR SELECT USING (auth.role() = 'authenticated');

-- Authenticated users can update companies (we'll add business logic checks in the app)
CREATE POLICY "Authenticated users can update companies" ON companies
    FOR UPDATE USING (auth.role() = 'authenticated');

-- Authenticated users can create companies
CREATE POLICY "Authenticated users can create companies" ON companies
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Authenticated users can delete companies (we'll add business logic checks in the app)
CREATE POLICY "Authenticated users can delete companies" ON companies
    FOR DELETE USING (auth.role() = 'authenticated');

-- Verify the database policies were created
SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
FROM pg_policies 
WHERE tablename IN ('users', 'companies'); 