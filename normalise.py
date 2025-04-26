import re

def normalize_log(content):
    lines = content.split("\n")
    normalized_lines = []

    for line in lines:
        raw_line = line.strip()

        #Rimworld log patching
        raw_lower = raw_line.lower()
        if "initialize engine version" in raw_lower:
            normalized_lines.append("<engine_version>")
            continue
        elif "tried loading mod with the same packageid" in raw_lower:
            normalized_lines.append("<duplicate_mod>")
            continue
        elif "is missing packageid" in raw_lower:
            normalized_lines.append("<mod_missing_id>")
            continue
        elif raw_lower.startswith("applying prepatch"):
            normalized_lines.append("<mod_patch>")
            continue
        elif "fallback handler could not load library" in raw_lower:
            normalized_lines.append("<dll_fail>")
            continue
        elif raw_lower.startswith("prepatcher:"):
            normalized_lines.append("<prepatcher_event>")
            continue
        elif "mod " in raw_lower and "about.xml" in raw_lower:
            normalized_lines.append("<mod_config_warning>")
            continue
        elif "applying prepatch" in raw_lower and "on method" in raw_lower:
            normalized_lines.append("<mod_hook>")
            continue
        elif "graphics device:" in raw_lower or "direct3d" in raw_lower:
            normalized_lines.append("<unity_init>")
            continue
        elif "performancefish" in raw_lower:
            normalized_lines.append("<performance_patch>")
            continue
        elif "/workshop/content/294100/" in raw_lower:
            normalized_lines.append("<mod_path>")
            continue
        elif "about.xml" in raw_lower and ("error" in raw_lower or "missing" in raw_lower):
            normalized_lines.append("<mod_config_warning>")
            continue

        #apply general regex-based normalization
        line = raw_lower
        line = re.sub(r"/workshop/content/294100/(\d+)", r"/workshop/content/294100/<mod_id>", line)
        line = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", "<ip>", line)
        line = re.sub(r"\[\w{3} \w{3} \d{2} \d{2}:\d{2}:\d{2} \d{4}\]", "<timestamp>", line)
        line = re.sub(r"\b[a-z]{3} \d{2} \d{2}:\d{2}:\d{2}", "<timestamp>", line)
        line = re.sub(r"\bport \d+", "port <port>", line)
        line = re.sub(r"child \d+", "child <id>", line)
        line = re.sub(r"\buser [a-z0-9_]+", "user <user>", line, flags=re.IGNORECASE)
        line = re.sub(r"/[^\s]*", "<path>", line)
        line = re.sub(r"\b\d+\b", "<id>", line)
        line = re.sub(r"/workshop/content/294100/(\d+)", r"/workshop/content/294100/<mod_id>", line)
        line = re.sub(r"\b\d{1,5}\b", "<id>", line)
        line = re.sub(r"[^\w<> ]+", "", line)
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            normalized_lines.append(line)

    return "\n".join(normalized_lines)
