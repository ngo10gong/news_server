News Server
==========

This repository contains differnt database table definitin and the middleware which help inidividual program/script to get/set/manipulate data in database.  The middleware is using sqlalchemy to handle the communication with sqlite database. 

Example
-------
After starting python in your terminal, you may do the following 

```pycon
Python 3.5.2 (default, Nov 17 2016, 17:05:23) 
[GCC 5.4.0 20160609] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> from news_server_db import NewsAllTable
>>> newserver = NewsAllTable("news.db")
>>> newserver.init_all_table()
<sqlalchemy.orm.session.Session object at 0x7fcdd6fd2588>
>>> newserver.deleteAllTable()
>>> newserver.init_fake_data()
>>> newserver.getArticleDict()
[<ArticleTable(id='1', firstsubdomaintable_id='1', finalurl='url1', timestampondoc='2018-01-11 06:11:10.872448', timestamponretrieve='2018-01-11 06:11:10.872471', title='title 1', content='content 1', jpegname='None', imageurl='None', similaritieslist='None', similaritiescount='None' , )>, <ArticleTable(id='2', firstsubdomaintable_id='2', finalurl='url2', timestampondoc='2018-01-11 06:11:10.872817', timestamponretrieve='2018-01-11 06:11:10.872829', title='title 2', content='content 2', jpegname='None', imageurl='None', similaritieslist='None', similaritiescount='None' , )>]

```

License
-------
See the [LICENSE][1] file for details.

[1]: https://github.com/ngo10gong/news_server/blob/master/LICENSE
