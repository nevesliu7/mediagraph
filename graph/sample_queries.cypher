
// Top bridge creators between Chinese and American markets
MATCH (p:Person)-[r]->(n)
WHERE r.relationship IN ['CROSSES_MARKET','WON_AWARD']
RETURN p.name AS creator, count(r) AS signal_strength
ORDER BY signal_strength DESC
LIMIT 20;

// Award pathways for prestige strategy
MATCH (p:Person)-[:WON_AWARD]->(a:Award)
RETURN p.name AS creator, collect(a.name) AS awards
ORDER BY size(awards) DESC
LIMIT 20;

// Genre opportunity map
MATCH (f:Film)-[:BELONGS_TO_GENRE]->(g:Genre {name: $genre})
RETURN f.title AS title, f.year AS year, f.market_type AS market_type
ORDER BY f.popularity_score DESC;

// Creative fit discovery
MATCH (d:Person {name: $director})-[:DIRECTED]->(f:Film)<-[:ACTED_IN]-(a:Person {name: $actor})
RETURN f.title AS past_collaboration;
