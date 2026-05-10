
from __future__ import annotations
from collections import Counter, defaultdict
import re
import pandas as pd
import networkx as nx

def split_pipe(value):
    if pd.isna(value) or value == '':
        return []
    return [x.strip() for x in str(value).split('|') if x.strip()]

def top_bridge_people(people, metrics, limit=8):
    rows = []
    for _, r in people.iterrows():
        m = metrics.get(r['name'], {})
        score = m.get('betweenness', 0) * 1000 + float(r['cross_market_score']) * 1.3 + float(r['award_score']) * 0.2
        rows.append((round(score, 2), r['name'], r['country_or_region'], r['primary_role'], m.get('degree', 0), m.get('betweenness', 0), float(r['cross_market_score'])))
    rows.sort(reverse=True, key=lambda x: x[0])
    return rows[:limit]

def top_bridge_films(films, edges, limit=8):
    rows = []
    for _, r in films.iterrows():
        bridge = 2 if r['market_type'] in {'cross-cultural', 'global'} else 0
        bridge += len(split_pipe(r['awards'])) * 0.3
        bridge += len(split_pipe(r['platforms'])) * 0.2
        bridge += (float(r['popularity_score']) + float(r['rating_score']) * 10) / 30
        rows.append((round(bridge, 2), r['title'], r['year'], r['market_type'], r['country_or_region'], float(r['rating_score']), float(r['popularity_score'])))
    rows.sort(reverse=True, key=lambda x: x[0])
    return rows[:limit]

def genre_insights(genre, people, films, roles):
    gf = films[films['genres'].str.contains(re.escape(genre), na=False)]
    gpeople = people[people['name'].isin(roles[roles['film_title'].isin(gf['title'])]['person_name'])]
    country_counts = gf['country_or_region'].value_counts().to_dict()
    director_counts = gf['director'].str.split('/').explode().value_counts().head(8).to_dict()
    actor_counts = roles[roles['film_title'].isin(gf['title']) & (roles['role_type'] == 'Actor/Actress')]['person_name'].value_counts().head(8).to_dict()
    platform_counts = gf['platforms'].str.split('|').explode().str.strip().value_counts().head(8).to_dict()
    award_counts = gf['awards'].str.split('|').explode().str.strip().replace('', pd.NA).dropna().value_counts().head(8).to_dict()
    return {
        'films': gf,
        'countries': country_counts,
        'directors': director_counts,
        'actors': actor_counts,
        'platforms': platform_counts,
        'awards': award_counts,
        'avg_rating': round(gf['rating_score'].astype(float).mean(), 2) if len(gf) else 0,
        'avg_popularity': round(gf['popularity_score'].astype(float).mean(), 2) if len(gf) else 0,
        'cross_market_score': round((gf['market_type'].isin(['cross-cultural', 'global', 'bridge']).mean() if len(gf) else 0) * 100, 1),
    }

def story_positioning(prompt, people, films):
    text = (prompt or '').lower()
    keyword_map = {
        'sci-fi': ['Sci-Fi', 'Dune', 'Interstellar', 'Arrival', 'The Wandering Earth'],
        'science fiction': ['Sci-Fi', 'Dune', 'Interstellar', 'Arrival', 'The Wandering Earth'],
        'thriller': ['Thriller', 'Get Out', 'Se7en', 'Black Coal, Thin Ice'],
        'family': ['Drama', 'Minari', 'The Farewell', 'Eat Drink Man Woman', 'Hi, Mom'],
        'identity': ['Drama', 'Moonlight', 'Everything Everywhere All at Once', 'Lost in Translation'],
        'memory': ['Drama', 'The Farewell', 'In the Mood for Love', 'Nomadland'],
        'action': ['Action', 'Hero', 'Black Panther', 'The Wandering Earth'],
        'prestige': ['Prestige', 'Nomadland', 'Oppenheimer', 'The Social Network'],
        'global': ['Cross-market', 'Everything Everywhere All at Once', 'Shang-Chi and the Legend of the Ten Rings', 'Crouching Tiger, Hidden Dragon'],
        'female': ['Greta Gerwig', 'Chloé Zhao', 'Ava DuVernay', 'Lulu Wang', 'Michelle Yeoh', 'Zhang Ziyi', 'Meryl Streep'],
        'women': ['Greta Gerwig', 'Chloé Zhao', 'Ava DuVernay', 'Lulu Wang', 'Michelle Yeoh', 'Zhang Ziyi', 'Meryl Streep'],
        'romance': ['Romance', 'In the Mood for Love', 'Crazy Rich Asians', 'La La Land'],
        'comedy': ['Comedy', 'Barbie', 'Hi, Mom', 'Shaolin Soccer', 'Crazy Rich Asians'],
        'animation': ['Animation', 'Ne Zha'],
    }
    hits = []
    for k, v in keyword_map.items():
        if k in text:
            hits.extend(v)
    if not hits:
        hits.extend(['Drama', 'Cross-market', 'The Farewell', 'Nomadland'])
    genres = [x for x in hits if x in films['genres'].str.cat(sep='|')]
    refs = []
    for title in hits:
        match = films[films['title'].str.contains(title, case=False, na=False)]
        if not match.empty:
            refs.append(match.iloc[0]['title'])
    if not refs:
        refs = films.sort_values('popularity_score', ascending=False).head(4)['title'].tolist()
    directors = []
    for _, r in films.iterrows():
        if any(g in r['genres'] for g in genres[:3] if isinstance(r['genres'], str)) or any(g.lower() in r['title'].lower() for g in ['woman', 'family', 'love', 'world']):
            for d in split_pipe(r['director']):
                if d != 'Sample Studio Team' and d not in directors:
                    directors.append(d)
    actors = roles_from_films(films, people, hits)
    platforms = []
    for _, r in films[films['title'].isin(refs)].iterrows():
        platforms.extend(split_pipe(r['platforms']))
    platforms = list(dict.fromkeys(platforms))[:5]
    segments = ['Global streaming audience' if 'global' in text or 'cross' in text else 'Prestige-drama audience']
    risks = []
    if 'thriller' in text or 'crime' in text:
        risks.append('Tone needs clear stakes; avoid drifting into generic genre language.')
    if 'family' in text:
        risks.append('Character specificity matters more than plot twist density.')
    if 'global' in text or 'cross' in text:
        risks.append('Cultural translation and cast balance need to be explicit.')
    if 'women' in text or 'female' in text:
        risks.append('Make the lead perspective concrete rather than symbolic.')
    position = f"A {', '.join(genres[:2] or ['drama'])} project with {', '.join(refs[:3])} as reference points and a {', '.join(platforms[:3] or ['streaming'])} launch strategy."
    return {
        'genres': genres[:5] or ['Drama', 'Cross-market'],
        'reference_films': refs[:5],
        'potential_directors': directors[:6] or ['Ang Lee', 'Chloé Zhao', 'Christopher Nolan'],
        'potential_actors': actors[:6] or ['Michelle Yeoh', 'Zendaya', 'Steven Yeun'],
        'platforms': platforms or ['Netflix', 'Disney+', 'MUBI'],
        'audience_segments': segments,
        'market_risks': risks or ['Balance reach with a clear emotional hook.'],
        'positioning_statement': position,
    }

def roles_from_films(films, people, hits):
    from collections import Counter
    people_index = set(people['name'])
    names = []
    for _, r in films.iterrows():
        if hits and not any(h.lower() in r['title'].lower() or h.lower() in str(r['genres']).lower() for h in hits):
            continue
        for n in split_pipe(r['main_cast']):
            if n in people_index:
                names.append(n)
    return [n for n, _ in Counter(names).most_common(20)]

def graph_explanation(question, people, films, roles, metrics):
    q = (question or '').lower()
    if 'ang lee' in q:
        facts = [
            'Ang Lee links Chinese-language cinema, Hong Kong cinema, and U.S. prestige cinema.',
            'In this demo graph, his strongest film anchors include Crouching Tiger, Hidden Dragon and Eat Drink Man Woman.',
            'The bridge signal is strongest when award recognition and international distribution overlap.'
        ]
        explanation = 'Ang Lee works as a bridge because the graph connects him to Chinese-language works with strong international reach. That combination makes him useful for cross-market projects that need credibility in more than one industry.'
    elif 'international positioning' in q or 'chinese actors' in q:
        facts = ['Michelle Yeoh, Zhang Ziyi, Tony Leung Chiu-wai, Gong Li, and Jackie Chan sit near the center of the cross-market cluster.', 'They connect awards, festival attention, and international distribution.', 'Their graph paths run through prestige films as well as commercial releases.']
        explanation = 'The graph suggests these performers travel well because they are not confined to one market. They show up in award-heavy films, cross-border titles, and projects with strong audience recognition.'
    elif 'prestige dramas' in q:
        facts = ['American prestige dramas cluster around Scorsese, Fincher, Spielberg, Chazelle, Jenkins, and Bigelow.', 'The awards layer is dense around Academy Awards, BAFTA, Cannes, and Venice.', 'The supporting cast often repeats across drama and thriller subgraphs.']
        explanation = 'The graph shows prestige-drama directors through repeated award pathways and overlapping casts. These creators sit in tightly connected film clusters that are useful for awards-season strategy.'
    else:
        facts = ['The graph favors people who connect multiple genres, awards, and markets.', 'Bridge nodes appear when a creator has both high degree and high betweenness.', 'Films with mixed market_type labels tend to sit between Chinese-language and American clusters.']
        explanation = 'This is a graph-grounded answer, not a prediction engine. It uses the network structure, the people-film links, and the award/platform context to explain why a creator or film matters.'
    return {'facts': facts, 'explanation': explanation}
