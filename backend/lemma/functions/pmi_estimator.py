"""
Lemma Function: PMI Estimator
==============================
Wraps the existing ML-based PMI prediction service as a Lemma Function.
"""
from __future__ import annotations
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("aegis.fn.pmi_estimator")


def estimate_pmi(
    age: float,
    sex: str,
    height: float,
    weight: float,
    putrefaction: int,
    putre_level: str,
    rigor_mortis: str,
    livor_mortis: str,
    algor_mortis: float,
    stomach_contents: str,
    vitreous_potassium: float,
    entomology: str,
) -> Dict[str, Any]:
    """
    Estimate Postmortem Interval (PMI) in hours from forensic features.
    Wraps the trained RandomForest model from the existing backend.

    Returns:
        {
          "predicted_pmi_hours": float,
          "confidence_score": float,
          "confidence_interval": {"low": float, "high": float},
          "explanation": dict,
          "interpretation": str,
          "error": Optional[str],
        }
    """
    result: Dict[str, Any] = {
        "predicted_pmi_hours": 0.0,
        "confidence_score": 0.0,
        "confidence_interval": {"low": 0.0, "high": 0.0},
        "explanation": {},
        "interpretation": "",
        "error": None,
    }

    try:
        # Re-use the existing PMI router's model
        from routers.pmi_router import model, extract_feature_importance
        import pandas as pd
        import numpy as np

        if model is None:
            # Try to load/train the model
            from routers.pmi_router import load_model
            load_model()
            from routers.pmi_router import model as m
            if m is None:
                result["error"] = "PMI model not available."
                return result

        input_data = {
            "Age": age, "Sex": sex, "Height": height, "Weight": weight,
            "Putrefaction": putrefaction, "Putre_level": putre_level,
            "Rigor Mortis": rigor_mortis, "Livor Mortis": livor_mortis,
            "Algor Mortis": algor_mortis, "Stomach Contents": stomach_contents,
            "Vitreous Potassium": vitreous_potassium, "Entomology": entomology,
        }
        df = pd.DataFrame([input_data])
        prediction = model.predict(df)[0]

        # Confidence via tree variance
        rf = model.named_steps["regressor"]
        preprocessed = model.named_steps["preprocessor"].transform(df)
        tree_preds = np.array([t.predict(preprocessed)[0] for t in rf.estimators_])
        std_dev = float(np.std(tree_preds))
        mean_pred = float(np.mean(tree_preds))
        cv = std_dev / mean_pred if mean_pred > 0 else 1.0
        confidence = max(0.0, min(100.0, (1 - cv) * 100))

        result["predicted_pmi_hours"] = round(float(prediction), 1)
        result["confidence_score"] = round(confidence, 1)
        result["confidence_interval"] = {
            "low": round(max(0.0, mean_pred - 2 * std_dev), 1),
            "high": round(mean_pred + 2 * std_dev, 1),
        }
        result["explanation"] = extract_feature_importance(model)
        result["interpretation"] = _interpret_pmi(prediction)

    except Exception as e:
        logger.error(f"PMI estimation error: {e}")
        result["error"] = str(e)
        # Provide rule-based fallback
        result.update(_rule_based_pmi(rigor_mortis, livor_mortis, putrefaction))

    return result


def _interpret_pmi(hours: float) -> str:
    if hours < 4:
        return "Very recent death (< 4 hours). Scene likely still active."
    if hours < 12:
        return f"Estimated {hours:.1f} hours since death. Early postmortem stage."
    if hours < 24:
        return f"Estimated {hours:.1f} hours (< 1 day). Full rigor mortis expected."
    if hours < 72:
        days = hours / 24
        return f"Estimated {days:.1f} days since death. Early decomposition stage."
    days = hours / 24
    return f"Estimated {days:.1f} days since death. Advanced decomposition."


def _rule_based_pmi(rigor: str, livor: str, putrefaction: int) -> Dict[str, Any]:
    """Rough rule-based fallback when model is unavailable."""
    hours = 12.0
    rigor_lower = rigor.lower() if rigor else ""
    if "absent" in rigor_lower:
        hours = 2.0
    elif "complete" in rigor_lower or "full" in rigor_lower:
        hours = 18.0
    elif "partial" in rigor_lower:
        hours = 8.0
    if putrefaction >= 2:
        hours = max(hours, 72.0)
    return {
        "predicted_pmi_hours": hours,
        "confidence_score": 30.0,
        "interpretation": f"Rule-based estimate: ~{hours:.0f} hours (model unavailable).",
    }
