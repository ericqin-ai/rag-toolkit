"""Native-theme Plotly figures; recall channels are separate paths."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from rag_toolkit.web.inspector import latency_rows, ranking_rows


def ranking_figure(response):
    stages = {t.stage for t in response.traces}
    channels = [s for s in ("bm25", "dense") if s in stages] or ["bm25", "dense"]
    fig = make_subplots(
        rows=len(channels),
        cols=1,
        subplot_titles=[s.upper() + " recall channel" for s in channels],
        vertical_spacing=0.2 if len(channels) > 1 else 0,
    )
    for row in ranking_rows(response):
        for index, channel in enumerate(channels, 1):
            if row.get(f"{channel}_rank") is None:
                continue
            path = [channel] + [s for s in ("fusion", "rerank") if s in stages]
            fig.add_trace(
                go.Scatter(
                    x=path,
                    y=[row.get(f"{s}_rank") for s in path],
                    mode="lines+markers",
                    name=f"{row['doc_id'][:24]}/{row['chunk_id'][:10]} · {channel}",
                    customdata=[[row["doc_id"], row["chunk_id"]]] * len(path),
                    hovertemplate=(
                        "%{customdata[0]}<br>%{customdata[1]}<br>%{x}: %{y}<extra></extra>"
                    ),
                    connectgaps=False,
                ),
                row=index,
                col=1,
            )
    for index, channel in enumerate(channels, 1):
        path = [channel] + [s for s in ("fusion", "rerank") if s in stages]
        fig.update_xaxes(categoryorder="array", categoryarray=path, row=index, col=1)
        fig.update_yaxes(autorange="reversed", title="Rank", row=index, col=1)
    fig.update_layout(
        height=max(360, 300 * len(channels)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def latency_figure(response):
    rows = latency_rows(response) + [{"stage": "total", "latency_ms": response.total_latency_ms}]
    fig = go.Figure(go.Bar(x=[r["stage"] for r in rows], y=[r["latency_ms"] for r in rows]))
    fig.update_layout(yaxis_title="ms", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig
