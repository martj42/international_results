### Context

Well, what happened was that I was looking for a semi-definite easy-to-read list of international football matches and couldn't find anything decent. So I took it upon myself to collect it for my own use. I might as well share it.

### Content

This dataset includes **47,960** results of international football matches starting from the very first official match in 1872 up to 2024. The matches range from FIFA World Cup to FIFI Wild Cup to regular friendly matches. The matches are strictly men's full internationals and the data does not include Olympic Games or matches where at least one of the teams was the nation's B-team, U-23 or a league select team.

`results.csv` includes the following columns:

-   `date` - date of the match
-   `home_team` - the name of the home team
-   `away_team` - the name of the away team
-   `home_score` - full-time home team score including extra time, not including penalty-shootouts
-   `away_score` - full-time away team score including extra time, not including penalty-shootouts
-   `tournament` - the name of the tournament
-   `city` - the name of the city/town/administrative unit where the match was played
-   `country` - the name of the country where the match was played
-   `neutral` - TRUE/FALSE column indicating whether the match was played at a neutral venue

`shootouts.csv` includes the following columns:

-   `date` - date of the match
-   `home_team` - the name of the home team
-   `away_team` - the name of the away team
-   `winner` - winner of the penalty-shootout
-   `first_shooter` - the team that went first in the shootout

`goalscorers.csv` includes the following columns:

-   `date` - date of the match
-   `home_team` - the name of the home team
-   `away_team` - the name of the away team
-   `team` - name of the team scoring the goal
-   `scorer` - name of the player scoring the goal
-   `own_goal` - whether the goal was an own-goal
-   `penalty` - whether the goal was a penalty

Note on team and country names: For home and away teams the *current* name of the team has been used. For example, when in 1882 a team who called themselves Ireland played against England, in this dataset, it is called Northern Ireland because the current team of Northern Ireland is the successor of the 1882 Ireland team. This is done so it is easier to track the history and statistics of teams.

For country names, the name of the country *at the time of the match* is used. So when Ghana played in Accra, Gold Coast in the 1950s, even though the names of the home team and the country don't match, it was a home match for Ghana. This is indicated by the neutral column, which says FALSE for those matches, meaning it was **not** at a neutral venue.

### Acknowledgements

The data is gathered from several sources including but not limited to Wikipedia, rsssf.com, and individual football associations' websites.

### Inspiration

Some directions to take when exploring the data:

-   Who is the best team of all time
-   Which teams dominated different eras of football
-   What trends have there been in international football throughout the ages - home advantage, total goals scored, distribution of teams' strength etc
-   Can we say anything about geopolitics from football fixtures - how has the number of countries changed, which teams like to play each other
-   Which countries host the most matches where they themselves are not participating in
-   How much, if at all, does hosting a major tournament help a country's chances in the tournament
-   Which teams are the most active in playing friendlies and friendly tournaments - does it help or hurt them

The world's your oyster, my friend.

### Contribute

If you notice a mistake or the results are not updated fast enough for your liking, you can fix that by submitting a pull request.