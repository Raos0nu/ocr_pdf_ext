"""
Motor Insurance PDF Field Extraction Module
Enhanced version with improved accuracy and OCR error handling.
AUTHOR: @raos0nu (https://github.com/Raos0nu)
"""

import re
from datetime import datetime
from typing import Dict, Optional, List, Tuple


def normalize_text_for_ocr(text: str) -> str:
    """
    Normalize text to handle common OCR errors and improve matching.
    """
    if not text:
        return ""
    
    # Common OCR mistakes: 0->O, 1->I, 5->S, 8->B, etc.
    # We'll keep original but also create variations
    text = text.strip()
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Handle common OCR artifacts
    text = text.replace('|', 'I').replace('l', 'I')  # Common OCR mistakes
    text = text.replace('O', '0')  # In numeric contexts
    
    return text


def normalize_date(date_str: str) -> str:
    """
    Normalize date strings to a consistent format (YYYY-MM-DD).
    Handles various date formats commonly found in Indian insurance documents.
    """
    if not date_str or not date_str.strip():
        return ""
    
    date_str = date_str.strip()
    
    # Remove common prefixes/suffixes
    date_str = re.sub(r'^(Date|Dated?|On|As of|As on)\s*[:=\-]?\s*', '', date_str, flags=re.IGNORECASE)
    
    # Common date patterns in Indian insurance documents
    patterns = [
        # DD/MM/YYYY formats
        (r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})", lambda m: f"{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}"),
        # DD/MM/YY formats
        (r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2})\b", lambda m: (f"20{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}" if (m.group(3) and m.group(3).strip() and int(m.group(3)) < 50) else f"19{m.group(3)}-{m.group(2).zfill(2)}-{m.group(1).zfill(2)}") if (m.group(3) and m.group(3).strip()) else ""),
        # YYYY/MM/DD formats
        (r"(\d{4})[/\-\.](\d{1,2})[/\-\.](\d{1,2})", lambda m: f"{m.group(1)}-{m.group(2).zfill(2)}-{m.group(3).zfill(2)}"),
        # DD Month YYYY
        (r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})", 
         lambda m: datetime.strptime(f"{m.group(1)} {m.group(2)[:3]} {m.group(3)}", "%d %b %Y").strftime("%Y-%m-%d")),
        # DD Month YY
        (r"(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{2})\b",
         lambda m: datetime.strptime(f"{m.group(1)} {m.group(2)[:3]} {('20' if (m.group(3) and m.group(3).strip() and int(m.group(3)) < 50) else '19') + m.group(3)}", "%d %b %Y").strftime("%Y-%m-%d") if (m.group(3) and m.group(3).strip()) else ""),
    ]
    
    for pattern, formatter in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                return formatter(match)
            except (ValueError, IndexError):
                continue
    
    # Try to extract any date-like pattern
    date_match = re.search(r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}', date_str)
    if date_match:
        return date_match.group(0)
    
    return date_str


def extract_number(text: str, allow_decimal: bool = True) -> str:
    """
    Extract numeric value from text, removing currency symbols and text.
    Handles Indian number format with commas.
    """
    if not text:
        return ""
    
    # Remove currency symbols and common text
    text = re.sub(r'[₹Rs\$€£\.\s]', '', str(text), flags=re.IGNORECASE)
    
    # Remove common words
    text = re.sub(r'\b(rupees?|only|lakhs?|crores?|thousands?)\b', '', text, flags=re.IGNORECASE)
    
    # Extract numbers (handling commas in Indian format)
    if allow_decimal:
        # Match numbers with optional commas and decimals
        pattern = r'[\d,]+\.?\d*'
    else:
        # Match only integers
        pattern = r'[\d,]+'
    
    matches = re.findall(pattern, text)
    if matches:
        # Take the largest number (usually the main value)
        numbers = [m.replace(',', '') for m in matches]
        # Filter out empty strings and invalid numbers
        numbers = [n for n in numbers if n and n.strip()]
        # Return the one that looks most like a currency amount
        def sort_key(x):
            try:
                return float(x) if '.' in x else int(x)
            except (ValueError, TypeError):
                return 0
        
        for num in sorted(numbers, key=sort_key, reverse=True):
            try:
                if float(num) > 0:
                    return num
            except (ValueError, TypeError):
                continue
    
    return ""


def find_field_by_keywords(text: str, keywords: List[str], multiline: bool = False, 
                          value_pattern: Optional[str] = None, max_lines: int = 5,
                          context_before: int = 0, context_after: int = 0) -> str:
    """
    Enhanced field finder with better keyword matching and context awareness.
    """
    if not text:
        return ""
    
    # Normalize text for better matching
    text_normalized = normalize_text_for_ocr(text)
    text_upper = text.upper()
    text_lines = text.split('\n')
    
    # Expand keywords with common variations
    expanded_keywords = []
    for keyword in keywords:
        expanded_keywords.append(keyword)
        # Add variations
        expanded_keywords.append(keyword.replace(' ', ''))
        expanded_keywords.append(keyword.replace(' ', '-'))
        expanded_keywords.append(keyword.replace(' ', '_'))
        # Add common OCR mistakes
        expanded_keywords.append(keyword.replace('0', 'O').replace('1', 'I'))
    
    best_match = None
    best_score = 0
    
    for keyword in expanded_keywords:
        keyword_upper = keyword.upper()
        
        # Multiple patterns to try
        patterns = [
            # Pattern 1: "Keyword:" or "Keyword -" or "Keyword="
            rf"{re.escape(keyword_upper)}\s*[:=\-]\s*(.+?)(?:\n|$)",
            # Pattern 2: "Keyword " (space)
            rf"{re.escape(keyword_upper)}\s+(.+?)(?:\n|$)",
            # Pattern 3: "Keyword" at start of line
            rf"^{re.escape(keyword_upper)}\s*[:=\-]?\s*(.+?)(?:\n|$)",
            # Pattern 4: Flexible spacing
            rf"{re.escape(keyword_upper.replace(' ', r'\s+'))}\s*[:=\-]?\s*(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_upper, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                value = match.group(1).strip()
                
                # Skip if value is too short or looks like another keyword
                if len(value) < 2 or re.match(r'^[A-Z\s]+[:=\-]', value):
                    continue
                
                # If multiline, collect continuation lines
                if multiline:
                    match_line_idx = text_upper[:match.end()].count('\n')
                    collected = [value]
                    
                    for i in range(match_line_idx + 1, min(match_line_idx + 1 + max_lines, len(text_lines))):
                        next_line = text_lines[i].strip()
                        if not next_line:
                            break
                        # Stop if next line looks like a new field
                        if re.match(r'^[A-Z\s]{3,}[:=\-]', next_line, re.IGNORECASE):
                            break
                        # Stop if we hit common section headers
                        if re.match(r'^(Policy|Vehicle|Premium|Customer|Address|Nominee)', next_line, re.IGNORECASE):
                            if i > match_line_idx + 2:  # Allow 1-2 lines after keyword
                                break
                        collected.append(next_line)
                    
                    value = ' '.join(collected).strip()
                
                # Apply value pattern if provided
                if value_pattern:
                    pattern_match = re.search(value_pattern, value, re.IGNORECASE)
                    if pattern_match:
                        value = pattern_match.group(0)
                
                # Score this match (longer, more complete values score higher)
                score = len(value) + (10 if multiline and len(collected) > 1 else 0)
                
                if value and score > best_score:
                    best_match = value
                    best_score = score
    
    return best_match if best_match else ""


def extract_insurance_fields(text: str) -> Dict[str, str]:
    """
    Extract all required fields from insurance PDF text with enhanced accuracy.
    Returns a dictionary with all schema keys, using empty strings for missing values.
    """
    result = {
        "BROKER_NAME": "",
        "CC": "",
        "CGST": "",
        "CHASIS_NUMBER": "",
        "CITY_NAME": "",
        "COVER": "",
        "CUSTOMER_EMAIL": "",
        "CUSTOMER_NAME": "",
        "CV_TYPE": "",
        "ENGINE_NUMBER": "",
        "FINANCIER_NAME": "",
        "FUEL_TYPE": "",
        "GST": "",
        "GVW": "",
        "IDV_SUM_INSURED": "",
        "IGST": "",
        "INSURANCE_COMPANY_NAME": "",
        "COMPLETE_LOCATION_ADDRESS": "",
        "MOB_NO": "",
        "NCB": "",
        "NET_PREMIUM": "",
        "NOMINEE_NAME": "",
        "NOMINEE_RELATIONSHIP": "",
        "OD_EXPIRE_DATE": "",
        "OD_PREMIUM": "",
        "PINCODE": "",
        "POLICY_ISSUE_DATE": "",
        "POLICY_NO": "",
        "PRODUCT_CODE": "",
        "REGISTRATION_DATE": "",
        "REGISTRATION_NUMBER": "",
        "RISK_END_DATE": "",
        "RISK_START_DATE": "",
        "SGST": "",
        "STATE_NAME": "",
        "TOTAL_PREMIUM": "",
        "TP_ONLY_PREMIUM": "",
        "VEHICLE_MAKE": "",
        "VEHICLE_MODEL": "",
        "VEHICLE_SUB_TYPE": "",
        "VEHICLE_VARIANT": "",
        "YEAR_OF_MANUFACTURE": "",
    }
    
    # Policy Number - Enhanced with more patterns
    policy_patterns = [
        r"(?:Policy\s*(?:No|Number|#|No\.?))\s*[:=\-]?\s*([A-Z0-9/\-]{4,})",
        r"Policy\s+([A-Z]{2,}\d{4,})",
        r"POL\s*[:=\-]?\s*([A-Z0-9/\-]+)",
    ]
    for pattern in policy_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["POLICY_NO"] = match.group(1).strip()
            break
    if not result["POLICY_NO"]:
        result["POLICY_NO"] = find_field_by_keywords(
            text, 
            ["Policy No", "Policy Number", "Policy No.", "Policy #", "Policy Number:", "POL No", "POL Number"],
            value_pattern=r"[A-Z0-9/\-]{4,}"
        )
    
    # Insurance Company Name - Look for common insurance company names
    insurance_companies = [
        "LIC", "HDFC", "ICICI", "Bajaj", "Reliance", "Tata", "New India", 
        "United India", "Oriental", "National", "Future Generali", "Royal Sundaram",
        "Bharti AXA", "IFFCO Tokio", "SBI General", "Kotak", "Go Digit", "Acko"
    ]
    for company in insurance_companies:
        if re.search(rf"\b{re.escape(company)}\b", text, re.IGNORECASE):
            result["INSURANCE_COMPANY_NAME"] = company
            break
    
    if not result["INSURANCE_COMPANY_NAME"]:
        result["INSURANCE_COMPANY_NAME"] = find_field_by_keywords(
            text,
            ["Insurance Company", "Company Name", "Insurer", "Insurance Co", "Company:", 
             "Underwritten by", "Issued by", "Insurance Provider"]
        )
    
    # Customer Name - Enhanced
    result["CUSTOMER_NAME"] = find_field_by_keywords(
        text,
        ["Customer Name", "Insured Name", "Name of Insured", "Policy Holder", 
         "Insured", "Name", "Customer:", "Insured Name:", "Insured Person",
         "Proposer Name", "Proposer", "Name of Proposer"]
    )
    
    # Customer Email - Enhanced pattern
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    email_matches = re.findall(email_pattern, text, re.IGNORECASE)
    if email_matches:
        result["CUSTOMER_EMAIL"] = email_matches[0]  # Take first email found
    else:
        result["CUSTOMER_EMAIL"] = find_field_by_keywords(
            text,
            ["Email", "E-mail", "Email ID", "Email Address", "E-Mail"]
        )
    
    # Mobile Number - Enhanced patterns
    mobile_patterns = [
        r"(\+91[\s\-]?)?[6-9]\d{9}",  # Standard Indian mobile
        r"(\+91[\s\-]?)?[6-9][\d\s\-]{9,12}",  # With spaces/dashes
        r"Mobile[:\s]+(\d{10})",
        r"Phone[:\s]+(\d{10})",
        r"Mob[:\s]+(\d{10})",
    ]
    for pattern in mobile_patterns:
        match = re.search(pattern, text)
        if match:
            mobile = re.sub(r"[\s\-]", "", match.group(0))
            if len(mobile) >= 10:
                result["MOB_NO"] = mobile[-10:]  # Take last 10 digits
                break
    
    if not result["MOB_NO"]:
        result["MOB_NO"] = find_field_by_keywords(
            text,
            ["Mobile", "Phone", "Contact", "Mobile No", "Phone No", "Mob No", "Mobile Number"],
            value_pattern=r"[\d\s\+\-]{10,}"
        )
        # Clean up the mobile number
        if result["MOB_NO"]:
            result["MOB_NO"] = re.sub(r"[\s\-]", "", result["MOB_NO"])
            # Extract only digits, take last 10
            digits = re.findall(r'\d', result["MOB_NO"])
            if len(digits) >= 10:
                result["MOB_NO"] = ''.join(digits[-10:])
    
    # Registration Number - Enhanced patterns
    reg_patterns = [
        r"[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,2}\s?[0-9]{4}",  # Standard format
        r"[A-Z]{2}[\s\-]?[0-9]{1,2}[\s\-]?[A-Z]{1,2}[\s\-]?[0-9]{4}",  # With dashes
        r"Reg[:\s]+([A-Z]{2}[\s\-]?[0-9]{1,2}[\s\-]?[A-Z]{1,2}[\s\-]?[0-9]{4})",
    ]
    for pattern in reg_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["REGISTRATION_NUMBER"] = re.sub(r'[\s\-]', '', match.group(0)).upper()
            break
    
    if not result["REGISTRATION_NUMBER"]:
        reg_text = find_field_by_keywords(
            text,
            ["Registration No", "Reg No", "Vehicle No", "Registration Number", 
             "Reg. No", "Vehicle Number", "RC No", "RC Number", "Regn No"],
            value_pattern=r"[A-Z0-9\s]{6,}"
        )
        if reg_text:
            # Clean and format
            reg_clean = re.sub(r'[\s\-]', '', reg_text.upper())
            if len(reg_clean) >= 8:
                result["REGISTRATION_NUMBER"] = reg_clean
    
    # Chassis Number - Enhanced
    chassis_patterns = [
        r"Chassis[:\s]+([A-Z0-9]{10,})",
        r"CH[:\s]+([A-Z0-9]{10,})",
        r"Chassis\s+No[:\s]+([A-Z0-9]{10,})",
    ]
    for pattern in chassis_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["CHASIS_NUMBER"] = match.group(1).strip().upper()
            break
    
    if not result["CHASIS_NUMBER"]:
        result["CHASIS_NUMBER"] = find_field_by_keywords(
            text,
            ["Chassis No", "Chassis Number", "Chassis", "Chassis No.", "CH No", "CH Number"],
            value_pattern=r"[A-Z0-9]{10,}"
        )
        if result["CHASIS_NUMBER"]:
            result["CHASIS_NUMBER"] = result["CHASIS_NUMBER"].upper()
    
    # Engine Number - Enhanced
    engine_patterns = [
        r"Engine[:\s]+([A-Z0-9]{6,})",
        r"EN[:\s]+([A-Z0-9]{6,})",
        r"Engine\s+No[:\s]+([A-Z0-9]{6,})",
    ]
    for pattern in engine_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["ENGINE_NUMBER"] = match.group(1).strip().upper()
            break
    
    if not result["ENGINE_NUMBER"]:
        result["ENGINE_NUMBER"] = find_field_by_keywords(
            text,
            ["Engine No", "Engine Number", "Engine", "Engine No.", "EN No", "EN Number"],
            value_pattern=r"[A-Z0-9]{6,}"
        )
        if result["ENGINE_NUMBER"]:
            result["ENGINE_NUMBER"] = result["ENGINE_NUMBER"].upper()
    
    # Vehicle Make - Enhanced with common makes
    vehicle_makes = [
        "Maruti", "Hyundai", "Honda", "Toyota", "Tata", "Mahindra", "Ford",
        "Volkswagen", "Nissan", "Renault", "Skoda", "MG", "Kia", "Jeep",
        "BMW", "Mercedes", "Audi", "Jaguar", "Land Rover", "Volvo"
    ]
    for make in vehicle_makes:
        if re.search(rf"\b{re.escape(make)}\b", text, re.IGNORECASE):
            result["VEHICLE_MAKE"] = make
            break
    
    if not result["VEHICLE_MAKE"]:
        result["VEHICLE_MAKE"] = find_field_by_keywords(
            text,
            ["Make", "Vehicle Make", "Manufacturer", "Brand", "Make of Vehicle", "Car Make"]
        )
    
    # Vehicle Model
    result["VEHICLE_MODEL"] = find_field_by_keywords(
        text,
        ["Model", "Vehicle Model", "Model Name", "Model of Vehicle", "Car Model"]
    )
    
    # Vehicle Variant
    result["VEHICLE_VARIANT"] = find_field_by_keywords(
        text,
        ["Variant", "Vehicle Variant", "Variant Name", "Car Variant"]
    )
    
    # Vehicle Sub Type
    result["VEHICLE_SUB_TYPE"] = find_field_by_keywords(
        text,
        ["Sub Type", "Vehicle Sub Type", "Sub-Type", "Type", "Vehicle Type", "Body Type"]
    )
    
    # Year of Manufacture - Enhanced
    year_patterns = [
        r"(?:Year|Manufacturing Year|YOM|YOM:|Mfg Year|Manufacture Year)\s*[:=\-]?\s*(\d{4})",
        r"(\d{4})\s*(?:Year|YOM)",
    ]
    for pattern in year_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            year = match.group(1)
            if year and year.strip():
                try:
                    if 1990 <= int(year) <= 2030:
                        result["YEAR_OF_MANUFACTURE"] = year
                        break
                except (ValueError, TypeError):
                    continue
    
    if not result["YEAR_OF_MANUFACTURE"]:
        # Look for 4-digit years in reasonable range
        year_matches = re.findall(r'\b(19[9]\d|20[0-2]\d)\b', text)
        if year_matches:
            # Prefer years near current date, but take any reasonable year
            valid_years = []
            for y in year_matches:
                if y and y.strip():
                    try:
                        if 1990 <= int(y) <= 2030:
                            valid_years.append(y)
                    except (ValueError, TypeError):
                        continue
            if valid_years:
                result["YEAR_OF_MANUFACTURE"] = max(valid_years)
    
    # Registration Date
    reg_date = find_field_by_keywords(
        text,
        ["Registration Date", "Reg Date", "Date of Registration", "Registration", "Regn Date"]
    )
    result["REGISTRATION_DATE"] = normalize_date(reg_date)
    
    # Policy Issue Date
    issue_date = find_field_by_keywords(
        text,
        ["Policy Issue Date", "Issue Date", "Date of Issue", "Policy Date", 
         "Issued On", "Policy Issued On", "Date of Policy", "Policy Issued Date"]
    )
    result["POLICY_ISSUE_DATE"] = normalize_date(issue_date)
    
    # Risk Start Date
    risk_start = find_field_by_keywords(
        text,
        ["Risk Start Date", "Coverage Start", "Start Date", "From Date", 
         "Period From", "Coverage From", "Policy Start", "Coverage Start Date"]
    )
    result["RISK_START_DATE"] = normalize_date(risk_start)
    
    # Risk End Date
    risk_end = find_field_by_keywords(
        text,
        ["Risk End Date", "Coverage End", "End Date", "To Date", 
         "Period To", "Coverage To", "Expiry Date", "Policy End", "Coverage End Date"]
    )
    result["RISK_END_DATE"] = normalize_date(risk_end)
    
    # OD Expire Date
    od_expire = find_field_by_keywords(
        text,
        ["OD Expire", "OD Expiry", "Own Damage Expiry", "OD Expiry Date", "OD Expire Date"]
    )
    result["OD_EXPIRE_DATE"] = normalize_date(od_expire)
    
    # Complete Location Address - Enhanced multiline
    result["COMPLETE_LOCATION_ADDRESS"] = find_field_by_keywords(
        text,
        ["Address", "Complete Address", "Location", "Residential Address", 
         "Permanent Address", "Correspondence Address", "Registered Address", "Full Address"],
        multiline=True,
        max_lines=8
    )
    
    # City Name - Enhanced
    result["CITY_NAME"] = find_field_by_keywords(
        text,
        ["City", "City Name", "City:", "City of Registration"]
    )
    
    # State Name - Enhanced
    result["STATE_NAME"] = find_field_by_keywords(
        text,
        ["State", "State Name", "State:", "State of Registration"]
    )
    
    # Pincode - Enhanced
    pincode_patterns = [
        r"(?:Pincode|Pin Code|PIN|Pin|Pincode:)\s*[:=\-]?\s*(\d{6})",
        r"PIN[:\s]+(\d{6})",
        r"(\d{6})\s*(?:Pincode|PIN)",
    ]
    for pattern in pincode_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result["PINCODE"] = match.group(1)
            break
    
    if not result["PINCODE"]:
        # Look for 6-digit numbers near address/city keywords
        address_context = find_field_by_keywords(text, ["Address", "City", "Location"], multiline=True, max_lines=5)
        if address_context:
            pincodes = re.findall(r'\b\d{6}\b', address_context)
            if pincodes:
                result["PINCODE"] = pincodes[0]
    
    # Fuel Type - Enhanced
    fuel_types = ["Petrol", "Diesel", "CNG", "LPG", "Electric", "Hybrid", "Petrol+CNG", "Diesel+CNG"]
    for fuel in fuel_types:
        if re.search(rf"\b{re.escape(fuel)}\b", text, re.IGNORECASE):
            result["FUEL_TYPE"] = fuel
            break
    
    if not result["FUEL_TYPE"]:
        result["FUEL_TYPE"] = find_field_by_keywords(
            text,
            ["Fuel Type", "Fuel", "Fuel:", "Type of Fuel"]
        )
    
    # CV Type (Commercial Vehicle Type)
    result["CV_TYPE"] = find_field_by_keywords(
        text,
        ["CV Type", "Vehicle Type", "Type of Vehicle", "Commercial Vehicle Type", "Vehicle Category"]
    )
    
    # Cover
    result["COVER"] = find_field_by_keywords(
        text,
        ["Cover", "Coverage", "Cover Type", "Type of Cover", "Policy Cover"]
    )
    
    # IDV / Sum Insured - Enhanced
    idv_text = find_field_by_keywords(
        text,
        ["IDV", "Sum Insured", "Insured Value", "IDV Amount", "Sum Assured", "Insured Sum"]
    )
    result["IDV_SUM_INSURED"] = extract_number(idv_text)
    
    # NCB (No Claim Bonus) - Enhanced
    ncb_text = find_field_by_keywords(
        text,
        ["NCB", "No Claim Bonus", "NCB %", "No Claim Bonus %", "NCB Percentage"]
    )
    result["NCB"] = extract_number(ncb_text, allow_decimal=True)
    
    # Net Premium - Enhanced
    net_prem_text = find_field_by_keywords(
        text,
        ["Net Premium", "Premium", "Net Premium Amount", "Base Premium"]
    )
    result["NET_PREMIUM"] = extract_number(net_prem_text)
    
    # OD Premium (Own Damage Premium) - Enhanced
    od_prem_text = find_field_by_keywords(
        text,
        ["OD Premium", "Own Damage Premium", "OD Premium Amount", "OD Premium:", "Own Damage"]
    )
    result["OD_PREMIUM"] = extract_number(od_prem_text)
    
    # TP Only Premium (Third Party Premium) - Enhanced
    tp_prem_text = find_field_by_keywords(
        text,
        ["TP Premium", "Third Party Premium", "TP Only Premium", "TP Premium Amount", 
         "TP Premium:", "Third Party", "TP"]
    )
    result["TP_ONLY_PREMIUM"] = extract_number(tp_prem_text)
    
    # Total Premium - Enhanced
    total_prem_text = find_field_by_keywords(
        text,
        ["Total Premium", "Premium Total", "Total Amount", "Grand Total", "Total", "Final Premium"]
    )
    result["TOTAL_PREMIUM"] = extract_number(total_prem_text)
    
    # GST - Enhanced
    gst_text = find_field_by_keywords(
        text,
        ["GST", "GST Amount", "Goods and Services Tax", "GST:", "Total GST"]
    )
    result["GST"] = extract_number(gst_text)
    
    # CGST - Enhanced
    cgst_text = find_field_by_keywords(
        text,
        ["CGST", "CGST Amount", "Central GST", "CGST:"]
    )
    result["CGST"] = extract_number(cgst_text)
    
    # SGST - Enhanced
    sgst_text = find_field_by_keywords(
        text,
        ["SGST", "SGST Amount", "State GST", "SGST:"]
    )
    result["SGST"] = extract_number(sgst_text)
    
    # IGST - Enhanced
    igst_text = find_field_by_keywords(
        text,
        ["IGST", "IGST Amount", "Integrated GST", "IGST:"]
    )
    result["IGST"] = extract_number(igst_text)
    
    # CC (Cubic Capacity) - Enhanced
    cc_text = find_field_by_keywords(
        text,
        ["CC", "Cubic Capacity", "Engine CC", "CC:", "Cubic Capacity (CC)"]
    )
    result["CC"] = extract_number(cc_text, allow_decimal=False)
    
    # GVW (Gross Vehicle Weight) - Enhanced
    gvw_text = find_field_by_keywords(
        text,
        ["GVW", "Gross Vehicle Weight", "GVW:", "Vehicle Weight", "Gross Weight"]
    )
    result["GVW"] = extract_number(gvw_text)
    
    # Product Code
    result["PRODUCT_CODE"] = find_field_by_keywords(
        text,
        ["Product Code", "Product", "Product ID", "Code", "Product Code:"]
    )
    
    # Broker Name - Enhanced
    result["BROKER_NAME"] = find_field_by_keywords(
        text,
        ["Broker", "Broker Name", "Agent", "Agent Name", "Intermediary", "Broker Code"]
    )
    
    # Financier Name - Enhanced
    result["FINANCIER_NAME"] = find_field_by_keywords(
        text,
        ["Financier", "Financier Name", "Finance Company", "Loan Provider", "Financing Company"]
    )
    
    # Nominee Name - Enhanced multiline
    result["NOMINEE_NAME"] = find_field_by_keywords(
        text,
        ["Nominee", "Nominee Name", "Nominee:", "Name of Nominee"],
        multiline=True,
        max_lines=3
    )
    
    # Nominee Relationship - Enhanced
    relationships = ["Father", "Mother", "Son", "Daughter", "Spouse", "Wife", "Husband", "Brother", "Sister"]
    for rel in relationships:
        if re.search(rf"Nominee.*{re.escape(rel)}|{re.escape(rel)}.*Nominee", text, re.IGNORECASE):
            result["NOMINEE_RELATIONSHIP"] = rel
            break
    
    if not result["NOMINEE_RELATIONSHIP"]:
        result["NOMINEE_RELATIONSHIP"] = find_field_by_keywords(
            text,
            ["Nominee Relationship", "Relationship", "Relation", "Relationship with Nominee", "Relation with Nominee"]
        )
    
    return result
