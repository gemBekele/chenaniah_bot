-- Check for appointments booked by applicants who are NOT approved
-- This query finds appointments where the matching submission status is not 'approved'

-- First, let's see appointments with their matching submission status
-- Note: This matches on phone number (last 8 digits)

SELECT 
    a.id AS appointment_id,
    a.applicant_name,
    a.applicant_phone,
    a.scheduled_date,
    a.scheduled_time,
    a.status AS appointment_status,
    a.created_at AS appointment_created,
    s.id AS submission_id,
    s.name AS submission_name,
    s.phone AS submission_phone,
    s.status AS submission_status,
    s.submitted_at,
    CASE 
        WHEN s.status IS NULL THEN 'NO SUBMISSION FOUND'
        WHEN s.status != 'approved' THEN 'NOT APPROVED'
        ELSE 'APPROVED'
    END AS issue_type
FROM appointments a
LEFT JOIN submissions s ON 
    -- Match on last 8 digits of phone number
    SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        a.applicant_phone, ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''), '.', ''), '/', ''), '\\', ''), '*', ''), '#', ''), -8) = 
    SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        s.phone, ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''), '.', ''), '/', ''), '\\', ''), '*', ''), '#', ''), -8)
WHERE 
    s.status IS NULL  -- No matching submission
    OR s.status != 'approved'  -- Submission exists but not approved
ORDER BY a.created_at DESC;

-- Summary query: Count unapproved appointments
SELECT 
    COUNT(*) AS total_unapproved_appointments,
    SUM(CASE WHEN s.status IS NULL THEN 1 ELSE 0 END) AS no_submission_found,
    SUM(CASE WHEN s.status = 'pending' THEN 1 ELSE 0 END) AS pending_status,
    SUM(CASE WHEN s.status = 'rejected' THEN 1 ELSE 0 END) AS rejected_status,
    SUM(CASE WHEN s.status IS NOT NULL AND s.status NOT IN ('pending', 'rejected', 'approved') THEN 1 ELSE 0 END) AS other_status
FROM appointments a
LEFT JOIN submissions s ON 
    SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        a.applicant_phone, ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''), '.', ''), '/', ''), '\\', ''), '*', ''), '#', ''), -8) = 
    SUBSTR(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(
        s.phone, ' ', ''), '-', ''), '(', ''), ')', ''), '+', ''), '.', ''), '/', ''), '\\', ''), '*', ''), '#', ''), -8)
WHERE 
    s.status IS NULL 
    OR s.status != 'approved';

