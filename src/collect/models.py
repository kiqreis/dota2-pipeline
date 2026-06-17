from sqlalchemy import func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from typing import Optional


class Base(DeclarativeBase):
    pass


class Match(Base):
    __tablename__ = "match"

    match_id: Mapped[int] = mapped_column(primary_key=True)
    duration: Mapped[int]
    start_time: Mapped[int]
    radiant_team_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    radiant_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    dire_team_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    dire_name: Mapped[Optional[str]] = mapped_column(nullable=True)
    leagueid: Mapped[Optional[int]] = mapped_column(nullable=False)
    league_name: Mapped[Optional[str]] = mapped_column(nullable=False)
    series_id: Mapped[Optional[int]] = mapped_column(nullable=True)
    series_type: Mapped[Optional[int]] = mapped_column(nullable=True)
    radiant_score: Mapped[int]
    dire_score: Mapped[int]
    radiant_win: Mapped[bool]
    version: Mapped[Optional[int]] = mapped_column(nullable=True)
    flag_details_collected: Mapped[bool] = mapped_column(default=False)
    flag_details_processed: Mapped[bool] = mapped_column(default=False)


def get_oldest_match_id(engine):
    with Session(engine) as session:
        match_id = session.scalar(select(func.min(Match.match_id)))

    return match_id