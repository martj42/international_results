import pandas as pd

result_data = pd.read_csv("./results.csv")
goalscorer_data = pd.read_csv("./goalscorers.csv")
shootout_data = pd.read_csv("./shootouts.csv")

# Create result ID
result_data['home_score'] = result_data['home_score'].fillna(0).astype(int)
result_data['away_score'] = result_data['away_score'].fillna(0).astype(int)
result_data.insert(0, 'result_id', range(0, len(result_data)))
result_data.to_csv("./compiled_data/results.csv", index=False)

# Merge Result ID to Goalscorer data
goalscorer_data = pd.merge(goalscorer_data, result_data[['result_id', 'home_team', 'away_team', 'date']], on=['home_team', 'away_team', 'date'], how='left')
goalscorer_data['minute'] = goalscorer_data['minute'].fillna(0).astype(int)
goalscorer_column_titles = ['result_id', 'date', 'home_team', 'away_team', 'team', 'scorer', 'minute', 'own_goal', 'penalty']
goalscorer_data = goalscorer_data.reindex(columns=goalscorer_column_titles)
goalscorer_data.insert(0, 'goal_id', range(0, len(goalscorer_data)))
goalscorer_data.to_csv("./compiled_data/goalscorers.csv", index=False)

# Merge Result ID to Shootout data
shootout_data = pd.merge(shootout_data, result_data[['result_id', 'home_team', 'away_team', 'date']], on=['home_team', 'away_team', 'date'], how='left')
shootout_column_titles = ['result_id', 'date', 'home_team', 'away_team', 'winner']
shootout_data = shootout_data.reindex(columns=shootout_column_titles)
shootout_data['result_id'] = shootout_data['result_id'].fillna(0).astype(int)
shootout_data.insert(0, 'shootout_id', range(0, len(shootout_data)))
shootout_data.to_csv("./compiled_data/shootouts.csv", index=False)