
from __future__ import annotations
from pathlib import Path
import math
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import networkx as nx

from utils.graph_builder import load_data, build_graph, compute_metrics, top_nodes, make_network_figure, build_ego_figure
from utils.scoring import person_profile, creative_fit_score, similar_talents
from utils.insights import top_bridge_people, top_bridge_films, genre_insights, story_positioning, graph_explanation, split_pipe

st.set_page_config(page_title='MediaGraph', page_icon='◉', layout='wide', initial_sidebar_state='expanded')

CSS = """
<style>
.stApp {
    background:
        radial-gradient(circle at top left, rgba(14,165,233,0.08), transparent 30%),
        radial-gradient(circle at top right, rgba(124,58,237,0.08), transparent 28%),
        linear-gradient(180deg, #f8fafc 0%, #ffffff 28%, #f8fafc 100%);
}
.hero-shell {
    padding: 1.4rem 1.5rem 1.25rem;
    border-radius: 24px;
    background: linear-gradient(135deg, rgba(15,23,42,0.98), rgba(29,78,216,0.88) 58%, rgba(88,28,135,0.88));
    color: white;
    box-shadow: 0 24px 60px rgba(15,23,42,0.18);
    border: 1px solid rgba(148,163,184,0.18);
    position: relative;
    overflow: hidden;
}
.hero-shell::after {
    content: "";
    position: absolute;
    inset: auto -12% -35% auto;
    width: 340px;
    height: 340px;
    border-radius: 999px;
    background: radial-gradient(circle, rgba(255,255,255,0.18), rgba(255,255,255,0.02) 60%, transparent 70%);
    pointer-events: none;
}
.hero-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.18em;
    color: rgba(191,219,254,0.95);
    margin-bottom: 0.45rem;
}
.hero-shell h1 {
    margin: 0;
    font-size: 2.45rem;
    line-height: 1.02;
    letter-spacing: -0.04em;
}
.hero-shell p {
    margin: 0.55rem 0 0;
    color: rgba(226,232,240,0.95);
    font-size: 1.02rem;
    max-width: 60rem;
}
.hero-chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.55rem;
    margin-top: 1rem;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.42rem 0.75rem;
    border-radius: 999px;
    background: rgba(255,255,255,0.10);
    border: 1px solid rgba(255,255,255,0.16);
    color: rgba(255,255,255,0.95);
    font-size: 0.8rem;
    backdrop-filter: blur(10px);
}
.hero-panel {
    height: 100%;
    padding: 1.15rem 1.15rem 1rem;
    border-radius: 24px;
    background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(248,250,252,0.98));
    border: 1px solid #e2e8f0;
    box-shadow: 0 18px 42px rgba(15,23,42,0.08);
}
.panel-label {
    color: #2563eb;
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.16em;
    font-weight: 700;
}
.panel-title {
    color: #0f172a;
    font-size: 1.12rem;
    font-weight: 700;
    margin-top: 0.45rem;
    line-height: 1.34;
}
.panel-list {
    margin: 0.85rem 0 0;
    padding-left: 1.05rem;
    color: #334155;
}
.panel-list li { margin-bottom: 0.45rem; }
.metric-card {
    padding: 0.9rem 1rem;
    border-radius: 16px;
    background: white;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 25px rgba(15,23,42,0.05);
}
.metric-label { color: #64748b; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.08em; }
.metric-value { font-size: 1.48rem; font-weight: 700; color: #0f172a; line-height: 1.2; }
.metric-note { color: #64748b; font-size: 0.82rem; }
.section-title { font-size: 1.05rem; font-weight: 700; margin: 0.2rem 0 0.5rem; color: #0f172a; }
.section-sub { color: #475569; margin-bottom: 0.8rem; }
.insight-box {
    background: linear-gradient(180deg, rgba(255,255,255,0.95), rgba(248,250,252,0.98));
    border: 1px solid #e2e8f0;
    border-radius: 18px;
    padding: 1rem 1.1rem;
    box-shadow: 0 10px 24px rgba(15,23,42,0.05);
}
.small-muted { color: #64748b; font-size: 0.9rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

DATA_DIR = Path(__file__).resolve().parent / 'data'
people, films, roles, awards, platforms, audience, edges = load_data(str(DATA_DIR))
graph = build_graph(edges, people, films)
metrics = compute_metrics(graph)

chinese_regions = {'China', 'Hong Kong', 'Taiwan'}
american_regions = {'United States'}

def role_bucket(role: str) -> str:
    if str(role).lower() == 'director':
        return 'Director'
    return 'Performer'

people['role_bucket'] = people['primary_role'].map(role_bucket)
films['year'] = films['year'].astype(int)
films['decade'] = (films['year'] // 10 * 10).astype(str) + 's'

all_genres = sorted(set(g for s in films['genres'].dropna() for g in split_pipe(s)))
all_platforms = sorted(set(p for s in films['platforms'].dropna() for p in split_pipe(s)))
all_decades = sorted(set(people['active_decades'].dropna().str.split('|').explode().str.strip().tolist() + films['decade'].tolist()))
all_markets = sorted(films['market_type'].dropna().unique().tolist())
all_regions = sorted(people['country_or_region'].dropna().unique().tolist())

hero_left, hero_right = st.columns([1.35, 0.85])
with hero_left:
    st.markdown(
        """
        <div class='hero-shell'>
            <div class='hero-kicker'>GRAPH INTELLIGENCE • STRATEGY PROTOTYPE</div>
            <h1>MediaGraph</h1>
            <p>A graph-based media intelligence system for exploring creative networks across Chinese and American film industries.</p>
            <div class='hero-chip-row'>
                <span class='pill'>Chinese × American market bridges</span>
                <span class='pill'>Creative fit scoring</span>
                <span class='pill'>Awards + platform pathways</span>
                <span class='pill'>Explainable strategy summaries</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with hero_right:
    st.markdown(
        """
        <div class='hero-panel'>
            <div class='panel-label'>Opening intelligence brief</div>
            <div class='panel-title'>MediaGraph reads like an internal strategy surface for a studio, streamer, agency, or investor.</div>
            <ul class='panel-list'>
                <li>Spotlight nodes surface the highest-signal creators and titles first.</li>
                <li>Bridge analysis exposes cross-market talent and film connections.</li>
                <li>Every insight stays transparent and graph-grounded.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
st.caption('Curated demonstration dataset; expand it with verified public sources such as TMDb, IMDb, Wikidata, Wikipedia, or official award databases.')

# Sidebar filters
st.sidebar.header('Network filters')
country_filter = st.sidebar.multiselect('Country or region', all_regions, default=all_regions)
role_filter = st.sidebar.multiselect('Role', ['Director', 'Performer'], default=['Director', 'Performer'])
genre_filter = st.sidebar.multiselect('Genre', all_genres, default=[])
decade_filter = st.sidebar.multiselect('Decade', all_decades, default=[])
award_filter = st.sidebar.selectbox('Award status', ['All', 'Award-connected only', 'No awards'])
market_filter = st.sidebar.multiselect('Market type', all_markets, default=all_markets)
platform_filter = st.sidebar.multiselect('Platform', all_platforms, default=[])
max_nodes = st.sidebar.slider('Max nodes in network view', 60, 180, 120, 10)

def _selected_people():
    df = people.copy()
    if country_filter:
        df = df[df['country_or_region'].isin(country_filter)]
    if role_filter:
        df = df[df['role_bucket'].isin(role_filter)]
    if decade_filter:
        df = df[df['active_decades'].apply(lambda s: any(d in str(s) for d in decade_filter))]
    return df

def _selected_films():
    df = films.copy()
    if country_filter:
        df = df[df['country_or_region'].isin(country_filter)]
    if genre_filter:
        df = df[df['genres'].apply(lambda s: any(g in split_pipe(s) for g in genre_filter))]
    if decade_filter:
        df = df[df['decade'].isin(decade_filter)]
    if market_filter:
        df = df[df['market_type'].isin(market_filter)]
    if platform_filter:
        df = df[df['platforms'].apply(lambda s: any(p in split_pipe(s) for p in platform_filter))]
    if award_filter == 'Award-connected only':
        df = df[df['awards'].fillna('').str.len() > 0]
    elif award_filter == 'No awards':
        df = df[df['awards'].fillna('').str.len() == 0]
    return df

def filtered_subgraph():
    psel = _selected_people()
    fsel = _selected_films()
    names = set(psel['name']).union(set(fsel['title']))
    if not names:
        names = set(people['name']).union(set(films['title']))
    ed = edges[(edges['source_name'].isin(names)) | (edges['target_name'].isin(names))].copy()
    # add one hop of important support nodes for selected films so the graph feels like a strategy map
    support = set(ed['source_name']).union(set(ed['target_name']))
    if len(support) < 10:
        support = names
    ed = edges[(edges['source_name'].isin(support)) | (edges['target_name'].isin(support))].copy()
    return build_graph(ed, people, films)

Gf = filtered_subgraph()
metrics_f = compute_metrics(Gf)

def fmt_num(x):
    try:
        return f"{int(round(float(x))):,}"
    except Exception:
        return str(x)

chinese_creators = int((people['country_or_region'].isin(chinese_regions)).sum())
american_creators = int((people['country_or_region'].isin(american_regions)).sum())
most_connected = top_nodes(metrics, node_type='Person', key='degree', limit=1)
most_connected_person = most_connected[0][0] if most_connected else '—'
most_connected_director = top_nodes(metrics, node_type='Person', key='degree', limit=20)
most_connected_director = next((n for n, d in most_connected_director if (people[people['name'] == n]['primary_role'].iloc[0] if not people[people['name'] == n].empty else '') == 'Director'), '—')
most_bridge = top_nodes(metrics, node_type='Person', key='betweenness', limit=20)
most_bridge_creator = next((n for n, d in most_bridge if n in set(people['name'])), '—')

st.markdown("<div class='section-title'>Network snapshot</div><div class='section-sub'>The opening panel keeps the first read concise: scale, market balance, and the most strategic nodes in the graph.</div>", unsafe_allow_html=True)

row1 = st.columns(4)
row2 = st.columns(4)
primary_cards = [
    ('People', len(people), 'curated creator nodes'),
    ('Films', len(films), 'curated film nodes'),
    ('Relationships', len(edges), 'graph edges'),
    ('Chinese-language creators', chinese_creators, 'China / Hong Kong / Taiwan'),
]
secondary_cards = [
    ('American creators', american_creators, 'United States'),
    ('Most connected person', most_connected_person, 'highest degree in graph'),
    ('Most connected director', most_connected_director, 'top director by degree'),
    ('Most bridge-like creator', most_bridge_creator, 'highest betweenness'),
]
for col, (label, value, note) in zip(row1, primary_cards):
    col.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)
for col, (label, value, note) in zip(row2, secondary_cards):
    col.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-note'>{note}</div></div>", unsafe_allow_html=True)

st.markdown("<div class='insight-box'><div class='section-title'>Opening intelligence brief</div><div class='section-sub'>MediaGraph maps the entertainment industry as a living network of creators, films, genres, platforms, awards, and audience signals. Instead of searching titles one by one, users can explore creative ecosystems and discover strategic relationships.</div></div>", unsafe_allow_html=True)

tabs = st.tabs([
    'Global creative network',
    'Talent network explorer',
    'Director-actor creative fit',
    'Genre opportunity map',
    'Cross-market bridge analysis',
    'Story positioning assistant',
    'Graph-based explanation demo',
    'Awards and prestige pathway',
    'Strategic insight dashboard',
])

with tabs[0]:
    st.markdown("<div class='section-title'>Global creative network</div><div class='section-sub'>This view shows how creators, films, genres, and institutions cluster together. Larger nodes have more connections. Bridge nodes often connect different countries, genres, or creative communities.</div>", unsafe_allow_html=True)
    fig = make_network_figure(Gf, max_nodes=max_nodes, title='Global creative network')
    st.plotly_chart(fig, use_container_width=True)

with tabs[1]:
    st.markdown("<div class='section-title'>Talent network explorer</div><div class='section-sub'>Pick a creator to inspect their creative neighborhood, collaborator web, and cross-market positioning.</div>", unsafe_allow_html=True)
    talent = st.selectbox('Select a person', sorted(people['name'].tolist()))
    pprof = person_profile(talent, people, films, roles)
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><div class='metric-label'>Primary role</div><div class='metric-value'>{pprof.get('primary_role','—')}</div><div class='metric-note'>{pprof.get('country_or_region','')}</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='metric-label'>Known works</div><div class='metric-value'>{len(pprof['films'])}</div><div class='metric-note'>{', '.join(pprof['films'][:3])}</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='metric-label'>Awards</div><div class='metric-value'>{len(pprof['awards'])}</div><div class='metric-note'>{', '.join(list(pprof['awards'])[:3]) if pprof['awards'] else 'No award signal in demo dataset'}</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><div class='metric-label'>Cross-market score</div><div class='metric-value'>{pprof.get('cross_market_score', 0)}</div><div class='metric-note'>portfolio demo signal</div></div>", unsafe_allow_html=True)

    left, right = st.columns([1.25, 1])
    with left:
        st.markdown("<div class='section-title'>Profile</div>", unsafe_allow_html=True)
        st.write({
            'name': talent,
            'country_or_region': pprof.get('country_or_region', ''),
            'active_decades': pprof.get('active_decades', ''),
            'known_for': pprof.get('known_for', ''),
            'international_recognition_score': pprof.get('international_recognition_score', ''),
            'genre_diversity_score': pprof.get('genre_diversity_score', ''),
            'award_score': pprof.get('award_score', ''),
            'collaboration_score': pprof.get('collaboration_score', ''),
            'cross_market_score': pprof.get('cross_market_score', ''),
        })
        st.markdown("<div class='section-title'>Known works, repeated collaborators, and platform footprint</div>", unsafe_allow_html=True)
        repeat = pprof['collaborators'].most_common(8)
        st.dataframe(pd.DataFrame(repeat, columns=['collaborator', 'count']), use_container_width=True, hide_index=True)
        st.dataframe(pd.DataFrame({'film': pprof['films'][:10]}), use_container_width=True, hide_index=True)
    with right:
        st.markdown("<div class='section-title'>Person-centered ego network</div>", unsafe_allow_html=True)
        ego_fig = build_ego_figure(graph, talent, radius=1, max_nodes=60)
        st.plotly_chart(ego_fig, use_container_width=True)

    st.markdown("<div class='section-title'>Recommended similar talents</div>", unsafe_allow_html=True)
    similars = similar_talents(talent, people, films, roles, limit=8)
    st.dataframe(pd.DataFrame([
        {'name': n, 'similarity_score': s, 'country_or_region': prof.get('country_or_region', ''), 'primary_role': prof.get('primary_role', ''), 'cross_market_score': prof.get('cross_market_score', '')}
        for s, n, prof in similars
    ]), use_container_width=True, hide_index=True)

    st.info(f"{talent} appears as a bridge between auteur cinema, regional industry networks, and cross-market distribution paths." if pprof.get('cross_market_score', 0) >= 60 else f"{talent} shows a more local network shape, with room for cross-market expansion.")

with tabs[2]:
    st.markdown("<div class='section-title'>Director-actor creative fit score</div><div class='section-sub'>The score is a prototype for explainable creative strategy. It is not a prediction model; it is a structured way to compare overlap, pathways, and market fit.</div>", unsafe_allow_html=True)
    directors = sorted(people[people['primary_role'] == 'Director']['name'].tolist())
    performers = sorted(people[people['primary_role'] != 'Director']['name'].tolist())
    col1, col2 = st.columns(2)
    with col1:
        director = st.selectbox('Select director', directors, index=directors.index('Christopher Nolan') if 'Christopher Nolan' in directors else 0)
    with col2:
        actor = st.selectbox('Select actor', performers, index=performers.index('Zhang Ziyi') if 'Zhang Ziyi' in performers else 0)
    fit = creative_fit_score(director, actor, people, films, roles, graph)
    a1, a2, a3, a4 = st.columns(4)
    a1.markdown(f"<div class='metric-card'><div class='metric-label'>Creative fit score</div><div class='metric-value'>{fit['total_score']}</div><div class='metric-note'>prototype score out of 100</div></div>", unsafe_allow_html=True)
    a2.markdown(f"<div class='metric-card'><div class='metric-label'>Past collaboration signal</div><div class='metric-value'>{len(fit['past_collabs'])}</div><div class='metric-note'>{', '.join(fit['past_collabs'][:3]) if fit['past_collabs'] else 'No direct past collaboration in dataset'}</div></div>", unsafe_allow_html=True)
    a3.markdown(f"<div class='metric-card'><div class='metric-label'>Cross-market potential</div><div class='metric-value'>{fit['subscores']['Cross-market potential']}</div><div class='metric-note'>strategy layer</div></div>", unsafe_allow_html=True)
    a4.markdown(f"<div class='metric-card'><div class='metric-label'>Audience compatibility</div><div class='metric-value'>{fit['subscores']['Audience compatibility']}</div><div class='metric-note'>format + platform fit</div></div>", unsafe_allow_html=True)

    radar = go.Figure()
    radar.add_trace(go.Scatterpolar(r=list(fit['subscores'].values()), theta=list(fit['subscores'].keys()), fill='toself', name='fit'))
    radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=False, height=520, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(radar, use_container_width=True)
    st.markdown('<div class="insight-box"><b>Explanation</b><br>' + fit['explanation'] + '</div>', unsafe_allow_html=True)
    if fit['past_collabs']:
        st.write('Comparable past collaborations or shared network motifs:')
        st.write(', '.join(fit['past_collabs']))

with tabs[3]:
    st.markdown("<div class='section-title'>Genre opportunity map</div><div class='section-sub'>Use this to see which directors, actors, countries, awards, and platforms cluster around a genre.</div>", unsafe_allow_html=True)
    genre = st.selectbox('Select genre', all_genres, index=all_genres.index('Drama') if 'Drama' in all_genres else 0)
    gi = genre_insights(genre, people, films, roles)
    g1, g2, g3, g4 = st.columns(4)
    g1.markdown(f"<div class='metric-card'><div class='metric-label'>Films</div><div class='metric-value'>{len(gi['films'])}</div><div class='metric-note'>genre sample size</div></div>", unsafe_allow_html=True)
    g2.markdown(f"<div class='metric-card'><div class='metric-label'>Avg rating</div><div class='metric-value'>{gi['avg_rating']}</div><div class='metric-note'>demo dataset average</div></div>", unsafe_allow_html=True)
    g3.markdown(f"<div class='metric-card'><div class='metric-label'>Avg popularity</div><div class='metric-value'>{gi['avg_popularity']}</div><div class='metric-note'>demo dataset average</div></div>", unsafe_allow_html=True)
    g4.markdown(f"<div class='metric-card'><div class='metric-label'>Cross-market opportunity</div><div class='metric-value'>{gi['cross_market_score']}</div><div class='metric-note'>0-100 score</div></div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(px.bar(x=list(gi['countries'].keys()), y=list(gi['countries'].values()), title='Genre by country', labels={'x': 'Country', 'y': 'Films'}), use_container_width=True)
        decade_counts = gi['films'].assign(decade=gi['films']['year'].astype(int).apply(lambda y: f'{(y//10)*10}s')).groupby('decade').size().reset_index(name='films')
        st.plotly_chart(px.bar(decade_counts, x='decade', y='films', title='Genre by decade'), use_container_width=True)
    with c2:
        st.plotly_chart(px.bar(x=list(gi['platforms'].keys()), y=list(gi['platforms'].values()), title='Genre by platform', labels={'x': 'Platform', 'y': 'Films'}), use_container_width=True)
        st.plotly_chart(px.bar(x=list(gi['awards'].keys()), y=list(gi['awards'].values()), title='Genre by award recognition', labels={'x': 'Award', 'y': 'Mentions'}), use_container_width=True)
    st.dataframe(pd.DataFrame({
        'top directors': pd.Series(gi['directors']),
        'top actors': pd.Series(gi['actors']),
    }), use_container_width=True, hide_index=True)

with tabs[4]:
    st.markdown("<div class='section-title'>Cross-market bridge analysis</div><div class='section-sub'>This section highlights creators and films that connect Chinese and American markets, especially where awards, platforms, and genre overlap create network bridges.</div>", unsafe_allow_html=True)
    bridge_people = top_bridge_people(people, metrics, limit=10)
    bridge_films = top_bridge_films(films, edges, limit=10)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="section-title">Bridge creators</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(bridge_people, columns=['score','creator','region','role','degree','betweenness','cross_market_score']), use_container_width=True, hide_index=True)
    with c2:
        st.markdown('<div class="section-title">Bridge films</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(bridge_films, columns=['score','title','year','market_type','region','rating','popularity']), use_container_width=True, hide_index=True)

    chinese_bridge_candidates = [n for _, n, region, role, _, _, _ in bridge_people if region in chinese_regions or 'Hong Kong' in region or 'Taiwan' in region]
    american_bridge_candidates = [n for _, n, region, role, _, _, _ in bridge_people if region in american_regions]
    path_found = None
    for a in chinese_bridge_candidates:
        for b in american_bridge_candidates:
            if a in graph and b in graph:
                try:
                    p = nx.shortest_path(graph, a, b)
                    if len(p) > 2:
                        path_found = p
                        break
                except Exception:
                    pass
        if path_found:
            break
    if path_found:
        st.success('Example network path between Chinese and American clusters')
        st.write(' → '.join(path_found))
    else:
        st.info('No short path found in the current filtered graph. The bridge nodes still surface through betweenness and shared cross-cultural titles.')

    if bridge_people:
        lead = bridge_people[0][1]
        st.plotly_chart(build_ego_figure(graph, lead, radius=1, max_nodes=55), use_container_width=True)

with tabs[5]:
    st.markdown("<div class='section-title'>Story positioning assistant</div><div class='section-sub'>Enter a project idea and get a rule-based development read: genre lanes, reference titles, candidate creatives, platform fit, audience, and risk notes.</div>", unsafe_allow_html=True)
    prompt = st.text_area('Describe your project idea', 'A female-led sci-fi thriller about memory, family, and identity for a global streaming audience.', height=120)
    story = story_positioning(prompt, people, films)
    s1, s2, s3, s4 = st.columns(4)
    s1.markdown(f"<div class='metric-card'><div class='metric-label'>Recommended genres</div><div class='metric-value'>{', '.join(story['genres'][:2])}</div><div class='metric-note'>rule-based match</div></div>", unsafe_allow_html=True)
    s2.markdown(f"<div class='metric-card'><div class='metric-label'>Reference films</div><div class='metric-value'>{len(story['reference_films'])}</div><div class='metric-note'>{', '.join(story['reference_films'][:3])}</div></div>", unsafe_allow_html=True)
    s3.markdown(f"<div class='metric-card'><div class='metric-label'>Potential directors</div><div class='metric-value'>{len(story['potential_directors'])}</div><div class='metric-note'>{', '.join(story['potential_directors'][:3])}</div></div>", unsafe_allow_html=True)
    s4.markdown(f"<div class='metric-card'><div class='metric-label'>Audience segments</div><div class='metric-value'>{', '.join(story['audience_segments'])}</div><div class='metric-note'>positioning target</div></div>", unsafe_allow_html=True)
    st.markdown(f"<div class='insight-box'><b>Positioning statement</b><br>{story['positioning_statement']}</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write('Potential directors')
        st.write(', '.join(story['potential_directors']))
        st.write('Potential actors')
        st.write(', '.join(story['potential_actors']))
    with c2:
        st.write('Potential platforms')
        st.write(', '.join(story['platforms']))
        st.write('Market risks')
        st.write(' • '.join(story['market_risks']))

with tabs[6]:
    st.markdown("<div class='section-title'>Graph-based explanation demo</div><div class='section-sub'>The graph facts come first. Then the explanation translates them into strategy language.</div>", unsafe_allow_html=True)
    question = st.selectbox('Choose a question', [
        'Why might Ang Lee be a strong bridge figure between Chinese and American cinema?',
        'Which Chinese actors have strong international positioning?',
        'Which American directors are most connected to award-winning prestige dramas?',
        'Which creators connect action cinema across Chinese and American markets?',
    ])
    expl = graph_explanation(question, people, films, roles, metrics)
    st.markdown('<div class="section-title">Retrieved graph facts</div>', unsafe_allow_html=True)
    st.write(expl['facts'])
    st.markdown('<div class="section-title">Generated explanation</div>', unsafe_allow_html=True)
    st.write(expl['explanation'])

with tabs[7]:
    st.markdown("<div class='section-title'>Awards and prestige pathway</div><div class='section-sub'>Which creators and films connect most strongly to awards, festivals, and prestige distribution?</div>", unsafe_allow_html=True)
    award_people = []
    for _, r in people.iterrows():
        award_count = len([a for a in roles[roles['person_name'] == r['name']]['film_title'].tolist() if a]) + int(float(r['award_score']) / 20)
        award_people.append((award_count, r['name'], r['country_or_region'], r['primary_role']))
    award_people.sort(reverse=True)
    award_films = []
    for _, r in films.iterrows():
        award_films.append((len(split_pipe(r['awards'])) + (1 if r['market_type'] in {'festival','prestige','international'} else 0), r['title'], r['year'], r['country_or_region'], r['market_type']))
    award_films.sort(reverse=True)
    c1, c2 = st.columns(2)
    with c1:
        st.dataframe(pd.DataFrame(award_people[:12], columns=['signal','creator','region','role']), use_container_width=True, hide_index=True)
    with c2:
        st.dataframe(pd.DataFrame(award_films[:12], columns=['signal','film','year','region','market_type']), use_container_width=True, hide_index=True)
    pathway = pd.DataFrame([
        {'pathway': 'Chinese-language awards', 'count': len(awards[awards['region'].isin(['Asia','Europe'])])},
        {'pathway': 'American awards', 'count': len(awards[awards['region'] == 'Global'])},
    ])
    st.plotly_chart(px.bar(pathway, x='pathway', y='count', title='Chinese vs American award pathways'), use_container_width=True)

with tabs[8]:
    st.markdown("<div class='section-title'>Strategic insight dashboard</div><div class='section-sub'>A recruiter-friendly summary of the most strategic nodes in the graph.</div>", unsafe_allow_html=True)
    top_people = top_nodes(metrics, node_type='Person', key='degree', limit=10)
    top_bridges = top_nodes(metrics, node_type='Person', key='betweenness', limit=10)
    top_films = top_bridge_films(films, edges, limit=10)
    c1, c2 = st.columns(2)
    with c1:
        st.write('Top central creators')
        st.dataframe(pd.DataFrame([{'name': n, 'degree': d['degree'], 'betweenness': round(d['betweenness'], 4), 'type': d['node_type']} for n, d in top_people]), use_container_width=True, hide_index=True)
        st.write('Top bridge creators')
        st.dataframe(pd.DataFrame([{'name': n, 'degree': d['degree'], 'betweenness': round(d['betweenness'], 4), 'type': d['node_type']} for n, d in top_bridges]), use_container_width=True, hide_index=True)
    with c2:
        st.write('Top cross-market films')
        st.dataframe(pd.DataFrame(top_films, columns=['score','title','year','market_type','region','rating','popularity']), use_container_width=True, hide_index=True)
        st.write('Most award-connected creators')
        award_counts = []
        for _, r in people.iterrows():
            award_counts.append((len(awards[awards['recipient_name'] == r['name']]), r['name'], r['country_or_region']))
        award_counts.sort(reverse=True)
        st.dataframe(pd.DataFrame(award_counts[:10], columns=['award_count','creator','region']), use_container_width=True, hide_index=True)
    st.info('Portfolio relevance: graph database thinking, media strategy, recommendation logic, explainable insight generation, and cross-cultural entertainment analysis in one polished prototype.')

st.caption('MediaGraph is a curated demonstration project built for portfolio presentation. It is intentionally transparent about what is verified, curated, or synthetic.')
