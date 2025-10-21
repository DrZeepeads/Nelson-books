-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Nelson Textbook of Pediatrics table
CREATE TABLE IF NOT EXISTS nelson_textbook (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  chapter VARCHAR(255) NOT NULL,
  section VARCHAR(500) NOT NULL,
  page_number INTEGER,
  content TEXT NOT NULL,
  embedding vector(1536), -- OpenAI embedding dimension
  keywords TEXT[],
  medical_category VARCHAR(100),
  age_group VARCHAR(50),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pediatric Medical Resources table
CREATE TABLE IF NOT EXISTS pediatric_medical_resources (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title VARCHAR(500) NOT NULL,
  content TEXT NOT NULL,
  resource_type VARCHAR(50) CHECK (resource_type IN ('protocol', 'dosage', 'guideline', 'reference')),
  category VARCHAR(100) NOT NULL,
  age_range VARCHAR(50),
  weight_range VARCHAR(50),
  embedding vector(1536),
  source VARCHAR(255),
  last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Sessions table
CREATE TABLE IF NOT EXISTS chat_sessions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID, -- Optional for anonymous sessions
  title VARCHAR(500) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Chat Messages table
CREATE TABLE IF NOT EXISTS chat_messages (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
  role VARCHAR(20) CHECK (role IN ('user', 'assistant')) NOT NULL,
  content TEXT NOT NULL,
  citations TEXT[],
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_nelson_textbook_embedding ON nelson_textbook USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_pediatric_resources_embedding ON pediatric_medical_resources USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_nelson_textbook_category ON nelson_textbook(medical_category);
CREATE INDEX IF NOT EXISTS idx_nelson_textbook_keywords ON nelson_textbook USING GIN(keywords);
CREATE INDEX IF NOT EXISTS idx_pediatric_resources_category ON pediatric_medical_resources(category);
CREATE INDEX IF NOT EXISTS idx_pediatric_resources_type ON pediatric_medical_resources(resource_type);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated ON chat_sessions(updated_at DESC);

-- Function to search similar documents using embeddings
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding vector(1536),
  match_table TEXT,
  match_count int DEFAULT 5,
  similarity_threshold float DEFAULT 0.7
)
RETURNS TABLE (
  id UUID,
  content TEXT,
  similarity FLOAT,
  metadata JSONB
)
LANGUAGE SQL STABLE
AS $$
  SELECT 
    CASE 
      WHEN match_table = 'nelson_textbook' THEN nt.id
      ELSE pmr.id
    END as id,
    CASE 
      WHEN match_table = 'nelson_textbook' THEN nt.content
      ELSE pmr.content
    END as content,
    CASE 
      WHEN match_table = 'nelson_textbook' THEN 1 - (nt.embedding <=> query_embedding)
      ELSE 1 - (pmr.embedding <=> query_embedding)
    END as similarity,
    CASE 
      WHEN match_table = 'nelson_textbook' THEN 
        jsonb_build_object(
          'chapter', nt.chapter,
          'section', nt.section,
          'page_number', nt.page_number,
          'category', nt.medical_category,
          'age_group', nt.age_group,
          'source', 'Nelson Textbook of Pediatrics'
        )
      ELSE 
        jsonb_build_object(
          'title', pmr.title,
          'resource_type', pmr.resource_type,
          'category', pmr.category,
          'age_range', pmr.age_range,
          'weight_range', pmr.weight_range,
          'source', pmr.source
        )
    END as metadata
  FROM 
    CASE 
      WHEN match_table = 'nelson_textbook' THEN nelson_textbook nt
      ELSE pediatric_medical_resources pmr
    END
  WHERE 
    CASE 
      WHEN match_table = 'nelson_textbook' THEN 1 - (nt.embedding <=> query_embedding)
      ELSE 1 - (pmr.embedding <=> query_embedding)
    END > similarity_threshold
  ORDER BY 
    CASE 
      WHEN match_table = 'nelson_textbook' THEN nt.embedding <=> query_embedding
      ELSE pmr.embedding <=> query_embedding
    END
  LIMIT match_count;
$$;

-- Sample data for testing
INSERT INTO nelson_textbook (chapter, section, page_number, content, keywords, medical_category, age_group) VALUES 
(
  'Chapter 12: Infectious Diseases',
  'Otitis Media',
  234,
  'Acute otitis media (AOM) is one of the most common infections in children. First-line treatment typically includes amoxicillin 80-90 mg/kg/day divided twice daily for 10 days in children under 2 years or with severe symptoms. For children 2-5 years with mild symptoms, watchful waiting may be appropriate. Second-line antibiotics include amoxicillin-clavulanate or azithromycin.',
  ARRAY['otitis media', 'ear infection', 'amoxicillin', 'antibiotic', 'pediatric dosing'],
  'Infectious Diseases',
  'Pediatric'
);

