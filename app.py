from flask import Flask, request, jsonify
import chess
import chess.engine
import os
import sys

app = Flask(__name__)

# Initialize the chess board and engine
board = chess.Board()
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model.pb.gz")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")

lc0_command = ["lc0", f"--weights={model_path}"]
try:
    engine = chess.engine.SimpleEngine.popen_uci(lc0_command)
except Exception as e:
    print(f"Error initializing Lc0 engine: {e}")
    sys.exit(1)

@app.route('/move', methods=['POST'])
def make_move():
    data = request.json
    move_uci = data.get('move')
    if not move_uci:
        return jsonify({"error": "No move provided"}), 400

    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            ai_move = get_ai_move(engine, board)
            board.push(ai_move)
            return jsonify({"player_move": move_uci, "ai_move": ai_move.uci()})
        else:
            return jsonify({"error": "Illegal move"}), 400
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

@app.route('/reset', methods=['POST'])
def reset_game():
    board.reset()
    return jsonify({"status": "Game reset"})

@app.route('/board', methods=['GET'])
def get_board():
    return jsonify({"fen": board.fen()})

def get_ai_move(engine, board):
    result = engine.play(board, chess.engine.Limit(time=0.1))
    return result.move

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)