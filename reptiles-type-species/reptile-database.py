import pandas as pd

csv_file = open("reptiles-type-species/Reptile_database201412/Reptile_database2014-12.txt", encoding="utf8", errors='ignore')

df = pd.read_csv(csv_file, engine="python", sep="ISO-8859-1")
df.to_csv("reptiles-type-species/reptile.csv")

all_ts = {}

for index, row in df.iterrows():
    # Clean up data
    row_new = row[0].replace('\x00','')
    row_new = row_new.replace("\x1d", "")
    # Specific Bugs
    row_new = row_new.replace("et al.", "")
    row_new = row_new.replace("T.", "")
    row_new = row_new.replace("549.", "")
    row_new = row_new.replace("G.M.", "")    
    row_new = row_new.replace("C.W.", "")
    row_new = row_new.replace("var.", "")

    # Faulty lines IDK
    if len(row_new) < 100 or not row_new[0].isupper():
        continue
    
    # Species Name
    split = row_new.split("\t", 3)
    type_species = split[1] + " " + split[2]

    # Type Species Information
    split = row_new.split("Type Species:")

    if len(split) == 1:
        info = ""
    else:
        info = split[1].split(".") #split[1] refers to the text after the split
        try:
            info2 = info[0].split("genus ")[1]
            genus = info2.split(" ")[0]
        except:
            genus = info[0]
        all_ts[genus] = type_species

print(all_ts)
# FINAL RESULT OF RUNNING PROGRAM: keys are genus, values are its type species
# all_ts = {'Contomastix': 'Contomastix vittata', 'Aporarchus': 'Amphisbaena prunicolor', 'Aurivela': 'Aurivela longicauda', 'Coggeria': 'Coggeria naufragus', 'Acratosaura': 'Acratosaura mentalis', 'Colopus': 'Colopus wahlbergii', 'Cophosaurus': 'Cophosaurus texanus', 'Cophoscincopus': 'Cophoscincopus simulans', 'Corytophanes': 'Corytophanes cristatus', 'Cryptactites': 'Cryptactites peringueyi', 'Cryptoblepharus': 'Cryptoblepharus poecilopleurus', 'Cryptoscincus': 'Paracontias minimus', 'Ctenotus': 'Ctenotus taeniolatus', 'Cyclodina': 'Oligosoma aeneum', 'Siwaligecko': 'Cyrtopodion battalense', 'Davewakeum': 'Brachymeles miriamae', 'Lucasium': 'Lucasium damaeum', 'Diplodactylus': 'Diplodactylus vittatus', 'Diploglossus': 'Diploglossus fasciatus', 'Diplometopon': 'Diplometopon zarudnyi', 'Dogania': 'Dogania subplana', 'Ebenavia': 'Ebenavia inunguis', 'Lissolepis': 'Lissolepis luctuosa', 'Bellatorias': 'Bellatorias major', 'Liopholis': 'Liopholis whitii', 'Elgaria': 'Elgaria multicarinata', 'Elseya': 'Elseya dentata', 'Elusor': 'Elusor macrurus', 'Emydura': 'Emydura macquarii', 'Eremiascincus': 'Eremiascincus richardsonii', 'Eugongylus': 'Eugongylus rufescens', 'Eumeces': 'Eumeces schneideri', 'Eurylepis': 'Eurylepis taeniolata', 'Gambelia': 'Gambelia wislizenii', 'Geomyersia': 'Geomyersia glabra', 'Glaphyromorphus': 'Glaphyromorphus punctulatus', 'Goggia,': 'Goggia lineata', 'Haackgreerius': 'Haackgreerius miopus', 'Haemodracon': 'Haemodracon riebeckii', 'Harpesaurus': 'Harpesaurus tricinctus', 'Homopus': 'Homopus areolatus', 'Iguana': 'Iguana iguana', 'Lacerta': 'Lacerta agilis', 'Atlantolacerta': 'Atlantolacerta andreanskyi', 'Archaeolacerta': 'Archaeolacerta bedriagae', 'Apathya': 'Apathya cappadocica', 'Anatololacerta': 'Anatololacerta danfordi', 'Hellenolacerta': 'Hellenolacerta graeca', 'Phoenicolacerta': 'Phoenicolacerta laevis', 'Iberolacerta': 'Iberolacerta monticola', 'Dinarolacerta': 'Dinarolacerta mosorensis', 'Dalmatolacerta': 'Dalmatolacerta oxycephala', 'Parvilacerta': 'Parvilacerta parva', 'Lacertoides': 'Lacertoides pardalis', 'Lampropholis': 'Lampropholis guichenoti', 'Lankascincus': 'Lankascincus fallax', 'Leiolopisma': 'Leiolopisma telfairii', 'Leiosaurus': 'Leiosaurus bellii', 'Wondjinia': 'Lerista apoda', 'Gaia': 'Lerista bipes', 'Marrunisauria': 'Lerista borealis', 'Krishna': 'Lerista fragilis', 'Spectrascincus': 'Lerista ingrami', 'Aphroditia': 'Lerista macropisthopus', 'Lokisaurus': 'Lerista muelleri', 'Goldneyia': 'Lerista planiventralis', 'Cybelia': 'Lerista terdigitata', 'Alcisius': 'Lerista vermicularis', 'Lioscincus': 'Lioscincus steindachneri', 'Lipinia': 'Lipinia pulchella', 'Lygisaurus': 'Lygisaurus foliorum', 'Vanzoia': 'Lygodactylus klugei', 'Lygosoma': 'Lygosoma quadrupes', 'Varzea': 'Varzea bistriata', 'Panopa': 'Panopa croizati', 'Manciola': 'Manciola guaporicola', 'Eutropis': 'Eutropis multifasciata', 'Exila': 'Exila nigropalmata', 'Marisora': 'Marisora unimarginata', 'Macroscincus': 'Chioninia coctei', 'Celatiscincus': 'Celatiscincus euryotis', 'Marmorosphax': 'Marmorosphax tricolor', 'Matoatoa': 'Matoatoa brevipes', 'Menetia': 'Menetia greyii', 'Mesobaena': 'Mesobaena huebneri', 'Mesoscincus': 'Mesoscincus schwartzei', 'Micrablepharus': 'Micrablepharus maximiliani', 'Lepidothyris': 'Lepidothyris fernandi', 'Monopeltis': 'Monopeltis capensis', 'Morethia': 'Morethia lineoocellata', 'Morunasaurus': 'Morunasaurus groi', 'Naultinus': 'Naultinus elegans', 'Neusticurus': 'Neusticurus bicarinatus', 'Niveoscincus': 'Niveoscincus greeni', 'Notoscincus': 'Notoscincus ornatus', 'Oligosoma': 'Oligosoma zelandicum', 'Ophiodes': 'Ophiodes striatus', 'Ophisaurus': 'Ophisaurus ventralis', 'Pachycalamus': 'Pachycalamus brevis', '': 'Elasmodactylus tuberculosus', 'Palmatogecko': 'Pachydactylus rangei', 'Panaspis': 'Panaspis cabindae', 'Paracontias': 'Paracontias brocchii', 'Phoboscincus': 'Phoboscincus bocourti', 'Mesoclemmys': 'Mesoclemmys gibba', 'Batrachemys': 'Mesoclemmys nasuta', 'Rhinemys': 'Rhinemys rufipes', 'Bufocephala': 'Mesoclemmys vanderhaegei', 'Teira': 'Teira dugesii', 'Prasinohaema': 'Prasinohaema flavipes', 'Proablepharus': 'Proablepharus reginae', 'Proctoporus': 'Proctoporus pachyurus', 'Riama': 'Riama unicolor', 'Pseudoacontias': 'Pseudoacontias madagascariensis', 'Pseudopus': 'Pseudopus apodus', 'Ptychoglossus': 'Ptychoglossus bilineatus', 'Pygomeles': 'Pygomeles braconnieri', 'Mniarogekko': 'Mniarogekko chahoua', 'Correlophus': 'Correlophus ciliatus', 'Rieppeleon': 'Rieppeleon kerstenii', 'Rhampholeon': 'Rhampholeon spectrum', 'Rhineura': 'Rhineura floridana', 'Saiphos': 'Saiphos equalis', 'Saltuarius': 'Saltuarius cornutus', 'Orraya': 'Orraya occultus', 'Kaestlea': 'Kaestlea bilineata', 'Scincopus': 'Scincopus fasciatus', 'Scincus': 'Scincus albifasciatus', 'Sigaloseps': 'Sigaloseps deplanchei', 'Piersonus': 'Crotalus ravus', 'Stenocercus': 'Stenocercus roseiventris', 'Ophryoessoides': 'Stenocercus tricristatus', 'Takydromus': 'Takydromus sexlineatus', 'Altigekko': 'Altiphylax baturensis', 'Indogekko': 'Cyrtopodion indusoani', 'Chersina': 'Chersina angulata', 'Trogonophis': 'Trogonophis wiegmanni', 'Tropidolaemus': 'Tropidolaemus wagleri', 'Tropidophorus': 'Tropidophorus cocincinensis', 'Eurolophosaurus': 'Eurolophosaurus nanuzae', 'Tapinurus': 'Tropidurus semitaeniatus', 'Typhlosaurus': 'Typhlosaurus caecus', 'Saara': 'Orosaura nebulosylvestris', 'Zygaspis': 'Zygaspis quadrifrons', 'Tychismia': 'Lerista chordae', 'Timon': 'Timon lepidus'}