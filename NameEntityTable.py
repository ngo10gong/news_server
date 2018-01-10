
import sqlalchemy
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base
#from SentenceTable import SentenceTable

#
# entity's url which contains detail information 
# 
class NameEntityTable(Base):
  __tablename__ = 'nameentitytable'

  # row id
  id=Column(Integer, primary_key=True)
  # name of entity
  name=Column(Text)
  # url that contains  entity's detail information
  urllink=Column(Text)


  def __repr__(self):
    return "<NameEntityTable(id='%d', name='%s', urllink='%s')>" % (self.id, self.name, self.urllink)

