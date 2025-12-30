/*
  # Add Anonymous Access Policies for DMV OCR

  1. Changes
    - Add policies to allow anonymous (anon) users to access ocr_sessions table
    - Add policies to allow anonymous (anon) users to access extracted_licenses table

  2. Security Notes
    - This allows public access to the OCR system
    - In a production environment, you may want to add authentication
    - For now, this enables the application to work with the anon key

  3. Policies Added
    - Anon users can view all OCR sessions
    - Anon users can insert OCR sessions
    - Anon users can update OCR sessions
    - Anon users can view all extracted licenses
    - Anon users can insert extracted licenses
    - Anon users can update extracted licenses
*/

-- Drop existing anon policies if they exist and recreate them
DO $$ 
BEGIN
  DROP POLICY IF EXISTS "Anon users can view all OCR sessions" ON ocr_sessions;
  DROP POLICY IF EXISTS "Anon users can insert OCR sessions" ON ocr_sessions;
  DROP POLICY IF EXISTS "Anon users can update OCR sessions" ON ocr_sessions;
  DROP POLICY IF EXISTS "Anon users can view all extracted licenses" ON extracted_licenses;
  DROP POLICY IF EXISTS "Anon users can insert extracted licenses" ON extracted_licenses;
  DROP POLICY IF EXISTS "Anon users can update extracted licenses" ON extracted_licenses;
END $$;

-- Add anon policies for ocr_sessions
CREATE POLICY "Anon users can view all OCR sessions"
  ON ocr_sessions FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Anon users can insert OCR sessions"
  ON ocr_sessions FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anon users can update OCR sessions"
  ON ocr_sessions FOR UPDATE
  TO anon
  USING (true)
  WITH CHECK (true);

-- Add anon policies for extracted_licenses
CREATE POLICY "Anon users can view all extracted licenses"
  ON extracted_licenses FOR SELECT
  TO anon
  USING (true);

CREATE POLICY "Anon users can insert extracted licenses"
  ON extracted_licenses FOR INSERT
  TO anon
  WITH CHECK (true);

CREATE POLICY "Anon users can update extracted licenses"
  ON extracted_licenses FOR UPDATE
  TO anon
  USING (true)
  WITH CHECK (true);
