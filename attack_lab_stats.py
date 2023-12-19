# Built-in libraries
import re
from datetime import datetime
from urllib.request import urlopen

# Other libraries
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

"""
Python script to collect and display the statistics from scoreboard of the Attack Lab (also know as Buffer Lab),
a very common CS Systems project made by R. Bryant and D. O'Hallaron from Carnegie Mellon University.
"""

__author__ = "Kaito Sekiya"
__copyright__ = "Copyright (C) 2023 Kaito Sekiya"
__credits__ = ["Kaito Sekiya"]
__license__ = "MIT License"
__version__ = "1.2"
__maintainer__ = "Kaito Sekiya"
__email__ = "kaitosekiya@outlook.com"
__status__ = "Complete"

#####################
# HTML File Reading #
#####################

# URL of the Attack Lab scoreboard webpage
# TODO: insert your URL before running the script
url = "http://systems3.cs.uic.edu:15513/scoreboard"

# If the user forgot to replace the URL placeholder, notify the user to do it
if url == "INSERT URL HERE":
    exit("Missing URL: add URL to the line 13 (or 11) of the script")

# Open the URL, read and decode the binary file to get a html of the scoreboard as a string
html = urlopen(url).read().decode("utf-8")

# Search the html file with regex pattern of the title of the Attack Lab. If it does 
# not exist, then either the URL is incorrect, or the webpage is not available anymore
if not re.search(r"<title>Attack Lab Scoreboard</title>", html):
    exit("Incorrect URL or the webpage is not available: check URL manually!")

#################################
# Helper Lists and Dictionaries #
#################################
 
# List of the project phases column names
phases = [f"Phase {i}" for i in range(1, 6, 1)]

# Dictionary with phases as keys and scores as values
# NOTE: some Attack Labs can have a different number of points for one or some phases. If so, replace values accordingly. 
points_per_phase = dict(zip(phases, ["15", "25", "25", "35", "20"]))

# Float and string dictionaries with phases as keys and penalized scores as values
# NOTE: some Attack Labs can have a different number of points for one or some phases. If so, replace values accordingly. 
float_penalized_points_per_phase = dict(zip(phases, [12.75, 21.25, 21.25, 29.75, 17]))
str_penalized_points_per_phase = dict(zip(phases, ["12.75", "21.25", "21.25", "29.75", "17"]))

########################
# Scoreboard Dataframe #
########################

# Read the scoreboard from the html file and drop unnecessary columns
scoreboard_df = pd.read_html(html, match="#")[0].drop(labels=["#", "Date"], axis=1)

# Replace penalized scores with "Penalized" no matter if they are floats or strings, and then cast everything to the string type
scoreboard_df = scoreboard_df.replace(float_penalized_points_per_phase, "Penalized").replace(str_penalized_points_per_phase, "Penalized").astype(str) 

# Loop through all phases columns and remove ".0" in the scores
for phase in phases:
    scoreboard_df[phase] = scoreboard_df[phase].str.replace(".0", "")

# NOTE: replacements above simplifies counting later

# Cast only the score column to the float type
scoreboard_df["Score"] = scoreboard_df["Score"].astype(float)

#################
# Date and Time #
#################

# Search the html file for the string containing the time of the last Attack lab update, and convert it to a datetime object
date_and_time = datetime.strptime(re.search(r"updated: (.*) \(updated", html).group(1), "%a %b %d %X %Y")

# Get a date and a time of the latest Attack lab update
date = date_and_time.strftime("%A, %B %d")
time = date_and_time.strftime("%I:%M %p")

##############
# Statistics #
##############

# Add different statistics of the Attack lab to string variable that later will be written to a txt file
stats = f"The Attack Project Stats on {date} at {time}:\n\n"
stats += f"Total number of targets: {len(scoreboard_df.index)}\n" # length of the dataframe index is equal to the number of rows in it

for phase in phases[::-1]:
    # Get a dataframe that contains counts of each score including special cases in one phase
    phase_count_ser = scoreboard_df[phase].value_counts().reindex([points_per_phase[phase], "0", "Penalized", "Too Late", "Invalid"], fill_value=0)

    # Add the number of targets passed one phase with and without penalty
    stats += f"● {phase} - {phase_count_ser[points_per_phase[phase]] + phase_count_ser['Penalized']} targets\n"
    # Add numbers of penalized, late and invalid solutions in one phase
    stats += f"  ○ penalized - {phase_count_ser['Penalized']}\n"
    stats += f"  ○ too late - {phase_count_ser['Too Late']}\n"
    stats += f"  ○ invalid - {phase_count_ser['Invalid']}\n"

# Add the number of targets passed none of phases
stats += f"● No phases - {len(scoreboard_df[scoreboard_df['Score'] == 0.0].index)} targets\n\n"

# Get a dataframe that contains counts of each score including special cases for all phases
count_df = scoreboard_df[phases].apply(pd.Series.value_counts)

# Add total numbers of penalized, late and invalid solutions 
stats += f"Total number of penalized phases: {int(count_df.loc['Penalized'].sum())}\n"
stats += f"Total number of late phases: {int(count_df.loc['Too Late'].sum())}\n"
stats += f"Total number of invalid phases: {int(count_df.loc['Invalid'].sum())}\n\n"

# Add standard statistics
stats += f"Highest score: {scoreboard_df['Score'].max()}\n"
stats += f"Lowest score: {scoreboard_df['Score'].min()}\n"
stats += f"Range: {scoreboard_df['Score'].max() - scoreboard_df['Score'].min()}\n"
stats += f"Mean: {'{:.4f}'.format(scoreboard_df['Score'].mean())}\n"
stats += f"Variance: {'{:.4f}'.format(scoreboard_df['Score'].var())}\n"
stats += f"Standard deviation: {'{:.4f}'.format(scoreboard_df['Score'].std())}\n"

# Write the statistics of the Attack Lab to the text file
with open("project_stats.txt", "w") as f:
    f.write(stats)

####################
# Scores Histogram #
####################

fig, ax = plt.subplots(figsize=(6,4)) # specify the plot proportions

sns.histplot(scoreboard_df, x="Score", stat="percent", bins=np.arange(0, 121, 5), ax=ax)

plt.title("Score Distribution of the Attack Project:", pad=10)
plt.ylabel(None) # remove ylabel

ax.xaxis.set_major_locator(mtick.MultipleLocator(10)) # set major xtick spacing
ax.xaxis.set_minor_locator(mtick.MultipleLocator(2.5)) # set minor xtick spacing

ax.yaxis.set_major_locator(mtick.MultipleLocator(10)) # set major ytick spacing
ax.yaxis.set_minor_locator(mtick.MultipleLocator(2.5)) # set minor ytick spacing

ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0)) # format major ytick labels to percents

# Set bars colors to "Spectral" palette (starts from red and ends with blue)
for bar, color in zip(ax.patches, sns.color_palette("Spectral", len(ax.patches))):
    bar.set_facecolor(color)

plt.tight_layout() # make the plot layout more compact
sns.despine() # remove the upper and right border

# NOTE: increase or decrease dpi number to enlarge or reduce the plot image size
plt.savefig("scores_histogram.png", dpi=150)

#########################
# Passed Phases Barplot #
#########################

fig, ax = plt.subplots(figsize=(6,4)) # specify the plot proportions

# List to store how many targets passed up to some phase (all 5, just 4, just 3 etc.)
phases_count = [] 

# In reverse order, so starting from Phase 5
for phase in phases[::-1]:
    # Get a dataframe with targets that passed one phase
    passed_phase_df = scoreboard_df[phase][(scoreboard_df[phase] == points_per_phase[phase]) | (scoreboard_df[phase] == str_penalized_points_per_phase[phase])]
    # Append the number of row in the dataframe as the number of targets
    phases_count.append(len(passed_phase_df.index))
    # Drop the rows with indexes of this dataframe from the scoreboard dataframe
    scoreboard_df.drop(index=passed_phase_df.index, inplace=True)

# Get a dataframe containing count, proportion and percentage of each phase
phases_df = pd.DataFrame(phases_count[::-1], index=phases, columns=["Count"])
phases_df["Proportion"] = phases_df["Count"] / phases_df["Count"].sum()
phases_df["Percent"] = phases_df["Proportion"] * 100

sns.barplot(data=phases_df, x=phases_df.index, y="Proportion", ax=ax)

plt.title("Completed the Attack Project up to:", pad=10, y=1.08) # y is not 1 since bar labels can collide with it
plt.xlabel(None) # remove xlabel
plt.ylabel(None) # remove ylabel

ax.yaxis.set_major_locator(mtick.MultipleLocator(0.1)) # set major ytick spacing
ax.yaxis.set_minor_locator(mtick.MultipleLocator(0.025)) # set minor ytick spacing
ax.yaxis.set_major_formatter(mtick.StrMethodFormatter("{x:.1f}")) # format major ytick labels

# Get bar labels that contains percent and count separated by newline 
bars_labels = phases_df["Percent"].round(1).astype("str") + "%\n" + phases_df["Count"].astype("str")

# Add labels over the bars
ax.bar_label(ax.containers[0], labels=bars_labels, padding=2)

# Set bars colors based on the number of phases passed
for bar, color in zip(ax.patches, ["#ED4D36","#F29B28","#E9D536","#D3EF5E","#6FE180"]):
    bar.set_facecolor(color)

plt.tight_layout() # make the plot layout more compact
sns.despine() # remove the upper and right border

# NOTE: increase or decrease dpi number to enlarge or reduce the plot image size
plt.savefig("phases_barplot.png", dpi=150) 