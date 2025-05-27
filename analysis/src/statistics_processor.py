import csv
import logging
from collections import defaultdict
from statistics import mean, median, mode
from typing import Dict, List, Protocol, Optional
from pathlib import Path
from .records import MatchRecord, ScorerRecord

class TeamStats:
    def __init__(self):
        self.matches = 0
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.goals_for = 0
        self.goals_against = 0
        self.goals_list: List[int] = []

    def update(self, scored: int, conceded: int, result: str):
        self.matches += 1
        self.goals_for += scored
        self.goals_against += conceded
        self.goals_list.append(scored)
        if result == "win":
            self.wins += 1
        elif result == "loss":
            self.losses += 1
        elif result == "draw":
            self.draws += 1

    def stats_summary(self) -> Dict:
        stats = {
            "matches": self.matches,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "goals_for": self.goals_for,
            "goals_against": self.goals_against,
        }
        if self.goals_list:
            stats["mean_goals"] = int(mean(self.goals_list))
            stats["median_goals"] = int(median(self.goals_list))
            stats["mode_goals"] = int(mode(self.goals_list))
        return stats

class TeamStatsCalculator(Protocol):
    def update(self, record: MatchRecord) -> None:
        ...
    def get_team_stats(self) -> Dict[str, 'TeamStats']:
        ...

class DefaultTeamStatsCalculator:
    def __init__(self):
        self.teams: Dict[str, TeamStats] = defaultdict(TeamStats)

    def update(self, record: MatchRecord):
        if record.home_score > record.away_score:
            home_result, away_result = "win", "loss"
        elif record.home_score < record.away_score:
            home_result, away_result = "loss", "win"
        else:
            home_result = away_result = "draw"
        self.teams[record.home_team].update(record.home_score, record.away_score, home_result)
        self.teams[record.away_team].update(record.away_score, record.home_score, away_result)

    def get_team_stats(self):
        return self.teams

class FormerNamesResolver:
    def __init__(self, former_names_path: Path):
        self.former_to_current = {}
        self._load_former_names(former_names_path)

    def _load_former_names(self, path: Path):
        with path.open(newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                self.former_to_current[row['former']] = row['current']

    def resolve(self, name: str) -> str:
        # Return the current name if exists, else the original name
        return self.former_to_current.get(name, name)

class ReportPrinter(Protocol):
    def print_table(self, teams: Dict[str, TeamStats]) -> None:
        ...

class MarkdownReportPrinter:
    def print_table(self, teams: Dict[str, TeamStats]) -> None:
        team_stats = [
            (team, stats.stats_summary())
            for team, stats in teams.items()
        ]
        team_stats.sort(key=lambda x: x[0])
        if not team_stats:
            print("No statistics to display.")
            return
        headers = ["Team"] + list(team_stats[0][1].keys())
        print("| " + " | ".join(headers) + " |")
        print("|" + "|".join(["---"] * len(headers)) + "|")
        for team, summary in team_stats:
            row = [team] + [str(summary.get(h, "")) for h in headers[1:]]
            print("| " + " | ".join(row) + " |")

class DataLoader:
    def __init__(self, data_dir: Path, name_resolver: FormerNamesResolver):
        self.data_dir = data_dir
        self.name_resolver = name_resolver

    def load_goal_scorers(self) -> List[dict]:
        path = self.data_dir / "goalscorers.csv"
        scorers = []
        with path.open(newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                scorers.append(row)
        return scorers

    def load_matches(self) -> List[MatchRecord]:
        results_path = self.data_dir / "results.csv"
        goal_scorers = self.load_goal_scorers()
        scorer_index: Dict[tuple, List[dict]] = defaultdict(list)
        for row in goal_scorers:
            key = (row['date'], row['home_team'], row['away_team'])
            scorer_index[key].append(row)

        matches = []
        with results_path.open(newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                date = row.get('date', "")
                home_team = self.name_resolver.resolve(row['home_team'])
                away_team = self.name_resolver.resolve(row['away_team'])
                key = (date, row['home_team'], row['away_team'])
                scorer_records = [
                    ScorerRecord(
                        team=self.name_resolver.resolve(scorer['team']),
                        scorer=scorer['scorer'],
                        minute=scorer['minute'],
                        own_goal=scorer['own_goal'].upper() == "TRUE",
                        penalty=scorer['penalty'].upper() == "TRUE"
                    )
                    for scorer in scorer_index.get(key, [])
                ]
                matches.append(MatchRecord(
                    home_team=home_team,
                    away_team=away_team,
                    home_score=int(row['home_score']),
                    away_score=int(row['away_score']),
                    date=date,
                    tournament=row.get('tournament', ""),
                    city=row.get('city', ""),
                    country=row.get('country', ""),
                    neutral=row.get('neutral', "False") in ("True", "true", "1"),
                    scorers=scorer_records
                ))
        return matches

class StatisticsProcessor:
    def __init__(
        self,
        data_dir: Path,
        printer: ReportPrinter = MarkdownReportPrinter(),
        calculator: Optional[TeamStatsCalculator] = None
    ):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.data_dir = data_dir
        self.name_resolver = FormerNamesResolver(data_dir / "former_names.csv")
        self.calculator = calculator or DefaultTeamStatsCalculator()
        self.printer = printer
        self.data_loader = DataLoader(data_dir, self.name_resolver)

    def process_results(self):
        matches = self.data_loader.load_matches()
        for record in matches:
            self.calculator.update(record)

    def print_statistics(self):
        self.printer.print_table(self.calculator.get_team_stats())