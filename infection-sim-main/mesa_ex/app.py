from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.space import SingleGrid
from mesa.datacollection import DataCollector
import numpy as np

# Import Solara components
from solara.envs import MessageChannel
from solara.constants import COLORS
from solara.agent_visualizer.agents import AgentVisualizer
from solara.agent_visualizer.agents import visualize_agents

# Define Solara environment
env = MessageChannel()

# Create Solara agent visualizer
visualizer = AgentVisualizer(env)

# Define Solara visualization function
@env.subscribe
def visualize_model(iteration, **kwargs):
    agent_positions = [(agent.pos[0], agent.pos[1]) for agent in model.schedule.agents]
    visualize_agents(agent_positions, colors=[COLORS['red']], env=env, iteration=iteration)

# Run the model
if __name__ == "__main__":
    model = MyModel(100)  # Example: 100 agents
    for i in range(10):  # Example of running the model for 10 steps
        model.step()
        visualize_model(i)  # Update Solara visualization

