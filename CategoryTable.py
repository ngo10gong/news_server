
import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table
from sqlalchemy import ForeignKey
from CommonBase import Base



# 
# a table contains the information about different news categories
#
class CategoryTable(Base):
  __tablename__ = 'categorytable'

  # row id
  id=Column(Integer, primary_key=True)
  # chinese name of category
  chi_name=Column(Text)
  # english name of category
  eng_name=Column(Text)
 
  # define the relationship between CategoryTable's id and FirstSubDomaintable's categorytable_id
  firstsubdomaintable_list=relationship("FirstSubDomainTable", back_populates="categorytable" , cascade="all, delete, delete-orphan")

  def __repr__(self):
    return "<CategoryTable(id='%d', chi_name='%s', eng_name='%s')>" % (self.id, self.chi_name, self.eng_name)

