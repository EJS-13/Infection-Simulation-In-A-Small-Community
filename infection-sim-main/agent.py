from mesa import Agent
import mesa_geo as mg
import mesa
from shapely.geometry import Point
import geopandas as gpd


class CitizenAgent(mg.GeoAgent):
    def __init__(self, unique_id, model, geometry, crs, weekday_pattern, weekend_pattern, household_id, home,
                 work_school, status="susceptible",
                 days_exposed=0, days_infected=0, mobility_range=100):
        super().__init__(unique_id, model, geometry, crs)
        self.status = status
        self.household_id = household_id
        self.days_exposed = days_exposed
        self.days_infected = days_infected
        self.mobility_range = mobility_range
        self.schedule = mesa.time.RandomActivation(self.model)
        self.weekday_pattern = weekday_pattern  # List of FIDs
        self.weekend_pattern = weekend_pattern  # List of FIDs
        self.building_agents = model.building_agents

    def step(self):
        # TODO put agent logic in **EACH STEP IS A TIME PERIOD (Mon-Morning, Mon-Afternoon, Mon-Evening,
        #  Tues-Morning, etc) Get neighbouring agents within the exposure distance For every neighbour, check if they
        #  are infected If they are, then check if they are family/friend - bigger infection risk if they are Change
        #  status to exposed Get neighbouring agents within the exposure distance

        # debug print to see time period of day
        # print("time period:", self.model.schedule.current_time_period())

        if self.status == "susceptible":
            # Get the grid from the model's space
            neighbors = self.model.space.get_neighbors_within_distance(self, self.model.exposure_distance)

            # Filter out DistrictAgents from neighbors
            citizen_neighbors = [neighbor for neighbor in neighbors if isinstance(neighbor, CitizenAgent)]

            for neighbor in citizen_neighbors:
                if neighbor.status == "infected":
                    # Check if they are family
                    if neighbor.household_id == self.household_id:
                        if self.random.random() < self.model.infection_risk_close:
                            self.status = "exposed"
                    else: # stranger
                        if self.random.random() < self.model.infection_risk_stranger:
                            self.status = "exposed"

                    break  # No need to check other neighbors if already exposed

        elif self.status == "exposed":
            # if it's morning, days_exposed ++
            # if days exposed >= incubation period, then change to infected and reset days_exposed count to 0
            #print("Exposed Individual")
            if self.model.schedule.current_time_period() == "Morning":
                self.days_exposed += 1  # Increment days exposed
                #print(self.days_exposed)  # debug print statement
            # Check if the incubation period has passed
            if self.days_exposed >= self.model.incubation_period:
                # Change status to infected
                self.status = "infected"
                # Reset days_exposed count to 0
                self.days_exposed = 0
            # Implement logic for afternoon and evening if needed

        elif self.status == "infected":
            # if it's morning, days_infected ++
            if self.model.schedule.current_time_period() == "Morning":
                self.days_infected += 1
            # if days infected >= duration of infectiousness, then change to recovered and reset days_infected count
            if self.days_infected >= self.model.infection_duration:
                self.status = "recovered"
                self.days_infected = 0


        self.geometry = self.move()  # Reassign geometry
        self.model.counts[self.status] += 1

    def move(self):
        current_day = self.model.schedule.current_day_of_week()
        current_time_period = self.model.schedule.current_time_period()

        if current_day in ['Mon', 'Tue', 'Wed', 'Thu', 'Fri']:
            index = 0 if current_time_period == 'Morning' else (1 if current_time_period == 'Afternoon' else 2)
            return self.building_location(int(self.weekday_pattern[index]))

        elif current_day in ['Sat', 'Sun']:
            index = 0 if current_time_period == 'Morning' else (1 if current_time_period == 'Afternoon' else 2)
            return self.building_location(int(self.weekend_pattern[index]))

    def building_location(self, fid):
        building_agent = self.building_agents[fid]
        center_x, center_y = building_agent.geometry.centroid.coords.xy
        this_bounds = building_agent.geometry.bounds
        spread_x = int(this_bounds[2] - this_bounds[0])
        spread_y = int(this_bounds[3] - this_bounds[1])
        this_x = center_x[0] + self.random.randint(0, spread_x) - spread_x / 2
        this_y = center_y[0] + self.random.randint(0, spread_y) - spread_y / 2
        # print("Agent", self.unique_id, "this_x =", this_x, "this_y =", this_y)
        return Point(this_x, this_y)

    def get_status(self):
        return self.status


class DistrictAgent(mg.GeoAgent):
    def __init__(self, unique_id, model, geometry, crs):
        super().__init__(unique_id, model, geometry, crs)
