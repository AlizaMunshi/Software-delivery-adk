# Multi-agent ADK workflow code goes here

class Agent:
    def __init__(self, name):
        self.name = name

    def workflow(self):
        print(f"Running workflow for agent: {self.name}")

agents = [Agent(name=f"Agent-{i}") for i in range(5)]

for agent in agents:
    agent.workflow()