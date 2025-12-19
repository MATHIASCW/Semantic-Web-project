import os
import re

infobox_dir = os.path.join(os.path.dirname(__file__), '..', 'infoboxes')

for filename in os.listdir(infobox_dir):
    if filename.startswith('infobox_') and filename.endswith('.txt'):
        file_path = os.path.join(infobox_dir, filename)
        with open(file_path, 'r', encoding='utf-8') as f:
            first_line = f.readline().strip()
        match = re.match(r'^---\s*(.+?)\s*---$', first_line)
        if match:
            entity = match.group(1)
            entity_clean = re.sub(r'[^\w\-]', '_', entity)
            new_filename = f"infobox_{entity_clean}.txt"
            new_path = os.path.join(infobox_dir, new_filename)
            if not os.path.exists(new_path):
                os.rename(file_path, new_path)
                print(f"Renamed {filename} -> {new_filename}")
            else:
                print(f"Skipped {filename}: {new_filename} already exists.")
        else:
            print(f"Could not extract entity from {filename}")