ALTER TABLE treningi ADD COLUMN IF NOT EXISTS usunieto_o TIMESTAMPTZ;

CREATE TABLE IF NOT EXISTS historia_treningow (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trening_id INTEGER NOT NULL REFERENCES treningi(id),
    operacja TEXT NOT NULL CHECK (operacja IN ('dodanie', 'edycja', 'usuniecie')),
    autor VARCHAR(100) NOT NULL,
    czas TIMESTAMPTZ NOT NULL DEFAULT clock_timestamp(),
    przed JSONB,
    po JSONB
);

CREATE INDEX IF NOT EXISTS historia_treningow_trening_idx
    ON historia_treningow (trening_id, id);
