-- sqlite3 commands to start our db
DROP TABLE IF EXISTS urls;
CREATE TABLE urls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  shortened TEXT UNIQUE NOT NULL
);
CREATE INDEX idx_shortened ON urls (shortened);
