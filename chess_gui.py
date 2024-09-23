import os
import sys
import chess
import chess.engine
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QDialog, QGridLayout
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QColor, QPen
from PyQt5.QtCore import Qt, QSize, QRect, QPropertyAnimation, QEasingCurve, QPoint, QTimer

class PromotionDialog(QDialog):
    def __init__(self, parent=None, color=chess.WHITE):
        super().__init__(parent)
        self.setWindowTitle("Choose Promotion")
        layout = QGridLayout()
        self.buttons = {}
        pieces = ['q', 'r', 'b', 'n']
        piece_names = {'q': 'Queen', 'r': 'Rook', 'b': 'Bishop', 'n': 'Knight'}
        for i, piece in enumerate(pieces):
            button = QPushButton()
            pixmap = QPixmap(f"images/{'white' if color else 'black'}_{piece}.png")
            icon = QIcon(pixmap)
            button.setIcon(icon)
            button.setIconSize(QSize(50, 50))
            button.setText(piece_names[piece])  # Add text label
            button.clicked.connect(lambda _, p=piece: self.accept_promotion(p))
            layout.addWidget(button, 0, i)
            self.buttons[piece] = button
        self.setLayout(layout)
        self.promotion_piece = None

    def accept_promotion(self, piece):
        self.promotion_piece = piece
        self.accept()

class ChessPiece(QLabel):
    def __init__(self, parent, piece, square):
        super().__init__(parent)
        self.piece = piece
        self.square = square
        pixmap = QPixmap(f"images/{'white' if piece.color else 'black'}_{chess.piece_name(piece.piece_type)}.gif")
        scaled_pixmap = pixmap.scaled(50, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled_pixmap)
        self.setFixedSize(50, 50)
        self.move(chess.square_file(square) * 50, (7 - chess.square_rank(square)) * 50)

class ChessGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.board = chess.Board()
        self.pieces = {}
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.player_color = chess.WHITE  # Player is white, AI is black
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model.pth")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Maia model file not found: {model_path}")
        
        lc0_command = ["lc0", f"--weights={model_path}"]
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(lc0_command)
        except Exception as e:
            print(f"Error initializing Lc0 engine: {e}")
            sys.exit(1)
        
        self.initUI()
        self.update_pieces()

    def initUI(self):
        self.setWindowTitle('Chess GUI')
        self.setGeometry(100, 100, 600, 500)

        layout = QHBoxLayout()

        board_layout = QVBoxLayout()
        self.board_label = QLabel(self)
        self.board_label.setFixedSize(400, 400)
        board_layout.addWidget(self.board_label)

        button_layout = QHBoxLayout()
        reset_button = QPushButton('Reset', self)
        reset_button.clicked.connect(self.reset_game)
        button_layout.addWidget(reset_button)

        board_layout.addLayout(button_layout)
        layout.addLayout(board_layout)

        self.move_list = QListWidget(self)
        layout.addWidget(self.move_list)

        self.setLayout(layout)
        self.update_board()

    def update_board(self):
        pixmap = QPixmap(400, 400)
        self.draw_board(pixmap)
        self.board_label.setPixmap(pixmap)

    def draw_board(self, pixmap):
        painter = QPainter(pixmap)
        for i in range(8):
            for j in range(8):
                x, y = j * 50, i * 50
                color = QColor(240, 217, 181) if (i + j) % 2 == 0 else QColor(181, 136, 99)
                painter.fillRect(x, y, 50, 50, color)

        if self.selected_square:
            painter.fillRect(chess.square_file(self.selected_square) * 50,
                             (7 - chess.square_rank(self.selected_square)) * 50,
                             50, 50, QColor(124, 252, 0, 127))

        pen = QPen(QColor(124, 252, 0))
        pen.setWidth(3)
        painter.setPen(pen)
        for move in self.legal_moves:
            x = chess.square_file(move.to_square) * 50
            y = (7 - chess.square_rank(move.to_square)) * 50
            painter.drawRect(x, y, 50, 50)

        painter.end()

    def update_pieces(self):
        for square in chess.SQUARES:
            if square in self.pieces:
                self.pieces[square].hide()
                self.pieces[square].deleteLater()
                del self.pieces[square]
            piece = self.board.piece_at(square)
            if piece:
                self.pieces[square] = ChessPiece(self.board_label, piece, square)
                self.pieces[square].show()

    def mousePressEvent(self, event):
        if not self.board_label.geometry().contains(event.pos()) or self.board.turn != self.player_color:
            return

        x = event.x() - self.board_label.x()
        y = event.y() - self.board_label.y()
        file = x // 50
        rank = 7 - (y // 50)
        square = chess.square(file, rank)

        if self.selected_square is None:
            piece = self.board.piece_at(square)
            if piece and piece.color == self.board.turn:
                self.selected_square = square
                self.legal_moves = [move for move in self.board.legal_moves if move.from_square == square]
        else:
            # Check for regular move
            move = chess.Move(self.selected_square, square)
            
            # Check for promotion move
            if self.is_promotion(move):
                promotion_moves = [
                    chess.Move(self.selected_square, square, promotion=chess.QUEEN),
                    chess.Move(self.selected_square, square, promotion=chess.ROOK),
                    chess.Move(self.selected_square, square, promotion=chess.BISHOP),
                    chess.Move(self.selected_square, square, promotion=chess.KNIGHT)
                ]
                legal_promotion_moves = [m for m in promotion_moves if m in self.board.legal_moves]
                
                if legal_promotion_moves:
                    promotion = self.get_promotion()
                    if promotion:
                        move = chess.Move(self.selected_square, square, promotion=promotion)
                    else:
                        self.selected_square = None
                        self.legal_moves = []
                        self.update_board()
                        return
                else:
                    print(f"No legal promotion moves for {move}")
                    self.selected_square = None
                    self.legal_moves = []
                    self.update_board()
                    return
            
            if move in self.board.legal_moves:
                self.last_move = move
                self.animate_move(move)
                QTimer.singleShot(300, self.after_move)
            else:
                print(f"Move {move} is not legal")
            
            self.selected_square = None
            self.legal_moves = []

        self.update_board()

    def is_promotion(self, move):
        piece = self.board.piece_at(move.from_square)
        print(f"Checking promotion for piece: {piece} at {move.from_square} to {move.to_square}")  # Debugging
        if piece.piece_type == chess.PAWN:
            if piece.color == chess.WHITE and chess.square_rank(move.to_square) == 7:
                print("White pawn promotion detected")  # Debugging
                return True
            elif piece.color == chess.BLACK and chess.square_rank(move.to_square) == 0:
                print("Black pawn promotion detected")  # Debugging
                return True
        return False

    def get_promotion(self):
        dialog = PromotionDialog(self, self.board.turn)
        if dialog.exec_():
            return {'q': chess.QUEEN, 'r': chess.ROOK, 'b': chess.BISHOP, 'n': chess.KNIGHT}[dialog.promotion_piece]
        return None

    def animate_move(self, move):
        piece = self.pieces[move.from_square]
        start = piece.pos()
        end = QPoint(chess.square_file(move.to_square) * 50, (7 - chess.square_rank(move.to_square)) * 50)
        
        animation = QPropertyAnimation(piece, b"pos")
        animation.setDuration(300)
        animation.setStartValue(start)
        animation.setEndValue(end)
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        animation.start()

    def after_move(self):
        if self.last_move:
            san = self.board.san(self.last_move)
            self.board.push(self.last_move)
            self.move_list.addItem(san)
            self.last_move = None
        self.update_pieces()
        self.update_board()
        
        if self.board.turn != self.player_color:
            QTimer.singleShot(500, self.make_ai_move)

    def make_ai_move(self):
        try:
            result = self.engine.play(self.board, chess.engine.Limit(time=0.1))
            self.last_move = result.move
            self.animate_move(result.move)
            QTimer.singleShot(300, self.after_move)
        except Exception as e:
            print(f"Error making AI move: {e}")

    def reset_game(self):
        self.board.reset()
        self.selected_square = None
        self.legal_moves = []
        self.last_move = None
        self.update_board()
        self.update_pieces()
        self.move_list.clear()

    def closeEvent(self, event):
        self.engine.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    try:
        ex = ChessGUI()
        ex.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Error initializing Chess GUI: {e}")
        sys.exit(1)
