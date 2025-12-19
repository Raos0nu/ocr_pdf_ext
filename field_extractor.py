"""
Motor Insurance PDF Field Extraction Module
Simple and reliable field extraction.
AUTHOR: @raos0nu (https://github.com/Raos0nu)
"""

import re
from datetime import datetime
from typing import Dict, Optional


def normalize_date(date_str: str) -> str:
    """
    Normalize date strings to a consistent format (YYYY-MM-DD).
    Handles various date formats commonly found in Indian insurance documents.
    """
    if not date_str or not date_str.strip():
        return ""
    
    date_str = date_str.strip()
    
    # Common date patterns in Indian insurance documents
    patterns = [
        (r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", "%d/%m/%Y"),  # DD/MM/YYYY or DD-MM-YYYY
        (r"(\d{1,2})[/-](\d{1,2})[/-](\d{2})", "%d/%m/%y"),  # DD/MM/YY
        (r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", "%Y/%m/%d"),  # YYYY/MM/DD
        (r"(\d{1,2})\s+(\w+)\s+(\d{4})", "%d %B %Y"),  # DD Month YYYY
        (r"(\d{1,2})\s+(\w+)\s+(\d{2})", "%d %B %y"),  # DD Month YY
    ]
    
    for pattern, fmt in patterns:
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                date_obj = datetime.strptime(match.group(0), fmt)
                return date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
    
    # If no pattern matches, return original (cleaned)
    return date_str


def extract_number(text: str) -> str:
    """
    Extract numeric value from text, removing currency symbols and text.
    """
    if not text:
        return ""
    
    # Remove currency symbols and common text
    text = re.sub(r"[₹Rs\.\s,]", "", str(text), flags=re.IGNORECASE)
    
    # Extract numbers (including decimals)
    match = re.search(r"\d+\.?\d*", text)
    if match:
        return match.group(0)
    
    return ""


def find_field_by_keywords(text: str, keywords: list, multiline: bool = False, 
                          value_pattern: Optional[str] = None) -> str:
    """
    Find a field value by searching for keywords in the text.
    
    Args:
        text: The full text to search
        keywords: List of possible keywords/labels for this field
        multiline: If True, capture multi-line values (like addresses)
        value_pattern: Optional regex pattern to match the value format
    """
    if not text:
        return ""
    
    text_upper = text.upper()
    
    for keyword in keywords:
        keyword_upper = keyword.upper()
        
        # Try different patterns: "Keyword:", "Keyword -", "Keyword=", etc.
        patterns = [
            rf"{re.escape(keyword_upper)}\s*[:=\-]\s*(.+?)(?:\n|$)",
            rf"{re.escape(keyword_upper)}\s+(.+?)(?:\n|$)",
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_upper, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                value = match.group(1).strip()
                
                # If multiline, try to capture more lines
                if multiline:
                    # Look ahead for continuation lines (non-empty, not starting with common keywords)
                    lines = text_upper.split('\n')
                    match_line_idx = text_upper[:match.end()].count('\n')
                    collected = [value]
                    
                    for i in range(match_line_idx + 1, len(lines)):
                        next_line = lines[i].strip()
                        if not next_line:
                            break
                        # Stop if next line looks like a new field
                        if re.match(r'^[A-Z\s]+[:=\-]', next_line):
                            break
                        collected.append(next_line)
                    
                    value = ' '.join(collected).strip()
                
                # Apply value pattern if provided
                if value_pattern:
                    pattern_match = re.search(value_pattern, value, re.IGNORECASE)
                    if pattern_match:
                        value = pattern_match.group(0)
                
                if value:
                    return value.strip()
    
    return ""


def extract_insurance_fields(text: str) -> Dict[str, str]:
    """
    Extract all required fields from insurance PDF text.
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
    
    # Policy Number
    result["POLICY_NO"] = find_field_by_keywords(
        text, 
        ["Policy No", "Policy Number", "Policy No.", "Policy #", "Policy Number:"],
        value_pattern=r"[A-Z0-9/\-]+"
    )
    
    # Insurance Company Name
    result["INSURANCE_COMPANY_NAME"] = find_field_by_keywords(
        text,
        ["Insurance Company", "Company Name", "Insurer", "Insurance Co", "Company:"]
    )
    
    # Customer Name
    result["CUSTOMER_NAME"] = find_field_by_keywords(
        text,
        ["Customer Name", "Insured Name", "Name of Insured", "Policy Holder", 
         "Insured", "Name", "Customer:", "Insured Name:"]
    )
    
    # Customer Email
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    email_match = re.search(email_pattern, text, re.IGNORECASE)
    if email_match:
        result["CUSTOMER_EMAIL"] = email_match.group(0)
    else:
        result["CUSTOMER_EMAIL"] = find_field_by_keywords(
            text,
            ["Email", "E-mail", "Email ID", "Email Address"]
        )
    
    # Mobile Number
    mobile_pattern = r"(\+91[\s\-]?)?[6-9]\d{9}"
    mobile_match = re.search(mobile_pattern, text)
    if mobile_match:
        result["MOB_NO"] = re.sub(r"[\s\-]", "", mobile_match.group(0))
    else:
        result["MOB_NO"] = find_field_by_keywords(
            text,
            ["Mobile", "Phone", "Contact", "Mobile No", "Phone No", "Mob No"],
            value_pattern=r"[\d\s\+\-]+"
        )
    
    # Registration Number
    reg_pattern = r"[A-Z]{2}\s?[0-9]{1,2}\s?[A-Z]{1,2}\s?[0-9]{4}"
    reg_match = re.search(reg_pattern, text, re.IGNORECASE)
    if reg_match:
        result["REGISTRATION_NUMBER"] = reg_match.group(0).strip()
    else:
        result["REGISTRATION_NUMBER"] = find_field_by_keywords(
            text,
            ["Registration No", "Reg No", "Vehicle No", "Registration Number", 
             "Reg. No", "Vehicle Number", "RC No"],
            value_pattern=r"[A-Z0-9\s]+"
        )
    
    # Chassis Number
    result["CHASIS_NUMBER"] = find_field_by_keywords(
        text,
        ["Chassis No", "Chassis Number", "Chassis", "Chassis No.", "CH No"],
        value_pattern=r"[A-Z0-9]+"
    )
    
    # Engine Number
    result["ENGINE_NUMBER"] = find_field_by_keywords(
        text,
        ["Engine No", "Engine Number", "Engine", "Engine No.", "EN No"],
        value_pattern=r"[A-Z0-9]+"
    )
    
    # Vehicle Make
    result["VEHICLE_MAKE"] = find_field_by_keywords(
        text,
        ["Make", "Vehicle Make", "Manufacturer", "Brand", "Make of Vehicle"]
    )
    
    # Vehicle Model
    result["VEHICLE_MODEL"] = find_field_by_keywords(
        text,
        ["Model", "Vehicle Model", "Model Name", "Model of Vehicle"]
    )
    
    # Vehicle Variant
    result["VEHICLE_VARIANT"] = find_field_by_keywords(
        text,
        ["Variant", "Vehicle Variant", "Variant Name"]
    )
    
    # Vehicle Sub Type
    result["VEHICLE_SUB_TYPE"] = find_field_by_keywords(
        text,
        ["Sub Type", "Vehicle Sub Type", "Sub-Type", "Type"]
    )
    
    # Year of Manufacture
    year_match = re.search(r"(?:Year|Manufacturing Year|YOM|YOM:)\s*[:=\-]?\s*(\d{4})", text, re.IGNORECASE)
    if year_match:
        result["YEAR_OF_MANUFACTURE"] = year_match.group(1)
    else:
        # Look for 4-digit years in context
        year_pattern = r"\b(19|20)\d{2}\b"
        years = re.findall(year_pattern, text)
        if years:
            # Use the most recent reasonable year
            valid_years = [y for y in years if 1990 <= int(y) <= 2030]
            if valid_years:
                result["YEAR_OF_MANUFACTURE"] = max(valid_years)
    
    # Registration Date
    reg_date = find_field_by_keywords(
        text,
        ["Registration Date", "Reg Date", "Date of Registration", "Registration"]
    )
    result["REGISTRATION_DATE"] = normalize_date(reg_date)
    
    # Policy Issue Date
    issue_date = find_field_by_keywords(
        text,
        ["Policy Issue Date", "Issue Date", "Date of Issue", "Policy Date", 
         "Issued On", "Policy Issued On"]
    )
    result["POLICY_ISSUE_DATE"] = normalize_date(issue_date)
    
    # Risk Start Date
    risk_start = find_field_by_keywords(
        text,
        ["Risk Start Date", "Coverage Start", "Start Date", "From Date", 
         "Period From", "Coverage From"]
    )
    result["RISK_START_DATE"] = normalize_date(risk_start)
    
    # Risk End Date
    risk_end = find_field_by_keywords(
        text,
        ["Risk End Date", "Coverage End", "End Date", "To Date", 
         "Period To", "Coverage To", "Expiry Date"]
    )
    result["RISK_END_DATE"] = normalize_date(risk_end)
    
    # OD Expire Date
    od_expire = find_field_by_keywords(
        text,
        ["OD Expire", "OD Expiry", "Own Damage Expiry", "OD Expiry Date"]
    )
    result["OD_EXPIRE_DATE"] = normalize_date(od_expire)
    
    # Complete Location Address
    result["COMPLETE_LOCATION_ADDRESS"] = find_field_by_keywords(
        text,
        ["Address", "Complete Address", "Location", "Residential Address", 
         "Permanent Address", "Correspondence Address"],
        multiline=True
    )
    
    # City Name
    result["CITY_NAME"] = find_field_by_keywords(
        text,
        ["City", "City Name", "City:"]
    )
    
    # State Name
    result["STATE_NAME"] = find_field_by_keywords(
        text,
        ["State", "State Name", "State:"]
    )
    
    # Pincode
    pincode_match = re.search(r"(?:Pincode|Pin Code|PIN|Pin)\s*[:=\-]?\s*(\d{6})", text, re.IGNORECASE)
    if pincode_match:
        result["PINCODE"] = pincode_match.group(1)
    else:
        # Look for 6-digit numbers that could be pincodes
        pincode_pattern = r"\b\d{6}\b"
        pincodes = re.findall(pincode_pattern, text)
        if pincodes:
            # Use the first 6-digit number found (could be refined)
            result["PINCODE"] = pincodes[0]
    
    # Fuel Type
    fuel_types = ["Petrol", "Diesel", "CNG", "LPG", "Electric", "Hybrid"]
    for fuel in fuel_types:
        if re.search(rf"\b{fuel}\b", text, re.IGNORECASE):
            result["FUEL_TYPE"] = fuel
            break
    
    if not result["FUEL_TYPE"]:
        result["FUEL_TYPE"] = find_field_by_keywords(
            text,
            ["Fuel Type", "Fuel", "Fuel:"]
        )
    
    # CV Type (Commercial Vehicle Type)
    result["CV_TYPE"] = find_field_by_keywords(
        text,
        ["CV Type", "Vehicle Type", "Type of Vehicle", "Commercial Vehicle Type"]
    )
    
    # Cover
    result["COVER"] = find_field_by_keywords(
        text,
        ["Cover", "Coverage", "Cover Type", "Type of Cover"]
    )
    
    # IDV / Sum Insured
    idv_text = find_field_by_keywords(
        text,
        ["IDV", "Sum Insured", "Insured Value", "IDV Amount", "Sum Assured"]
    )
    result["IDV_SUM_INSURED"] = extract_number(idv_text)
    
    # NCB (No Claim Bonus)
    ncb_text = find_field_by_keywords(
        text,
        ["NCB", "No Claim Bonus", "NCB %", "No Claim Bonus %"]
    )
    result["NCB"] = extract_number(ncb_text)
    
    # Net Premium
    net_prem_text = find_field_by_keywords(
        text,
        ["Net Premium", "Premium", "Net Premium Amount"]
    )
    result["NET_PREMIUM"] = extract_number(net_prem_text)
    
    # OD Premium (Own Damage Premium)
    od_prem_text = find_field_by_keywords(
        text,
        ["OD Premium", "Own Damage Premium", "OD Premium Amount"]
    )
    result["OD_PREMIUM"] = extract_number(od_prem_text)
    
    # TP Only Premium (Third Party Premium)
    tp_prem_text = find_field_by_keywords(
        text,
        ["TP Premium", "Third Party Premium", "TP Only Premium", "TP Premium Amount"]
    )
    result["TP_ONLY_PREMIUM"] = extract_number(tp_prem_text)
    
    # Total Premium
    total_prem_text = find_field_by_keywords(
        text,
        ["Total Premium", "Premium Total", "Total Amount", "Grand Total"]
    )
    result["TOTAL_PREMIUM"] = extract_number(total_prem_text)
    
    # GST
    gst_text = find_field_by_keywords(
        text,
        ["GST", "GST Amount", "Goods and Services Tax"]
    )
    result["GST"] = extract_number(gst_text)
    
    # CGST
    cgst_text = find_field_by_keywords(
        text,
        ["CGST", "CGST Amount", "Central GST"]
    )
    result["CGST"] = extract_number(cgst_text)
    
    # SGST
    sgst_text = find_field_by_keywords(
        text,
        ["SGST", "SGST Amount", "State GST"]
    )
    result["SGST"] = extract_number(sgst_text)
    
    # IGST
    igst_text = find_field_by_keywords(
        text,
        ["IGST", "IGST Amount", "Integrated GST"]
    )
    result["IGST"] = extract_number(igst_text)
    
    # CC (Cubic Capacity)
    cc_text = find_field_by_keywords(
        text,
        ["CC", "Cubic Capacity", "Engine CC", "CC:"]
    )
    result["CC"] = extract_number(cc_text)
    
    # GVW (Gross Vehicle Weight)
    gvw_text = find_field_by_keywords(
        text,
        ["GVW", "Gross Vehicle Weight", "GVW:", "Vehicle Weight"]
    )
    result["GVW"] = extract_number(gvw_text)
    
    # Product Code
    result["PRODUCT_CODE"] = find_field_by_keywords(
        text,
        ["Product Code", "Product", "Product ID", "Code"]
    )
    
    # Broker Name
    result["BROKER_NAME"] = find_field_by_keywords(
        text,
        ["Broker", "Broker Name", "Agent", "Agent Name", "Intermediary"]
    )
    
    # Financier Name
    result["FINANCIER_NAME"] = find_field_by_keywords(
        text,
        ["Financier", "Financier Name", "Finance Company", "Loan Provider"]
    )
    
    # Nominee Name
    result["NOMINEE_NAME"] = find_field_by_keywords(
        text,
        ["Nominee", "Nominee Name", "Nominee:", "Name of Nominee"],
        multiline=True
    )
    
    # Nominee Relationship
    result["NOMINEE_RELATIONSHIP"] = find_field_by_keywords(
        text,
        ["Nominee Relationship", "Relationship", "Relation", "Relationship with Nominee"]
    )
    
    return result
