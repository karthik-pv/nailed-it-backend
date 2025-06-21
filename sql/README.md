# Database Setup Instructions

This folder contains SQL scripts to set up the NailedIt Quote AI database with proper tables, triggers, functions, and Row Level Security (RLS) policies.

## Prerequisites

1. Make sure you have access to your Supabase project dashboard
2. Ensure RLS is enabled on your Supabase project (it should be by default)
3. Have your Supabase project URL and service role key ready

## Setup Order

**IMPORTANT**: Run these SQL files in the exact order specified below. Do not skip any files or run them out of order.

### Step 1: Create Tables and Indexes

```sql
-- Run in Supabase SQL Editor
-- File: 01_setup_tables.sql
```

This creates:

- `companies` table
- `users` table (extends auth.users)
- Necessary indexes
- Storage bucket for file uploads

### Step 2: Create Triggers and Functions

```sql
-- Run in Supabase SQL Editor
-- File: 02_setup_triggers.sql
```

This creates:

- `update_updated_at_column()` function
- Automatic timestamp update triggers
- `handle_new_user()` function for user registration
- User role management functions

### Step 3: Setup Row Level Security Policies

```sql
-- Run in Supabase SQL Editor
-- File: 03_setup_rls_policies.sql
```

This creates:

- RLS policies for users table
- RLS policies for companies table
- Storage bucket policies
- Proper access control for all operations

## Running the Scripts

1. Open your Supabase dashboard
2. Go to the SQL Editor
3. Copy and paste each file's content in order
4. Run each script one by one
5. Verify no errors occurred before proceeding to the next file

## Verification

After running all scripts, verify the setup by checking:

1. **Tables**: Ensure `users` and `companies` tables are created
2. **Indexes**: Check that all indexes are properly created
3. **Triggers**: Verify triggers are active
4. **RLS**: Confirm RLS is enabled on both tables
5. **Storage**: Ensure `company-assets` bucket exists

## Troubleshooting

If you encounter errors:

1. **Permission errors**: Make sure you're using the service role key
2. **Table exists errors**: Drop existing tables if you're re-running setup
3. **Function errors**: Check for syntax issues in function definitions
4. **RLS errors**: Ensure RLS is enabled before creating policies

## Post-Setup

After successful database setup:

1. Test user registration flow
2. Test company creation
3. Test file upload to storage bucket
4. Verify RLS policies are working correctly

## Important Notes

- **Never disable RLS** on production databases
- **Always backup** your database before running setup scripts
- **Test thoroughly** in development before applying to production
- **Keep these scripts** for future reference and re-deployment
