# pokergame

A gesture-controlled Texas Hold’em poker game in Python.

- Hand-gesture input: via MediaPipe & OpenCV  
- Accurate poker logic: with full hand-rank evaluation  
- Canvas-based GUI: with card images and live status  
- Round summary window logging each deal  

---

## Demo

https://youtu.be/fUleF5eKl2E

---

##  Installation

- bash

git clone https://github.com/BiscoitoSLK/pokergame.git
cd pokergame

# (Optional) Create & activate a venv
python -m venv .venv
# Windows
.\.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Ensure you have:
# - assets/table.png
# - assets/cards/2C.png … back.png

python app.py
