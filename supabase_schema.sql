-- ==============================================================================
-- CareerCompass-AI 2026: Unified PostgreSQL / Supabase Schema (16 Tables)
-- Single Unified Backend: Career Advisory, Knowledge Graph, RAG, & Admissions Data Retrieval
-- Standardized according to Supabase PostgreSQL Best Practices (2026)
-- ==============================================================================

-- 1. EXTENSIONS
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS "vector";
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'pgvector extension is not available or disabled; using standard vectors.';
END $$;

-- 2. USERS TABLE
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    school_name TEXT,
    grade INT DEFAULT 12,
    target_block TEXT DEFAULT 'A00',
    phone TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);

-- 3. ACADEMIC RECORDS (THPT 3-Year Transcripts & Exam Estimates)
CREATE TABLE IF NOT EXISTS public.academic_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    target_block TEXT NOT NULL DEFAULT 'A00',
    gpa_10 NUMERIC(3, 2),
    gpa_11 NUMERIC(3, 2),
    gpa_12 NUMERIC(3, 2),
    transcript_gpa_overall NUMERIC(3, 2),
    transcript_subject_scores JSONB DEFAULT '{}'::jsonb,
    transcript_block_score NUMERIC(4, 2),
    academic_ranking TEXT DEFAULT 'Giỏi',
    conduct_ranking TEXT DEFAULT 'Tốt',
    estimated_exam_score NUMERIC(4, 2),
    favorite_subjects JSONB DEFAULT '[]'::jsonb,
    certificate_type TEXT,
    certificate_score NUMERIC(4, 2),
    awards TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_academic_user_id ON public.academic_records(user_id);
CREATE INDEX IF NOT EXISTS idx_academic_target_block ON public.academic_records(target_block);

-- 4. SURVEY SUBMISSIONS (Holland RIASEC, SCCT, Gardner, DISC)
CREATE TABLE IF NOT EXISTS public.survey_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    survey_type TEXT NOT NULL,
    student_name TEXT NOT NULL,
    answers JSONB NOT NULL DEFAULT '{}'::jsonb,
    scores JSONB NOT NULL DEFAULT '{}'::jsonb,
    summary_result TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_surveys_user_id ON public.survey_submissions(user_id);
CREATE INDEX IF NOT EXISTS idx_surveys_type ON public.survey_submissions(survey_type);

-- 5. STUDENT CAREER PROFILES (Career Passport)
CREATE TABLE IF NOT EXISTS public.student_career_profiles (
    id TEXT PRIMARY KEY,
    user_id UUID REFERENCES public.users(id) ON DELETE SET NULL,
    student_name TEXT NOT NULL,
    holland_code TEXT NOT NULL,
    holland_scores JSONB NOT NULL,
    scct_results JSONB NOT NULL,
    gardner_intelligences JSONB NOT NULL,
    disc_profile JSONB NOT NULL,
    top_recommended_majors JSONB NOT NULL,
    executive_summary TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_career_profiles_holland ON public.student_career_profiles(holland_code);

-- 6. RECOMMENDATIONS HISTORY
CREATE TABLE IF NOT EXISTS public.recommendations_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    profile_id TEXT,
    dream_tier JSONB NOT NULL DEFAULT '[]'::jsonb,
    target_tier JSONB NOT NULL DEFAULT '[]'::jsonb,
    safety_tier JSONB NOT NULL DEFAULT '[]'::jsonb,
    strategy_notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. USER WISHLISTS / BOOKMARKS
CREATE TABLE IF NOT EXISTS public.user_wishlists (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    university_code TEXT NOT NULL,
    major_code TEXT NOT NULL,
    university_name TEXT,
    major_name TEXT,
    cutoff_score_2025 NUMERIC(4, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, university_code, major_code)
);

CREATE INDEX IF NOT EXISTS idx_wishlists_user ON public.user_wishlists(user_id);

-- 8. CHAT CONVERSATIONS
CREATE TABLE IF NOT EXISTS public.chat_conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL DEFAULT 'Tư vấn Tuyển sinh 2026',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 9. CHAT MESSAGES
CREATE TABLE IF NOT EXISTS public.chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES public.chat_conversations(id) ON DELETE CASCADE,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    thought_process TEXT,
    citations JSONB DEFAULT '[]'::jsonb,
    graph_context JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_messages_conv_id ON public.chat_messages(conversation_id);

-- 10. KNOWLEDGE GRAPH NODES
CREATE TABLE IF NOT EXISTS public.knowledge_graph_nodes (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    name TEXT NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 11. KNOWLEDGE GRAPH EDGES
CREATE TABLE IF NOT EXISTS public.knowledge_graph_edges (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    weight NUMERIC(3, 2) DEFAULT 1.0,
    properties JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON public.knowledge_graph_edges(source_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON public.knowledge_graph_edges(target_id);

-- 12. RAG ADMISSION DOCUMENTS
CREATE TABLE IF NOT EXISTS public.rag_documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_category ON public.rag_documents(category);

-- 13. UNIVERSITIES (Cơ sở đào tạo đại học)
CREATE TABLE IF NOT EXISTS public.universities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    short_name TEXT,
    region TEXT,
    website TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_uni_code ON public.universities(code);

-- 14. MAJORS (Danh mục ngành đào tạo chuẩn)
CREATE TABLE IF NOT EXISTS public.majors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    major_code TEXT NOT NULL,
    major_name TEXT NOT NULL,
    group_name TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(major_code, major_name)
);

-- 15. ADMISSION SCORES (Điểm chuẩn đại học)
CREATE TABLE IF NOT EXISTS public.admission_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    university_id UUID REFERENCES public.universities(id) ON DELETE CASCADE,
    major_id UUID REFERENCES public.majors(id) ON DELETE CASCADE,
    year INT NOT NULL,
    subject_groups TEXT[],
    cutoff_score NUMERIC(5,2),
    note TEXT,
    source TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(university_id, major_id, year)
);

CREATE INDEX IF NOT EXISTS idx_scores_year ON public.admission_scores(year);
CREATE INDEX IF NOT EXISTS idx_scores_cutoff ON public.admission_scores(cutoff_score);
CREATE INDEX IF NOT EXISTS idx_scores_groups ON public.admission_scores USING GIN(subject_groups);

-- 16. EXAM SCORES (Điểm thi THPT quốc gia - Ẩn danh theo Nghị định 13/2023)
CREATE TABLE IF NOT EXISTS public.exam_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    exam_number TEXT NOT NULL,
    year INT NOT NULL,
    province_code TEXT,
    math NUMERIC(4,2),
    literature NUMERIC(4,2),
    physics NUMERIC(4,2),
    chemistry NUMERIC(4,2),
    biology NUMERIC(4,2),
    history NUMERIC(4,2),
    geography NUMERIC(4,2),
    civic_education NUMERIC(4,2),
    foreign_language NUMERIC(4,2),
    language_code TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- 17. CRAWL LOGS
CREATE TABLE IF NOT EXISTS public.crawl_logs (
    id TEXT PRIMARY KEY,
    source_name TEXT NOT NULL,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL,
    records_count INT DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ DEFAULT now(),
    finished_at TIMESTAMPTZ
);

-- 18. ENABLE ROW LEVEL SECURITY
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.academic_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.survey_submissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_career_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.recommendations_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_wishlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_graph_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.knowledge_graph_edges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rag_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.universities ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.majors ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.admission_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.exam_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.crawl_logs ENABLE ROW LEVEL SECURITY;

-- 19. POLICIES: PUBLIC ACCESS FOR API CLIENT
DO $$
DECLARE
    tbl text;
    tables text[] := ARRAY[
        'users', 'academic_records', 'survey_submissions', 'student_career_profiles',
        'recommendations_history', 'user_wishlists', 'chat_conversations', 'chat_messages',
        'knowledge_graph_nodes', 'knowledge_graph_edges', 'rag_documents',
        'universities', 'majors', 'admission_scores', 'exam_scores', 'crawl_logs'
    ];
BEGIN
    FOREACH tbl IN ARRAY tables LOOP
        EXECUTE format('DROP POLICY IF EXISTS "Public access for %I" ON public.%I', tbl, tbl);
        EXECUTE format('CREATE POLICY "Public access for %I" ON public.%I FOR ALL TO public USING (true) WITH CHECK (true)', tbl, tbl);
    END LOOP;
END $$;

-- 20. EXPLICIT GRANTS
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated, service_role;
