"""
وحدة تحليل البيانات المتقدمة لكرة القدم
تتضمن 8 عوامل متطورة للتنبؤ
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from scipy import stats
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TeamStats:
    """إحصائيات الفريق"""
    team_name: str
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_scored: int = 0
    goals_conceded: int = 0
    xg_scored: float = 0.0
    xg_conceded: float = 0.0
    points: int = 0
    form_last_5: List[str] = None
    home_wins: int = 0
    home_draws: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_draws: int = 0
    away_losses: int = 0


class AdvancedFootballAnalyzer:
    """
    محلل كرة القدم المتقدم
    يحسب 8 عوامل متطورة للتنبؤ بالنتائج
    """
    
    def __init__(self, matches_df: pd.DataFrame):
        self.df = matches_df.copy()
        self.team_stats = {}
        self._calculate_all_stats()
        
    def _calculate_all_stats(self):
        """حساب إحصائيات جميع الفرق"""
        all_teams = set(self.df['home_team'].unique()) | set(self.df['away_team'].unique())
        
        for team in all_teams:
            self.team_stats[team] = self._calculate_team_stats(team)
            
    def _calculate_team_stats(self, team: str) -> TeamStats:
        """حساب إحصائيات فريق معين"""
        home_matches = self.df[self.df['home_team'] == team]
        away_matches = self.df[self.df['away_team'] == team]
        all_matches = pd.concat([home_matches, away_matches])
        
        stats = TeamStats(team_name=team)
        
        if len(all_matches) == 0:
            return stats
            
        stats.matches_played = len(all_matches)
        
        # نتائج المباريات
        for _, match in all_matches.iterrows():
            if match['home_team'] == team:
                stats.goals_scored += match['home_goals']
                stats.goals_conceded += match['away_goals']
                stats.xg_scored += match.get('home_xg', 0) or 0
                stats.xg_conceded += match.get('away_xg', 0) or 0
                
                if match['home_goals'] > match['away_goals']:
                    stats.wins += 1
                    stats.home_wins += 1
                    stats.points += 3
                elif match['home_goals'] == match['away_goals']:
                    stats.draws += 1
                    stats.home_draws += 1
                    stats.points += 1
                else:
                    stats.losses += 1
                    stats.home_losses += 1
            else:
                stats.goals_scored += match['away_goals']
                stats.goals_conceded += match['home_goals']
                stats.xg_scored += match.get('away_xg', 0) or 0
                stats.xg_conceded += match.get('home_xg', 0) or 0
                
                if match['away_goals'] > match['home_goals']:
                    stats.wins += 1
                    stats.away_wins += 1
                    stats.points += 3
                elif match['away_goals'] == match['home_goals']:
                    stats.draws += 1
                    stats.away_draws += 1
                    stats.points += 1
                else:
                    stats.losses += 1
                    stats.away_losses += 1
        
        # آخر 5 مباريات
        recent = all_matches.sort_values('date').tail(5)
        form = []
        for _, match in recent.iterrows():
            if match['home_team'] == team:
                if match['home_goals'] > match['away_goals']:
                    form.append('W')
                elif match['home_goals'] == match['away_goals']:
                    form.append('D')
                else:
                    form.append('L')
            else:
                if match['away_goals'] > match['home_goals']:
                    form.append('W')
                elif match['away_goals'] == match['home_goals']:
                    form.append('D')
                else:
                    form.append('L')
        stats.form_last_5 = form
        
        return stats
    
    # العامل 1: شكل الفريق
    def factor_1_form(self, team: str) -> float:
        stats = self.team_stats.get(team)
        if not stats or not stats.form_last_5:
            return 0.5
            
        points = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in stats.form_last_5)
        max_points = len(stats.form_last_5) * 3
        return points / max_points if max_points > 0 else 0.5
    
