import sys
import pandas as pd
import numpy as np
import ssl
import glob
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

# Get Q-value, definition, prelabel (use with triple style code)
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
    # query may conjure up multiple results, we choose the first one. question: should we assume all queries only return one?
    try:
        result = results["results"]["bindings"][0]
        url = result['item']['value']
        label = result['itemLabel']['value']
        try:
            description = result['itemDescription']['value']
        except: #in the case of no description 
            description = ""
        n = -1
        id = ""    
        while url[n] != "/":
            id = url[n:]
            n -= 1
        print(id + "  " + label + "  " + description)
        return id, label.capitalize(), description.capitalize()
    except:
        return "", "", ""

# Query with subgenus, more accuracy as utilizes parent ID
def animal_id2(animal, parent):
    query = "SELECT ?item ?itemLabel ?itemDescription  \
        WHERE \
            {?item wdt:P171 wd:" + parent + ";\
                   wdt:P225 \"" + animal + "\" . \
            SERVICE wikibase:label \
            {bd:serviceParam wikibase:language \"en\" . } \
        }"

    results = get_results(endpoint_url, query)
    print('result1:')
    print(results)
    # query may conjure up multiple results, we choose the first one. question: should we assume all queries only return one?
    try:
        result = results["results"]["bindings"][0]
        url = result['item']['value']
        label = result['itemLabel']['value']
        try:
            description = result['itemDescription']['value']
        except: #in the case of no description 
            description = ""
        n = -1
        id = ""    
        while url[n] != "/":
            id = url[n:]
            n -= 1
        print(id + "  " + label + "  " + description)
        return id, label.capitalize(), description.capitalize()
    except:
        return "", "", ""


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



# open ttl file
outfile = open('100-species.ttl', 'w')

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

# Q-values for ranks
ranks = {"kingdom": "Q36732", "subkingdom": "Q2752679", "infrakingdom": "Q3150876", "superphylum":"Q3978005", "phylum": "Q38348", "subphylum": "Q1153785", "infraphylum": "Q2361851", "superclass": "Q3504061", "infraclass": "Q2007442", "class": "Q37517", "subclass": "Q5867051", "superorder":"Q5868144", "infraorder": "Q2889003", "order" :"Q36602", "suborder": "Q5867959", "superfamily" : "Q2136103", "family": "Q35409", "subfamily": "Q164280", "tribe":"Q227936","subtribe": "Q3965313", "genus": "Q34740", "subgenus":"Q3238261", "species": "Q7432", "subspecies": "Q68947"}

# open species files
folder_path = 'species'
file_list = glob.glob(folder_path + "/*.txt")

for i in range(1,len(file_list)):
    #keep track of prev ID, used for subParentID
    q_values = {}

    data = pd.read_table(file_list[i])
    df = pd.DataFrame(data)
    
    outfile.write("#-----TAXON------\n")
    # convert data to triples here 
    for index, row in df.iterrows():
        # check row: already looked up OR not valid
        if row["taxonID"] in q_values or not row['taxonomicStatus'] == "valid":
            continue

        scientificName = row["scientificName"]

        # change scientificName, some have author appended onto it
        if not pd.isna(row["scientificNameAuthorship"]) and row["scientificNameAuthorship"]in row["scientificName"]:
            scientificName = row["scientificName"].replace(" " + row["scientificNameAuthorship"], "")
        

        # subTaxon dictionary lookup + INFO lookup: usage of parentID in query IF parentID exists
        if not pd.isna(row["parentNameUsageID"]) and int(row["parentNameUsageID"]) in q_values: 
            parent_id = q_values[int(row["parentNameUsageID"])]
            full_parent_ID = "kgo:subTaxonOf\tboltz:" + parent_id + " ; \n\t"
        else:
            full_parent_ID = ""


        # if sub-genus, actual name is the one in the parenthesis. for example: Cicindela (Cicindelidia) means that Cicindelidia is the sub-genus in hand, where Cicindela is its parent. cannot directly use entire term in serach query, as that generates no results. also generate a more precise search query which uses the parentID: 
        if row['taxonRank'] == "subgenus":
            x = scientificName.split(" (")
            y = x[1].split(")")
            scientificName = y[0]
            ID, label, definition = animal_id2(scientificName, parent_id)
        else:
            ID, label, definition = animal_id(scientificName)

            
        full_name = "kgo:taxonName \t" + "\"" + scientificName + "\"@en ; \n\t"
        full_ID = "boltz:" + ID + " a kgo:Taxon ; \n\t" #ID
        full_rank = "kgo:taxonRank\tboltz:" + ranks[row['taxonRank']] + " ; \n\t" #rank
        full_definition = "skos:definition\t\"\"\"" + definition + "\"\"\"@en ;\n\t"

        # preflabel – common name
        full_label = "skos:prefLabel\t\"" + label + "\"@en .\n\n"
        
        # update dict
        q_values[row["taxonID"]] = ID
            
        d =  full_ID + full_parent_ID + full_name + full_rank + full_definition + full_label 
        outfile.write(d)
    outfile.write("\n")

outfile.close()
