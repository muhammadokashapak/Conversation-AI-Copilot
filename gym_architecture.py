"""
Gym & Fitness Center GoHighLevel (GHL) Sub-Account Production Architecture.
Contains complete schemas for Custom Fields, Tags Taxonomy, Sales Pipeline, Retention Pipeline,
and Lead Scoring Hysteresis logic.
"""

from typing import List, Dict, Any

GYM_CUSTOM_FIELDS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "Primary Fitness Goal",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Weight Loss", "Muscle Building", "General Health & Fitness", "Athletic Performance", "Post-Rehab / Mobility"]
    },
    {
        "name": "Exercise Experience",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Beginner (0-6 mo)", "Intermediate (1-2 yrs)", "Advanced (3+ yrs)"]
    },
    {
        "name": "Exercise Limitations",
        "dataType": "SINGLE_OPTIONS",
        "options": ["No", "Yes"]
    },
    {
        "name": "Limitation Category",
        "dataType": "SINGLE_OPTIONS",
        "options": ["None", "Lower Body / Knee", "Upper Body / Shoulder", "Back / Core", "Cardiovascular / Endurance"]
    },
    {
        "name": "Trainer Safety Notes",
        "dataType": "TEXT"
    },
    {
        "name": "Preferred Workout Time",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Early Morning (5am-8am)", "Morning (9am-12pm)", "Afternoon (1pm-4pm)", "Evening (5pm-9pm)"]
    },
    {
        "name": "Lead Score",
        "dataType": "NUMBER"
    },
    {
        "name": "Lead Tier",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Cold", "Warm", "Hot"]
    },
    {
        "name": "Score Last Evaluated Date",
        "dataType": "DATE"
    },
    {
        "name": "Membership Plan Type",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Month-to-Month Basic", "Annual VIP Uncapped", "Personal Training 1-on-1", "Student / Senior Pass", "Corporate Partner"]
    },
    {
        "name": "Membership Status",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Prospect", "Trial Active", "Member Active", "Membership Frozen", "Renewal Due", "Cancelled / Churned"]
    },
    {
        "name": "Trial Start Date",
        "dataType": "DATE"
    },
    {
        "name": "Trial Expiry Date",
        "dataType": "DATE"
    },
    {
        "name": "Membership Start Date",
        "dataType": "DATE"
    },
    {
        "name": "Membership Expiry Date",
        "dataType": "DATE"
    },
    {
        "name": "Last Facility Check-In",
        "dataType": "DATE"
    },
    {
        "name": "Churn Risk Score",
        "dataType": "SINGLE_OPTIONS",
        "options": ["Low", "Medium", "High", "Critical"]
    }
]

GYM_TAGS_TAXONOMY: List[str] = [
    # Sources
    "Src: Meta Ads", "Src: Google Ads", "Src: Referral", "Src: Walk-In", "Src: Organic",
    # States
    "State: Lead - New", "State: Contacted", "State: Qualified", "State: Trial - Booked",
    "State: Trial - Attended", "State: Trial - No Show", "State: Trial - Cancelled",
    "State: Member - Active", "State: Member - Frozen", "State: Member - Renewal Due", "State: Member - Churned",
    # Campaigns
    "Campaign: Active - SpeedToLead", "Campaign: Active - TrialReminders", "Campaign: Active - NoShowRecovery",
    "Campaign: Active - ConversionNurture", "Campaign: Active - RetentionReactivation",
    # Tiers
    "Tier: Cold", "Tier: Warm", "Tier: Hot"
]

GYM_SALES_PIPELINE = {
    "name": "Gym Lead-to-Member Sales Pipeline",
    "stages": [
        "New Lead",
        "Contact Attempted",
        "Engaged / Qualified",
        "Trial Booked",
        "Trial Attended",
        "Membership Offer Sent",
        "Closed Won (Member)",
        "Closed Lost / Disqualified"
    ]
}

GYM_RETENTION_PIPELINE = {
    "name": "Member Retention & Renewal Pipeline",
    "stages": [
        "New Member Onboarding",
        "Active Regular Member",
        "Renewal Upcoming (30D)",
        "Renewal In Discussion",
        "Renewed (Won)",
        "Churn Risk (Inactive 14D+)",
        "Cancelled / Churned"
    ]
}


def calculate_lead_tier_hysteresis(current_score: int, current_tier: str) -> str:
    """
    Calculates Lead Tier with 10-point Hysteresis Buffer Zone (60-69) to prevent flapping.
    - HOT: 70+ (Drops to Warm ONLY if score falls below 60)
    - WARM: 40-69
    - COLD: <40
    """
    if current_tier == "Hot":
        if current_score < 60:
            return "Warm" if current_score >= 40 else "Cold"
        return "Hot"
    else:
        if current_score >= 70:
            return "Hot"
        elif current_score >= 40:
            return "Warm"
        else:
            return "Cold"
