import tempfile
from pathlib import Path

from App.database import OpportunityDatabase
from App.models import Opportunity


def make(url: str, title: str, reward: float = 10000, discount: float = 0):
    return Opportunity(
        source_id="test", source_name="Test", title=title, url=url,
        country="CL", category="fintech", description="cashback real",
        reward_amount=reward, score=80, probability=90,
        raw_data={"reward_known": True, "cost_known": False,
                  "discount_percent": discount, "opportunity_type": "cashback"},
    )


with tempfile.TemporaryDirectory() as tmp:
    db = OpportunityDatabase(Path(tmp) / "test.db")
    first = make("https://example.com/promo/?utm_source=x#hero", "Cashback $10.000")
    assert db.save(first) == "new"

    same = make("https://www.example.com/promo?utm_campaign=y", "Cashback $10.000")
    assert db.save(same) == "duplicate"

    changed = make("https://example.com/promo/", "Cashback $20.000", reward=20000)
    assert db.save(changed) == "updated"

print("V0.8 DEDUP/UPDATE TESTS OK")
