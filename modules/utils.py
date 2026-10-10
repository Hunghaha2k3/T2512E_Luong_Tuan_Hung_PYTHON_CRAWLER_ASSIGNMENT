def read_int(prompt):
    while True:
        try:
            return int(input(prompt).strip())
        except ValueError:
            print("Vui lòng nhập số hợp lệ.")

def read_required(prompt):
    while True:
        value = input(prompt).strip()
        if value:
            return value
        print("Không được để trống.")

def read_optional(prompt):
    value = input(prompt).strip()
    return value if value else None

def read_keep(label, current):
    """Enter = giữ nguyên giá trị hiện tại."""
    value = input(f"{label} [{current or ''}]: ").strip()
    return value if value else current

def print_table(headers, rows, widths):
    line = "".join(f"{h:<{w}}" for h, w in zip(headers, widths))
    print(line)
    print("-" * len(line))
    for r in rows:
        print("".join(f"{str(v)[:w - 1]:<{w}}" for v, w in zip(r, widths)))