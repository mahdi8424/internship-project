from sqlalchemy import text


def test_database_is_available(db):
    result = db.execute(
        text("SELECT 1")
    )

    assert result.scalar() == 1