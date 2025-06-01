from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP, JSON, Boolean
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Publisher(Base):
    __tablename__ = 'publisher'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    stance = Column(String(45))

    


class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(Text)
    url = Column(String(500))
    reporter = Column(String(45))
    publish_date = Column(TIMESTAMP)
    publisher = Column(String(255))
    img_addr = Column(String(255))
    likes = Column(Integer)
    views = Column(Integer)
    field = Column(String(255))
    headline = Column(Integer)

    # 관계
    article_summaries = relationship("ArticleSummary", back_populates="article")
    bridges = relationship("Bridge", back_populates="article")


class HotTopic(Base):
    __tablename__ = 'hot_topics'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    create_date = Column(TIMESTAMP)
    activate = Column(Integer)

    article_summaries = relationship("ArticleSummary", back_populates="hot_topic")
    analysis_summaries = relationship("AnalysisSummary", back_populates="hot_topic")
    bridges = relationship("Bridge", back_populates="hot_topic")


class Bridge(Base):
    __tablename__ = 'bridge'

    id = Column(Integer, primary_key=True)
    hot_topics_id = Column(Integer, ForeignKey('hot_topics.id'))
    articles_id = Column(Integer, ForeignKey('articles.id'))
    stance = Column(String(255))

    hot_topic = relationship("HotTopic", back_populates="bridges")
    article = relationship("Article", back_populates="bridges")


class ArticleSummary(Base):
    __tablename__ = 'article_summary'

    id = Column(Integer, primary_key=True)
    summary_text = Column(Text)
    create_date = Column(TIMESTAMP)
    hot_topics_id = Column(Integer, ForeignKey('hot_topics.id'))
    articles_id = Column(Integer, ForeignKey('articles.id'))

    article = relationship("Article", back_populates="article_summaries")
    hot_topic = relationship("HotTopic", back_populates="article_summaries")


class AnalysisSummary(Base):
    __tablename__ = 'analysis_summary'

    id = Column(Integer, primary_key=True)
    content = Column(JSON)
    hot_topics_id = Column(Integer, ForeignKey('hot_topics.id'))

    hot_topic = relationship("HotTopic", back_populates="analysis_summaries")
