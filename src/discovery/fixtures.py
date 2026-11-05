"""Realistic fixture data for Industrial Temperature Sensors supplier discovery and verification."""

from __future__ import annotations

from typing import Any, Dict, List

# Closed-set autocomplete results for industry resolution
FIXTURE_INDUSTRY_AUTOCOMPLETE = {
    "query": "temperature sensor",
    "suggestions": [
        "Industrial Automation & Instrumentation",
        "Electrical & Electronic Manufacturing",
        "Sensors & Measuring Instruments",
        "Mechanical or Industrial Engineering",
    ],
}

# Raw Crustdata POST /company/search response fixture
FIXTURE_COMPANY_SEARCH_RESULTS: Dict[str, Any] = {
    "status": "success",
    "total_results": 6,
    "credits_used": 0.18,
    "results": [
        {
            "name": "Alpha Thermal",
            "domain": "alpha-thermal.example",
            "year_founded": 1976,
            "industry": "Sensors & Measuring Instruments",
            "location": "City A, Region A, India",
            "country": "India",
            "relevance_score": 0.98,
        },
        {
            "name": "Bravo Electro",
            "domain": "bravo-electro.example",
            "year_founded": 1980,
            "industry": "Industrial Automation & Instrumentation",
            "location": "Mumbai, Maharashtra, India",
            "country": "India",
            "relevance_score": 0.94,
        },
        {
            "name": "Charlie Sensors",
            "domain": "charlie-sensors.example",
            "year_founded": 1952,
            "industry": "Electrical & Electronic Manufacturing",
            "location": "Pune, Maharashtra, India",
            "country": "India",
            "relevance_score": 0.91,
        },
        {
            "name": "Delta Pyro",
            "domain": "delta-pyro.example",
            "year_founded": 1977,
            "industry": "Sensors & Measuring Instruments",
            "location": "Bengaluru, Karnataka, India",
            "country": "India",
            "relevance_score": 0.88,
        },
        {
            # Designed with empty description to verify HUMAN_OR_SIMULATED status
            "name": "Echo Instruments",
            "domain": "echo-instruments.example",
            "year_founded": 2012,
            "industry": "Sensors & Measuring Instruments",
            "location": "Ahmedabad, Gujarat, India",
            "country": "India",
            "relevance_score": 0.82,
        },
        {
            # Duplicate of Alpha Thermal to test deduplication
            "name": "Alpha Thermal Pvt. Ltd.",
            "domain": "https://www.alpha-thermal.example/",
            "year_founded": 1976,
            "industry": "Sensors & Measuring Instruments",
            "location": "City A, Region A, India",
            "country": "India",
            "relevance_score": 0.79,
        },
    ],
}

# Raw Crustdata POST /company/identify responses (free)
FIXTURE_COMPANY_IDENTIFY_MAP: Dict[str, Dict[str, Any]] = {
    "alpha-thermal.example": {
        "crustdata_company_id": 918231,
        "name": "Alpha Thermal",
        "domain": "alpha-thermal.example",
        "verified": True,
    },
    "bravo-electro.example": {
        "crustdata_company_id": 847291,
        "name": "Bravo Electro",
        "domain": "bravo-electro.example",
        "verified": True,
    },
    "charlie-sensors.example": {
        "crustdata_company_id": 102938,
        "name": "Charlie Sensors",
        "domain": "charlie-sensors.example",
        "verified": True,
    },
    "delta-pyro.example": {
        "crustdata_company_id": 654321,
        "name": "Delta Pyro",
        "domain": "delta-pyro.example",
        "verified": True,
    },
    "echo-instruments.example": {
        "crustdata_company_id": 789123,
        "name": "Echo Instruments",
        "domain": "echo-instruments.example",
        "verified": True,
    },
}

# Raw Crustdata POST /company/enrich responses (2 credits per match)
# Contains headcount, locations, and basic_info.description
FIXTURE_COMPANY_ENRICH_MAP: Dict[int, Dict[str, Any]] = {
    918231: {
        "crustdata_company_id": 918231,
        "headcount": {"total": 650, "range": "501-1000"},
        "locations": {"headquarters": "City A, Region A, India", "country": "India"},
        "basic_info": {
            "description": (
                "Leading manufacturer of industrial temperature sensors, thermocouples, "
                "resistance temperature detectors (RTDs), pyrometers, and thermal cables."
            ),
        },
        "year_founded": 1976,
    },
    847291: {
        "crustdata_company_id": 847291,
        "headcount": {"total": 280, "range": "201-500"},
        "locations": {"headquarters": "Mumbai, Maharashtra, India", "country": "India"},
        "basic_info": {
            "description": (
                "Design and manufacture of temperature sensors, transmitters, process indicators, "
                "and signal isolators for industrial manufacturing."
            ),
        },
        "year_founded": 1980,
    },
    102938: {
        "crustdata_company_id": 102938,
        "headcount": {"total": 150, "range": "101-250"},
        "locations": {"headquarters": "Pune, Maharashtra, India", "country": "India"},
        "basic_info": {
            "description": (
                "Manufacturer of precision sensor solutions, industrial temperature transmitters, "
                "and process instrumentation."
            ),
        },
        "year_founded": 1952,
    },
    654321: {
        "crustdata_company_id": 654321,
        "headcount": {"total": 75, "range": "51-100"},
        "locations": {"headquarters": "Bengaluru, Karnataka, India", "country": "India"},
        "basic_info": {
            "description": (
                "Manufacturer and supplier of temperature sensors, RTDs, thermocouples, "
                "and calibration equipment for demanding industrial processes."
            ),
        },
        "year_founded": 1977,
    },
    789123: {
        # Intentionally empty description to trigger HUMAN_OR_SIMULATED status
        "crustdata_company_id": 789123,
        "headcount": {"total": 45, "range": "11-50"},
        "locations": {"headquarters": "Ahmedabad, Gujarat, India", "country": "India"},
        "basic_info": {
            "description": "",
        },
        "year_founded": 2012,
    },
}
