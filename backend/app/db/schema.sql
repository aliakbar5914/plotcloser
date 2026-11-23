-- PlotCloser database tables.
-- Safe to run many times: "IF NOT EXISTS" skips tables that already exist.

-- Properties and cars that agencies/dealers want to sell or rent.
CREATE TABLE IF NOT EXISTS listings (
    id           SERIAL PRIMARY KEY,
    agency_id    TEXT NOT NULL DEFAULT 'capital-estates',
    type         TEXT NOT NULL CHECK (type IN ('property', 'car')),
    title        TEXT NOT NULL,
    city         TEXT NOT NULL,
    area         TEXT NOT NULL,          -- sector/society for property, showroom area for car
    size_label   TEXT,                   -- "10 marla", "1 kanal", or car year/mileage
    size_marla   NUMERIC,                -- for property search (1 kanal = 20 marla)
    price_pkr    BIGINT NOT NULL,
    purpose      TEXT NOT NULL DEFAULT 'sale' CHECK (purpose IN ('sale', 'rent')),
    bedrooms     INT,
    description  TEXT,
    image_url    TEXT,
    status       TEXT NOT NULL DEFAULT 'available',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One lead per user: what we learned about them + their score + pipeline stage.
CREATE TABLE IF NOT EXISTS leads (
    id              SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL UNIQUE,
    name            TEXT,
    interest_type   TEXT,                -- property or car
    budget_pkr      BIGINT,
    preferred_area  TEXT,
    timeline_months INT,                 -- buying within how many months
    payment_type    TEXT,                -- cash / installment / bank loan
    score           INT,                 -- 1 to 10
    temperature     TEXT,                -- hot / warm / cold
    stage           TEXT NOT NULL DEFAULT 'new',  -- new, qualified, visit_booked, closed
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE leads ADD COLUMN IF NOT EXISTS timeline_months INT;
ALTER TABLE leads DROP COLUMN IF EXISTS timeline;

-- Site visits / test drives that a user confirmed.
CREATE TABLE IF NOT EXISTS visits (
    id              SERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    thread_id       TEXT NOT NULL,
    listing_id      INT NOT NULL REFERENCES listings(id),
    requested_time  TEXT NOT NULL,       -- kept as text: "Saturday 4 PM"
    status          TEXT NOT NULL DEFAULT 'booked',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Follow-up reminders that a user agreed to.
CREATE TABLE IF NOT EXISTS follow_ups (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL,
    due         TEXT NOT NULL,           -- e.g. "next Monday"
    note        TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'scheduled',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Risky actions waiting for the user's "yes" (human-in-the-loop).
CREATE TABLE IF NOT EXISTS pending_actions (
    id          SERIAL PRIMARY KEY,
    user_id     TEXT NOT NULL,
    thread_id   TEXT NOT NULL,
    action      TEXT NOT NULL,           -- book_visit / schedule_follow_up
    payload     JSONB NOT NULL,
    turn_id     TEXT,                    -- which /chat call created this draft
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE pending_actions ADD COLUMN IF NOT EXISTS turn_id TEXT;

-- Every /chat call, for the admin dashboard and the benchmark.
CREATE TABLE IF NOT EXISTS chat_logs (
    id            SERIAL PRIMARY KEY,
    user_id       TEXT NOT NULL,
    thread_id     TEXT NOT NULL,
    user_message  TEXT NOT NULL,
    reply         TEXT NOT NULL,
    tool_calls    JSONB NOT NULL DEFAULT '[]',
    tokens_in     INT NOT NULL DEFAULT 0,
    tokens_out    INT NOT NULL DEFAULT 0,
    latency_ms    INT NOT NULL DEFAULT 0,
    blocked       BOOLEAN NOT NULL DEFAULT false,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes make "WHERE user_id = ..." lookups fast.
CREATE INDEX IF NOT EXISTS idx_visits_user     ON visits(user_id);
CREATE INDEX IF NOT EXISTS idx_followups_user  ON follow_ups(user_id);
CREATE INDEX IF NOT EXISTS idx_pending_user    ON pending_actions(user_id, thread_id);
CREATE INDEX IF NOT EXISTS idx_chatlogs_user   ON chat_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_listings_search ON listings(type, city, price_pkr);
