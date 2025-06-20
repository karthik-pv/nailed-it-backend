-- Nailed It Database Schema
-- Run these commands in your Supabase SQL editor

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Companies table
CREATE TABLE IF NOT EXISTS companies (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    owner_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(50),
    website VARCHAR(255),
    description TEXT,
    logo_url TEXT,
    
    -- Business information
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'United States',
    
    -- Subscription and payment
    selected_plan VARCHAR(50) DEFAULT 'professional',
    plan_details JSONB DEFAULT '{}',
    payment_status VARCHAR(50) DEFAULT 'pending',
    subscription_status VARCHAR(50) DEFAULT 'trial',
    subscription_start_date TIMESTAMP WITH TIME ZONE,
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    
    -- Document and AI training
    pricing_document_url TEXT,
    ai_training_status VARCHAR(50) DEFAULT 'not_started',
    ai_training_completed_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_payment_status CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    CONSTRAINT valid_subscription_status CHECK (subscription_status IN ('trial', 'active', 'cancelled', 'expired')),
    CONSTRAINT valid_ai_training_status CHECK (ai_training_status IN ('not_started', 'in_progress', 'completed', 'failed')),
    CONSTRAINT valid_plan CHECK (selected_plan IN ('starter', 'professional', 'enterprise'))
);

-- Users table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS users (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE SET NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'owner',
    onboarding_completed BOOLEAN DEFAULT FALSE,
    
    -- User preferences
    preferences JSONB DEFAULT '{}',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT valid_role CHECK (role IN ('owner', 'admin', 'user', 'viewer'))
);

-- Quotes table (for future use)
CREATE TABLE IF NOT EXISTS quotes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_email VARCHAR(255),
    customer_phone VARCHAR(50),
    
    -- Quote details
    quote_number VARCHAR(100) UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    total_amount DECIMAL(10,2) DEFAULT 0.00,
    status VARCHAR(50) DEFAULT 'draft',
    
    -- Quote items stored as JSON
    items JSONB DEFAULT '[]',
    
    -- AI generated content
    ai_generated BOOLEAN DEFAULT FALSE,
    ai_prompt TEXT,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    sent_at TIMESTAMP WITH TIME ZONE,
    
    -- Constraints
    CONSTRAINT valid_quote_status CHECK (status IN ('draft', 'sent', 'accepted', 'rejected', 'expired'))
);

-- Customers table (for future use)
CREATE TABLE IF NOT EXISTS customers (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    zip_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'United States',
    
    -- Customer details
    notes TEXT,
    customer_since DATE DEFAULT CURRENT_DATE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_company_id ON users(company_id);
CREATE INDEX IF NOT EXISTS idx_quotes_company_id ON quotes(company_id);
CREATE INDEX IF NOT EXISTS idx_customers_company_id ON customers(company_id);
CREATE INDEX IF NOT EXISTS idx_companies_email ON companies(email);
CREATE INDEX IF NOT EXISTS idx_companies_payment_status ON companies(payment_status);
CREATE INDEX IF NOT EXISTS idx_quotes_status ON quotes(status);
CREATE INDEX IF NOT EXISTS idx_quotes_quote_number ON quotes(quote_number);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers to automatically update updated_at
CREATE TRIGGER update_companies_updated_at BEFORE UPDATE ON companies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quotes_updated_at BEFORE UPDATE ON quotes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;

-- Companies RLS: Users can only access their own company
CREATE POLICY "Users can view their own company" ON companies
    FOR SELECT USING (
        id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can update their own company" ON companies
    FOR UPDATE USING (
        id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

-- Users RLS: Users can view and update their own record
CREATE POLICY "Users can view their own record" ON users
    FOR SELECT USING (id = auth.uid());

CREATE POLICY "Users can update their own record" ON users
    FOR UPDATE USING (id = auth.uid());

-- Quotes RLS: Users can only access quotes from their company
CREATE POLICY "Users can view company quotes" ON quotes
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can manage company quotes" ON quotes
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

-- Customers RLS: Users can only access customers from their company
CREATE POLICY "Users can view company customers" ON customers
    FOR SELECT USING (
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Users can manage company customers" ON customers
    FOR ALL USING (
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

-- Insert policies for authenticated users
CREATE POLICY "Authenticated users can insert companies" ON companies
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert users" ON users
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users can insert quotes" ON quotes
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

CREATE POLICY "Authenticated users can insert customers" ON customers
    FOR INSERT WITH CHECK (
        auth.role() = 'authenticated' AND
        company_id IN (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    );

-- Create storage bucket for assets (run this in Supabase dashboard or via SQL)
INSERT INTO storage.buckets (id, name, public) 
VALUES ('assets', 'assets', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for assets bucket
CREATE POLICY "Authenticated users can upload assets" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'assets' AND 
        auth.role() = 'authenticated'
    );

CREATE POLICY "Authenticated users can view assets" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'assets' AND 
        auth.role() = 'authenticated'
    );

CREATE POLICY "Users can update their own assets" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'assets' AND 
        auth.role() = 'authenticated' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

CREATE POLICY "Users can delete their own assets" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'assets' AND 
        auth.role() = 'authenticated' AND
        auth.uid()::text = (storage.foldername(name))[1]
    );

COMMENT ON TABLE companies IS 'Stores company information for the Nailed It application';
COMMENT ON TABLE users IS 'Stores user information linked to Supabase auth.users';
COMMENT ON COLUMN companies.logo_url IS 'URL to company logo stored in Supabase storage';
COMMENT ON COLUMN companies.pricing_document_url IS 'URL to pricing document stored in Supabase storage'; 