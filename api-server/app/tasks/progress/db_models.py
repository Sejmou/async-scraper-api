# generated with the help of sqlacodegen (https://github.com/agronholm/sqlacodegen)
# command used: sqlacodegen sqlite:///data/task_progress_dbs/{some_random_existing_task_id}.db > app/tasks/progress/db_models.py

from sqlalchemy import Float, Integer, LargeBinary
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, MappedAsDataclass


class Base(DeclarativeBase, MappedAsDataclass):
    pass


class QueueFailures(Base):
    __tablename__ = "queue_failures"

    _id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    timestamp: Mapped[float] = mapped_column(Float)


class QueueInputsWithoutOutput(Base):
    __tablename__ = "queue_inputs_without_output"

    _id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    timestamp: Mapped[float] = mapped_column(Float)


class UniqueQueueInputs(Base):
    __tablename__ = "unique_queue_inputs"

    _id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary, unique=True)
    timestamp: Mapped[float] = mapped_column(Float)


class QueueSuccesses(Base):
    __tablename__ = "queue_successes"

    _id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data: Mapped[bytes] = mapped_column(LargeBinary)
    timestamp: Mapped[float] = mapped_column(Float)
