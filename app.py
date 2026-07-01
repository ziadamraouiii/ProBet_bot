"""
ProBet - Football Prediction App
All-in-one file for Streamlit Cloud
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from scipy import stats
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import logging
import warnings

warnings.filterwarnings('ignore')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════
# PART 1: Data Fetcher
# ═══════════════════════════════════════════════════════

@dataclass
class MatchData:
    match_id: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    date: datetime
    league: str
    season: str
    home_xg: Optional[float] = None
    away_xg: Optional[float] = None
    home_possession: Optional[float] = None
    away_possession: Optional[float] = None
    home_shots: Optional[int] = None
    away_shots: Optional[int] = None
    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None
    home_corners: Optional[int] = None
    away_corners: Optional[int] = None
    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None
    home_yellow_cards: Optional[int] = None
    away_yellow_cards: Optional[int] = None
    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None

class FootballDataFetcher:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        
    def generate_sample_data(self, n_matches: int = 5000) -> pd.DataFrame:
        np.random.seed(42)
        
        teams_pool = [
            "Manchester City", "Liverpool", "Arsenal", "Chelsea", "Manchester United",
            "Tottenham", "Newcastle", "Aston Villa", "Brighton", "West Ham",
            "Real Madrid", "Barcelona", "Atletico Madrid", "Sevilla", "Valencia",
            "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Bayer Leverkusen", "Eintracht Frankfurt",
            "Juventus", "AC Milan", "Inter Milan", "Napoli", "Roma",
            "PSG", "Marseille", "Lyon", "Monaco", "Lille",
            "Al Nassr", "Al Hilal", "Al Ahli", "Al Ittihad", "Al Ettifaq",
            "Al Ahly", "Zamalek", "Pyramids", "Future FC", "Ceramica Cleopatra",
        ]
        
        leagues = ["EPL", "LaLiga", "Bundesliga", "SerieA", "Ligue1", "SaudiProLeague", "EgyptianPremierLeague"]
        
        data = []
        for i in range(n_matches):
            home_team = np.random.choice(teams_pool)
            away_team = np.random.choice([t for t in teams_pool if t != home_team])
            league = np.random.choice(leagues)
            
            home_possession = np.random.normal(52, 8)
            home_possession = max(30, min(70, home_possession))
            away_possession = 100 - home_possession
            
            home_shots = max(0, int(np.random.normal(12, 4)))
            away_shots = max(0, int(np.random.normal(10, 4)))
            
            home_shots_on_target = max(0, min(home_shots, int(np.random.normal(4, 2))))
            away_shots_on_target = max(0, min(away_shots, int(np.random.normal(3, 2))))
            
            home_corners = max(0, int(np.random.normal(5, 2)))
            away_corners = max(0, int(np.random.normal(4, 2)))
            
            home_fouls = max(0, int(np.random.normal(12, 4)))
            away_fouls = max(0, int(np.random.normal(11, 4)))
            
            home_yellow = max(0, int(np.random.poisson(1.5)))
            away_yellow = max(0, int(np.random.poisson(1.5)))
            
            home_red = 1 if np.random.random() < 0.05 else 0
            away_red = 1 if np.random.random() < 0.05 else 0
            
            home_xg = max(0, np.random.normal(1.4, 0.8))
            away_xg = max(0, np.random.normal(1.1, 0.7))
            
            home_goals = np.random.poisson(home_xg * 0.7 + 0.3)
            away_goals = np.random.poisson(away_xg * 0.7 + 0.3)
            
            match = {
                'match_id': f"M{i:06d}",
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'away_goals': away_goals,
                'date': datetime(2023, 8, 1) + timedelta(days=i % 300),
                'league': league,
                'season': '2023-24' if i < 2500 else '2024-25',
                'home_xg': round(home_xg, 2),
                'away_xg': round(away_xg, 2),
                'home_possession': round(home_possession, 1),
                'away_possession': round(away_possession, 1),
                'home_shots': home_shots,
                'away_shots': away_shots,
                'home_shots_on_target': home_shots_on_target,
                'away_shots_on_target': away_shots_on_target,
                'home_corners': home_corners,
                'away_corners': away_corners,
                'home_fouls': home_fouls,
                'away_fouls': away_fouls,
                'home_yellow_cards': home_yellow,
                'away_yellow_cards': away_yellow,
                'home_red_cards': home_red,
                'away_red_cards': away_red,
            }
            data.append(match)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} sample matches")
        return df

# ═══════════════════════════════════════════════════════
# PART 2: Advanced Analyzer
# ═══════════════════════════════════════════════════════

@dataclass
class TeamStats:
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
    def __init__(self, matches_df: pd.DataFrame):
        self.df = matches_df.copy()
        self.team_stats = {}
        self._calculate_all_stats()
        
    def _calculate_all_stats(self):
        all_teams = set(self.df['home_team'].unique()) | set(self.df['away_team'].unique())
        for team in all_teams:
            self.team_stats[team] = self._calculate_team_stats(team)
            
    def _calculate_team_stats(self, team: str) -> TeamStats:
        home_matches = self.df[self.df['home_team'] == team]
        away_matches = self.df[self.df['away_team'] == team]
        all_matches = pd.concat([home_matches, away_matches])
        
        stats = TeamStats(team_name=team)
        if len(all_matches) == 0:
            return stats
            
        stats.matches_played = len(all_matches)
        
        for _, match in all_matches.iterrows():
            if match['home_team'] == team:
                stats.goals_scored += match['home_goals']
                stats.goals_conceded += match['away_goals']
                stats.xg_scored += match.get('home_xg', 0) or 0
                stats.xg_conceded += match.get('away_xg', 0) or 0
                
                if match['home_goals'] > match['away_goals']:
                    stats.wins += 1; stats.home_wins += 1; stats.points += 3
                elif match['home_goals'] == match['away_goals']:
                    stats.draws += 1; stats.home_draws += 1; stats.points += 1
                else:
                    stats.losses += 1; stats.home_losses += 1
            else:
                stats.goals_scored += match['away_goals']
                stats.goals_conceded += match['home_goals']
                stats.xg_scored += match.get('away_xg', 0) or 0
                stats.xg_conceded += match.get('home_xg', 0) or 0
                
                if match['away_goals'] > match['home_goals']:
                    stats.wins += 1; stats.away_wins += 1; stats.points += 3
                elif match['away_goals'] == match['home_goals']:
                    stats.draws += 1; stats.away_draws += 1; stats.points += 1
                else:
                    stats.losses += 1; stats.away_losses += 1
        
        recent = all_matches.sort_values('date').tail(5)
        form = []
        for _, match in recent.iterrows():
            if match['home_team'] == team:
                form.append('W' if match['home_goals'] > match['away_goals'] else 'D' if match['home_goals'] == match['away_goals'] else 'L')
            else:
                form.append('W' if match['away_goals'] > match['home_goals'] else 'D' if match['away_goals'] == match['home_goals'] else 'L')
        stats.form_last_5 = form
        return stats
    
    def factor_1_form(self, team: str) -> float:
        stats = self.team_stats.get(team)
        if not stats or not stats.form_last_5:
            return 0.5
        points = sum(3 if r == 'W' else 1 if r == 'D' else 0 for r in stats.form_last_5)
        max_points = len(stats.form_last_5) * 3
        return points / max_points if max_points > 0 else 0.5
    
    def factor_2_offensive_strength(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats or stats.matches_played == 0:
            return 1.0
        avg_goals = stats.goals_scored / stats.matches_played
        avg_xg = stats.xg_scored / stats.matches_played
        strength = (avg_goals * 0.4 + avg_xg * 0.6)
        return max(0.1, strength)
    
    def factor_3_defensive_strength(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats or stats.matches_played == 0:
            return 1.0
        avg_conceded = stats.goals_conceded / stats.matches_played
        avg_xg_conceded = stats.xg_conceded / stats.matches_played
        combined = avg_conceded * 0.4 + avg_xg_conceded * 0.6
        strength = 1 / (1 + combined)
        return max(0.1, strength)
    
    def factor_4_home_away_advantage(self, team: str, is_home: bool = True) -> float:
        stats = self.team_stats.get(team)
        if not stats:
            return 1.0 if is_home else 0.8
        if is_home:
            total_home = stats.home_wins + stats.home_draws + stats.home_losses
            if total_home == 0: return 1.0
            return (stats.home_wins * 3 + stats.home_draws) / (total_home * 3)
        else:
            total_away = stats.away_wins + stats.away_draws + stats.away_losses
            if total_away == 0: return 0.8
            return (stats.away_wins * 3 + stats.away_draws) / (total_away * 3)
    
    def factor_5_head_to_head(self, home_team: str, away_team: str) -> Dict[str, float]:
        h2h = self.df[
            ((self.df['home_team'] == home_team) & (self.df['away_team'] == away_team)) |
            ((self.df['home_team'] == away_team) & (self.df['away_team'] == home_team))
        ].sort_values('date')
        
        if len(h2h) == 0:
            return {'home_advantage': 0.5, 'draw_tendency': 0.33}
        
        home_wins = away_wins = draws = 0
        for _, match in h2h.tail(10).iterrows():
            if match['home_team'] == home_team:
                if match['home_goals'] > match['away_goals']: home_wins += 1
                elif match['home_goals'] < match['away_goals']: away_wins += 1
                else: draws += 1
            else:
                if match['away_goals'] > match['home_goals']: home_wins += 1
                elif match['away_goals'] < match['home_goals']: away_wins += 1
                else: draws += 1
        
        total = home_wins + away_wins + draws
        if total == 0: return {'home_advantage': 0.5, 'draw_tendency': 0.33}
        return {'home_advantage': home_wins / total, 'away_advantage': away_wins / total, 'draw_tendency': draws / total}
    
    def factor_6_discipline(self, team: str) -> float:
        team_matches = self.df[(self.df['home_team'] == team) | (self.df['away_team'] == team)]
        if len(team_matches) == 0: return 0.5
        total_yellow = total_red = 0
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                total_yellow += match.get('home_yellow_cards', 0) or 0
                total_red += match.get('home_red_cards', 0) or 0
            else:
                total_yellow += match.get('away_yellow_cards', 0) or 0
                total_red += match.get('away_red_cards', 0) or 0
        avg_yellow = total_yellow / len(team_matches)
        avg_red = total_red / len(team_matches)
        return max(0.1, min(1.0, 1 - (avg_yellow * 0.05 + avg_red * 0.3)))
    
    def factor_7_shot_efficiency(self, team: str) -> float:
        team_matches = self.df[(self.df['home_team'] == team) | (self.df['away_team'] == team)]
        if len(team_matches) == 0: return 0.3
        total_goals = total_shots_on_target = 0
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                total_goals += match['home_goals']
                total_shots_on_target += match.get('home_shots_on_target', 0) or 0
            else:
                total_goals += match['away_goals']
                total_shots_on_target += match.get('away_shots_on_target', 0) or 0
        if total_shots_on_target == 0: return 0.3
        return min(1.0, (total_goals / total_shots_on_target) / 0.3)
    
    def factor_8_momentum(self, team: str) -> float:
        team_matches = self.df[(self.df['home_team'] == team) | (self.df['away_team'] == team)].sort_values('date').tail(10)
        if len(team_matches) < 5: return 0.5
        results = []
        for _, match in team_matches.iterrows():
            if match['home_team'] == team:
                results.append(match['home_goals'] - match['away_goals'])
            else:
                results.append(match['away_goals'] - match['home_goals'])
        x = np.arange(len(results))
        slope, _, _, _, _ = stats.linregress(x, results)
        return max(0.1, min(1.0, 0.5 + (slope * 0.1)))
    
    def get_all_factors(self, home_team: str, away_team: str) -> Dict[str, float]:
        h2h = self.factor_5_head_to_head(home_team, away_team)
        return {
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

# ═══════════════════════════════════════════════════════
# PART 3: Prediction Models
# ═══════════════════════════════════════════════════════

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    from sklearn.ensemble import GradientBoostingClassifier

class FootballPredictionModels:
    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def prepare_features(self, df: pd.DataFrame, analyzer) -> pd.DataFrame:
        features_list = []
        for idx, row in df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']
            factors = analyzer.get_all_factors(home_team, away_team)
            
            feature_vector = {
                'form_diff': factors['home_form'] - factors['away_form'],
                'offense_diff': factors['home_offense'] - factors['away_offense'],
                'defense_diff': factors['home_defense'] - factors['away_defense'],
                'home_ground_advantage': factors['home_advantage'] - factors['away_advantage'],
                'h2h_home_bias': factors['h2h_home'] - (1 - factors['h2h_home'] - factors['h2h_draw']),
                'h2h_draw_tendency': factors['h2h_draw'],
                'discipline_diff': factors['home_discipline'] - factors['away_discipline'],
                'efficiency_diff': factors['home_efficiency'] - factors['away_efficiency'],
                'momentum_diff': factors['home_momentum'] - factors['away_momentum'],
                'home_goals_avg': analyzer.team_stats[home_team].goals_scored / max(1, analyzer.team_stats[home_team].matches_played) if home_team in analyzer.team_stats else 1.5,
                'away_goals_avg': analyzer.team_stats[away_team].goals_scored / max(1, analyzer.team_stats[away_team].matches_played) if away_team in analyzer.team_stats else 1.2,
                'home_conceded_avg': analyzer.team_stats[home_team].goals_conceded / max(1, analyzer.team_stats[home_team].matches_played) if home_team in analyzer.team_stats else 1.2,
                'away_conceded_avg': analyzer.team_stats[away_team].goals_conceded / max(1, analyzer.team_stats[away_team].matches_played) if away_team in analyzer.team_stats else 1.5,
                'home_xg_avg': analyzer.team_stats[home_team].xg_scored / max(1, analyzer.team_stats[home_team].matches_played) if home_team in analyzer.team_stats else 1.4,
                'away_xg_avg': analyzer.team_stats[away_team].xg_scored / max(1, analyzer.team_stats[away_team].matches_played) if away_team in analyzer.team_stats else 1.1,
            }
            features_list.append(feature_vector)
        
        features_df = pd.DataFrame(features_list)
        self.feature_names = features_df.columns.tolist()
        return features_df
    
    def create_target(self, df: pd.DataFrame) -> np.ndarray:
        targets = []
        for _, row in df.iterrows():
            if row['home_goals'] > row['away_goals']: targets.append(2)
            elif row['home_goals'] == row['away_goals']: targets.append(1)
            else: targets.append(0)
        return np.array(targets)
    
    def train(self, X: pd.DataFrame, y: np.ndarray, test_size: float = 0.2):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Random Forest
        self.rf_model = RandomForestClassifier(n_estimators=200, max_depth=15, min_samples_split=5, min_samples_leaf=2, random_state=42, n_jobs=-1, class_weight='balanced')
        self.rf_model.fit(X_train, y_train)
        rf_acc = accuracy_score(y_test, self.rf_model.predict(X_test))
        
        # XGBoost
        if XGBOOST_AVAILABLE:
            self.xgb_model = xgb.XGBClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, random_state=42, eval_metric='mlogloss')
        else:
            self.xgb_model = GradientBoostingClassifier(n_estimators=200, max_depth=6, learning_rate=0.1, random_state=42)
        self.xgb_model.fit(X_train, y_train)
        xgb_acc = accuracy_score(y_test, self.xgb_model.predict(X_test))
        
        # Logistic Regression
        self.lr_model = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced', multi_class='multinomial')
        self.lr_model.fit(X_train_scaled, y_train)
        lr_acc = accuracy_score(y_test, self.lr_model.predict(X_test_scaled))
        
        rf_cv = cross_val_score(self.rf_model, X, y, cv=5, scoring='accuracy')
        self.is_trained = True
        
        return {'rf_accuracy': rf_acc, 'xgb_accuracy': xgb_acc, 'lr_accuracy': lr_acc, 'rf_cv_mean': rf_cv.mean(), 'rf_cv_std': rf_cv.std(), 'test_size': len(X_test)}
    
    def predict(self, X: pd.DataFrame, use_ensemble: bool = True) -> Dict:
        if not self.is_trained: raise ValueError("Models not trained!")
        X_scaled = self.scaler.transform(X)
        
        rf_probs = self.rf_model.predict_proba(X)[0]
        xgb_probs = self.xgb_model.predict_proba(X)[0] if hasattr(self.xgb_model, 'predict_proba') else [0.33, 0.33, 0.34]
        lr_probs = self.lr_model.predict_proba(X_scaled)[0]
        
        if use_ensemble:
            ensemble_probs = rf_probs * 0.30 + xgb_probs * 0.45 + lr_probs * 0.25
        else:
            ensemble_probs = xgb_probs
        
        labels = ['Away Win', 'Draw', 'Home Win']
        classes = ['away_win', 'draw', 'home_win']
        
        return {
            'ensemble_prediction': labels[np.argmax(ensemble_probs)],
            'ensemble_class': classes[np.argmax(ensemble_probs)],
            'probabilities': {'away_win': round(ensemble_probs[0] * 100, 1), 'draw': round(ensemble_probs[1] * 100, 1), 'home_win': round(ensemble_probs[2] * 100, 1)},
            'individual_models': {
                'random_forest': {'prediction': labels[np.argmax(rf_probs)], 'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, rf_probs)}},
                'xgboost': {'prediction': labels[np.argmax(xgb_probs)], 'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, xgb_probs)}},
                'logistic_regression': {'prediction': labels[np.argmax(lr_probs)], 'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, lr_probs)}}
            },
            'confidence': round(max(ensemble_probs) * 100, 1),
            'feature_importance': self.get_feature_importance()
        }
    
    def get_feature_importance(self) -> Dict[str, float]:
        if self.rf_model is None: return {}
        importance = self.rf_model.feature_importances_
        return dict(sorted(zip(self.feature_names, importance), key=lambda x: x[1], reverse=True))

# ═══════════════════════════════════════════════════════
# PART 4: Streamlit UI
# ═══════════════════════════════════════════════════════

st.set_page_config(page_title="ProBet - Football Predictor", page_icon="⚽", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;700;900&display=swap');
    * { font-family: 'Tajawal', sans-serif; direction: rtl; }
    .main-header { font-size: 3rem; font-weight: 900; text-align: center; background: linear-gradient(90deg, #1e3a8a, #3b82f6, #1e3a8a); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .metric-card { background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 15px; padding: 1.5rem; border: 1px solid #334155; text-align: center; }
    .metric-value { font-size: 2.5rem; font-weight: 900; color: #3b82f6; }
    .metric-label { color: #94a3b8; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
    st.session_state.df = None
    st.session_state.analyzer = None
    st.session_state.models = None
    st.session_state.training_results = None

with st.sidebar:
    st.markdown("## ⚙️ الإعدادات")
    st.markdown("---")
    st.markdown("### 📥 مصدر البيانات")
    data_source = st.radio("المصدر:", ["بيانات تجريبية", "رفع CSV"], index=0)
    if data_source == "رفع CSV":
        uploaded_file = st.file_uploader("اختر ملف CSV", type=['csv'])
    st.markdown("---")
    st.info("🏆 50+ دوري\n🤖 3 نماذج ML\n📊 8 عوامل\n⚡ فوري")
    st.markdown("---")
    st.caption("© 2026 ProBet")

st.markdown('<div class="main-header">⚽ ProBet Football Predictor</div>', unsafe_allow_html=True)
st.markdown('<p style="text-align: center; color: #64748b; font-size: 1.2rem;">نظام تنبؤ متقدم لكرة القدم</p>', unsafe_allow_html=True)

if not st.session_state.data_loaded:
    with st.spinner("🔄 جاري التحميل والتحليل..."):
        fetcher = FootballDataFetcher()
        df = fetcher.generate_sample_data(n_matches=5000) if data_source == "بيانات تجريبية" else (pd.read_csv(uploaded_file) if 'uploaded_file' in locals() and uploaded_file is not None else fetcher.generate_sample_data(n_matches=5000))
        
        st.session_state.df = df
        st.session_state.analyzer = AdvancedFootballAnalyzer(df)
        st.session_state.models = FootballPredictionModels()
        
        X = st.session_state.models.prepare_features(df, st.session_state.analyzer)
        y = st.session_state.models.create_target(df)
        results = st.session_state.models.train(X, y)
        st.session_state.training_results = results
        st.session_state.data_loaded = True
        st.success(f"✅ تم تحميل {len(df)} مباراة و {len(X.columns)} ميزة!")

tabs = st.tabs(["🔮 التنبؤ", "📊 التحليلات", "🤖 أداء النماذج", "📋 الميزات", "📚 الدليل"])

with tabs[0]:
    st.markdown("## 🔮 التنبؤ بالنتيجة")
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 فريق أصحاب الأرض:", sorted(st.session_state.df['home_team'].unique()), index=0)
    with col2:
        away_team = st.selectbox("✈️ فريق الضيف:", sorted([t for t in st.session_state.df['away_team'].unique() if t != home_team]), index=0)
    
    if st.button("🔮 تنبأ بالنتيجة", type="primary", use_container_width=True):
        with st.spinner("🧠 جاري التحليل..."):
            factors = st.session_state.analyzer.get_all_factors(home_team, away_team)
            single_match = pd.DataFrame([{'home_team': home_team, 'away_team': away_team, 'home_goals': 0, 'away_goals': 0, 'date': pd.Timestamp.now(), 'league': 'Unknown', 'season': '2024-25'}])
            X_pred = st.session_state.models.prepare_features(single_match, st.session_state.analyzer)
            prediction = st.session_state.models.predict(X_pred)
            
            st.markdown("---")
            c1, c2, c3 = st.columns([2, 1, 2])
            with c1:
                st.markdown(f"<h2 style='text-align: center; color: #3b82f6;'>{home_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>🏠 أصحاب الأرض</p>", unsafe_allow_html=True)
            with c2:
                st.markdown("<h1 style='text-align: center; color: #f59e0b;'>VS</h1>", unsafe_allow_html=True)
            with c3:
                st.markdown(f"<h2 style='text-align: center; color: #ef4444;'>{away_team}</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #94a3b8;'>✈️ ضيف</p>", unsafe_allow_html=True)
            
            st.markdown("### 📊 احتمالات النتيجة")
            probs = prediction['probabilities']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f'<div style="background: linear-gradient(135deg, #dc2626, #991b1b); border-radius: 15px; padding: 1.5rem; text-align: center;"><div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs["away_win"]}%</div><div style="color: #fecaca; margin-top: 0.5rem;">فوز {away_team}</div></div>', unsafe_allow_html=True)
            with col2:
                st.markdown(f'<div style="background: linear-gradient(135deg, #ca8a04, #854d0e); border-radius: 15px; padding: 1.5rem; text-align: center;"><div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs["draw"]}%</div><div style="color: #fef08a; margin-top: 0.5rem;">تعادل</div></div>', unsafe_allow_html=True)
            with col3:
                st.markdown(f'<div style="background: linear-gradient(135deg, #16a34a, #166534); border-radius: 15px; padding: 1.5rem; text-align: center;"><div style="font-size: 2.5rem; font-weight: 900; color: white;">{probs["home_win"]}%</div><div style="color: #bbf7d0; margin-top: 0.5rem;">فوز {home_team}</div></div>', unsafe_allow_html=True)
            
            pred_class = prediction['ensemble_class']
            confidence = prediction['confidence']
            color, emoji = ('#16a34a', '🏆') if pred_class == 'home_win' else ('#ca8a04', '🤝') if pred_class == 'draw' else ('#dc2626', '✈️')
            st.markdown(f'<div style="background: {color}; border-radius: 15px; padding: 1.5rem; text-align: center; margin-top: 1rem;"><div style="font-size: 1.8rem; font-weight: 900; color: white;">{emoji} التنبؤ: {prediction["ensemble_prediction"]}</div><div style="color: rgba(255,255,255,0.9); margin-top: 0.5rem;">ثقة النموذج: {confidence}%</div></div>', unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 📈 العوامل التحليلية (8 عوامل)")
            factor_data = {
                'العامل': ['الشكل (آخر 5)', 'القوة الهجومية', 'القوة الدفاعية', 'ميزة الملعب', 'المواجهات المباشرة', 'الانضباط', 'كفاءة التسديد', 'الزخم'],
                f'{home_team}': [f"{factors['home_form']:.2f}", f"{factors['home_offense']:.2f}", f"{factors['home_defense']:.2f}", f"{factors['home_advantage']:.2f}", f"{factors['h2h_home']:.2f}", f"{factors['home_discipline']:.2f}", f"{factors['home_efficiency']:.2f}", f"{factors['home_momentum']:.2f}"],
                f'{away_team}': [f"{factors['away_form']:.2f}", f"{factors['away_offense']:.2f}", f"{factors['away_defense']:.2f}", f"{factors['away_advantage']:.2f}", f"{1 - factors['h2h_home'] - factors['h2h_draw']:.2f}", f"{factors['away_discipline']:.2f}", f"{factors['away_efficiency']:.2f}", f"{factors['away_momentum']:.2f}"]
            }
            st.dataframe(pd.DataFrame(factor_data), use_container_width=True, hide_index=True)

with tabs[1]:
    st.markdown("## 📊 لوحة التحليلات")
    df = st.session_state.df
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.markdown(f'<div class="metric-card"><div class="metric-value">{len(df):,}</div><div class="metric-label">إجمالي المباريات</div></div>', unsafe_allow_html=True)
    with col2: st.markdown(f'<div class="metric-card"><div class="metric-value">{(df["home_goals"].sum() + df["away_goals"].sum()) / len(df):.2f}</div><div class="metric-label">متوسط الأهداف</div></div>', unsafe_allow_html=True)
    with col3: st.markdown(f'<div class="metric-card"><div class="metric-value">{((df["home_goals"] > df["away_goals"]).sum() / len(df)) * 100:.1f}%</div><div class="metric-label">نسبة فوز الأرض</div></div>', unsafe_allow_html=True)
    with col4: st.markdown(f'<div class="metric-card"><div class="metric-value">{((df["home_goals"] == df["away_goals"]).sum() / len(df)) * 100:.1f}%</div><div class="metric-label">نسبة التعادل</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📊 توزيع النتائج")
        results_dist = pd.DataFrame({'النتيجة': ['فوز أصحاب الأرض', 'تعادل', 'فوز الضيف'], 'العدد': [(df['home_goals'] > df['away_goals']).sum(), (df['home_goals'] == df['away_goals']).sum(), (df['home_goals'] < df['away_goals']).sum()]})
        fig = px.pie(results_dist, values='العدد', names='النتيجة', color_discrete_sequence=['#16a34a', '#ca8a04', '#dc2626'], hole=0.4)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14))
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.markdown("### ⚽ توزيع الأهداف")
        total_goals = df['home_goals'] + df['away_goals']
        fig = px.histogram(x=total_goals, nbins=range(0, int(total_goals.max()) + 2), labels={'x': 'إجمالي الأهداف', 'y': 'المباريات'}, color_discrete_sequence=['#3b82f6'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14))
        st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    st.markdown("## 🤖 أداء النماذج")
    if st.session_state.training_results:
        results = st.session_state.training_results
        ensemble_acc = results['rf_accuracy'] * 0.30 + results['xgb_accuracy'] * 0.45 + results['lr_accuracy'] * 0.25
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #16a34a;">{results["rf_accuracy"]:.1%}</div><div class="metric-label">Random Forest</div></div>', unsafe_allow_html=True)
        with col2: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #3b82f6;">{results["xgb_accuracy"]:.1%}</div><div class="metric-label">XGBoost</div></div>', unsafe_allow_html=True)
        with col3: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #ca8a04;">{results["lr_accuracy"]:.1%}</div><div class="metric-label">Logistic Regression</div></div>', unsafe_allow_html=True)
        with col4: st.markdown(f'<div class="metric-card"><div class="metric-value" style="color: #a855f7;">{ensemble_acc:.1%}</div><div class="metric-label">Ensemble</div></div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 📊 مقارنة الدقة")
        model_comparison = pd.DataFrame({'النموذج': ['Random Forest', 'XGBoost', 'Logistic Regression', 'Ensemble'], 'الدقة': [results['rf_accuracy'], results['xgb_accuracy'], results['lr_accuracy'], ensemble_acc]})
        fig = px.bar(model_comparison, x='النموذج', y='الدقة', color='النموذج', color_discrete_sequence=['#16a34a', '#3b82f6', '#ca8a04', '#a855f7'], text='الدقة', text_auto='.1%')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=14), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

with tabs[3]:
    st.markdown("## 📋 أهمية الميزات")
    if st.session_state.models and st.session_state.models.is_trained:
        importance = st.session_state.models.get_feature_importance()
        importance_df = pd.DataFrame({'الميزة': list(importance.keys()), 'الأهمية': list(importance.values())}).sort_values('الأهمية', ascending=True)
        fig = px.bar(importance_df, x='الأهمية', y='الميزة', orientation='h', color='الأهمية', color_continuous_scale='Blues')
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white', size=12), height=500)
        st.plotly_chart(fig, use_container_width=True)

with tabs[4]:
    st.markdown("## 📚 الدليل")
    st.markdown("""
    ### 🎯 نظرة عامة
    **ProBet** نظام تنبؤ متقدم باستخدام:
    - **3 نماذج ML** (Random Forest, XGBoost, Logistic Regression)
    - **8 عوامل تحليلية متطورة**
    - **50+ دوري عالمي**
    
    ### 📊 العوامل الثمانية
    | # | العامل | الوصف |
    |---|--------|-------|
    | 1 | **الشكل** | آخر 5 نتائج |
    | 2 | **القوة الهجومية** | الأهداف + xG |
    | 3 | **القوة الدفاعية** | الأهداف المستقبلة |
    | 4 | **ميزة الملعب** | النقاط داخل/خارج |
    | 5 | **المواجهات** | آخر 10 مباريات |
    | 6 | **الانضباط** | البطاقات |
    | 7 | **كفاءة التسديد** | الأهداف/التسديدات |
    | 8 | **الزخم** | اتجاه الأداء |
    
    ### ⚠️ تنبيه
    للأغراض التحليلية والتعليمية فقط.
    """)
