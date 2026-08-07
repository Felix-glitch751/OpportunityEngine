import json
import sqlite3
from pathlib import Path

from App.models import Opportunity


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "Data"
DATABASE_PATH = DATA_DIR / "opportunities.db"


class OpportunityDatabase:
    """
    Administra el historial completo de oportunidades detectadas.
    """

    def __init__(self, database_path: Path = DATABASE_PATH) -> None:
        self.database_path = database_path
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_tables()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_tables(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS opportunities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    country TEXT NOT NULL,
                    category TEXT NOT NULL,
                    description TEXT,
                    currency TEXT,
                    reward_amount REAL DEFAULT 0,
                    required_cost REAL DEFAULT 0,
                    estimated_minutes INTEGER DEFAULT 0,
                    probability REAL DEFAULT 0,
                    score REAL DEFAULT 0,
                    requirements TEXT,
                    tags TEXT,
                    published_at TEXT,
                    expires_at TEXT,
                    detected_at TEXT NOT NULL,
                    raw_data TEXT,
                    queue TEXT NOT NULL,
                    notified INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'pending'
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunities_score
                ON opportunities(score)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunities_score
                ON opportunities(score)
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS source_state (
                    source_id TEXT PRIMARY KEY,
                    last_checked_at TEXT,
                    last_status TEXT,
                    consecutive_errors INTEGER DEFAULT 0
                )
                """

            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunities_queue
                ON opportunities(queue)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_opportunities_source
                ON opportunities(source_id)
                """
            )

    def save(
        self,
        opportunity: Opportunity,
        threshold: float = 50.0,
    ) -> bool:
        """
        Guarda una oportunidad.

        Devuelve:
        True  -> se guardó correctamente.
        False -> ya existía una oportunidad con la misma URL.
        """

        opportunity.validate()

        queue = (
            "primary"
            if opportunity.should_notify(threshold)
            else "secondary"
        )

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO opportunities (
                        source_id,
                        source_name,
                        title,
                        url,
                        country,
                        category,
                        description,
                        currency,
                        reward_amount,
                        required_cost,
                        estimated_minutes,
                        probability,
                        score,
                        requirements,
                        tags,
                        published_at,
                        expires_at,
                        detected_at,
                        raw_data,
                        queue
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        opportunity.source_id,
                        opportunity.source_name,
                        opportunity.title,
                        opportunity.url,
                        opportunity.country,
                        opportunity.category,
                        opportunity.description,
                        opportunity.currency,
                        opportunity.reward_amount,
                        opportunity.required_cost,
                        opportunity.estimated_minutes,
                        opportunity.probability,
                        opportunity.score,
                        json.dumps(
                            opportunity.requirements,
                            ensure_ascii=False,
                        ),
                        json.dumps(
                            opportunity.tags,
                            ensure_ascii=False,
                        ),
                        opportunity.published_at,
                        opportunity.expires_at,
                        opportunity.detected_at,
                        json.dumps(
                            opportunity.raw_data,
                            ensure_ascii=False,
                        ),
                        queue,
                    ),
                )

            return True

        except sqlite3.IntegrityError:
            return False

    def get_primary_queue(self) -> list[dict]:
        return self._get_by_queue("primary")

    def get_secondary_queue(self) -> list[dict]:
        return self._get_by_queue("secondary")

    def _get_by_queue(self, queue: str) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM opportunities
                WHERE queue = ?
                ORDER BY score DESC, detected_at DESC
                """,
                (queue,),
            ).fetchall()

        return [dict(row) for row in rows]

    def mark_as_notified(self, url: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE opportunities
                SET notified = 1
                WHERE url = ?
                """,
                (url,),
            )

    def was_notified(self, url: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT notified
                FROM opportunities
                WHERE url = ?
                """,
                (url,),
            ).fetchone()

        return bool(row and row["notified"])

    def get_source_state(
        self,
        source_id: str,
    ) -> dict | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    source_id,
                    last_checked_at,
                    last_status,
                    consecutive_errors
                FROM source_state
                WHERE source_id = ?
                """,
                (source_id,),
            ).fetchone()

        if row is None:
            return None

        return dict(row)

    def update_source_state(
        self,
        source_id: str,
        checked_at: str,
        status: str,
    ) -> None:
        previous = self.get_source_state(source_id)

        if status == "ok":
            consecutive_errors = 0
        else:
            consecutive_errors = (
                previous["consecutive_errors"] + 1
                if previous
                else 1
            )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO source_state (
                    source_id,
                    last_checked_at,
                    last_status,
                    consecutive_errors
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(source_id)
                DO UPDATE SET
                    last_checked_at = excluded.last_checked_at,
                    last_status = excluded.last_status,
                    consecutive_errors =
                        excluded.consecutive_errors
                """,
                (
                    source_id,
                    checked_at,
                    status,
                    consecutive_errors,
                ),
            )
            
    def count_all(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM opportunities
                """
            ).fetchone()

        return int(row["total"])