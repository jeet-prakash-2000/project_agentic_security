"""Demo request repository (table ``demo_requests``)."""

from database.models import DemoRequest
from database.repositories.base import BaseRepository


class DemoRequestsRepository(BaseRepository):
    model = DemoRequest

    def create(self, data):
        lead = DemoRequest(
            name=(data.get("name") or "").strip(),
            email=(data.get("email") or "").strip().lower(),
            company=(data.get("company") or "").strip(),
            role=(data.get("role") or "").strip(),
            message=(data.get("message") or "").strip(),
            status=(data.get("status") or "new").strip(),
            created=data.get("created"),
        )
        self.session.add(lead)
        self.session.commit()
        return lead

    def list_leads(self, limit=200):
        return (
            self.session.query(DemoRequest)
            .order_by(DemoRequest.created.desc())
            .limit(limit)
            .all()
        )
