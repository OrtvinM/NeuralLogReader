import re

def extract_mod_ids_from_log(content):
    mod_ids = set()
    for line in content.splitlines():
        match = re.search(r"(?:/|\\)294100(?:/|\\)(\d{9,10})", line)
        if match:
            mod_ids.add(match.group(1))
    return mod_ids
    
def extract_error_mods(content):
    mod_names_in_errors = set()
    for line in content.splitlines():
        if "error" in line.lower() or "exception" in line.lower():
            match = re.search(r'mod ([\w\d\.\-_ ]+)', line, re.IGNORECASE)
            if match:
                mod_names_in_errors.add(match.group(1).strip())
    return mod_names_in_errors
