import sys
import re

def fen_generator(input_file):
    with open(input_file) as in_file:
        for line in in_file:
            if line == '\n' or line[0] == '[':
                continue 
            matches = re.findall(r'\{\s([0-9a-zA-Z\/\s\-\.]+)\s\}', line)
            for match in matches:
                yield match.split(' ')[:2]

def extract_fen(input_file, output_file):
    processed = 0
    with open(output_file, 'w') as out_file:
        for fen in fen_generator(input_file):
            out_file.write('{}\n'.format(' '.join(fen)))
            processed += 1
            if processed % 1_000_000 == 0:
                print(f'Processed {processed} positions...', file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_fen.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    extract_fen(input_file, output_file)
    print("Extraction complete.", file=sys.stderr)