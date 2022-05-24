import csv
import sys
import json
import pandas as pd

from SPARQLWrapper import SPARQLWrapper, JSON
from os import sep

endpoint_url = "https://query.wikidata.org/sparql"

def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

# Get alligator id
def animal_id(animal):
    query = "SELECT ?item WHERE {?item rdfs:label " + animal + "@en. }"
    results = get_results(endpoint_url, query)
    print('result1:')

    for result in results["results"]["bindings"]:
        url = result['item']['value']
        n = -1
        id = ""    
        while url[n] != "/":
            id = url[n:]
            n -= 1
        print(id)
    return id


# Get parent taxon property id

def parent_ID(parent_taxon):
    query = "SELECT ?x ?p ?wdt WHERE { \
        ?x rdfs:label " + parent_taxon + "@en; \
        wikibase:claim ?p; \
        wikibase:directClaim ?wdt. \
        }" 

    results = get_results(endpoint_url, query)
    print('result2:')

    for result in results["results"]["bindings"]:
        url = result['p']['value']
        n = -1
        parent_taxon = ""
        while url[n] != "/":
            parent_taxon = url[n:]
            n -= 1
        print(parent_taxon)
    return parent_taxon


# Get taxon rank property

def taxon_rank(rank):
    query = "SELECT ?x ?p ?wdt WHERE { \
        ?x rdfs:label " + rank + "@en;  \
        wikibase:claim ?p; \
        wikibase:directClaim ?wdt. \
        }" 

    results = get_results(endpoint_url, query)
    print('result3:')

    for result in results["results"]["bindings"]:
        url = result['p']['value']
        n = -1
        taxon_rank = ""
        while url[n] != "/":
            taxon_rank = url[n:]
            n -= 1
        print(taxon_rank)    
    return taxon_rank

# Print taxonomic hierarchy

def taxonomic_hierarchy():
    query = " SELECT ?item ?taxonrank ?itemlabel ?taxonranklabel \
    WHERE \
    { \
        wd:Q530397 wdt:P171* ?item. \
        ?item wdt:P105 ?taxonrank. \
        ?item rdfs:label ?itemlabel filter (lang(?itemlabel) = \"en\"). \
        ?taxonrank rdfs:label ?taxonranklabel filter (lang(?taxonranklabel) = \"en\"). \
    }" 

    results = get_results(endpoint_url, query)
    print('results4:')

    for result in results["results"]["bindings"]:
        taxonrank = result['taxonranklabel']['value']
        item = result['itemlabel']['value']
        print(taxonrank, 'is', item)


            
df = pd.read_csv("itis/taxa_9796598.txt", sep='\t')
type = df.dtypes
num_rows = len(df.count(axis=1))
num_columns = len(df.count(axis=0))

# convert to readable csv file
df.to_csv('itis.csv')

# open ttl file
outfile = open('itis-alligator-data.ttl', 'a')

# convert data to triples here 
for index, row in df.iterrows():
    if index == 0:
        pass
    else: 
        ID = animal_id(row['scientificName'])
        
        # handle taxonRemarks 
        info = ''
        if not pd.isna(row['taxonRemarks']):
            info = row['taxonRemarks']
        
        d = "boltz: " + ID + " a kgo:Taxon ; \n\t kgo:subTaxonOf boltz: ; \n\t kgo:taxonName \t" + "\"" + row['scientificName'] + "\"" + "@en ; \n\t kgo:taxonRank \t kgo:" + row['taxonRank'] + " ; \n\t kgo:taxonRemark \t" + "\"" + info + "\"" + " . \n"
        outfile.write(d)



outfile.close()
