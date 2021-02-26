import datetime


def get_lines(file):
    lines = []
    with open(file) as f:
        for l in f.readlines():
            if l[0] != '#' and len(l) > 1:
                lines.append(l.rstrip("\n"))
    return lines


# function for outputting something
def out(text: str):
    print(f"{datetime.datetime.now()} {text}")
