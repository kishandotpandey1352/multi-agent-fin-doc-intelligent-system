from app.charts.revenue_chart import build_revenue_chart


def main():
    series = [(2018, 100_000_000), (2019, 150_000_000), (2020, 200_000_000), (2021, 250_000_000)]
    chart = build_revenue_chart(series)
    if not chart:
        print("No chart generated.")
        return
    svg = chart.get("svg")
    out = "data/sample_revenue_chart.svg"
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Wrote sample chart to {out}")


if __name__ == "__main__":
    main()
