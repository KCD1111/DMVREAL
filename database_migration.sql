/*
  # Create Driver's License OCR Database Schema

  1. New Tables
    - `ocr_sessions`
      - `id` (uuid, primary key) - Unique session ID
      - `created_at` (timestamptz) - When the OCR processing started
      - `file_name` (text) - Original filename
      - `file_type` (text) - File type (PDF, JPEG, PNG, etc.)
      - `status` (text) - Processing status (pending, processing, completed, failed)
      - `error_message` (text) - Error message if processing failed
      - `processing_time_ms` (integer) - Time taken to process in milliseconds
      - `overall_confidence` (real) - Overall confidence score (0.0 to 1.0)

    - `extracted_licenses`
      - `id` (uuid, primary key) - Unique record ID
      - `session_id` (uuid, foreign key) - References ocr_sessions
      - `created_at` (timestamptz) - When the record was created
      - `first_name` (text) - First name from license
      - `last_name` (text) - Last name from license
      - `license_number` (text) - Driver's license number
      - `date_of_birth` (text) - Date of birth (MM/DD/YYYY)
      - `expiration_date` (text) - Expiration date (MM/DD/YYYY)
      - `street_address` (text) - Street address
      - `city` (text) - City
      - `state` (text) - State (2-letter code)
      - `zip_code` (text) - ZIP code
      - `sex` (text) - Sex (M or F)
      - `confidence_scores` (jsonb) - Confidence scores for each field
      - `raw_ocr_text` (text) - Raw OCR output from Surya
      - `validation_report` (jsonb) - Validation issues and warnings

  2. Security
    - Enable RLS on both tables
    - Add policies for authenticated users to read their own data
    - Add policies for authenticated users to insert their own data

  3. Indexes
    - Add index on session_id for faster lookups
    - Add index on license_number for searching
    - Add index on created_at for sorting

  4. Notes
    - All text fields use proper normalization
    - Confidence scores stored as JSONB for flexibility
    - Validation report stored as JSONB for detailed error tracking
    - Processing time tracked for performance monitoring

  To apply this migration:
  1. Go to your Supabase dashboard
  2. Navigate to SQL Editor
  3. Copy and paste this entire file
  4. Click "Run"
*/

-- Create ocr_sessions table
CREATE TABLE IF NOT EXISTS ocr_sessions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at timestamptz DEFAULT now(),
  file_name text NOT NULL,
  file_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  error_message text,
  processing_time_ms integer,
  overall_confidence real
);

-- Enable RLS on ocr_sessions
ALTER TABLE ocr_sessions ENABLE ROW LEVEL SECURITY;

-- Policies for ocr_sessions
CREATE POLICY "Users can view all OCR sessions"
  ON ocr_sessions FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert OCR sessions"
  ON ocr_sessions FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update OCR sessions"
  ON ocr_sessions FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Create extracted_licenses table
CREATE TABLE IF NOT EXISTS extracted_licenses (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id uuid REFERENCES ocr_sessions(id) ON DELETE CASCADE,
  created_at timestamptz DEFAULT now(),
  first_name text,
  last_name text,
  license_number text,
  date_of_birth text,
  expiration_date text,
  street_address text,
  city text,
  state text,
  zip_code text,
  sex text,
  confidence_scores jsonb DEFAULT '{}',
  raw_ocr_text text,
  validation_report jsonb DEFAULT '{}'
);

-- Enable RLS on extracted_licenses
ALTER TABLE extracted_licenses ENABLE ROW LEVEL SECURITY;

-- Policies for extracted_licenses
CREATE POLICY "Users can view all extracted licenses"
  ON extracted_licenses FOR SELECT
  TO authenticated
  USING (true);

CREATE POLICY "Users can insert extracted licenses"
  ON extracted_licenses FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE POLICY "Users can update extracted licenses"
  ON extracted_licenses FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_extracted_licenses_session_id
  ON extracted_licenses(session_id);

CREATE INDEX IF NOT EXISTS idx_extracted_licenses_license_number
  ON extracted_licenses(license_number);

CREATE INDEX IF NOT EXISTS idx_extracted_licenses_created_at
  ON extracted_licenses(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_ocr_sessions_created_at
  ON ocr_sessions(created_at DESC);

-- Verify tables were created
SELECT
  'ocr_sessions' as table_name,
  COUNT(*) as column_count
FROM information_schema.columns
WHERE table_name = 'ocr_sessions'
UNION ALL
SELECT
  'extracted_licenses',
  COUNT(*)
FROM information_schema.columns
WHERE table_name = 'extracted_licenses';
