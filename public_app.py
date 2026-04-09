import json
from pathlib import Path

import pandas as pd
import streamlit as st

DRAFT_FILE = Path("draft_state.json")
SCORES_FILE = Path("scores.csv")


def clean_display_value(x):
    if pd.isna(x):
        return ""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return x


def load_scores_file():
    if SCORES_FILE.exists():
        df = pd.read_csv(SCORES_FILE)
        if "Player" in df.columns and "Score" in df.columns:
            return df
    return pd.DataFrame(columns=["Player", "Score"])


def build_team_scores(picks, participants):
    picks_df = pd.DataFrame(picks)[["manager", "player"]].rename(
        columns={"manager": "Manager", "player": "Player"}
    )

    scores_df = load_scores_file()

    if scores_df.empty or "Player" not in scores_df.columns or "Score" not in scores_df.columns:
        scores_df = pd.DataFrame(columns=["Player", "Score"])

    scores_df = scores_df.copy()
    scores_df["Player"] = scores_df["Player"].astype(str).str.strip()
    scores_df["Score"] = pd.to_numeric(scores_df["Score"], errors="coerce")

    merged = picks_df.merge(scores_df, on="Player", how="left")

    standings = []
    for manager, group in merged.groupby("Manager"):
        scores = pd.to_numeric(group["Score"], errors="coerce").dropna().tolist()
        scores = sorted(scores)
        counted = scores[:4]
        total = sum(counted) if counted else pd.NA

        standings.append(
            {
                "Manager": manager,
                "Team Total": "" if pd.isna(total) else int(total) if float(total).is_integer() else total,
                "Counted Scores": ", ".join(
                    str(int(x)) if float(x).is_integer() else str(x) for x in counted
                ),
                "MC Count": sum(1 for s in scores if s == 1000),
            }
        )

    out = pd.DataFrame(standings)
    out = out.fillna("")
    if not out.empty:
        out = out.sort_values(["Team Total", "MC Count"], ascending=[True, True], na_position="last")
        out = out.reset_index(drop=True)
        out.insert(0, "Rank", range(1, len(out) + 1))

    return out


def roster_scores_display_df(picks, participants, rounds=6):
    picks_df = pd.DataFrame(picks)[["manager", "player"]].rename(
        columns={"manager": "Manager", "player": "Player"}
    )

    scores_df = load_scores_file()

    if scores_df.empty or "Player" not in scores_df.columns or "Score" not in scores_df.columns:
        scores_df = pd.DataFrame(columns=["Player", "Score"])

    scores_df = scores_df.copy()
    scores_df["Player"] = scores_df["Player"].astype(str).str.strip()
    scores_df["Score"] = pd.to_numeric(scores_df["Score"], errors="coerce")

    merged = picks_df.merge(scores_df, on="Player", how="left")

    rows = []
    for manager in participants:
        group = merged[merged["Manager"] == manager].reset_index(drop=True)

        row = {"Manager": manager}
        numeric_scores = []

        for i in range(rounds):
            if i < len(group):
                player = group.loc[i, "Player"]
                score = group.loc[i, "Score"]
            else:
                player = ""
                score = pd.NA

            row[f"P{i+1}"] = player
            row[f"S{i+1}"] = clean_display_value(score)

            if pd.notna(score):
                numeric_scores.append(score)

        numeric_scores = sorted(numeric_scores)
        counted_scores = numeric_scores[:4]
        team_total = sum(counted_scores) if counted_scores else pd.NA

        row["Total"] = clean_display_value(team_total)
        row["_counted_scores"] = counted_scores
        rows.append(row)

    return pd.DataFrame(rows)


def highlight_counted_scores(display_row, full_row):
    styles = [""] * len(display_row)

    counted = full_row.get("_counted_scores", [])
    remaining = counted.copy()

    for i, col in enumerate(display_row.index):
        if str(col).startswith("S"):
            val = display_row[col]
            try:
                numeric_val = float(val)
            except Exception:
                continue

            if numeric_val in remaining:
                styles[i] = "background-color: #1e7f4f; color: white;"
                remaining.remove(numeric_val)

    return styles


st.set_page_config(page_title="Masters Pool Live Standings", layout="wide")
st.title("Masters Pool Live Standings")

c1, c2 = st.columns([1, 3])
with c1:
    if st.button("Refresh scores", use_container_width=True):
        st.rerun()

with c2:
    if SCORES_FILE.exists():
        last_updated = pd.Timestamp(SCORES_FILE.stat().st_mtime, unit="s")
        st.caption(f"Scores last updated: {last_updated}")

if not DRAFT_FILE.exists():
    st.error("draft_state.json not found.")
    st.stop()

with open(DRAFT_FILE, "r", encoding="utf-8") as f:
    state = json.load(f)

picks = state.get("picks", [])
participants = state.get("participants", [])
rounds = state.get("rounds", 6)

if not picks:
    st.info("No picks found in saved draft.")
    st.stop()

standings = build_team_scores(picks, participants)
roster_scores_wide = roster_scores_display_df(picks, participants, rounds=rounds)

st.subheader("Standings")
st.dataframe(standings, use_container_width=True, hide_index=True)

ordered_cols = ["Manager", "Total"]
for i in range(1, rounds + 1):
    ordered_cols.extend([f"P{i}", f"S{i}"])
ordered_cols.append("_counted_scores")

roster_scores_wide = roster_scores_wide[ordered_cols]

st.subheader("Rosters with Scores")
display_df = roster_scores_wide.drop(columns=["_counted_scores"]).copy()
styled = display_df.style.apply(
    lambda row: highlight_counted_scores(row, roster_scores_wide.loc[row.name]),
    axis=1
)
st.table(styled)
st.caption("Green score cells are the 4 counted scores.")