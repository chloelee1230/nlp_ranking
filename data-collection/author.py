import requests
from bs4 import BeautifulSoup
import pandas as pd
import glob
import os
from os import walk


def get_author_IDs():
    txt_dir = './txt/'
    for txt_file in glob.glob(os.path.join(txt_dir, '*.txt')):
        id = txt_file.split('/')[-1].split('.')[0]
        checked_file = [line.rstrip('\n') for line in open('checked_file.txt')]

        if id not in checked_file:
            try:
                url = 'https://www.aclweb.org/anthology/' + id + '/'

                r = requests.get(url)
                soup = BeautifulSoup(r.text, 'html.parser')

                authors = soup.find('p', class_ = 'lead').find_all('a')

                with open('author_webpages.txt', 'a') as webpage:
                    for a in authors:
                        author = a.get('href')
                        if '/people/'in author:
                            webpage.write(author + '\t' + id + '\n')

                    webpage.close()

                with open('checked_file.txt', 'a') as checked:
                    checked.write(id+'\n')
                    checked.close()

                print('Checked all the authors in document ' + id)
            except:
                continue


def author_bib():

    authors = {}
    for line in open('author_webpages.txt'):
        info = line.rstrip('\n').split('\t')
        url = info[0]
        paper = info[1]
        if url in authors:
            authors[url].append(paper)
        else:
            authors[url] = [paper]




    checked_author = [line.rstrip('\n') for line in open('checked_author.txt')]

    for k, v in authors.items():

        if k not in checked_author:

            with open('author_publications.txt', 'a') as author_pub:
                r = requests.get('https://www.aclweb.org' + k)
                soup = BeautifulSoup(r.text, 'html.parser')
                firstname = soup.find('span', class_='font-weight-normal').text
                lastname = soup.find('span', class_='font-weight-bold').text

                key = k.split('/')[-2]
                pub = ','.join(v)

                author_pub.write(key + '\t' + firstname + '\t' + lastname + '\t' + pub + '\n')
                author_pub.close()

                print('Added author ' + firstname + ' ' + lastname + ' to txt')

            with open('checked_author.txt', 'a') as checked:
                checked.write(k + '\n')
                checked.close()



def author2json():

    dat = pd.read_csv('author_publications.txt', sep='\t', header=None)
    dat.columns = ['key', 'firstname', 'lastname', 'publications']

    dat['publications'] = dat['publications'].str.split(',')

    dat.to_json('author.json', orient='records')


# add missing publication to author_webpages.txt
def add_missing():

    a = [] # in author_publications.txt
    dat = pd.read_csv('author_publication.txt', sep='\t', header=None)
    dat.columns = ['key', 'firstname', 'lastname', 'publications']
    for da in [d.split(',') for d in dat['publications'].values.tolist()]:
        a.extend(da)
    a = list(set(a))


    for (dirpath, dirnames, filenames) in walk('./txt/'):
        filenames.remove('.DS_Store')
        filenames = [f.split('.')[0] for f in filenames]

    print(len(list(set(filenames)-set(a))))

    for id in list(set(filenames)-set(a)):
        url = 'https://www.aclweb.org/anthology/' + id + '/'

        r = requests.get(url)
        soup = BeautifulSoup(r.text, 'html.parser')

        authors = soup.find('p', class_='lead').find_all('a')

        with open('author_webpages.txt', 'a') as webpage:
            for a in authors:
                author = a.get('href')
                if '/people/' in author:
                    webpage.write(author + '\t' + id + '\n')

            webpage.close()

        with open('checked_file.txt', 'a') as checked:
            checked.write(id + '\n')
            checked.close()

        print('Checked all the authors in document ' + id)


from itertools import islice
import numpy as np


def add_missing_to_pub():
    dat = pd.read_csv('author_publications.txt', sep='\t', header=None)
    dat.columns = ['key', 'firstname', 'lastname', 'publications']
    dat = dat.replace(np.nan, '', regex=True)
    author_pub = dat.set_index(dat.key).T.to_dict()

    # print(author_pub)

    with open('author_webpages.txt') as f:
        for line in islice(f, 76273, None):
            info = line.rstrip('\n').split('\t')
            a_id = info[0].split('/')[-2]
            paper = info[1]
            try:
                author_pub[a_id]['publications'] += ','+paper
            except:
                r = requests.get('https://www.aclweb.org' + info[0])
                soup = BeautifulSoup(r.text, 'html.parser')
                firstname = soup.find('span', class_='font-weight-normal').text
                lastname = soup.find('span', class_='font-weight-bold').text

                author_pub[a_id] = {'key': a_id, 'firstname': firstname, 'lastname': lastname, 'publications': paper}


            print('Added paper ' + paper + ' to dict')






    with open('author_publications.txt', 'w') as f:
        for v1 in author_pub.values():
            f.write('\t'.join([v2 for v2 in v1.values()]) + '\n')




if __name__ == '__main__':
    # get_author_IDs()
    # author_bib()
    author2json()
    # add_missing()
    # add_missing_to_pub()
