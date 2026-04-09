import time
from io import StringIO
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://www.espn.com/golf/leaderboard?season=2026&tournamentId=401811941"


def normalize_score(value):
    s = str(value).strip().upper()

    if s in {"MC", "CUT"}:
        return 1000
    if s in {"E", "EVEN", "PAR"}:
        return 0
    if s in {"-", ""}:
        return None

    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return None


def scrape_espn_scores():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1600,1200")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

    try:
        driver.get(URL)
        time.sleep(5)

        tables = pd.read_html(StringIO(driver.page_source))

        for table in tables:
            player_col = next((c for c in table.columns if "player" in str(c).lower()), None)
            score_col = next((c for c in table.columns if str(c).strip().lower() == "score"), None)

            if player_col and score_col:
                df = table[[player_col, score_col]].copy()
                df.columns = ["Player", "Score"]

                df["Player"] = df["Player"].astype(str).str.strip()
                df["Score"] = df["Score"].apply(normalize_score)

                df = df.dropna(subset=["Player"])
                df = df[df["Player"] != ""]
                df = df.drop_duplicates(subset=["Player"], keep="first").reset_index(drop=True)

                return df

        return pd.DataFrame(columns=["Player", "Score"])

    finally:
        driver.quit()


def write_scores_csv(path="scores.csv"):
    df = scrape_espn_scores()
    if df.empty:
        raise RuntimeError("No scores parsed from ESPN.")
    df.to_csv(path, index=False)
    return df


if __name__ == "__main__":
    df = write_scores_csv("scores.csv")
    print(df.head(20))
    print(f"Wrote {len(df)} rows to scores.csv")