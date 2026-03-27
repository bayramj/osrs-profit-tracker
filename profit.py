import requests
import time

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


HERBS_PER_HOUR_DEGRIME = 9000   # you can change all of these depending on how quickly or efficient you're playing
HERBS_PER_HOUR_UNF     = 3100   
HIDES_PER_HOUR_TAN     = 5000   

PROFIT_THRESHOLD = 1_000_000   
ENABLE_NOTIFICATIONS = False    # need to install plyer for this w/ pip install plyer

REFRESH_SECONDS = 300            
HERBLORE_LEVEL = 99             

LATEST_API = "https://prices.runescape.wiki/api/v1/osrs/latest"
MAPPING_API = "https://prices.runescape.wiki/api/v1/osrs/mapping"
USER_AGENT = "OSRS-CombinedProfit/1.0 (contact: your_email@example.com)"

# =========================
# Data structures
# =========================
NATURE_RUNES_PER_CAST = 2
HERBS_PER_CAST = 27
VIAL_OF_WATER_ID = 227

HERBS = [
    # you can add huasca, I didn't include it bc the volume is so low 
    {"name": "Guam leaf",     "grimy_name": "Grimy guam leaf",     "clean_name": "Guam leaf",     "unf_name": "Guam potion (unf)",     "level": 3},
    {"name": "Marrentill",    "grimy_name": "Grimy marrentill",    "clean_name": "Marrentill",    "unf_name": "Marrentill potion (unf)", "level": 5},
    {"name": "Tarromin",      "grimy_name": "Grimy tarromin",      "clean_name": "Tarromin",      "unf_name": "Tarromin potion (unf)",   "level": 11},
    {"name": "Harralander",   "grimy_name": "Grimy harralander",   "clean_name": "Harralander",   "unf_name": "Harralander potion (unf)", "level": 20},
    {"name": "Ranarr weed",   "grimy_name": "Grimy ranarr weed",   "clean_name": "Ranarr weed",   "unf_name": "Ranarr potion (unf)",      "level": 25},
    {"name": "Toadflax",      "grimy_name": "Grimy toadflax",      "clean_name": "Toadflax",      "unf_name": "Toadflax potion (unf)",    "level": 30},
    {"name": "Irit leaf",     "grimy_name": "Grimy irit leaf",     "clean_name": "Irit leaf",     "unf_name": "Irit potion (unf)",        "level": 40},
    {"name": "Avantoe",       "grimy_name": "Grimy avantoe",       "clean_name": "Avantoe",       "unf_name": "Avantoe potion (unf)",     "level": 48},
    {"name": "Kwuarm",        "grimy_name": "Grimy kwuarm",        "clean_name": "Kwuarm",        "unf_name": "Kwuarm potion (unf)",      "level": 54},
    {"name": "Snapdragon",    "grimy_name": "Grimy snapdragon",    "clean_name": "Snapdragon",    "unf_name": "Snapdragon potion (unf)",  "level": 59},
    {"name": "Cadantine",     "grimy_name": "Grimy cadantine",     "clean_name": "Cadantine",     "unf_name": "Cadantine potion (unf)",   "level": 65},
    {"name": "Lantadyme",     "grimy_name": "Grimy lantadyme",     "clean_name": "Lantadyme",     "unf_name": "Lantadyme potion (unf)",   "level": 67},
    {"name": "Dwarf weed",    "grimy_name": "Grimy dwarf weed",    "clean_name": "Dwarf weed",    "unf_name": "Dwarf weed potion (unf)",  "level": 70},
    {"name": "Torstol",       "grimy_name": "Grimy torstol",       "clean_name": "Torstol",       "unf_name": "Torstol potion (unf)",     "level": 75},
] 

TAN_COST = 20
LEATHERS = [
    {"color": "Green", "hide_name": "Green dragonhide",     "leather_name": "Green dragon leather"},
    {"color": "Blue",  "hide_name": "Blue dragonhide",      "leather_name": "Blue dragon leather"},
    {"color": "Red",   "hide_name": "Red dragonhide",       "leather_name": "Red dragon leather"},
    {"color": "Black", "hide_name": "Black dragonhide",     "leather_name": "Black dragon leather"},
]

def fetch_json(url):
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    r.raise_for_status()
    return r.json()

def build_name_to_id_map():
    data = fetch_json(MAPPING_API)
    name_to_id = {}
    for item in data:
        item_id = item.get("id")
        item_name = item.get("name")
        if item_id is None or not item_name:
            continue
        name_to_id[item_name.strip().lower()] = item_id
    return name_to_id

def fetch_latest_prices():
    data = fetch_json(LATEST_API)
    return data.get("data", {})

def get_price(price_data, item_id):
    entry = price_data.get(str(item_id), {})
    return {
        "low": entry.get("low", 0) or 0,
        "high": entry.get("high", 0) or 0,
    }


def resolve_herb_ids(name_to_id):
    missing = []
    for herb in HERBS:
        grimy_id = name_to_id.get(herb["grimy_name"].lower())
        clean_id = name_to_id.get(herb["clean_name"].lower())
        unf_id   = name_to_id.get(herb["unf_name"].lower())

        herb["grimy_id"] = grimy_id
        herb["clean_id"] = clean_id
        herb["unf_id"]   = unf_id

        if grimy_id is None:
            missing.append(herb["grimy_name"])
        if clean_id is None:
            missing.append(herb["clean_name"])
        if unf_id is None:
            missing.append(herb["unf_name"])

    nature_rune_id = name_to_id.get("nature rune")
    if nature_rune_id is None:
        missing.append("Nature rune")
    return nature_rune_id, missing

def resolve_leather_ids(name_to_id):
    missing = []
    for leather in LEATHERS:
        hide_id = name_to_id.get(leather["hide_name"].lower())
        leather_id = name_to_id.get(leather["leather_name"].lower())
        leather["hide_id"] = hide_id
        leather["leather_id"] = leather_id
        if hide_id is None:
            missing.append(leather["hide_name"])
        if leather_id is None:
            missing.append(leather["leather_name"])
    return missing


def compute_herb_profits(price_data, nature_rune_id):
    nature_prices = get_price(price_data, nature_rune_id)
    nature_buy = nature_prices["high"]
    rune_cost_per_herb = (nature_buy * NATURE_RUNES_PER_CAST) / HERBS_PER_CAST

    vial_prices = get_price(price_data, VIAL_OF_WATER_ID)
    vial_buy = vial_prices["high"]

    degrime_rows = []
    unf_rows = []

    for herb in HERBS:
        if HERBLORE_LEVEL > 0 and herb.get("level", 0) > HERBLORE_LEVEL:
            continue
        if herb.get("grimy_id") is None or herb.get("clean_id") is None or herb.get("unf_id") is None:
            continue

        grimy_prices = get_price(price_data, herb["grimy_id"])
        clean_prices = get_price(price_data, herb["clean_id"])
        unf_prices   = get_price(price_data, herb["unf_id"])

        # Degrime
        degrime_profit_per_herb = clean_prices["low"] - grimy_prices["high"] - rune_cost_per_herb
        degrime_profit_per_hour = degrime_profit_per_herb * HERBS_PER_HOUR_DEGRIME
        degrime_rows.append({
            "name": herb["name"],
            "profit_per_herb": degrime_profit_per_herb,
            "profit_per_hour": degrime_profit_per_hour,
        })

        # Unf
        unf_profit_per_herb = unf_prices["low"] - (clean_prices["high"] + vial_buy)
        unf_profit_per_hour = unf_profit_per_herb * HERBS_PER_HOUR_UNF
        unf_rows.append({
            "name": herb["name"],
            "profit_per_herb": unf_profit_per_herb,
            "profit_per_hour": unf_profit_per_hour,
        })

    degrime_rows.sort(key=lambda r: r["profit_per_hour"], reverse=True)
    unf_rows.sort(key=lambda r: r["profit_per_hour"], reverse=True)

    return degrime_rows, unf_rows

def compute_leather_profits(price_data):
    rows = []
    for leather in LEATHERS:
        if leather.get("hide_id") is None or leather.get("leather_id") is None:
            continue
        hide_prices = get_price(price_data, leather["hide_id"])
        leather_prices = get_price(price_data, leather["leather_id"])

        hide_buy = hide_prices["high"]
        leather_sell = leather_prices["low"]

        profit_per_hide = leather_sell - hide_buy - TAN_COST
        profit_per_hour = profit_per_hide * HIDES_PER_HOUR_TAN

        rows.append({
            "color": leather["color"],
            "profit_per_hide": profit_per_hide,
            "profit_per_hour": profit_per_hour,
        })

    rows.sort(key=lambda r: r["profit_per_hour"], reverse=True)
    return rows


def send_notification(title, message):
    if ENABLE_NOTIFICATIONS and PLYER_AVAILABLE:
        try:
            notification.notify(title=title, message=message, timeout=10)
        except Exception as e:
            print(f"[Notification failed] {e}")

def print_report(degrime_rows, unf_rows, leather_rows):
    print("\n" + "="*110)
    print("Real‑time Profit Comparison (buy at HIGH, sell at LOW)")
    print("="*110)

    # Degrime section
    if degrime_rows:
        print("\n--- DEGRIME (Clean grimy herbs) ---")
        print(f"{'Herb':<12} {'Profit/ea':>12} {'Profit/hour':>15}")
        print("-"*40)
        for r in degrime_rows:
            print(f"{r['name']:<12} {r['profit_per_herb']:>11.2f} {r['profit_per_hour']:>15,.0f}")
        best_degrime = degrime_rows[0]
        print("-"*40)
        print(f"Best Degrime: {best_degrime['name']} – {best_degrime['profit_per_hour']:,.0f} GP/hr")
    else:
        print("\nNo Degrime data available (check Herblore level).")

    # Unf section
    if unf_rows:
        print("\n--- UNFINISHED POTIONS (from clean herbs) ---")
        print(f"{'Herb':<12} {'Profit/ea':>12} {'Profit/hour':>15}")
        print("-"*40)
        for r in unf_rows:
            print(f"{r['name']:<12} {r['profit_per_herb']:>11.2f} {r['profit_per_hour']:>15,.0f}")
        best_unf = unf_rows[0]
        print("-"*40)
        print(f"Best Unf: {best_unf['name']} – {best_unf['profit_per_hour']:,.0f} GP/hr")
    else:
        print("\nNo Unf data available (check Herblore level).")

    # Leather section
    if leather_rows:
        print("\n--- TAN LEATHER (Tan Leather spell) ---")
        print(f"{'Leather':<12} {'Profit/hide':>12} {'Profit/hour':>15}")
        print("-"*40)
        for r in leather_rows:
            print(f"{r['color']:<12} {r['profit_per_hide']:>11.2f} {r['profit_per_hour']:>15,.0f}")
        best_leather = leather_rows[0]
        print("-"*40)
        print(f"Best Tan: {best_leather['color']} leather – {best_leather['profit_per_hour']:,.0f} GP/hr")
    else:
        print("\nNo leather data available (check item names).")

    print("="*110)
  #  print("\n")

    print(f"\nBest Degrime: {best_degrime['name']} – {best_degrime['profit_per_hour']:,.0f} GP/hr")
    print(f"Best Unf: {best_unf['name']} – {best_unf['profit_per_hour']:,.0f} GP/hr")
    print(f"Best Tan: {best_leather['color']} leather – {best_leather['profit_per_hour']:,.0f} GP/hr")

    # Send notifications if thresholds exceeded
    if degrime_rows and best_degrime["profit_per_hour"] >= PROFIT_THRESHOLD:
        send_notification("OSRS Profit Alert",
                          f"Degrime: {best_degrime['name']} – {best_degrime['profit_per_hour']:,.0f} GP/hr")
    if unf_rows and best_unf["profit_per_hour"] >= PROFIT_THRESHOLD:
        send_notification("OSRS Profit Alert",
                          f"Unf potions: {best_unf['name']} – {best_unf['profit_per_hour']:,.0f} GP/hr")
    if leather_rows and best_leather["profit_per_hour"] >= PROFIT_THRESHOLD:
        send_notification("OSRS Profit Alert",
                          f"Tanning: {best_leather['color']} leather – {best_leather['profit_per_hour']:,.0f} GP/hr")


def main():
    print("Loading OSRS item mapping...")
    try:
        name_to_id = build_name_to_id_map()
        nature_rune_id, herb_missing = resolve_herb_ids(name_to_id)
        leather_missing = resolve_leather_ids(name_to_id)

        if herb_missing:
            print("Warning: Could not resolve herb IDs for:", ", ".join(sorted(set(herb_missing))))
        if leather_missing:
            print("Warning: Could not resolve leather IDs for:", ", ".join(sorted(set(leather_missing))))

    except Exception as e:
        print(f"Failed to build item map: {e}")
        return

    while True:
        try:
            print("\nFetching latest OSRS Wiki prices...")
            price_data = fetch_latest_prices()

            degrime_rows, unf_rows = compute_herb_profits(price_data, nature_rune_id)
            leather_rows = compute_leather_profits(price_data)

            print_report(degrime_rows, unf_rows, leather_rows)

        except Exception as e:
            print(f"Error during refresh cycle: {e}")

        print(f"\nRefreshing again in {REFRESH_SECONDS // 60} minutes...\n")
        time.sleep(REFRESH_SECONDS)

if __name__ == "__main__":
    main()