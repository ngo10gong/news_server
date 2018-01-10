
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, Boolean, DateTime
from sqlalchemy import ForeignKey
from CommonBase import Base



#
# this is a table declaration for Article
#
class ArticleTable(Base):
  __tablename__ = 'articletable'

  # row id
  id=Column(Integer, primary_key=True)

  # reference to firstsubdomain table's id
  firstsubdomaintable_id = Column(Integer, ForeignKey('firstsubdomaintable.id')) 
  # define the relationship between article table's firstsubdomaintable_id column and firstsubdomain table's id
  firstsubdomaintable= relationship("FirstSubDomainTable", back_populates="articletable_list", foreign_keys=[firstsubdomaintable_id])

  # define the relationship between article table and SentenceTable's articletable_id
  sentencetable_list=relationship("SentenceTable", back_populates='articletable', cascade="all, delete, delete-orphan")

  # define the relationship between article table and tokenArticleTable's articletable_id
  tokenarticletable_list= relationship("TokenArticleTable", back_populates='articletable', cascade="all, delete, delete-orphan")


  # url to the article
  finalurl=Column(Text)
  # timestamp on the article
  timestampondoc=Column(DateTime)
  # retrieval timestamp of this article
  timestamponretrieve=Column(DateTime)
  # title of this article
  title=Column(Text)
  # article's content
  content=Column(Text)
  # jpeg name of article
  jpegname=Column(Text)
  # article's image url
  imageurl=Column(Text)
  # a list of articles related to current article 
  similaritieslist =Column(Text)
  # number of related articles
  similaritiescount =Column(Integer)


  def __repr__(self):
    return "<ArticleTable(id='%d', firstsubdomaintable_id='%d', finalurl='%s', timestampondoc='%s', timestamponretrieve='%s', title='%s', content='%s', jpegname='%s', imageurl='%s', similaritieslist='%s', similaritiescount='%s' , )>" % (self.id, self.firstsubdomaintable_id, self.finalurl, self.timestampondoc, self.timestamponretrieve, self.title, self.content, self.jpegname, self.imageurl, self.similaritieslist , str(self.similaritiescount) )

