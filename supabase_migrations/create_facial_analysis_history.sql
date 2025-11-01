-- Create facial_analysis_history table
CREATE TABLE IF NOT EXISTS facial_analysis_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  skin_type VARCHAR(50),
  detected_concerns TEXT[], -- Array of concern strings
  analysis_result TEXT NOT NULL,
  product_ids INTEGER[], -- Array of product IDs (references to product table)
  recommendation_reasons JSONB, -- Store product_id -> reasons mapping
  input_skin_type VARCHAR(50), -- User-provided skin type (optional)
  input_concerns TEXT[], -- User-provided concerns (optional)
  budget_range JSONB, -- {min?: number, max?: number}
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_facial_analysis_history_user_id ON facial_analysis_history(user_id);
CREATE INDEX IF NOT EXISTS idx_facial_analysis_history_created_at ON facial_analysis_history(created_at DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE facial_analysis_history ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view own history" ON facial_analysis_history;
DROP POLICY IF EXISTS "Users can insert own history" ON facial_analysis_history;
DROP POLICY IF EXISTS "Users can delete own history" ON facial_analysis_history;

-- Policy: Users can only see their own history
CREATE POLICY "Users can view own history" 
  ON facial_analysis_history FOR SELECT 
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own history
CREATE POLICY "Users can insert own history" 
  ON facial_analysis_history FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can delete their own history
CREATE POLICY "Users can delete own history" 
  ON facial_analysis_history FOR DELETE 
  USING (auth.uid() = user_id);

