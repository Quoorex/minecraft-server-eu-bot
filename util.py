def get_lines(file):
    lines = []
    with open(file) as f:
        for l in f.readlines():
            lines.append(l)
    return lines
