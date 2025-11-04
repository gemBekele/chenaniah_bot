#!/usr/bin/env python3
"""
Convert applicants CSV to VCF (vCard) format for phone import
"""

import csv

def escape_vcf_text(text):
    """Escape special characters for VCF format"""
    if not text:
        return ""
    # Replace newlines with spaces, escape commas and semicolons
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    text = text.replace(',', '\\,').replace(';', '\\;')
    return text

def write_contact_to_vcf(f, contact):
    """Write a single contact to VCF file"""
    name = escape_vcf_text(contact['name'])
    phone = contact['phone'].strip()
    
    # Write vCard format
    f.write('BEGIN:VCARD\n')
    f.write('VERSION:3.0\n')
    f.write(f'FN:{name}\n')  # Full Name
    f.write(f'N:{name};;;;\n')  # Name (structured)
    f.write(f'TEL;TYPE=CELL:{phone}\n')  # Phone number
    f.write('END:VCARD\n')
    f.write('\n')

def csv_to_vcf_batches(csv_file, batch_size=100):
    """Convert CSV file to multiple VCF files, each with up to batch_size contacts"""
    contacts = []
    
    # Read CSV
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row['name'].strip().strip('"')
            phone = row['phone'].strip()
            
            if name and phone:
                contacts.append({
                    'name': name,
                    'phone': phone
                })
    
    total_contacts = len(contacts)
    num_batches = (total_contacts + batch_size - 1) // batch_size  # Ceiling division
    
    vcf_files = []
    
    # Create batches
    for batch_num in range(num_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, total_contacts)
        batch_contacts = contacts[start_idx:end_idx]
        
        # Create VCF file for this batch
        vcf_file = f'applicants_contacts_batch_{batch_num + 1:02d}_of_{num_batches:02d}.vcf'
        vcf_files.append(vcf_file)
        
        with open(vcf_file, 'w', encoding='utf-8') as f:
            for contact in batch_contacts:
                write_contact_to_vcf(f, contact)
        
        print(f"✅ Created batch {batch_num + 1}/{num_batches}: {vcf_file} ({len(batch_contacts)} contacts)")
    
    print(f"\n✅ Total: {total_contacts} contacts split into {num_batches} batches of up to {batch_size} contacts each")
    print(f"\n📱 Import Instructions:")
    print(f"   1. Import each batch file one at a time on your phone")
    print(f"   2. After importing one batch, wait for it to finish before importing the next")
    print(f"   3. Start with: applicants_contacts_batch_01_of_{num_batches:02d}.vcf")
    print(f"\n📋 Batch files created:")
    for vcf_file in vcf_files:
        print(f"   - {vcf_file}")
    
    return vcf_files

if __name__ == '__main__':
    csv_file = 'applicants_processed.csv'
    batch_size = 100
    
    csv_to_vcf_batches(csv_file, batch_size)

