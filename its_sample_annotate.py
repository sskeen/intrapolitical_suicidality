# -*- coding: utf-8 -*-
"""its_sample_annotate.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/19tiLKQYztn3aO9JUSptMh6MU8qtDVoHb

## ‘What Destroys a Person When that Person Appears to Be Destroying Himself?’

_Imports, re-indexes by date, cleans, reduces, restricts by timeframe; permits regex pattern-matched purposive (Wave 1) and random (Wave 2) sampling and named entity redaction of PushShift .gzip Reddit archives for .xlsx annotation. Computes Cohen's $\kappa$ post-annotation. Prepares training dataset for annotation post-IAA._

> its_sample_annotate_iaa.ipynb<br>
> Simone J. Skeen (07-20-2024)

1. [Prepare](#scrollTo=lVsJPtzvMeX6)
2. [Pre-annotation](#scrollTo=a629e1bc)
3. [Post-annotation](#scrollTo=f0f0da81-88a0-4c6d-976e-fca33d9ba44e)

### 1. Prepare
Installs, imports, and downloads requisite models and packages.
***
"""

# Commented out IPython magic to ensure Python compatibility.
#%%capture

# %pip install irrCAC

#%pip install openai
#%pip install --upgrade openai

# %python -m spacy download en_core_web_lg --user

# Import + calibrate

import gzip
import json
import numpy as np
import os
import pandas as pd
import random
import re
import spacy
import warnings

from collections import Counter
from irrCAC.raw import CAC
from sklearn.metrics import cohen_kappa_score

spacy.cli.download('en_core_web_lg')

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = 'all'

pd.set_option(
              'display.max_columns',
              None,
              )
pd.set_option(
              'display.max_rows',
              None,
              )

warnings.simplefilter(
                      action = 'ignore',
                      category = FutureWarning,
                      )

#!python -m prodigy stats

drive.mount(
            '/content/gdrive/',
            force_remount = True,
            )

"""### 2. Pre-annotation
Cleans Pushshift archives, samples via PB- and TB-informed regex.
***
"""

# Tap archives

os.chdir('<my_dir>')
#%pwd

# Import _posts_

wd = '<my_dir>/sw_complete-posts.json.gz'
d = pd.DataFrame(json.loads(l) for l in gzip.open(wd, 'rb'))

d = d.drop_duplicates(subset = 'id')

# Index by post date

d['date'] = pd.to_datetime(
                           d.created_utc,
                           unit = 's',
                           )

d.set_index(
            'date',
            drop = False,
            inplace = True,
            )

# Inspect - as needed

#d.resample('1M').subreddit.count().plot()
#d.shape ### N = 874,269
#print(d.columns.tolist())
#d.dtypes
#d.head(3)
#d.tail(3)

# Reduce

d = d[[
       'author',
       'created_utc',
       'date',
       'id',
       'num_comments',
       'selftext',
       'subreddit',
       'title',
       ]].copy()

# Rename

d.rename(
         columns = {
                    'author': 'p_au',
                    'created_utc': 'p_utc',
                    'date': 'p_date',
                    'id': 'p_id',
                    'num_comments': 'n_cmnt',
                    'selftext': 'text',
                    'subreddit': 'subrddt',
                    'title': 'p_titl',
                    }, inplace = True,
        )

# Incl target sub/constructs, rationale cols

d = d.assign(
             lone = ' ',     ### loneliness
             recp = ' ',     ### nonreciprocity
             tb = ' ',       ### thwarted belonginess (TB)
             tb_rtnl = ' ',  ### TB rationale
             hate = ' ',     ### self-hatred
             libl = ' ',     ### liability
             pb = ' ',       ### perceived burdensomeness (PB)
             pb_rtnl = ' ',  ### PB rationale
             lgth = ' ',     ### log excess length/brevity
             )

# Drop user deletions

d = d[~d['text'].isin(['[deleted]', '[removed]'])]

# Verify

d.shape ### n = 458,118
d.head(3)
d.tail(3)
print(d.columns.tolist())

# Purposive sample: PB

'burden\S*' ### a priori/canonical
'unwanted\S*|useless\S*|nuisance|leech\S*|parasit\S*|piece of shit|hate myself' ### inductively derived

pb = re.compile('burden\S*|unwanted\S*|useless\S*|nuisance|leech\S*|parasit\S*|piece of shit|hate myself', re.I)

d_pb = d.loc[
             d['text'].str.contains(
                                    pb,
                                    regex = True,
                                    )
            ]

# Prevalence

d_pb.shape ### n = 54,335

# Anonymize + export subsample: PB

d_pb = d_pb.sample(400)

# Redact w/ EntityRecognizer

nlp = spacy.load('en_core_web_lg')

# Define Fx

def redact(p_text):
    ne = list(
              [
               'PERSON',   ### people, including fictional
               'NORP',     ### nationalities or religious or political groups
               'FAC',      ### buildings, airports, highways, bridges, etc.
               'ORG',      ### companies, agencies, institutions, etc.
               #'GPE',     ### countries, cities, states
               'LOC',      ### non-GPE locations, mountain ranges, bodies of water
               'PRODUCT',  ### objects, vehicles, foods, etc. (not services)
               'EVENT',    ### named hurricanes, battles, wars, sports events, etc.
               ]
                )

    doc = nlp(p_text)
    ne_to_remove = []
    final_string = str(p_text)
    for sent in doc.ents:
        if sent.label_ in ne:
            ne_to_remove.append(str(sent.text))
    for n in range(len(ne_to_remove)):
        final_string = final_string.replace(
                                            ne_to_remove[n],
                                            '<|PII|>',
                                            )
    return final_string

# Redact

d_pb['text'] = d_pb['text'].astype(str).apply(lambda i: redact(i))

# Export

d_pb.to_excel('d_pb_annotate.xlsx')

# Purposive sample: TB

'.lone\S*|isolat\S*' ### a priori/canonical
'withdraw\S*|alienat\S*|ostrac\S*|shun\S*|abandon\S*|reject\S*' ### inductively derived

tb = re.compile('.lone\S*|isolat\S*|withdraw\S*|alienat\S*|ostrac\S*|shun\S*|abandon\S*|reject\S*', re.I)

d_tb = d.loc[
             d['text'].str.contains(
                                    tb,
                                    regex = True,
                                    )
            ]

# Prevalence

d_tb.shape ### n = 87,657

# Anonymize + export subsample: TB

d_tb = d_tb.sample(400)

# Redact

d_tb['text'] = d_tb['text'].astype(str).apply(lambda i: redact(i))

# Export

d_tb.to_excel('d_tb_annotate.xlsx')

"""### 3. Post-annotation
Computes Cohen's $\kappa$ cycle x sub/construct to assess IAA. Post-IAA, merges and strctures $\mathcal{d}$<sub>annotated</sub>.
***

#### Compute IAA
"""

# Import annotated data

os.chdir('<my_dir>')
#%pwd

lc = '<my_dir>/d_cycle*_lc.xlsx' ### * = annotation cycle; lc = LMC
d_lc = pd.read_excel(lc)
#d_lc.dtypes

d_lc = d_lc.replace(' ', 0)
d_lc.columns = [f'{col}_lc' for col in d_lc.columns]

ss = '<my_dir>/d_cycle*_ss.xlsx' ### * = annotation cycle; ss = SJS
d_ss = pd.read_excel(ss)

d_ss = d_ss.replace(' ', 0)
d_ss.columns = [f'{col}_ss' for col in d_ss.columns]

# Inspect

#d_lc.head(3)
#d_ss.head(3)

# Merge

iaa = pd.merge(
               d_lc,
               d_ss,
               left_index = True,
               right_index = True,
               )

targets = [
           'lone_lc',
           'lone_ss',
           'recp_lc',
           'recp_ss',
           'tb_lc',
           'tb_ss',
           'hate_lc',
           'hate_ss',
           'libl_lc',
           'libl_ss',
           'pb_lc',
           'pb_ss',
           ]

iaa = iaa[targets].copy()

# IAA

'Cohen K: Self-hatred (hate)'
hate_lc = iaa['hate_lc'].to_numpy()
hate_ss = iaa['hate_ss'].to_numpy()

cohen_kappa_score(hate_lc, hate_ss)

'Cohen K: Liability (libl)'
libl_lc = iaa['libl_lc'].to_numpy()
libl_ss = iaa['libl_ss'].to_numpy()

cohen_kappa_score(libl_lc, libl_ss)

'Cohen K: PB (pb)'
pb_lc = iaa['pb_lc'].to_numpy()
pb_ss = iaa['pb_ss'].to_numpy()

cohen_kappa_score(pb_lc, pb_ss)

'Cohen K: Loneliness (lone)'
lone_lc = iaa['lone_lc'].to_numpy()
lone_ss = iaa['lone_ss'].to_numpy()

cohen_kappa_score(lone_lc, lone_ss)

'Cohen K: Nonreciprocity (recp)'
recp_lc = iaa['recp_lc'].to_numpy()
recp_ss = iaa['recp_ss'].to_numpy()

cohen_kappa_score(recp_lc, recp_ss)

'Cohen K: TB (tb)'
tb_lc = iaa['tb_lc'].to_numpy()
tb_ss = iaa['tb_ss'].to_numpy()

cohen_kappa_score(tb_lc, tb_ss)

"""#### Build: $\mathcal{d}$<sub>annotated</sub>

"""

# Import + calibrate

import gzip
import json
import numpy as np
import os
import pandas as pd
import re
import warnings

from IPython.core.interactiveshell import InteractiveShell
InteractiveShell.ast_node_interactivity = 'all'

pd.set_option('display.max_columns', None)

# Tap TB cycle w/ IAA benchmark achieved

wd_tb = 'C:/Users/sskee/OneDrive/Documents/02_tulane/01_research/tu_ceai/its/submissions/01_savir/data/tb_crosswalk 150+negotiated.xlsx'
d_tb = pd.read_excel(wd_tb)

d_tb.fillna(
            0,
            inplace = True,
            )

# Inspect

d_tb.dtypes
d_tb.head(3)
print(d_tb.columns.tolist())

# Transform id of already-annotated posts to NumPy array

tb_drop = d_tb['id'].to_numpy()
print(tb_drop)



# Shape TB purposive annotation set

os.chdir('<my_dir>')
#%pwd

# Import _posts_

wd = '<my_dir>/sw_complete-posts.json.gz'
d = pd.DataFrame(json.loads(l) for l in gzip.open(wd, 'rb'))

d = d.drop_duplicates(subset = 'id')

# Index by post date

d['date'] = pd.to_datetime(
                           d.created_utc,
                           unit = 's',
                           )

d.set_index(
            'date',
            drop = False,
            inplace = True,
            )

# Reduce

d = d[[
       'author',
       'created_utc',
       'date',
       'id',
       'num_comments',
       'selftext',
       'subreddit',
       'title',
       ]].copy()

# Rename

d.rename(
         columns = {
                    'author': 'p_au',
                    'created_utc': 'p_utc',
                    'date': 'p_date',
                    'id': 'p_id',
                    'num_comments': 'n_cmnt',
                    'selftext': 'text',
                    'subreddit': 'subrddt',
                    'title': 'p_titl',
                    }, inplace = True,
        )

# Incl target sub/constructs, rationale cols

d = d.assign(
             lone = ' ',     ### loneliness
             recp = ' ',     ### nonreciprocity
             tb = ' ',       ### thwarted belonginess (TB)
             tb_rtnl = ' ',  ### TB rationale
             hate = ' ',     ### self-hatred
             libl = ' ',     ### liability
             pb = ' ',       ### perceived burdensomeness (PB)
             pb_rtnl = ' ',  ### PB rationale
             lgth = ' ',     ### log excess length/brevity
             )

# Drop user deletions

d = d[~d['text'].isin(['[deleted]', '[removed]'])]

# Random sample

rnd_antt = d.sample(500)

# Purposive sample: TB

'.lone\S*|isolat\S*' ### a priori/canonical
'withdraw\S*|alienat\S*|ostrac\S*|shun\S*|abandon\S*|reject\S*' ### inductively derived

tb = re.compile('.lone\S*|isolat\S*|withdraw\S*|alienat\S*|ostrac\S*|shun\S*|abandon\S*|reject\S*', re.I)

d_tb = d.loc[
             d['text'].str.contains(
                                    tb,
                                    regex = True,
                                    )
            ]

# Prevalence

d_tb.shape ### n = 87,657

# Drop already-annotated n = 50

drop = d_tb['id'].isin(tb_drop)
d_tb = d_tb[~drop]

# Random subset, n = 450

tb_antt = d_tb.sample(450)
tb_antt.count()

# Redact

rnd_antt['text'] = rnd_antt['text'].astype(str).apply(lambda i: redact(i))

tb_antt['text'] = tb_antt['text'].astype(str).apply(lambda i: redact(i))

# Tap PB cycle w/ IAA benchmark achieved

wd_pb = 'C:/Users/sskee/OneDrive/Documents/02_tulane/01_research/tu_ceai/its/submissions/01_savir/data/pb_crosswalk 150+negotiated.xlsx'
d_pb = pd.read_excel(wd_pb)

d_pb.fillna(
            0,
            inplace = True,
            )

# Inspect

d_pb.dtypes
d_pb.head(3)
print(d_pb.columns.tolist())

# Transform id of already-annotated posts to NumPy array

pb_drop = d_pb['id'].to_numpy()
print(pb_drop)

# Shape PB purposive annotation set

os.chdir('<my_dir>')
#%pwd

# Import _posts_

wd = '<my_dir>/sw_complete-posts.json.gz'
d = pd.DataFrame(json.loads(l) for l in gzip.open(wd, 'rb'))

d = d.drop_duplicates(subset = 'id')

# Index by post date

d['date'] = pd.to_datetime(
                           d.created_utc,
                           unit = 's',
                           )

d.set_index(
            'date',
            drop = False,
            inplace = True,
            )

# Reduce

d = d[[
       'author',
       'created_utc',
       'date',
       'id',
       'num_comments',
       'selftext',
       'subreddit',
       'title',
       ]].copy()

# Rename

d.rename(
         columns = {
                    'author': 'p_au',
                    'created_utc': 'p_utc',
                    'date': 'p_date',
                    'id': 'p_id',
                    'num_comments': 'n_cmnt',
                    'selftext': 'text',
                    'subreddit': 'subrddt',
                    'title': 'p_titl',
                    }, inplace = True,
        )

# Incl target sub/constructs, rationale cols

d = d.assign(
             lone = ' ',     ### loneliness
             recp = ' ',     ### nonreciprocity
             tb = ' ',       ### thwarted belonginess (TB)
             tb_rtnl = ' ',  ### TB rationale
             hate = ' ',     ### self-hatred
             libl = ' ',     ### liability
             pb = ' ',       ### perceived burdensomeness (PB)
             pb_rtnl = ' ',  ### PB rationale
             lgth = ' ',     ### log excess length/brevity
             )

# Drop user deletions

d = d[~d['text'].isin(['[deleted]', '[removed]'])]

# Purposive sample: PB

'burden\S*' ### a priori/canonical
'unwanted\S*|useless\S*|nuisance|leech\S*|parasit\S*|piece of shit|hate myself' ### inductively derived

pb = re.compile('burden\S*|unwanted\S*|useless\S*|nuisance|leech\S*|parasit\S*|piece of shit|hate myself', re.I)

d_pb = d.loc[
             d['text'].str.contains(
                                    pb,
                                    regex = True,
                                    )
            ]

# Prevalence

d_pb.shape ### n = 54,335

# Drop already-annotated n = 50

drop = d_pb['id'].isin(pb_drop)
d_pb = d_pb[~drop]

# Random subset, n = 450

pb_antt = d_pb.sample(450)
pb_antt.count()

# Redact

pb_antt['text'] = pb_antt['text'].astype(str).apply(lambda i: redact(i))

# Append: PB, TB, rnd + IAA annotation benchmark cycle

its_annotate = pd.concat(
                         [
                          pb_antt,  ### PB, regex/purposive
                          tb_antt,  ### TB, regex/purposive
                          rnd_antt, ### random subsample
                          d_cycle3_pb,  ### n = 50 cycle, IAA achieved: PB
                          d_cycle3_tb,  ### n = 50 cycle, IAA achieved: TB
                          ], ignore_index = True,
                         )

"""> End of its_sample_annotate_iaa.ipynb (07-20-2024)"""