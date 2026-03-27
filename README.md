# osrs-profit-tracker
Live GP/hr calculator for Tan Leather, Degrime, and Unf Potions using the OSRS Wiki API

## Requirements
- Python 3
- pip install requests
- pip install plyer (if you want notifications)

## Usage
python profit.py

## config
- HERBLORE_LEVEL — filters out herbs based on lvl
- HERBS_PER_HOUR_DEGRIME / HERBS_PER_HOUR_UNF / HIDES_PER_HOUR_TAN — adjust to your speed
- PROFIT_THRESHOLD — GP/hr threshold for notifications
- REFRESH_SECONDS — how often it re-checks prices
