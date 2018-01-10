
import sqlalchemy
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base
#from SentenceTable import SentenceTable


#
# A table contains tokenize article information
# 
class TokenArticleTable(Base):
  __tablename__ = 'tokenarticletable'

  # row id
  id=Column(Integer, primary_key=True)

  # reference to article table id 
  articletable_id = Column(Integer, ForeignKey('articletable.id'))
  # define relationship between article table's id and this row
  articletable = relationship("ArticleTable", back_populates="tokenarticletable_list", foreign_keys=[articletable_id])

  # a tokenize article content
  tokencontent = Column(Text)
  # a list of relatedt article table id
  listofrelatedarticle = Column(Text)


  def __repr__(self):
    return "<TokenArticleTable(id='%d', articletable_id='%d', tokencontent='%s', listofrelatedarticle='%s')>" % (self.id, self.articletable_id, self.tokencontent, self.listofrelatedarticle)

