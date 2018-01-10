
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base



#
# this table contain a list of news domain's information 
#
class DomainTable(Base):
  __tablename__ = 'domaintable'

  # row id
  id=Column(Integer, primary_key=True)
  # base url of domain
  baseurl=Column(Text)
  # domain's chinese name
  chi_name=Column(Text)
  # domain's english name
  eng_name=Column(Text)

  # define the relationship between DomainTable's id and FirstSubDomainTable's domaintable_id 
  firstsubdomaintable_list=relationship( "FirstSubDomainTable", back_populates='domaintable_entry', cascade="all, delete, delete-orphan")

  def __repr__(self):
    return "<DomainTable(id='%d', baseurl='%s', chi_name='%s', eng_name='%s')>" % (self.id, self.baseurl, self.chi_name, self.eng_name)

