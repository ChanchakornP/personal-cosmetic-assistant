-- Create skincare_routine table
CREATE TABLE IF NOT EXISTS skincare_routine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  date DATE NOT NULL,
  morning_products INTEGER[], -- Array of product IDs
  evening_products INTEGER[], -- Array of product IDs
  skin_condition_rating INTEGER, -- Overall rating 1-5
  skin_conditions JSONB, -- Detailed ratings: {dryness: 1-5, irritation: 1-5, oiliness: 1-5, etc.}
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  -- Prevent duplicate entries for same user and date
  UNIQUE(user_id, date)
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_skincare_routine_user_id ON skincare_routine(user_id);
CREATE INDEX IF NOT EXISTS idx_skincare_routine_date ON skincare_routine(date DESC);
CREATE INDEX IF NOT EXISTS idx_skincare_routine_user_date ON skincare_routine(user_id, date DESC);

-- Enable RLS (Row Level Security)
ALTER TABLE skincare_routine ENABLE ROW LEVEL SECURITY;

-- Drop existing policies if they exist (for idempotency)
DROP POLICY IF EXISTS "Users can view own routines" ON skincare_routine;
DROP POLICY IF EXISTS "Users can insert own routines" ON skincare_routine;
DROP POLICY IF EXISTS "Users can update own routines" ON skincare_routine;
DROP POLICY IF EXISTS "Users can delete own routines" ON skincare_routine;

-- Policy: Users can only see their own routines
CREATE POLICY "Users can view own routines" 
  ON skincare_routine FOR SELECT 
  USING (auth.uid() = user_id);

-- Policy: Users can insert their own routines
CREATE POLICY "Users can insert own routines" 
  ON skincare_routine FOR INSERT 
  WITH CHECK (auth.uid() = user_id);

-- Policy: Users can update their own routines
CREATE POLICY "Users can update own routines" 
  ON skincare_routine FOR UPDATE 
  USING (auth.uid() = user_id);

-- Policy: Users can delete their own routines
CREATE POLICY "Users can delete own routines" 
  ON skincare_routine FOR DELETE 
  USING (auth.uid() = user_id);

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_skincare_routine_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create a trigger to update updated_at on routine updates
CREATE TRIGGER on_skincare_routine_updated
  BEFORE UPDATE ON skincare_routine
  FOR EACH ROW EXECUTE FUNCTION update_skincare_routine_updated_at();

