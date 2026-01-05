# Dotter

A simple 2D PvP game where you dodge and shoot. Last one alive wins.

## How to Play

```bash
git clone https://github.com/Justinfan827/dotter.git
cd dotter
./run.sh
```

## Game Modes

| Key | Mode |
|-----|------|
| **1** | Single Player (vs bot) |
| **2** | Host Game (you're blue) |
| **3** | Join Game (you're green) |

## Controls

| Key | Action |
|-----|--------|
| Arrow keys / WASD | Move |
| SPACE | Shoot toward mouse |
| ESC | Quit |
| R | Restart (after game ends) |

## Multiplayer Setup

### Host:
1. Run `./run.sh` and press **2** to Host
2. In another terminal: `ngrok tcp 5555`
3. Share the ngrok URL with your friend (e.g., `0.tcp.ngrok.io:12345`)

### Join:
1. Run `./run.sh` and press **3** to Join
2. Paste the host's ngrok URL
3. Press Enter

## Requirements

- Python 3
- pygame (auto-installed by run.sh)
- ngrok (for hosting multiplayer)
