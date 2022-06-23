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
    1157319: {"name": "Cnephasia", "Q": "Q3427090", "definition": "Genus of insects", "rank": "genus", "label": "Cnephasia", "image": ""},
    944067: {"name": "Lepilemur hubbardi", "Q": "Q1209803", "definition": "Species of mammal", "rank": "species", "label": "Lepilemur hubbardi", "image": "https://commons.wikimedia.org/wiki/File:Lepilemur_hubbardorum.jpg"},
    944084: {"name": "Avahi ramanantsoavani", "Q": "Q1210789", "definition": "Species of mammal", "rank": "species","label": "Ramanantsoavana's woolly lemur", "image": ""},
    944102: {"name": "Sciurocheirus gabonensis", "Q": "Q1202102", "definition": "Species of mammal", "rank": "species","label": "Gabon bushbaby", "image": ""},
    944136: {"name": "Mico chrysoleucos", "Q": "Q3427090", "definition": "Species of mammal", "rank": "species","label": "Mico chrysoleucos", "image": "https://commons.wikimedia.org/wiki/File:Mico_chrysoleucus_Kenny_Ross_1.jpg"},
    944137: {"name": "Mico saterei", "Q": "Q20890485", "definition": "Species of mammal", "rank": "species","label": "Mico saterei", "image": ""},
    573020: {"name": "Plecturocebus olallae", "Q": "Q737104", "definition": "Species of mammal","rank": "species", "label": "Ollala Brothers' titi", "image": "https://commons.wikimedia.org/wiki/File:M%C3%A2le_macaque_maure_(Macaca_maura).jpg"},
    1025115: {"name": "Plecturocebus urubambensis", "Q": "Q20721824", "definition": "Species of mammal", "rank": "species", "label": "Plecturocebus urubambensis", "image": ""},
    1025117: {"name": "Cnephasia", "Q": "Q3427090", "definition": "Species of mammal", "rank": "species", "label": "Cnephasia", "image": ""},
    1025124: {"name": "Plecturocebus miltoni", "Q": "Q19279592", "definition": "Species of mammal", "rank": "species", "label": "Plecturocebus miltoni", "image": ""},
    1025133: {"name": "Plecturocebus toppini", "Q": "Q20721823", "definition": "Species of mammal", "rank": "species", "label": "Plecturocebus toppini", "image": "https://commons.wikimedia.org/wiki/File:Callicebus_cupreus_Tambopata_Research_Center.jpg"},
    1025150: {"name": "Paragalago zanzibaricus", "Q": "Q104005586", "definition": "Species of mammal", "rank": "species", "label": "Paragalago zanzibarensis", "image": ""},
    1149093: {"name": "Chlorocebus dryas", "Q": "Q1075064", "definition": "Species of mammal", "rank": "species", "label": "Dryas monkey", "image": "https://commons.wikimedia.org/wiki/File:Chlorocebus_dryas_still-frame.png"},
    1147531: {"name": "Trachypithecus melamerus", "Q": "Q101543962", "definition": "Species of mammal", "rank": "species", "label": "Trachypithecus melamerus", "image": ""},
    944165: {"name": "Cebus versicolor", "Q": "Q500000005", "definition": "Species of mammal", "rank": "species", "label": "Cebus versicolor", "image": ""},
    944167: {"name": "Cebus aequatorialis", "Q": "Q500000006", "definition": "Species of mammal", "rank": "species", "label": "Cebus aequatorialis", "image": ""},
    944162: {"name": "Cebus brunneus", "Q": "Q500000007", "definition": "Species of mammal", "rank": "species", "label": "Cebus brunneus", "image": ""},
    208597: {"name": "Terrapene bauri", "Q": "Q500000008", "definition": "Species of reptile", "rank": "species", "label": "Common Box Turtle", "image": ""},
    1147510: {"name": "Sapajus cucullatus", "Q": "Q500000009", "definition": "Species of mammal", "rank": "species", "label": "Sapajus cucullatus", "image": ""},
}

used_taxa = {}
name_to_id = {}

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
        image_link = result['thumb']['value']
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
    query1 = "SELECT ?item ?image ?thumb ?itemLabel ?itemDescription  \
        WHERE \
            {?item wdt:P225 \"" + animal + "\" . \
             OPTIONAL{?item wdt:P18 ?image} . \
            SERVICE wikibase:label \
            {bd:serviceParam wikibase:language \"en\" . } \
            BIND(REPLACE(wikibase:decodeUri(STR(?image)), \"http://commons.wikimedia.org/wiki/Special:FilePath/\", \"\") as ?fileName) . \
            BIND(REPLACE(?fileName, \" \", \"_\") as ?safeFileName) \
            BIND(MD5(?safeFileName) as ?fileNameMD5) . \
            BIND(CONCAT(\"https://upload.wikimedia.org/wikipedia/commons/thumb/\", SUBSTR(?fileNameMD5, 1, 1), \"/\", SUBSTR(?fileNameMD5, 1, 2), \"/\", ?safeFileName, \"/650px-\", ?safeFileName) as ?thumb)} "
    results = get_results(endpoint_url, query1)
    print('result1:')
    print(results)
    return results
    
# use of alt label, sometimes the taxonomic name is the alias
# def run_q2(animal):
#     query2 = "SELECT ?item ?image ?itemLabel ?itemDescription  \
#         WHERE \
#             {?item skos:altlabel \"" + animal + "\"@en . \
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
        # might not be EXACT parentlabel but the PATH matches, intentional because some discrepancies between WikiData and ITIS parentTaxons
        query3 = "SELECT ?item ?image ?thumb ?itemLabel ?itemDescription WHERE \
            { \
            ?item wdt:P171* wd:" + parent + "; \
                   rdfs:label ?itemLabel. \
            OPTIONAL{?item wdt:P18 ?image} . \
            filter(regex(str(?itemLabel), \"" + new_animal + "\" )) \
            SERVICE wikibase:label  \
            {bd:serviceParam wikibase:language \"en\"  . } \
            BIND(REPLACE(wikibase:decodeUri(STR(?image)), \"http://commons.wikimedia.org/wiki/Special:FilePath/\", \"\") as ?fileName) . \
            BIND(REPLACE(?fileName, \" \", \"_\") as ?safeFileName)  \
            BIND(MD5(?safeFileName) as ?fileNameMD5) . \
            BIND(CONCAT(\"https://upload.wikimedia.org/wikipedia/commons/thumb/\", SUBSTR(?fileNameMD5, 1, 1), \"/\", SUBSTR(?fileNameMD5, 1, 2), \"/\", ?safeFileName, \"/650px-\", ?safeFileName) as ?thumb)} "
        results = get_results(endpoint_url, query3)
        # check if query yielded a valid result
        if valid_search(results):
            return results
        n += 1
    return results

# Get Q-value, definition, prelabel (use with triple style code)
# Try/except: get_results(endpoint_url, query) often times out randomly, so the except just makes sure the rest of the algorithm can run
def taxa(animal, parent):
    try:
        results1 = run_q1(animal)
    except:
        return "", "", "", ""
    if valid_search(results1): #way to check if search yields results
        return extract(results1)        
    if parent != "":
        try:
            results2 = run_q3(animal, parent)
        except:
            return "", "", "", ""
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
    query = " SELECT ?item ?taxonrank ?itemLabel ?taxonranklabel \
    WHERE \
    { \
        wd:Q530397 wdt:P171* ?item. \
        ?item wdt:P105 ?taxonrank. \
        ?item rdfs:label ?itemLabel filter (lang(?itemLabel) = \"en\"). \
        ?taxonrank rdfs:label ?taxonranklabel filter (lang(?taxonranklabel) = \"en\"). \
    }" 

    results = get_results(endpoint_url, query)
    print('results4:')

    for result in results["results"]["bindings"]:
        taxonrank = result['taxonranklabel']['value']
        item = result['itemLabel']['value']
        print(taxonrank, 'is', item)


# Get reptile type species:
reptile_ts = {'Ablepharus': 'Ablepharus pannonicus', 'Abronia': 'Abronia deppii', 'Acalyptophis': 'Hydrophis peronii', 'Acanthocercus': 'Acanthocercus cyanogaster', 'Acanthochelys': 'Acanthochelys spixii', 'Taenieremias': 'Acanthodactylus guineensis', 'Acanthophis': 'Acanthophis antarcticus', 'Acanthosaura': 'Acanthosaura armata', 'Achalinus': 'Achalinus spinalis', 'Microacontias': 'Acontias lineatus', 'Acontias': 'Acontias meleagris', 'Acontophiops': 'Acontias rieppeli', 'Acrochordus': 'Acrochordus javanicus', 'Acutotyphlops': 'Acutotyphlops kunuaensis', 'Adelophis': 'Adelophis copei', 'Adelphicos': 'Adelphicos quadrivirgatum', 'Adolfus': 'Adolfus africanus', 'Congolacerta': 'Congolacerta vauereselli', 'Aeluroglena': 'Aeluroglena cucullata', 'Aeluroscalabotes': 'Aeluroscalabotes felinus', 'Afroablepharus': 'Afroablepharus wahlbergi', 'Afroedura': 'Afroedura bogerti', 'Afrogecko': 'Afrogecko porphyreus', 'Ramigekko': 'Ramigekko swartbergensis', 'Afronatrix': 'Afronatrix anoscopus', 'Agama': 'Agama agama', 'Agamodon': 'Agamodon anguliceps', 'Rhinogecko': 'Rhinogecko misonnei', 'Agamura': 'Agamura persica', 'Agkistorodon': 'Agkistrodon contortrix', 'Testudo': 'Testudo horsfieldii', 'Ahaetulla': 'Ahaetulla mycterizans', 'Ailuronyx': 'Ailuronyx seychellensis', 'Aipysurus': 'Aipysurus laevis', 'Algyroides': 'Algyroides moreoticus', 'Alligator': 'Alligator mississippiensis', 'Alluaudina': 'Alluaudina bellyi', 'Alopoglossus': 'Alopoglossus copii', 'Haitiophis': 'Haitiophis anomalus', 'Alsophis': 'Alsophis antillensis', 'Ocyophis': 'Hypsirhynchus ater', 'Cubophis': 'Cubophis cantherigerus', 'Lygophis': 'Lygophis lineatus', 'Borikenophis': 'Borikenophis portoricensis', 'Alsophylax': 'Alsophylax pipiens', 'Amapasaurus': 'Amapasaurus tetradactylus', 'Amastridium': 'Amastridium veliferum', 'Amblyodipsas': 'Amblyodipsas microphthalma', 'Amblyrhynchus': 'Amblyrhynchus cristatus', 'Ameiva': 'Ameiva ameiva', 'MedopheosHARVEY': 'Medopheos edracanthus', 'Holcosus': 'Holcosus septemlineatus', 'Contomastix': 'Contomastix vittata', 'Amphibolurus': 'Amphibolurus muricatus', 'Paranatrix': 'Hebius modestum', 'Herpetoreas': 'Herpetoreas sieboldii', 'Amphiesma': 'Amphiesma stolatum', 'Hebius': 'Hebius vibakari', 'Amphiesmoides': 'Amphiesmoides ornaticeps', 'Amphiglossus': 'Amphiglossus astrolabi', 'Cadea': 'Cadea blanoides', 'Amphisbaena': 'Amphisbaena fuliginosa', 'Amplorhinus': 'Amplorhinus multimaculatus', 'Xestosaurus': 'Anadia bogotensis', 'Argalia': 'Anadia marmorata', 'Anadia': 'Anadia ocellata', 'Ancylocranium': 'Ancylocranium somalicum', 'Anelytropsis': 'Anelytropsis papillosus', 'Angolosaurus': 'Gerrhosaurus skoogi', 'Anguis': 'Anguis fragilis', 'Anilius': 'Anilius scytale', 'Anisolepis': 'Anisolepis undulatus', 'Anniella': 'Anniella pulchra', 'Audantia': 'Anolis armouri', 'Norops': 'Anolis auratus', 'Eupristis': 'Anolis equestris', 'Xiphocercus': 'Anolis valencienni', 'Anomochilus': 'Anomochilus weberi', 'Anops': 'Amphisbaena kingii', 'Rhachisaurus': 'Rhachisaurus brachylepis', 'Anotosaura': 'Anotosaura collaris', 'Caraiba': 'Caraiba andreae', 'Antillophis': 'Hypsirhynchus parvifrons', 'Aphaniotis': 'Aphaniotis fusca', 'Aprasia': 'Aprasia pulchella', 'Abilaena': 'Aprasia rostrata', 'Apterygodon': 'Dasia vittata', 'Argyrogena': 'Argyrogena fasciolata', 'Aristelliger': 'Aristelliger lar', 'Arizona': 'Arizona elegans', 'Schwartzophis': 'Hypsirhynchus callilaemus', 'Magliophis': 'Magliophis exiguum', 'Arrhyton': 'Arrhyton taeniatum', 'Arthrosaura': 'Arthrosaura reticulata', 'Asaccus': 'Asaccus elisae', 'Aspidelaps': 'Aspidelaps lubricus', 'Aspidites': 'Aspidites melanocephalus', 'Aspidomorphus': 'Aspidomorphus muelleri', 'Aspidura': 'Aspidura brachyorrhos', 'Astrotia': 'Hydrophis stokesii', 'Ateuchosaurus': 'Ateuchosaurus chinensis', 'Atheris': 'Atheris chlorechis', 'Atractaspis': 'Atractaspis bibronii', 'Atractus': 'Atractus trilineatus', 'Atretium': 'Atretium schistosum', 'Atropoides': 'Atropoides picadoi', 'Aulura': 'Amphisbaena anomala', 'Vhembelacerta': 'Vhembelacerta rupicola', 'Austrelaps': 'Austrelaps superbus', 'Azemiops': 'Azemiops feae', 'Bachia': 'Bachia dorbignyi', 'Baikia': 'Baikia africana', 'Balanophis': 'Balanophis ceylonensis', 'Barisia': 'Barisia imbricata', 'Bartleia': 'Techmarscincus jigurru', 'Basiliscus': 'Basiliscus basiliscus', 'Eulepis': 'Bassiana duperreyi', 'Batagur': 'Batagur baska', 'Bavayia': 'Bavayia cyclura', 'Dierogekko': 'Dierogekko validiclavis', 'Bipes': 'Bipes canaliculatus', 'Bitia': 'Bitia hydroides', 'Keniabitis': 'Bitis worthingtoni', 'Blaesodactylus': 'Blaesodactylus sakalava', 'Blanus': 'Blanus cinereus', 'Blythia': 'Blythia reticulata', 'Boa': 'Boa constrictor', 'Acrantophis': 'Acrantophis dumerili', 'Sanzinia': 'Sanzinia madagascariensis', 'Bogertia': 'Phyllopezus lutzae', 'Boiga': 'Boiga irregularis', 'Bolyeria': 'Bolyeria multocarinata', 'Bothriopsis': 'Bothrops taeniata', 'Bothrochilus': 'Bothrochilus boa', 'Bothrolycus': 'Bothrolycus ater', 'Rhinocerophis': 'Bothrops ammodytoides', 'Bothrocophias': 'Bothrocophias hyoprora', 'Bothrops': 'Bothrops lanceolatus', 'Bothropoides': 'Bothrops neuwiedi', 'Boulengerina': 'Naja annulata', 'Brachylophus': 'Brachylophus fasciatus', 'Brachymeles': 'Brachymeles bonitae', 'Brachyophidium': 'Brachyophidium rhodogaster', 'Brachyophis': 'Brachyophis revoili', 'Brachyorrhos': 'Brachyorrhos albus', 'Brachysaura': 'Brachysaura minor', 'Kinyongia': 'Kinyongia fischeri', 'Nadzikambia': 'Nadzikambia mlanjensis', 'Bradypodion': 'Bradypodion pumilum', 'Bronchocela': 'Bronchocela cristatella', 'Bronia': 'Amphisbaena brasiliana', 'Palleon': 'Palleon lolontany', 'Brookesia': 'Brookesia superciliaris', 'Bungarus': 'Bungarus fasciatus', 'Bunopus': 'Bunopus tuberculatus', 'Cacophis': 'Cacophis krefftii', 'Caiman': 'Caiman latirostris', 'Calabaria': 'Calabaria reinhardtii', 'Calamaria': 'Calamaria lumbricoidea', 'Calamodontophis': 'Calamodontophis paucidens', 'Calliophis': 'Calliophis gracilis', 'Sinomicrurus': 'Sinomicrurus macclellandi', 'Callisaurus': 'Callisaurus draconoides', 'Callopistes': 'Callopistes maculatus', 'Calloselasma': 'Calloselasma rhodostoma', 'Calotes': 'Calotes calotes', 'Hypsicalotes': 'Hypsicalotes kinabaluensis', 'Complicitus': 'Complicitus nigrigularis', 'Calumma': 'Calumma cucullatum', 'Archaius': 'Archaius tigris', 'Calyptommatus': 'Calyptommatus sinebrachiatus', 'Candoia': 'Candoia carinata', 'Djokoiskandarus': 'Djokoiskandarus annulata', 'Cantoria': 'Cantoria violacea', 'Caretta': 'Caretta caretta', 'Carettochelys': 'Carettochelys insculpta', 'Carinatogecko': 'Mediodactylus aspratilis', 'Liburnascincus': 'Liburnascincus coensis', 'Carlia': 'Carlia munda', 'Carphodactylus': 'Carphodactylus laevis', 'Casarea': 'Casarea dussumieri', 'Causus': 'Causus rhombeatus', 'Celestus': 'Celestus stenurus', 'Ceratophora': 'Ceratophora stoddartii', 'Cerberus': 'Cerberus rynchops', 'Cercolophia': 'Amphisbaena roberti', 'Cercosaura': 'Cercosaura ocellata', 'Cerrophidion': 'Cerrophidion godmani', 'Chalcides': 'Chalcides chalcides', 'Chamaeleo': 'Chamaeleo chamaeleon', 'Trioceros': 'Trioceros oweni', 'Charina': 'Charina bottae', 'Lichanura': 'Lichanura trivirgata', 'Chelodina': 'Chelodina longicollis', 'Chelosania': 'Chelosania brunnea', 'Chelus': 'Chelus fimbriata', 'Chelydra': 'Chelydra serpentina', 'Chersodromus': 'Chersodromus liebmanni', 'Chilorhinophis': 'Chilorhinophis butleri', 'Chirindia': 'Chirindia swynnertoni', 'Chironius': 'Chironius carinatus', 'Chlamydosaurus': 'Chlamydosaurus kingii', 'Chondrodactylus': 'Chondrodactylus angulifer', 'Ridegekko': 'Christinus guentheri', 'Christinus': 'Christinus marmoratus', 'Chrysemys': 'Chrysemys picta', '': 'Alinea pergravis', 'Paraphimophis': 'Paraphimophis rusticus', 'Clemmys': 'Clemmys guttata', 'Glyptemys': 'Glyptemys insculpta', 'Actinemys': 'Actinemys marmorata', 'Clonophis': 'Clonophis kirtlandii', 'Cnemaspis': 'Cnemaspis boulengerii', 'Ancylodactylus': 'Cnemaspis spinicollis', 'Aurivela': 'Aurivela longicauda', 'Cnemidophorus': 'Cnemidophorus murinus', 'Ameivula': 'Ameivula ocellifera', 'Aspidoscelis': 'Aspidoscelis sexlineata', 'Coggeria': 'Coggeria naufragus', 'Chatogekko': 'Chatogekko amazonicus', 'Coleodactylus': 'Coleodactylus meridionalis', 'Coleonyx': 'Coleonyx elegans', 'Colobodactylus': 'Colobodactylus taunayi', 'Acratosaura': 'Acratosaura mentalis', 'Colobosaura': 'Colobosaura modesta', 'Colobosauroides': 'Colobosauroides cearensis', 'Coloptychon': 'Coloptychon rhombifer', 'Colopus': 'Colopus wahlbergii', 'Dolichophis': 'Dolichophis caspius', 'Coluber': 'Drymarchon corais', 'Bamanophis': 'Bamanophis dorri', 'Hemorrhois': 'Hemorrhois hippocrepis', 'Orientocoluber': 'Orientocoluber spinalis', 'Platyceps': 'Platyceps ventromaculatus', 'Hierophis': 'Hierophis viridiflavus', 'Coniophanes': 'Coniophanes fissidens', 'Conolophus': 'Conolophus subcristatus', 'Conophis': 'Conophis vittatus', 'Conopsis': 'Conopsis nasus', 'Cophosaurus': 'Cophosaurus texanus', 'Cophoscincopus': 'Cophoscincopus simulans', 'Cophotis': 'Cophotis ceylanica', 'Corallus': 'Corallus hortulanus', 'Ouroborus': 'Ouroborus cataphractus', 'Ninurta': 'Ninurta coeruleopunctatus', 'Cordylus': 'Cordylus cordylus', 'Smaug': 'Smaug giganteus', 'Karusasaurus': 'Karusasaurus polyzonus', 'Namazonurus': 'Namazonurus pustulatus', 'Coronella': 'Coronella austriaca', 'Coryphophylax': 'Coryphophylax subcristatus', 'Corytophanes': 'Corytophanes cristatus', 'Crenadactylus': 'Crenadactylus ocellatus', 'Crocodilurus': 'Crocodilurus amazonicus', 'Mecistops': 'Mecistops cataphractus', 'Crossobamon': 'Crossobamon eversmanni', 'Crotalus': 'Crotalus horridus', 'Crotaphopeltis': 'Crotaphopeltis hotamboeia', 'Crotaphytus': 'Crotaphytus collaris', 'Cryptactites': 'Cryptactites peringueyi', 'Cryptagama': 'Cryptagama aurita', 'Cryptoblepharus': 'Cryptoblepharus poecilopleurus', 'Ctenophorus': 'Ctenophorus decresii', 'Ctenosaura': 'Ctenosaura acanthura', 'Ctenotus': 'Ctenotus taeniolatus', 'Cuora': 'Cuora amboinensis', 'Cyclemys': 'Cyclemys dentata', 'Cyclophiops': 'Cyclophiops doriae', 'Entechinus': 'Cyclophiops major', 'Cyclotyphlops': 'Cyclotyphlops deharvengi', 'Cyclura': 'Cyclura carinata', 'Cylindrophis': 'Cylindrophis ruffus', 'Placogaster': 'Cynisca feae', 'Cynisca': 'Cynisca leucura', 'Ophioproctes': 'Cynisca liberiensis', 'Siwaligecko': 'Cyrtopodion battalense', 'Cyrtodactylus': 'Cyrtodactylus pulchellus', 'Cyrtopodion': 'Cyrtopodion scabrum', 'Daboia': 'Daboia russelii', 'Dalophia': 'Monopeltis welwitschii', 'Darlingtonia': 'Ialtris haetianus', 'Dasia': 'Dasia olivacea', 'Davewakeum': 'Brachymeles miriamae', 'Deinagkistrodon': 'Deinagkistrodon acutus', 'Deirochelys': 'Deirochelys reticularia', 'Dendragama': 'Dendragama boulengeri', 'Dendrelaphis': 'Dendrelaphis caudolineatus', 'Dermatemys': 'Dermatemys mawii', 'Dermochelys': 'Dermochelys coriacea', 'Diaphorolepis': 'Diaphorolepis wagneri', 'Dibamus': 'Dibamus novaeguineae', 'Dicrodon': 'Dicrodon guttulatum', 'Dinodon': 'Lycodon rufozonatus', 'Lucasium': 'Lucasium damaeum', 'Eremiastrophurus': 'Strophurus elderi', 'Strophurus': 'Strophurus strophurus', 'Oedurella': 'Strophurus taeniatus', 'Diplodactylus': 'Diplodactylus vittatus', 'Diploglossus': 'Diploglossus fasciatus', 'Diplometopon': 'Diplometopon zarudnyi', 'Diporiphora': 'Diporiphora bilineata', 'Dipsadoboa': 'Dipsadoboa unicolor', 'Dipsas': 'Dipsas indica', 'Tropidodipsas': 'Tropidodipsas fasciata', 'Aldabrachelys': 'Aldabrachelys gigantea', 'Dipsosaurus': 'Dipsosaurus dorsalis', 'Disteira': 'Hydrophis major', 'Ditypophis': 'Ditypophis vivax', 'Dixonius,': 'Dixonius siamensis', 'Dogania': 'Dogania subplana', 'Dracaena': 'Dracaena guianensis', 'Draco': 'Draco volans', 'Dromophis': 'Psammophis praeornatus', 'Drymobius': 'Drymobius margaritiferus', 'Drymoluber': 'Drymoluber dichrous', 'Duberria': 'Duberria lutrix', 'Ebenavia': 'Ebenavia inunguis', 'Echinosaura': 'Echinosaura horrida', 'Echiopsis': 'Echiopsis curta', 'Echis': 'Echis carinatus', 'Ecpleopus': 'Ecpleopus gaudichaudii', 'Egernia': 'Egernia cunninghami', 'Lissolepis': 'Lissolepis luctuosa', 'Bellatorias': 'Bellatorias major', 'Liopholis': 'Liopholis whitii', 'Pediophis': 'Eirenis coronella', 'Sub': 'Eirenis decemlineatus', 'Eirenis': 'Eirenis modestus', 'Euprepiophis': 'Euprepiophis conspicillata', 'Pantherophis': 'Pantherophis guttatus', 'Zamenis': 'Zamenis longissimus', 'Orthriophis': 'Orthriophis moellendorffi', 'Oreocryptophis': 'Oreocryptophis porphyraceus', 'Coelognathus': 'Coelognathus radiatus', 'Rhinechis': 'Rhinechis scalaris', 'Mintonius': 'Pantherophis vulpinus', 'Elapsoidea': 'Elapsoidea guentherii', 'Elgaria': 'Elgaria multicarinata', 'Elseya': 'Elseya dentata', 'Myuchelys': 'Myuchelys latisternum', 'Elusor': 'Elusor macrurus', 'Emoia': 'Emoia atrocostata', 'Emydocephalus': 'Emydocephalus annulatus', 'Emydura': 'Emydura macquarii', 'Enhydrina': 'Hydrophis schistosus', 'Sumatranus': 'Sumatranus albomaculata', 'Miralia': 'Miralia alternans', 'Subsessor': 'Subsessor bocourti', 'Homalophis': 'Homalophis doriae', 'Dieurostus': 'Dieurostus dussumieri', 'Hypsirhina': 'Enhydris enhydris', 'Raclitia': 'Raclitia indica', 'Gyiophis': 'Gyiophis maculosa', 'Kualatahan': 'Kualatahan pahangensis', 'Mintonophis': 'Mintonophis pakistanicus', 'Enhydris': 'Hypsiscopus plumbea', 'Pseudoferania': 'Pseudoferania polylepis', 'Phytolopsis': 'Phytolopsis punctata', 'Enuliophis': 'Enuliophis sclateri', 'Enyalioides': 'Enyalioides heterolepis', 'Enyalius': 'Enyalius catenatus', 'Epicrates': 'Epicrates cenchria', 'Chilabothrus': 'Chilabothrus inornatus', 'Eremias': 'Eremias arguta', 'Eremiascincus': 'Eremiascincus richardsonii', 'Eristicophis': 'Eristicophis macmahoni', 'Erpeton': 'Erpeton tentaculatum', 'Erythrolamprus': 'Erythrolamprus aesculapii', 'Eryx': 'Eryx jaculus', 'Eugongylus': 'Eugongylus rufescens', 'Costinisauria': 'Eulamprus kosciuskoi', 'Tumbunascincus': 'Tumbunascincus luteilateralis', 'Silvascincus': 'Silvascincus murrayi', 'Eulamprus': 'Eulamprus quoyii', 'Concinnia': 'Concinnia tenuis', 'FITZINGER': 'Euleptes europaea', 'Eumeces': 'Eumeces schneideri', 'Eumecia': 'Eumecia anchietae', 'Eunectes': 'Eunectes murinus', 'Eurydactylodes': 'Eurydactylodes vieillardi', 'Eurylepis': 'Eurylepis taeniolata', 'Euspondylus': 'Euspondylus maculatus', 'Elapotinus': 'Elapotinus picteti', 'Exiliboa': 'Exiliboa placata', 'Farancia': 'Farancia abacura', 'Fojia': 'Fojia bumui', 'Fordonia': 'Fordonia leucobalia', 'Furcifer': 'Furcifer bifidus', 'Furina': 'Furina diadema', 'Gambelia': 'Gambelia wislizenii', 'Gastropyxis': 'Hapsidophrys smaragdina', 'Geckoella': 'Cyrtodactylus triedrus', 'Geckolepis': 'Geckolepis typica', 'Phyriadoria': 'Gehyra australis', 'Gehyra': 'Gehyra oceanica', 'Gekko': 'Gekko gecko', 'Geocalamus': 'Geocalamus modestus', 'Chelonoidis': 'Chelonoidis carbonaria', 'Astrochelys': 'Astrochelys radiata', 'Geoclemys': 'Geoclemys hamiltonii', 'Geoemyda': 'Geoemyda spengleri', 'Geomyersia': 'Geomyersia glabra', 'Geophis': 'Geophis chalybeus', 'Gerarda': 'Gerarda prevostiana', 'Gerrhonotus': 'Gerrhonotus liocephalus', 'Gerrhosaurus': 'Gerrhosaurus flavigularis', 'Broadleysaurus': 'Broadleysaurus major', 'Matobosaurus': 'Matobosaurus validus', 'Mawsoniascincus': 'Eremiascincus isolepis', 'Glaphyromorphus': 'Glaphyromorphus punctulatus', 'Gloydius': 'Gloydius halys', 'Goggia,': 'Goggia lineata', 'Gymnodactylus': 'Gymnodactylus geckoides', 'Gongylomorphus': 'Gongylomorphus bojerii', 'Gongylophis': 'Eryx conicus', 'Opacitascincus': 'Glaphyromorphus crassicaudus', 'Gonionotophis': 'Gonionotophis capensis', 'Gonocephalus': 'Gonocephalus chamaeleontinus', 'Gonyophis': 'Gonyosoma margaritatus', 'Gonyosoma': 'Gonyosoma oxycephalum', 'Graptemys': 'Graptemys geographica', 'Gymnophthalmus': 'Gymnophthalmus lineatus', 'Haackgreerius': 'Haackgreerius miopus', 'Haemodracon': 'Haemodracon riebeckii', 'Hapsidophrys': 'Hapsidophrys lineatus', 'Hardella': 'Hardella thurjii', 'Harpesaurus': 'Harpesaurus tricinctus', 'Helicops': 'Helicops carinicaudus', 'Lampreremias': 'Heliobolus nitidus', 'Helminthophis': 'Helminthophis frontalis', 'Heloderma': 'Heloderma horridum', 'Hemidactylus': 'Hemidactylus mabouia', 'Arenicolascincus': 'Hemiergis millewae', 'Hemiphyllodactylus': 'Hemiphyllodactylus typus', 'Hemitheconyx': 'Hemitheconyx caudicinctus', 'Heosemys': 'Heosemys spinosa', 'Heterodactylus': 'Heterodactylus imbricatus', 'Heteronotia': 'Heteronotia binoei', 'Heurnia': 'Heurnia ventromaculata', 'Holodactylus': 'Holodactylus africanus', 'Homalopsis': 'Homalopsis buccata', 'Homopus': 'Homopus areolatus', 'Hoplocercus': 'Hoplocercus spinosus', 'Hoplodactylus': 'Hoplodactylus duvaucelii', 'Mokopirirakau': 'Mokopirirakau granulatus', 'Woodworthia': 'Woodworthia maculatus', 'Dactylocnemis': 'Dactylocnemis pacificus', 'Tukutuku': 'Tukutuku rakiurae', 'Toropuku': 'Toropuku stephensi', 'Hydrelaps': 'Hydrelaps darwiniensis', 'Polyodontognathus': 'Hydrophis caerulescens', 'Hydrophis': 'Hydrophis fasciatus', 'Chitulia': 'Hydrophis inornatus', 'Hydrosaurus': 'Hydrosaurus amboinensis', 'Hypnale': 'Hypnale hypnale', 'Hypoptophis': 'Hypoptophis wilsonii', 'Hypsilurus': 'Hypsilurus godeffroyi', 'Hypsirhynchus': 'Hypsirhynchus ferox', 'Ialtris': 'Ialtris dorsalis', 'Iguana': 'Iguana iguana', 'Imantodes': 'Imantodes cenchoa', 'Asthenodipsas': 'Asthenodipsas malaccanus', 'Iphisa': 'Iphisa elegans', 'Janetaescincus': 'Janetaescincus braueri', 'Japalura': 'Japalura variegata', 'Kentropyx': 'Kentropyx calcarata', 'Kerilia': 'Hydrophis jerdonii', 'Kinosternon': 'Kinosternon scorpioides', 'Lacerta': 'Lacerta agilis', 'Atlantolacerta': 'Atlantolacerta andreanskyi', 'Archaeolacerta': 'Archaeolacerta bedriagae', 'Iranolacerta': 'Iranolacerta brandtii', 'Apathya': 'Apathya cappadocica', 'Anatololacerta': 'Anatololacerta danfordi', 'Hellenolacerta': 'Hellenolacerta graeca', 'Phoenicolacerta': 'Phoenicolacerta laevis', 'Iberolacerta': 'Iberolacerta monticola', 'Dinarolacerta': 'Dinarolacerta mosorensis', 'Dalmatolacerta': 'Dalmatolacerta oxycephala', 'Parvilacerta': 'Parvilacerta parva', 'Scelarcis': 'Scelarcis perspicillata', 'Darevskia': 'Darevskia saxicola', 'Zootoca': 'Zootoca vivipara', 'Lacertoides': 'Lacertoides pardalis', 'Lachesis': 'Lachesis muta', 'Lamprolepis': 'Lamprolepis smaragdina', 'Lampropeltis': 'Lampropeltis getula', 'Lamprophis': 'Lamprophis aurora', 'Boaedon': 'Boaedon lineatus', 'Inyoka': 'Inyoka swazicus', 'Ndurascincus': 'Lampropholis adonis', 'Adrasteia': 'Lampropholis elongata', 'Lampropholis': 'Lampropholis guichenoti', 'Helioscincus': 'Lampropholis mirabilis', 'Lankascincus': 'Lankascincus fallax', 'Lanthanotus': 'Lanthanotus borneensis', 'Larutia': 'Larutia larutensis', 'Laticauda': 'Laticauda laticaudata', 'Pseudolaticauda': 'Laticauda semifasciata', 'Paralaudakia': 'Paralaudakia caucasia', 'Laudakia': 'Laudakia tuberculata', 'Leiocephalus': 'Leiocephalus carinatus', 'Leioheterodon': 'Leioheterodon madagascariensis', 'Leiolepis': 'Leiolepis guttata', 'Leiolopisma': 'Leiolopisma telfairii', 'Leiosaurus': 'Leiosaurus bellii', 'Lepidoblepharis': 'Lepidoblepharis festae', 'Lepidodactylus': 'Lepidodactylus lugubris', 'Leposoma': 'Leposoma scincoides', 'Leposternon': 'Amphisbaena microcephalum', 'Leptodeira': 'Leptodeira annulata', 'Leptoseps': 'Leptoseps poilani', 'Leptosiaphos': 'Leptosiaphos meleagris', 'Perretia': 'Leptosiaphos rhomboidalis', 'Tricheilostoma': 'Tricheilostoma bicolor', 'Tetracheilostoma': 'Tetracheilostoma bilineatum', 'Rena': 'Rena humilis', 'Myriopholis': 'Myriopholis longicauda', 'Trilepida': 'Trilepida macrolepis', 'Leptotyphlops': 'Leptotyphlops nigricans', 'Namibiana': 'Namibiana occidentalis', 'Mitophis': 'Mitophis pyrites', 'Epacrophis': 'Epacrophis reticulatus', 'Siagonodon': 'Siagonodon septemstriatus', 'EPICTIA': 'Epictia undecimstriata', 'Wondjinia': 'Lerista apoda', 'Gaia': 'Lerista bipes', 'Marrunisauria': 'Lerista borealis', 'Nodorha': 'Lerista bougainvillii', 'Miculia': 'Lerista elegans', 'Krishna': 'Lerista fragilis', 'Spectrascincus': 'Lerista ingrami', 'Lerista': 'Lerista lineata', 'Rhodona': 'Lerista lineopunctulata', 'Aphroditia': 'Lerista macropisthopus', 'Lokisaurus': 'Lerista muelleri', 'Telchinoscincus': 'Lerista nichollsi', 'Goldneyia': 'Lerista planiventralis', 'Soridia': 'Lerista praepedita', 'Xynoscincus': 'Lerista stictopleura', 'Cybelia': 'Lerista terdigitata', 'Alcisius': 'Lerista vermicularis', 'Gavisus': 'Lerista wilkinsi', 'Liasis': 'Liasis mackloti', 'Limnophis': 'Limnophis bicolor', 'Liolaemus': 'Liolaemus chiliensis', 'Parasibynophis': 'Liophidium torquatum', 'Caaeteboia': 'Caaeteboia amarali', 'Liophis': 'Erythrolamprus cobella', 'and': 'Amnesteophis melanauchen', 'Liopholidophis': 'Liopholidophis grandidieri', 'Bibilava': 'Thamnosophis lateralis', 'Lioscincus': 'Lioscincus steindachneri', 'Liotyphlops': 'Liotyphlops albirostris', 'Lipinia': 'Lipinia pulchella', 'Lobulia': 'Lobulia elegans', 'Lophocalotes': 'Lophocalotes ludekingi', 'Lophognathus': 'Lophognathus gilberti', 'Luperosaurus': 'Luperosaurus cumingii', 'Lepturophis': 'Lepturophis albofuscus', 'Lycodon': 'Lycodon aulicus', 'Lycodryas': 'Lycodryas maculatus', '\x0bLycophidion': 'Lycophidion capense', 'Lygisaurus': 'Lygisaurus foliorum', 'Lygodactylus': 'Lygodactylus capensis', 'Vanzoia': 'Lygodactylus klugei', 'Mochlus': 'Mochlus afer', 'Squamicilia': 'Lygosoma isodactylum', 'Riopa': 'Lygosoma punctata', 'Lygosoma': 'Lygosoma quadrupes', 'Lyriocephalus': 'Lyriocephalus scutatus', 'Lystrophis': 'Xenodon dorbignyi', 'Varzea': 'Varzea bistriata', 'Panopa': 'Panopa croizati', 'Aspronema': 'Aspronema dorsivittatum', 'Manciola': 'Manciola guaporicola', 'Mabuya': 'Mabuya mabouya', 'Eutropis': 'Eutropis multifasciata', 'Exila': 'Exila nigropalmata', 'Copeoglossum': 'Copeoglossum nigropunctatum', 'Trachylepis': 'Trachylepis quinquetaeniata', 'Marisora': 'Marisora unimarginata', 'Macropholidus': 'Macropholidus ruthveni', 'Macroscincus': 'Chioninia coctei', 'Macrovipera': 'Macrovipera lebetina', 'Malaclemys': 'Malaclemys terrapin', 'Malpolon': 'Malpolon monspessulanus', 'Celatiscincus': 'Celatiscincus euryotis', 'Marmorosphax': 'Marmorosphax tricolor', 'Masticophis': 'Coluber taeniatus', 'Maticora': 'Calliophis intestinalis', 'Matoatoa': 'Matoatoa brevipes', 'Mauremys': 'Mauremys leprosa', 'Mediodactylus': 'Mediodactylus kotschyi', 'Meizodon': 'Meizodon regularis', 'Melanochelys': 'Melanochelys trijuga', 'Melanoseps': 'Melanoseps ater', 'Melanosuchus': 'Melanosuchus niger', 'Menetia': 'Menetia greyii', 'PygmaeascincusCOUPER': 'Pygmaeascincus timlowi', 'Mesalina': 'Mesalina rubropunctata', 'Mesaspis': 'Mesaspis moreletii', 'Mesobaena': 'Mesobaena huebneri', 'Mesoscincus': 'Mesoscincus schwartzei', 'Micrablepharus': 'Micrablepharus maximiliani', 'Micrelaps': 'Micrelaps muelleri', 'Microgecko': 'Microgecko helenae', 'Leptomicrurus': 'Micrurus collaris', 'Micrurus': 'Micrurus spixii', 'Mictopholis': 'Pseudocalotes austeniana', 'Lepidothyris': 'Lepidothyris fernandi', 'Moloch': 'Moloch horridus', 'Monopeltis': 'Monopeltis capensis', 'Montatheris': 'Montatheris hindii', 'Simalia': 'Simalia amethistina', 'Morelia': 'Morelia spilota', 'Morenia': 'Morenia ocellata', 'Morethia': 'Morethia lineoocellata', 'Morunasaurus': 'Morunasaurus groi', 'Myron': 'Myron richardsonii', 'Nactus': 'Nactus pelagicus', 'Uraeus': 'Naja haje', 'Naja': 'Naja naja', 'Afronaja': 'Naja nigricollis', 'Narudasia': 'Narudasia festiva', 'Natriciteres': 'Natriciteres olivacea', 'Natrix': 'Natrix natrix', 'Naultinus': 'Naultinus elegans', 'Nephrurus': 'Nephrurus asper', 'Underwoodisaurus': 'Underwoodisaurus milii', 'Uvidicolus': 'Uvidicolus sphyrurus', 'Nerodia': 'Nerodia sipedon', 'Neusticurus': 'Potamites ecpleopus', 'Potamites': 'Potamites strangulatus', 'Ninia': 'Ninia diademata', 'Niveoscincus': 'Niveoscincus greeni', 'Litotescincus': 'Niveoscincus metallicus', 'Nothobachia': 'Nothobachia ablephara', 'Notochelys': 'Notochelys platynota', 'Notoscincus': 'Notoscincus ornatus', 'Amalosia': 'Amalosia lesueurii', 'Oedura': 'Oedura marmorata', 'Hesperoedura': 'Hesperoedura reticulata', 'Nebulifera': 'Nebulifera robusta', 'Ogmodon': 'Ogmodon vitianus', 'Archelaphe': 'Archelaphe bella', 'Oligodon': 'Oligodon bitorquatus', 'Stichophanes': 'Stichophanes ningshaanensis', 'Oligosoma': 'Oligosoma zelandicum', 'Ophiodes': 'Ophiodes striatus', 'Ophiomorus': 'Ophiomorus punctatissimus', 'Ophiophagus': 'Ophiophagus hannah', 'Dopasia': 'Dopasia gracilis', 'Ophisaurus': 'Ophisaurus ventralis', 'Ophryacus': 'Ophryacus undulatus', 'Opipeuter': 'Proctoporus xestus', 'Paratapinophis': 'Paratapinophis praemaxillaris', 'Oriocalotes': 'Oriocalotes paulus', 'Osteolaemus': 'Osteolaemus tetraspis', 'Otocryptis': 'Otocryptis wiegmanni', 'Garthius': 'Garthius chaseni', 'Ovophis': 'Ovophis monticola', 'Oxyrhopus': 'Oxyrhopus petolarius', 'Pachycalamus': 'Pachycalamus brevis', 'Pachydactylus': 'Pachydactylus geitje', 'Paleosuchus': 'Paleosuchus trigonatus', 'Palmatogecko': 'Pachydactylus rangei', 'Panaspis': 'Panaspis cabindae', 'Papuascincus': 'Papuascincus stanleyanus', 'Paracontias': 'Paracontias brocchii', 'Paragehyra': 'Paragehyra petiti', 'Parahelicops': 'Parahelicops annamensis', 'Pararhadinaea': 'Pararhadinaea melanogaster', 'Pareas': 'Pareas carinatus', 'Paroedura': 'Paroedura sanctijohannis', 'Parvoscincus': 'Parvoscincus sisoni', 'Pelamis': 'Hydrophis platurus', 'Pelomedusa': 'Pelomedusa subrufa', 'Pelusios': 'Pelusios subniger', 'Perochirus': 'Perochirus ateles', 'Streptosaurus': 'Petrosaurus mearnsi', 'Phalotris': 'Phalotris tricolor', 'Phelsuma': 'Phelsuma cepediana', 'Rhoptropella': 'Rhoptropella ocellata', 'Phenacosaurus': 'Anolis heterodermus', 'Philodryas': 'Philodryas olfersii', 'Dendrophis': 'Philothamnus semivariegatus', 'Rodriguesophis': 'Rodriguesophis iglesiasi', 'Phoboscincus': 'Phoboscincus bocourti', 'Pholidobolus': 'Pholidobolus montium', 'Phoxophrys': 'Phoxophrys tuberculata', 'Phrynocephalus': 'Phrynocephalus guttatus', 'Phrynops': 'Phrynops geoffroanus', 'Mesoclemmys': 'Mesoclemmys gibba',  'Rhinemys': 'Rhinemys rufipes', 'Phrynosoma': 'Phrynosoma orbiculare', 'Phyllodactylus': 'Phyllodactylus pulcher', 'Phyllorhynchus': 'Phyllorhynchus browni', 'Phyllurus': 'Phyllurus platurus', 'Phymaturus': 'Phymaturus palluma', 'Physignathus': 'Physignathus cocincinus', 'Istiurus': 'Intellagama lesueurii', 'Placosoma': 'Placosoma cordylinum', 'Homopholis': 'Homopholis walbergii', 'Platyplectrurus': 'Platyplectrurus trilineatus', 'Platysaurus': 'Platysaurus capensis', 'Plectrurus': 'Plectrurus perroteti', 'Teira': 'Teira dugesii', 'Podarcis': 'Podarcis muralis', 'Pogona': 'Pogona barbata', 'Uxoriousauria': 'Pogona microlepidota', 'Polychrus': 'Polychrus marmoratus', 'Porthidium': 'Porthidium nasutum', 'Prasinohaema': 'Prasinohaema flavipes', 'Pristurus': 'Pristurus carteri', 'Proablepharus': 'Proablepharus reginae', 'Proatheris': 'Proatheris superciliaris', 'Procellosaurinus': 'Procellosaurinus erythrocercus', 'Proctoporus': 'Proctoporus pachyurus', 'Riama': 'Riama unicolor', 'Petracola': 'Petracola ventrimaculatus', 'Proscelotes': 'Proscelotes eggeli', 'Prosymna': 'Prosymna meleagris', 'Protobothrops': 'Protobothrops flavoviridis', 'Psammophilus': 'Psammophilus dorsalis', 'Taphrometopon': 'Psammophis lineolatus', 'Psammophis': 'Psammophis sibilans', 'Pseudaspis': 'Pseudaspis cana', 'Pseudemys': 'Pseudemys concinna', 'Pseudoacontias': 'Pseudoacontias madagascariensis', 'Pseudoboa': 'Pseudoboa coronata', 'Pseudocophotis': 'Pseudocophotis sumatrana', 'Pseudocalotes': 'Pseudocalotes tympanistriga', 'Pseudocerastes': 'Pseudocerastes persicus', 'Hemicrodulus': 'Hemicordylus capensis', 'Pseudocordylus': 'Pseudocordylus microlepidotus', 'Pseudocyclophis': 'Eirenis persicus', 'Pseudoeryx': 'Pseudoeryx plicatilis', 'Pseudogekko': 'Pseudogekko compressicorpus', 'Pseudogonatodes': 'Pseudogonatodes furvus', 'Pseudohaje': 'Pseudohaje nigra', 'Pseudoleptodeira': 'Pseudoleptodeira latifasciata', 'Pseudonaja': 'Pseudonaja nuchalis', 'Pseudopus': 'Pseudopus apodus', 'Pseudorabdon': 'Pseudorabdion longiceps', 'Pseudotrapelus': 'Pseudotrapelus sinaitus', 'Pseudotyphlops': 'Pseudotyphlops philippinus', 'Pseudoxyrhopus': 'Pseudoxyrhopus microps', 'Pseustes': 'Spilotes sulphureus', 'Psilophthalmus': 'Psilophthalmus paeminosus', 'Psomophis,': 'Psomophis obtusus', 'Ptenopus': 'Ptenopus garrulus', 'Ptychoglossus': 'Ptychoglossus bilineatus', 'Ptychozoon': 'Ptychozoon kuhli', 'Ptyctolaemus': 'Ptyctolaemus gularis', 'Mantheyus': 'Mantheyus phuwuanensis', 'Ptyodactylus': 'Ptyodactylus hasselquistii', 'Pygomeles': 'Pygomeles braconnieri', 'Python': 'Python molurus', 'Malayopython': 'Malayopython reticulatus', 'Pythonodipsas': 'Pythonodipsas carinata', 'Quedenfeldtia': 'Quedenfeldtia trachyblepharus', 'Anilios': 'Anilios australis', 'Cathetorhinus': 'Cathetorhinus melanocephalus', 'Ramphotyphlops': 'Ramphotyphlops multilineatus', 'Austrotyphlops': 'Anilios nigrescens', 'Rankinia': 'Rankinia diemensis', 'Regina': 'Regina septemvittata', 'Nuchisulcophis': 'Rhabdophis nuchalis', 'Rhabdophis': 'Rhabdophis subminiatus', 'Pseudothecadactylus': 'Pseudothecadactylus australis', 'Mniarogekko': 'Mniarogekko chahoua', 'Correlophus': 'Correlophus ciliatus', 'Rhacodactylus': 'Rhacodactylus leachianus', 'Rhadinella': 'Rhadinella schistosa', 'Rhadinaea': 'Rhadinaea vermiculaticeps', 'Rieppeleon': 'Rieppeleon kerstenii', 'Bicuspis': 'Rhampholeon marshalli', 'Rhinodigitum': 'Rhampholeon platyceps', 'Rhampholeon': 'Rhampholeon spectrum', 'Rheodytes': 'Rheodytes leukops', 'Rhineura': 'Rhineura floridana', 'Rhinocheilus': 'Rhinocheilus lecontei', 'Rhinoleptus': 'Rhinoleptus koniagui', 'Rhinophis': 'Rhinophis oxyrhynchus', 'Grypotyphlops': 'Grypotyphlops acutus', 'Letheobia': 'Letheobia caeca', 'Rhoptropus': 'Rhoptropus afer', 'Rhynchoedura': 'Rhynchoedura ornata', 'Rhynchophis': 'Gonyosoma boulengeri', 'Riolama': 'Riolama leucosticta', 'Saiphos': 'Saiphos equalis', 'Salea': 'Salea horsfieldii', 'Saltuarius': 'Saltuarius cornutus', 'Orraya': 'Orraya occultus', 'Salvadora': 'Salvadora grahamiae', 'Sator': 'Sceloporus grandaevus', 'Saurodactylus': 'Saurodactylus mauritanicus', 'Sauromalus': 'Sauromalus ater', 'Scaphiodontophis': 'Scaphiodontophis annulatus', 'Sceloporus': 'Sceloporus torquatus', 'Scelotes': 'Scelotes bipes', 'Kaestlea': 'Kaestlea bilineata', 'Scincella': 'Scincella lateralis', 'Scincopus': 'Scincopus fasciatus', 'Scincus': 'Scincus albifasciatus', 'Scolecophis': 'Scolecophis atrocinctus', 'Scolecoseps': 'Scolecoseps boulengeri', 'Lycognathophis': 'Lycognathophis seychellensis', 'Seminatrix': 'Seminatrix pygaea', 'Senticolis': 'Senticolis triaspis', 'Sepsina': 'Sepsina angolensis', 'Shinisaurus': 'Shinisaurus crocodilurus', 'Sibon': 'Sibon nebulatus', 'Sibynophis': 'Sibynophis geminatus', 'Sigaloseps': 'Sigaloseps deplanchei', 'Simophis': 'Simophis rhinostoma', 'Antaioserpens': 'Antaioserpens warro', 'Sinonatrix': 'Sinonatrix annularis', 'Siphlophis': 'Siphlophis cervinus', 'Tripanurgos,': 'Siphlophis compressus', 'Piersonus': 'Crotalus ravus', 'Sitana': 'Sitana ponticeriana', 'Sonora': 'Sonora semiannulata', 'Spalerosophis': 'Spalerosophis microlepis', 'Sphaerodactylus': 'Sphaerodactylus sputator', 'Sphenodon': 'Sphenodon punctatus', 'Otosaurus': 'Otosaurus cumingi', 'Pinoyscincus': 'Pinoyscincus jagori', 'Sphenomorphus': 'Sphenomorphus melanopogon', 'Insulasaurus': 'Insulasaurus wrighti', 'Stenocercus': 'Stenocercus roseiventris', 'Ophryoessoides': 'Stenocercus tricristatus', 'Pseudoceramodactylus': 'Pseudoceramodactylus khobarensis', 'Stenodactylus': 'Stenodactylus sthenodactylus', 'Stenolepis': 'Stenolepis ridleyi', 'Phisalixella': 'Phisalixella arctifasciata', 'Parastenophis': 'Parastenophis betsileanus', 'Stenophis': 'Lycodryas gaimardi', 'Stoliczkia': 'Stoliczkia khasiensis', 'Storeria': 'Storeria dekayi', 'Suta': 'Suta suta', 'Symphimus': 'Symphimus leucostomus', 'Sympholis': 'Sympholis lippiens', 'Synophis': 'Synophis bicolor', 'Tachygyia': 'Tachygyia microlepis', 'Takydromus': 'Takydromus sexlineatus', 'Tantillita': 'Tantillita lintoni', 'Tarentola': 'Tarentola mauritanica', 'Teius': 'Teius teyou', 'Altigekko': 'Altiphylax baturensis', 'Tenuidactylus': 'Tenuidactylus caspius', 'Indogekko': 'Cyrtopodion indusoani', 'Teratoscincus': 'Teratoscincus scincus', 'Teretrurus': 'Teretrurus sanguineus', 'Chersina': 'Chersina angulata', 'Tetradactylus': 'Tetradactylus tetradactylus', 'Teuchocercus': 'Teuchocercus keyi', 'Thalassophina': 'Hydrophis viperinus', 'Tropidonotus': 'Thamnophis sauritus', 'Thaumatorhynchus': 'Thaumatorhynchus brooksi', 'Thecadactylus': 'Thecadactylus rapicauda', 'Thermophis': 'Thermophis baileyi', 'Tomistoma': 'Tomistoma schlegelii', 'Tomodon': 'Tomodon dorsatum', 'Trachemys': 'Trachemys scripta', 'Trachyboa': 'Trachyboa gularis', 'Trapelus': 'Trapelus mutabilis', 'Tretioscincus': 'Tretioscincus bifasciatus', 'Parias': 'Trimeresurus flavomaculatus', 'Trimeresurus': 'Trimeresurus viridis', 'Peltopelor': 'Trimeresurus macrolepis', 'Cryptelytrops': 'Trimeresurus purpureomaculatus', 'Viridovipera': 'Trimeresurus stejnegeri', 'Himalayophis': 'Trimeresurus tibetanus', 'Trogonophis': 'Trogonophis wiegmanni', 'Tropidodryas': 'Tropidodryas serra', 'Tropidolaemus': 'Tropidolaemus wagleri', 'Tropidonophis': 'Tropidonophis picturatus', 'Tropidophis': 'Tropidophis melanurus', 'Tropidophorus': 'Tropidophorus cocincinensis', 'Eurolophosaurus': 'Eurolophosaurus nanuzae', 'Tapinurus': 'Tropidurus semitaeniatus', 'Tropidurus': 'Tropidurus torquatus', 'Tropiocolotes': 'Tropiocolotes tripolitanus', 'Salvator': 'Salvator merianae', 'Tupinambis': 'Tupinambis teguixin', 'Rotundacryptus': 'Tympanocryptis cephalus', 'Tympanocryptis': 'Tympanocryptis lineata', 'Typhlacontias': 'Typhlacontias punctatissimus', 'Typhlophis': 'Typhlophis squamosus', 'Madatyphlops': 'Madatyphlops arenarius', 'Gerrhopilus': 'Gerrhopilus ater', 'Cubatyphlops': 'Typhlops biminiensis', 'Amerotyphlops': 'Amerotyphlops brongersmianus', 'Antillotyphlops': 'Typhlops hypomethes', 'Typhlops': 'Typhlops lumbricalis', 'Malayotyphlops': 'Malayotyphlops luzonensis', 'Lemuriatyphlops': 'Lemuriatyphlops microcephalus', 'Argyrophis': 'Argyrophis muelleri', 'Indotyphlops': 'Indotyphlops pammeces', 'Afrotyphlops': 'Afrotyphlops punctatus', 'Xerotyphlops': 'Xerotyphlops vermicularis', 'Typhlosaurus': 'Typhlosaurus caecus', 'Ungaliophis': 'Ungaliophis continentalis', 'Urocotyledon': 'Urocotyledon inexpectata', 'Uromacer': 'Uromacer oxyrhynchus', 'Uromacerina': 'Uromacerina ricardinii', 'Uromastyx': 'Uromastyx aegyptia', 'Saara': 'Orosaura nebulosylvestris', 'Uropeltis': 'Uropeltis ceylanicus', 'Uroplatus': 'Uroplatus fimbriatus', 'Urostrophus': 'Urostrophus vautieri', 'Vanzosaura': 'Vanzosaura rubricauda', 'Varanus': 'Varanus varius', 'Vipera': 'Vipera aspis', 'Montivipera': 'Montivipera xanthina', 'Voeltzkowia': 'Voeltzkowia mira', 'Waglerophis': 'Xenodon merremi', 'Xantusia': 'Xantusia vigilis', 'Xenagama': 'Xenagama batillifera', 'Xenocalamus': 'Xenocalamus bicolor', 'Xenodermus': 'Xenodermus javanicus', 'Xenodon': 'Xenodon severus', 'Xenopeltis': 'Xenopeltis unicolor', 'Xenophidion': 'Xenophidion acanthognathus', 'Xenosaurus': 'Xenosaurus grandis', 'Xenotyphlops': 'Xenotyphlops grandidieri', 'Zygaspis': 'Zygaspis quadrifrons', 'Eublepharis': 'Eublepharis hardwickii', 'Lioheterophis': 'Lioheterophis iheringi', 'Adercosaurus': 'Adercosaurus vixadnexus', 'Paniegekko': 'Paniegekko madjo', 'Homonota': 'Garthia gaudichaudii', 'Lapemis': 'Hydrophis hardwickii', 'Homodactylus': 'Chondrodactylus turneri', 'Tytthoscincus': 'Tytthoscincus hallieri', 'Brasiliscincus': 'Brasiliscincus agilis', 'Chitra': 'Chitra indica', 'Popeia': 'Trimeresurus popeiorum', 'Xyelodontophis': 'Xyelodontophis uluguruensis', 'Elaphe': 'Elaphe sauromates', 'Boiruna': 'Boiruna maculata', 'Kaieteurosaurus': 'Kaieteurosaurus hindsi', 'Oedodera': 'Oedodera marmorata', 'Alexandresaurus': 'Alexandresaurus camacan', 'Dryadosaura': 'Dryadosaura nordestina', 'Quantasia': 'Cyrtodactylus tuberculatus', 'Calamophis': 'Calamophis jobiensis', 'Tychismia': 'Lerista chordae', 'Trimorphodon': 'Trimorphodon lambda', 'Hypsiglena': 'Hypsiglena ochrorhyncha', 'Strobilurus': 'Strobilurus torquatus', 'Kolekanos': 'Kolekanos plumicaudus', 'Megatyphlops': 'Afrotyphlops mucruso', 'Colubroelaps': 'Colubroelaps nguyenvansangi', 'Caparaonia': 'Caparaonia itaiquara', 'Aprosdoketophis': 'Aprosdoketophis andreonei', 'Chelonia': 'Chelonia mydas', 'Opisthotropis': 'Opisthotropis atra', 'Sinovipera': 'Trimeresurus sichuanensis', 'Marinussaurus': 'Marinussaurus curupira', 'Malayemys': 'Malayemys macrocephala', 'Capitellum': 'Capitellum metallicum', 'Karnsophis': 'Karnsophis siantaris', 'Terrapene': 'Terrapene carolina', 'Timon': 'Timon lepidus', 'Eutrachelophis': 'Eutrachelophis bassleri', 'Sundatyphlops': 'Anilios polygrammicus', 'Pelodiscus': 'Pelodiscus sinensis', 'Flaviemys': 'Flaviemys purvisi', 'Ptyas': 'Ptyas mucosa', 'Rhagerhis': 'Rhagerhis moilensis', 'Notomabuya': 'Notomabuya frenata', 'Stellagama': 'Stellagama stellio', 'Rhadinophis': 'Gonyosoma frenatum', 'Calodactylodes': 'Calodactylodes aureus', 'Apostolepis': 'Apostolepis flavotorquata', 'Apalone': 'Apalone ferox'}
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

        # Obtain parent-Q value: used when running algorithm.
        parent_Q = ""
        parent_id = used_taxa[taxonID]["parent_id"]
        if parent_id in used_taxa:
            parent_Q = used_taxa[parent_id]["Q"]
        if taxonID in added_taxa:
            Q, image, definition, label = added_taxa[taxonID]["Q"], added_taxa[taxonID]["image"],added_taxa[taxonID]["definition"],added_taxa[taxonID]["label"]
        else:
            Q, image, definition, label = taxa(scientificName, parent_Q)
        
        # Add information to taxon dictionary for second-pass algorithm
        name_to_id[scientificName] = taxonID
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
        

# SECOND PASS
for taxon_id in list(used_taxa.keys()):
    taxon = used_taxa[taxon_id]
    full_Q = "boltz:" + taxon["Q"] + " a kgo:Taxon ; \n\t" #Q-ID
    full_name = "kgo:taxonName\t\""  + taxon["name"] + "\"@en ; \n\t"
    full_rank = "kgo:taxonRank\tboltz:" + ranks[taxon["rank"]] + " ; \n\t" #rank
    
    full_parent_Q = ""
    full_type_species = ""
    full_tso = ""
    full_image = ""

    parent_id = taxon["parent_id"]
    if parent_id != 0:
        parent_Q = used_taxa[parent_id]["Q"]
        full_parent_Q = "kgo:subTaxonOf\tboltz:" + parent_Q + " ; \n\t" 
    # Goal: change type species to use the q-value property, instead of the name right now.  
    type_species = taxon["type_species"]
    type_species_of = taxon["type_species_of"]
    if type_species in name_to_id:
        type_speciesID = name_to_id[type_species]
        full_type_species = "kgo:typeSpecies\tboltz:" + used_taxa[type_speciesID]["Q"] + " ;\n\t" #type species
    elif type_species != "":
        full_type_species = "kgo:typeSpecies\t\"" + type_species + "\"@en ;\n\t" #type species
    if type_species_of in name_to_id:
        type_species_ofID = name_to_id[type_species_of]
        full_tso = "kgo:typeSpeciesOf\tboltz:" + used_taxa[type_species_ofID]["Q"] + " ;\n\t" #type species of
    elif type_species_of != "":
        full_type_species = "kgo:typeSpeciesOf\t\"" + full_tso + "\"@en ;\n\t" #type species
    if taxon["image"] != "":
        full_image = "kgo:taxonImage\t<" + taxon["image"] + "> ; \n\t"
    full_definition = "skos:definition\t\"\"\"" + taxon["definition"] + "\"\"\"@en ;\n\t" #definition
    full_label = "skos:prefLabel\t\"" + taxon["label"] + "\"@en .\n\n"    #prefLabel – common name

    d = full_Q + full_parent_Q + full_name + full_rank + full_type_species + full_tso + full_image + full_definition + full_label 

    outfile.write(d)

print(to_confirm)
outfile.close()
