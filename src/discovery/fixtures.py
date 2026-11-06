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
        # One-item demo: Neodymium speaker magnet suppliers in China
        {
            "name": "Shandong Sinter Magnetics",
            "domain": "shandong-sinter-mag.example",
            "year_founded": 2011,
            "industry": "Magnets & Magnetic Materials",
            "location": "Shandong, China",
            "country": "China",
            "relevance_score": 0.98,
        },
        {
            "name": "Ningbo Small Magnetics",
            "domain": "ningbo-small-mag.example",
            "year_founded": 2004,
            "industry": "Magnets & Magnetic Materials",
            "location": "Ningbo, Zhejiang, China",
            "country": "China",
            "relevance_score": 0.94,
        },
        {
            "name": "Beijing Rare Earth Dynamics",
            "domain": "beijing-rare-earth.example",
            "year_founded": 2003,
            "industry": "Magnets & Magnetic Materials",
            "location": "Beijing, China",
            "country": "China",
            "relevance_score": 0.91,
        },
        {
            "name": "Hangzhou Large Magnetics",
            "domain": "hangzhou-large-mag.example",
            "year_founded": 1990,
            "industry": "Magnets & Magnetic Materials",
            "location": "Hangzhou, Zhejiang, China",
            "country": "China",
            "relevance_score": 0.88,
        },
        {
            "name": "Zhejiang NdFeB Precision",
            "domain": "zhejiang-ndfeb-precision.example",
            "year_founded": 2000,
            "industry": "Magnets & Magnetic Materials",
            "location": "Ningbo, Zhejiang, China",
            "country": "China",
            "relevance_score": 0.85,
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
    "shandong-sinter-mag.example": {
        "crustdata_company_id": 501001,
        "name": "Shandong Sinter Magnetics",
        "domain": "shandong-sinter-mag.example",
        "verified": True,
    },
    "ningbo-small-mag.example": {
        "crustdata_company_id": 501002,
        "name": "Ningbo Small Magnetics",
        "domain": "ningbo-small-mag.example",
        "verified": True,
    },
    "beijing-rare-earth.example": {
        "crustdata_company_id": 501003,
        "name": "Beijing Rare Earth Dynamics",
        "domain": "beijing-rare-earth.example",
        "verified": True,
    },
    "hangzhou-large-mag.example": {
        "crustdata_company_id": 501004,
        "name": "Hangzhou Large Magnetics",
        "domain": "hangzhou-large-mag.example",
        "verified": True,
    },
    "zhejiang-ndfeb-precision.example": {
        "crustdata_company_id": 501005,
        "name": "Zhejiang NdFeB Precision",
        "domain": "zhejiang-ndfeb-precision.example",
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
    501001: {
        "crustdata_company_id": 501001,
        "headcount": {"total": 350, "range": "201-500"},
        "locations": {"headquarters": "Shandong, China", "country": "China"},
        "basic_info": {
            "description": "Sintered neodymium (NdFeB) maker, HQ in Shandong, founded 2011, 201-500 staff band; describes custom magnets, fast delivery, ISO TS 16949",
        },
        "year_founded": 2011,
    },
    501002: {
        "crustdata_company_id": 501002,
        "headcount": {"total": 35, "range": "11-50"},
        "locations": {"headquarters": "Ningbo, Zhejiang, China", "country": "China"},
        "basic_info": {
            "description": "Small permanent magnet maker including neodymium, 11-50 staff band, founded 2004, exports to the US among other regions",
        },
        "year_founded": 2004,
    },
    501003: {
        "crustdata_company_id": 501003,
        "headcount": {"total": 600, "range": "501-1000"},
        "locations": {"headquarters": "Beijing, China", "country": "China"},
        "basic_info": {
            "description": "Listed rare earth magnet maker, founded 2003, ISO 9001 and IATF 16949, motor and custom assembly focus",
        },
        "year_founded": 2003,
    },
    501004: {
        "crustdata_company_id": 501004,
        "headcount": {"total": 7500, "range": "5001-10000"},
        "locations": {"headquarters": "Hangzhou, Zhejiang, China", "country": "China"},
        "basic_info": {
            "description": "Large listed magnet maker, founded 1990, 5001-10000 staff band, neodymium patent licence",
        },
        "year_founded": 1990,
    },
    501005: {
        "crustdata_company_id": 501005,
        "headcount": {"total": 280, "range": "201-500"},
        "locations": {"headquarters": "Ningbo, Zhejiang, China", "country": "China"},
        "basic_info": {
            "description": "Sintered NdFeB maker, founded 2000, 201-500 staff band, quality system certifications listed",
        },
        "year_founded": 2000,
    },
}
