from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
import os
import sys
import subprocess
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

board = chess.Board()
current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model.pb.gz")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")

lc0_command = ["lc0", f"--weights={model_path}"]

def initialize_engine():
    try:
        return chess.engine.SimpleEngine.popen_uci(lc0_command)
    except Exception as e:
        logging.error(f"Error initializing Lc0 engine: {e}")
        return None

engine = initialize_engine()

@app.route('/move', methods=['POST'])
def make_move():
    global engine, board
    data = request.json
    move_uci = data.get('move')
    if not move_uci:
        return jsonify({"error": "No move provided"}), 400

    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            
            if board.is_game_over():
                result = get_game_result(board)
                return jsonify({
                    "player_move": move_uci,
                    "game_over": True,
                    "result": result
                })
            
            # Attempt to get AI move, reinitialize engine if it fails
            for _ in range(3):  # Try up to 3 times
                try:
                    ai_move = get_ai_move(engine, board)
                    board.push(ai_move)
                    if board.is_game_over():
                        result = get_game_result(board)
                        return jsonify({
                            "player_move": move_uci,
                            "ai_move": ai_move.uci(),
                            "game_over": True,
                            "result": result
                        })
                    return jsonify({"player_move": move_uci, "ai_move": ai_move.uci()})
                except chess.engine.EngineTerminatedError:
                    logging.warning("Engine terminated. Attempting to restart...")
                    if engine:
                        engine.quit()
                    engine = initialize_engine()
                    if not engine:
                        return jsonify({"error": "Failed to restart chess engine"}), 500
            
            return jsonify({"error": "Failed to get AI move after multiple attempts"}), 500
        else:
            return jsonify({"error": "Illegal move"}), 400
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

@app.route('/reset', methods=['POST'])
def reset_game():
    global board, engine
    board.reset()
    if engine:
        engine.quit()
    engine = initialize_engine()
    if not engine:
        return jsonify({"error": "Failed to initialize chess engine"}), 500
    return jsonify({"status": "Game reset"})

@app.route('/board', methods=['GET'])
def get_board():
    return jsonify({"fen": board.fen()})

def get_ai_move(engine, board):
    if not engine:
        raise chess.engine.EngineTerminatedError("Engine not initialized")
    result = engine.play(board, chess.engine.Limit(time=0.1))
    return result.move

def get_game_result(board):
    if board.is_checkmate():
        return "checkmate"
    elif board.is_stalemate():
        return "stalemate"
    elif board.is_insufficient_material():
        return "insufficient material"
    elif board.is_fifty_moves():
        return "fifty-move rule"
    elif board.is_repetition():
        return "threefold repetition"
    else:
        return "draw"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)