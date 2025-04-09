from flask import Flask, request, redirect, url_for, render_template
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
            if i == 0:
                board.append(Square(i, color=None, is_start=True))
            elif i == total_spaces - 1:
                board.append(Square(i, color="red", is_finish=True))
            else:
                color = COLORS[(i-1) % len(COLORS)]
                board.append(Square(i, color=color))

        # Mark picture spaces at fixed indices:
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
        self.card_type = card_type  # 'single', 'double', or 'picture'
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
        for color in COLORS:
            for _ in range(6):
                self.draw_pile.append(Card('single', color))
        for color in COLORS:
            for _ in range(2):
                self.draw_pile.append(Card('double', color))
        for pic in PICTURE_CARDS:
            self.draw_pile.append(Card('picture', pic))
        # Total cards: 6*6 + 2*6 + 6 = 54

    def shuffle(self):
        random.shuffle(self.draw_pile)

    def draw(self):
        if not self.draw_pile:
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
        self.messages = []

    def init_players(self, num_players, names):
        for i in range(num_players):
            pawn_color = COLORS[i % len(COLORS)]
            name = names[i] if i < len(names) and names[i] else f"Player {i+1}"
            self.players.append(Player(i+1, pawn_color, name))

    def get_current_player(self):
        return self.players[self.current_player_index]

    def advance_turn(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def move_player(self, player, card):
        orig_position = player.position
        new_position = orig_position
        board = self.board.spaces

        if card.card_type in ['single', 'double']:
            needed = 1 if card.card_type == 'single' else 2
            found = 0
            for pos in range(orig_position + 1, len(board)):
                if board[pos].color == card.value:
                    found += 1
                    if found == needed:
                        new_position = pos
                        break
        elif card.card_type == 'picture':
            for pos in range(len(board)):
                if board[pos].is_picture and board[pos].picture_name == card.value:
                    new_position = pos
                    break

        move_msg = f"Player {player.name} moves from {orig_position} to {new_position} due to {card}."
        self.messages.append(move_msg)
        player.position = new_position

        current_square = board[player.position]
        if current_square.is_shortcut_start and card.card_type in ['single', 'double']:
            shortcut_msg = f"Player {player.name} took shortcut from {player.position} to {current_square.shortcut_target}."
            self.messages.append(shortcut_msg)
            player.position = current_square.shortcut_target

        current_square = board[player.position]
        if current_square.is_lose_turn:
            player.skip_turn = True
            self.messages.append(f"Player {player.name} landed on Molasses Swamp! Lose next turn.")

        if player.position >= board[-1].index:
            self.status = "Finished"
            self.winner = player

    def play_turn(self):
        player = self.get_current_player()
        if player.skip_turn:
            self.messages.append(f"Player {player.name} loses a turn.")
            player.skip_turn = False
            self.advance_turn()
            return None
        card = self.deck.draw()
        self.messages.append(f"Player {player.name} drew {card}.")
        self.move_player(player, card)
        if self.status == "Finished":
            return card
        self.advance_turn()
        return card

# ---------- Global Game Instance ----------
game = None

# ---------- Flask Routes ----------
@app.route("/", methods=["GET"])
def setup():
    return render_template("setup.html")

@app.route("/start", methods=["POST"])
def start():
    global game
    num_players = int(request.form.get("num_players"))
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
    return render_template("game.html", game=game)

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
