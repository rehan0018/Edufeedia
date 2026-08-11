-- ==============================================================================
-- Edufeedia PostgreSQL + pgvector Production Database Migration
-- Target: PostgreSQL 16+ with pgvector extension enabled
-- Vector Dimension: 384 (Matching Sentence-BERT / all-MiniLM-L6-v2)
-- ==============================================================================

-- 1. Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Add 384-dimensional vector columns to content_items and curriculum_chunks
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'content_items' AND column_name = 'vector_embedding'
    ) THEN
        ALTER TABLE content_items ADD COLUMN vector_embedding vector(384);
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'curriculum_chunks' AND column_name = 'vector_embedding'
    ) THEN
        ALTER TABLE curriculum_chunks ADD COLUMN vector_embedding vector(384);
    END IF;
END $$;

-- 3. Create Approximate Nearest Neighbor (ANN) IVFFlat Indices for Sub-millisecond Cosine Search
-- Note: Recommended after populating initial corpus rows (e.g. lists = 100 for 10k-100k chunks)
CREATE INDEX IF NOT EXISTS idx_content_items_vector_cosine 
ON content_items USING ivfflat (vector_embedding vector_cosine_ops)
WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_curriculum_chunks_vector_cosine 
ON curriculum_chunks USING ivfflat (vector_embedding vector_cosine_ops)
WITH (lists = 100);

-- 4. Sample Fast Vector Search Query (Cosine Distance Operator <=>)
-- SELECT id, title, topic, 1 - (vector_embedding <=> :query_vector) AS cosine_similarity
-- FROM curriculum_chunks
-- WHERE grade_level = :student_grade
-- ORDER BY vector_embedding <=> :query_vector
-- LIMIT 5;
