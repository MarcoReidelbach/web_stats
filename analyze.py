import pandas as pd

# Load Data
month_old="04"
month_new="05"
year = "2025"

# 'Remove' lists User that don't want to appear in the statistics, stored in external remove file
try:
    with open("remove", "r", encoding="utf-8") as f:
        Remove = [line.strip() for line in f if line.strip()]
except FileNotFoundError:
    print("Warning: 'remove' not found. No users will be removed.")
    Remove = []

top=100

dold = pd.read_pickle(f"raw_data/01.{month_old}.{year}.pkl")
dnew = pd.read_pickle(f"raw_data/01.{month_new}.{year}.pkl")

rgiven = pd.read_pickle(f"raw_data/{month_old}.{year}_RG.pkl") 

# Remove 'Not Defined' Users aka Users without Posts and Reactions
dold=dold[dold['User Name'] != 'Not Defined']
dnew=dnew[dnew['User Name'] != 'Not Defined']

dold=dold[dold['User ID'] != 'Not Defined']
dnew=dnew[dnew['User ID'] != 'Not Defined']

# Data Type Stuff
dold['Number of Posts']=dold['Number of Posts'].astype(str).str.replace('.', '',regex=False).astype(int)
dnew['Number of Posts']=dnew['Number of Posts'].astype(str).str.replace('.', '',regex=False).astype(int)

dold['Number of Reactions']=dold['Number of Reactions'].astype(str).str.replace('.', '',regex=False).astype(int)
dnew['Number of Reactions']=dnew['Number of Reactions'].astype(str).str.replace('.', '',regex=False).astype(int) 

dold['Number of Trophies']=dold['Number of Trophies'].astype(str).str.replace('.', '',regex=False).astype(int)
dnew['Number of Trophies']=dnew['Number of Trophies'].astype(str).str.replace('.', '',regex=False).astype(int)

# Total Number of Posts/Reactions and total number of Users with Posts/Reactions
usr_with_posting=dnew["Number of Posts"][dnew["Number of Posts"]>0].count()
number_of_posts=dnew["Number of Posts"][dnew["Number of Posts"]>0].sum()

usr_with_posting_old=dold["Number of Posts"][dold["Number of Posts"]>0].count()

usr_with_reaction=dnew['Number of Reactions'][dnew['Number of Reactions']>0].count()
number_of_reactions=dnew['Number of Reactions'][dnew['Number of Reactions']>0].sum() 

# Total Number Trophies
usr_with_trophies=dnew["Number of Trophies"][dnew["Number of Trophies"]>0].count()
number_of_trophies=dnew["Number of Trophies"][dnew["Number of Trophies"]>0].sum()

number_of_trophies_old=dold["Number of Trophies"][dold["Number of Trophies"]>0].sum()

# Total Number of Posts/Reactions/Profile Visits per User
post_total=dnew.sort_values('Number of Posts',ascending=False).reset_index()
reaction_total=dnew.sort_values('Number of Reactions',ascending=False).reset_index()

post_total_old=dold.sort_values('Number of Posts',ascending=False).reset_index()
reaction_total_old=dold.sort_values('Number of Reactions',ascending=False).reset_index()

# New Post/Reaction in period per User (merge User IDs, Names and Number of Posts/Reactions from dnew and dold with respect to User IDs, 
# User IDs missing in dnew (aka deleted User) / dold (aka new User), get a 0 as new/old post/reaction number. Add another column containing difference between new and old posts/reactions.
# Sort the dataframe from high to low change and reset the index.
post_change=pd.merge(dnew[['User ID','User Name','Number of Posts']].rename(columns={'Number of Posts': 'NoP_new','User Name': 'User Name new'}),
                     dold[['User ID','User Name','Number of Posts']].rename(columns={'Number of Posts': 'NoP_old','User Name': 'User Name old'}), on='User ID', how='outer')
post_change['NoP_old']=post_change['NoP_old'].fillna(0)
post_change=post_change.eval('Change = NoP_new - NoP_old').sort_values('Change',ascending=False).reset_index()

reaction_change=pd.merge(dnew[['User ID','User Name','Number of Reactions']].rename(columns={'Number of Reactions': 'NoR_new','User Name': 'User Name new'}),
                         dold[['User ID','User Name','Number of Reactions']].rename(columns={'Number of Reactions': 'NoR_old','User Name': 'User Name old'}), on='User ID', how='outer')
reaction_change['NoR_old']=reaction_change['NoR_old'].fillna(0)
reaction_change=reaction_change.eval('Change = NoR_new - NoR_old').sort_values('Change',ascending=False).reset_index()

rgiven_sorted = rgiven.set_index('User ID').loc[reaction_change['User ID'].head(100)].reset_index()

# Number of posts/reactions per User in period
usr_with_posting_in_period=post_change['Change'][post_change['Change']>0].count()
number_of_posts_in_period=int(post_change['Change'][post_change['Change']>0].sum())

usr_with_reaction_in_period=reaction_change['Change'][reaction_change['Change']>0].count()
number_of_reactions_in_period=int(reaction_change['Change'][reaction_change['Change']>0].sum())

# Remove Users which do not want to be listed
post_change=post_change[~post_change['User ID'].isin(Remove)].reset_index()
post_total=post_total[~post_total['User ID'].isin(Remove)].reset_index()
post_total_old=post_total_old[~post_total_old['User ID'].isin(Remove)].reset_index()
reaction_change=reaction_change[~reaction_change['User ID'].isin(Remove)].reset_index()
reaction_total=reaction_total[~reaction_total['User ID'].isin(Remove)].reset_index()
reaction_total_old=reaction_total_old[~reaction_total_old['User ID'].isin(Remove)].reset_index()

print(
"""Die aktuellen Userstatistiken.

Vorab: Ab diesem Monat gibt es unabhängig von der Spendensumme nur noch die jeweiligen Top 100s.

Abgefragt wird der Zeitraum vom 01."""+month_old+"""."""+year+""" bis zum 01."""+month_new+"""."""+year+""".

Es gibt insgesamt """+f'{usr_with_posting:,}'.replace(',','.')+""" User mit Postings, diesen Monat haben davon """+f'{usr_with_posting_in_period:,}'.replace(",",".")+""" User gepostet.
Wir haben in unserer Datenbank insgesamt """+ f'{number_of_posts:,}'.replace(",",".")+""" Postings, davon wurden in diesem Monat """+f'{number_of_posts_in_period:,}'.replace(",",".")+""" abgegeben.

Hier die Top Poster des Tages:

INSERT TOP POSTER


Hier die Top """+str(top)+""" aus diesem Monat:
""")

count=0
for i in range(top):
    num=int(post_change.at[i,'Change'])
    # Same rank for users with identical numbers
    if i>0:
        num_old=int(post_change.at[i-1,'Change'])
        if num==num_old:
            I=i+1-(1+count)
            count+=1
        else:
            I=i+1
            count=0
    else:
        I=i+1
    print(str(I)+'. '+post_change.at[i,'User Name new']+' - '+f'{num:,}'.replace(",","."))

print(
'''
Hier die Top '''+str(top)+''' insgesamt:
''')

count=0
for i in range(top):
    num=int(post_total.at[i,'Number of Posts'])
    # Same rank for users with identical numbers
    if i>0:
        num_old=int(post_total.at[i-1,'Number of Posts'])
        if num==num_old:
            I=i+1-(1+count)
            count+=1
        else:
            I=i+1
            count=0
    else:
        I=i+1
    # Check if User in Top changed positions, only show actual changes (+/-), if new registered User enters Top write (New) 
    try:
        ind=post_total_old[post_total_old['User ID']==post_total.at[i,'User ID']].index.values.astype(int)[0]
        if ind==i:
            rank_change=''
        elif ind>i:
            rank_change='(+'+str(ind-i)+')'
        elif ind<i:
            rank_change='(-'+str(i-ind)+')'
    except:
        rank_change='(New)'
    print(str(I)+'. '+post_total.at[i,'User Name']+' - '+f'{num:,}'.replace(",",".")+' '+rank_change)

print(
"""

Es gibt insgesamt """+f'{usr_with_reaction:,}'.replace(",",".")+""" User, die Reaktionen erhalten haben. Diesen Monat haben davon """+f'{usr_with_reaction_in_period:,}'.replace(",",".")+""" User Reaktionen erhalten.
Wir haben in unserer Datenbank insgesamt """+ f'{number_of_reactions:,}'.replace(",",".")+""" Reaktionen, davon wurden in diesem Monat """+f'{number_of_reactions_in_period:,}'.replace(",",".")+""" abgegeben.

Hier die Top """+str(top)+""" aus diesem Monat (in Klammern zusätzlich die Anzahl an vergebenen Reaktionen):
""")

count=0
for i in range(top):
    num=int(reaction_change.at[i,'Change'])
    rea=rgiven_sorted.at[i,'Given Reaction']
    # Same rank for users with identical numbers
    if i>0:
        num_old=int(reaction_change.at[i-1,'Change'])
        if num==num_old:
            I=i+1-(1+count)
            count+=1
        else:
            I=i+1
            count=0
    else:
        I=i+1
    print(str(I)+'. '+reaction_change.at[i,'User Name new']+' - '+f'{num:,}'.replace(",",".")+f' ({rea})')

print(
'''
Hier die Top '''+str(top)+''' insgesamt:
''')

count=0
for i in range(top):
    num=int(reaction_total.at[i,'Number of Reactions'])
    # Same rank for users with identical numbers
    if i>0:
        num_old=int(reaction_total.at[i-1,'Number of Reactions'])
        if num==num_old:
            I=i+1-(1+count)
            count+=1
        else:
            I=i+1
            count=0
    else:
        I=i+1
    # Check if User in Top changed positions, only show actual changes (+/-), if new registered User enter Top write (New)
    try:
        ind=reaction_total_old[reaction_total_old['User ID']==reaction_total.at[i,'User ID']].index.values.astype(int)[0]
        if ind==i:
            rank_change=''
        elif ind>i:
            rank_change='(+'+str(ind-i)+')'
        elif ind<i:
            rank_change='(-'+str(i-ind)+')'
    except:
        rank_change='(New)'
    print(str(I)+'. '+reaction_total.at[i,'User Name']+' - '+f'{num:,}'.replace(",",".")+' '+rank_change)

print(
'''

Und hier noch ein paar Rahmendaten:

User mit Postings insgesamt: '''+f'{usr_with_posting:,}'.replace(",",".")+'''
User mit Postings im Zeitraum: '''+f'{usr_with_posting_in_period:,}'.replace(",",".")+'''
User mit ihren ersten Beiträgen in diesem Monat: '''+f'{usr_with_posting-usr_with_posting_old:,}'.replace(",",".")+'''
Postings insgesamt: '''+f'{number_of_posts:,}'.replace(",",".")+'''
Postings insgesamt im Zeitraum: '''+f'{number_of_posts_in_period:,}'.replace(",",".")+'''
Reaktionen insgesamt: '''+f'{number_of_reactions:,}'.replace(",",".")+'''
Reaktionen insgesamt im Zeitraum: '''+f'{number_of_reactions_in_period:,}'.replace(",",".")+'''
User mit Trophäen: '''+f'{usr_with_trophies:,}'.replace(",",".")+'''
Trophäen insgesamt: '''+f'{number_of_trophies:,}'.replace(",",".")+'''
Trophäen insgesamt im Zeitraum: '''+f'{number_of_trophies-number_of_trophies_old:,}'.replace(",",".")+'''



Solltet ihr Fehler / Unstimmigkeiten finden oder nicht namentlich in den Listen auftauchen wollen, meldet euch bei uns.

Danke für's Lesen :)''')





