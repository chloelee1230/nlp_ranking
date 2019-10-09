import re
import os
import pandas as pd
import bibtexparser



def get_emails(txtfile, authors):
    filepath = os.path.join('./txt/', txtfile + '.txt')

    doc = []
    n = 0
    fin = open(filepath)
    for line in fin:
        line = line.strip()
        if line:
            doc.append(line)
            n += len(line)
            if n > 2000: break
    doc = ' '.join(doc)

    re_email = re.compile('[({\[]?\s*([a-z0-9\.\-_]+(?:\s*[,;|]\s*[a-z0-9\.\-_]+)*)\s*[\]})]?\s*@\s*([a-z0-9\.\-_]+\.[a-z]{2,})')

    emails = []
    if re_email.findall(doc) is not None:
        for m in re_email.findall(doc):
            ids = m[0].replace(';', ',').replace('|', ',')
            domain = m[1]

            if ',' in ids:
                emails.extend([ID.strip() + '@' + domain for ID in ids.split(',')])
            else:
                emails.append(ids + '@' + domain)

        fin.close()

    # fixing firstname.lastname email types
    re_name1 = re.compile('firstname.lastname@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name2 = re.compile('first-name.last-name@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name3 = re.compile('first.last@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name4 = re.compile('\{first-name.last-name\}@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name5 = re.compile('name.surname@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')
    re_name6 = re.compile('\{firstname.surname\}@([a-z]+.[a-z]+(-[a-z]+.[a-z]+)?)')

    re_name_list = [re_name1, re_name2, re_name3, re_name4, re_name5, re_name6]

    for email in emails:
        if any(regex.findall(email) for regex in re_name_list):
            for m in re_email.findall(email):
                if 'first' in m[0]:
                    domain = m[1]

            for author in authors:
                try:
                    f = author.split(', ')[1].split(' ')[0]
                    l = author.split(', ')[0]
                except:
                    f = author.split(' ')[0]
                    l = author.split(' ')[1]
                if all(f.lower() not in e for e in emails):
                    emails.append(f.lower() + '.' + l.lower() + '@' + domain)

            emails.remove(email) # remove firstname.lastname email template from emails


    return emails


from os import walk

def publication_json():

    bibmap = pd.read_json('bibmap.json')
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)

    # files already in pub_json dir
    files = []
    for (dirpath, dirnames, filenames) in walk('./pub_json/'):
        for filename in filenames:
            if '.json' in filename:
                files.append(filename.split('.')[0])


    for ID in bibmap['id'].tolist():
        if ID not in files:
            bibs = {}
            pub_data = []

            filepath = './bib/' + ID + '.bib'
            f = open(filepath)
            bib = bibtexparser.loads(f.read(), parser=parser)
            bibs.update(
                [(entry['url'].split('/')[-1], entry) for entry in bib.entries
                 if ('author' in entry and 'pages' in entry and 'url' in entry)])
            # bibs.update(
            #     [(entry['ID'], entry) for entry in bib.entries
            #      if ('author' in entry and 'pages' in entry and 'url' in entry)])


            for k,v in bibs.items():
                pub_dict = {}
                pub_dict['id'] = k
                pub_dict['title'] = v['title']
                del v['title']

                pub_dict['authors'] = v['author'].split('  and\n')
                del v['author']
                # print(ID, k, pub_dict['authors'])
                pub_dict['emails'] = get_emails(k, pub_dict['authors'])
                pub_dict['emails'] = email_match(pub_dict['authors'], pub_dict['emails'])

                # print(k)
                # print(pub_dict['authors'])
                # print(pub_dict['emails'])


                del v['ENTRYTYPE']
                del v['ID']
                pub_dict.update(v)

                pub_data.append(pub_dict)


            df = pd.DataFrame(pub_data)
            df.to_json('./pub_json/' + ID + '.json', orient='records')
            print("Added " + ID + ".json to file")


from fuzzywuzzy import fuzz
import numpy as np

def email_match(authors, emails):

    author_list = authors[:] # create a copy of authors (not changing the input)

    # result = reordered emails list
    result = [''] * len(author_list)

    matrix = []
    for email in emails:
        ratios = []
        for author in author_list:
            try:
                email_id = email.split('@')[0]

                try:
                    lname = author.split(', ')[0].lower()
                    fname = author.split(', ')[1].lower()
                except:
                    fname = author.split(' ')[0].lower()
                    lname = author.split(' ')[1].lower()

                initial = ''.join([i[0].lower() for i in re.findall(r"[\w']+", fname)]) + ''.join(
                    [j[0].lower() for j in re.findall(r"[\w']+", lname)])
                f_lastname = fname[0] + lname
                name = fname + lname


                ratios.append([fuzz.partial_ratio(lname, email_id), fuzz.partial_ratio(fname, email_id),
                               fuzz.partial_ratio(initial, email_id), fuzz.partial_ratio(f_lastname, email_id),
                               fuzz.ratio(name, email_id)])

                # ratios.append([fuzz.ratio(lname, email_id), fuzz.ratio(fname, email_id),
                #                fuzz.ratio(initial, email_id), fuzz.ratio(f_lastname, email_id),
                #                fuzz.ratio(name, email_id)])

            except:
                ratios.append([0] * 5)


        ratios = np.array(ratios)
        ratios = np.transpose(ratios)
        matrix.extend(ratios)


    matrix = np.array(matrix)


    indices = {}
    for score in sorted(set(matrix.flat), reverse=True):
            cord = np.where(matrix == score)
            for c in list(zip(cord[0], cord[1])):
                if c[0]//5 not in indices.keys() and c[1] not in indices.values():
                    indices[c[0]//5] = c[1]

                if len(indices) == len(emails):
                    break


    for k,v in indices.items():
        result[v] = emails[k]



    return result

if __name__ == '__main__':
    publication_json()
