#!/usr/bin/env python3
"""
Compare user's list with CSV files and find entries in CSV that are not in the list.
"""

import csv
import sys
from pathlib import Path

# User's list (tab-separated)
user_list_text = """Bereket teshale	0943656575	2025-11-18	10:00 AM	መበርቻዬ (ተከስተ ጌትነት)	ስምህን አወኩት 	Aster abebe 
Natnael hailu	0913107650	2025-11-18	10:07 AM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ሰው አይረሳም	Yosef ayalew 
Abigya Abebe	0906325645	2025-11-18	10:21 AM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ለኛ አይደለም	እያሱ እና  ኣብርሃም
እያሱ ዘመዴ አኒቶ	0933158650	2025-11-18	10:28 AM	መበርቻዬ (ተከስተ ጌትነት)	ይወደኛል	ተስፋዬ ጫላ 
Christian Sawo	0953440667	2025-11-18	10:35 AM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ጠብቅሃለው geta	ዳዊት ጌታቸው 
My Name is Dawit Eshetu	0937703529	2025-11-18	10:42 AM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	Eyesus eyesus yemilew	Kalkidan tilahun
Kidus mesay	0975831113	2025-11-18	11:24 AM	መበርቻዬ (ተከስተ ጌትነት)	ክብር የበቃህ ነህ	Aster abebe
Dibora shiferaw	0940664750	2025-11-18	11:38 AM	መበርቻዬ (ተከስተ ጌትነት)	ዘላለም አይጠፋም	ዳዊት ጌታቸው
Eyerusalem Alemu	0928280728	2025-11-18	11:45 AM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ከዛሬ ጀምሮ	ሳሙኤልአበበ
SHIFERAW TESFAYE GEBREYES	913642461	2025-11-18	03:00 PM	መበርቻዬ (ተከስተ ጌትነት)	መደምደሚያዬ ነህ	አገኘው ይደግ
Hallelujah Girma	0944227821	2025-11-18	03:07 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	Aynochen ke meskel ansche	Zema 4 Christ
ፀጋ ጥሩነህ	0983419898	2025-11-18	03:28 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ሀብተ ሰማይ	ሀና ተክሌ
Metsnanat abebe megersa	930800361	2025-11-18	04:31 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ስምህን አወኩኝ	አስቴር አበበ መገርሳ
Dibora Abrham	0940049721	2025-11-18	04:59 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	Gize	Feven yosef
Bereket Derbe	0953867635	2025-11-18	05:06 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	የዘላለም አምላክ	ሀና ተክሌ
Hana ashenafi	0985468848	2025-11-18	05:13 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	Eregnaye	Yohannes Girma
መ	0953504161	2025-11-18	05:41 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ላውድልህ	ይድነቃቸው 
Mihiret mulugeta	0921236417	2025-11-18	05:48 PM	መበርቻዬ (ተከስተ ጌትነት)	Aynegerim	Eyasu tekilemariyam
						
Evana shiferaw	0948697720	2025-11-19	10:21 AM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ሥምህን አውቅኩት ተረዳሁት	Aster abebe
Selam Meseret	0906625517	2025-11-19	10:28 AM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	Broken vessels(amazing grace)	Hillsong worship 
Biniyam Edeglign	0967421338	2025-11-19	10:56 AM	መበርቻዬ (ተከስተ ጌትነት)	መውድዴን ከልቤ ዘርዝሬ	ለአለም ጥላሁን
Samuel Wondmu	251947482086	2025-11-19	11:38 AM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	Eyesus 	Dagmawi Tilahun 
Beimnet sisay tolosa	0988435925	2025-11-19	12:06 PM	መበርቻዬ (ተከስተ ጌትነት)	አልተጋነነም 	Tekeste Getnet 
ሐና መስፍን	0989011842	2025-11-19	12:13 PM	መበርቻዬ (ተከስተ ጌትነት)	መበርቻዬ	ተከስተ ጌትነት
Mintesnot Demelash	0936436758	2025-11-19	12:20 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	እናመልክሃለን	Azeb hailu
"ፀጋ ደመላሽ
Tsega Demelash"	+251909602292	2025-11-19	12:27 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ኧረ እኔ ማን ነኝ	ዳግማዊ ጥላሁን
Isayas legesse	0908220838	2025-11-19	12:34 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ለፍቅሬ መግለጫ እንዲሆነኝ	ለአለም ጥላሁን
Mahlet Mussie	0974314120	2025-11-19	12:41 PM	መበርቻዬ (ተከስተ ጌትነት)	Eyesus	Ezra
Misganaye Amare Dereje	+251911598384	2025-11-19	12:48 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	መደምደሚያዬ ነህ	አገኘሁ ይደግ
Tizita Saol Wodajo	0902902081	2025-11-19	03:00 PM	መበርቻዬ (ተከስተ ጌትነት)	ይህ ነው ቤዛዬ	መስከረም ጌቱ 
Ruth Tasew	0904436853	2025-11-19	03:07 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ማን ያንከባለው ይህን ድንጋይ	ተከስተ ጌትነት
Nebiyu Mulatu Alemu	+251977045056	2025-11-19	03:14 PM	መበርቻዬ (ተከስተ ጌትነት)	አንተ ለኔ መልካም ነህ	Temesgen markos
ሳራ በለጠ	0987096128	2025-11-19	03:21 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ፈልጌ 	Aster abebe
Bereket dereje	0955866374	2025-11-19	03:28 PM	መበርቻዬ (ተከስተ ጌትነት)	Walth	Tekesta Getenet
Meron Ayele Aba	0983962544	2025-11-19	03:35 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	መንፈስቅዱስ 	ዳንኤል ታደሰ
ልዑልሰገድ ከበደ ወ/ሰንበት	0935107902	2025-11-19	03:42 PM	መበርቻዬ (ተከስተ ጌትነት)	አለምን ሁሉ አትርፈ/ አንድ ቀን በቤትህ 	ዳዊት ጌታቸው 
Kidist dawit	0953752424	2025-11-19	03:49 PM	መበርቻዬ (ተከስተ ጌትነት)	ፅድቅን እንዲያወረ	አዜብ ሀይሉ
Jalele genene	0942104372	2025-11-19	03:56 PM	መበርቻዬ (ተከስተ ጌትነት)	Eyesus	Ezra redda
Melewot Wolde	0921100952	2025-11-19	04:03 PM	መበርቻዬ (ተከስተ ጌትነት)	Efeligihalehu	Dawit Getachew
Wengel Mesfin Derash	0934446953	2025-11-19	04:10 PM	መበርቻዬ (ተከስተ ጌትነት)	ይሄ ነው የኔ ጌታ 	አዜብ ሀይሉ
Dursitu Zeleke Lanto	0922228892	2025-11-19	04:17 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ዘላለማዊ ልብሴ	እንዳለ ወ/ጊዮርጊስ 
Rohobot Abebe	+251941493696	2025-11-19	04:24 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	መኖሪያዬ ነህ 	Betelhem welde
Henok Sebsibe	0705116166	2025-11-19	04:31 PM	መበርቻዬ (ተከስተ ጌትነት)	Anten Lawequbih Kibir Neh	Yohannes Girma
Ruhama ayele	0985372873	2025-11-19	04:38 PM	መበርቻዬ (ተከስተ ጌትነት)	Ye Eyesus dem	Bereket tesfaye
Mehiret mulugeta haylemaryam	0991331907	2025-11-19	05:06 PM	መበርቻዬ (ተከስተ ጌትነት)	የዘላለም ፈጣሪ	hana tekle
ሰላም ይንገስ	0988141912	2025-11-19	05:20 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	ምህረቱ አያልቅምና	pator tesfaye gabiso
Endalkachew Desta	0984548178	2025-11-19	05:27 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	Abet meherteh yebezalet	Daniel Amdemichael
Dinksra Asmamaw	0951021441	2025-11-19	05:34 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	አንድ ቀን በቤትህ 	ዳዊት ጌታቸው 
Rediet Asmamaw	+251973325111	2025-11-19	05:34 PM	ደሙን ለእኔ አፍሱ (አዲሱ ወርቁ)	አንተ ክብሬ ነህ 	ዳዊት ጌታቸው 
Helina Tadesse	0911689998	2025-11-19	05:48 PM	እውቀት ሳይኖረኝ (አብርሃም እና እያሱ)	ጉዳዬ 	አስቴር አበበ"""

def normalize_phone(phone):
    """Normalize phone numbers for comparison"""
    # Remove spaces, dashes, and convert to string
    phone = str(phone).strip()
    # Remove leading + or 0 if present
    if phone.startswith('+'):
        phone = phone[1:]
    if phone.startswith('0'):
        phone = phone[1:]
    return phone

def normalize_name(name):
    """Normalize names for comparison"""
    return str(name).strip().lower().replace('"', '')

def normalize_time(time_str):
    """Normalize time strings for comparison"""
    return str(time_str).strip().upper()

def parse_user_list(text):
    """Parse the user's tab-separated list"""
    user_entries = set()
    lines = text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('\t') or all(c in '\t ' for c in line):
            continue
        
        parts = line.split('\t')
        if len(parts) >= 4:
            name = normalize_name(parts[0])
            phone = normalize_phone(parts[1])
            date = parts[2].strip()
            time = normalize_time(parts[3])
            
            # Create a unique key: name + phone + date + time
            key = (name, phone, date, time)
            user_entries.add(key)
    
    return user_entries

def read_csv_file(csv_path):
    """Read CSV file and return list of entries"""
    entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries

def find_missing_entries(user_entries, csv_entries):
    """Find entries in CSV that are not in user's list"""
    missing = []
    
    for entry in csv_entries:
        name = normalize_name(entry.get('applicant_name', ''))
        phone = normalize_phone(entry.get('applicant_phone', ''))
        date = entry.get('scheduled_date', '').strip()
        time = normalize_time(entry.get('scheduled_time', ''))
        
        key = (name, phone, date, time)
        
        if key not in user_entries:
            missing.append(entry)
    
    return missing

def main():
    # Parse user's list
    user_entries = parse_user_list(user_list_text)
    print(f"Found {len(user_entries)} entries in user's list\n")
    
    # CSV file paths
    csv_files = [
        Path('/home/barch/projects/chenaniah/web/chenaniah-web/appointments_nov18_2025.csv'),
        Path('/home/barch/projects/chenaniah/web/chenaniah-web/appointments_nov19_2025.csv')
    ]
    
    all_missing = []
    
    for csv_file in csv_files:
        if not csv_file.exists():
            print(f"Warning: {csv_file} not found, skipping...")
            continue
        
        print(f"\n{'='*80}")
        print(f"Checking: {csv_file.name}")
        print(f"{'='*80}")
        
        csv_entries = read_csv_file(csv_file)
        missing = find_missing_entries(user_entries, csv_entries)
        
        if missing:
            print(f"\nFound {len(missing)} entries in CSV that are NOT in your list:\n")
            for entry in missing:
                print(f"ID: {entry.get('id', 'N/A')}")
                print(f"  Name: {entry.get('applicant_name', 'N/A')}")
                print(f"  Phone: {entry.get('applicant_phone', 'N/A')}")
                print(f"  Date: {entry.get('scheduled_date', 'N/A')}")
                print(f"  Time: {entry.get('scheduled_time', 'N/A')}")
                print(f"  Selected Song: {entry.get('selected_song', 'N/A')}")
                print()
            all_missing.extend(missing)
        else:
            print("\nAll entries in CSV are in your list!")
    
    # Summary
    print(f"\n{'='*80}")
    print(f"SUMMARY: Found {len(all_missing)} total entries in CSV files that are NOT in your list")
    print(f"{'='*80}")

if __name__ == '__main__':
    main()

