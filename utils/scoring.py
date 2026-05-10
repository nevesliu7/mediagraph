
from __future__ import annotations
from collections import Counter, defaultdict
import math
import networkx as nx
import pandas as pd

def _split(value):
    if pd.isna(value) or value == '':
        return []
    return [x.strip() for x in str(value).split('|') if x.strip()]

def person_profile(name, people, films, roles):
    p = people[people['name'] == name]
    profile = {
        'name': name,
        'genres': set(),
        'themes': set(),
        'awards': set(),
        'platforms': set(),
        'countries': set(),
        'films': [],
        'collaborators': Counter(),
        'roles': [],
    }
    if not p.empty:
        profile.update(p.iloc[0].to_dict())
    person_films = roles[roles['person_name'] == name]['film_title'].tolist()
    profile['films'] = person_films
    for title in person_films:
        f = films[films['title'] == title]
        if f.empty:
            continue
        row = f.iloc[0]
        profile['genres'].update(_split(row['genres']))
        profile['themes'].update(_split(row['themes']))
        profile['awards'].update(_split(row['awards']))
        profile['platforms'].update(_split(row['platforms']))
        profile['countries'].add(row['country_or_region'])
    for film_title in person_films:
        rel = roles[roles['film_title'] == film_title]
        for collaborator in rel['person_name'].tolist():
            if collaborator != name:
                profile['collaborators'][collaborator] += 1
    return profile

def jaccard(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 0.0
    return len(a & b) / max(1, len(a | b))

def creative_fit_score(director, actor, people, films, roles, graph=None):
    dp = person_profile(director, people, films, roles)
    ap = person_profile(actor, people, films, roles)
    genre_overlap = jaccard(dp['genres'], ap['genres'])
    theme_overlap = jaccard(dp['themes'], ap['themes'])
    award_overlap = jaccard(dp['awards'], ap['awards'])
    market_overlap = jaccard(dp['countries'], ap['countries'])
    collab_distance = 0.0
    if graph is not None and director in graph and actor in graph:
        try:
            path = nx.shortest_path(graph, director, actor)
            collab_distance = max(0.0, 1.0 - min(len(path) - 1, 5) / 5)
        except Exception:
            collab_distance = 0.1
    cross_market = ((float(dp.get('cross_market_score', 50)) + float(ap.get('cross_market_score', 50))) / 2) / 100
    audience = 0.5 + 0.5 * min(1.0, (len(dp['platforms']) + len(ap['platforms'])) / 10)
    score = (
        genre_overlap * 0.25 + theme_overlap * 0.15 + award_overlap * 0.1 +
        market_overlap * 0.1 + collab_distance * 0.15 + cross_market * 0.15 + audience * 0.1
    )
    score = round(score * 100, 1)
    subscores = {
        'Genre overlap': round(genre_overlap * 100, 1),
        'Thematic fit': round(theme_overlap * 100, 1),
        'Award pathway similarity': round(award_overlap * 100, 1),
        'Market compatibility': round(market_overlap * 100, 1),
        'Collaboration proximity': round(collab_distance * 100, 1),
        'Cross-market potential': round(cross_market * 100, 1),
        'Audience compatibility': round(audience * 100, 1),
    }
    past_collabs = []
    d_films = set(roles[roles['person_name'] == director]['film_title'])
    a_films = set(roles[roles['person_name'] == actor]['film_title'])
    shared = list(d_films & a_films)
    if shared:
        past_collabs = shared[:5]
    else:
        shared_director_people = roles[roles['film_title'].isin(d_films)]['person_name'].tolist()
        counts = Counter(shared_director_people)
        for k, v in counts.most_common(5):
            if k != director:
                past_collabs.append(k)
    explanation = f"{director} and {actor} share {len(dp['genres'] & ap['genres'])} genres, {len(dp['themes'] & ap['themes'])} themes, and a cross-market profile that supports a mixed audience strategy."
    return {'total_score': score, 'subscores': subscores, 'past_collabs': past_collabs, 'explanation': explanation, 'director_profile': dp, 'actor_profile': ap}

def similar_talents(name, people, films, roles, limit=8):
    base = person_profile(name, people, films, roles)
    rows = []
    for other in people['name'].tolist():
        if other == name:
            continue
        prof = person_profile(other, people, films, roles)
        s = 0.0
        s += jaccard(base['genres'], prof['genres']) * 0.35
        s += jaccard(base['themes'], prof['themes']) * 0.25
        s += jaccard(base['awards'], prof['awards']) * 0.15
        s += jaccard(base['countries'], prof['countries']) * 0.1
        s += min(len(set(base['films']) & set(prof['films'])), 3) * 0.05
        s += (float(base.get('cross_market_score', 50)) + float(prof.get('cross_market_score', 50))) / 200 * 0.1
        rows.append((round(s * 100, 1), other, prof))
    rows.sort(reverse=True, key=lambda x: x[0])
    return rows[:limit]
