# 🚀 Storage Setup Guide for File Uploads

Since storage policies cannot be configured via SQL (requires superuser permissions), you need to set them up through the Supabase Dashboard.

## Step 1: Run Database Policies

First, run the SQL file for database policies:

1. Go to your **Supabase Dashboard**
2. Navigate to **SQL Editor**
3. Copy and paste the content from `backend/sql/03_setup_rls_policies.sql`
4. Click **Run** to execute the database policies

## Step 2: Configure Storage Bucket

### Create the Bucket:

1. Go to **Storage** in your Supabase Dashboard
2. Click **Create a new bucket**
3. Set the following:
   - **Name**: `company-assets`
   - **Public bucket**: ✅ **Enable** (check this box)
   - **File size limit**: `52428800` (50MB)
   - **Allowed MIME types**: Leave empty for now (we'll handle validation in code)

### Configure Bucket Settings:

1. Click on the `company-assets` bucket
2. Go to **Configuration** tab
3. Make sure **Public** is enabled
4. Set **File size limit** to `52428800` bytes (50MB)

## Step 3: Configure Storage Policies

### Method 1: Through Dashboard UI (Recommended)

1. Go to **Storage** → **Policies**
2. You'll see a section for **Objects in company-assets**
3. Click **New Policy** for each of the following:

#### Policy 1: Allow Anyone to Upload

- **Policy Name**: `Allow anyone to upload`
- **Allowed operation**: `INSERT`
- **Target roles**: `public` (or leave empty for all roles)
- **Policy definition**:

```sql
bucket_id = 'company-assets'
```

#### Policy 2: Allow Anyone to View

- **Policy Name**: `Allow anyone to view`
- **Allowed operation**: `SELECT`
- **Target roles**: `public` (or leave empty for all roles)
- **Policy definition**:

```sql
bucket_id = 'company-assets'
```

#### Policy 3: Allow Anyone to Update

- **Policy Name**: `Allow anyone to update`
- **Allowed operation**: `UPDATE`
- **Target roles**: `public` (or leave empty for all roles)
- **Policy definition**:

```sql
bucket_id = 'company-assets'
```

#### Policy 4: Allow Anyone to Delete

- **Policy Name**: `Allow anyone to delete`
- **Allowed operation**: `DELETE`
- **Target roles**: `public` (or leave empty for all roles)
- **Policy definition**:

```sql
bucket_id = 'company-assets'
```

### Method 2: Quick Setup (Alternative)

If you want to disable RLS completely for the storage bucket (less secure but simpler):

1. Go to **Storage** → **Policies**
2. Find the **Objects in company-assets** section
3. Click **Disable RLS** (if available)

This will allow unrestricted access to the bucket.

## Step 4: Verify Setup

### Test the Configuration:

1. Try uploading a file through your application
2. Check if the file appears in the Storage bucket
3. Verify you can access the file URL

### Troubleshooting:

If you still get 403 errors:

1. **Check bucket exists**: Verify `company-assets` bucket exists
2. **Check bucket is public**: Make sure the bucket has public access enabled
3. **Check policies**: Ensure all 4 policies are created and active
4. **Check file size**: Make sure your file is under 50MB
5. **Check CORS**: Verify CORS is properly configured in your backend

## Step 5: Alternative - Disable Storage RLS Completely

If policies are still causing issues, you can disable RLS entirely for storage:

1. Go to **SQL Editor** in Supabase
2. Run this SQL:

```sql
ALTER TABLE storage.objects DISABLE ROW LEVEL SECURITY;
```

⚠️ **Warning**: This makes your storage completely open. Only use for development/testing.

## Expected Result

After completing these steps:

- ✅ Anyone can upload files to `company-assets` bucket
- ✅ Files are publicly accessible
- ✅ No 403 unauthorized errors
- ✅ File uploads work from your application

## File Upload Test

You can test file uploads using curl:

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@/path/to/your/file.jpg" \
  http://localhost:5000/files/upload/logo
```

The upload should return a success response with the file URL.
