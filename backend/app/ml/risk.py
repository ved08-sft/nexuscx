"""
Risk calculation engine for NexusCX.
Combines WEKA model probability with sentiment and hold count to produce final risk score.
"""

from typing import Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Risk calculation weights (can be adjusted based on model performance)
RISK_WEIGHT_WEKA = 0.55
RISK_WEIGHT_SENTIMENT = 0.30
RISK_WEIGHT_HOLD = 0.15

# Hold count normalization factor (max hold count considered for normalization)
HOLD_COUNT_NORM_FACTOR = 3.0  # hold_count / 3.0, capped at 1.0


def sentiment_to_s_neg(sentiment: float) -> float:
    """
    Convert sentiment score [-1, 1] to negativity score [0, 1].
    S_neg = (1 - sentiment) / 2
    Maps: -1 -> 1.0 (most negative), 0 -> 0.5, 1 -> 0.0 (most positive)
    """
    return (1.0 - sentiment) / 2.0


def calculate_risk_components(
    weka_probability: float,
    sentiment_score: float,
    hold_count: float
) -> Dict[str, float]:
    """
    Calculate the individual components of the risk score.
    Returns dict with P_weka, S_neg, T_hold components.
    """
    # Validate inputs
    weka_prob = max(0.0, min(1.0, float(weka_probability)))
    sentiment = max(-1.0, min(1.0, float(sentiment_score)))
    hold_cnt = max(0.0, float(hold_count))

    # Calculate S_neg: (1 - sentiment) / 2
    s_neg = sentiment_to_s_neg(sentiment)

    # Calculate T_hold: min(hold_count / 3, 1)
    t_hold = min(hold_cnt / HOLD_COUNT_NORM_FACTOR, 1.0)

    return {
        "P_weka": weka_prob,
        "S_neg": s_neg,
        "T_hold": t_hold
    }


def calculate_risk_score(
    weka_probability: float,
    sentiment_score: float,
    hold_count: float
) -> float:
    """
    Calculate the final risk score using the formula:
    R = clip(0.55 * P_weka + 0.30 * S_neg + 0.15 * T_hold, 0, 1)
    where S_neg = (1 - sentiment) / 2 and T_hold = min(hold_count / 3, 1)
    """
    components = calculate_risk_components(weka_probability, sentiment_score, hold_count)

    # Apply the weighted formula
    risk_score = (
        RISK_WEIGHT_WEKA * components["P_weka"] +
        RISK_WEIGHT_SENTIMENT * components["S_neg"] +
        RISK_WEIGHT_HOLD * components["T_hold"]
    )

    # Clip to [0, 1] range
    return max(0.0, min(1.0, risk_score))


def get_risk_band(risk_score: float) -> str:
    """
    Convert risk score to risk band.
    Bands: Low <0.50, Medium 0.50-0.70, High 0.70-0.85, Critical >0.85
    """
    if risk_score < 0.50:
        return "low"
    elif risk_score < 0.70:
        return "medium"
    elif risk_score < 0.85:
        return "high"
    else:
        return "critical"


def is_critical_risk(risk_score: float) -> bool:
    """
    Check if risk score is in critical band (> 0.85).
    """
    return risk_score > 0.85


def calculate_risk_with_model(
    escalation_model_path: str,
    churn_model_path: str,
    features: Dict[str, Any],
    use_fallback: bool = False
) -> Dict[str, Any]:
    """
    Calculate risk score using WEKA models (with Python fallback).
    Returns comprehensive risk assessment.
    """
    # Prepare features for WEKA models
    # For escalation model: avg_handling_time_sec, past_escalation_count,
    #                      customer_sentiment_score, channel_type, ekyc_verified
    # For churn model: similar but potentially different features

    # Extract common features
    weka_features = {
        "avg_handling_time_sec": features.get("avg_handling_time_sec", 0.0),
        "past_escalation_count": features.get("past_escalation_count", 0),
        "customer_sentiment_score": features.get("customer_sentiment_score", 0.0),
        "channel_type": features.get("channel_type", "voice"),
        "ekyc_verified": features.get("ekyc_verified", False)
    }

    # Get escalation probability from WEKA model
    p_weka, weka_fallback = predict_escalation(escalation_model_path, weka_features)

    # For churn risk class, we would use a separate model
    # For now, we'll focus on escalation prediction as the primary risk factor
    # In a full implementation, we would also predict churn risk class

    # Calculate sentiment and hold components
    sentiment_score = weka_features["customer_sentiment_score"]
    hold_count = features.get("hold_count", 0)

    # Calculate final risk score
    risk_score = calculate_risk_score(p_weka, sentiment_score, hold_count)

    # Get risk band
    risk_band = get_risk_band(risk_score)

    # Determine if this is critical (triggers alert)
    is_critical = is_critical_risk(risk_score)

    return {
        "risk_score": risk_score,
        "risk_band": risk_band,
        "is_critical": is_critical,
        "components": {
            "P_weka": p_weka,
            "S_neg": sentiment_to_s_neg(sentiment_score),
            "T_hold": min(hold_count / HOLD_COUNT_NORM_FACTOR, 1.0)
        },
        "model_used": {
            "escalation_model": os.path.basename(escalation_model_path),
            "weka_available": not weka_fallback,
            "fallback_used": weka_fallback
        }
    }


# Convenience function for backward compatibility
def compute_risk(p_weka: float, s_neg: float, t_hold: float) -> float:
    """
    Legacy compatibility function.
    Computes risk from pre-calculated components.
    """
    risk_score = (
        RISK_WEIGHT_WEKA * p_weka +
        RISK_WEIGHT_SENTIMENT * s_neg +
        RISK_WEIGHT_HOLD * t_hold
    )
    return max(0.0, min(1.0, risk_score))