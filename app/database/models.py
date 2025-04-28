from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String

Base = declarative_base()

class Usertable(Base):
    __tablename__ = "inlog_gegevens"

    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String)
    profile_picture = Column(String, nullable=False, default="img/default.png")

    @classmethod
    def get_or_create(cls, db, user_id, email, name, profile_picture):
        user = db.query(cls).filter_by(user_id=user_id).first()
        if not user:
            user = cls(user_id=user_id, email=email, name=name, profile_picture=profile_picture)
            db.add(user)
            db.commit()
        return user
