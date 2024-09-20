import numpy as np
import torch
from torch.utils.data import IterableDataset, DataLoader
import chess

# Constants
BOARD_SIZE = 8
NUM_PIECE_TYPES = 6  # pawn, knight, bishop, rook, queen, king
NUM_COLORS = 2  # white, black
NUM_CHANNELS = NUM_PIECE_TYPES * NUM_COLORS

def fen_to_tensor(fen):
    board_state = fen.split()[0]
    tensor = np.zeros((NUM_CHANNELS, BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    
    piece_dict = {
        'p': 0, 'n': 1, 'b': 2, 'r': 3, 'q': 4, 'k': 5,
        'P': 6, 'N': 7, 'B': 8, 'R': 9, 'Q': 10, 'K': 11
    }
    
    row, col = 0, 0
    for char in board_state:
        if char == '/':
            row += 1
            col = 0
        elif char.isdigit():
            col += int(char)
        else:
            tensor[piece_dict[char], row, col] = 1
            col += 1
    
    # Normalize the tensor
    tensor = tensor / 6.0  # Divide by the number of piece types
    
    return tensor

def augment_data(fen, moved_from, moved_to):
    board = chess.Board(fen)
    augmented_data = [(fen, moved_from, moved_to)]
    
    # Mirror horizontally
    mirrored_board = board.mirror()
    mirrored_fen = mirrored_board.fen()
    mirrored_from = chess.square_mirror(moved_from)
    mirrored_to = chess.square_mirror(moved_to)
    augmented_data.append((mirrored_fen, mirrored_from, mirrored_to))
    
    return augmented_data

class StreamingChessDataset(IterableDataset):
    def __init__(self, filename):
        self.filename = filename

    def __iter__(self):
        with open(self.filename, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) >= 4:
                    fen = ' '.join(parts[:-3])  # FEN might contain spaces
                    color = parts[-3]
                    moved_from = int(parts[-2])
                    moved_to = int(parts[-1])
                    # Augment data
                    augmented_data = augment_data(fen, moved_from, moved_to)
                    for aug_fen, aug_from, aug_to in augmented_data:
                        input_tensor = torch.tensor(fen_to_tensor(aug_fen), dtype=torch.float32)
                        
                        # Create output label (one-hot encoding for the move)
                        output_label = torch.zeros(64 * 64, dtype=torch.float32)
                        move_index = aug_from * 64 + aug_to
                        output_label[move_index] = 1
                        
                        yield input_tensor, output_label

def create_data_loaders(filename, batch_size=32, train_split=0.8):
    dataset = StreamingChessDataset(filename)
    
    # Determine the total number of samples
    total_samples = sum(1 for _ in open(filename)) * 2  # *2 because of data augmentation
    
    train_size = int(train_split * total_samples)
    test_size = total_samples - train_size
    
    train_dataset = torch.utils.data.Subset(dataset, range(train_size))
    test_dataset = torch.utils.data.Subset(dataset, range(train_size, total_samples))
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, num_workers=4)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, num_workers=4)
    
    return train_loader, test_loader

if __name__ == "__main__":
    filename = "dataset.txt"
    train_loader, test_loader = create_data_loaders(filename)
    print(f"Number of training batches: {len(train_loader)}")
    print(f"Number of testing batches: {len(test_loader)}")

    # Example of accessing a batch
    for inputs, labels in train_loader:
        print(f"Input shape: {inputs.shape}")
        print(f"Label shape: {labels.shape}")
        break