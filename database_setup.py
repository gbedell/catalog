from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
 
Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key = True)
    name = Column(String(250), nullable = False)
    email = Column(String(250), nullable = False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """Returns object data in easily serializeable format"""
        return {
            'id':       self.id,
            'name':     self.name,
            'email':    self.email,
            'picture':  self.picture,
        }    

class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key = True)
    name =Column(String(80), nullable = False)
    picture = Column(String, nullable = False)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializeable format"""
        return {
            'id':      self.id,
            'name':    self.name,
            'picture': self.picture,
        }

class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable = False)
    picture = Column(String, nullable = False)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category, cascade='delete')
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """Returns object data in easily serializable format"""
        return {
            'id':           self.id,
            'name':         self.name,
            'description':  self.description,
            'picture':      self.picture,
        }

engine = create_engine('sqlite:///catalog.db')

Base.metadata.create_all(engine)