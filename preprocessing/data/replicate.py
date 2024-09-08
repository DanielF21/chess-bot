def replicate_file(input_file='daniel_openings.pgn'):
    output_file = f"{input_file.split('.')[0]}_scaled.pgn"  # Create output file name

    with open(input_file, 'r') as infile:
        content = infile.read()  # Read the entire content of the input file
    
    # Replicate the content 299 times
    replicated_content = content * 299
    
    with open(output_file, 'w') as outfile:
        outfile.write(replicated_content)  # Write the replicated content to the output file
    
    print(f"Created {output_file} with {len(content)} characters replicated 299 times.")

# Usage example
replicate_file()