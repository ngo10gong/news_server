
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base



# 
# a table indicate relationship between active entities and passive entities
#
class CaseTable(Base):
  __tablename__ = 'casetable'

  # row id
  id=Column(Integer, primary_key=True)
  # active entity name
  active=Column(Text)
  # passive entity name
  passive=Column(Text)

  # define the relationship between CaseTable's id and SentenceTable's casetable_id
  sentencetable_list=relationship( "SentenceTable", back_populates='casetable', cascade="all ,delete, delete-orphan")

  def __repr__(self):
    return "<CaseTable(id='%d', active='%s', passive='%s')>" % (self.id, self.active, self.passive)

