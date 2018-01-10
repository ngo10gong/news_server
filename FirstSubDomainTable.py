
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, Boolean, DateTime
from sqlalchemy import ForeignKey
from CommonBase import Base


#
# a table contains first subdomain information like domaintable's id, categorytable's id, url etc.
# 
class FirstSubDomainTable(Base):
  __tablename__ = 'firstsubdomaintable'

  # row id
  id=Column(Integer, primary_key=True)

  # domain table id
  domaintable_id = Column(Integer, ForeignKey('domaintable.id') )
  domaintable_entry= relationship("DomainTable", back_populates="firstsubdomaintable_list", foreign_keys=[domaintable_id])

  # category table id
  categorytable_id = Column(Integer, ForeignKey('categorytable.id') )
  categorytable= relationship("CategoryTable", back_populates="firstsubdomaintable_list", foreign_keys=[categorytable_id])

  # list of article that relate to one row of first subdomain 
  articletable_list=relationship("ArticleTable", back_populates='firstsubdomaintable', cascade="all, delete, delete-orphan")

  # url append to domain
  firstsubd=Column(Text)
  # indicate whether this is only for weekdays
  onlyweekdays=Column(Boolean, default=False)  #True False
  # the latest article retrieval time
  latestupdatetime=Column(DateTime)
  # the latest article url
  latestupdateurl=Column(Text)
  # icon url of this first sub domain
  sourceiconurl=Column(Text)

  def __repr__(self):
    return "<FirstSubDomainTable(id='%d', domaintable_id='%d', categorytable_id='%d', firstsubd='%s', onlyweekdays='%s', latestupdatetime='%s', latestupdateurl='%s', sourceiconurl='%s', )>" % (self.id, self.domaintable_id, self.categorytable_id, self.firstsubd, self.onlyweekdays, self.latestupdatetime, self.latestupdateurl, self.sourceiconurl )

