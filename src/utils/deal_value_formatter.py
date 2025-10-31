"""
Deal Value Formatter Utility
Provides consistent formatting of deal_value with source annotations across all reports
"""
from typing import Dict, Any, Tuple


def format_deal_value_with_annotation(state: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
    """
    Format deal_value with source annotation for reports
    
    Args:
        state: Analysis state containing deal_value and deal_value_metadata
        
    Returns:
        Tuple of (formatted_value, annotation, metadata_dict)
        
    Examples:
        User-provided:
        - formatted_value: "$50,000,000,000"
        - annotation: "Deal value specified by user: $50,000,000,000 (DCF base case: $45,000,000,000, variance: +11.1%)"
        
        Auto-calculated:
        - formatted_value: "$45,000,000,000"
        - annotation: "Deal value auto-calculated from DCF analysis. Base case: $45,000,000,000. Range: $36,000,000,000 - $54,000,000,000"
    """
    deal_value = state.get('deal_value', 0)
    metadata = state.get('deal_value_metadata', {})
    
    # Format the value
    if deal_value and deal_value > 0:
        formatted_value = f"${deal_value:,.0f}"
    else:
        formatted_value = "Not Specified"
    
    # Get annotation from metadata
    annotation = metadata.get('report_annotation', '')
    
    # If no metadata, provide default annotation
    if not annotation:
        if deal_value and deal_value > 0:
            annotation = f"Deal value: ${deal_value:,.0f} (Source not documented)"
        else:
            annotation = "Deal value not provided"
    
    return formatted_value, annotation, metadata


def get_deal_value_comment_for_excel(state: Dict[str, Any]) -> str:
    """
    Get Excel cell comment for deal_value
    
    Returns:
        Multi-line comment string suitable for Excel cell comments
    """
    metadata = state.get('deal_value_metadata', {})
    
    if not metadata:
        return "Deal Value\n\nSource: Not documented"
    
    source = metadata.get('source', 'unknown')
    user_provided = metadata.get('user_provided', False)
    
    if user_provided:
        comment_lines = [
            "Deal Value - USER PROVIDED",
            "",
            f"Value: ${state.get('deal_value', 0):,.0f}",
            "",
            "Source: Specified by user at analysis creation",
        ]
        
        # Add DCF comparison if available
        dcf_comparison = metadata.get('dcf_comparison', {})
        if dcf_comparison:
            dcf_base = dcf_comparison.get('dcf_base_case', 0)
            variance_pct = dcf_comparison.get('variance_percent', 0)
            
            if dcf_base > 0:
                comment_lines.extend([
                    "",
                    "DCF Comparison:",
                    f"  DCF Base Case: ${dcf_base:,.0f}",
                    f"  Variance: {variance_pct:+.1f}%"
                ])
    
    else:
        # Auto-calculated
        comment_lines = [
            "Deal Value - AUTO-CALCULATED",
            "",
            f"Value: ${state.get('deal_value', 0):,.0f}",
            "",
            "Source: Calculated from DCF Analysis",
            "Reason: User did not specify deal value",
            "",
            "Calculation Method:",
            metadata.get('method', 'DCF Base Case Valuation'),
        ]
        
        # Add DCF scenarios if available
        dcf_base = metadata.get('dcf_base_case', 0)
        dcf_optimistic = metadata.get('dcf_optimistic', 0)
        dcf_pessimistic = metadata.get('dcf_pessimistic', 0)
        
        if dcf_base or dcf_optimistic or dcf_pessimistic:
            comment_lines.extend([
                "",
                "DCF Scenarios:",
            ])
            if dcf_base:
                comment_lines.append(f"  Base Case: ${dcf_base:,.0f}")
            if dcf_optimistic:
                comment_lines.append(f"  Optimistic: ${dcf_optimistic:,.0f}")
            if dcf_pessimistic:
                comment_lines.append(f"  Pessimistic: ${dcf_pessimistic:,.0f}")
        
        # Add valuation range if available
        val_range = metadata.get('valuation_range', {})
        if val_range:
            comment_lines.extend([
                "",
                "Valuation Range:",
                f"  Low: ${val_range.get('low', 0):,.0f}",
                f"  Mid: ${val_range.get('mid', 0):,.0f}",
                f"  High: ${val_range.get('high', 0):,.0f}"
            ])
    
    return "\n".join(comment_lines)


def get_deal_value_footnote_for_pdf(state: Dict[str, Any]) -> str:
    """
    Get PDF footnote for deal_value
    
    Returns:
        Formatted footnote text for PDF reports
    """
    metadata = state.get('deal_value_metadata', {})
    
    if not metadata:
        return "* Deal value source not documented."
    
    user_provided = metadata.get('user_provided', False)
    
    if user_provided:
        footnote = f"* Deal value of ${state.get('deal_value', 0):,.0f} was specified by user."
        
        # Add DCF comparison
        dcf_comparison = metadata.get('dcf_comparison', {})
        if dcf_comparison:
            dcf_base = dcf_comparison.get('dcf_base_case', 0)
            variance_pct = dcf_comparison.get('variance_percent', 0)
            
            if dcf_base > 0:
                footnote += f" DCF base case valuation: ${dcf_base:,.0f} (variance: {variance_pct:+.1f}%)."
    
    else:
        # Auto-calculated
        footnote = metadata.get('note', 'Deal value calculated from DCF analysis.')
        
        # Add DCF scenarios
        dcf_base = metadata.get('dcf_base_case', 0)
        dcf_optimistic = metadata.get('dcf_optimistic', 0)
        dcf_pessimistic = metadata.get('dcf_pessimistic', 0)
        
        if dcf_base:
            footnote += f" Base case: ${dcf_base:,.0f}."
        
        if dcf_optimistic and dcf_pessimistic:
            footnote += f" Range: ${dcf_pessimistic:,.0f} - ${dcf_optimistic:,.0f}."
    
    return footnote


def get_deal_value_slide_note_for_ppt(state: Dict[str, Any]) -> str:
    """
    Get PowerPoint slide note for deal_value
    
    Returns:
        Slide note text for PowerPoint presentations
    """
    metadata = state.get('deal_value_metadata', {})
    
    if not metadata:
        return "Deal Value: Source not documented"
    
    user_provided = metadata.get('user_provided', False)
    
    if user_provided:
        note = f"DEAL VALUE: ${state.get('deal_value', 0):,.0f} (User-Specified)\n\n"
        note += "This deal value was provided by the user at the time of analysis creation.\n\n"
        
        # Add DCF comparison
        dcf_comparison = metadata.get('dcf_comparison', {})
        if dcf_comparison:
            dcf_base = dcf_comparison.get('dcf_base_case', 0)
            variance_pct = dcf_comparison.get('variance_percent', 0)
            
            if dcf_base > 0:
                note += f"For comparison, our DCF analysis calculated a base case valuation of ${dcf_base:,.0f}, "
                note += f"which represents a {variance_pct:+.1f}% variance from the user-specified value.\n"
    
    else:
        # Auto-calculated
        note = f"DEAL VALUE: ${state.get('deal_value', 0):,.0f} (Auto-Calculated from DCF)\n\n"
        note += "User did not specify a deal value. The system automatically calculated this value from our DCF analysis.\n\n"
        
        method = metadata.get('method', 'DCF Base Case Valuation')
        note += f"Calculation Method: {method}\n\n"
        
        # Add DCF scenarios
        dcf_base = metadata.get('dcf_base_case', 0)
        dcf_optimistic = metadata.get('dcf_optimistic', 0)
        dcf_pessimistic = metadata.get('dcf_pessimistic', 0)
        
        if dcf_base or dcf_optimistic or dcf_pessimistic:
            note += "DCF Valuation Scenarios:\n"
            if dcf_pessimistic:
                note += f"  • Pessimistic Case: ${dcf_pessimistic:,.0f}\n"
            if dcf_base:
                note += f"  • Base Case: ${dcf_base:,.0f} (used as deal value)\n"
            if dcf_optimistic:
                note += f"  • Optimistic Case: ${dcf_optimistic:,.0f}\n"
    
    return note


def should_show_deal_value_warning(state: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Determine if a warning should be shown about deal_value
    
    Returns:
        Tuple of (show_warning, warning_message)
    """
    metadata = state.get('deal_value_metadata', {})
    deal_value = state.get('deal_value', 0)
    
    # Warning if deal_value is 0 or not set
    if not deal_value or deal_value <= 0:
        return True, "Deal value not specified and could not be calculated from DCF analysis."
    
    # Warning if large variance between user value and DCF
    if metadata.get('user_provided'):
        dcf_comparison = metadata.get('dcf_comparison', {})
        variance_pct = dcf_comparison.get('variance_percent', 0)
        
        if abs(variance_pct) > 25:
            return True, f"User-specified deal value differs from DCF base case by {variance_pct:+.1f}%. Review assumptions."
    
    return False, ""
