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

# IMPORTED DATA 
# Q-values for ranks
ranks = {"kingdom": "Q36732", "subkingdom": "Q2752679", "infrakingdom": "Q3150876", "superphylum":"Q3978005", "phylum": "Q38348", "subphylum": "Q1153785", "infraphylum": "Q2361851", "superclass": "Q3504061",  "class": "Q37517", "subclass": "Q5867051", "infraclass": "Q2007442","superorder":"Q5868144", "order" :"Q36602", "suborder": "Q5867959",  "infraorder": "Q2889003", "superfamily" : "Q2136103", "family": "Q35409", "subfamily": "Q164280", "tribe":"Q227936","subtribe": "Q3965313", "genus": "Q34740", "subgenus":"Q3238261", "species": "Q7432", "subspecies": "Q68947"}

def run_query(q_value):
    query = "SELECT DISTINCT * WHERE { \
    wd:" + q_value + "\trdfs:label ?label; \
                schema:description ?itemdesc . \
    FILTER (langMatches( lang(?label), \"en\" ) )  \
    FILTER(LANG(?itemdesc) = \"en\") \
    SERVICE wikibase:label { bd:serviceParam wikibase:language \"en\". } \
    }"
    results = get_results(endpoint_url, query)
    result = results["results"]["bindings"][0]
    print(result)
    return result

outfile = open('RANKS/rank-triples.ttl', 'w')

# Need data structure that is able to access previous element. Linked list LOL?
for q_val in ranks.values():
    res = run_query(q_val)
    description = res["itemdesc"]["value"].capitalize()
    label = res["label"]["value"].capitalize()
    triple = "boltz:" + q_val + " a kgo:taxonRank ;\n\
    rdfs:label\t\"" + label + "\"@en ;\n\
    skos:definition\t\"" + description + "\"@en .\n\n"
    outfile.write(triple)

outfile.close()