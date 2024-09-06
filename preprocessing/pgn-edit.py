def get_opening(file_path):
    with open(file_path, 'r') as file:
        pgns = file.readlines()
    
    modified_pgns = []
    for pgn in pgns:
        moves = pgn.split(' ')
        opening_moves = ' '.join(moves[:10])  # Keep only the first 5 moves (10 half-moves)
        modified_pgns.append(opening_moves)
    
    output_file = file_path.replace('.txt', '_opening.txt')  # Create output file name
    with open(output_file, 'w') as out_file:
        out_file.writelines(modified_pgns)  # Write modified PGNs to the new file

def get_endgame(file_path):
    with open(file_path, 'r') as file:
        pgns = file.readlines()
    
    modified_pgns = []
    for pgn in pgns:
        moves = pgn.split(' ')
        endgame_moves = ' '.join(moves[10:])  # Get moves from 11 to the end
        modified_pgns.append(endgame_moves)
    
    output_file = file_path.replace('.txt', '_endgame.txt')  # Create output file name
    with open(output_file, 'w') as out_file:
        out_file.writelines(modified_pgns)  # Write modified PGNs to the new file

