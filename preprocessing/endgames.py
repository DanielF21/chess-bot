def extract_endgame(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith('['):
                outfile.write(line)
            elif line.strip():
                moves = line.split('6.')
                if len(moves) > 1:
                    endgame = '6.' + '6.'.join(moves[1:])  # Keep '6.' and everything after
                    outfile.write(endgame.strip() + '\n\n')
                else:
                    outfile.write(line)  # If there's no '6.', write the whole line

# Usage
input_file = 'filtered_dataset.pgn'
output_file = 'lichess_endgames.pgn'

extract_endgame(input_file, output_file)
print(f"Extracted endgames (from 6th move onwards) from {input_file} to {output_file}")