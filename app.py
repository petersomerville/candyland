import random

from flask import Flask, request, redirect, url_for, render_template, flash


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
            # Use title case for better readability
            return f"{self.card_type.title()} {self.value.title()}"
        else:
            # Keep picture names as they are
            return f"Picture: {self.value}"

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
            # Optional: Add a message indicating reshuffle
            # self.messages.append("Deck reshuffled.") # Need access to game messages here
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
        # --- ADD THIS LINE ---
        self.last_card = None # Initialize the last drawn card attribute

    def init_players(self, num_players, names):
        pawn_colors = ['#FF0000', '#0000FF', '#FFFF00', '#008000', '#FFA500', '#800080'] # Example distinct colors
        for i in range(num_players):
            # Use more distinct pawn colors if possible
            pawn_color = pawn_colors[i % len(pawn_colors)]
            name = names[i] if i < len(names) and names[i] else f"Player {i+1}"
            self.players.append(Player(i+1, pawn_color, name))

    def get_current_player(self):
        return self.players[self.current_player_index]

    def advance_turn(self):
        # Find the next player who doesn't have skip_turn set
        next_player_index = (self.current_player_index + 1) % len(self.players)
        while self.players[next_player_index].skip_turn:
            self.messages.append(f"Player {self.players[next_player_index].name} loses a turn.")
            self.players[next_player_index].skip_turn = False # Reset skip flag
            next_player_index = (next_player_index + 1) % len(self.players)
            # Safety break in case all players somehow get skip_turn
            if next_player_index == self.current_player_index and self.players[next_player_index].skip_turn:
                 self.messages.append("All players skipping turn? Resetting skip for current player.")
                 self.players[next_player_index].skip_turn = False # Prevent infinite loop

        self.current_player_index = next_player_index


    def move_player(self, player, card):
        orig_position = player.position
        new_position = orig_position
        board = self.board.spaces
        found_target = False # Flag to check if a valid move was found

        if card.card_type in ['single', 'double']:
            needed = 1 if card.card_type == 'single' else 2
            found = 0
            # Start searching from the square *after* the current one
            for pos in range(orig_position + 1, len(board)):
                # Don't count the finish square as a colored square for movement
                if not board[pos].is_finish and board[pos].color == card.value:
                    found += 1
                    if found == needed:
                        new_position = pos
                        found_target = True
                        break
            # If the required squares weren't found before the end, move to finish
            if not found_target:
                 new_position = board[-1].index # Move to finish if color not found ahead
                 found_target = True # Consider this a valid move completion

        elif card.card_type == 'picture':
            # Picture cards always move forward to the specific picture square
            for pos in range(len(board)): # Search the whole board
                if board[pos].is_picture and board[pos].picture_name == card.value:
                    new_position = pos
                    found_target = True
                    break

        # Only update position and messages if a valid target was found
        if found_target:
            move_msg = f"{player.name} drew {card}. Moves from {orig_position} to {new_position}."
            self.messages.append(move_msg)
            player.position = new_position

            # Check for special square effects *after* the initial move
            current_square = board[player.position]

            # Handle shortcuts only if not moving to the finish line directly
            if current_square.is_shortcut_start and not current_square.is_finish:
                shortcut_msg = f"{player.name} took shortcut from {player.position} to {current_square.shortcut_target}!"
                self.messages.append(shortcut_msg)
                player.position = current_square.shortcut_target
                # Re-check the square after the shortcut
                current_square = board[player.position]

            # Handle lose turn only if not moving to the finish line directly
            if current_square.is_lose_turn and not current_square.is_finish:
                player.skip_turn = True
                self.messages.append(f"{player.name} landed on {current_square.picture_name}! Lose next turn.")

            # Check for win condition
            if player.position >= board[-1].index:
                self.status = "Finished"
                self.winner = player
                self.messages.append(f"{player.name} reached Candy Castle and wins!")
        else:
             # This case should ideally not happen with the current logic,
             # but good for robustness
             self.messages.append(f"{player.name} drew {card}, but no valid move found.")


    def play_turn(self):
        # Reset last card at the beginning of a new turn attempt
        self.last_card = None
        player = self.get_current_player()

        # Skip turn logic is now handled within advance_turn,
        # but we keep the check here for clarity before drawing.
        if player.skip_turn:
             # This message is now redundant if advance_turn handles it,
             # but can be kept for debugging or specific turn flow logging.
             # self.messages.append(f"Player {player.name} is skipping this turn.")
             # The skip_turn flag is reset in advance_turn
             self.advance_turn()
             return None # Indicate no card was drawn this attempt

        card = self.deck.draw()
        # --- ADD THIS LINE ---
        # self.last_card = str(card) # Store the string representation of the drawn card
        self.last_card = card # Store the actual Card object

        # Add message about the draw *before* moving
        self.messages.append(f"{player.name} drew: {self.last_card}.")

        self.move_player(player, card)

        # Advance turn only if the game is not finished
        if self.status != "Finished":
            self.advance_turn()

        return card # Return the card object itself (might be useful later)

# ---------- Global Game Instance ----------
# Using a global variable for simplicity in this example.
# For larger apps, consider Flask sessions or a database.
game = None

# ---------- Flask Routes ----------
@app.route("/", methods=["GET"])
def setup():
    global game
    game = None # Ensure game is reset when going back to setup
    return render_template("setup.html")

@app.route("/start", methods=["POST"])
def start():
    global game
    try:
        num_players = int(request.form.get("num_players", 0))
        if not 2 <= num_players <= 6: # Basic validation
             flash("Please enter a number of players between 2 and 6.", "error")
             return redirect(url_for("setup"))
    except (ValueError, TypeError):
        flash("Invalid number of players.", "error")
        return redirect(url_for("setup"))

    names = []
    for i in range(1, num_players + 1):
        name = request.form.get(f"player{i}", f"Player {i}").strip()
        if not name: # Ensure names are not empty
            name = f"Player {i}"
        names.append(name)

    game = Game(num_players, names)
    game.messages.append("Game started!")
    return redirect(url_for("game_route"))

@app.route("/game", methods=["GET"])
def game_route():
    if game is None:
        # Redirect to setup if game hasn't been started
        flash("Please start a new game first.", "info")
        return redirect(url_for("setup"))
    # The 'game' object (including game.last_card) is passed to the template
    return render_template("game.html", game=game)

@app.route("/draw", methods=["POST"])
def draw():
    global game
    if game is None:
        return redirect(url_for("setup"))
    if game.status == "Finished":
        # Prevent drawing if game is over
        flash("The game has already finished!", "info")
        return redirect(url_for("game_route"))

    # play_turn now handles drawing, storing the card, moving, and advancing turn
    game.play_turn()

    # Redirect back to the game board, which will render with the updated game state
    return redirect(url_for("game_route"))

@app.route("/reset", methods=["POST"])
def reset():
    global game
    game = None # Clear the game state
    flash("Game has been reset.", "info")
    return redirect(url_for("setup"))

if __name__ == '__main__':
    # Use 0.0.0.0 to make it accessible on your network if needed
    app.run(host='0.0.0.0', port=5000, debug=True)

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
