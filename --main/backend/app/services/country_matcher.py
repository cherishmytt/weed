from __future__ import annotations

from dataclasses import dataclass

from shapely.geometry import Point, shape
from shapely.strtree import STRtree
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CountryBoundary


@dataclass
class CountryInfo:
    name: str | None
    code: str | None


class CountryMatcher:
    def __init__(self, boundaries: list[CountryBoundary]):
        self.boundaries: list[CountryBoundary] = []
        self.geometries = []
        for boundary in boundaries:
            geometry = shape(boundary.geojson)
            if not geometry.is_valid:
                geometry = geometry.buffer(0)
            self.boundaries.append(boundary)
            self.geometries.append(geometry)
        self.tree = STRtree(self.geometries) if self.geometries else None

    @classmethod
    def from_db(cls, db: Session) -> "CountryMatcher":
        boundaries = db.execute(select(CountryBoundary)).scalars().all()
        return cls(boundaries)

    def match(self, longitude: float, latitude: float) -> CountryInfo:
        if not self.tree:
            return CountryInfo(name=None, code=None)
        point = Point(longitude, latitude)
        candidates = self.tree.query(point)
        for index in candidates:
            idx = int(index)
            geometry = self.geometries[idx]
            if geometry.contains(point) or geometry.touches(point):
                boundary = self.boundaries[idx]
                return CountryInfo(name=boundary.country_name, code=boundary.country_code)
        return CountryInfo(name=None, code=None)
