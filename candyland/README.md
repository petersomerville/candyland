# Candyland Game

## Overview

Candyland is a web-based board game implemented using Flask. Players navigate through a colorful board by drawing cards and moving their pawns, aiming to reach the finish square first.

## Project Structure

```
candyland
├── app.py                # Main application file for the Flask app
├── requirements.txt      # Lists dependencies required for the project
├── templates             # Contains HTML templates for the application
│   ├── index.html       # HTML template for the game setup page
│   └── game.html        # HTML template for the main game page
├── static                # Contains static files like CSS
│   └── css
│       └── style.css     # CSS styles for the application
└── README.md             # Documentation for the project
```

## Requirements

To run this application, you need to have Python and Flask installed. You can install the required packages using the following command:

```
pip install -r requirements.txt
```

## Running the Application

1. Navigate to the project directory.
2. Run the application using the command:
   ```
   python app.py
   ```
3. Open your web browser and go to `http://127.0.0.1:5000/` to access the game.

## How to Play

1. Select the number of players (2 to 4).
2. Enter the names of the players.
3. Click "Start Game" to begin.
4. Players take turns drawing cards and moving their pawns on the board.
5. The first player to reach the finish square wins the game!

## Contributing

Feel free to fork the repository and submit pull requests for any improvements or features you would like to add.
