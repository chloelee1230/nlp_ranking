import pandas as pd
from os import walk
from collections import Counter

def university_pub():

    universities = pd.read_csv('us_universities.tsv', sep='\t', names=['university', 'domain', 'city', 'state'])


    uni = {}

    for u in universities['domain']:
        uni[u] = []

    for (dirpath, dirnames, filenames) in walk('./pub_json/'):
        for filename in filenames:
            pub = pd.read_json(dirpath + filename)
            records = pub.to_dict(orient='records')
            # print(records)

            for record in records:
                domains = [parse_email(e.split('@')[-1]) for e in record['emails']]
                # print(record['emails'])
                c = Counter(domains)
                for key in c.keys():
                    if key in uni.keys():
                        # (pub_id, year, contribution_percentage)
                        uni[key].append((record['id'], record['year'], c[key]/len(record['authors'])))



    print(uni)

    university_list = []
    for k,v in uni.items():
        name = universities[universities['domain'] == k]['university'].values[0]
        university_list.append({'domain_id': k, 'name': name, 'publications': v})

    df = pd.DataFrame(university_list)
    df.to_json('university.json', orient='records')


def parse_email(domain):
    if '.edu' in domain:
        d = domain.split('.')
        return '.'.join(d[d.index('edu')-1:])
    else:
        return domain





if __name__ == '__main__':
    university_pub()
    ['cs.utexas.edu', 'cs.utexas.edu', 'cs.utexas.edu']
    # print(parse_email('mail.neu.edu.cn'))