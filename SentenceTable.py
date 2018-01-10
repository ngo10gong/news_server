
import sqlalchemy
from sqlalchemy.orm import relationship, aliased
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, Boolean, DateTime
from sqlalchemy import ForeignKey
from CommonBase import Base



#
# Each row provides the relationship between one sentence and other table
# information (like which article does this sentence belongs to , which case
# does this sentence belongs to, which entity does this sentnece belongs to)
# 
class SentenceTable(Base):
  __tablename__ = 'sentencetable'

  # row id
  id=Column(Integer, primary_key=True)

  # article table id
  articletable_id = Column(Integer, ForeignKey('articletable.id') )
  # define relationship between article table id and this sentence row 
  articletable= relationship("ArticleTable", 
    back_populates="sentencetable_list", foreign_keys=[articletable_id])

  # sentence data
  sentencecontent=Column(Text)

  # case table id
  casetable_id = Column(Integer, ForeignKey('casetable.id') )
  # define relationship between casetable id and this sentence row 
  casetable= relationship("CaseTable", back_populates="sentencetable_list", 
    foreign_keys=[casetable_id])

  # entity id as active role
  activeentity_id = Column(Integer, ForeignKey('entitytable.id') )
  # define relationship between entitytable id and this sentence row
  activeentity_table= relationship("EntityTable", 
    back_populates="activerole_list", 
    foreign_keys="SentenceTable.activeentity_id")

  # entity id as passive role
  passiveentity_id = Column(Integer, ForeignKey('entitytable.id') )
  # define relationship between entitytable id and this sentence row
  passiveentity_table= relationship("EntityTable", 
    back_populates="passiverole_list", 
    foreign_keys="SentenceTable.passiveentity_id")

  # sentence table id that before the current sentence
  previoussentence_id=Column(Integer, ForeignKey('sentencetable.id'))
  # define relationship between sentencetable id and this sentence row
  previoussentence=relationship( "SentenceTable", 
    foreign_keys="SentenceTable.previoussentence_id")

  # sentence table id that after the current sentence
  nextsentence_id=Column(Integer, ForeignKey('sentencetable.id'))
  # define relationship between sentencetable id and this sentence row
  nextsentence=relationship( "SentenceTable", 
    foreign_keys="SentenceTable.nextsentence_id")

  # list of TokenSentenceTable'id reference this row 
  tokensentencetable_list = relationship("TokenSentenceTable", 
                            back_populates='sentencetable', 
                            cascade="all,delete, delete-orphan")

  #indicate whether this sentence has been used for training or not
  traintype= Column(Integer)


  def __repr__(self):
    return "<SentenceTable(id='%s', articletable_id='%s', sentencecontent='%s', casetable_id='%s', activeentitytable_id='%s', passiveentitytable_id='%s', previoussentence_id='%s', nextsentence_id='%s' , traintype='%d')>\n" % (str(self.id), 
            str(self.articletable_id), 
            self.sentencecontent, 
            str(self.casetable_id), 
            str(self.activeentity_id), 
            str(self.passiveentity_id), 
            str(self.previoussentence_id), 
            str(self.nextsentence_id),
            str(self.traintype)
            )

