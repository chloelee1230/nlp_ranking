from flask import Flask, request, render_template, redirect
import json
from collections import defaultdict
import pandas as pd


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':

        # TODO: change score on screen after submit reweights


        # journal
        CL = float(request.form['CL'])
        TACL = float(request.form['TACL'])

        # conference
        ACL_C = float(request.form['ACL-C'])
        NAACL_C = float(request.form['NAACL-C'])
        EMNLP_C = float(request.form['EMNLP-C'])
        CoNLL_C = float(request.form['CoNLL-C'])
        EACL_C = float(request.form['EACL-C'])
        COLING = float(request.form['COLING'])
        IJCNLP = float(request.form['IJCNLP'])

        # workshop or demo
        ACL_WSD = float(request.form['ACL-WSD'])
        NAACL_WSD = float(request.form['NAACL-WSD'])
        EMNLP_WSD = float(request.form['EMNLP-WSD'])
        CoNLL_WSD = float(request.form['CoNLL-WSD'])
        EACL_WSD = float(request.form['EACL-WSD'])


        # TODO: read selected tag for startYear & endYear (make sure they are int)
        startYear = 2010
        endYear = 2019


        rank = ranking(startYear, endYear,
        CL,TACL,ACL_C,NAACL_C,EMNLP_C,CoNLL_C,EACL_C,COLING,IJCNLP,ACL_WSD,NAACL_WSD,EMNLP_WSD,CoNLL_WSD,EACL_WSD)
        rank.index = rank.index + 1

        return render_template('home.html', tables=[rank.to_html(classes='data')])

    else:

        rank = ranking(2010,2019, 3,3,3,3,3,2,2,2,2,1,1,1,1,1)
        rank.index = rank.index + 1

        return render_template('home.html', tables=[rank.to_html(classes='data')])



def ranking(startYear, endYear,
        CL,TACL,ACL_C,NAACL_C,EMNLP_C,CoNLL_C,EACL_C,COLING,IJCNLP,ACL_WSD,NAACL_WSD,EMNLP_WSD,CoNLL_WSD,EACL_WSD):


    university = pd.read_json('../data-collection/university.json', orient='records')
    bibmap = json.load(open('../data-collection/bibmap.json'))

    venue_pub = {} # only look at publications with authors from an university institution
    for pub_id in [y[0] for x in university['publications'].values.tolist() if x for y in x]:
        venue = find_venue(pub_id)
        if venue in venue_pub.keys():
            venue_pub[venue].append(pub_id)
        else:
            venue_pub[venue] = [pub_id]

    # scoring each venue type
    score = {'journal': 3, 'conference': 3, 'workshop': 1, 'demonstration': 1}


    # authors = {author_id: {2019: {university1_domain: score, university2_domain: score}}}
    authors = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))


    empty = []

    for k,v in venue_pub.items():
        bib = next((y for y in bibmap if y['id'] == k), None)
        with open('../data-collection/pub_json/'+ k+'.json') as p:
            json_file = json.load(p)

            # customized scoring weights
            if 'J' in k:
                venue_score = CL
            elif 'Q' in k:
                venue_score = TACL
            elif 'P' in k and bib['type'] == 'conference':
                venue_score = ACL_C
            elif 'N' in k and bib['type'] == 'conference':
                venue_score = NAACL_C
            elif 'D' in k and bib['type'] == 'conference':
                venue_score = EMNLP_C
            elif 'K' in k and bib['type'] == 'conference':
                venue_score = CoNLL_C
            elif 'E' in k and bib['type'] == 'conference':
                venue_score = EACL_C
            elif 'C' in k:
                venue_score = COLING
            elif 'I' in k:
                venue_score = IJCNLP
            elif 'P' in k and bib['type'] in ['workshop', 'demonstration']:
                venue_score = ACL_WSD
            elif 'N' in k and bib['type'] in ['workshop', 'demonstration']:
                venue_score = NAACL_WSD
            elif 'D' in k and bib['type'] in ['workshop', 'demonstration']:
                venue_score = EMNLP_WSD
            elif 'K' in k and bib['type'] in ['workshop', 'demonstration']:
                venue_score = CoNLL_WSD
            elif 'E' in k and bib['type'] in ['workshop', 'demonstration']:
                venue_score = EACL_WSD
            else:
                venue_score = score[bib['type']]


            for pub in [x for x in json_file if x['id'] in v]:
                for i in range(len(pub['authors'])):
                    if '.edu' in pub['emails'][i]:
                        author_id = pub['author_id'][i]
                        if author_id == '':
                            empty.append(k)
                        year = pub['year']
                        uni_domain = parse_email(pub['emails'][i].split('@')[1])
                        authors[author_id][year][uni_domain] += 1 / len(pub['authors']) * venue_score



    # TODO: add faculty of the institution during the period
    result = {}
    for author, years in authors.items():
        for year, institutions in years.items():
            if int(year) in range(startYear, endYear+1):
                for institution in institutions.items():
                    if institution[0] in result.keys():
                        result[institution[0]] += institution[1]
                    else:
                        result[institution[0]] = institution[1]


    us_universities = pd.read_csv('../data-collection/us_universities.tsv', sep='\t', names=['name', 'domain', 'city', 'state'])

    us_name = dict(zip(us_universities.domain, us_universities.name))

    rank = pd.DataFrame(sorted(list(result.items()), key=lambda x: x[1], reverse=True), columns=['Institution', 'Score'])
    rank = rank[rank['Institution'].isin(us_name.keys())]

    rank = rank.replace({'Institution': us_name})
    rank = rank.round(2)
    rank = rank.reset_index(drop=True)

    # print(rank)

    return rank



def parse_email(domain):
    if '.edu' in domain:
        d = domain.split('.')
        return '.'.join(d[d.index('edu')-1:])
    else:
        return domain


def find_venue(pub_id):
    if 'W' in pub_id:
        return pub_id[:-2]
    else:
        return pub_id[:-3]



if __name__ == '__main__':
    # ranking(2010,2019, 3,3,3,3,3,2,2,2,2,1,1,1,1,1)
    app.run(debug=True, use_debugger=False, use_reloader=False, passthrough_errors=True)