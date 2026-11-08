CREATE TABLE IF NOT EXISTS treningi (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    data DATE NOT NULL,
    nazwa TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cwiczenia (
    id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    trening_id INTEGER NOT NULL REFERENCES treningi(id) ON DELETE CASCADE,
    nazwa_cwiczenia TEXT NOT NULL,
    serie INTEGER NOT NULL,
    powtorzenia INTEGER NOT NULL,
    ciezar_kg NUMERIC(5,2) DEFAULT 0
);

INSERT INTO treningi (data, nazwa) VALUES 
('2026-11-01', 'Góra ciała - Siła'),
('2026-11-03', 'Trening Obwodowy');

INSERT INTO cwiczenia (trening_id, nazwa_cwiczenia, serie, powtorzenia, ciezar_kg) VALUES 
(1, 'Wyciskanie na maszynie', 4, 10, 45.0),
(1, 'Rozpiętki Butterfly', 3, 12, 50.0),
(2, 'Wznosy bokiem', 4, 15, 10.0);