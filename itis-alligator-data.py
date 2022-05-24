import csv
from os import sep
import pandas as pd
            
df = pd.read_csv("itis/taxa_9796598.txt", sep='\t')
type = df.dtypes
num_rows = len(df.count(axis=1))
num_columns = len(df.count(axis=0))

# convert to readable csv file
df.to_csv('itis.csv')

# open ttl file
outfile = open('itis-alligator-data.ttl', 'a')

# convert data to triples here 
all_info = []  #string dictionary 
for index, row in df.iterrows():
    if index == 0:
        pass
    else: 
        info = ''
        if not pd.isna(row['taxonRemarks']):
            info = row['taxonRemarks']
        d = "boltz: a kgo:Taxon ; \n\t kgo:subTaxonOf boltz: ; \n\t kgo:taxonName \t" + "\"" + row['scientificName'] + "\"" + "@en ; \n\t kgo:taxonRank \t kgo:" + row['taxonRank'] + " ; \n\t kgo:taxonRemark \t" + "\"" + info + "\"" + " . \n"
        outfile.write(d)

outfile.close()
