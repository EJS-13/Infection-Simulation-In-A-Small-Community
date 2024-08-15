from pymongo import MongoClient
import pandas as pd
import re
import random
import numpy as np

# def get_database():
#     # Provide the mongodb atlas url to connect python to mongodb using pymongo
#     CONNECTION_STRING = "mongodb+srv://khanhdo:N1wEjMrPx5AiHvLK@infectionsimcluster.w1zbgsj.mongodb.net/"
#
#     # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
#     client = MongoClient(CONNECTION_STRING)
#
#     # Create the database for our example (we will use the same database throughout the tutorial
#     return client["infection_db"]
#
#
# def create_collection():
#     dbname = get_database()
#     collection_name = dbname["agent_data"]
#     item_1 = {
#         "_id": "U1IT00001",
#         "item_name": "Blender",
#         "max_discount": "10%",
#         "batch_number": "RR450020FRG",
#         "price": 340,
#         "category": "kitchen appliance"
#     }
#
#     collection_name.insert_one(item_1)
#
# def add_to_database(df, collection_name, database_name="infection_db"):
#     # Connect to Mongodb
#     db = get_database()
#
#     #Convert dataframe to dictionary
#     data = df.to_dict(orient='records')
#
#     # Insert data into collection
#     db[collection_name].insert_many(data)

def add_age_to_df(row, df):

    for i in range(int(row['Total'])):
        pattern = r'\d+'
        matches = re.findall(pattern, row['Characteristic'])
        numbers = [int(match) for match in matches]
        if (len(numbers) == 1):
            new_agent = {'age': random.randint(100, 110)}
        else:
            new_agent = {'age': random.randint(numbers[0],numbers[1])}
        df.loc[len(df)] = new_agent



def add_household_to_df(df, household_distribution, df_homes):
    # Shuffle the household distribution
    np.random.shuffle(household_distribution)

    # Ensure that individuals under 18 are not assigned alone
    df['household_id'] = np.nan
    household_counter = 1

    # Iterate through the household distribution and assign individuals to households
    for household_size in household_distribution:
        indexes_with_nan = df.index[df['household_id'].isna()].tolist()
        if not indexes_with_nan:
            break
        if household_size == 1:
            # If household size is 1, ensure that the individual is not under 18
            indexes_selected = np.random.choice(df.index[(df['age'] >= 18) & (df['household_id'].isna())].tolist(),
                                                size=1, replace=False)
            df.loc[indexes_selected, 'household_id'] = household_counter

            # Add home
            df_apartments = df_homes[df_homes['BuildingUs'].isin(['Townhouse/Apartment/Walk Up - R3', 'Apartments-Elevators - R5'])]
            df.loc[indexes_selected, 'home'] = df_apartments.sample(n=1)['FID'].item()

        else:
            indexes_selected = np.random.choice(indexes_with_nan, size=household_size, replace=False)
            df.loc[indexes_selected, 'household_id'] = household_counter

            # Add home
            df.loc[indexes_selected, 'home'] = df_homes.sample(n=1)['FID'].item()

        household_counter += 1
    return

def get_household_distribution(row, household_distribution):
    pattern = r'\d+'
    matches = re.findall(pattern, row['Characteristic'])
    numbers = [int(match) for match in matches]
    household_distribution += [numbers[0]] * int(row['Total'])

def create_weekday_pattern(row):
    return [row['work/school'], row['work/school'], row['home']]

def create_weekend_pattern(row):
    return [row['home'], row['home'], row['home']]

def create_agent_dataframe():
    """
    Create agent dataframe containing the following columns:
        _id:                unique id for each agent
        age:                integer
        household_id:       integer (agents with the same household_id are in the same family
        weekday_pattern:    agent's schedule in format [morning location, afternoon location, evening location]
        weekend_pattern:    agent's schedule in format [morning location, afternoon location, evening location]
        home:               FID of building that is assigned as home
        work/school:        FID of building that is assigned as work or school

    :return: df
    """
    print("Creating agent database from Canmore census data...")
    df_buildings = pd.read_csv('files/canmore_buildings.csv')
    df_census = pd.read_excel('files/canmore_census_new.xlsx')
    df_census = df_census.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df_census = df_census.dropna(how='all')
    df = pd.DataFrame(columns=['_id', 'age', 'household_id', 'weekday_pattern', 'weekend_pattern', 'home', 'work/school'])

    # add age
    print("Adding age distributions...")
    df_age = df_census[(df_census["Topic"] == "Age characteristics") & (df_census["Characteristic"].str.contains("years"))]
    df_age.apply(add_age_to_df, axis=1, args=(df,))

    # id
    df['_id'] = df.index

    # house buildings
    print("Assigning households and home buildings...")
    df_homes = df_buildings[df_buildings['BuildingUs'].isin(['Single Family Detached - R1', 'Duplex - R2',
                                                             'Townhouse/Apartment/Walk Up - R3',
                                                             'Townhouse/Fourplex - R4',
                                                             'Mobile Home Residential - MHR',
                                                             'Mixed Use - Residential with Service/Retail/Office',
                                                             'Mixed Use - Residential with Visitor Accommodation',
                                                             'Apartments-Elevators - R5'])]

    # add family and home
    household_df = df_census[(df_census['Topic'] == 'Household and dwelling characteristics')
                             & (df_census['Characteristic'].str.contains('|'.join(['1 ', '2 ', '3 ', '4 ', '5 '])))]
    household_distribution = []
    household_df.apply(get_household_distribution, axis=1, args=(household_distribution,))
    add_household_to_df(df, household_distribution, df_homes)
    random_homes = np.random.choice(df_homes['FID'], size=len(df[df['home'].isna()]), replace=True)
    df['home'] = df['home'].fillna(pd.Series(random_homes, index=df.index[df['home'].isnull()]))

    # add school for those 18 and under and add work for those over 18
    print("Assigning schools and workplaces...")
    df_schools = df_buildings[df_buildings['BuildingUs'] == 'School']
    kids_index = df[df['age'] <= 18].index
    random_schools = np.random.choice(df_schools['FID'], size=len(df[df['age'] <= 18]), replace=True)
    school_mapping = dict(zip(kids_index, random_schools))

    df_work = df_buildings[~df_buildings['BuildingCl'].isin(['Residential', 'Transportation/Utilities', 'Duplex - R2'])]
    adults_index = df[df['age'] > 18].index
    random_workplaces = np.random.choice(df_work['FID'], size=len(df[df['age'] > 18]), replace=True)
    work_mapping = dict(zip(adults_index, random_workplaces))

    school_work_mapping = {**school_mapping, **work_mapping}
    df['work/school'] = df.index.map(school_work_mapping)

    # add week patterns
    print("Assigning weekday and weekend patterns...")
    df['weekday_pattern'] = df.apply(lambda row: create_weekday_pattern(row), axis=1)
    df['weekend_pattern'] = df.apply(lambda row: create_weekend_pattern(row), axis=1)

    shuffled_df = df.sample(frac=1).reset_index(drop=True)

    return shuffled_df

if __name__ == "__main__":
    create_agent_dataframe()