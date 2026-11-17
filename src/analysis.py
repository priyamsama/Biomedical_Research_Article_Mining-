import re
from collections import Counter
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, ENGLISH_STOP_WORDS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'raw' / 'pubmed_articles.csv'
TOPICS = {
    'Machine learning / AI': [r'\bmachine learning\b', r'\bdeep learning\b', r'\bartificial intelligence\b', r'\bneural network', r'\bclassification model'],
    'Genomics / sequencing': [r'\bgenom', r'\bsequenc', r'\bwhole.genome', r'\bwg[s]?\b'],
    'Resistance genes / mechanisms': [r'\bresistance gene', r'\bresistance mechanism', r'\bmutation', r'\bdeterminant', r'\bbeta.lactamase'],
    'Diagnostics / susceptibility': [r'\bdiagnos', r'\bsusceptib', r'\bmaldi', r'\bmass spectrom', r'\bclinical microbiolog'],
    'Surveillance / epidemiology': [r'\bsurveill', r'\bepidemiolog', r'\bprevalence', r'\bmonitoring'],
}
STOP = list(ENGLISH_STOP_WORDS.union({'amr','antimicrobial','resistance','antibiotic','antibiotics','study','studies','using','based','results','methods','data','research','predict','prediction','predicting','model','models','patients','clinical'}))

def load_articles(path=DATA):
    df=pd.read_csv(path, dtype={'PMID':str}).fillna('')
    required={'PMID','Title','Abstract','Authors','Journal','Publication_Date'}
    missing=required-set(df.columns)
    if missing: raise ValueError('Missing columns: '+', '.join(sorted(missing)))
    df=df.drop_duplicates(subset=['PMID']).copy()
    df['Year']=pd.to_numeric(df['Publication_Date'].astype(str).str.extract(r'(\d{4})')[0],errors='coerce').astype('Int64')
    df['Text']=(df['Title'].astype(str)+' '+df['Abstract'].astype(str)).str.strip()
    df['Clean_Text']=df['Text'].str.lower().str.replace(r'[^a-z0-9\s-]',' ',regex=True).str.replace(r'\s+',' ',regex=True).str.strip()
    for topic,patterns in TOPICS.items():
        df[topic]=df['Text'].str.contains('|'.join(patterns),case=False,regex=True,na=False)
    return df

def analyze(df, top_n=20):
    texts=df['Clean_Text'].fillna('').tolist()
    if not any(x.strip() for x in texts): return pd.DataFrame(columns=['Term','Count']),pd.DataFrame(columns=['Term','Mean_TFIDF'])
    cv=CountVectorizer(stop_words=STOP,ngram_range=(1,2),min_df=1,token_pattern=r'(?u)\b[a-z][a-z0-9-]{2,}\b')
    counts=cv.fit_transform(texts)
    count_df=pd.DataFrame({'Term':cv.get_feature_names_out(),'Count':counts.sum(axis=0).A1}).sort_values(['Count','Term'],ascending=[False,True]).head(top_n).reset_index(drop=True)
    tf=TfidfVectorizer(vocabulary=cv.vocabulary_,use_idf=True,sublinear_tf=True)
    matrix=tf.fit_transform(texts)
    tf_df=pd.DataFrame({'Term':tf.get_feature_names_out(),'Mean_TFIDF':matrix.mean(axis=0).A1}).sort_values('Mean_TFIDF',ascending=False).head(top_n).reset_index(drop=True)
    return count_df,tf_df

def export_analysis(df,output=ROOT/'outputs'):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    df.to_csv(ROOT/'data'/'processed'/'processed_articles.csv',index=False)
    terms,tfidf=analyze(df)
    terms.to_csv(output/'top_terms.csv',index=False)
    tfidf.to_csv(output/'top_tfidf.csv',index=False)
    df.groupby('Year',dropna=False).size().rename('Articles').reset_index().to_csv(output/'publication_by_year.csv',index=False)
    pd.DataFrame({'Topic':list(TOPICS),'Articles':[int(df[t].sum()) for t in TOPICS]}).to_csv(output/'topic_counts.csv',index=False)
    return terms,tfidf

if __name__=='__main__':
    d=load_articles();export_analysis(d)
    print(f'Analyzed {len(d)} unique articles; outputs saved to outputs/ and data/processed/')
