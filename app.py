from flask import Flask, request, redirect, url_for, render_template_string, flash
import random

app = Flask(__name__)
app.secret_key = 'candyland-secret-key'  # for flash messages

# ---------- Game Models and Logic ----------

COLORS = ['red', 'purple', 'yellow', 'blue', 'orange', 'green']
PICTURE_CARDS = [
    "Peppermint Forest", 
    "Gumdrop Mountain",
    "Lollipop Woods",
    "Ice Cream Sea",
    "Gingerbread Tree",
    "Gloppy the Molasses Monster"
]

class Square:
    def __init__(self, index, color=None, is_start=False, is_finish=False,
                 is_picture=False, picture_name=None, is_shortcut_start=False,
                 shortcut_target=None, is_lose_turn=False):
        self.index = index
        self.color = color
        self.is_start = is_start
        self.is_finish = is_finish
        self.is_picture = is_picture
        self.picture_name = picture_name
        self.is_shortcut_start = is_shortcut_start
        self.shortcut_target = shortcut_target
        self.is_lose_turn = is_lose_turn

class Board:
    def __init__(self):
        self.spaces = self.generate_board()

    def generate_board(self):
        board = []
        total_spaces = 134

        # Create basic board with repeating colors
        for i in range(total_spaces):
            # first square is the START square
            if i == 0:
                board.append(Square(i, color=None, is_start=True))
            # last square is the finish square, now red
            elif i == total_spaces - 1:
                board.append(Square(i, color="red", is_finish=True))
            else:
                color = COLORS[(i-1) % len(COLORS)]
                board.append(Square(i, color=color))

        # Mark picture spaces at fixed indices as an example:
        picture_positions = {
            10: "Peppermint Forest",
            30: "Gumdrop Mountain",
            60: "Lollipop Woods",
            90: "Ice Cream Sea",
            110: "Gingerbread Tree",
            120: "Gloppy the Molasses Monster"  # Also the lose-turn square
        }
        for pos, name in picture_positions.items():
            if pos < total_spaces:
                board[pos].is_picture = True
                board[pos].picture_name = name
                # Mark Gloppy's space as lose turn (Molasses Swamp) if applicable
                if name == "Gloppy the Molasses Monster":
                    board[pos].is_lose_turn = True

        # Example shortcut: if a player lands exactly on space 50, move to space 70.
        shortcut_start = 50
        shortcut_end = 70
        if shortcut_start < total_spaces and shortcut_end < total_spaces:
            board[shortcut_start].is_shortcut_start = True
            board[shortcut_start].shortcut_target = shortcut_end

        return board

class Card:
    def __init__(self, card_type, value):
        # card_type is one of: 'single', 'double', 'picture'
        # For 'single' and 'double', value is a color (lowercase string)
        # For 'picture', value is the picture name.
        self.card_type = card_type
        self.value = value

    def __repr__(self):
        if self.card_type in ['single', 'double']:
            return f"{self.card_type.upper()} {self.value.upper()}"
        else:
            return f"PICTURE: {self.value}"

class Deck:
    def __init__(self):
        self.draw_pile = []
        self.discard_pile = []
        self.build_deck()
        self.shuffle()

    def build_deck(self):
        # Add single color cards (6 of each)
        for color in COLORS:
            for _ in range(6):
                self.draw_pile.append(Card('single', color))
        # Add double color cards (2 of each)
        for color in COLORS:
            for _ in range(2):
                self.draw_pile.append(Card('double', color))
        # Add picture cards (1 of each)
        for pic in PICTURE_CARDS:
            self.draw_pile.append(Card('picture', pic))
        # Total cards should be 54 (6*6 + 2*6 + 6)

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self):
        if not self.draw_pile:
            # Reshuffle discard pile into draw pile if empty.
            self.draw_pile = self.discard_pile.copy()
            self.discard_pile = []
            self.shuffle()
        card = self.draw_pile.pop(0)
        self.discard_pile.append(card)
        return card

class Player:
    def __init__(self, pid, pawn_color, name):
        self.pid = pid
        self.pawn_color = pawn_color
        self.name = name
        self.position = 0
        self.skip_turn = False

class Game:
    def __init__(self, num_players, names):
        self.status = "Setup"
        self.board = Board()
        self.deck = Deck()
        self.players = []
        self.current_player_index = 0
        self.winner = None
        self.init_players(num_players, names)
        self.status = "InProgress"
        self.messages = []  # for game event messages

    def init_players(self, num_players, names):
        # Assign pawn colors from the COLORS list (cycle if needed) and use provided names.
        for i in range(num_players):
            pawn_color = COLORS[i % len(COLORS)]
            name = names[i] if i < len(names) and names[i] else f"Player {i+1}"
            self.players.append(Player(i+1, pawn_color, name))

    def get_current_player(self):
        return self.players[self.current_player_index]

    def advance_turn(self):
        # move to next player in sequence.
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def move_player(self, player, card):
        orig_position = player.position
        new_position = orig_position
        board = self.board.spaces

        if card.card_type in ['single', 'double']:
            needed = 1 if card.card_type == 'single' else 2
            found = 0
            # Search forward from the next space
            for pos in range(orig_position + 1, len(board)):
                if board[pos].color == card.value:
                    found += 1
                    if found == needed:
                        new_position = pos
                        break
            # Edge case: if no matching space found, player does not move.
        elif card.card_type == 'picture':
            # Move directly to the picture space with that name.
            for pos in range(len(board)):
                if board[pos].is_picture and board[pos].picture_name == card.value:
                    new_position = pos
                    break

        # Update player position and record move message.
        move_msg = f"Player {player.name} moves from {orig_position} to {new_position} due to {card}."
        self.messages.append(move_msg)
        player.position = new_position

        # Check for shortcut: Only trigger if move was due to color card (not picture card)
        current_square = board[player.position]
        if current_square.is_shortcut_start and card.card_type in ['single', 'double']:
            shortcut_msg = f"Player {player.name} took shortcut from {player.position} to {current_square.shortcut_target}."
            self.messages.append(shortcut_msg)
            player.position = current_square.shortcut_target
            # Do not chain shortcuts further

        # Check for lose turn
        current_square = board[player.position]
        if current_square.is_lose_turn:
            player.skip_turn = True
            self.messages.append(f"Player {player.name} landed on Molasses Swamp! Lose next turn.")

        # Check win condition: if player has reached or passed the finish square.
        if player.position >= board[-1].index:
            self.status = "Finished"
            self.winner = player

    def play_turn(self):
        player = self.get_current_player()
        # Check if player should skip turn
        if player.skip_turn:
            self.messages.append(f"Player {player.name} loses a turn.")
            player.skip_turn = False
            self.advance_turn()
            return None  # indicate no card drawn

        card = self.deck.draw()
        self.messages.append(f"Player {player.name} drew {card}.")
        self.move_player(player, card)

        # Check if game finished
        if self.status == "Finished":
            return card

        # After move, advance to next player.
        self.advance_turn()
        return card

# ---------- Global Game Instance ----------
game = None

# ---------- Flask Routes ----------

# Helper HTML templates (using inline templates for simplicity)
setup_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Candyland Setup</title>
  <script>
    function updatePlayerFields() {
      var numPlayers = document.querySelector('input[name="num_players"]:checked').value;
      for (var i = 1; i <= 4; i++) {
        document.getElementById('player' + i + '_div').style.display = (i <= numPlayers) ? 'block' : 'none';
      }
    }
    window.onload = updatePlayerFields;
  </script>
</head>
<body>
  <h1>Welcome to Candyland!</h1>
  <form action="{{ url_for('start') }}" method="post">
    <label>Select Number of Players:</label><br>
    <input type="radio" name="num_players" value="2" required onchange="updatePlayerFields()">2<br>
    <input type="radio" name="num_players" value="3" onchange="updatePlayerFields()">3<br>
    <input type="radio" name="num_players" value="4" onchange="updatePlayerFields()">4<br><br>
    <div id="player1_div">
      <label>Player 1 Name:</label>
      <input type="text" name="player1" required><br>
    </div>
    <div id="player2_div">
      <label>Player 2 Name:</label>
      <input type="text" name="player2" required><br>
    </div>
    <div id="player3_div" style="display:none;">
      <label>Player 3 Name:</label>
      <input type="text" name="player3"><br>
    </div>
    <div id="player4_div" style="display:none;">
      <label>Player 4 Name:</label>
      <input type="text" name="player4"><br>
    </div><br>
    <input type="submit" value="Start Game">
  </form>
</body>
</html>
"""

game_template = """
<!DOCTYPE html>
<html>
<head>
  <title>Candyland Game</title>
  <style>
    .board { display: flex; flex-wrap: wrap; width: 1200px; }
    .square { 
              width: 80px; 
              height: 80px; 
              border: 1px solid #000; 
              display: flex; 
              align-items: center; 
              justify-content: center; 
              font-size: 16px; 
            }
    .pawn { 
              border-radius: 50%; 
              width: 40px; 
              height: 40px; 
              border: 1px solid black;  /* added border */
            }
  </style>
</head>
<body>
  <h1>Candyland</h1>
  
  <h3>Board:</h3>
  <div class="board">
  {% for square in game.board.spaces %}
    <div class="square" style="background-color: {{ square.color if square.color else '#ccc' }};">
      {% if square.is_start %}START{% elif square.is_finish %}END{% elif square.is_picture %}{{ square.picture_name[0:3] }}{% else %}{{ square.index }}{% endif %}
      {% for p in game.players %}
        {% if p.position == square.index %}
          <div class="pawn" style="background-color: {{ p.pawn_color }};"></div>
        {% endif %}
      {% endfor %}
    </div>
  {% endfor %}
  </div>
  
  {% if game.status == "Finished" %}
    <h2>{{ game.winner.name }} Wins!</h2>
    <form action="{{ url_for('reset') }}" method="post">
      <input type="submit" value="Play Again">
    </form>
  {% else %}
    <h3>Current Turn: {{ game.get_current_player().name }}</h3>
    <form action="{{ url_for('draw') }}" method="post">
      <input type="submit" value="Draw Card">
    </form>
  {% endif %}
  
  <h3>Messages (last 6):</h3>
  <ul>
    {% for msg in game.messages[-6:] %}
      <li>{{ msg }}</li>
    {% endfor %}
  </ul>
  
  <h3>Player Positions:</h3>
  <ul>
    {% for p in game.players %}
      <li>{{ p.name }} ({{ p.pawn_color }}): Position {{ p.position }}
        {% if p.skip_turn %} - Loses Next Turn{% endif %}
      </li>
    {% endfor %}
  </ul>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def setup():
    return render_template_string(setup_template)

@app.route("/start", methods=["POST"])
def start():
    global game
    num_players = int(request.form.get("num_players"))
    # Retrieve names from request. Only required for players up to num_players.
    names = []
    for i in range(1, num_players + 1):
        name = request.form.get(f"player{i}")
        names.append(name)
    game = Game(num_players, names)
    return redirect(url_for("game_route"))

@app.route("/game", methods=["GET"])
def game_route():
    if game is None:
        return redirect(url_for("setup"))
    return render_template_string(game_template, game=game)

@app.route("/draw", methods=["POST"])
def draw():
    global game
    if game is None or game.status == "Finished":
        return redirect(url_for("game_route"))
    game.play_turn()
    return redirect(url_for("game_route"))

@app.route("/reset", methods=["POST"])
def reset():
    global game
    game = None
    return redirect(url_for("setup"))

if __name__ == '__main__':
    app.run(debug=True)
