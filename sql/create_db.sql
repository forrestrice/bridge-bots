-- postgres -D /usr/local/var/postgres/
-- psql -U frice -d bridge -a -f sql/create_db.sql
-- psql -U frice -d bridge
CREATE TABLE hands (
    id SERIAL PRIMARY KEY,
    dealer TEXT NOT NULL,
    ew_vulnerable BOOLEAN NOT NULL,
    ns_vulnerable BOOLEAN NOT NULL,
    nspades TEXT[] NOT NULL DEFAULT '{}',
    nhearts TEXT[] NOT NULL DEFAULT '{}',
    ndiamonds TEXT[] NOT NULL DEFAULT '{}',
    nclubs TEXT[] NOT NULL DEFAULT '{}',
    espades TEXT[] NOT NULL DEFAULT '{}',
    ehearts TEXT[] NOT NULL DEFAULT '{}',
    ediamonds TEXT[] NOT NULL DEFAULT '{}',
    eclubs TEXT[] NOT NULL DEFAULT '{}',
    sspades TEXT[] NOT NULL DEFAULT '{}',
    shearts TEXT[] NOT NULL DEFAULT '{}',
    sdiamonds TEXT[] NOT NULL DEFAULT '{}',
    sclubs TEXT[] NOT NULL DEFAULT '{}',
    wspades TEXT[] NOT NULL DEFAULT '{}',
    whearts TEXT[] NOT NULL DEFAULT '{}',
    wdiamonds TEXT[] NOT NULL DEFAULT '{}',
    wclubs TEXT[] NOT NULL DEFAULT '{}'
);

CREATE TABLE players (
    id SERIAL PRIMARY KEY,
    first_name TEXT,
    last_name TEXT
);

CREATE TABLE hand_scores (
    hand_id SERIAL references hands(id),
    north SERIAL references players(id),
    east SERIAL references players(id),
    south SERIAL references players(id),
    west SERIAL references players(id),
    contract_level int,
    contract_suit TEXT,
    contract_doubles int,
    declarer TEXT NOT NULL,
    result int,
    score int NOT NULL
);

CREATE TABLE recap_files(
    file_name TEXT not null
);