import csv
import sys
import json
import pandas as pd
import ssl
ssl._create_default_https_context = ssl._create_unverified_context

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

# Get alligator id, definition, prelabel (use with triple style code)
def animal_id(animal):
    query = "SELECT ?item ?itemLabel ?itemDescription  \
        WHERE \
            {?item rdfs:label \"" + animal + "\"@en. \
            SERVICE wikibase:label \
            {bd:serviceParam wikibase:language \"en\" . } \
        }"

    results = get_results(endpoint_url, query)
    print('result1:')
    print(results)
    id=""
    for result in results["results"]["bindings"]:
        url = result['item']['value']
        label = result['itemLabel']['value']
        description = result['itemDescription']['value']
        n = -1
        id = ""    
        while url[n] != "/":
            id = url[n:]
            n -= 1
        print(id + "  " + label + "  " + description)
        return id, label, description
    return id, "", ""
    


# Get parent taxon property id: didn't end up using, just accessed previous generated ID
def parent_ID(parent_taxon):
    query = "SELECT ?x ?p ?wdt WHERE { \
        ?x rdfs:label \"" + parent_taxon + "\"@en; \
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

# Get taxon rank property (faulty)

def taxon_rank(rank):
    query = "SELECT ?x ?p ?wdt WHERE { \
        ?x rdfs:label \"" + rank + "\"@en;  \
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

# clean up dataframe 
df = df.loc[df["taxonomicStatus"] == "valid"]
updated_names = [a.replace(" " + b, "") for (a, b) in zip(df["scientificName"].values, df["scientificNameAuthorship"].fillna('').values)]
df["scientificName"] = updated_names
print(df)


# extraneous information
type = df.dtypes
num_rows = len(df.count(axis=1))
num_columns = len(df.count(axis=0))

# convert to readable csv file
df.to_csv('itis.csv')

# open ttl file
outfile = open('itis-alligator-data.ttl', 'a')

#keep track of prev ID, used for subParentID
ID = "" 
full_parent_ID = ""

# convert data to triples here 
for index, row in df.iterrows():
    if index != 0: 
        parent_id = ID
        full_parent_ID = "kgo:subTaxonOf\tboltz:" + parent_id + " ; \n\t"
    
    print(row['scientificName'])
    ID, label, definition = animal_id(row['scientificName'])
    full_name = "kgo:taxonName \t" + "\"" + row['scientificName'] + "\"@en ; \n\t"
    full_ID = "boltz:" + ID + " a kgo:Taxon ; \n\t" #ID
    full_rank = "kgo:taxonRank\tkgo:" + row['taxonRank'].capitalize() + " ; \n\t" #rank
    full_definition = "skos:definition\t\"" + definition + "\"@en ;\n\t"
    full_label = "skos:prefLabel\t\"" + label + "\"@en .\n\n"
    
        
    d =  full_ID + full_parent_ID + full_name + full_rank + full_definition + full_label
    outfile.write(d)



outfile.close()
