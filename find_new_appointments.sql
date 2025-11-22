-- OPTION 1: One-liner command (easiest - automatically extracts IDs from CSV)
-- Run this from the command line (validates IDs are numeric):
-- 
-- IDS=$(tail -n +2 appointments_nov19_2025.csv | awk -F',' '{print $1}' | grep -E '^[0-9]+$' | tr '\n' ',' | sed 's/,$//'); if [ -n "$IDS" ]; then sqlite3 -header -csv vocalist_screening.db "SELECT id, applicant_name, applicant_phone, scheduled_date, CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN '' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 0 THEN '12' || substr(scheduled_time, 3) || ' AM' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) < 12 THEN scheduled_time || ' AM' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 12 THEN scheduled_time || ' PM' ELSE printf('%02d%s PM', CAST(substr(scheduled_time, 1, 2) AS INTEGER) - 12, substr(scheduled_time, 3)) END as scheduled_time, selected_song, additional_song, additional_song_singer FROM appointments WHERE scheduled_date = '2025-11-19' AND id NOT IN ($IDS) ORDER BY CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999 ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER) END ASC;"; else sqlite3 -header -csv vocalist_screening.db "SELECT id, applicant_name, applicant_phone, scheduled_date, CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN '' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 0 THEN '12' || substr(scheduled_time, 3) || ' AM' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) < 12 THEN scheduled_time || ' AM' WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 12 THEN scheduled_time || ' PM' ELSE printf('%02d%s PM', CAST(substr(scheduled_time, 1, 2) AS INTEGER) - 12, substr(scheduled_time, 3)) END as scheduled_time, selected_song, additional_song, additional_song_singer FROM appointments WHERE scheduled_date = '2025-11-19' ORDER BY CASE WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999 ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER) END ASC;"; fi

-- OPTION 2: Manual SQL query (replace IDs with actual values from CSV)
-- First extract IDs: cut -d',' -f1 appointments_nov19_2025.csv | tail -n +2
-- Then use this query:

SELECT 
    id, 
    applicant_name, 
    applicant_phone, 
    scheduled_date,
    CASE 
        WHEN scheduled_time IS NULL OR scheduled_time = '' THEN '' 
        WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 0 THEN '12' || substr(scheduled_time, 3) || ' AM' 
        WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) < 12 THEN scheduled_time || ' AM' 
        WHEN CAST(substr(scheduled_time, 1, 2) AS INTEGER) = 12 THEN scheduled_time || ' PM' 
        ELSE printf('%02d%s PM', CAST(substr(scheduled_time, 1, 2) AS INTEGER) - 12, substr(scheduled_time, 3)) 
    END as scheduled_time,
    selected_song, 
    additional_song, 
    additional_song_singer 
FROM appointments 
WHERE scheduled_date = '2025-11-19' 
    AND id NOT IN (
        -- Replace these with IDs from your CSV file
        -- Example: 1, 2, 3, 4, 5
    )
ORDER BY 
    CASE 
        WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999
        ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER)
    END ASC;

