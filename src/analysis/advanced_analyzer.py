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
