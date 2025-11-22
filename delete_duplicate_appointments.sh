#!/bin/bash
# Script to delete all duplicate appointments and free up time slots
# Keeps the earliest appointment for each phone number

DB_PATH="${DATABASE_PATH:-./vocalist_screening.db}"

if [ ! -f "$DB_PATH" ]; then
    echo "Error: Database file not found at $DB_PATH"
    exit 1
fi

echo "=== Checking for duplicate appointments ==="
sqlite3 "$DB_PATH" << 'SQL'
-- Show what duplicates exist before deletion
SELECT 'Current duplicates:' as info;
SELECT 
  applicant_phone,
  applicant_name,
  COUNT(*) as count,
  GROUP_CONCAT(id || ':' || scheduled_date || ' ' || scheduled_time, ', ') as appointments
FROM appointments
WHERE status = 'scheduled'
GROUP BY applicant_phone
HAVING COUNT(*) > 1;
SQL

echo ""
echo "=== Deleting duplicates and freeing time slots ==="

sqlite3 "$DB_PATH" << 'SQL'
-- Step 1: Create a temporary table with appointments to keep (earliest for each phone)
CREATE TEMP TABLE appointments_to_keep AS
SELECT MIN(id) as id
FROM appointments
WHERE status = 'scheduled'
GROUP BY applicant_phone;

-- Step 2: Store appointments that will be deleted (for reporting)
CREATE TEMP TABLE appointments_to_delete AS
SELECT 
  a.id,
  a.applicant_phone,
  a.applicant_name,
  a.scheduled_date,
  a.scheduled_time
FROM appointments a
WHERE a.status = 'scheduled'
  AND a.id NOT IN (SELECT id FROM appointments_to_keep)
  AND a.applicant_phone IN (
    SELECT applicant_phone 
    FROM appointments 
    WHERE status = 'scheduled' 
    GROUP BY applicant_phone 
    HAVING COUNT(*) > 1
  );

-- Step 3: Get the time slots that need to be freed
CREATE TEMP TABLE slots_to_free AS
SELECT DISTINCT ts.id as slot_id, a.scheduled_date, a.scheduled_time
FROM time_slots ts
INNER JOIN appointments_to_delete a ON ts.date = a.scheduled_date AND ts.time = a.scheduled_time;

-- Step 4: Show what will be deleted
SELECT 'Appointments to be deleted:' as info;
SELECT 
  applicant_phone,
  applicant_name,
  COUNT(*) as count,
  GROUP_CONCAT(id || ':' || scheduled_date || ' ' || scheduled_time, ', ') as appointments
FROM appointments_to_delete
GROUP BY applicant_phone, applicant_name;

-- Step 5: Free up the time slots
UPDATE time_slots 
SET available = 1, updated_at = CURRENT_TIMESTAMP
WHERE id IN (SELECT slot_id FROM slots_to_free);

SELECT 'Freed time slots:' as info;
SELECT COUNT(*) as freed_count FROM slots_to_free;

-- Step 6: Delete duplicate appointments
DELETE FROM appointments
WHERE id IN (SELECT id FROM appointments_to_delete);

SELECT 'Deleted appointments:' as info;
SELECT COUNT(*) as deleted_count FROM appointments_to_delete;

-- Step 7: Verify no duplicates remain
SELECT 'Verification - Remaining duplicates:' as info;
SELECT applicant_phone, COUNT(*) as count 
FROM appointments 
WHERE status = 'scheduled' 
GROUP BY applicant_phone 
HAVING COUNT(*) > 1;

-- Cleanup temp tables
DROP TABLE IF EXISTS appointments_to_keep;
DROP TABLE IF EXISTS appointments_to_delete;
DROP TABLE IF EXISTS slots_to_free;
SQL

echo ""
echo "=== Done ==="

