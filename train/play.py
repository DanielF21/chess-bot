import chess
import torch
import numpy as np
from model import ChessCNN
from load import fen_to_tensor

def load_model(model_path):
    model = ChessCNN()
    model.load_state_dict(torch.load(model_path, map_location=torch.device('cpu')))
    model.eval()
    return model

def get_ai_move(model, board):
    input_tensor = fen_to_tensor(board.fen())
    input_tensor = torch.from_numpy(input_tensor).float().unsqueeze(0)
    
    with torch.no_grad():
        output = model(input_tensor)
    
    move_probs = output.squeeze().numpy()
    legal_moves = list(board.legal_moves)
    legal_move_indices = [move.from_square * 64 + move.to_square for move in legal_moves]
    legal_move_probs = move_probs[legal_move_indices]
    best_move_index = np.argmax(legal_move_probs)
    return legal_moves[best_move_index]

def play_game():
    model = load_model("best_chess_model.pth")
    board = chess.Board()

    print("Welcome to Chess vs AI!")
    print("Enter moves in UCI format (e.g., e2e4)")
    print("Type 'quit' to end the game")

    while not board.is_game_over():
        print("\n" + str(board))
        
        if board.turn == chess.WHITE:
            move_uci = input("Your move (White): ")
            if move_uci.lower() == 'quit':
                break
            try:
                move = chess.Move.from_uci(move_uci)
                if move in board.legal_moves:
                    board.push(move)
                else:
                    print("Illegal move. Try again.")
                    continue
            except ValueError:
                print("Invalid move format. Use UCI (e.g., e2e4)")
                continue
        else:
            print("AI is thinking...")
            ai_move = get_ai_move(model, board)
            board.push(ai_move)
            print(f"AI moved: {ai_move.uci()}")

    print("\nGame Over")
    print(f"Result: {board.result()}")

if __name__ == "__main__":
    play_game()