

from __future__ import annotations
import os
import random
from typing import Optional

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split

router = APIRouter(prefix="/ml", tags=["ML Predictions"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "ml_data")
os.makedirs(DATA_DIR, exist_ok=True)

# ─────────────────────────────────────────────
#  MODEL CACHE  (train once per process)
# ─────────────────────────────────────────────
_MODELS: dict = {}



def _train_cost_model():
    fp = os.path.join(DATA_DIR, "cost_dataset.csv")
    if not os.path.exists(fp):
        rows = []
        for _ in range(3000):
            budget = random.randint(20000, 150000)
            duration = random.randint(3, 18)
            team_size = random.randint(2, 15)
            complexity = random.randint(1, 5)
            risk = random.uniform(0.8, 1.5)
            actual = (budget * risk) + (complexity * 4000) + (duration * 1500) - (team_size * 800)
            actual = max(actual, budget * 0.7)
            rows.append([budget, duration, team_size, complexity, actual])
        pd.DataFrame(
            rows, columns=["budget", "duration", "team_size", "complexity", "actual_cost"]
        ).to_csv(fp, index=False)

    df = pd.read_csv(fp)
    df["cost_per_person"] = df["budget"] / df["team_size"]
    X = df[["budget", "duration", "team_size", "complexity", "cost_per_person"]]
    y = df["actual_cost"]
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestRegressor(
        n_estimators=300, max_depth=10, min_samples_split=5,
        min_samples_leaf=2, random_state=42,
    )
    m.fit(Xtr, ytr)
    return m


class CostOverrunIn(BaseModel):
    budget: float = Field(..., gt=0)
    ac: float = Field(..., ge=0, description="Actual cost so far")
    cpi: float = Field(..., gt=0)
    spi: float = Field(..., gt=0)
    duration: Optional[int] = Field(default=12, ge=1)
    team_size: Optional[int] = Field(default=6, ge=1)
    complexity: Optional[int] = Field(default=3, ge=1, le=5)


@router.post("/cost-overrun")
def predict_cost_overrun(body: CostOverrunIn):
    if "cost" not in _MODELS:
        _MODELS["cost"] = _train_cost_model()

    feat = pd.DataFrame([{
        "budget": body.budget,
        "duration": body.duration,
        "team_size": body.team_size,
        "complexity": body.complexity,
        "cost_per_person": body.budget / max(body.team_size, 1),
    }])

    predicted_actual_cost = float(_MODELS["cost"].predict(feat)[0])
    overrun_amount = predicted_actual_cost - body.budget
    overrun_pct = (overrun_amount / body.budget) * 100

    # Derive probability_of_overrun from CPI and predicted overage ratio
    # CPI < 1 means spending more than earned → higher overrun probability
    cpi_factor = max(0.0, min(1.0, (2.0 - body.cpi) / 2.0))
    predicted_ratio = max(0.0, overrun_amount / body.budget)
    prob_overrun = round(min(1.0, max(0.0, (cpi_factor * 0.6 + min(predicted_ratio, 1.0) * 0.4))), 3)

    if prob_overrun >= 0.65:
        risk_level = "High"
    elif prob_overrun >= 0.40:
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # predicted_eac = Estimate at Completion
    predicted_eac = round(predicted_actual_cost, 2)
    # predicted_variance: positive = under budget, negative = over budget
    predicted_variance = round(body.budget - predicted_actual_cost, 2)

    # Confidence: tree estimator variance → use std of individual tree preds
    individual_preds = [t.predict(feat)[0] for t in _MODELS["cost"].estimators_]
    std_dev = float(np.std(individual_preds))
    confidence = round(max(0.5, min(0.99, 1.0 - std_dev / max(predicted_actual_cost, 1))), 3)

    return {
        "prediction": "Overrun" if overrun_amount > 0 else "On Budget",
        "probability_of_overrun": prob_overrun,
        "risk_level": risk_level,
        "predicted_eac": predicted_eac,
        "predicted_variance": predicted_variance,
        "confidence": confidence,
        "model": "RandomForestRegressor",
        # extra context
        "overrun_amount": round(overrun_amount, 2),
        "overrun_percent": round(overrun_pct, 2),
        "current_cpi": body.cpi,
        "current_spi": body.spi,
    }


def _train_delay_model():
    fp = os.path.join(DATA_DIR, "delay_dataset.csv")
    if not os.path.exists(fp):
        rows = []
        for _ in range(3000):
            planned = random.randint(3, 18)
            team = random.randint(2, 15)
            complexity = random.randint(1, 5)
            bugs = random.randint(0, 50)
            pending = random.randint(0, 40)
            progress = random.randint(20, 100)
            risk = random.uniform(0.5, 1.5)
            score = (progress * 0.4) + (team * 2) - (complexity * 5) - (bugs * 0.3) - (pending * 0.4)
            status = "OnTime" if score > 60 else "Risk" if score > 40 else "Delay"
            rows.append([planned, team, complexity, bugs, pending, progress, risk, status])
        pd.DataFrame(rows, columns=[
            "planned_duration", "team_size", "complexity", "bugs",
            "pending_tasks", "progress", "risk", "status"
        ]).to_csv(fp, index=False)

    df = pd.read_csv(fp)
    X = df[["planned_duration", "team_size", "complexity", "bugs",
            "pending_tasks", "progress", "risk"]]
    y = df["status"]
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestClassifier(n_estimators=200, random_state=42)
    m.fit(Xtr, ytr)
    return m


class ScheduleSlipIn(BaseModel):
    planned_duration_days: float = Field(..., gt=0)
    elapsed_days: float = Field(..., ge=0)
    spi: float = Field(..., gt=0)
    completed_pct: float = Field(..., ge=0, le=100)
    team_size: Optional[int] = Field(default=6, ge=1)
    complexity: Optional[int] = Field(default=3, ge=1, le=5)
    bugs: Optional[int] = Field(default=5, ge=0)
    pending_tasks: Optional[int] = Field(default=10, ge=0)


@router.post("/schedule-slip")
def predict_schedule_slip(body: ScheduleSlipIn):
    if "delay" not in _MODELS:
        _MODELS["delay"] = _train_delay_model()

    planned = max(int(round(body.planned_duration_days / 30)), 1)
    risk = 1 / max(body.spi, 0.01)

    feat = pd.DataFrame([{
        "planned_duration": planned,
        "team_size": body.team_size,
        "complexity": body.complexity,
        "bugs": body.bugs,
        "pending_tasks": body.pending_tasks,
        "progress": body.completed_pct,
        "risk": risk,
    }])

    pred_label = str(_MODELS["delay"].predict(feat)[0])
    proba = _MODELS["delay"].predict_proba(feat)[0]
    classes = list(_MODELS["delay"].classes_)
    proba_dict = {c: round(float(p), 3) for c, p in zip(classes, proba)}

    # Map classifier output to probability_of_slip
    # "Delay" → high slip prob, "Risk" → medium, "OnTime" → low
    delay_prob   = proba_dict.get("Delay", 0.0)
    risk_prob    = proba_dict.get("Risk", 0.0)
    ontime_prob  = proba_dict.get("OnTime", 0.0)
    prob_slip = round(delay_prob + risk_prob * 0.5, 3)

    if pred_label == "Delay":
        risk_level = "High"
    elif pred_label == "Risk":
        risk_level = "Medium"
    else:
        risk_level = "Low"

    # Estimate delay in days based on SPI and remaining work
    remaining_pct = max(0.0, 100.0 - body.completed_pct) / 100.0
    remaining_days = body.planned_duration_days * remaining_pct
    if body.spi > 0 and body.spi < 1.0:
        expected_finish = remaining_days / body.spi
        predicted_finish_delay_days = max(0, int(round(expected_finish - remaining_days)))
    else:
        predicted_finish_delay_days = 0 if pred_label == "OnTime" else int(remaining_days * 0.1)

    # Confidence = max proba of top class
    confidence = round(float(max(proba)), 3)

    return {
        "prediction": pred_label,
        "probability_of_slip": prob_slip,
        "risk_level": risk_level,
        "predicted_finish_delay_days": predicted_finish_delay_days,
        "confidence": confidence,
        "model": "RandomForestClassifier",
        "probabilities": proba_dict,
        "spi": body.spi,
        "completed_pct": body.completed_pct,
    }



def _train_defects_model():
    fp = os.path.join(DATA_DIR, "defects_dataset.csv")
    if not os.path.exists(fp):
        rows = []
        for _ in range(2000):
            sp = random.randint(5, 100)
            team = random.randint(2, 15)
            past = random.randint(0, 30)
            qpi = random.uniform(0.5, 1.0)
            future = max(0, int(past * (1.5 - qpi) + sp / max(team, 1) * 0.2 + random.gauss(0, 2)))
            rows.append([sp, team, past, qpi, future])
        pd.DataFrame(rows, columns=["story_points", "team_size",
                                     "past_defects", "qpi", "future_defects"]
                     ).to_csv(fp, index=False)

    df = pd.read_csv(fp)
    X = df[["story_points", "team_size", "past_defects", "qpi"]]
    y = df["future_defects"]
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestRegressor(n_estimators=200, random_state=42)
    m.fit(Xtr, ytr)
    return m


class DefectsIn(BaseModel):
    story_points: float = Field(..., ge=0)
    team_size: int = Field(..., ge=1)
    past_defects: float = Field(..., ge=0)
    qpi: float = Field(..., ge=0, le=1.5)


@router.post("/defects")
def predict_defects(body: DefectsIn):
    if "defects" not in _MODELS:
        _MODELS["defects"] = _train_defects_model()

    feat = pd.DataFrame([{
        "story_points": body.story_points,
        "team_size": body.team_size,
        "past_defects": body.past_defects,
        "qpi": body.qpi,
    }])

    pred = float(_MODELS["defects"].predict(feat)[0])
    predicted_defects = round(pred, 1)

    # critical_share: lower QPI → higher share of critical defects
    # qpi is 0-1 (or 0-1.5), normalise to 0-1
    qpi_norm = min(1.0, body.qpi)
    critical_share = round(max(0.0, min(0.5, (1.0 - qpi_norm) * 0.5)), 3)

    # recommended QA hours: ~2h per defect + extra for critical ones
    critical_count = critical_share * predicted_defects
    recommended_qa_hours = round(predicted_defects * 2.0 + critical_count * 3.0, 1)

    # Confidence from tree variance
    individual_preds = [t.predict(feat)[0] for t in _MODELS["defects"].estimators_]
    std_dev = float(np.std(individual_preds))
    confidence = round(max(0.5, min(0.99, 1.0 - std_dev / max(pred + 1, 1))), 3)

    return {
        "prediction": predicted_defects,
        "predicted_defects_next_sprint": predicted_defects,
        "expected_defects_next_sprint": predicted_defects,
        "critical_share": critical_share,
        "recommended_qa_hours": recommended_qa_hours,
        "confidence": confidence,
        "model": "RandomForestRegressor",
        "inputs": body.dict(),
    }


# ─────────────────────────────────────────────
#  4) HEALTH  — Healthy / At Risk / Critical
#     Response matches HealthResult renderer:
#       predicted_health   ("Green"|"Yellow"|"Red")
#       probability        { Green: 0-1, Yellow: 0-1, Red: 0-1 }
#       confidence         (0-1)
#       model              (string)
# ─────────────────────────────────────────────
def _train_health_model():
    fp = os.path.join(DATA_DIR, "cpi_spi_dataset.csv")
    if not os.path.exists(fp):
        rows = []
        for _ in range(2000):
            PV = random.randint(10000, 100000)
            EV = random.randint(8000, PV)
            AC = random.randint(9000, 120000)
            t = random.randint(1, 12)
            CPI = EV / AC
            SPI = EV / PV
            status = ("Healthy" if CPI >= 1 and SPI >= 1
                      else "At Risk" if CPI >= 0.8 and SPI >= 0.8
                      else "Critical")
            rows.append([PV, EV, AC, t, CPI, SPI, status])
        pd.DataFrame(rows, columns=["PV", "EV", "AC", "time", "CPI", "SPI", "status"]
                     ).to_csv(fp, index=False)

    df = pd.read_csv(fp)
    X = df[["PV", "EV", "AC", "time", "CPI", "SPI"]]
    y = df["status"]
    Xtr, _, ytr, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    m = RandomForestClassifier(n_estimators=200, random_state=42)
    m.fit(Xtr, ytr)
    return m


class HealthIn(BaseModel):
    cpi: float = Field(..., gt=0)
    spi: float = Field(..., gt=0)
    qpi: float = Field(..., ge=0)
    team_velocity: float = Field(..., ge=0)
    pv: Optional[float] = Field(default=50000, gt=0)
    ev: Optional[float] = Field(default=45000, gt=0)
    ac: Optional[float] = Field(default=48000, gt=0)
    time: Optional[int] = Field(default=6, ge=1)


@router.post("/health")
def predict_health(body: HealthIn):
    if "health" not in _MODELS:
        _MODELS["health"] = _train_health_model()

    feat = pd.DataFrame([{
        "PV": body.pv, "EV": body.ev, "AC": body.ac,
        "time": body.time, "CPI": body.cpi, "SPI": body.spi,
    }])

    # Internal model classes: "Healthy", "At Risk", "Critical"
    pred_internal = str(_MODELS["health"].predict(feat)[0])
    proba = _MODELS["health"].predict_proba(feat)[0]
    classes = list(_MODELS["health"].classes_)
    proba_internal = {c: round(float(p), 3) for c, p in zip(classes, proba)}

    # Map internal labels → frontend colour labels the HealthResult renderer uses
    # HealthResult expects: predicted_health in {"Green","Yellow","Red"}
    #                       probability keys in {"Green","Yellow","Red"}
    label_map = {"Healthy": "Green", "At Risk": "Yellow", "Critical": "Red"}
    predicted_health = label_map.get(pred_internal, "Yellow")

    probability = {
        "Green":  proba_internal.get("Healthy", 0.0),
        "Yellow": proba_internal.get("At Risk", 0.0),
        "Red":    proba_internal.get("Critical", 0.0),
    }

    confidence = round(float(max(proba)), 3)

    return {
        "prediction": pred_internal,
        "predicted_health": predicted_health,
        "health_color": predicted_health,
        "probability": probability,
        "probabilities": proba_internal,
        "confidence": confidence,
        "model": "RandomForestClassifier",
        "qpi": body.qpi,
        "team_velocity": body.team_velocity,
    }
