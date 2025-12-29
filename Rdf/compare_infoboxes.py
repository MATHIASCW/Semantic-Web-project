"""
Comparaison des infoboxes entre infoboxes/ et infoboxes_old_data/

Ce script :
- Compte le nombre d'infoboxes dans chaque dossier
- Extrait les titres des pages (partie "--- Title ---")
- Compare les titres pour trouver les similaires/différences
- Affiche un rapport détaillé
"""

import os
import re
from pathlib import Path
from collections import defaultdict


def extract_page_title(infobox_file):
    """
    Extrait le titre de la page depuis le contenu du fichier infobox.
    Format: --- Page Title ---
    """
    try:
        with open(infobox_file, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            match = re.match(r"^---\s+(.+?)\s+---$", first_line)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Error reading {infobox_file}: {e}")
    return None


def get_infoboxes_from_directory(directory):
    """
    Récupère tous les fichiers infobox d'un répertoire.
    Retourne un dictionnaire {filename: page_title}
    """
    infoboxes = {}
    
    if not os.path.exists(directory):
        print(f"⚠️  Répertoire non trouvé: {directory}")
        return infoboxes
    
    for filename in os.listdir(directory):
        if filename.startswith("infobox_") and filename.endswith(".txt"):
            filepath = os.path.join(directory, filename)
            title = extract_page_title(filepath)
            if title:
                infoboxes[filename] = title
    
    return infoboxes


def compare_infoboxes():
    """
    Compare les infoboxes entre les deux dossiers.
    """
    print("=" * 80)
    print("COMPARAISON DES INFOBOXES")
    print("=" * 80)
    
    current_dir = "infoboxes"
    old_dir = "infoboxes_old_data"
    
    current_infoboxes = get_infoboxes_from_directory(current_dir)
    old_infoboxes = get_infoboxes_from_directory(old_dir)
    
    print(f"\n📊 STATISTIQUES:")
    print(f"  • Infoboxes actuelles ({current_dir}): {len(current_infoboxes)}")
    print(f"  • Infoboxes anciennes ({old_dir}):     {len(old_infoboxes)}")
    
    current_titles = set(current_infoboxes.values())
    old_titles = set(old_infoboxes.values())
    
    common_titles = current_titles & old_titles
    only_current = current_titles - old_titles
    only_old = old_titles - current_titles
    
    print(f"\n📈 COMPARAISON:")
    print(f"  • Titres en commun:      {len(common_titles)}")
    print(f"  • Uniquement dans {current_dir}: {len(only_current)}")
    print(f"  • Uniquement dans {old_dir}:     {len(only_old)}")
    
    total = max(len(current_titles), len(old_titles))
    if total > 0:
        similarity = (len(common_titles) / total) * 100
        print(f"  • Taux de similitude:    {similarity:.1f}%")
    
    if only_current:
        print(f"\n✨ NOUVELLES PAGES DANS {current_dir.upper()} ({len(only_current)}):")
        for title in sorted(only_current)[:20]:
            print(f"    - {title}")
        if len(only_current) > 20:
            print(f"    ... et {len(only_current) - 20} autres")
    
    if only_old:
        print(f"\n🗑️  PAGES UNIQUEMENT DANS {old_dir.upper()} ({len(only_old)}):")
        for title in sorted(only_old)[:20]:
            print(f"    - {title}")
        if len(only_old) > 20:
            print(f"    ... et {len(only_old) - 20} autres")
    
    print(f"\n" + "=" * 80)
    print(f"RÉSUMÉ:")
    print(f"  • Pages à récupérer (non présentes):  {len(only_current)}")
    print(f"  • Couverture totale:                   {len(current_titles | old_titles)} pages")
    print(f"=" * 80 + "\n")
    
    report_file = "infobox_comparison_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("RAPPORT DÉTAILLÉ DE COMPARAISON\n")
        f.write("=" * 80 + "\n\n")
        
        f.write(f"NOUVELLES PAGES ({len(only_current)}):\n")
        for title in sorted(only_current):
            f.write(f"  {title}\n")
        
        f.write(f"\n\nPAGES SUPPRIMÉES ({len(only_old)}):\n")
        for title in sorted(only_old):
            f.write(f"  {title}\n")
        
        f.write(f"\n\nPAGES EN COMMUN ({len(common_titles)}):\n")
        for title in sorted(common_titles):
            f.write(f"  {title}\n")
    
    print(f"✅ Rapport détaillé sauvegardé: {report_file}\n")


if __name__ == "__main__":
    compare_infoboxes()
