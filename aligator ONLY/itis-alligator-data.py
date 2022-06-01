import csv
import sys
import json
import pandas as pd
import numpy as np
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

# taxon name: P225
# taxon common name: P1843
# Get alligator id, definition, prelabel (use with triple style code)
def animal_id(animal):
    query = "SELECT ?item ?itemLabel ?itemDescription  \
        WHERE \
            {?item wdt:P225 \"" + animal + "\" . \
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
        return id, label.capitalize(), description.capitalize()
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


            
df = pd.read_csv("animal-species/Chinese Alligator/taxa_9796598.txt", sep="\t")
print(df)

# extraneous information
type = df.dtypes
print(type)
num_rows = len(df.count(axis=1))
num_columns = len(df.count(axis=0))


# open ttl file
outfile = open('itis-alligator-data.ttl', 'w')

outfile.write("@prefix boltz: <http://solid.boltz.cs.cmu.edu:3030/data/> . \n\
@prefix kgo:   <http://solid.boltz.cs.cmu.edu:3030/ontology/> . \n\
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> . \n\
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> . \n\
@prefix owl:   <http://www.w3.org/2002/07/owl#> . \n\
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> . \n\
@prefix qudt:  <http://qudt.org/schema/qudt/> . \n\
@prefix unit:  <http://qudt.org/vocab/unit/> . \n\
@prefix qkdv:  <http://qudt.org/vocab/dimensionvector/> . \n\
@prefix sou: <http://qudt.org/vocab/sou/> . \n\
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> . \n\n\
")

#keep track of prev ID, used for subParentID
q_values = {}

# convert data to triples here 
for index, row in df.iterrows():
    # check row: already looked up OR not valid
    if row["taxonID"] in q_values or not row['taxonomicStatus'] == "valid":
        continue

    scientificName = row["scientificName"]
    # change scientificName, some have author appended onto it
    if not pd.isna(row["scientificNameAuthorship"]) and row["scientificNameAuthorship"]in row["scientificName"]:
        scientificName = row["scientificName"].replace(" " + row["scientificNameAuthorship"], "")

    # subTaxon dictionary lookup
    if not pd.isna(row["parentNameUsageID"]) and int(row["parentNameUsageID"]) in q_values: 
        parent_id = q_values[int(row["parentNameUsageID"])]
        full_parent_ID = "kgo:subTaxonOf\tboltz:" + parent_id + " ; \n\t"
    else:
        full_parent_ID = ""
    
    ID, label, definition = animal_id(scientificName)
    full_name = "kgo:taxonName \t" + "\"" + scientificName + "\"@en ; \n\t"
    full_ID = "boltz:" + ID + " a kgo:Taxon ; \n\t" #ID
    full_rank = "kgo:taxonRank\tkgo:" + row['taxonRank'].capitalize() + " ; \n\t" #rank
    full_definition = "skos:definition\t\"" + definition + "\"@en ;\n\t"

    # preflabel – common name
    full_label = "skos:prefLabel\t\"" + label + "\"@en .\n\n"
    
    # update dict
    q_values[row["taxonID"]] = ID
        
    d =  full_ID + full_parent_ID + full_name + full_rank + full_definition + full_label
    outfile.write(d)

outfile.close()
print(q_values)