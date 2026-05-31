-- ============================================================
-- SAFE MIGRATION: Add ON UPDATE CASCADE to all foreign keys
-- that reference mentees(campus_roll) or mentors(campus_roll)
-- ============================================================
-- ⚠️  Run this in a transaction so it's all-or-nothing.
--     If anything fails, nothing changes.
-- ============================================================

BEGIN;

-- ─────────────────────────────────────────
-- 1. mentor_skills → mentors(campus_roll)
--    Was: ON DELETE CASCADE, no ON UPDATE CASCADE
-- ─────────────────────────────────────────
ALTER TABLE mentor_skills
    DROP CONSTRAINT mentor_skills_mentor_roll_fkey;

ALTER TABLE mentor_skills
    ADD CONSTRAINT mentor_skills_mentor_roll_fkey
    FOREIGN KEY (mentor_roll)
    REFERENCES mentors(campus_roll)
    ON DELETE CASCADE
    ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 2. mentee_interests → mentees(campus_roll)
--    Was: ON DELETE CASCADE, no ON UPDATE CASCADE
-- ─────────────────────────────────────────
ALTER TABLE mentee_interests
    DROP CONSTRAINT mentee_interests_mentee_roll_fkey;

ALTER TABLE mentee_interests
    ADD CONSTRAINT mentee_interests_mentee_roll_fkey
    FOREIGN KEY (mentee_roll)
    REFERENCES mentees(campus_roll)
    ON DELETE CASCADE
    ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 3. skill_scores (4 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE skill_scores
    DROP CONSTRAINT skill_scores_mentee_interest_id_fkey,
    DROP CONSTRAINT skill_scores_mentor_skill_id_fkey,
    DROP CONSTRAINT skill_scores_mentee_roll_fkey,
    DROP CONSTRAINT skill_scores_mentor_roll_fkey;

ALTER TABLE skill_scores
    ADD CONSTRAINT skill_scores_mentee_interest_id_fkey
        FOREIGN KEY (mentee_interest_id) REFERENCES mentee_interests(interest_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT skill_scores_mentor_skill_id_fkey
        FOREIGN KEY (mentor_skill_id) REFERENCES mentor_skills(skill_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT skill_scores_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT skill_scores_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 4. personality_scores (2 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE personality_scores
    DROP CONSTRAINT personality_scores_mentee_roll_fkey,
    DROP CONSTRAINT personality_scores_mentor_roll_fkey;

ALTER TABLE personality_scores
    ADD CONSTRAINT personality_scores_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT personality_scores_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 5. aspiration_scores (2 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE aspiration_scores
    DROP CONSTRAINT aspiration_scores_mentee_roll_fkey,
    DROP CONSTRAINT aspiration_scores_mentor_roll_fkey;

ALTER TABLE aspiration_scores
    ADD CONSTRAINT aspiration_scores_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT aspiration_scores_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 6. similarity_scores (4 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE similarity_scores
    DROP CONSTRAINT similarity_scores_mentee_interest_id_fkey,
    DROP CONSTRAINT similarity_scores_mentor_skill_id_fkey,
    DROP CONSTRAINT similarity_scores_mentee_roll_fkey,
    DROP CONSTRAINT similarity_scores_mentor_roll_fkey;

ALTER TABLE similarity_scores
    ADD CONSTRAINT similarity_scores_mentee_interest_id_fkey
        FOREIGN KEY (mentee_interest_id) REFERENCES mentee_interests(interest_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT similarity_scores_mentor_skill_id_fkey
        FOREIGN KEY (mentor_skill_id) REFERENCES mentor_skills(skill_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT similarity_scores_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT similarity_scores_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 7. assignments (4 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE assignments
    DROP CONSTRAINT assignments_mentee_roll_fkey,
    DROP CONSTRAINT assignments_mentor_roll_fkey,
    DROP CONSTRAINT assignments_mentee_interest_id_fkey,
    DROP CONSTRAINT assignments_mentor_skill_id_fkey;

ALTER TABLE assignments
    ADD CONSTRAINT assignments_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT assignments_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT assignments_mentee_interest_id_fkey
        FOREIGN KEY (mentee_interest_id) REFERENCES mentee_interests(interest_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT assignments_mentor_skill_id_fkey
        FOREIGN KEY (mentor_skill_id) REFERENCES mentor_skills(skill_id)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 8. recommendations (4 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE recommendations
    DROP CONSTRAINT recommendations_mentee_roll_fkey,
    DROP CONSTRAINT recommendations_mentor_roll_fkey,
    DROP CONSTRAINT recommendations_mentee_interest_id_fkey,
    DROP CONSTRAINT recommendations_mentor_skill_id_fkey;

ALTER TABLE recommendations
    ADD CONSTRAINT recommendations_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT recommendations_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT recommendations_mentee_interest_id_fkey
        FOREIGN KEY (mentee_interest_id) REFERENCES mentee_interests(interest_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT recommendations_mentor_skill_id_fkey
        FOREIGN KEY (mentor_skill_id) REFERENCES mentor_skills(skill_id)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- 9. generated_emails (2 foreign keys)
-- ─────────────────────────────────────────
ALTER TABLE generated_emails
    DROP CONSTRAINT generated_emails_mentee_roll_fkey,
    DROP CONSTRAINT generated_emails_mentor_roll_fkey;

ALTER TABLE generated_emails
    ADD CONSTRAINT generated_emails_mentee_roll_fkey
        FOREIGN KEY (mentee_roll) REFERENCES mentees(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE,
    ADD CONSTRAINT generated_emails_mentor_roll_fkey
        FOREIGN KEY (mentor_roll) REFERENCES mentors(campus_roll)
        ON DELETE CASCADE ON UPDATE CASCADE;


-- ─────────────────────────────────────────
-- ✅ Commit — all constraints updated atomically
-- ─────────────────────────────────────────
COMMIT;
