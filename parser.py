def parse_log(path):
    errors = []
    with open(path) as f:
        lines = f.readlines()
        for i, line in enumerate(lines):
            if "ERROR" in line.upper() or "WARN" in line.upper():
                errors.append({"line": i+1, "text": line.strip()})
    return {"errors": errors, "total_lines": len(lines)}