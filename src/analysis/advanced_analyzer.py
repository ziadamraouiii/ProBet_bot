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
            (self.df['home_team'] == team) | (self.df['away_team'] == team)
        ]
        
        if len(team_matches) == 0:
            return 0.3
        
        total_goals = 0
        total_shots_on_target = 0
        
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                total_goals += match['home_goals']
                total_shots_on_target += match.get('home_shots_on_target', 0) or 0
            else:
                total_goals += match['away_goals']
                total_shots_on_target += match.get('away_shots_on_target', 0) or 0
        
        if total_shots_on_target == 0:
            return 0.3
        
        efficiency = total_goals / total_shots_on_target
        return min(1.0, efficiency / 0.3)
    
    # العامل 8: زخم الأداء
    def factor_8_momentum(self, team: str) -> float:
        team_matches = self.df[
            (self.df['home_team'] == team) | (self.df['away_team'] == team)
        ].sort_values('date').tail(10)
        
        if len(team_matches) < 5:
            return 0.5
        
        results = []
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                goal_diff = match['home_goals'] - match['away_goals']
            else:
                goal_diff = match['away_goals'] - match['home_goals']
            results.append(goal_diff)
        
        x = np.arange(len(results))
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, results)
        
        momentum = 0.5 + (slope * 0.1)
        return max(0.1, min(1.0, momentum))
    
    def get_all_factors(self, home_team: str, away_team: str) -> Dict[str, float]:
        """الحصول على جميع العوامل الثمانية للمباراة"""
        h2h = self.factor_5_head_to_head(home_team, away_team)
        
        factors = {
            'home_form': self.factor_1_form(home_team),
            'away_form': self.factor_1_form(away_team),
            'home_offense': self.factor_2_offensive_strength(home_team, True),
            'away_offense': self.factor_2_offensive_strength(away_team, False),
            'home_defense': self.factor_3_defensive_strength(home_team, True),
            'away_defense': self.factor_3_defensive_strength(away_team, False),
            'home_advantage': self.factor_4_home_away_advantage(home_team, True),
            'away_advantage': self.factor_4_home_away_advantage(away_team, False),
            'h2h_home': h2h['home_advantage'],
            'h2h_draw': h2h['draw_tendency'],
            'home_discipline': self.factor_6_discipline(home_team),
            'away_discipline': self.factor_6_discipline(away_team),
            'home_efficiency': self.factor_7_shot_efficiency(home_team),
            'away_efficiency': self.factor_7_shot_efficiency(away_team),
            'home_momentum': self.factor_8_momentum(home_team),
            'away_momentum': self.factor_8_momentum(away_team),
        }
        
        return factors
