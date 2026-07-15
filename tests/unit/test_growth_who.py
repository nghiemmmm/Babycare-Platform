import pytest
from app.modules.growth_tracking.service import calculate_who_status
from app.modules.growth_tracking.utils import get_closest_standard, evaluate_metric


def test_who_standard_boy_newborn():
    # 0 months, boy
    std = get_closest_standard(gender="boy", age_months=0.0)
    
    # limits are weight: (2.5, 3.3, 4.4), height: (46.3, 49.9, 53.4)
    assert std["weight"] == (2.5, 3.3, 4.4)
    assert std["height"] == (46.3, 49.9, 53.4)


def test_evaluate_metric_normal():
    # value is normal (between low and high limits)
    status = evaluate_metric(value=3.5, limits=(2.5, 3.3, 4.4), low_label="underweight", high_label="overweight")
    assert status == "normal"


def test_evaluate_metric_low():
    # value is low
    status = evaluate_metric(value=2.0, limits=(2.5, 3.3, 4.4), low_label="underweight", high_label="overweight")
    assert status == "underweight"


def test_evaluate_metric_high():
    # value is high
    status = evaluate_metric(value=5.0, limits=(2.5, 3.3, 4.4), low_label="underweight", high_label="overweight")
    assert status == "overweight"


def test_calculate_who_status_3_months_boy():
    # Birthdate: 2026-01-15, Log date: 2026-04-15 (about 90 days, rounded to 3 months)
    # 3 months boy standards: weight: (5.0, 6.4, 8.0), height: (57.6, 61.4, 65.3)
    status = calculate_who_status(
        baby_birthday_str="2026-01-15",
        baby_gender="boy",
        log_date_str="2026-04-15T12:00:00Z",
        height=55.0,     # stunted (< 57.6)
        weight=9.0,      # overweight (> 8.0)
        head=35.0        # microcephaly (< 38.3)
    )
    
    assert status.age_in_months == 3.0
    assert status.height_status == "stunted"
    assert status.weight_status == "overweight"
    assert status.head_circumference_status == "microcephaly"
