import datetime


def get_lines(file):
    lines = []
    with open(file) as f:
        for l in f.readlines():
            lines.append(l)
    return lines


# function for outputting something
def out(text: str):
    print(f"{datetime.datetime.now()} {text}")
