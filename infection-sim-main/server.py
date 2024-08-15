import mesa
import mesa_geo as mg

from model import InfectionModel, get_susceptible_count, get_exposed_count, get_infected_count, get_recovered_count
from agent import CitizenAgent, DistrictAgent

from create_agent_db import create_agent_dataframe

class TimeText(mesa.visualization.TextElement):
    def __init__(self):
        pass

    def render(self, model):
        return ("Schedule: " + model.schedule.current_day_of_week() + " " + model.schedule.current_time_period())

class CountText(mesa.visualization.TextElement):
    def __init__(self):
        pass

    def render(self, model):
        susceptible_text = str(get_susceptible_count(model))
        exposed_text = str(get_exposed_count(model))
        infected_text = str(get_infected_count(model))
        recovered_text = str(get_recovered_count(model))
        return ("Susceptible: " + susceptible_text +
                "  Exposed: " + exposed_text +
                "  Infected: " + infected_text +
                "  Recovered " + recovered_text)



model_params = {
    "num_agents": 15000,
    "infection_risk_close": 0.75,          # percent
    "infection_risk_stranger": 0.25,       # percent
    "exposure_distance": 500,              # o idea what unit this is in
    "incubation_period": 4,                # days
    "infection_duration": 7,               # days
    "starting_infected_individuals": 5,
    "agent_database": create_agent_dataframe(),  # set it to None if you don't want to use
    "disease": mesa.visualization.Choice("Disease", value="Measles", choices=['Custom', 'Measles', 'COVID-19', 'Influenza'])
    # "disease": 'Measles'
}

def agent_portrayal(agent):
    portrayal = {}
    if isinstance(agent, CitizenAgent):
        portrayal["radius"] = "2"
        if agent.status == "susceptible":
            portrayal["color"] = "Green"
        elif agent.status == "exposed":
            portrayal["color"] = "Yellow"
        elif agent.status == "infected":
            portrayal["color"] = "Red"
        elif agent.status == "recovered":
            portrayal["color"] = "Blue"
    elif isinstance(agent, DistrictAgent):
        portrayal["color"] = "Grey"
    return portrayal

time_text = TimeText()
count_text = CountText()
map_element = mg.visualization.MapModule(agent_portrayal)

server = mesa.visualization.ModularServer(
    InfectionModel,
    [map_element, time_text, count_text],
    "Infection Simulation",
    model_params
)




