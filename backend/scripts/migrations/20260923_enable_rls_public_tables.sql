ALTER TABLE public.faculties ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.research_labs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.quiz_attempts ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF to_regclass('public.scholars_unassigned') IS NOT NULL THEN
        EXECUTE 'ALTER TABLE public.scholars_unassigned ENABLE ROW LEVEL SECURITY';
    END IF;
END;
$$;
