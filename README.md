
# MediaGraph

A graph-based media intelligence system for exploring creative networks across Chinese and American film industries.

[Live demo placeholder](#) · [Screenshot placeholder](assets/screenshots/)

## Why I built this

Most media tools treat films, creators, awards, genres, and platforms as separate tables. MediaGraph models the industry as a connected network so you can see how talent, taste, recognition, and distribution shape strategic opportunities.

This is designed to feel like an internal tool for a streaming platform, studio, talent agency, or entertainment investor, not a basic movie browser.

## What it does

- Maps creators, films, genres, awards, platforms, countries, languages, decades, audience segments, and themes in one graph
- Surfaces bridge figures between Chinese-language cinema and American cinema
- Scores director-actor creative fit with explainable sub-scores
- Shows genre opportunity maps by country, decade, awards, and platform
- Generates graph-grounded strategy summaries from retrieved network facts
- Supports an optional Neo4j workflow with reusable Cypher examples

## Key features

### 1) Opening intelligence brief
A polished dashboard summary with metric cards for people, films, relationships, Chinese-language creators, American creators, and the most central / bridge-like nodes.

### 2) Global creative network
An interactive network graph with filters for:
- country or region
- role
- genre
- decade
- award status
- market type
- platform

### 3) Talent network explorer
Select a person and inspect:
- profile summary
- known works
- collaborators
- genres, awards, and platforms
- centrality and cross-market signals
- similar talents
- ego network visualization

### 4) Director-actor creative fit score
A transparent prototype score built from:
- genre overlap
- thematic compatibility
- award pathway similarity
- collaboration proximity
- audience compatibility
- cross-market potential

### 5) Genre opportunity map
Shows which creators, countries, awards, and platforms cluster around a genre.

### 6) Cross-market bridge analysis
Highlights creators and films that connect Chinese and American markets using:
- betweenness centrality
- degree centrality
- cross-market score
- bridge films and bridge creators

### 7) Story positioning assistant
A rule-based development assistant for project ideas. It returns:
- recommended genres
- reference films
- potential directors
- potential actors
- likely platforms
- audience segments
- market risks
- a positioning statement

### 8) Graph-based explanation demo
Shows graph facts first, then a concise explanation built from those facts. The goal is transparency, not hype.

### 9) Awards and prestige pathway
Surfaces creators and films connected to major awards and festival pathways.

### 10) Strategic insight dashboard
Summarizes the most central creators, bridge creators, cross-market films, award-connected creators, and promising pairings.

## Data model

Nodes:
- Person
- Film
- Genre
- Award
- Platform
- Country
- Language
- Decade
- AudienceSegment
- Theme

Relationships:
- DIRECTED
- ACTED_IN
- WROTE
- PRODUCED
- BELONGS_TO_GENRE
- WON_AWARD
- NOMINATED_FOR
- DISTRIBUTED_ON
- RELEASED_IN
- MADE_IN_COUNTRY
- USES_LANGUAGE
- HAS_THEME
- APPEALS_TO
- SIMILAR_TO
- COLLABORATED_WITH
- CROSSES_MARKET

## How the Creative Fit Score works

The score is a prototype, not a predictive model. It combines:
- genre overlap between director and actor filmographies
- thematic overlap
- award pathway similarity
- collaboration proximity in the graph
- audience compatibility through platform footprint
- cross-market potential based on the creator profiles

Each sub-score is visible in the app so the logic stays explainable.

## How the Cross-Market Bridge Analysis works

MediaGraph identifies bridge nodes by combining:
- betweenness centrality
- degree centrality
- cross-market score from the creator profile
- bridge-film signals from mixed-market titles

It is especially useful for spotting creators and projects that can travel between Chinese-language markets and the U.S. market.

## How the graph-based explanation demo works

The app first retrieves graph facts, such as:
- connected films
- awards and festival signals
- cluster membership
- cross-market links

It then turns those facts into a short strategy explanation. The point is to make the reasoning visible before the narrative.

## Tech stack

- Python
- Streamlit
- Pandas
- NetworkX
- Plotly
- Neo4j optional
- scikit-learn optional for future similarity work

## How to run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Optional Neo4j setup

1. Start Neo4j locally or in Aura.
2. Load the schema in `graph/neo4j_schema.cypher`.
3. Use `graph/sample_queries.cypher` to explore bridge creators, awards, and genre clusters.
4. Expand the demo CSVs with verified public data if you want a larger production-ready graph.

## Project structure

```text
mediagraph/
├── app.py
├── requirements.txt
├── README.md
├── data/
│   ├── people.csv
│   ├── films.csv
│   ├── roles.csv
│   ├── awards.csv
│   ├── platforms.csv
│   ├── audience_signals.csv
│   └── edges.csv
├── graph/
│   ├── neo4j_schema.cypher
│   └── sample_queries.cypher
├── assets/
│   └── screenshots/
└── utils/
    ├── graph_builder.py
    ├── scoring.py
    └── insights.py
```

## Sample questions the system can answer

- Which directors and actors are most central in Chinese and American film networks?
- Which creators frequently cross genres, countries, or platforms?
- Which directors have strong award pathways?
- Which actor-director combinations look strategically promising?
- What kinds of films connect Chinese and American entertainment markets?
- Which creators are bridge figures between Chinese-language cinema and American cinema?

## Data ethics and limitations

- The dataset is a curated demonstration dataset, not a complete industry database.
- Some sample fields are synthetic or generalized when verified public data was not necessary for the prototype.
- The README and app intentionally avoid claiming prediction accuracy.
- The project does not scrape private data or use non-public personal information.

## Future improvements

- Replace demo data with verified public datasets from TMDb, IMDb, Wikidata, or official award feeds
- Connect the app to Neo4j directly for graph queries
- Add saved searches and bookmarks
- Add deeper community detection and path explanations
- Add richer filtering by audience segment and distribution window

## Portfolio relevance

MediaGraph demonstrates:
- graph database thinking
- connected data modeling
- media strategy judgment
- recommendation logic
- explainable insight generation
- cross-cultural entertainment analysis
- interactive dashboard design
- data storytelling
- product thinking

## Repository metadata

- Recommended repo name: `mediagraph`
- Recommended repository description: Graph-based media intelligence prototype for exploring creative networks, cross-market talent bridges, and content strategy across Chinese and American film industries.

## Resume bullet

Built MediaGraph, a hybrid Vercel-ready bubble graph + Streamlit analyst prototype that maps Chinese and American film ecosystems, scores director-actor creative fit, and surfaces cross-market talent and award pathways through explainable network analysis.


## Hybrid web experience

MediaGraph is designed as a two-layer portfolio product:

- Web experience: `web/` contains a Vercel-ready static site with draggable bubble-network exploration.
- Analyst view: `app.py` runs the deeper Streamlit strategy workspace with fit scoring, bridge analysis, and graph explanations.

### Suggested deployment setup

- GitHub repo: source of truth for code, data, schema, and documentation
- Vercel: deploy the `web/` directory as the public product-facing site
- Streamlit Community Cloud: deploy `app.py` as the analyst console

### Why this split works

- The web site feels like a polished product with bubbles, hover, drag, and selection.
- Streamlit is better for fast iteration on strategy logic, score explanation, and analyst workflows.
- Both views share the same curated CSV data model.

### Vercel setup

Set the project Root Directory to `web/` so the static site serves `index.html`, `app.js`, `styles.css`, and `graph-data.json`.
