import csv

csvfile =  open('rnc_mic_key_phrases.csv', newline='', encoding='utf-8')

reader = csv.DictReader(csvfile) 

def find_title_id(title):
    for row in reader:
        if row['mcTitle'] == title:
            return row['mcId']
