
import sqlalchemy
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base
#from SentenceTable import SentenceTable

#
# the entitytable contain entity's information for tensorflow/gensim app to use
# 
class EntityTable(Base):
  __tablename__ = 'entitytable'

  # row id
  id=Column(Integer, primary_key=True)
  # entity's organization name
  organization=Column(Text)
  # entity's current title in the organization
  title=Column(Text)
  # name of entity
  name=Column(Text)
  # nickname of entity
  nickname=Column(Text)
  # entity's previous title
  previoustitle=Column(Text)
  # has it updated to server
  hasfirebasetable=Column(Integer, default=0)
  # a list of casetable's id 
  checkrelatedcaselist=Column(Text)


  # define relationship between Entity's id and SentenceTable's activeenttity_id
  activerole_list=relationship( "SentenceTable", 
    foreign_keys="SentenceTable.activeentity_id", 
    back_populates='activeentity_table', 
    cascade="all ,delete, delete-orphan")
  # define relationship between Entity's id and SentenceTable's passiveenttity_id
  passiverole_list=relationship( "SentenceTable", 
    foreign_keys="SentenceTable.passiveentity_id", 
    back_populates='passiveentity_table', 
    cascade="all, delete, delete-orphan")

  def __repr__(self):
    return "<EntityTable(id='%d', organization='%s', title='%s', name='%s', nickname='%s', previoustitle='%s', hasirebasetable='%d' ,)>" % (self.id, self.organization, self.title, self.name, self.nickname, self.previoustitle, self.hasfirebasetable)

