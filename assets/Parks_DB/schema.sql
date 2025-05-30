CREATE TABLE parks (park_ID INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE);
CREATE TABLE sqlite_sequence(name,seq);
CREATE TABLE details (detail_ID INTEGER PRIMARY KEY AUTOINCREMENT, park_ID INTEGER NOT NULL, location TEXT, established INTEGER, size_acres INTEGER, ecosystems TEXT, unique_feature TEXT, description TEXT, FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE);
CREATE TABLE camping (camping_ID INTEGER PRIMARY KEY AUTOINCREMENT, park_ID INTEGER NOT NULL, type TEXT, capacity TEXT, amenities TEXT, notes TEXT, FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE);
CREATE TABLE fees (fee_ID INTEGER PRIMARY KEY AUTOINCREMENT, park_ID INTEGER NOT NULL, category TEXT, cost TEXT, notes TEXT, FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE);
CREATE TABLE seasons (season_ID INTEGER PRIMARY KEY AUTOINCREMENT, park_ID INTEGER NOT NULL, season_name TEXT, dates TEXT, characteristics TEXT, FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE);
CREATE TABLE attractions (attraction_ID INTEGER PRIMARY KEY AUTOINCREMENT, park_ID INTEGER NOT NULL, attraction_name TEXT, description TEXT, notes TEXT, FOREIGN KEY (park_ID) REFERENCES parks (park_ID) ON DELETE CASCADE);
