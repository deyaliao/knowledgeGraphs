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
added_taxa =  {
    1157319: {"Q": "Q3427090", "Def": "Genus of insects", "Label": "Cnephasia", "image": "", "WikiData": True},
    729890: {"Q": "Q27636553", "Def": "Subspecies of bird", "Label": "Molothrus oryzivorus impacifus", "image": "", "WikiData": True },
    949898: {"Q": "Q500000000", "Def": "Subspecies of reptile", "Label": "Psammobates tentorius tentorius", "image": "", "WikiData": False},
    1084534: {"Q": "Q500000001", "Def": "Subspecies of reptile", "Label": "Telescopus dhara somalicus", "image": "", "WikiData": False},
    1084130: {"Q": "Q500000002", "Def": "Subspecies of reptile", "Label": "Duberria lutrix atriventris",  "image": "","WikiData": False},
    1084132: {"Q": "Q500000003", "Def": "Subspecies of reptile", "Label": "Duberria lutrix lutrix",  "image": "","WikiData": False},
    1157483: {"Q": "Q500000004", "Def": "Subspecies of mammal", "Label": "Eptesicus serotinus mirza",  "image": "", "WikiData": False}
}

# TAXA that we already inserted: gets rid of repeats
used_taxa = {}

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
# def run_q2(animal):
#     query2 = "SELECT ?item ?image ?itemLabel ?itemDescription  \
#         WHERE \
#             {?item skos:altLabel \"" + animal + "\"@en . \
#                  OPTIONAL{?item wdt:P18 ?image} . \
#             SERVICE wikibase:label \
#             {bd:serviceParam wikibase:language \"en\" . } \
#         }"
#     results = get_results(endpoint_url, query2)
#     print('result1:')
#     print(results)
#     return results

# use of regex – three letter difference maximum
def run_q3(animal, parent):
    n = 0
    while n < 3:
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
def taxa(animal, parent):
    results1 = run_q1(animal)
    if valid_search(results1): #way to check if search yields results
        return extract(results1)
        
    if parent != "":
        results2 = run_q3(animal, parent)
        if valid_search(results2):
            return extract(results2)

    # foregeo running query 2: just not worth the time it takes to run
    # else:
    #     to_confirm[ID] = animal
    #     results3 = run_q3(animal, parent)
    #     if valid_search(results3):
    #         return extract(results3)

    return "", "", "", ""
    

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


# Get reptile type species:
reptile_ts = {'Contomastix': 'Contomastix vittata', 'Aporarchus': 'Amphisbaena prunicolor', 'Aurivela': 'Aurivela longicauda', 'Coggeria': 'Coggeria naufragus', 'Acratosaura': 'Acratosaura mentalis', 'Colopus': 'Colopus wahlbergii', 'Cophosaurus': 'Cophosaurus texanus', 'Cophoscincopus': 'Cophoscincopus simulans', 'Corytophanes': 'Corytophanes cristatus', 'Cryptactites': 'Cryptactites peringueyi', 'Cryptoblepharus': 'Cryptoblepharus poecilopleurus', 'Cryptoscincus': 'Paracontias minimus', 'Ctenotus': 'Ctenotus taeniolatus', 'Cyclodina': 'Oligosoma aeneum', 'Siwaligecko': 'Cyrtopodion battalense', 'Davewakeum': 'Brachymeles miriamae', 'Lucasium': 'Lucasium damaeum', 'Diplodactylus': 'Diplodactylus vittatus', 'Diploglossus': 'Diploglossus fasciatus', 'Diplometopon': 'Diplometopon zarudnyi', 'Dogania': 'Dogania subplana', 'Ebenavia': 'Ebenavia inunguis', 'Lissolepis': 'Lissolepis luctuosa', 'Bellatorias': 'Bellatorias major', 'Liopholis': 'Liopholis whitii', 'Elgaria': 'Elgaria multicarinata', 'Elseya': 'Elseya dentata', 'Elusor': 'Elusor macrurus', 'Emydura': 'Emydura macquarii', 'Eremiascincus': 'Eremiascincus richardsonii', 'Eugongylus': 'Eugongylus rufescens', 'Eumeces': 'Eumeces schneideri', 'Eurylepis': 'Eurylepis taeniolata', 'Gambelia': 'Gambelia wislizenii', 'Geomyersia': 'Geomyersia glabra', 'Glaphyromorphus': 'Glaphyromorphus punctulatus', 'Goggia,': 'Goggia lineata', 'Haackgreerius': 'Haackgreerius miopus', 'Haemodracon': 'Haemodracon riebeckii', 'Harpesaurus': 'Harpesaurus tricinctus', 'Homopus': 'Homopus areolatus', 'Iguana': 'Iguana iguana', 'Lacerta': 'Lacerta agilis', 'Atlantolacerta': 'Atlantolacerta andreanskyi', 'Archaeolacerta': 'Archaeolacerta bedriagae', 'Apathya': 'Apathya cappadocica', 'Anatololacerta': 'Anatololacerta danfordi', 'Hellenolacerta': 'Hellenolacerta graeca', 'Phoenicolacerta': 'Phoenicolacerta laevis', 'Iberolacerta': 'Iberolacerta monticola', 'Dinarolacerta': 'Dinarolacerta mosorensis', 'Dalmatolacerta': 'Dalmatolacerta oxycephala', 'Parvilacerta': 'Parvilacerta parva', 'Lacertoides': 'Lacertoides pardalis', 'Lampropholis': 'Lampropholis guichenoti', 'Lankascincus': 'Lankascincus fallax', 'Leiolopisma': 'Leiolopisma telfairii', 'Leiosaurus': 'Leiosaurus bellii', 'Wondjinia': 'Lerista apoda', 'Gaia': 'Lerista bipes', 'Marrunisauria': 'Lerista borealis', 'Krishna': 'Lerista fragilis', 'Spectrascincus': 'Lerista ingrami', 'Aphroditia': 'Lerista macropisthopus', 'Lokisaurus': 'Lerista muelleri', 'Goldneyia': 'Lerista planiventralis', 'Cybelia': 'Lerista terdigitata', 'Alcisius': 'Lerista vermicularis', 'Lioscincus': 'Lioscincus steindachneri', 'Lipinia': 'Lipinia pulchella', 'Lygisaurus': 'Lygisaurus foliorum', 'Vanzoia': 'Lygodactylus klugei', 'Lygosoma': 'Lygosoma quadrupes', 'Varzea': 'Varzea bistriata', 'Panopa': 'Panopa croizati', 'Manciola': 'Manciola guaporicola', 'Eutropis': 'Eutropis multifasciata', 'Exila': 'Exila nigropalmata', 'Marisora': 'Marisora unimarginata', 'Macroscincus': 'Chioninia coctei', 'Celatiscincus': 'Celatiscincus euryotis', 'Marmorosphax': 'Marmorosphax tricolor', 'Matoatoa': 'Matoatoa brevipes', 'Menetia': 'Menetia greyii', 'Mesobaena': 'Mesobaena huebneri', 'Mesoscincus': 'Mesoscincus schwartzei', 'Micrablepharus': 'Micrablepharus maximiliani', 'Lepidothyris': 'Lepidothyris fernandi', 'Monopeltis': 'Monopeltis capensis', 'Morethia': 'Morethia lineoocellata', 'Morunasaurus': 'Morunasaurus groi', 'Naultinus': 'Naultinus elegans', 'Neusticurus': 'Neusticurus bicarinatus', 'Niveoscincus': 'Niveoscincus greeni', 'Notoscincus': 'Notoscincus ornatus', 'Oligosoma': 'Oligosoma zelandicum', 'Ophiodes': 'Ophiodes striatus', 'Ophisaurus': 'Ophisaurus ventralis', 'Pachycalamus': 'Pachycalamus brevis', '': 'Elasmodactylus tuberculosus', 'Palmatogecko': 'Pachydactylus rangei', 'Panaspis': 'Panaspis cabindae', 'Paracontias': 'Paracontias brocchii', 'Phoboscincus': 'Phoboscincus bocourti', 'Mesoclemmys': 'Mesoclemmys gibba', 'Batrachemys': 'Mesoclemmys nasuta', 'Rhinemys': 'Rhinemys rufipes', 'Bufocephala': 'Mesoclemmys vanderhaegei', 'Teira': 'Teira dugesii', 'Prasinohaema': 'Prasinohaema flavipes', 'Proablepharus': 'Proablepharus reginae', 'Proctoporus': 'Proctoporus pachyurus', 'Riama': 'Riama unicolor', 'Pseudoacontias': 'Pseudoacontias madagascariensis', 'Pseudopus': 'Pseudopus apodus', 'Ptychoglossus': 'Ptychoglossus bilineatus', 'Pygomeles': 'Pygomeles braconnieri', 'Mniarogekko': 'Mniarogekko chahoua', 'Correlophus': 'Correlophus ciliatus', 'Rieppeleon': 'Rieppeleon kerstenii', 'Rhampholeon': 'Rhampholeon spectrum', 'Rhineura': 'Rhineura floridana', 'Saiphos': 'Saiphos equalis', 'Saltuarius': 'Saltuarius cornutus', 'Orraya': 'Orraya occultus', 'Kaestlea': 'Kaestlea bilineata', 'Scincopus': 'Scincopus fasciatus', 'Scincus': 'Scincus albifasciatus', 'Sigaloseps': 'Sigaloseps deplanchei', 'Piersonus': 'Crotalus ravus', 'Stenocercus': 'Stenocercus roseiventris', 'Ophryoessoides': 'Stenocercus tricristatus', 'Takydromus': 'Takydromus sexlineatus', 'Altigekko': 'Altiphylax baturensis', 'Indogekko': 'Cyrtopodion indusoani', 'Chersina': 'Chersina angulata', 'Trogonophis': 'Trogonophis wiegmanni', 'Tropidolaemus': 'Tropidolaemus wagleri', 'Tropidophorus': 'Tropidophorus cocincinensis', 'Eurolophosaurus': 'Eurolophosaurus nanuzae', 'Tapinurus': 'Tropidurus semitaeniatus', 'Typhlosaurus': 'Typhlosaurus caecus', 'Saara': 'Orosaura nebulosylvestris', 'Zygaspis': 'Zygaspis quadrifrons', 'Tychismia': 'Lerista chordae', 'Timon': 'Timon lepidus'}
reptile_ts_keys = list(reptile_ts.keys())
reptile_ts_values = list(reptile_ts.values())

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

# FIRST PASS: For every file in directory, insert information into dictionary for future access
for i in range(0,len(file_list)):
    data = pd.read_table(file_list[i])
    df = pd.DataFrame(data)

    # For every taxa in file: 
    for index, row in df.iterrows():
        taxonID = row["taxonID"]
        parentID = row['parentNameUsageID']
        taxonAuthor = row['scientificNameAuthorship']
        taxonRank = row["taxonRank"]
        scientificName = row["scientificName"]

        # Only run valid taxa
        if taxonID in used_taxa or not row['taxonomicStatus'] == "valid" or taxonRank == "subspecies":
            continue
        
        # SET UP for future use
        used_taxa[taxonID] = {}

        #----- CLEAN DATA -----
        # Change scientificName, some have author appended onto it
        if not pd.isna(taxonAuthor) and taxonAuthor in scientificName:
            scientificName = scientificName.replace(" " + taxonAuthor, "")

        # if sub-genus, actual name is the one in the parenthesis. for example: Cicindela (Cicindelidia) means that Cicindelidia is the sub-genus in hand, where Cicindela is its parent. cannot directly use entire term in serach query, as that generates no results. also generate a more precise search query which uses the parentID: 
        if row['taxonRank'] == "subgenus":
            x = scientificName.split(" (")
            y = x[1].split(")")
            scientificName = y[0]
        
        # ----- RETRIEVE INFORMATION ----
        # Search parentTaxon information
        parent_id = 0
        if not pd.isna(parentID): 
            parent_id = int(parentID)
        used_taxa[taxonID]["parent_id"] = parent_id

        # If manually added info, retrieve through dictionary, else search query, add to used taxa
        # Obtain parent-Q value: used when running algorithm.
        parent_Q = ""
        parent_id = used_taxa[taxonID]["parent_id"]
        if parent_id in used_taxa:
            parent_Q = used_taxa[parent_id]["Q"]
        if taxonID in added_taxa:
            Q, image, definition, label = added_taxa[taxonID]["Q"], added_taxa[taxonID]["image"], added_taxa[taxonID]["Def"], added_taxa[taxonID]["Label"]
        else:
            Q, image, definition, label = taxa(scientificName, parent_Q)
        
        taxon = used_taxa[taxonID]
        taxon["name"] = scientificName
        taxon["Q"] = Q
        taxon["rank"] = taxonRank
        taxon["image"] = image
        taxon["definition"] = definition
        taxon["label"] = label
        
        # Type-species:
        # Check if the genus has a type species:
        type_species = ""
        if taxonRank == "genus" and scientificName in reptile_ts:
            type_species = reptile_ts[scientificName]
        used_taxa[taxonID]["type_species"] = type_species

        # Check if the SPECIES is the designated type species for its genus
        type_species_of = "" 
        if taxonRank == "species" and scientificName in reptile_ts_values:
            type_species_of = reptile_ts_keys[reptile_ts_values.index(scientificName)]
        used_taxa[taxonID]["type_species_of"] = type_species_of
        print("HELLO")
        print(used_taxa[taxonID])

# SECOND PASS
for taxon_id in list(used_taxa.keys()):
    taxon = used_taxa[taxon_id]
    print(taxon)
    full_Q = "boltz:" + taxon["Q"] + " a kgo:Taxon ; \n\t" #Q-ID
    full_name = "kgo:taxonName \t\""  + taxon["name"] + "\"@en ; \n\t"
    full_rank = "kgo:taxonRank\tboltz:" + ranks[taxon["rank"]] + " ; \n\t" #rank

    full_parent_Q = ""
    full_type_species = ""
    full_tso = ""

    parent_id = taxon["parent_id"]
    if parent_id != 0:
        parent_Q = used_taxa[parent_id]["Q"]
        full_parent_Q = "kgo:subTaxonOf\tboltz:" + parent_Q + " ; \n\t" 
    if taxon["type_species"] != "":
        full_type_species = "kgo:typeSpecies\t\"" + taxon["type_species"] + "\"@en ;\n\t" #type species
    if taxon["type_species_of"] != "":
        full_tso = "kgo:typeSpeciesOf\t\"" + taxon["type_species_of"] + "\"@en ;\n\t" #type species of

    full_image = "kgo:taxonImage\t<" + taxon["image"] + "> ; \n\t"
    full_definition = "skos:definition\t\"\"\"" + taxon["definition"] + "\"\"\"@en ;\n\t" #definition
    full_label = "skos:prefLabel\t\"" + taxon["label"] + "\"@en .\n\n"    #preflabel – common name

    d = full_Q + full_parent_Q + full_name + full_rank + full_type_species + full_tso + full_image + full_definition + full_label 

    outfile.write(d)

print(to_confirm)
outfile.close()
