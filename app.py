import streamlit as st
import pandas as pd
from understatapi import UnderstatClient
import matplotlib.pyplot as plt
from mplsoccer import VerticalPitch


# Set up the Streamlit page layout
st.set_page_config(layout="wide")

# Create a title for the app
st.title("xG Map Visualization For 5 Big Leagues")

# Initialize the Understat API client
understat = UnderstatClient()

# Define the two columns
col1, col2 = st.columns([1, 2])

# Use the first column for the dropdown selections
with col1:
    # Get data for all Premier League players in the selected season
    leagues = ['EPL', 'La_Liga', 'Bundesliga', 'Serie_A', 'Ligue_1', 'RFPL']
    seasons = ['2019', '2020', '2021', '2022', '2023', '2024']
    selected_league = st.selectbox('Choose a League', leagues)
    selected_season = st.selectbox('Choose a Season', seasons)

    # Fetch league player data for the selected season and league
    league_player_data = understat.league(league=selected_league).get_player_data(season=selected_season)

    # Extract player and team information
    player_data = {"ids": [], "names": [], "teams": []}
    for item in league_player_data:
        player_data[0].append(item['id'])
        player_data[1].append(item['player_name'])
        player_data[2].append(item['team_title'])

    # Create team and player dropdowns
    teams = sorted(set(player_data['teams']))
    selected_team = st.selectbox('Choose a Team', teams)

    # Filter players based on selected team
    team_players = [player_data['names'][i] for i in range(len(player_data['teams'])) if player_data['teams'][i] == selected_team]
    selected_player = st.selectbox('Choose a Player', team_players)

# Use the second column for the xG map and statistics
with col2:
    if selected_player:
        # Get the player ID and shot data
        player_id = player_data['ids'][player_data['names'].index(selected_player)]
        player_shot_data = understat.player(player=player_id).get_shot_data()

        # Create a DataFrame from the shot data
        df = pd.DataFrame(player_shot_data)
        df = df[df['season'] == selected_season]
        df['X'] = df['X'].astype(float) * 100
        df['Y'] = df['Y'].astype(float) * 100
        df['xG'] = df['xG'].astype(float)

        # Set background and font colors
        background_color = '#0C0D0E'
        font_color = 'white'

        # Create the pitch layout using mplsoccer
        pitch = VerticalPitch(
            pitch_type='opta', 
            half=True, 
            pitch_color=background_color, 
            line_color='white'
        )

        # Set up the figure
        fig = plt.figure(figsize=(8, 12))
        fig.patch.set_facecolor(background_color)

        # Top row for the player name and shot information
        ax1 = fig.add_axes([0, 0.7, 1, 0.2])
        ax1.set_facecolor(background_color)
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)

        # Title and shot information
        ax1.text(
            x=0.5, y=.85, s=f'{selected_player}', fontsize=20, fontweight='bold', color=font_color, ha='center'
        )
        ax1.text(
            x=0.25, y=0.5, s='Low Quality Chance', fontsize=12, color=font_color, ha='center'
        )
        ax1.text(
            x=0.75, y=0.5, s='High Quality Chance', fontsize=12, color=font_color, ha='center'
        )

        # Plotting quality chance scatter points
        for i, size in enumerate([100, 200, 300, 400, 500], start=1):
            ax1.scatter(x=0.37 + i * 0.05, y=0.53, s=size, color=background_color, edgecolor=font_color, linewidth=.8)

        # Plotting goal vs no goal
        ax1.text(x=0.45, y=0.27, s='Goal', fontsize=10, color=font_color, ha='right')
        ax1.scatter(x=0.47, y=0.3, s=100, color='red', edgecolor=font_color, linewidth=.8, alpha=.7)
        ax1.text(x=0.55, y=0.27, s='No Goal', fontsize=10, color=font_color, ha='left')
        ax1.scatter(x=0.53, y=0.3, s=100, color=background_color, edgecolor=font_color, linewidth=.8)

        ax1.text(
            x=0.5, y=.7, s=f'All shots in the {selected_league} {selected_season} season', fontsize=14, fontweight='bold', color=font_color, ha='center'
        )
        ax1.set_axis_off()

        # Pitch plot
        ax2 = fig.add_axes([.05, 0.25, .9, .5])
        ax2.set_facecolor(background_color)

        pitch.draw(ax=ax2)

        # Plot each shot on the pitch
        for _, shot in df.iterrows():
            color = 'red' if shot['result'] == 'Goal' else background_color
            pitch.scatter(
                x=shot['X'], y=shot['Y'], s=300 * shot['xG'], color=color, edgecolor='white', linewidth=1, alpha=0.7, ax=ax2
            )

        ax2.set_axis_off()

        # Display additional stats
        total_shots = df.shape[0]
        total_goals = df[df['result'] == 'Goal'].shape[0]
        total_xG = df['xG'].sum()
        xG_per_shot = total_xG / total_shots if total_shots > 0 else 0

        # Stats at the bottom
        ax3 = fig.add_axes([0, 0.2, 1, 0.05])
        ax3.set_facecolor(background_color)
        ax3.set_xlim(0, 1)
        ax3.set_ylim(0, 1)

        stats = [("Shots", total_shots), ("Goals", total_goals), ("xG", total_xG), ("xG/Shot", xG_per_shot)]
        for i, (stat_name, stat_value) in enumerate(stats):
            ax3.text(x=0.25 + i * 0.13, y=.5, s=stat_name, fontsize=20, fontweight='bold', color=font_color, ha='left')
            ax3.text(x=0.25 + i * 0.13, y=0, s=f'{stat_value:.2f}' if isinstance(stat_value, float) else f'{stat_value}', fontsize=16, color='red', ha='left')

        ax3.set_axis_off()

        # Display the plot
        st.pyplot(fig)

        # Display additional stats below the map
        st.markdown(f"**Total Shots:** {total_shots}")
        st.markdown(f"**Total Goals:** {total_goals}")
        st.markdown(f"**Total xG:** {total_xG:.2f}")
        st.markdown(f"**xG per Shot:** {xG_per_shot:.2f}")
# Observations Section
st.subheader("Observations")
observations = []

# Add observations based on player's performance
if total_shots < 10:
    observations.append("The player has taken fewer than 10 shots this season, indicating limited goal-scoring opportunities.")
if total_goals > 0:
    observations.append("The player has successfully converted some chances into goals, showcasing their finishing ability.")
else:
    observations.append("The player has not scored any goals yet this season, highlighting a need for improvement in finishing.")

if total_xG > 0:
    observations.append(f"The player's expected goals (xG) total is {total_xG:.2f}, which suggests they are creating scoring chances.")
else:
    observations.append("The player has yet to create significant goal-scoring opportunities this season.")

# Display observations
for obs in observations:
    st.write(f"- {obs}")

# Recommendations Section
st.subheader("Recommendations")
recommendations = []

# Provide recommendations based on performance
if total_goals / total_shots < 0.2:
    recommendations.append("Consider improving shot accuracy, as currently, less than 20% of shots are resulting in goals.")
if xG_per_shot < 0.1:
    recommendations.append("Focus on taking higher quality chances, as the average xG per shot is below 0.1.")
if total_xG < 5:
    recommendations.append("Aim to increase total xG by seeking more goal-scoring opportunities.")

if not recommendations:
    recommendations.append("Keep up the great work! Your shooting and goal-scoring abilities are on point.")

# Display recommendations
for rec in recommendations:
    st.write(f"- {rec}")
