from money_model import MoneyModel
import numpy as np
import seaborn as sns
import mesa

model = MoneyModel(100, 10, 10)
for i in range(100):
    model.step()


gini = model.datacollector.get_model_vars_dataframe()
# Plot the Gini coefficient over time
g = sns.lineplot(data=gini)
g.set(title="Gini Coefficient over Time", ylabel="Gini Coefficient");

print("debug")