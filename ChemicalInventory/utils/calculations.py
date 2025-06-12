"""
Utility functions for chemical inventory calculations
"""

def calculate_closing_balance(opening_balance, receive_qty, consumption_qty):
    """
    Calculate closing balance based on the formula:
    Closing Balance = Opening Balance + Receive Qty - Consumption Qty
    
    Args:
        opening_balance (float): Opening balance quantity
        receive_qty (float): Quantity received
        consumption_qty (float): Quantity consumed
        
    Returns:
        float: Calculated closing balance
    """
    try:
        opening = float(opening_balance) if opening_balance else 0.0
        received = float(receive_qty) if receive_qty else 0.0
        consumed = float(consumption_qty) if consumption_qty else 0.0
        
        closing = opening + received - consumed
        return round(closing, 2)
    
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid numeric values for balance calculation: {e}")

def validate_consumption_data(data):
    """
    Validate consumption data before processing
    
    Args:
        data (dict): Consumption data dictionary
        
    Returns:
        tuple: (is_valid, error_message)
    """
    required_fields = ['dc_date', 'unit_code', 'chemical_code', 'opening_balance']
    
    # Check required fields
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Missing required field: {field}"
    
    # Validate numeric fields
    numeric_fields = ['opening_balance', 'receive_qty', 'consumption_qty', 'sap_balance']
    for field in numeric_fields:
        if field in data and data[field] is not None:
            try:
                float(data[field])
            except (ValueError, TypeError):
                return False, f"Invalid numeric value for {field}"
    
    # Validate quantities are not negative
    non_negative_fields = ['opening_balance', 'receive_qty', 'consumption_qty']
    for field in non_negative_fields:
        if field in data and data[field] is not None:
            try:
                value = float(data[field])
                if value < 0:
                    return False, f"{field} cannot be negative"
            except (ValueError, TypeError):
                pass  # Already handled above
    
    return True, None

def calculate_stock_variance(sap_balance, calculated_balance):
    """
    Calculate variance between SAP balance and calculated balance
    
    Args:
        sap_balance (float): Balance as per SAP system
        calculated_balance (float): Calculated closing balance
        
    Returns:
        dict: Variance information including absolute difference and percentage
    """
    try:
        sap = float(sap_balance) if sap_balance else 0.0
        calculated = float(calculated_balance) if calculated_balance else 0.0
        
        absolute_variance = calculated - sap
        percentage_variance = (absolute_variance / sap * 100) if sap != 0 else 0.0
        
        return {
            'absolute_variance': round(absolute_variance, 2),
            'percentage_variance': round(percentage_variance, 2),
            'has_variance': abs(absolute_variance) > 0.01,  # Consider variance if > 0.01
            'variance_type': 'surplus' if absolute_variance > 0 else 'shortage' if absolute_variance < 0 else 'matched'
        }
    
    except (ValueError, TypeError) as e:
        return {
            'absolute_variance': 0.0,
            'percentage_variance': 0.0,
            'has_variance': False,
            'variance_type': 'error',
            'error': str(e)
        }

def get_consumption_trends(consumption_records, days=30):
    """
    Analyze consumption trends for a chemical over specified days
    
    Args:
        consumption_records (list): List of consumption records
        days (int): Number of days to analyze
        
    Returns:
        dict: Trend analysis data
    """
    if not consumption_records:
        return {
            'average_consumption': 0.0,
            'max_consumption': 0.0,
            'min_consumption': 0.0,
            'trend': 'stable',
            'records_count': 0
        }
    
    try:
        consumptions = [float(record.consumption_qty) for record in consumption_records if record.consumption_qty]
        
        if not consumptions:
            return {
                'average_consumption': 0.0,
                'max_consumption': 0.0,
                'min_consumption': 0.0,
                'trend': 'no_data',
                'records_count': 0
            }
        
        avg_consumption = sum(consumptions) / len(consumptions)
        max_consumption = max(consumptions)
        min_consumption = min(consumptions)
        
        # Simple trend calculation (last vs first half comparison)
        if len(consumptions) >= 4:
            mid_point = len(consumptions) // 2
            first_half_avg = sum(consumptions[:mid_point]) / mid_point
            second_half_avg = sum(consumptions[mid_point:]) / (len(consumptions) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                trend = 'increasing'
            elif second_half_avg < first_half_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
        else:
            trend = 'insufficient_data'
        
        return {
            'average_consumption': round(avg_consumption, 2),
            'max_consumption': round(max_consumption, 2),
            'min_consumption': round(min_consumption, 2),
            'trend': trend,
            'records_count': len(consumptions)
        }
    
    except Exception as e:
        return {
            'average_consumption': 0.0,
            'max_consumption': 0.0,
            'min_consumption': 0.0,
            'trend': 'error',
            'records_count': 0,
            'error': str(e)
        }
