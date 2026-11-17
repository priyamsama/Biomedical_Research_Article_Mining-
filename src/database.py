import sqlite3
from pathlib import Path
from src.analysis import ROOT, load_articles

def save_database(df, path=ROOT/'data'/'articles.db'):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS articles (pmid TEXT PRIMARY KEY, title TEXT, abstract TEXT, authors TEXT, journal TEXT, publication_date TEXT, year INTEGER)")
        rows=[(str(r.PMID),r.Title,r.Abstract,r.Authors,r.Journal,r.Publication_Date,None if str(r.Year)=='<NA>' else int(r.Year)) for r in df.itertuples()]
        conn.executemany('INSERT OR REPLACE INTO articles VALUES (?,?,?,?,?,?,?)',rows)
        conn.commit()
    return path

if __name__=='__main__':
    df=load_articles();print('Saved',len(df),'articles to',save_database(df))
