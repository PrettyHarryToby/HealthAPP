"""Copy existing SQLite clinical records into MongoDB without deleting the source."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import get_database, get_model_types, init_database, serialize_model


def migrate():
    sqlite_url = os.getenv("SQLITE_DATABASE_URL", "sqlite:///health_database.db")
    sqlite_engine = create_engine(sqlite_url)
    SQLiteSession = sessionmaker(bind=sqlite_engine)
    mongo = get_database()
    migrated_counts = {}

    try:
        with SQLiteSession() as sqlite_session:
            for model in get_model_types():
                records = sqlite_session.query(model).all()
                collection = mongo[model.__tablename__]
                for record in records:
                    document = serialize_model(record)
                    collection.replace_one({"id": document["id"]}, document, upsert=True)
                if records:
                    mongo["counters"].update_one(
                        {"_id": model.__tablename__},
                        {"$max": {"value": max(record.id for record in records)}},
                        upsert=True,
                    )
                migrated_counts[model.__tablename__] = len(records)
    finally:
        sqlite_engine.dispose()

    for collection, count in migrated_counts.items():
        print(f"{collection}: {count} records copied")
    print("Migration finished. The SQLite database was left unchanged.")


if __name__ == "__main__":
    init_database()
    migrate()
