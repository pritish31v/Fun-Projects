# 🎮 Game Tracker

A premium desktop app for tracking which games you've played, are playing, or have left halfway through. Built with Python and Tkinter, with a custom onyx, gold, and emerald interface.

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

## ✨ Features

- **Status tracking:** Mark games as *Not played*, *Playing*, *Halfway*, or *Played*
- **Quick updates:** Select multiple games and set their status at once, or double-click a status dot to cycle through them
- **Steam library scan:** Automatically imports the games you have installed on Steam
- **Internet search:** Find any game on the Steam store and see its developer, genres, price, release date, and Metacritic score
- **One-click add:** Save a search result to your library with its status
- **Live statistics:** Rounded stat cards and a completion ring show your progress
- **Search and filters:** Find games by name and filter by status
- **Persistent storage:** Your progress is saved to a local JSON file automatically
- **Custom styling:** Rounded buttons, cards, and badges in an onyx, ivory, silver, gold, emerald, and velvet red palette

## 📸 Screenshots

<!-- Add screenshots here, for example: -->
<!-- ![Library](screenshots/library.png) -->
<!-- ![Discover](screenshots/discover.png) -->

## 🚀 Getting Started

### Requirements

- Python 3.8 or newer
- tkinter (included with most Python installers)

On Linux, if tkinter is missing, install it with:

```bash
sudo apt install python3-tk
```

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/pritish31v/Fun-Projects.git
   cd game-tracker
   ```

2. Run the app:

   ```bash
   python game_tracker.py
   ```

No additional packages are required. The app uses only the Python standard library.

## 🧭 How to Use

1. **Library tab:** Browse your games, use the search box and filter pills, and select games to change their status.
2. **Scan Steam:** Click **Scan Steam** to import your installed Steam games.
3. **Add Custom:** Add games from other platforms like Epic, Xbox, or mobile.
4. **Discover tab:** Search the Steam store, click a result to see its details, and add it to your library with one click.
5. **Status dots:** Click the colored dot on the left of a game to advance its status.

## 🎨 Customizing the Theme

All colors are defined at the top of `game_tracker.py`. Change `GOLD`, `EMERALD`, `VELVET`, or `BG` to restyle the entire app.

## 🗂️ Project Structure

game-tracker/
├── game_tracker.py # Main application
├── games_tracker.json # Your saved data (created automatically)
└── README.md # This file


> **Tip:** Add `games_tracker.json` to a `.gitignore` file if you don't want your personal game list on GitHub.

## 🔒 Privacy

Your game list is stored locally. The only network requests go to the Steam store when you use the Discover search.

## 🤝 Contributing

Contributions are welcome. Feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## 🙏 Acknowledgements

- Game data and search results from the [Steam Store](https://store.steampowered.com/)
- Built with [Tkinter](https://docs.python.org/3/library/tkinter.html)