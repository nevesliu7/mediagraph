
from __future__ import annotations
import csv
from pathlib import Path
from functools import lru_cache
import networkx as nx
import pandas as pd
import plotly.graph_objects as go

DATA_TYPES = {
    'Person': '#7c3aed',
    'Film': '#0ea5e9',
    'Genre': '#f59e0b',
    'Award': '#ef4444',
    'Platform': '#10b981',
    'Country': '#8b5cf6',
    'Language': '#14b8a6',
    'Decade': '#64748b',
    'AudienceSegment': '#f97316',
    'Theme': '#06b6d4',
}

def load_table(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

@lru_cache(maxsize=1)
def load_data(data_dir: str):
    p = Path(data_dir)
    people = load_table(p / 'people.csv')
    films = load_table(p / 'films.csv')
    roles = load_table(p / 'roles.csv')
    awards = load_table(p / 'awards.csv')
    platforms = load_table(p / 'platforms.csv')
    audience = load_table(p / 'audience_signals.csv')
    edges = load_table(p / 'edges.csv')
    source_map_path = p / 'public_source_map.csv'
    if source_map_path.exists():
        source_map = load_table(source_map_path)
        def attach_sources(df, key_col, entity_type):
            subset = source_map[source_map['entity_type'] == entity_type][['entity_name', 'source_type', 'source_title', 'source_url']].copy()
            if subset.empty:
                for col in ['source_type', 'source_title', 'source_url']:
                    if col not in df.columns:
                        df[col] = ''
                return df
            subset = subset.rename(columns={'entity_name': key_col})
            merged = df.merge(subset, on=key_col, how='left')
            for col in ['source_type', 'source_title', 'source_url']:
                if col not in merged.columns:
                    merged[col] = ''
            return merged
        people = attach_sources(people, 'name', 'person')
        films = attach_sources(films, 'title', 'film')
        awards = attach_sources(awards, 'award_name', 'award')
    return people, films, roles, awards, platforms, audience, edges

def build_graph(edges: pd.DataFrame, people: pd.DataFrame | None = None, films: pd.DataFrame | None = None):
    G = nx.Graph()
    for _, r in edges.iterrows():
        src = r['source_name']
        tgt = r['target_name']
        src_type = r['source_type']
        tgt_type = r['target_type']
        for node, ntype in [(src, src_type), (tgt, tgt_type)]:
            if node not in G:
                G.add_node(node, node_type=ntype, label=node)
            else:
                if 'node_type' not in G.nodes[node] or G.nodes[node]['node_type'] == 'Unknown':
                    G.nodes[node]['node_type'] = ntype
            if src_type == 'Person' and people is not None:
                match = people[people['name'] == node]
                if not match.empty:
                    row = match.iloc[0].to_dict()
                    G.nodes[node].update(row)
            if src_type == 'Film' and films is not None:
                match = films[films['title'] == node]
                if not match.empty:
                    row = match.iloc[0].to_dict()
                    G.nodes[node].update(row)
        if G.has_edge(src, tgt):
            G[src][tgt]['weight'] += float(r.get('weight', 1) or 1)
            rels = G[src][tgt].setdefault('relationship_types', [])
            if r['relationship'] not in rels:
                rels.append(r['relationship'])
        else:
            G.add_edge(src, tgt, weight=float(r.get('weight', 1) or 1), relationship_types=[r['relationship']], year=r.get('year', ''), note=r.get('note', ''))
    return G

def compute_metrics(G: nx.Graph):
    if G.number_of_nodes() == 0:
        return {}
    deg = dict(G.degree(weight='weight'))
    deg_cent = nx.degree_centrality(G)
    try:
        btw = nx.betweenness_centrality(G, weight='weight', normalized=True)
    except Exception:
        btw = {n: 0 for n in G.nodes}
    metrics = {}
    for n in G.nodes:
        metrics[n] = {
            'degree': deg.get(n, 0),
            'degree_centrality': deg_cent.get(n, 0),
            'betweenness': btw.get(n, 0),
            'node_type': G.nodes[n].get('node_type', 'Unknown'),
        }
    return metrics

def top_nodes(metrics: dict, node_type: str | None = None, key: str = 'degree', limit: int = 10):
    items = [
        (n, d) for n, d in metrics.items()
        if node_type is None or d.get('node_type') == node_type
    ]
    items.sort(key=lambda kv: kv[1].get(key, 0), reverse=True)
    return items[:limit]

def normalize_layout(G: nx.Graph, nodes):
    H = G.subgraph(nodes).copy()
    if H.number_of_nodes() == 0:
        return H, {}
    return H, nx.spring_layout(H, seed=42, k=0.9 / max(1, len(H.nodes()) ** 0.5))

def make_network_figure(G: nx.Graph, max_nodes: int = 120, title: str = 'Network graph', focus_nodes=None):
    metrics = compute_metrics(G)
    if focus_nodes:
        nodes = set()
        for n in focus_nodes:
            if n in G:
                nodes.update(nx.single_source_shortest_path_length(G, n, cutoff=1).keys())
        nodes = list(nodes)
    else:
        ranked = sorted(G.nodes(), key=lambda n: metrics.get(n, {}).get('degree', 0), reverse=True)
        nodes = ranked[:max_nodes]
    H, pos = normalize_layout(G, nodes)
    if H.number_of_nodes() == 0:
        return go.Figure()

    edge_x, edge_y = [], []
    for u, v, data in H.edges(data=True):
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=0.7, color='rgba(148,163,184,0.35)'),
        hoverinfo='none', mode='lines',
    )

    node_traces = []
    for node_type, color in DATA_TYPES.items():
        xs, ys, sizes, texts, custom = [], [], [], [], []
        for n in H.nodes():
            if H.nodes[n].get('node_type') != node_type:
                continue
            x, y = pos[n]
            xs.append(x); ys.append(y)
            deg = metrics.get(n, {}).get('degree', 0)
            btw = metrics.get(n, {}).get('betweenness', 0)
            size = 10 + min(30, deg * 0.6 + btw * 120)
            sizes.append(size)
            label = H.nodes[n].get('label', n)
            texts.append(label)
            rels = H.nodes[n].get('profile_notes', '') or ''
            custom.append(rels)
        if xs:
            node_traces.append(go.Scatter(
                x=xs, y=ys, mode='markers+text', text=[t if len(t) < 24 else t[:21] + '…' for t in texts], textposition='top center',
                marker=dict(size=sizes, color=color, line=dict(width=1, color='white'), opacity=0.92),
                name=node_type, hovertemplate='%{text}<extra></extra>',
                customdata=custom,
            ))

    fig = go.Figure(data=[edge_trace] + node_traces)
    fig.update_layout(
        title=title,
        showlegend=True,
        margin=dict(l=0, r=0, t=40, b=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        height=680,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='left', x=0)
    )
    return fig

def build_ego_figure(G: nx.Graph, center: str, radius: int = 1, max_nodes: int = 60):
    if center not in G:
        return go.Figure()
    nodes = set(nx.single_source_shortest_path_length(G, center, cutoff=radius).keys())
    if len(nodes) > max_nodes:
        deg = dict(G.degree(nodes, weight='weight'))
        nodes = set(sorted(nodes, key=lambda n: deg.get(n, 0), reverse=True)[:max_nodes]) | {center}
    return make_network_figure(G.subgraph(nodes).copy(), max_nodes=max_nodes, title=f'Ego network: {center}', focus_nodes=[center])
