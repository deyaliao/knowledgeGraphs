import pandas as pd

csv_file = open("species/primates.txt")

df = pd.read_csv(csv_file, sep="\t")
df.to_csv("primates.csv")