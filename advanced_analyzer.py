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
            # العامل 2: القوة الهجومية
    def factor_2_offensive_strength(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats or stats.matches_played == 0:
            return 1.0
            
        avg_goals = stats.goals_scored / stats.matches_played
        avg_xg = stats.xg_scored / stats.matches_played
        
        strength = (avg_goals * 0.4 + avg_xg * 0.6)
        
        if is_home:
            home_matches = stats.home_wins + stats.home_draws + stats.home_losses
            if home_matches > 0:
                home_goals = self.df[
                    (self.df['home_team'] == team)
                ]['home_goals'].sum()
                strength = (home_goals / home_matches) * 0.7 + strength * 0.3
        else:
            away_matches = stats.away_wins + stats.away_draws + stats.away_losses
            if away_matches > 0:
                away_goals = self.df[
                    (self.df['away_team'] == team)
                ]['away_goals'].sum()
                strength = (away_goals / away_matches) * 0.7 + strength * 0.3
        
        return max(0.1, strength)
    
    # العامل 3: القوة الدفاعية
    def factor_3_defensive_strength(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats or stats.matches_played == 0:
            return 1.0
            
        avg_conceded = stats.goals_conceded / stats.matches_played
        avg_xg_conceded = stats.xg_conceded / stats.matches_played
        
        combined = avg_conceded * 0.4 + avg_xg_conceded * 0.6
        
        if is_home:
            home_matches = stats.home_wins + stats.home_draws + stats.home_losses
            if home_matches > 0:
                home_conceded = self.df[
                    (self.df['home_team'] == team)
                ]['away_goals'].sum()
                combined = (home_conceded / home_matches) * 0.7 + combined * 0.3
        else:
            away_matches = stats.away_wins + stats.away_draws + stats.away_losses
            if away_matches > 0:
                away_conceded = self.df[
                    (self.df['away_team'] == team)
                ]['home_goals'].sum()
                combined = (away_conceded / away_matches) * 0.7 + combined * 0.3
        
        strength = 1 / (1 + combined)
        return max(0.1, strength)
    
    # العامل 4: الأداء في الملعب
    def factor_4_home_away_advantage(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats:
            return 1.0 if is_home else 0.8
            
        if is_home:
            total_home = stats.home_wins + stats.home_draws + stats.home_losses
            if total_home == 0:
                return 1.0
            home_points = stats.home_wins * 3 + stats.home_draws
            max_points = total_home * 3
            return home_points / max_points if max_points > 0 else 0.5
        else:
            total_away = stats.away_wins + stats.away_draws + stats.away_losses
            if total_away == 0:
                return 0.8
            away_points = stats.away_wins * 3 + stats.away_draws
            max_points = total_away * 3
            return away_points / max_points if max_points > 0 else 0.5
    
    # العامل 5: تاريخ المواجهات المباشرة
    def factor_5_head_to_head(self, home_team: str, away_team: str) -> Dict[str, float]:
        h2h = self.df[
            ((self.df['home_team'] == home_team) & (self.df['away_team'] == away_team)) |
            ((self.df['home_team'] == away_team) & (self.df['away_team'] == home_team))
        ].sort_values('date')
        
        if len(h2h) == 0:
            return {'home_advantage': 0.5, 'draw_tendency': 0.33}
        
        home_wins = 0
        away_wins = 0
        draws = 0
        
        for _, match in h2h.tail(10).iterrows():
            if match['home_team'] == home_team:
                if match['home_goals'] > match['away_goals']:
                    home_wins += 1
                elif match['home_goals'] < match['away_goals']:
                    away_wins += 1
                else:
                    draws += 1
            else:
                if match['away_goals'] > match['home_goals']:
                    home_wins += 1
                elif match['away_goals'] < match['home_goals']:
                    away_wins += 1
                else:
                    draws += 1
        
        total = home_wins + away_wins + draws
        if total == 0:
            return {'home_advantage': 0.5, 'draw_tendency': 0.33}
        
        return {
            'home_advantage': home_wins / total,
            'away_advantage': away_wins / total,
            'draw_tendency': draws / total
        }
    
    # العامل 6: إحصائيات اللعب النظيف
    def factor_6_discipline(self, team: str) -> float:
        team_matches = self.df[
            (self.df['home_team'] == team) | (self.df['away_team'] == team)
        ]
        
        if len(team_matches) == 0:
            return 0.5
        
        total_yellow = 0
        total_red = 0
        
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                total_yellow += match.get('home_yellow_cards', 0) or 0
                total_red += match.get('home_red_cards', 0) or 0
            else:
                total_yellow += match.get('away_yellow_cards', 0) or 0
                total_red += match.get('away_red_cards', 0) or 0
        
        avg_yellow = total_yellow / len(team_matches)
        avg_red = total_red / len(team_matches)
        
        discipline_score = 1 - (avg_yellow * 0.05 + avg_red * 0.3)
        return max(0.1, min(1.0, discipline_score))
    
    # العامل 7: كفاءة التسديد
    def factor_7_shot_efficiency(self, team: str) -> float:
        team_matches = self.df[

        return factors

    
