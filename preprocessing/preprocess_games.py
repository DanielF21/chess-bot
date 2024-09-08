import numpy as np
import sys

def fen_to_matrix(fen):
    fen = fen.split()[0]
    
    piece_dict = {
        'p' : [0,1,0,0,0,0,0,0,0,0,0,0,0],
        'P' : [0,0,0,0,0,0,0,1,0,0,0,0,0],
        'n' : [0,0,1,0,0,0,0,0,0,0,0,0,0],
        'N' : [0,0,0,0,0,0,0,0,1,0,0,0,0],
        'b' : [0,0,0,1,0,0,0,0,0,0,0,0,0],
        'B' : [0,0,0,0,0,0,0,0,0,1,0,0,0],
        'r' : [0,0,0,0,1,0,0,0,0,0,0,0,0],
        'R' : [0,0,0,0,0,0,0,0,0,0,1,0,0],
        'q' : [0,0,0,0,0,1,0,0,0,0,0,0,0],
        'Q' : [0,0,0,0,0,0,0,0,0,0,0,1,0],
        'k' : [0,0,0,0,0,0,1,0,0,0,0,0,0],
        'K' : [0,0,0,0,0,0,0,0,0,0,0,0,1],
        '.' : [0,0,0,0,0,0,0,0,0,0,0,0,0],
    }

    row_arr = []
    rows = fen.split('/')
    for row in rows:
        arr = []
        for ch in str(row):
            if ch.isdigit():
                for _ in range(int(ch)):
                    arr.append(piece_dict['.'])
            else:
                arr.append(piece_dict[ch])
        row_arr.append(arr)

    return np.array(row_arr)

def process_fen_generator(input_file):
    prev = None
    prev_fen = None
    prev_color = None
    
    with open(input_file) as in_file:
        for cnt, line in enumerate(in_file, 1):
            parts = line.rstrip().split(' ')
            fen = parts[0]
            color = parts[1]  # 'w' or 'b'
            cur = np.argmax(fen_to_matrix(fen), axis=-1)

            if prev is not None:
                dif = cur - prev
                lo = np.argmin(dif)
                hi = np.argmax(dif)
                yield prev_fen, prev_color, lo, hi

            prev = cur
            prev_fen = fen
            prev_color = color

            if cnt % 50_000 == 0:
                print('Processed', cnt, 'positions', file=sys.stderr)

def get_moves(input_file, output_file):
    with open(output_file, 'w') as out_file:
        for prev_fen, prev_color, lo, hi in process_fen_generator(input_file):
            out_file.write(f'{prev_fen} {prev_color} {lo} {hi}\n')

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python get_moves.py <input_file> <output_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    get_moves(input_file, output_file)
    print("Processing complete.", file=sys.stderr) 