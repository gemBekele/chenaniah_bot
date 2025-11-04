#!/usr/bin/env python3
"""
Process applicants CSV file to:
1. Normalize all phone numbers to 09xxxxxxxx format (10 digits)
2. Duplicate rows when there are multiple phone numbers
"""

import csv
import re

def normalize_phone(phone_str):
    """
    Normalize phone number to 09xxxxxxxx format (10 digits).
    Handles various formats:
    - +251911598384 -> 0911598384
    - 251911598384 -> 0911598384
    - 0966974706 -> 0966974706
    - 0704506242 -> 0904506242 (convert 07 to 09)
    """
    if not phone_str:
        return []
    
    # Remove quotes and clean up the string
    phone_str = str(phone_str).strip().strip('"').strip("'")
    
    # Split by common separators: /, newlines, commas
    # This handles multiple phone numbers in one field
    phones = re.split(r'[/,\n]', phone_str)
    
    normalized = []
    
    for phone in phones:
        phone = phone.strip()
        if not phone:
            continue
        
        original_phone = phone
            
        # Remove all non-digit characters except + at the start
        cleaned = re.sub(r'[^\d+\s]', '', phone)
        cleaned = cleaned.replace(' ', '')
        
        # Check for international numbers (not Ethiopian)
        # Skip numbers with country codes other than +251 or 251
        if cleaned.startswith('+'):
            if not cleaned.startswith('+251'):
                # International number - skip it
                continue
        elif len(cleaned) >= 10 and not (cleaned.startswith('0') or cleaned.startswith('251')):
            # Might be international - check if it's a valid Ethiopian format
            # Ethiopian numbers are typically 9-10 digits starting with 0 or 251
            if len(cleaned) > 12:  # Too long for Ethiopian number
                continue
        
        # Handle +251 country code
        if cleaned.startswith('+251'):
            cleaned = cleaned[4:]  # Remove +251
            if not cleaned.startswith('0'):
                # If it starts with 7, it should be 07 (for +2517)
                if cleaned.startswith('7'):
                    cleaned = '07' + cleaned[1:]
                else:
                    cleaned = '0' + cleaned
        # Handle 251 country code (without +)
        elif cleaned.startswith('251') and len(cleaned) > 3:
            cleaned = cleaned[3:]  # Remove 251
            if not cleaned.startswith('0'):
                # If it starts with 7, it should be 07 (for 2517)
                if cleaned.startswith('7'):
                    cleaned = '07' + cleaned[1:]
                else:
                    cleaned = '0' + cleaned
        
        # Remove any remaining non-digits
        cleaned = re.sub(r'\D', '', cleaned)
        
        # Skip if empty or too short (less than 9 digits)
        if not cleaned or len(cleaned) < 9:
            continue
        
        # Keep 07 numbers as-is (different service provider)
        # Convert 08 to 09, but keep 07
        if cleaned.startswith('08') and len(cleaned) == 10:
            cleaned = '09' + cleaned[2:]
        # Don't convert 07 - keep it as 07
        
        # Ensure it starts with 0
        if not cleaned.startswith('0'):
            if cleaned.startswith('9') and len(cleaned) == 9:
                cleaned = '0' + cleaned
            elif cleaned.startswith('7') and len(cleaned) == 9:
                # Handle +2517 case - if we have 7xxxxxxx after removing +251
                cleaned = '07' + cleaned[1:]
            elif len(cleaned) == 9:
                cleaned = '09' + cleaned
            else:
                # Try to extract last 9 digits if it's longer
                if len(cleaned) > 9:
                    cleaned = '0' + cleaned[-9:]
        
        # Final validation and normalization
        # Accept both 07xxxxxxxx and 09xxxxxxxx (10 digits)
        if len(cleaned) == 10:
            if cleaned.startswith('09') or cleaned.startswith('07'):
                normalized.append(cleaned)
            elif cleaned.startswith('0'):
                # Convert any other 0x to 09 (except 07 which we keep)
                if cleaned[1] in '0123456789' and not cleaned.startswith('07'):
                    normalized.append('09' + cleaned[2:])
        elif len(cleaned) == 9:
            if cleaned.startswith('9'):
                normalized.append('0' + cleaned)
            elif cleaned.startswith('7'):
                # Handle case where we have 7xxxxxxx (should be 07xxxxxxx)
                normalized.append('07' + cleaned[1:])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_normalized = []
    for phone in normalized:
        # Accept both 07 and 09 prefixes
        if phone not in seen and len(phone) == 10 and (phone.startswith('09') or phone.startswith('07')):
            seen.add(phone)
            unique_normalized.append(phone)
    
    return unique_normalized

def process_csv(input_file, output_file):
    """Process the CSV file and create a new one with normalized phone numbers"""
    rows_processed = []
    rows_skipped = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            name = row['name'].strip().strip('"')
            phone_field = row['phone']
            
            # Normalize phone numbers
            normalized_phones = normalize_phone(phone_field)
            
            if not normalized_phones:
                # Skip rows with no valid phone numbers
                rows_skipped.append(f"{name}: {phone_field}")
                continue
            
            # Create a row for each phone number
            for phone in normalized_phones:
                rows_processed.append({
                    'name': name,
                    'phone': phone
                })
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'phone'])
        writer.writeheader()
        writer.writerows(rows_processed)
    
    print(f"✅ Processed {len(rows_processed)} rows")
    print(f"⚠️  Skipped {len(rows_skipped)} rows with invalid phone numbers")
    
    if rows_skipped:
        print("\nSkipped rows:")
        for skipped in rows_skipped[:10]:  # Show first 10
            print(f"  - {skipped}")
        if len(rows_skipped) > 10:
            print(f"  ... and {len(rows_skipped) - 10} more")

if __name__ == '__main__':
    input_file = 'applicants copy.csv'
    output_file = 'applicants_processed.csv'
    
    process_csv(input_file, output_file)
    print(f"\n✅ Output saved to: {output_file}")

