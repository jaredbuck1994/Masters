import time
from update_scores import write_scores_csv

while True:
    try:
        df = write_scores_csv("scores.csv")
        print("Updated scores.csv with", len(df), "rows")
    except Exception as e:
        print("Update failed:", e)

    time.sleep(300)