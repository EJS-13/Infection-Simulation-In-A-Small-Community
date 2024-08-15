import random

import mesa
import mesa_geo as mg
from shapely.geometry import Point

from agent import DistrictAgent, CitizenAgent

class TimeScheduler(mesa.time.BaseScheduler):
    def __init__(self, model):
        super().__init__(model)
        self.days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.time_periods = ["Morning", "Afternoon", "Evening"]
        self.current_day = 0
        self.current_time = 0


    def step(self):
        # Increment current time and cycle if needed
        self.current_time = (self.current_time + 1) % len(self.time_periods)
        if self.current_time == 0:
            self.current_day = (self.current_day + 1) % len(self.days_of_week)

        # Perform actions for the current time period
        for agent in self.agents:
            agent.step()


    def current_day_of_week(self):
        return self.days_of_week[self.current_day]

    def current_time_period(self):
        return self.time_periods[self.current_time]


class InfectionModel(mesa.Model):

    # Geographical parameters
    geojson_regions = "files/shapefiles/Canmore_Land_Use_Districts.geojson"
    geojson_buildings = "files/shapefiles/Canmore_Building_Footprints.geojson"
    unique_id = "FID"

    def __init__(self, num_agents, infection_risk_close, infection_risk_stranger, exposure_distance, incubation_period,
                 infection_duration, starting_infected_individuals, agent_database, disease):

        self.schedule = TimeScheduler(self)
        self.space = mg.GeoSpace(warn_crs_conversion=False)

        # SEIR model
        self.num_agents = num_agents
        self.starting_infected_individuals = starting_infected_individuals
        self.counts = None
        self.reset_counts()
        self.counts['susceptible'] = num_agents

        self.running = True

        self.datacollector = mesa.DataCollector(
            {
                "susceptible": get_susceptible_count,
                "exposed": get_exposed_count,
                "infected": get_infected_count,
                "recovered": get_recovered_count,
            }
        )

        # Set disease parameters based on inputted disease
        if disease == 'Measles':
            self.incubation_period = 10             # days
            self.infection_duration = 8             # days
            self.infection_risk_close = 0.9 * 7.5    # percent (same household infection rate is 5-10x (avg. 7.5x) more likely)
            self.infection_risk_stranger = 0.9       # percent
            self.exposure_distance = 100
        elif disease == 'COVID-19':
            self.incubation_period = 11             # days
            self.infection_duration = 15            # days
            self.infection_risk_close = 0.2 * 7.5    # percent (same household infection rate is 5-10x (avg. 7.5x) more likely)
            self.infection_risk_stranger = 0.2       # percent
            self.exposure_distance = 100
        elif disease == 'Influenza':
            self.incubation_period = 2              # days
            self.infection_duration = 5             # days
            self.infection_risk_close = 0.073 * 7.5   # percent (same household infection rate is 5-10x (avg. 7.5x) more likely)
            self.infection_risk_stranger = 0.073      # percent
            self.exposure_distance = 100
        # else use custom parameters set in server.py

        # Set up district patches for every district in file
        ac = mg.AgentCreator(DistrictAgent, model=self)
        district_agents = ac.from_file(
            self.geojson_regions, unique_id=self.unique_id
        )
        self.space.add_agents(district_agents)

        # Set up buildings
        building_agents = ac.from_file(
            self.geojson_buildings, unique_id=self.unique_id
        )
        self.building_agents = building_agents
        self.space.add_agents(building_agents)

        # Create CitizenAgents
        if agent_database is None:
            ac_population = mg.AgentCreator(
                CitizenAgent,
                model=self,
                crs=self.space.crs,
                agent_kwargs={"weekday_pattern": ["school", 'school', 'home'], "weekend_pattern": ["home", "home", "home"], 'household_id': None, 'home': None, 'work_school': None},
            )

            # Generate a random location, add agent to grid
            for i in range(num_agents):  #Healthy Individuals/susceptible
                this_district = self.random.randint(0, len(district_agents) - 1)  # Region where agent starts
                center_x, center_y = district_agents[this_district].geometry.centroid.coords.xy
                this_bounds = district_agents[this_district].geometry.bounds
                spread_x = int(this_bounds[2] - this_bounds[0])  # Heuristic for agent spread in region
                spread_y = int(this_bounds[3] - this_bounds[1])
                this_x = center_x[0] + self.random.randint(0, spread_x) - spread_x / 2
                this_y = center_y[0] + self.random.randint(0, spread_y) - spread_y / 2
                this_person = ac_population.create_agent(Point(this_x, this_y), "P" + str(i))
                print("x" + str(this_x))
                print("y" + str(this_y))
                # Add to grid and schedule
                self.space.add_agents(this_person)
                self.schedule.add(this_person)

        else:
            # Randomly pick infected individuals
            random_infected_indices = random.sample(range(num_agents), starting_infected_individuals)
            self.counts["infected"] += len(random_infected_indices)
            self.counts["susceptible"] -= len(random_infected_indices)

            for index, row in agent_database.iterrows():
                if index >= num_agents:
                    break

                # Get location of home
                building_id_of_home = int(row['home'])  # Region where agent starts
                center_x, center_y = building_agents[building_id_of_home].geometry.centroid.coords.xy
                this_bounds = building_agents[building_id_of_home].geometry.bounds
                spread_x = int(this_bounds[2] - this_bounds[0])  # Heuristic for agent spread in region
                spread_y = int(this_bounds[3] - this_bounds[1])
                this_x = center_x[0] + self.random.randint(0, spread_x) - spread_x / 2
                this_y = center_y[0] + self.random.randint(0, spread_y) - spread_y / 2
                # print("Home: this_x =", this_x, "this_y =", this_y)

                agent_params = {
                    'unique_id': 'P' + str(row['_id']),
                    'model': self,
                    'geometry': Point(this_x, this_y),
                    'crs': self.space.crs,
                    'weekday_pattern': row['weekday_pattern'],
                    'weekend_pattern': row['weekend_pattern'],
                    'household_id': row['household_id'],
                    'home': row['home'],
                    'work_school': row['work/school']

                }

                if index in random_infected_indices:
                    agent_params['status'] = 'infected'

                this_person = CitizenAgent(**agent_params)

                self.space.add_agents(this_person)
                self.schedule.add(this_person)

        # Add district agents
        for agent in district_agents:
            self.schedule.add(agent)

        self.datacollector.collect(self)


    def reset_counts(self):
        self.counts = {
            "susceptible": 0,
            "infected": 0,
            "exposed": 0,
            "recovered": 0,
        }

    def step(self):
        self.reset_counts()
        self.schedule.step()
        self.datacollector.collect(self)

    def space(self):
        return self.space







# DataCollector functions
#TODO add some kind of "count" thing in the model so that it can be displayed somewhere in server.py
# Some example code for this can be found in mesa-examples github in the geo-sir project
def get_susceptible_count(model):
    return model.counts["susceptible"]

def get_exposed_count(model):
    return model.counts["exposed"]

def get_infected_count(model):
    return model.counts["infected"]

def get_recovered_count(model):
    return model.counts["recovered"]

def get_dead_count(model):
    return model.counts["dead"]
