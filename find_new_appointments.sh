#!/bin/bash

# Script to find appointments for 2025-11-19 that aren't in the CSV file

CSV_FILE="appointments_nov19_2025.csv"
DB_FILE="vocalist_screening.db"

# Extract IDs from CSV (skip header, get first column, validate numeric)
if [ -f "$CSV_FILE" ]; then
    # Get IDs from CSV, excluding header, filter to only numeric values
    # Using awk to handle CSV properly and extract first field
    IDS=$(tail -n +2 "$CSV_FILE" | awk -F',' '{print $1}' | grep -E '^[0-9]+$' | tr '\n' ',' | sed 's/,$//')
    
    if [ -z "$IDS" ]; then
        echo "No valid IDs found in CSV file, showing all appointments for the date:"
        # Query without NOT IN clause
        sqlite3 -header -csv "$DB_FILE" "
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
        ORDER BY 
            CASE 
                WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999
                ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER)
            END ASC;
        "
    else
        # Create and execute query with NOT IN clause
        sqlite3 -header -csv "$DB_FILE" "
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
            AND id NOT IN ($IDS)
        ORDER BY 
            CASE 
                WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999
                ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER)
            END ASC;
        "
    fi
else
    echo "CSV file not found: $CSV_FILE"
    echo "Showing all appointments for 2025-11-19:"
    sqlite3 -header -csv "$DB_FILE" "
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
    ORDER BY 
        CASE 
            WHEN scheduled_time IS NULL OR scheduled_time = '' THEN 9999
            ELSE CAST(substr(scheduled_time, 1, 2) AS INTEGER) * 100 + CAST(substr(scheduled_time, 4, 2) AS INTEGER)
        END ASC;
    "
fi

