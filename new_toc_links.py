import sys
import os
import argparse

def update_toc_links(text):
    text = text.replace("tocuniq4", "")
    return text

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Update Table of Contents links in a given writing')

    parser.add_argument(
        "-f",
        "--filename",
        type=str,
        help="Filename of existing .md writing file."
    )

    args = parser.parse_args()
    fname = args.filename
    print(fname)

    f = open(fname, 'r')
    text = f.read()
    f.close()

    text = update_toc_links(text)

    f = open(fname, "w")
    f.write(text)
    f.close()
