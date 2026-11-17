import pandas as pd
import streamlit as st
from src.analysis import load_articles, analyze, TOPICS, export_analysis
from src.database import save_database

st.set_page_config(page_title='PubMed Research Miner',page_icon='🧬',layout='wide')
st.title('🧬 PubMed Biomedical Article Mining')
st.caption('Exploratory text mining of titles and abstracts. Topic categories are rule-based and can overlap.')

@st.cache_data
def read_data(): return load_articles()
try: df=read_data()
except Exception as e:
    st.error(f'Unable to load CSV: {e}');st.stop()

st.sidebar.header('Explore articles')
query=st.sidebar.text_input('Search title or abstract',placeholder='e.g. genomic')
years=sorted([int(x) for x in df['Year'].dropna().unique()])
selected=st.sidebar.multiselect('Publication years',years,default=years)
chosen=st.sidebar.multiselect('Topic categories',list(TOPICS))
filtered=df[df['Year'].isin(selected)].copy()
if query: filtered=filtered[filtered['Text'].str.contains(query,case=False,regex=False,na=False)]
if chosen: filtered=filtered[filtered[chosen].any(axis=1)]

c1,c2,c3=st.columns(3)
c1.metric('Articles in dataset',len(df));c2.metric('Filtered articles',len(filtered));c3.metric('Articles with abstracts',int(filtered['Abstract'].str.strip().ne('').sum()))

t1,t2,t3,t4=st.tabs(['Articles','Keywords / TF-IDF','Yearly trends','Topic categories'])
with t1:
    st.dataframe(filtered[['PMID','Title','Journal','Publication_Date','Abstract']],use_container_width=True,hide_index=True)
    st.download_button('Download filtered articles (CSV)',filtered[['PMID','Title','Abstract','Authors','Journal','Publication_Date']].to_csv(index=False).encode(),'filtered_articles.csv','text/csv')
with t2:
    if filtered.empty: st.info('No articles match these filters.')
    else:
        terms,tf=analyze(filtered,20)
        left,right=st.columns(2)
        with left:
            st.subheader('Frequent words / phrases');st.bar_chart(terms.set_index('Term')['Count'])
            st.dataframe(terms,hide_index=True)
        with right:
            st.subheader('Mean TF-IDF scores');st.bar_chart(tf.set_index('Term')['Mean_TFIDF'])
            st.dataframe(tf,hide_index=True)
        st.caption('Stopwords and broad search terms are excluded to reveal more specific vocabulary; TF-IDF is computed on the currently filtered documents.')
with t3:
    counts=filtered.groupby('Year').size().rename('Articles').sort_index()
    if counts.empty: st.info('No matching records.')
    else: st.bar_chart(counts)
    st.caption('These are counts in the collected sample, not PubMed-wide annual publication totals. Relevance-ranked sampling can bias trends.')
with t4:
    topic_counts=pd.Series({t:int(filtered[t].sum()) for t in TOPICS}).sort_values(ascending=False)
    st.bar_chart(topic_counts)
    st.dataframe(topic_counts.rename('Articles'),use_container_width=True)
    st.caption('Rule-based keyword categories; a single article may appear in multiple categories. A keyword match does not establish the paper’s primary topic.')

st.divider()
if st.button('Save complete dataset analysis and SQLite database'):
    export_analysis(df);save_database(df);st.success('Saved processed CSV, analysis tables, and data/articles.db')
st.info('To collect a new PubMed topic, run `python src/data_collection.py` from the project root, then restart or clear Streamlit cache. NCBI access requires internet.')
