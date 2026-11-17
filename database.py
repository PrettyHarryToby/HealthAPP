"""MongoDB persistence with a small compatibility layer for the existing ORM calls."""
import os
from datetime import date, datetime

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError
from sqlalchemy import Date, DateTime, create_engine
from sqlalchemy.sql import operators
from sqlalchemy.sql.elements import BinaryExpression, BooleanClauseList

from models import (
    BloodParameters, GeneticData, GynecologicalRiskIndicators,
    Medication, MicronutrientLevels, Patient, PatientNeeds,
    ReproductiveHealth, VitaminLevels,
)

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "").strip()
DATABASE_NAME = os.getenv("MONGODB_DATABASE", "healthapp").strip()
MODEL_TYPES = (
    Patient, BloodParameters, ReproductiveHealth, VitaminLevels,
    MicronutrientLevels, Medication, GeneticData, PatientNeeds,
    GynecologicalRiskIndicators,
)
_client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000) if MONGODB_URI else None
mongo_database = _client[DATABASE_NAME] if _client else None

# Retained for the SQLite import/export and schema-maintenance scripts.
DATABASE_URL = os.getenv("SQLITE_DATABASE_URL", "sqlite:///health_database.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def _column_type(model, key):
    return model.__table__.columns[key].type


def _to_storage(model, key, value):
    column_type = _column_type(model, key)
    if value is None:
        return None
    if isinstance(column_type, DateTime) and isinstance(value, datetime):
        return value.isoformat()
    if isinstance(column_type, Date):
        if isinstance(value, datetime):
            return value.date().isoformat()
        if isinstance(value, date):
            return value.isoformat()
    return value


def _from_storage(model, key, value):
    column_type = _column_type(model, key)
    if value is None:
        return None
    if isinstance(column_type, DateTime):
        if isinstance(value, datetime):
            return value
        return datetime.fromisoformat(value)
    if isinstance(column_type, Date):
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(value)
    return value


def _model_document(instance):
    model = type(instance)
    return {
        column.name: _to_storage(model, column.name, getattr(instance, column.name))
        for column in model.__table__.columns
    }


def _model_from_document(model, document):
    values = {
        column.name: _from_storage(model, column.name, document.get(column.name))
        for column in model.__table__.columns
        if column.name in document
    }
    return model(**values)


def _expression_filter(model, expression):
    if isinstance(expression, BooleanClauseList):
        clauses = [_expression_filter(model, clause) for clause in expression.clauses]
        operator = "$or" if expression.operator is operators.or_ else "$and"
        return {operator: clauses}
    if not isinstance(expression, BinaryExpression):
        raise TypeError(f"Unsupported MongoDB filter expression: {expression!r}")

    field = expression.left.key
    value = _to_storage(model, field, expression.right.value)
    mongo_operator = {
        operators.eq: "$eq",
        operators.ne: "$ne",
        operators.gt: "$gt",
        operators.ge: "$gte",
        operators.lt: "$lt",
        operators.le: "$lte",
    }.get(expression.operator)
    if mongo_operator is None:
        raise TypeError(f"Unsupported MongoDB comparison: {expression.operator!r}")
    return {field: value} if mongo_operator == "$eq" else {field: {mongo_operator: value}}


def _merge_filters(filters):
    if not filters:
        return {}
    if len(filters) == 1:
        return filters[0]
    return {"$and": filters}


class MongoQuery:
    def __init__(self, session, model):
        self.session = session
        self.model = model
        self.filters = []
        self.sort = []
        self.result_limit = None

    @property
    def collection(self):
        return self.session.database[self.model.__tablename__]

    def filter_by(self, **criteria):
        self.filters.append({
            key: _to_storage(self.model, key, value)
            for key, value in criteria.items()
        })
        return self

    def filter(self, *expressions):
        self.filters.extend(_expression_filter(self.model, expression) for expression in expressions)
        return self

    def order_by(self, *expressions):
        for expression in expressions:
            descending = getattr(expression, "modifier", None) is operators.desc_op
            column = getattr(expression, "element", expression)
            self.sort.append((column.key, -1 if descending else 1))
        return self

    def limit(self, count):
        self.result_limit = count
        return self

    def _hydrate(self, document):
        instance = _model_from_document(self.model, document)
        key = (self.model, instance.id)
        self.session._tracked[key] = (instance, _model_document(instance))
        return instance

    def all(self):
        cursor = self.collection.find(_merge_filters(self.filters))
        if self.sort:
            cursor = cursor.sort(self.sort)
        if self.result_limit is not None:
            cursor = cursor.limit(self.result_limit)
        return [self._hydrate(document) for document in cursor]

    def first(self):
        self.result_limit = 1
        records = self.all()
        return records[0] if records else None

    def count(self):
        return self.collection.count_documents(_merge_filters(self.filters))


class MongoSession:
    def __init__(self, database):
        self.database = database
        self._pending = []
        self._tracked = {}
        self._deleted = []

    def query(self, model):
        return MongoQuery(self, model)

    def add(self, instance):
        self._pending.append(instance)

    def delete(self, instance):
        self._deleted.append(instance)

    def _next_id(self, model):
        counter = self.database["counters"].find_one_and_update(
            {"_id": model.__tablename__},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=True,
        )
        return counter["value"]

    @staticmethod
    def _apply_defaults(instance):
        for column in type(instance).__table__.columns:
            if getattr(instance, column.name) is not None or column.default is None:
                continue
            default = column.default.arg
            if callable(default):
                default = default(None)
            setattr(instance, column.name, default)

    def commit(self):
        for instance in self._pending:
            model = type(instance)
            self._apply_defaults(instance)
            if instance.id is None:
                instance.id = self._next_id(model)
            document = _model_document(instance)
            self.database[model.__tablename__].replace_one(
                {"id": instance.id}, document, upsert=True
            )
            self._tracked[(model, instance.id)] = (instance, document)

        for (model, record_id), (instance, original) in self._tracked.items():
            document = _model_document(instance)
            if document != original:
                self.database[model.__tablename__].replace_one(
                    {"id": record_id}, document, upsert=True
                )

        for instance in self._deleted:
            model = type(instance)
            if model is Patient:
                for child_model in MODEL_TYPES:
                    if child_model is not Patient and "patient_id" in child_model.__table__.columns:
                        self.database[child_model.__tablename__].delete_many(
                            {"patient_id": instance.id}
                        )
            self.database[model.__tablename__].delete_one({"id": instance.id})

        self._pending.clear()
        deleted = {(type(instance), instance.id) for instance in self._deleted}
        self._tracked = {
            key: (instance, _model_document(instance))
            for key, (instance, _) in self._tracked.items()
            if key not in deleted
        }
        self._deleted.clear()

    def rollback(self):
        self._pending.clear()
        self._tracked.clear()
        self._deleted.clear()

    def close(self):
        self.rollback()


def init_database():
    """Verify MongoDB connectivity and ensure the collection indexes exist."""
    if _client is None or mongo_database is None:
        raise RuntimeError("MONGODB_URI is required. Set it in your local .env or Render environment.")
    try:
        _client.admin.command("ping")
        mongo_database["patients"].create_index("patient_id", unique=True)
        mongo_database["portal_users"].create_index("email", unique=True)
        mongo_database["portal_users"].create_index("patient_ref", unique=True)
        mongo_database["portal_pending"].create_index("expires_at", expireAfterSeconds=0)
        mongo_database["portal_rate_limits"].create_index("expires_at", expireAfterSeconds=0)
        for model in MODEL_TYPES:
            collection = mongo_database[model.__tablename__]
            collection.create_index("id", unique=True)
            latest = collection.find_one(sort=[("id", -1)])
            highest_id = latest["id"] if latest else 0
            mongo_database["counters"].update_one(
                {"_id": model.__tablename__},
                {"$max": {"value": highest_id}},
                upsert=True,
            )
    except PyMongoError as error:
        raise RuntimeError(f"Unable to connect to MongoDB: {error}") from error


def get_session():
    if mongo_database is None:
        raise RuntimeError("MongoDB is not configured. Set MONGODB_URI.")
    return MongoSession(mongo_database)


def close_session(session):
    session.close()


def get_database():
    if mongo_database is None:
        raise RuntimeError("MongoDB is not configured. Set MONGODB_URI.")
    return mongo_database


def serialize_model(instance):
    """Convert a clinical model instance to its MongoDB document representation."""
    return _model_document(instance)


def get_model_types():
    return MODEL_TYPES
