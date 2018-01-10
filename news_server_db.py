import sqlalchemy
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import aliased
from sqlalchemy.sql import exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Table, func, exc
from sqlalchemy import ForeignKey, create_engine, Sequence, and_, or_, text
from ArticleTable import ArticleTable, Base as articleBase
from CaseTable import CaseTable, Base as caseBase
from CategoryTable import CategoryTable, Base as categoryBase
from DomainTable import DomainTable, Base as domainBase
from EntityTable import EntityTable, Base as entityBase
from FirstSubDomainTable import FirstSubDomainTable, Base as firstSubBase
from SentenceTable import SentenceTable, Base as sentenceBase
from NameEntityTable import NameEntityTable, Base as nameentityBase
from TokenArticleTable import TokenArticleTable, Base as tokenarticleBase
from TokenSentenceTable import TokenSentenceTable, Base as tokensentenceBase
from CommonBase import Base
from datetime import datetime, timedelta, timezone
import lxml.html
import re
import os
import threading
import fcntl


#
# This class acts as a middleware between actual database access and 
# individual program which want to get/set informtion to database.  
# The indivdual program does not need to handle the sqlalchemy usage
# It will create the database and the table on it.  
# It provides method for getting information by combine different 
# table information and modify them according to the input of method
#   
class NewsAllTable():
  database_loc='news.db'

  #
  # init function for this class
  # like do the connection establishment, locks...
  # database_loc : database name
  #
  def __init__(self, database_loc):
    #set up the database
    self.database_loc=database_loc
    self.engine=create_engine('sqlite:///%s'%self.database_loc , echo=False, connect_args={ 'timeout' : 1000 } )
    Base.metadata.create_all(self.engine)

    #set up the lock
    self._save_article_entry = threading.Lock()
    self.stoplist = ['的' , '在', '有', '他','為', '她', '到', '及','我', '係','與',  '和', '月',    '會','咁','佢', '但', '是', '就', '好', '亦', '嘅', '都', '唔', '於', '或', '時' , '由', '咗', '後', '仍' , '年', '日',  '冇', '多' , '至',    '哋', '吧','小' ]

  #
  # initialize the sqlalchemy session
  # return sqlalchemy session
  #
  def init_all_table(self):
    Session=sessionmaker(bind=self.engine)
    self.session=Session()
    self.session.commit()
    return self.session


  #
  # get a dict with 
  # key( DomainTable.eng_name, CategoryTable.eng_name ) : 
  #   valule (FirstSubDomainTable.id , DomainTable.baseurl 
  #            + FirstSubDomainTable.firstsubdomainid 
  # by combining domaintable, categorytable & firstsubdomaintable
  # subsitute_time : indicate whehter subsitute the time in url or not
  # return a dict as result of combining domaintable, categorytable 
  # and firstsubdomaintable
  #
  def getRetrieveURLPair(self, subsitute_time=None):
    #in query, the order of selection matter
    print('----------------- getRetrieveURLPair 0=', subsitute_time)
    #get all the domaintable row
    result = self.session.query(DomainTable).all()
    print('----------------- getRetrieveURLPair 0.1=', result)

    # combine firstsubdomaintable, categorytable & domaintable 
    # information 
    result=self.session.query(FirstSubDomainTable.id, 
         DomainTable.eng_name, CategoryTable.eng_name,  
         DomainTable.baseurl + FirstSubDomainTable.firstsubd ).join(
          CategoryTable).filter(and_(DomainTable.id == 
            FirstSubDomainTable.domaintable_id, 
            FirstSubDomainTable.categorytable_id == 
              CategoryTable.id)).all()
    final_dict = {}
    print('----------------- getRetrieveURLPair 1=', result)
    if subsitute_time is not None:
      # subsitute year,month,day in the url
      # i[0] = FirstSubDomainTable.id 
      # i[1] = DomainTable.eng_name
      # i[2] = CategoryTable.eng_name 
      # i[3] = DomainTable.baseurl + FirstSubDomainTable.firstsubd 
      for i in result :
        final_dict[ (i[1],i[2]) ] = [ i[0], 
                re.sub(r'MM', "%02d"%subsitute_time.month, 
                  re.sub(r'DD', "%02d"%subsitute_time.day, 
                    re.sub(r'YYYY', str(subsitute_time.year), i[3]))) ]
    else :
      final_dict= { (i[1],i[2]) : [ i[0], i[3] ] for i in result }

    print('----------------- getRetrieveURLPair 3')
    return final_dict


  #
  # set the FirstSubdomainTable's column of latest update time and 
  # latest update url
  # row_id : row id of firstsubdomain
  # in_datetime : new value of latest update time
  # in_url : new value of latest url
  # return how many rows are updated
  #
  def setLatestUpdateTimeAndUrl(self, row_id, in_datetime, in_url ):
    try : 
      # update the value in firstsubdomaintable
      result=self.session.query(FirstSubDomainTable).filter(
        FirstSubDomainTable.id == row_id).update(
          {FirstSubDomainTable.latestupdateurl : in_url , 
           FirstSubDomainTable.latestupdatetime : in_datetime} )
      self.session.commit()
    except exc.SQLAlchemyError :
      print ('error error error setlatestupdatetimeandurl exception')
      self.session.rollback()
      result=0
    else : 
      if result != 1 :
        print ('error error error setLatestUpdateTimeAndUrl')
    return result


  #
  # create a new article entry with input values
  # in_firstsubdomaintableid  : firstsubdomain table id
  # in_finalurl  : url value
  # in_timestampondoc  : timestamp on the article
  # in_title  : title of the article
  # in_content  : content of the article
  # in_jpegname  : jpeg filename for the article
  # in_imageurl  : image url of the article
  # parseIt  : should this method to parse the article
  # return the newly created row id 
  #
  def setArticleEntry(self, in_firstsubdomaintableid, in_finalurl, in_timestampondoc, in_title, in_content, in_jpegname, in_imageurl=None, parseIt=False) :
    try : 
      #lock for checking/adding entry
      with self._save_article_entry : 
        #double check the same entry
        result = self.session.query( ArticleTable.id, 
          ArticleTable.timestampondoc ).filter(
            ArticleTable.firstsubdomaintable_id == 
              in_firstsubdomaintableid ).filter( 
                ArticleTable.finalurl == in_finalurl ).filter( 
                  ArticleTable.title == in_title ).all()
        if len(result) > 0 :
          print (" error : why there is a duplicate article entry id=",result[0][0], ",timestampondoc=", result[0][1], ", in_timestampondoc=", in_timestampondoc)
          return 0 

        nowTime=datetime.now(timezone(timedelta(hours=8)))
        print('-------------- 1')
        #try to remove unnecessary character
        for x in ['【本報訊】', '(星島日報報道)','【明報專訊】','【本報綜合報道】' ]:
          if x in in_content :
            in_content=in_content.lstrip(x)
            #only either one will occur
            break

        print('-------------- 1.1')
        #add new article to the table
        newArticleEntry=ArticleTable( firstsubdomaintable_id =
          in_firstsubdomaintableid, finalurl=in_finalurl, 
          timestampondoc=in_timestampondoc, 
          timestamponretrieve=nowTime, 
          title=in_title, 
          content=in_content, 
          jpegname=in_jpegname, imageurl=in_imageurl)
        self.session.add(newArticleEntry)
        self.session.commit()
        #print('-------------- 2')
        result=newArticleEntry.id     
      if parseIt :
        #print('-------------- 3')
        if row.content is None or (len(row.content) < 2) :
          combine_content = row.title
        else :
          root = lxml.html.fromstring(in_content)
          listStripHTMLTagsString = root.xpath("//text()")
          combine_content = ''.join(listStripHTMLTagsString) 
        strip_content=re.sub(r"[^\u4e00-\u9fff()?.,%0-9\u3002\u300c\u300d\uff01\u3010\u3011\uff0c\u3001\u3002\u300a\u300b\uff1a\uff1b]"," ",combine_content)
        sentencerow_id = self.setSentenceEntry(row.id, 
                                           strip_content, 
                                           None, 
                                           None)

    except exc.SQLAlchemyError :
      print ('error error error setArticleEntry exception')
      result=0
      self.session.rollback()
    else : 
      print ('----> setArticleEntry good')
      self.session.commit()
    return result


  #
  # set sentence next id of a given row id in setence table
  # in_rowid : row id in setence table to be updated with next sentence
  #            id
  # in_nextsentenceid : sentence table id 
  # return row id that just updated   
  #
  def setSentenceNextSentenceID(self, in_rowid, in_nextsentenceid) :
    try:
      #do the update
      result=self.session.query(SentenceTable).filter(SentenceTable.id == in_rowid).update({SentenceTable.nextsentence_id : in_nextsentenceid } )
    except exc.SQLAlchemyError :
      result=0
      print ('error error error setSentenceNextSentenceID exception')
      self.session.rollback()
    else :
      self.session.commit()
    return result


  #
  # create one new entry in sentence table
  # in_articletableid : article table id
  # in_sentencecontent : sentence content
  # in_previoussentenceid : previous sentence table id 
  # in_nextsentenceid : next sentence table id 
  # return the newly added row id
  #
  def setSentenceEntry(self, in_articletableid, 
                       in_sentencecontent, 
                       in_previoussentenceid, 
                       in_nextsentenceid) :
    try : 
      #create a new entry in sentence table
      newSentenceEntry=SentenceTable( articletable_id=in_articletableid, sentencecontent=in_sentencecontent, previoussentence_id=in_previoussentenceid, nextsentence_id=in_nextsentenceid )
      self.session.add(newSentenceEntry)
      self.session.commit()
    except exc.SQLAlchemyError :
      print ('error error error setSentenceEntry exception')
      self.session.rollback()
      row_id=0
    else : 
      #print ('----> setSentenceEntry good')
      row_id=newSentenceEntry.id
      self.session.commit()
    return row_id


  #
  # get one sentnece entry 
  # row_id : row id in sentence table
  # return a entry in sentence table
  #
  def getSentenceEntry(self, row_id=0):
    if row_id ==0 :
      # get the latest one
      entry= self.session.query( SentenceTable).order_by('-id').first()
    else :
      # get the pass-in row_id
      entry= self.session.query( SentenceTable).get(row_id)
    final_dict=entry.__dict__
    #print (final_dict)
    return final_dict
    

  #
  # create a new entity entry
  # in_name : name of entity
  # in_urlink : url of a detail entity
  # return the newly added row id
  #
  def setNameEntityEntry(self, in_name, 
                       in_urllink ) :
    try : 
      if (self.session.query(NameEntityTable).filter(NameEntityTable.name == in_name).count() == 0) :
        print (' ------ > no entry setNameEntityEntry')
        #creating entity entry
        newNameEntityEntry=NameEntityTable( name=in_name, urllink=in_urllink)
        self.session.add(newNameEntityEntry)
        self.session.commit()
        row_id = newNameEntityEntry.id
        print (' ------ > setNameEntityEntry row_id=',  row_id)
      else :
        print (' ------ > has entry setNameEntityEntry')
        row_id = self.session.query(NameEntityTable.id).order_by(NameEntityTable.id.desc()).first()
    except exc.SQLAlchemyError :
      print ('error error error setNameEntityEntry exception')
      self.session.rollback()
      row_id=0
    else : 
      #print ('----> setNameEntityEntry good')
      self.session.commit()
    return row_id


  #
  # retrieve a tokenize article content with specific input criteria
  # in_startTime : start time for search
  # in_endTime : end time for search
  # in_domain_eng_name : specific domain english name
  # in_category_eng_name : specific category english name
  # return a list of tuples with (articletable's id, tokenize's content)
  #
  def getTokenDailyNewsArticle(self, 
                               in_startTime, 
                               in_endTime,
                               in_domain_eng_name,
                               in_category_eng_name
                               ) :
    print (' time tokendaily 1 : ', datetime.now(timezone(timedelta(hours=8))) )

    result = self.session.query( FirstSubDomainTable.id ).join(
      DomainTable).join(CategoryTable).filter(and_(
       DomainTable.eng_name == in_domain_eng_name, 
       CategoryTable.eng_name== in_category_eng_name )).all()
    if len(result) == 0:
      #empty result
      print (' error getTokenDailyNewsArticle 1')
      return 0

    print (' time tokendaily 2 : ', datetime.now(timezone(timedelta(hours=8))) )

    print ('result[0][0]=',result[0][0])
    print ('in_startTime=',in_startTime)
    print ('in_endTime=',in_endTime)

    # get a list of article with specific first subdomain
    # --> result[0][0] = FirstSubDomainTable.id 
    result = self.session.query( ArticleTable.id, ArticleTable.content,
       ArticleTable.title ).filter(
        ArticleTable.firstsubdomaintable_id == result[0][0]).filter(
          and_( ArticleTable.timestampondoc >= in_startTime , 
                ArticleTable.timestampondoc <= in_endTime)).all()

    print (' time tokendaily 3 : ', datetime.now(timezone(timedelta(hours=8))) )

    if len(result) == 0:
      #empty result
      print (' error getTokenDailyNewsArticle 2')
      return 0
    
    #start the tokenization
    articleTableIDList =[]
    resultList=[] 

    print (' time tokendaily 4 : ', datetime.now(timezone(timedelta(hours=8))) , ', len(result)=', len(result))

    for indTuple in result: 
        #with self.session.no_autoflush:
        # --> indTyple[0] = ArticleTable.id
        articleTableIDList.append(indTuple[0]) 
        tokenContentTuples = self.session.query(
          TokenArticleTable.articletable_id, 
          TokenArticleTable.tokencontent).filter(
            TokenArticleTable.articletable_id == indTuple[0]).all() 
        if tokenContentTuples is not None and len(tokenContentTuples) >= 1:
          #it has the entry
          resultList.append(tokenContentTuples[0])
          continue

        #do not have the entry , so
        #let's start tokenization
        
        strip_content = re.sub(r"[^\u4e00-\u9fff]", 
          " ", indTuple[2] + ' ' + indTuple[1][:200])
        strip_content = re.sub(r'[%s]'%''.join(self.stoplist),'' ,
          strip_content)

        # add more customize tokenization  to suit the need

        strip_content = re.sub(r'\s{2,}', ' ', strip_content)
        strip_content = re.sub(r'\u3000', '', strip_content)
 
        # add to session first 
        newTokenArticleEntry=TokenArticleTable( 
          articletable_id=indTuple[0], tokencontent=strip_content)
        self.session.add(newTokenArticleEntry)
        resultList.append((indTuple[0], strip_content))
      
    with open("databaselockfile", "w") as test_fd :
      # write to the database
      fcntl.lockf(test_fd, fcntl.LOCK_EX)
      self.session.commit()
      fcntl.lockf(test_fd, fcntl.LOCK_UN)


    print (' time tokendaily 5 : ', datetime.now(timezone(timedelta(hours=8))) )
    return resultList



  #
  # get a tokenize content of one sentence from article
  # in_sentencetableid : sentence table id
  # return a tuples with three values
  #   (  sentencetable id, tokensentencetable id ,tokenize content )
  # 
  def getOneTokenSentence(self, 
                       in_sentencetableid = None) :

    #check whether there is one or not 
    result = self.session.query(TokenSentenceTable.id, 
      TokenSentenceTable.tokensentencecontent ).filter( 
        TokenSentenceTable.sentencetable_id == 
          in_sentencetableid ).first()

    if result is None or (result is not None and len(result) == 0 ):
      #empty result
      result = self.session.query(SentenceTable.sentencecontent 
        ).filter( SentenceTable.id == in_sentencetableid ).first()

      if len(result) == 0 :
        print ('getOneTokenSentence error get sentencetable id')
        return None

      #let's start tokenization
      strip_content = re.sub(r"[^\u4e00-\u9fff\uff1a\u300c\u300d\ufe55]", "",  result[0] )
      strip_content = re.sub(r'\u3000', ' ', strip_content)
      strip_content = re.sub(r'[%s]'%''.join(self.stoplist),'' ,
          strip_content)
      strip_content = re.sub(r'\s{2,}', ' ', strip_content)
 
      #write to database 
      newTokenSentenceEntry=TokenSentenceTable( 
          sentencetable_id= in_sentencetableid, 
          tokensentencecontent=strip_content )
      self.session.add(newTokenSentenceEntry)
      self.session.commit()
      tokenContentTuples = self.session.query(TokenSentenceTable.id 
        ).filter( TokenSentenceTable.sentencetable_id == 
         in_sentencetableid ).one() 
      return (in_sentencetableid, tokenContentTuples[0], strip_content )
    elif len(result) == 2:
      # there is a entry
      return (in_sentencetableid, result[0], result[1] )
    else :
      print ( 'getOneTokenSentence error get result len sentencetableid=', in_sentencetableid )
      return None


  #
  # Given the case number and other criteria(like start/end time 
  # for searching), find a list of tuples with Casetable's id , 
  # sentencetable id, tokensentencetable id,tokenize sentence content 
  #
  # in_casenumber : CaseTable's id
  # in_startTime : start time for search
  # in_endTime : end time for search
  # in_needTrainType : indicate to retrieve a train type or not
  # in_tokenbreak : whether tokenize the sentence or not
  # return a list of tuples with four values
  #   ( Casetable's id , sentencetable id, tokensentencetable id, 
  #     tokenize sentence content )
  #
  def getTokenSentencesByCaseNumber (self, 
                       in_casenumber,
                       in_startTime=None, 
                       in_endTime=None,
                       in_needTrainType=False,
                       in_tokenbreak=True
                               ) :
    #there are only 1 to 14 case 
    if in_casenumber < 1 and in_casenumber > 14 :
      print ('getTokenSentencesbycasenumber error casenumber ')
      return None

    # make sure either starttime&endtime = None or both have defined
    if ( in_startTime != None and in_endTime == None) or ( in_endTime != None and in_startTime == None) :
      print ('getTokenSentencessbycasenumber error in_xxxtime  ')
      return None

    if ( in_startTime != None and in_endTime != None ) :
      # get a list of sentencetable id that fullfill the search 
      # criteria 
      result = self.session.query( SentenceTable.id ).join(
        ArticleTable).filter( and_( ArticleTable.timestampondoc >= 
         in_startTime , ArticleTable.timestampondoc <= in_endTime)
          ).filter( SentenceTable.casetable_id == in_casenumber 
           ).filter( SentenceTable.traintype == int(in_needTrainType) 
            ).all()
    else :
      # without searching criteria
      result = self.session.query( SentenceTable.id , 
        SentenceTable.sentencecontent ).filter( 
         SentenceTable.casetable_id == in_casenumber ).filter( 
           SentenceTable.traintype == int(in_needTrainType) ).all()

    if len(result) == 0:
      print ('getTokenSentencessbycasenumber error no result  ')
      #empty result
      return  None

    listOfTokenSentences = []
    # construct a list of tuples for returning
    for indRow in result :
      if in_tokenbreak :
        # tokenize the content
        indTokenSentences = self.getOneTokenSentence( indRow[0] )
        if indTokenSentences is None :
          print ('getTokenSentencesByCaseNumber error cannot getonetokensentence ')
          return None
        # append the result
        listOfTokenSentences.append(( in_casenumber, 
                   indTokenSentences[0], 
                   indTokenSentences[1], 
                   indTokenSentences[2] ) ) 
      else :
        # do not need to tokenize the content
        listOfTokenSentences.append(( in_casenumber, 
                   indRow[0], indRow[0], ' '.join(list(indRow[1])) ) ) 

    return listOfTokenSentences


  # retrieve a dict contains Entity information with a list of 
  # case number
  #
  # separator : separator in the return dict's key
  # numOfZeroFill : how many zero fill in key
  # return a dict with {
  #   key = EntityName & EntityID
  #   value = a dict of case number list
  #  }
  #
  def getEntityDictEmptyList (self,
                       separator='ZZ',
                       numOfZeroFill=10) :
    # get entity table information
    result = self.session.query( EntityTable.name , 
             EntityTable.id , 
             EntityTable.checkrelatedcaselist ).filter( 
               EntityTable.hasfirebasetable == 1).all()
    resultdict = {}
    if ( (result is not None) and  len(result) > 0) :
      # construct the dict
      for indResult in result :
        resultdict[ separator.join( [ indResult[0].zfill(numOfZeroFill),
            str(indResult[1] ).zfill(numOfZeroFill) ] ) ] =  { \
               'checkrelatedcaseList' : [ int(z) for z in indResult[2].strip().split() ],
               'relatedarticleList' : [] }

    return resultdict  


  #
  # get a list of sentences from article's content with given article 
  # id 
  #
  # articleID : article table id
  # return a list of tokenize sentences for a specific articletable id
  #
  def getTokenSenCaseList (self, articleID ) :
    #does it have the tokensentence
    #assume no tokensentence
    #do parse it
    row=self.session.query(ArticleTable).filter( ArticleTable.id == articleID ).first()
    #print ("getTokenSenCaseList articleid=",articleID)
    if row.content is None or (len(row.content) < 2) :
      combine_content = row.title
    else :
      root = lxml.html.fromstring(row.content)
      listStripHTMLTagsString = root.xpath("//text()")
      combine_content = ''.join(listStripHTMLTagsString)
    strip_content=re.sub(r"[^\u4e00-\u9fff()?.,%0-9\u3002\u300c\u300d\uff01\u3010\u3011\uff0c\u3001\u3002\u300a\u300b\uff1a\uff1b]"," ",combine_content)

    out_list=[strip_content.strip()]
    
    # divide up the article into multiple sentences
    for sentenceDivider in ['\u3002\u300d', '\uff01\u300d', 
     '\uff1f\u300d','\u3002', '\uff01', '\uff1b', '\u3000'] :
      intermediate_list=[]
      for index_list in out_list:
        intermediate_list=intermediate_list + \
          index_list.strip().split(sentenceDivider)
      out_list= intermediate_list
      #print('-------------- 7')
    articlerow_id=row.id
    out_list = [x for x in out_list if len(x) > 0 ]
    tokenResultList = []
    #let's start tokenization
    for indSentence in out_list :
      strip_content = re.sub(r"[^\u4e00-\u9fff\uff1a\u300c\u300d\ufe55]", "",  indSentence )
      strip_content = re.sub(r'\u3000', ' ', strip_content)
      strip_content = re.sub(r'[%s]'%''.join(self.stoplist),'' ,
          strip_content)
      strip_content = re.sub(r'\s{2,}', ' ', strip_content)
      # add more customize tokenization  to suit the need

      #add to the result
      tokenResultList.append( strip_content )

    return tokenResultList
      

  #
  # With a pair of articletable ids as input, set cross reference with 
  # the pair of articletable ids in similarities list 
  #
  # in_articleTablePair : two articleTable ids in the list 
  # 
  def setArticleSimilaritieslist(self, in_articleTablePair) :
    # go thur the pair 
    for index, entryID in enumerate(in_articleTablePair) :
      updateEntryID = in_articleTablePair[1] if index == 0 else \
          in_articleTablePair[0]

      #the first checking article id
      result = self.session.query(ArticleTable.similaritieslist, 
        ArticleTable.finalurl ).filter(ArticleTable.id == entryID 
          ).first()
      #the second checking article id  
      result_updateEntryID = self.session.query( ArticleTable.finalurl 
        ).filter(ArticleTable.id == updateEntryID ).first()

      if result is None  :
        # it should have something
        print ('setArticleSimilaritieslist 3 set error ' )
        return
      if result[1] in result_updateEntryID[0] :
        # has very very similiar url
        print ('setArticleSimilaritieslist 5 almost same url ' )
        return


      updatelist =''
      updatecount = 0
      # ---> result[0] =  similarities list of first checking article 
      #                   id
      if result[0] is None :
        # there are nothing in similarities list
        updatelist = updateEntryID 
        updatecount = 1
      else :
        #  checking whether "second checking article id" in 
        #  "first checking article id"'s similarities list
        if (' ' + str(updateEntryID) + ' ') not in (' ' + result[0] + ' ') :
          #if it is not there , add it 
          updatelist = result[0].strip() + ' ' +str(updateEntryID)  
          updatecount = len( updatelist.split() ) 

      
      if updatelist != '' :    
        # go ahead update to database
        result=1
        with open ("databaselockfile", "w") as test_fd :
          fcntl.lockf(test_fd, fcntl.LOCK_EX)
          result = self.session.query(ArticleTable.id).filter(
            ArticleTable.id == entryID ).update( 
              {ArticleTable.similaritieslist : updatelist , 
               ArticleTable.similaritiescount : updatecount } )
          self.session.commit()
          fcntl.lockf(test_fd, fcntl.LOCK_UN)

        if result is None  :
          print ('setArticleSimilaritieslist 8 set error ')
          return



  #
  # retrieve similarities list for specific article table id
  # 
  # in_articleid : article table id for retrieving similarities list
  # return similarities list
  #
  def getArticleSimilaritieslist(self, in_articleid) :
    result = self.session.query(ArticleTable.similaritieslist).filter(ArticleTable.id == in_articleid ).first()
    return result

  #
  # retrieve content and timestamp on doc of a particular article table
  # id
  #
  # in_articleid : article table id for retrieving similarities list
  # return a tuple with (content and  timestamp on doc)
  #
  def getArticleContentTimestamp (self, in_articleid) :
    result = self.session.query( ArticleTable.content , ArticleTable.timestampondoc ).filter(ArticleTable.id == in_articleid ).first()
    return result

  #
  # retrieve a list of tuples (article table id , content , 
  # timestamp on article) with the given a list of article table id,  
  #
  # in_listarticleid : a list of article table id
  # return a list of tuples ( article table id , content, 
  #                           timestamp on article )
  #
  def getListOfArticleContent (self, in_listarticleid) :
    final_resultlist= []
    for indArticleID in in_listarticleid :
      # get the content and timestamp of a article table id
      result = self.getArticleContentTimestamp(int(indArticleID))
      if result is not None :
        print ( 'getListOfArticleContent 4 ', indArticleID ) 
        # construct the result list 
        final_resultlist.append( (indArticleID, result[0], result[1] ) )
    return final_resultlist
   


  #
  # recursively construct a list of aritcle table id which is related 
  # to the input article table id by traversing the similiarities list
  #
  # in_checkArticleid : article table id that uses to retrieve a list 
  #                     of related/similiar article table id 
  # in_withinrangesimlistDict : a dict contains the related/similiar 
  #                             article table id that has similarities 
  #                             list
  # in_notwithinrangesimlistDict : a dict contains the related/similiar 
  #                                article table id that does not have
  #                                similarities list
  # in_starttime : start time for search
  # in_endtime : end time for search
  #
  def recursiveSimlist(self, in_checkArticleid, 
        in_withinrangesimlistDict, in_notwithinrangesimlistDict , 
        in_starttime, in_endtime ) :

    # check whether the article is from start time to end time 
    result = self.session.query(ArticleTable.similaritieslist).filter(
      ArticleTable.id == in_checkArticleid ).filter( and_( 
        ArticleTable.timestampondoc >= in_starttime , 
        ArticleTable.timestampondoc <= in_endtime) ).first()

    
    if result is not None and result[0] is not None :
      # the in_checkArticleid is within the range
      for indArticleid in result[0].strip().split():
        if ( indArticleid not in in_withinrangesimlistDict) and ( 
          indArticleid not in in_notwithinrangesimlistDict  ) : 
          in_withinrangesimlistDict[indArticleid] = indArticleid

          # recursive retrieve the list
          self.recursiveSimlist( in_checkArticleid, 
            in_withinrangesimlistDict, in_notwithinrangesimlistDict , 
            in_starttime, in_endtime )
    else :
      # the in_checkArticleid is not within the range
      in_notwithinrangesimlistDict[in_checkArticleid] = in_checkArticleid
      print ( 'recursiveSimlist 6 in_checkArticleid,=', 
        in_checkArticleid) 


  #
  # retrieve all the related/similiar article table ids within a time 
  # range with given article table id 
  #
  # in_articleid : article table id that uses to get all 
  #                     of related/similiar article table ids
  # in_starttime : start time for search
  # in_endtime : end time for search
  # return 
  #
  def getRecursiveArticleContentfromSimlistInRange (self, 
        in_articleid, in_starttime, in_endtime ) :

    # initial the dict for storing article table ids
    withinrangesimlistDict = {}
    notwithinrangesimlistDict = {}

    # start recursively retrieve similiar article table ids 
    self.recursiveSimlist(in_articleid, withinrangesimlistDict, 
      notwithinrangesimlistDict , in_starttime, in_endtime )
    if len(withinrangesimlistDict) == 0 :
      resultlist = [ in_articleid ]
    else :
      # flatten it out as a list
      resultlist = list(withinrangesimlistDict.keys())
      resultlist.insert(0, str(in_articleid))
    print ('getRecursiveArticleContentfromSimlistInRange 3 ', resultlist )
    return self.getListOfArticleContent ( resultlist )
    






  #
  # get one article entry
  #
  # entryID : article table id
  # return an entry of given article table id
  #
  def getIndArticleEntry(self, entryID) :
    result = self.session.query(ArticleTable).filter(
       ArticleTable.id == entryID ).first()
    return result

  #
  # retrieve number of articles in article table 
  # return the number of articles
  # 
  def getArticleTableCount(self):
    result_list= self.session.query(ArticleTable).count()
    return result_list 


  #
  # get a range of articles in article table 
  # startrow : starting article table id
  # endrow : ending article table id
  # return a range of articles
  # 
  def getArticleTableRange(self, startrow, endrow=0):
    result_list=[] 
    if endrow == 0 :
      result_list = self.session.query(ArticleTable).filter(
        ArticleTable.id > startrow).order_by(ArticleTable.id.asc()
         ).all()
    else : 
      result_list = self.session.query(ArticleTable).filter(
        and_(ArticleTable.id > startrow , ArticleTable.id < endrow)
         ).order_by(ArticleTable.id.asc()).all()
    return result_list 



  # 
  # get the total number of articles for a specified category  
  # 
  # category_eng_name : category english name
  # return total number of articles
  # 
  def getSumOfArticleWithCategory(self, category_eng_name) :
    stmt = self.session.query(FirstSubDomainTable.id).join(
      CategoryTable).filter(CategoryTable.eng_name==category_eng_name,
        CategoryTable.id == FirstSubDomainTable.categorytable_id 
         ).subquery()
    newtotal = self.session.query(ArticleTable).join(stmt, 
      ArticleTable.firstsubdomaintable_id==stmt.c.id ).order_by( 
        ArticleTable.timestampondoc.asc() ).count()
    if newtotal == 0:
      print ("error getSumOfArticleWithCategory  ...... ")
      return 0
    return newtotal


  # 
  # getting a list of articles which are either first category id or 
  # both first and second category id
  # 
  # category_eng_name : first category english name 
  # totalcountfromfirebase : first total number of articles in 
  #                          firebase
  # category_eng_name2 : second category english name 
  # totalcountfromfirebase_name2 : second total number of articles 
  #                          in firebase
  # return 
  # 
  def getArticleWithCategoryAndOffset(self, category_eng_name, 
     totalcountfromfirebase, category_eng_name2=None, 
     totalcountfromfirebase_name2=0) :

    # creating a complex statement for query
    if category_eng_name2 is None :
      stmt = self.session.query(FirstSubDomainTable.id).join(
        CategoryTable).filter(CategoryTable.eng_name==category_eng_name,
          CategoryTable.id == FirstSubDomainTable.categorytable_id 
            ).subquery()
    else :
      stmt = self.session.query(FirstSubDomainTable.id).join(
        CategoryTable).filter( or_(  and_(
          CategoryTable.eng_name==category_eng_name , 
          CategoryTable.id == FirstSubDomainTable.categorytable_id ),
           and_(CategoryTable.eng_name==category_eng_name2 , 
               CategoryTable.id == FirstSubDomainTable.categorytable_id
               ) ) ).subquery()
   
    # total number of articles which fulfill the searching criteria 
    newtotal = self.session.query(ArticleTable).join(stmt, 
      ArticleTable.firstsubdomaintable_id==stmt.c.id ).order_by( 
        ArticleTable.timestampondoc.asc() ).count()
   
    # offset to start retrieve article
    totaloffset = totalcountfromfirebase + totalcountfromfirebase_name2

    # query to get the list of articles
    result = self.session.query(ArticleTable).join(stmt, 
      ArticleTable.firstsubdomaintable_id==stmt.c.id ).order_by( 
        ArticleTable.timestampondoc.asc() ).offset(totaloffset ).limit(
          newtotal - totaloffset ).all()
    if len(result) == 0:
      print ("error getArticleWithCategoryAndOffset  ...... ")
      return 0
    return result




  #
  # get the whole article table 
  #
  # return all the rows from article table
  #  
  def getArticleDict(self):
    return  self.session.query(ArticleTable).all()



  #
  # get the whole Category table
  #
  # return list of CategoryTable's row 
  #  
  def getCategoryDict(self):
    return self.session.query(CategoryTable).all() 

  #
  # get the whole Domain table
  #
  # return list of DomainTable's row 
  #  
  def getDomainDict(self):
    return self.session.query(DomainTable).all() 


  #
  # get the whole First Subdomain table
  #
  # return list of first subdomain's row 
  #  
  def getFirstSubDomainDict(self):
    return self.session.query(FirstSubDomainTable).all() 

  #
  # delete all table content
  # 
  def deleteAllTable(self) :
    self.session.query(DomainTable).delete()
    self.session.query(CategoryTable).delete()
    self.session.query(FirstSubDomainTable).delete()
    self.session.query(ArticleTable).delete()
    self.session.commit()


  #
  # initialize database with fake data 
  #
  def init_fake_data(self):
    domaintable_entry=DomainTable(
      baseurl='http://news.rthk.hk',
      chi_name='香港電台',
      eng_name='rthk')
    self.session.add(domaintable_entry)
    domaintable_entry=DomainTable(
      baseurl='http://881903.com',
      chi_name='商業電台',
      eng_name='crhk')
    self.session.add(domaintable_entry)
    categorytable_entry=CategoryTable(
      chi_name='要聞港聞',
      eng_name='headlinenews')
    self.session.add(categorytable_entry)
    firstsubdomaintable_entry=FirstSubDomainTable(
      domaintable_id=1,
      categorytable_id=1,
      firstsubd='/hello1',
      onlyweekdays=False)
    self.session.add(firstsubdomaintable_entry)
    firstsubdomaintable_entry=FirstSubDomainTable(
      domaintable_id=1,
      categorytable_id=2,
      firstsubd='/hello2',
      onlyweekdays=False)
    self.session.add(firstsubdomaintable_entry)


    article_entry=ArticleTable(
      firstsubdomaintable_id=1,
      finalurl="url1",
      timestampondoc=datetime.now(timezone(timedelta(hours=8))),
      timestamponretrieve=datetime.now(timezone(timedelta(hours=8))),
      title="title 1",
      content="content 1"
      )
    self.session.add(article_entry)
    article_entry=ArticleTable(
      firstsubdomaintable_id=2,
      finalurl="url2",
      timestampondoc=datetime.now(timezone(timedelta(hours=8))),
      timestamponretrieve=datetime.now(timezone(timedelta(hours=8))),
      title="title 2",
      content="content 2"
      )
    self.session.add(article_entry)
    self.session.commit()








      
