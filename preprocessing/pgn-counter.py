def count_pgns(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        pgns = content.split('[Event "')
    
    return len(pgns) - 1  # Subtract 1 to account for the initial split

def count_valid_pgns(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
        pgns = content.split('[Event "')
    
    count = 0
    for pgn in pgns[1:]:  # Skip the first empty element
        if '[WhiteElo "' in pgn and '[BlackElo "' in pgn:
            white_elo = int(pgn.split('[WhiteElo "')[1].split('"')[0])
            black_elo = int(pgn.split('[BlackElo "')[1].split('"')[0])
            mean_elo = (white_elo + black_elo) / 2
            
            if mean_elo >= 1700:
                count += 1
    
    return count

def pgn_filter(input_file, output_file):
    with open(input_file, 'r') as file:
        content = file.read()
        pgns = content.split('[Event "')
    
    valid_pgns = []
    for pgn in pgns[1:]:  # Skip the first empty element
        if '[WhiteElo "' in pgn and '[BlackElo "' in pgn:
            white_elo = int(pgn.split('[WhiteElo "')[1].split('"')[0])
            black_elo = int(pgn.split('[BlackElo "')[1].split('"')[0])
            mean_elo = (white_elo + black_elo) / 2
            
            if mean_elo >= 1700:
                valid_pgns.append('[Event "' + pgn)
    
    with open(output_file, 'w') as file:
        file.write(''.join(valid_pgns))
    
    print(f"Filtered PGNs written to {output_file}")

input_file = 'data.pgn'
output_file = 'filtered_data.pgn'

# Count total PGNs in the file
total_pgns = count_pgns(input_file)
print(f'Total PGNs: {total_pgns}')

# Count valid PGNs with mean Elo 1700 or greater
valid_pgns_count = count_valid_pgns(input_file)
print(f'Valid PGNs (mean Elo 1700 or greater): {valid_pgns_count}')
pgn_filter(input_file, output_file)