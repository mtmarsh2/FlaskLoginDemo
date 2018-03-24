import datetime
import hashlib
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, text, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from werkzeug.security import generate_password_hash, \
    check_password_hash

Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    id = Column(Integer, primary_key=True)
    account_name = Column(String(80), unique=True)
    password = Column(String(80))
    active_user = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    is_new = Column(Boolean, default=True)

    def is_authenticated(self):
        return True

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.account_name

    def is_admin_user(self):
        return self.is_admin

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __unicode__(self):
        return self.account_name

class Accountdata(Base):
    __tablename__ = 'accountdata'
    id = Column(Integer, primary_key=True)
    account_name = Column(String, ForeignKey('account.account_name'))
    account = relationship('Account', foreign_keys='Accountdata.account_name')
    key = Column(String(200), unique=True)
    value = Column(String(80))

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
