import re

def extract_infobox(wikitext: str) -> str | None:
    """
    Extrait le bloc complet {{Infobox ... }} du wikitext
    """
    pattern = re.compile(r"\{\{Infobox[\s\S]*?\n\}\}", re.IGNORECASE)
    match = pattern.search(wikitext)
    return match.group(0) if match else None


def parse_infobox_fields(infobox_text: str) -> dict:
    fields = {}
    lines = infobox_text.splitlines()

    for line in lines:
        line = line.strip()
        if line.startswith("|") and "=" in line:
            key, value = line[1:].split("=", 1)
            fields[key.strip()] = clean_value(value.strip())

    return fields


def clean_value(value: str) -> str:
    """
    Nettoie une valeur wiki basique
    """
    # [[Page|Label]] → Label
    value = re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", value)

    # [[Page]] → Page
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)

    return value.strip()


