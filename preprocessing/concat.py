def concat_pgn_files(openings_file, endgames_file):
    with open(endgames_file, 'a') as endgames:
        # Add a newline for separation if needed
        endgames.write('\n')
        
        # Append contents of daniel_openings.pgn
        with open(openings_file, 'r') as openings:
            endgames.write(openings.read())

    print(f"Appended {openings_file} to the end of {endgames_file}")

# Usage
openings_file = 'daniel_openings.pgn'
endgames_file = 'lichess_endgames.pgn'

concat_pgn_files(openings_file, endgames_file)