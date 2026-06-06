#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np



# In[2]:


# 1. Load the datasets
df_2021 = pd.read_csv("C:\\Users\\HP\\Downloads\\input_files_for_participants_rpc\\input_files_for_participants_rpc\\data\\tn_2021_results.csv")
df_2021.head(5)


# In[3]:


df_2026 = pd.read_csv("C:\\Users\\HP\\Downloads\\input_files_for_participants_rpc\\input_files_for_participants_rpc\\data\\tn_2026_results.csv")
df_2026.head(5)


# In[4]:


df_master = pd.read_csv("C:\\Users\\HP\\Downloads\\input_files_for_participants_rpc\\input_files_for_participants_rpc\\data\\constituency_master.csv")
df_master.head(5)


# In[5]:


# 2. Print initial shape to verify data
print(f"2021 Data Rows: {df_2021.shape[0]}, 2026 Data Rows: {df_2026.shape[0]}")

# 3. Data Cleaning: Handling the blank 2026 Turnout Column
# Turnout calculate karne ke liye humein total votes per constituency chahiye hota hai,
# Lekin hum baseline ECI target 85.1% turnout state-wide lekar chalenge jaisa brief mein diya hai.
# Chaliye pehle check karte hain columns kya hain:
print("\n2026 Columns:", df_2026.columns.tolist())


# In[6]:


# 2021 State-wide Total Votes per Party
total_votes_2021 = df_2021['votes'].sum()
total_votes_2021


# In[7]:


party_votes_2021 = df_2021.groupby('party')['votes'].sum().reset_index()
party_votes_2021


# In[8]:


party_votes_2021['vote_share_2021_%'] = round((party_votes_2021['votes'] / total_votes_2021) * 100, 2)
party_votes_2021['vote_share_2021_%']


# In[9]:


# 2026 State-wide Total Votes per Party
total_votes_2026 = df_2026['votes'].sum()
total_votes_2026


# In[10]:


party_votes_2026 = df_2026.groupby('party')['votes'].sum().reset_index()
party_votes_2026 


# In[11]:


party_votes_2026['vote_share_2026_%'] = round((party_votes_2026['votes'] / total_votes_2026) * 100, 2)
party_votes_2026['vote_share_2026_%']


# In[12]:


# Merge both years to see the shift
vote_share_comparison = pd.merge(party_votes_2021[['party', 'vote_share_2021_%']], 
                                  party_votes_2026[['party', 'vote_share_2026_%']], 
                                  on='party', how='outer').fillna(0)
vote_share_comparison


# In[13]:


# Calculate the net shift
vote_share_comparison['shift'] = vote_share_comparison['vote_share_2026_%'] - vote_share_comparison['vote_share_2021_%']
vote_share_comparison['shift'] 


# In[14]:


print("\n--- Vote Share Shift (Top Parties) ---")
print(vote_share_comparison.sort_values(by='vote_share_2026_%', ascending=False).head(6))


# In[20]:


# Function to calculate margins for a given dataframe
def calculate_constituency_margins(df, year):
    # Sort by constituency and votes descending
    df_sorted = df.sort_values(by=['ac_number', 'votes'], ascending=[True, False])
    
    # Get Winner (Top 1) and Runner-up (Top 2)
    top_2 = df_sorted.groupby('ac_number').head(2).copy()
    
    # Assign rank within group
    top_2['rank'] = top_2.groupby('ac_number').cumcount() + 1
    
    # Pivot to get winner and runner up in same row
    winners = top_2[top_2['rank'] == 1][['ac_number', 'constituency', 'party', 'votes', 'region']].rename(columns={'party':'winner_party', 'votes':'winner_votes'})
    runners = top_2[top_2['rank'] == 2][['ac_number', 'party', 'votes']].rename(columns={'party':'runner_party', 'votes':'runner_votes'})
    
    margin_df = pd.merge(winners, runners, on='ac_number')
    margin_df['margin_votes'] = margin_df['winner_votes'] - margin_df['runner_votes']
    
    # Total votes in that constituency to find margin percentage
    total_ac_votes = df.groupby('ac_number')['votes'].sum().reset_index().rename(columns={'votes':'total_constituency_votes'})
    margin_df = pd.merge(margin_df, total_ac_votes, on='ac_number')
    margin_df['margin_percentage'] = round((margin_df['margin_votes'] / margin_df['total_constituency_votes']) * 100, 2)
    margin_df['year'] = year
    return margin_df

margin_2021 = calculate_constituency_margins(df_2021, 2021)
margin_2026 = calculate_constituency_margins(df_2026, 2026)

print("\n--- Average Margin of Victory Comparison ---")
print(f"2021 Average Margin %: {margin_2021['margin_percentage'].mean():.2f}%")
print(f"2026 Average Margin %: {margin_2026['margin_percentage'].mean():.2f}%")


# In[24]:


# 1. 2021 ke constituency-wise turnout ko nikalna
turnout_2021 = df_2021.groupby(['ac_number', 'constituency'])['turnout'].first().reset_index()
turnout_2021


# In[25]:


turnout_2021.rename(columns={'turnout': 'turnout_2021'}, inplace=True)



# In[26]:


# 2. 2026 ke turnout ko calculate karna
# Formula: (Total Votes Polled in Constituency / State Avg Adjuster) ya phir directly ECI base models.
# Kyunki exact total voters array missing hai, hum total votes ka growth base nikalenge:
total_v_2021 = df_2021.groupby('ac_number')['votes'].sum().reset_index().rename(columns={'votes':'votes_2021'})
total_v_2021


# In[27]:


total_v_2026 = df_2026.groupby('ac_number')['votes'].sum().reset_index().rename(columns={'votes':'votes_2026'})
total_v_2026


# In[28]:


turnout_growth = pd.merge(total_v_2021, total_v_2026, on='ac_number')
turnout_growth


# In[29]:


turnout_growth = pd.merge(turnout_growth, turnout_2021, on='ac_number')
turnout_growth


# In[30]:


# 2026 turnout proxy estimation based on 85.1% state benchmark adjustment
turnout_growth['turnout_2026'] = round(turnout_growth['turnout_2021'] * (turnout_growth['votes_2026'] / turnout_growth['votes_2021'] * 0.93), 2)
turnout_growth['turnout_2026'] 


# In[31]:


# Ensure data cap logic doesn't exceed practical limits, bounded around historical highs
turnout_growth['turnout_2026'] = turnout_growth['turnout_2026'].apply(lambda x: min(x, 96.5))
turnout_growth['turnout_2026']


# In[32]:


# Calculate absolute increase in turnout percentage points
turnout_growth['turnout_increase'] = round(turnout_growth['turnout_2026'] - turnout_growth['turnout_2021'], 2)
turnout_growth['turnout_increase'] 


# In[33]:


# Merge with master to get regions
turnout_final = pd.merge(turnout_growth, df_master[['ac_number', 'region']], on='ac_number')
turnout_final


# In[34]:


print("\n--- 📈 TOP 5 CONSTITUENCIES WITH HIGHEST TURNOUT INCREASE ---")
print(turnout_final.sort_values(by='turnout_increase', ascending=False).head(5)[['constituency', 'region', 'turnout_2021', 'turnout_2026', 'turnout_increase']])



# In[35]:


print("\n--- 🗺️ REGIONAL TURNOUT INCREASE AVERAGE ---")
print(turnout_final.groupby('region')['turnout_increase'].mean().reset_index().sort_values(by='turnout_increase', ascending=False))


# In[ ]:




