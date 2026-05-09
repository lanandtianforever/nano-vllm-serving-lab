from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Callable, Iterable


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "local_serving_baseline" / "results"
FIGURES_DIR = ROOT / "analysis" / "figures"


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def percentile(values: Iterable[float], p: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * p
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    weight = rank - lower
    return ordered[lower] * (1 - weight) + ordered[upper] * weight


def grouped_metric(
    rows: list[dict],
    key: str,
    metric: str,
    reducer: Callable[[list[float]], float],
    *,
    skip_errors: bool = True,
) -> list[tuple[float, float]]:
    grouped: dict[float, list[float]] = defaultdict(list)
    for row in rows:
        if skip_errors and row.get("error"):
            continue
        value = row.get(metric)
        if value is None:
            continue
        grouped[float(row[key])].append(float(value))
    return [(k, reducer(v)) for k, v in sorted(grouped.items()) if v]


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def esc(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def format_tick(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def render_line_chart(
    *,
    title: str,
    subtitle: str,
    x_label: str,
    y_label: str,
    series: list[dict],
    output_path: Path,
    width: int = 920,
    height: int = 520,
) -> None:
    margin_left = 78
    margin_right = 32
    margin_top = 96
    margin_bottom = 74
    plot_w = width - margin_left - margin_right
    plot_h = height - margin_top - margin_bottom

    all_x = [x for item in series for x, _ in item["points"]]
    all_y = [y for item in series for _, y in item["points"]]
    if not all_x or not all_y:
        raise ValueError(f"No data to plot for {output_path}")

    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = 0.0, max(all_y)
    if x_min == x_max:
        x_min -= 1
        x_max += 1
    if y_max <= y_min:
        y_max = 1.0
    y_max *= 1.12

    def x_pos(value: float) -> float:
        return margin_left + (value - x_min) / (x_max - x_min) * plot_w

    def y_pos(value: float) -> float:
        return margin_top + plot_h - (value - y_min) / (y_max - y_min) * plot_h

    x_ticks = sorted(set(all_x))
    y_ticks = [y_max * i / 4 for i in range(5)]

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfbf8"/>',
        f'<text x="{margin_left}" y="38" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="700" fill="#17202a">{esc(title)}</text>',
        f'<text x="{margin_left}" y="66" font-family="Inter, Arial, sans-serif" font-size="14" fill="#4f5b67">{esc(subtitle)}</text>',
        f'<line x1="{margin_left}" y1="{margin_top + plot_h}" x2="{margin_left + plot_w}" y2="{margin_top + plot_h}" stroke="#1f2933" stroke-width="1.2"/>',
        f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_h}" stroke="#1f2933" stroke-width="1.2"/>',
    ]

    for tick in y_ticks:
        y = y_pos(tick)
        lines.append(
            f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e0d8" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Inter, Arial, sans-serif" font-size="12" fill="#56616b">{format_tick(tick)}</text>'
        )

    for tick in x_ticks:
        x = x_pos(tick)
        lines.append(
            f'<line x1="{x:.2f}" y1="{margin_top + plot_h}" x2="{x:.2f}" y2="{margin_top + plot_h + 6}" stroke="#1f2933" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{margin_top + plot_h + 26}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="12" fill="#56616b">{format_tick(tick)}</text>'
        )

    color_palette = ["#1b6ca8", "#c74634", "#2d7d46", "#7a4fb3"]
    for idx, item in enumerate(series):
        color = item.get("color") or color_palette[idx % len(color_palette)]
        points = item["points"]
        path_parts = []
        for point_idx, (x_val, y_val) in enumerate(points):
            command = "M" if point_idx == 0 else "L"
            path_parts.append(f"{command} {x_pos(x_val):.2f} {y_pos(y_val):.2f}")
        lines.append(
            f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x_val, y_val in points:
            lines.append(
                f'<circle cx="{x_pos(x_val):.2f}" cy="{y_pos(y_val):.2f}" r="4.5" fill="{color}" stroke="#fbfbf8" stroke-width="2"/>'
            )

    legend_x = margin_left + plot_w - 230
    legend_y = margin_top - 18
    for idx, item in enumerate(series):
        color = item.get("color") or color_palette[idx % len(color_palette)]
        y = legend_y + idx * 22
        lines.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 26}" y2="{y}" stroke="{color}" stroke-width="3"/>')
        lines.append(
            f'<text x="{legend_x + 34}" y="{y + 4}" font-family="Inter, Arial, sans-serif" font-size="13" fill="#34414c">{esc(item["label"])}</text>'
        )

    lines.append(
        f'<text x="{margin_left + plot_w / 2:.2f}" y="{height - 24}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#34414c">{esc(x_label)}</text>'
    )
    lines.append(
        f'<text transform="translate(24 {margin_top + plot_h / 2:.2f}) rotate(-90)" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#34414c">{esc(y_label)}</text>'
    )
    lines.append("</svg>")

    output_path.write_text("\n".join(lines) + "\n")


def render_two_panel_chart(
    *,
    title: str,
    subtitle: str,
    x_label: str,
    top_label: str,
    bottom_label: str,
    top_points: list[tuple[float, float]],
    bottom_points: list[tuple[float, float]],
    output_path: Path,
    width: int = 920,
    height: int = 620,
) -> None:
    margin_left = 82
    margin_right = 32
    margin_top = 98
    panel_gap = 68
    margin_bottom = 74
    panel_h = (height - margin_top - margin_bottom - panel_gap) / 2
    plot_w = width - margin_left - margin_right

    all_x = [x for x, _ in top_points + bottom_points]
    if not all_x or not top_points or not bottom_points:
        raise ValueError(f"No data to plot for {output_path}")

    x_min, x_max = min(all_x), max(all_x)
    if x_min == x_max:
        x_min -= 1
        x_max += 1

    def x_pos(value: float) -> float:
        return margin_left + (value - x_min) / (x_max - x_min) * plot_w

    def render_panel(
        *,
        y_top: float,
        points: list[tuple[float, float]],
        label: str,
        color: str,
        lines: list[str],
    ) -> None:
        y_max = max(y for _, y in points) * 1.14
        if y_max <= 0:
            y_max = 1.0

        def y_pos(value: float) -> float:
            return y_top + panel_h - value / y_max * panel_h

        lines.append(
            f'<text x="{margin_left}" y="{y_top - 16:.2f}" font-family="Inter, Arial, sans-serif" font-size="14" font-weight="700" fill="#34414c">{esc(label)}</text>'
        )
        lines.append(
            f'<line x1="{margin_left}" y1="{y_top + panel_h:.2f}" x2="{margin_left + plot_w}" y2="{y_top + panel_h:.2f}" stroke="#1f2933" stroke-width="1.2"/>'
        )
        lines.append(
            f'<line x1="{margin_left}" y1="{y_top:.2f}" x2="{margin_left}" y2="{y_top + panel_h:.2f}" stroke="#1f2933" stroke-width="1.2"/>'
        )
        for idx in range(5):
            tick = y_max * idx / 4
            y = y_pos(tick)
            lines.append(
                f'<line x1="{margin_left}" y1="{y:.2f}" x2="{margin_left + plot_w}" y2="{y:.2f}" stroke="#e2e0d8" stroke-width="1"/>'
            )
            lines.append(
                f'<text x="{margin_left - 10}" y="{y + 4:.2f}" text-anchor="end" font-family="Inter, Arial, sans-serif" font-size="12" fill="#56616b">{format_tick(tick)}</text>'
            )

        path_parts = []
        for idx, (x_val, y_val) in enumerate(points):
            command = "M" if idx == 0 else "L"
            path_parts.append(f"{command} {x_pos(x_val):.2f} {y_pos(y_val):.2f}")
        lines.append(
            f'<path d="{" ".join(path_parts)}" fill="none" stroke="{color}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
        )
        for x_val, y_val in points:
            lines.append(
                f'<circle cx="{x_pos(x_val):.2f}" cy="{y_pos(y_val):.2f}" r="4.5" fill="{color}" stroke="#fbfbf8" stroke-width="2"/>'
            )

    lines: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fbfbf8"/>',
        f'<text x="{margin_left}" y="38" font-family="Inter, Arial, sans-serif" font-size="24" font-weight="700" fill="#17202a">{esc(title)}</text>',
        f'<text x="{margin_left}" y="66" font-family="Inter, Arial, sans-serif" font-size="14" fill="#4f5b67">{esc(subtitle)}</text>',
    ]

    render_panel(
        y_top=margin_top,
        points=top_points,
        label=top_label,
        color="#1b6ca8",
        lines=lines,
    )
    render_panel(
        y_top=margin_top + panel_h + panel_gap,
        points=bottom_points,
        label=bottom_label,
        color="#c74634",
        lines=lines,
    )

    bottom_axis = margin_top + panel_h + panel_gap + panel_h
    for tick in sorted(set(all_x)):
        x = x_pos(tick)
        lines.append(
            f'<line x1="{x:.2f}" y1="{bottom_axis:.2f}" x2="{x:.2f}" y2="{bottom_axis + 6:.2f}" stroke="#1f2933" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{bottom_axis + 26:.2f}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="12" fill="#56616b">{format_tick(tick)}</text>'
        )

    lines.append(
        f'<text x="{margin_left + plot_w / 2:.2f}" y="{height - 24}" text-anchor="middle" font-family="Inter, Arial, sans-serif" font-size="14" fill="#34414c">{esc(x_label)}</text>'
    )
    lines.append("</svg>")
    output_path.write_text("\n".join(lines) + "\n")


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    concurrency = load_jsonl(RESULTS_DIR / "concurrency_sweep_day2.jsonl")
    context = load_jsonl(RESULTS_DIR / "context_sweep_day3.jsonl")
    output = load_jsonl(RESULTS_DIR / "output_len_sweep_day4.jsonl")

    render_two_panel_chart(
        title="Concurrency Sweep: E2E Latency and TPOT",
        subtitle="MacBook Air M5 + LM Studio black-box baseline, qwen/qwen3-8b",
        x_label="Concurrency",
        top_label="Avg E2E latency (s)",
        bottom_label="Avg TPOT (s/chunk)",
        top_points=grouped_metric(concurrency, "concurrency", "e2e_latency", mean),
        bottom_points=grouped_metric(concurrency, "concurrency", "tpot", mean),
        output_path=FIGURES_DIR / "local_concurrency_e2e_tpot.svg",
    )

    render_line_chart(
        title="Context Sweep: Prompt Length vs TTFT",
        subtitle="Context label is experimental; prompt length is word-count estimate",
        x_label="Avg prompt words",
        y_label="Seconds",
        series=[
            {
                "label": "Avg TTFT",
                "points": grouped_metric(context, "prompt_len_estimate", "ttft", mean),
                "color": "#2d7d46",
            },
            {
                "label": "P95 TTFT",
                "points": grouped_metric(context, "prompt_len_estimate", "ttft", lambda values: percentile(values, 0.95)),
                "color": "#7a4fb3",
            },
        ],
        output_path=FIGURES_DIR / "local_context_ttft.svg",
    )

    render_two_panel_chart(
        title="Output Length Sweep: E2E Latency and TPOT",
        subtitle="Rows with non-null error are excluded from metric averages",
        x_label="Requested max_tokens",
        top_label="Avg E2E latency (s)",
        bottom_label="Avg TPOT (s/chunk)",
        top_points=grouped_metric(output, "max_tokens", "e2e_latency", mean),
        bottom_points=grouped_metric(output, "max_tokens", "tpot", mean),
        output_path=FIGURES_DIR / "local_output_e2e_tpot.svg",
    )

    print("Generated figures:")
    for path in sorted(FIGURES_DIR.glob("local_*.svg")):
        print(f"- {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
