#!/usr/bin/env python3
"""
Convert applicants CSV to VCF (vCard) format for phone import
"""

import csv
import os

def escape_vcf_text(text):
    """Escape special characters for VCF format"""
    if not text:
        return ""
    # Replace newlines with spaces, escape commas and semicolons
    text = str(text).replace('\n', ' ').replace('\r', ' ')
    text = text.replace(',', '\\,').replace(';', '\\;')
    return text

def write_contact_to_vcf(f, contact, group_prefix=None, group_name=None):
    """Write a single contact to VCF file"""
    original_name = escape_vcf_text(contact['name'])
    phone = contact['phone'].strip()
    
    # Add group prefix to name for easy searching on Samsung phones
    # Format: "G01: Original Name" - makes it easy to search and select all contacts in a group
    if group_prefix:
        display_name = f"{group_prefix}: {original_name}"
    else:
        display_name = original_name
    
    # Write vCard format
    f.write('BEGIN:VCARD\n')
    f.write('VERSION:3.0\n')
    f.write(f'FN:{display_name}\n')  # Full Name (with group prefix)
    f.write(f'N:{display_name};;;;\n')  # Name (structured)
    f.write(f'TEL;TYPE=CELL:{phone}\n')  # Phone number
    # Add organization field for better grouping (Samsung sometimes recognizes this)
    if group_name:
        f.write(f'ORG:{group_name}\n')
        f.write(f'CATEGORIES:{group_name}\n')
    f.write('END:VCARD\n')
    f.write('\n')

def csv_to_vcf_batches(csv_file, batch_size=20, output_folder='vcf_groups'):
    """Convert CSV file to multiple VCF files, each with up to batch_size contacts"""
    contacts = []
    
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        print(f"📁 Created folder: {output_folder}")
    
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
        
        # Create VCF file path in output folder
        vcf_filename = f'applicants_contacts_batch_{batch_num + 1:02d}_of_{num_batches:02d}.vcf'
        vcf_file = os.path.join(output_folder, vcf_filename)
        vcf_files.append(vcf_file)
        
        # Create group name and prefix for this batch (for Samsung group messaging)
        group_name = f'Applicants_Group_{batch_num + 1:02d}'
        group_prefix = f'G{batch_num + 1:02d}'  # Short prefix like G01, G02, etc.
        
        with open(vcf_file, 'w', encoding='utf-8') as f:
            for contact in batch_contacts:
                write_contact_to_vcf(f, contact, group_prefix=group_prefix, group_name=group_name)
        
        print(f"✅ Created batch {batch_num + 1}/{num_batches}: {vcf_filename} ({len(batch_contacts)} contacts)")
    
    print(f"\n✅ Total: {total_contacts} contacts split into {num_batches} batches of up to {batch_size} contacts each")
    print(f"\n📁 All VCF files saved in: {output_folder}/")
    print(f"\n📱 Import Instructions for Samsung S9:")
    print(f"   1. Import each batch file one at a time on your phone")
    print(f"   2. After importing one batch, wait for it to finish before importing the next")
    print(f"   3. Start with: {output_folder}/applicants_contacts_batch_01_of_{num_batches:02d}.vcf")
    print(f"\n💬 Group Messaging Instructions for Samsung S9:")
    print(f"   - Each VCF file contains exactly {batch_size} contacts (perfect for group messaging)")
    print(f"   - Contacts have group prefixes in their names (e.g., 'G01: John Doe', 'G02: Jane Smith')")
    print(f"   - After importing contacts, to create a group message:")
    print(f"     a. Open Messages app → Create new message")
    print(f"     b. Tap the '+' or 'Add recipient' button")
    print(f"     c. Search for the group prefix (e.g., type 'G01' to find all Group 01 contacts)")
    print(f"     d. Select all contacts that appear (they all start with the same prefix)")
    print(f"     e. Type your message and send to the group")
    print(f"   - Alternative: After importing, you can manually select up to {batch_size} contacts")
    print(f"     from the same batch by searching for their group prefix")
    print(f"\n📋 Batch files created in {output_folder}/:")
    for vcf_file in vcf_files:
        print(f"   - {os.path.basename(vcf_file)}")
    
    return vcf_files

if __name__ == '__main__':
    csv_file = 'applicants_processed.csv'
    batch_size = 20  # Changed to 20 for Samsung S9 group messaging
    output_folder = 'vcf_groups'  # Folder to store all VCF files
    
    csv_to_vcf_batches(csv_file, batch_size, output_folder)

