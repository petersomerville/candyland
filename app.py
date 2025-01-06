from flask import Flask, render_template, jsonify, request, session
from random import shuffle
import json

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for session management

class CandylandGame:
    def __init__(self):
        self.spaces = [
            {'type': 'regular', 'color': 'red'},
            {'type': 'regular', 'color': 'purple'},
            {'type': 'regular', 'color': 'yellow'},
            {'type': 'regular', 'color': 'blue'},
            {'type': 'regular', 'color': 'orange'},
            {'type': 'regular', 'color': 'green'},
            {'type': 'special', 'name': 'Peppermint Forest'},
        ]
        self.create_deck()
        self.players = {
            'player1': 0,
            'player2': 0,
            'player3': 0,
            'player4': 0
        }
        self.current_player = 'player1'

    def create_deck(self):
        self.deck = []
        colors = ['red', 'purple', 'yellow', 'blue', 'orange', 'green']
        for color in colors:
            self.deck.extend([color] * 6)
        special_locations = ['Peppermint Forest', 'Lollipop Woods', 'Gummy Hills']
        self.deck.extend(special_locations)
        shuffle(self.deck)

    def draw_card(self):
        if not self.deck:
            self.create_deck()
        return self.deck.pop()

    def move_player(self, card):
        current_pos = self.players[self.current_player]

        # Ensure the player advances to the next matching space
        for i in range(current_pos + 1, len(self.spaces)):
            if self.spaces[i]['type'] == 'regular' and self.spaces[i]['color'] == card:
                self.players[self.current_player] = i
                break

        player_list = list(self.players.keys())
        next_index = (player_list.index(self.current_player) + 1) % len(player_list)
        self.current_player = player_list[next_index]

@app.route('/')
def home():
    return render_template('game.html')

@app.route('/new_game', methods=['POST'])
def new_game():
    game = CandylandGame()
    session['game'] = game.__dict__
    return jsonify({
        'status': 'success',
        'players': game.players,
        'current_player': game.current_player
    })

@app.route('/draw_card', methods=['POST'])
def draw_card():
    game_data = session.get('game')
    if game_data:
        game = CandylandGame()
        game.__dict__.update(game_data)
        card = game.draw_card()
        game.move_player(card)
        session['game'] = game.__dict__
        return jsonify({
            'card': card,
            'players': game.players,
            'current_player': game.current_player
        })
    else:
        return jsonify({'error': 'Game not initialized'}), 400

if __name__ == '__main__':
    app.run(debug=True)
