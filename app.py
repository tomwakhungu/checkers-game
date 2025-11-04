from flask import Flask, render_template, jsonify, request
import json

app = Flask(__name__)

class CheckersGame:
    def __init__(self):
        self.board = self.initialize_board()
        self.current_player = 'red'
        self.selected_piece = None
        
    def initialize_board(self):
        """Initialize an 8x8 checkers board"""
        board = [[None for _ in range(8)] for _ in range(8)]
        
        # Place red pieces (top)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'red'
        
        # Place black pieces (bottom)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'black'
        
        return board
    
    def get_valid_moves(self, row, col):
        """Get all valid moves for a piece at given position"""
        if self.board[row][col] is None:
            return []
        
        piece = self.board[row][col]
        moves = []
        
        # Determine move directions based on piece color
        if piece == 'red' or piece == 'red_king':
            directions = [(1, -1), (1, 1)]
        if piece == 'black' or piece == 'black_king':
            directions = [(-1, -1), (-1, 1)]
        if piece.endswith('_king'):
            directions = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        
        # Check normal moves
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if self.board[new_row][new_col] is None:
                    moves.append({'row': new_row, 'col': new_col, 'type': 'normal'})
        
        # Check jump moves
        jump_moves = self.get_jump_moves(row, col, piece)
        moves.extend(jump_moves)
        
        return moves
    
    def get_jump_moves(self, row, col, piece):
        """Get all valid jump moves for a piece"""
        jumps = []
        
        # All possible jump directions
        if piece == 'red' or piece == 'red_king':
            directions = [(2, -2), (2, 2)]
        if piece == 'black' or piece == 'black_king':
            directions = [(-2, -2), (-2, 2)]
        if piece.endswith('_king'):
            directions = [(2, -2), (2, 2), (-2, -2), (-2, 2)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            mid_row, mid_col = row + dr//2, col + dc//2
            
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                mid_piece = self.board[mid_row][mid_col]
                if (self.board[new_row][new_col] is None and 
                    mid_piece is not None and 
                    not mid_piece.startswith(piece.split('_')[0])):
                    jumps.append({
                        'row': new_row, 
                        'col': new_col, 
                        'type': 'jump',
                        'captured': {'row': mid_row, 'col': mid_col}
                    })
        
        return jumps
    
    def make_move(self, from_row, from_col, to_row, to_col):
        """Execute a move and return result"""
        piece = self.board[from_row][from_col]
        
        if piece is None or not piece.startswith(self.current_player):
            return {'success': False, 'message': 'Invalid piece selection'}
        
        valid_moves = self.get_valid_moves(from_row, from_col)
        target_move = None
        
        for move in valid_moves:
            if move['row'] == to_row and move['col'] == to_col:
                target_move = move
                break
        
        if target_move is None:
            return {'success': False, 'message': 'Invalid move'}
        
        # Execute the move
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None
        
        # Handle capture
        if target_move['type'] == 'jump':
            cap = target_move['captured']
            self.board[cap['row']][cap['col']] = None
        
        # Check for king promotion
        if piece == 'red' and to_row == 7:
            self.board[to_row][to_col] = 'red_king'
        elif piece == 'black' and to_row == 0:
            self.board[to_row][to_col] = 'black_king'
        
        # Switch player
        self.current_player = 'black' if self.current_player == 'red' else 'red'
        
        return {'success': True, 'board': self.board, 'current_player': self.current_player}

# Global game instance
game = CheckersGame()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/game/state')
def game_state():
    return jsonify({
        'board': game.board,
        'current_player': game.current_player
    })

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    global game
    game = CheckersGame()
    return jsonify({'success': True, 'board': game.board, 'current_player': game.current_player})

@app.route('/api/game/moves', methods=['POST'])
def get_moves():
    data = request.json
    row = data.get('row')
    col = data.get('col')
    moves = game.get_valid_moves(row, col)
    return jsonify({'moves': moves})

@app.route('/api/game/move', methods=['POST'])
def make_move():
    data = request.json
    from_row = data.get('from_row')
    from_col = data.get('from_col')
    to_row = data.get('to_row')
    to_col = data.get('to_col')
    
    result = game.make_move(from_row, from_col, to_row, to_col)
    return jsonify(result)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
