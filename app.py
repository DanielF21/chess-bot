from flask import Flask, request, jsonify
from flask_cors import CORS
import chess
import chess.engine
import os
import threading
import logging

app = Flask(__name__)
CORS(app)

logging.basicConfig(level=logging.INFO)

current_dir = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(current_dir, "model.pb.gz")

if not os.path.exists(model_path):
    raise FileNotFoundError(f"Model file not found: {model_path}")

lc0_command = ["lc0", f"--weights={model_path}"]

# The engine process is the ONLY thing that outlives a request, and it holds no
# game state: every call passes a full board. There is deliberately no module
# level `board` any more. That global meant every visitor to the site shared one
# game, so one person's move made another person's next move illegal.
_engine = None
_engine_lock = threading.Lock()


def _spawn_engine():
    return chess.engine.SimpleEngine.popen_uci(lc0_command)


def get_engine():
    global _engine
    with _engine_lock:
        if _engine is None:
            _engine = _spawn_engine()
        return _engine


def restart_engine():
    global _engine
    with _engine_lock:
        if _engine is not None:
            try:
                _engine.quit()
            except Exception:
                pass
        _engine = _spawn_engine()
        return _engine


def choose_move(board):
    """One engine, possibly several gunicorn threads. python-chess engine
    objects are not thread safe, so serialise access. Each call is ~0.1s."""
    with _engine_lock:
        engine = _engine
        if engine is None:
            raise chess.engine.EngineTerminatedError("Engine not initialized")
        return engine.play(board, chess.engine.Limit(time=0.1)).move


@app.route('/move', methods=['POST'])
def make_move():
    data = request.get_json(silent=True) or {}
    fen = data.get('fen')
    move_uci = data.get('move')

    if not fen:
        return jsonify({"error": "No fen provided"}), 400
    if not move_uci:
        return jsonify({"error": "No move provided"}), 400

    try:
        board = chess.Board(fen)
    except ValueError:
        return jsonify({"error": "Invalid fen"}), 400

    try:
        move = chess.Move.from_uci(move_uci)
    except ValueError:
        return jsonify({"error": "Invalid move format"}), 400

    if move not in board.legal_moves:
        return jsonify({"error": "Illegal move"}), 400

    board.push(move)

    if board.is_game_over():
        return jsonify({
            "player_move": move_uci,
            "ai_move": None,
            "fen": board.fen(),
            "game_over": True,
            "result": get_game_result(board),
        })

    get_engine()
    ai_move = None
    for attempt in range(2):
        try:
            ai_move = choose_move(board)
            break
        except chess.engine.EngineTerminatedError:
            logging.warning("Engine terminated. Attempting to restart...")
            try:
                restart_engine()
            except Exception as e:
                logging.error(f"Error restarting Lc0 engine: {e}")
                return jsonify({"error": "Chess engine unavailable"}), 503

    if ai_move is None:
        return jsonify({"error": "Chess engine unavailable"}), 503

    board.push(ai_move)
    over = board.is_game_over()
    return jsonify({
        "player_move": move_uci,
        "ai_move": ai_move.uci(),
        "fen": board.fen(),
        "game_over": over,
        "result": get_game_result(board) if over else None,
    })


@app.route('/reset', methods=['POST'])
def reset_game():
    # Kept only so older cached clients do not error. The server holds no game
    # state now, so there is nothing to reset, and critically this no longer
    # restarts the engine on every page load.
    return jsonify({"status": "Game reset"})


@app.route('/board', methods=['GET'])
def get_board():
    # Was a read of the shared board. Now a warm-up and health probe: the first
    # call spawns the engine so the first real move is not the slow one.
    try:
        get_engine()
        return jsonify({"status": "ok"})
    except Exception as e:
        logging.error(f"Engine warm-up failed: {e}")
        return jsonify({"status": "engine unavailable"}), 503


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
