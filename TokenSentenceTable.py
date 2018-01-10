
import sqlalchemy
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, Boolean, DateTime
from sqlalchemy import ForeignKey
from CommonBase import Base



#
# A table contain tokenize sentence information
#
class TokenSentenceTable(Base):
  __tablename__ = 'tokensentencetable'

  # row id
  id=Column(Integer, primary_key=True)

  # sentence table id reference
  sentencetable_id = Column(Integer, ForeignKey('sentencetable.id') )
  # define relationship between TokenSentenceTable's id and sentencetable's id
  sentencetable= relationship("SentenceTable", 
    back_populates="tokensentencetable_list", foreign_keys=[sentencetable_id])

  # tokenize sentence content
  tokensentencecontent=Column(Text)

  def __repr__(self):
    return "<TokenSentenceTable(id='%d', sentencetable_id='%d', tokensentencecontent='%s' )>" % (self.id, 
            self.sentencetable_id, 
            self.tokensentencecontent, 
            )


