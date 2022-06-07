import sys
import pandas as pd
import numpy as np
import ssl
import glob
ssl._create_default_https_context = ssl._create_unverified_context

from SPARQLWrapper import SPARQLWrapper, JSON
from os import sep


endpoint_url = "https://query.wikidata.org/sparql"

# TAXA that didn't initially match: need to manually check again
to_confirm = {}

# IMPORTED DATA 
# Q-values for ranks
ranks = {"kingdom": "Q36732", "subkingdom": "Q2752679", "infrakingdom": "Q3150876", "superphylum":"Q3978005", "phylum": "Q38348", "subphylum": "Q1153785", "infraphylum": "Q2361851", "superclass": "Q3504061", "infraclass": "Q2007442", "class": "Q37517", "subclass": "Q5867051", "superorder":"Q5868144", "infraorder": "Q2889003", "order" :"Q36602", "suborder": "Q5867959", "superfamily" : "Q2136103", "family": "Q35409", "subfamily": "Q164280", "tribe":"Q227936","subtribe": "Q3965313", "genus": "Q34740", "subgenus":"Q3238261", "species": "Q7432", "subspecies": "Q68947"}


# MANUALLY CREATED TAXA: taxa that we manually added, no entry WikiData
all_taxa =  {
    1157319: {"Q": "Q3427090", "Def": "Genus of insects", "Label": "Cnephasia", "image": "", "WikiData": True},
    729890: {"Q": "Q27636553", "Def": "Subspecies of bird", "Label": "Molothrus oryzivorus impacifus", "image": "", "WikiData": True },
    949898: {"Q": "Q500000000", "Def": "Subspecies of reptile", "Label": "Psammobates tentorius tentorius", "image": "", "WikiData": False},
    1084534: {"Q": "Q500000001", "Def": "Subspecies of reptile", "Label": "Telescopus dhara somalicus", "image": "", "WikiData": False},
    1084130: {"Q": "Q500000002", "Def": "Subspecies of reptile", "Label": "Duberria lutrix atriventris",  "image": "","WikiData": False},
    1084132: {"Q": "Q500000003", "Def": "Subspecies of reptile", "Label": "Duberria lutrix lutrix",  "image": "","WikiData": False},
    1157483: {"Q": "Q500000004", "Def": "Subspecies of mammal", "Label": "Eptesicus serotinus mirza",  "image": "", "WikiData": False}
}

def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

# Extract ID, label, and description 
def extract(results):
    result = results["results"]["bindings"][0]
    url = result['item']['value']
    label = result['itemLabel']['value']
    try:
        image_link = result['image']['value']
    except:
        image_link = ""
    try:
        description = result['itemDescription']['value']
    except: #in the case of no description 
        description = ""
    n = -1
    id = ""    
    while url[n] != "/":
        id = url[n:]
        n -= 1
    print(id + "  " + image_link + " " + label + "  " + description)
    return id, image_link, description.capitalize(), label.capitalize(),

def valid_search(results):
    return len(results["results"]["bindings"]) != 0

def run_q1(animal):
    query1 = "SELECT ?item ?image ?itemLabel ?itemDescription  \
        WHERE \
            {?item wdt:P225 \"" + animal + "\" . \
             OPTIONAL{?item wdt:P18 ?image} . \
            SERVICE wikibase:label \
            {bd:serviceParam wikibase:language \"en\" . } \
        }"
    results = get_results(endpoint_url, query1)
    print('result1:')
    print(results)
    return results
    
# use of alt label, sometimes the taxonomic name is the alias
def run_q2(animal):
    query2 = "SELECT ?item ?image ?itemLabel ?itemDescription  \
        WHERE \
            {?item skos:altLabel \"" + animal + "\"@en . \
                 OPTIONAL{?item wdt:P18 ?image} . \
            SERVICE wikibase:label \
            {bd:serviceParam wikibase:language \"en\" . } \
        }"
    results = get_results(endpoint_url, query2)
    print('result1:')
    print(results)
    return results

# use of regex – three letter difference maximum
def run_q3(animal, parent):
    n = 0
    while n < 4:
        new_animal = animal[:0-1]
        # might not be EXACT parentLabel but the PATH matches, intentional because some discrepancies between WikiData and ITIS parentTaxons
        query3 = "SELECT ?item ?image ?itemLabel ?itemDescription WHERE \
            { \
             ?item wdt:P171* wd:" + parent + "; \
                   rdfs:label ?itemLabel. \
             OPTIONAL{?item wdt:P18 ?image} . \
            filter(regex(str(?itemLabel), \"" + new_animal + "\" )) . \
            SERVICE wikibase:label  \
            {bd:serviceParam wikibase:language \"en\"  . } \
            }" 
        results = get_results(endpoint_url, query3)
        # check if query yielded a valid result
        if valid_search(results):
            return results
        n += 1
    return results

# Get Q-value, definition, prelabel (use with triple style code)
def taxa(animal, ID, parent):
    results1 = run_q1(animal)
    if valid_search(results1): #way to check if search yields results
        return extract(results1)
    else:
        results2 = run_q2(animal)
    
    if valid_search(results2):
        return extract(results2)
    else:
        to_confirm[ID] = animal
        return extract(run_q3(animal, parent))
    

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

# open species files
folder_path = 'species'
file_list = glob.glob(folder_path + "/*.txt")

# For every file in directory:
for i in range(0,len(file_list)):
    data = pd.read_table(file_list[i])
    df = pd.DataFrame(data)
    
    outfile.write("#-----TAXON------\n")
    # For every taxa in file: 
    for index, row in df.iterrows():
        # Only run valid taxa
        if not row['taxonomicStatus'] == "valid":
            continue

        scientificName = row["scientificName"]
        #----- CLEAN DATA -----
        # Change scientificName, some have author appended onto it
        if not pd.isna(row["scientificNameAuthorship"]) and row["scientificNameAuthorship"]in row["scientificName"]:
            scientificName = row["scientificName"].replace(" " + row["scientificNameAuthorship"], "")

        # if sub-genus, actual name is the one in the parenthesis. for example: Cicindela (Cicindelidia) means that Cicindelidia is the sub-genus in hand, where Cicindela is its parent. cannot directly use entire term in serach query, as that generates no results. also generate a more precise search query which uses the parentID: 
        if row['taxonRank'] == "subgenus":
            x = scientificName.split(" (")
            y = x[1].split(")")
            scientificName = y[0]
        
        # ----- RETRIEVE INFORMATION ----
        # Search parentTaxon information
        if not pd.isna(row["parentNameUsageID"]) and int(row["parentNameUsageID"]) in all_taxa: 
            parent_Q = all_taxa[int(row["parentNameUsageID"])]["Q"]
            full_parent_Q = "kgo:subTaxonOf\tboltz:" + parent_Q + " ; \n\t"
        else:
            parent_Q = ""
            full_parent_Q = ""
        
        # Everything else: either quick dictionary access, or search query 
        taxonID = row["taxonID"]
        if taxonID in all_taxa:
            Q, image, definition, label =  all_taxa[taxonID]["Q"], all_taxa[taxonID]["image"], all_taxa[taxonID]["Def"], all_taxa[taxonID]["Label"]
        else:
            Q, image, definition, label = taxa(scientificName, taxonID, parent_Q)
            all_taxa[taxonID] = {}
            all_taxa[taxonID]["Q"] = Q
            all_taxa[taxonID]["Label"] = label
            all_taxa[taxonID]["Def"] = definition
            all_taxa[taxonID]["image"] = image
            all_taxa[taxonID]["WikiData"] = True

        full_name = "kgo:taxonName \t\""  + scientificName + "\"@en ; \n\t"
        full_ID = "boltz:" + Q + " a kgo:Taxon ; \n\t" #Q-ID
        full_rank = "kgo:taxonRank\tboltz:" + ranks[row['taxonRank']] + " ; \n\t" #rank
        full_image = "kgo:taxonImage\t<" + image + "> ; \n\t"
        full_definition = "skos:definition\t\"\"\"" + definition + "\"\"\"@en ;\n\t" #definition
        full_label = "skos:prefLabel\t\"" + label + "\"@en .\n\n"    #preflabel – common name

        d =  full_ID + full_parent_Q + full_name + full_rank + full_image + full_definition + full_label 
        outfile.write(d)
    outfile.write("\n")

print(to_confirm)
outfile.close()
