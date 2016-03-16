-- postgresql commands to start our db
DROP TABLE IF EXISTS urls;
CREATE TABLE urls (
  id serial PRIMARY KEY,
  url VARCHAR(2083) NOT NULL,
  shortened VARCHAR(255) UNIQUE NOT NULL
);
CREATE INDEX idx_shortened ON urls (shortened);
