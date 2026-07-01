"""
وحدة نماذج التعلم الآلي للتنبؤ بنتائج كرة القدم
3 نماذج: Random Forest, XGBoost, Logistic Regression
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score
import pickle
import logging
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, using GradientBoosting")
    from sklearn.ensemble import GradientBoostingClassifier


class FootballPredictionModels:
    """نظام التنبؤ متعدد النماذج"""
    
    def __init__(self):
        self.rf_model = None
        self.xgb_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        self.feature_names = []
        self.is_trained = False
        
    def prepare_features(self, df: pd.DataFrame, analyzer) -> pd.DataFrame:
        """تحضير الميزات من البيانات"""
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
        """إنشاء المتغير المستهدف"""
        targets = []
        for _, row in df.iterrows():
            if row['home_goals'] > row['away_goals']:
                targets.append(2)
            elif row['home_goals'] == row['away_goals']:
                targets.append(1)
            else:
                targets.append(0)
        return np.array(targets)
    
    def train(self, X: pd.DataFrame, y: np.ndarray, test_size: float = 0.2):
        """تدريب النماذج الثلاثة"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )
        
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        logger.info(f"Training size: {len(X_train)}")
        logger.info(f"Test size: {len(X_test)}")
        
        # Random Forest
        logger.info("Training Random Forest...")
        self.rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1,
            class_weight='balanced'
        )
        self.rf_model.fit(X_train, y_train)
        rf_pred = self.rf_model.predict(X_test)
        rf_acc = accuracy_score(y_test, rf_pred)
        logger.info(f"Random Forest accuracy: {rf_acc:.3f}")
        
        # XGBoost
        logger.info("Training XGBoost...")
        if XGBOOST_AVAILABLE:
            self.xgb_model = xgb.XGBClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                eval_metric='mlogloss'
            )
        else:
            self.xgb_model = GradientBoostingClassifier(
                n_estimators=200,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        
        self.xgb_model.fit(X_train, y_train)
        xgb_pred = self.xgb_model.predict(X_test)
        xgb_acc = accuracy_score(y_test, xgb_pred)
        logger.info(f"XGBoost accuracy: {xgb_acc:.3f}")
        
        # Logistic Regression
        logger.info("Training Logistic Regression...")
        self.lr_model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight='balanced',
            multi_class='multinomial'
        )
        self.lr_model.fit(X_train_scaled, y_train)
        lr_pred = self.lr_model.predict(X_test_scaled)
        lr_acc = accuracy_score(y_test, lr_pred)
        logger.info(f"Logistic Regression accuracy: {lr_acc:.3f}")
        
        # Cross-validation
        logger.info("\nCross-validation (5-fold):")
        rf_cv = cross_val_score(self.rf_model, X, y, cv=5, scoring='accuracy')
        logger.info(f"Random Forest CV: {rf_cv.mean():.3f} (+/- {rf_cv.std():.3f})")
        
        self.is_trained = True
        
        return {
            'rf_accuracy': rf_acc,
            'xgb_accuracy': xgb_acc,
            'lr_accuracy': lr_acc,
            'rf_cv_mean': rf_cv.mean(),
            'rf_cv_std': rf_cv.std(),
            'test_size': len(X_test)
        }
    
    def predict(self, X: pd.DataFrame, use_ensemble: bool = True) -> Dict:
        """التنبؤ بالنتيجة"""
        if not self.is_trained:
            raise ValueError("Models not trained yet!")
        
        X_scaled = self.scaler.transform(X)
        
        rf_probs = self.rf_model.predict_proba(X)[0]
        xgb_probs = self.xgb_model.predict_proba(X)[0] if hasattr(self.xgb_model, 'predict_proba') else [0.33, 0.33, 0.34]
        lr_probs = self.lr_model.predict_proba(X_scaled)[0]
        
        if use_ensemble:
            ensemble_probs = (
                rf_probs * 0.30 +
                xgb_probs * 0.45 +
                lr_probs * 0.25
            )
        else:
            ensemble_probs = xgb_probs
        
        labels = ['Away Win', 'Draw', 'Home Win']
        classes = ['away_win', 'draw', 'home_win']
        
        result = {
            'ensemble_prediction': labels[np.argmax(ensemble_probs)],
            'ensemble_class': classes[np.argmax(ensemble_probs)],
            'probabilities': {
                'away_win': round(ensemble_probs[0] * 100, 1),
                'draw': round(ensemble_probs[1] * 100, 1),
                'home_win': round(ensemble_probs[2] * 100, 1),
            },
            'individual_models': {
                'random_forest': {
                    'prediction': labels[np.argmax(rf_probs)],
                    'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, rf_probs)}
                },
                'xgboost': {
                    'prediction': labels[np.argmax(xgb_probs)],
                    'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, xgb_probs)}
                },
                'logistic_regression': {
                    'prediction': labels[np.argmax(lr_probs)],
                    'probabilities': {k: round(v * 100, 1) for k, v in zip(classes, lr_probs)}
                }
            },
            'confidence': round(max(ensemble_probs) * 100, 1),
            'feature_importance': self.get_feature_importance()
        }
        
        return result
    
    def get_feature_importance(self) -> Dict[str, float]:
        """أهمية الميزات"""
        if self.rf_model is None:
            return {}
        
        importance = self.rf_model.feature_importances_
        return dict(sorted(
            zip(self.feature_names, importance),
            key=lambda x: x[1],
            reverse=True
        ))
    
    def save_models(self, path: str):
        """حفظ النماذج"""
        models_dict = {
            'rf_model': self.rf_model,
            'xgb_model': self.xgb_model,
            'lr_model': self.lr_model,
            'scaler': self.scaler,
            'feature_names': self.feature_names
        }
        with open(path, 'wb') as f:
            pickle.dump(models_dict, f)
        logger.info(f"Models saved to {path}")
    
    def load_models(self, path: str):
        """تحميل النماذج"""
        with open(path, 'rb') as f:
            models_dict = pickle.load(f)
        self.rf_model = models_dict['rf_model']
        self.xgb_model = models_dict['xgb_model']
        self.lr_model = models_dict['lr_model']
        self.scaler = models_dict['scaler']
        self.feature_names = models_dict['feature_names']
        self.is_trained = True
        logger.info(f"Models loaded from {path}")
