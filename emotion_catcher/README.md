# 🎮 Emotion Catcher

A standalone Python game built with Pygame where you catch falling emotions to maintain emotional balance.

---

## 🎯 Concept

Control a catcher at the bottom of the screen to catch falling emotion objects. Each emotion affects your **balance value** differently. Keep it stable near zero for 30 seconds to win — but if it goes beyond ±50, you lose!

## 🖼️ Screenshot

| Element          | Description                                      |
|------------------|--------------------------------------------------|
| Window           | 800 × 600 pixels, sky-blue background            |
| Balance Meter    | Horizontal bar at the top (green safe zone)       |
| Falling Emojis   | Circle-cropped faces, heart-shaped Love           |
| Catcher          | Brown tray at the bottom of the screen            |

---

## 📦 Requirements

- **Python 3.7+**
- **Pygame** (`pip install pygame`)

---

## 🚀 How to Run

```bash
pip install pygame
python emotion_catcher_game.py
```

---

## 🕹️ Controls

| Key         | Action                     |
|-------------|----------------------------|
| ← Arrow     | Move catcher left          |
| → Arrow     | Move catcher right         |
| R           | Restart (after win/lose)   |
| ESC         | Quit                       |

---

## 😊 Emotions

| Emotion  | Emoji        | Balance Effect        | Color  |
|----------|--------------|-----------------------|--------|
| Joy      | 😊           | +10                   | Gold   |
| Sadness  | 😢           | −10                   | Blue   |
| Anger    | 😠           | +5                    | Red    |
| Fear     | 😨           | −5                    | Purple |
| Love     | 💗           | Reset to 0            | Pink   |

---

## 📊 Game Rules

- **Balance value** starts at 0 (range: −50 to +50).
- Emotions spawn randomly every 1–2 seconds and fall downward.
- Catching an emotion applies its effect and plays a pop sound.
- **Stable zone**: balance stays within [−5, +5].
- **Win**: keep balance stable for **30 consecutive seconds**.
- **Lose**: balance goes beyond **±50**.

---

## 📁 Project Structure

```
emotion_catcher/
├── emotion_catcher_game.py   # Main game (single file, self-contained)
├── joy.jpeg                  # 😊 Joy emoji image
├── sad.png                   # 😢 Sadness emoji image
├── anger.jpeg                # 😠 Anger emoji image
├── fear.jpeg                 # 😨 Fear emoji image
├── pink heart.png            # 💗 Love emoji image
└── README.md                 # This file
```

---

## 🔊 Sound

A short 880 Hz pop/beep sound is generated programmatically at startup — no external sound files needed.

---

## 📜 License

Free to use and modify.
