
CREATE CONSTRAINT person_name IF NOT EXISTS FOR (p:Person) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT film_title IF NOT EXISTS FOR (f:Film) REQUIRE f.title IS UNIQUE;
CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE;
CREATE CONSTRAINT award_name IF NOT EXISTS FOR (a:Award) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT platform_name IF NOT EXISTS FOR (p:Platform) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT country_name IF NOT EXISTS FOR (c:Country) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT language_name IF NOT EXISTS FOR (l:Language) REQUIRE l.name IS UNIQUE;
CREATE CONSTRAINT decade_name IF NOT EXISTS FOR (d:Decade) REQUIRE d.name IS UNIQUE;
CREATE CONSTRAINT audience_name IF NOT EXISTS FOR (s:AudienceSegment) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT theme_name IF NOT EXISTS FOR (t:Theme) REQUIRE t.name IS UNIQUE;

// Sample labels and relationships
// (:Person)-[:DIRECTED]->(:Film)
// (:Person)-[:ACTED_IN]->(:Film)
// (:Film)-[:BELONGS_TO_GENRE]->(:Genre)
// (:Film)-[:DISTRIBUTED_ON]->(:Platform)
// (:Film)-[:WON_AWARD]->(:Award)
// (:Film)-[:HAS_THEME]->(:Theme)
// (:Person)-[:CROSSES_MARKET]->(:Country)
