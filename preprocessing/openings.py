def crop_to_5_moves(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
        for line in infile:
            if line.startswith('['):
                outfile.write(line)
            elif line.strip():
                moves = line.split('6.')[0]  # Split at '6.' and take the first part
                outfile.write(moves.strip() + '\n\n')

input_file = 'daniel.pgn'
output_file = 'daniel_openings.pgn'

crop_to_5_moves(input_file, output_file)
print(f"Cropped games to first 5 moves from {input_file} to {output_file}")