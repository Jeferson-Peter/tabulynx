from __future__ import annotations

import argparse
from datetime import date, datetime
from pathlib import Path

import polars as pl


def build_frame(rows: int) -> pl.DataFrame:
    base_customers = ["Acme", "Beta", "Gamma", "Delta", "Echo", "Foxtrot", "Helix", "Iota"]
    data: list[dict[str, object]] = []

    for index in range(rows):
        customer = base_customers[index % len(base_customers)]
        orders = (index * 7) % 37 + 1
        revenue = round(49.5 + (index % 23) * 17.35 + (index // 5) * 1.1, 2)
        active = [True, False, None][index % 3]
        signup_month = (index % 12) + 1
        signup_day = (index % 27) + 1
        seen_hour = index % 24
        seen_minute = (index * 7) % 60
        notes = ["priority", "", "upsell candidate", "new", None, "follow-up"][index % 6]

        data.append(
            {
                "customer": customer,
                "orders": orders,
                "revenue": revenue,
                "active": active,
                "signup_date": date(2024, signup_month, signup_day),
                "last_seen": datetime(2025, ((index % 3) + 1), ((index % 27) + 1), seen_hour, seen_minute, 0),
                "notes": notes,
            }
        )

    return pl.DataFrame(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create sample CSV and Parquet files for TabuLynx.")
    parser.add_argument("--rows", type=int, default=1000, help="Number of rows to generate")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    output_dir = root / "sample_data"
    output_dir.mkdir(parents=True, exist_ok=True)

    frame = build_frame(args.rows)

    frame.write_parquet(output_dir / "filters_demo.parquet")
    frame.write_csv(output_dir / "filters_demo.csv")


if __name__ == "__main__":
    main()
