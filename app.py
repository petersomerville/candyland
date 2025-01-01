# app.py
from flask import Flask, render_template, jsonify, request, session
from random import shuffle
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

class CandylandGame:
    def __init__(self):
        # Define the board spaces
        self.spaces = [
            {'type': 'regular', 'color': 'red'},
            {'type': 'regular', 'color': 'purple'},
            {'type': 'regular', 'color': 'yellow'},
            {'type': 'regular', 'color': 'blue'},
            {'type': 'regular', 'color': 'orange'},
            {'type': 'regular', 'color': 'green'},
            {'type': 'special', 'name': 'Peppermint Forest'},
            # Add more spaces to match the real board...
        ]
        
        # Create the deck of cards
        self.create_deck()
        
        # Player positions (0-based index on board)
        self.players = {
            'player1': 0,
            'player2': 0
        }
        
        self.current_player = 'player1'
    
    def create_deck(self):
        """Create and shuffle the deck of cards"""
        self.deck = []
        colors = ['red', 'purple', 'yellow', 'blue', 'orange', 'green']
        # Add single color cards
        for color in colors:
            self.deck.extend([color] * 6)  # 6 cards of each color
        
        # Add special cards
        special_locations = ['Peppermint Forest', 'Lollipop Woods', 'Gummy Hills']
        self.deck.extend(special_locations)
        
        shuffle(self.deck)
    
    def draw_card(self):
        """Draw a card from the deck, reshuffle if empty"""
        if not self.deck:
            self.create_deck()
        return self.deck.pop()
    
    def move_player(self, card):
        """Move the current player based on the drawn card"""
        current_pos = self.players[self.current_player]
        
        if isinstance(card, str) and card in ['Peppermint Forest', 'Lollipop Woods', 'Gummy Hills']:
            # Find the next special location
            for i in range(current_pos + 1, len(self.spaces)):
                if self.spaces[i]['type'] == 'special' and self.spaces[i]['name'] == card:
                    self.players[self.current_player] = i
                    break
        else:
            # Move to next matching color
            for i in range(current_pos + 1, len(self.spaces)):
                if self.spaces[i]['type'] == 'regular' and self.spaces[i]['color'] == card:
                    self.players[self.current_player] = i
                    break
        
        # Switch players
        self.current_player = 'player2' if self.current_player == 'player1' else 'player1'

# Flask routes
@app.route('/')
def home():
    """Render the game board"""
    return render_template('game.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    """Start a new game"""
    game = CandylandGame()
    session['game'] = game.__dict__
    return jsonify({'status': 'success'})

@app.route('/draw_card', methods=['POST'])
def draw_card():
    """Draw a card and move player"""
    game = CandylandGame()
    game.__dict__ = session['game']
    
    card = game.draw_card()
    game.move_player(card)
    
    session['game'] = game.__dict__
    return jsonify({
        'card': card,
        'players': game.players,
        'current_player': game.current_player
    })

if __name__ == '__main__':
    app.run(debug=True)