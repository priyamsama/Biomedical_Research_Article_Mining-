from Bio import Entrez, Medline
import pandas as pd
import time
import os


Entrez.email = "priyamsama.iccr@gmail.com"


topic = input("Enter a biomedical research topic: ")
start_year = input("Enter starting year: ")
end_year = input("Enter ending year: ")
max_articles = int(input("How many articles should we collect? "))


query = (
    f'"{topic}"[Title/Abstract] AND '
    f'{start_year}:{end_year}[dp]'
)

print("\nSearching PubMed...")
print("Search query:", query)

handle = Entrez.esearch(
    db="pubmed",
    term=query,
    retmax=max_articles,
    sort="relevance"
)

search_results = Entrez.read(handle)
handle.close()

article_ids = search_results["IdList"]
total_found = int(search_results["Count"])

print("Total matching articles:", total_found)
print("Articles selected:", len(article_ids))


all_articles = []

for i in range(0, len(article_ids), 100):

    batch = article_ids[i:i + 100]

    handle = Entrez.efetch(
        db="pubmed",
        id=batch,
        rettype="medline",
        retmode="text"
    )

    records = Medline.parse(handle)

    for record in records:
        article = {
            "PMID": record.get("PMID", ""),
            "Title": record.get("TI", ""),
            "Abstract": record.get("AB", ""),
            "Authors": "; ".join(record.get("AU", [])),
            "Journal": record.get("JT", ""),
            "Publication_Date": record.get("DP", "")
        }

        all_articles.append(article)

    handle.close()
    time.sleep(0.4)


df = pd.DataFrame(all_articles)


os.makedirs("data/raw", exist_ok=True)

df.to_csv(
    "data/raw/pubmed_articles.csv",
    index=False,
    encoding="utf-8-sig"
)

print("\nData collection completed!")
print("Number of articles collected:", len(df))
print("Saved to: data/raw/pubmed_articles.csv")
