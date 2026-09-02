"""Shared repository base class.

Repositories are the only data-access layer; services never talk to the
database directly. All helpers commit the current transaction (the request/
caller transaction is short-lived and single-statement).
"""


class BaseRepository:
    model = None

    def __init__(self, session):
        self.session = session

    def all(self):
        return self.session.query(self.model).all()

    def first(self):
        return self.session.query(self.model).first()

    def count(self):
        return self.session.query(self.model).count()

    def get(self, pk):
        return self.session.get(self.model, pk)

    def add(self, obj):
        self.session.add(obj)
        self.session.commit()
        return obj

    def upsert(self, obj):
        self.session.merge(obj)
        self.session.commit()
        return obj

    def save(self, obj):
        self.session.add(obj)
        self.session.commit()
        return obj

    def delete(self, obj):
        self.session.delete(obj)
        self.session.commit()

    def delete_all(self):
        self.session.query(self.model).delete()
        self.session.commit()

    def replace_all(self, objs):
        """Replace every row of the table with the given objects (migration)."""
        self.session.query(self.model).delete()
        self.session.add_all(objs)
        self.session.commit()
        return len(objs)
