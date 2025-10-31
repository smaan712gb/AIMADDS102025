"""
Complete the M&A tabs addition by finding the right insertion point
"""
from pathlib import Path
from loguru import logger

def main():
    """Complete M&A tab method insertion"""
    
    excel_file = Path("src/outputs/revolutionary_excel_generator.py")
    content = excel_file.read_text(encoding='utf-8')
    
    # Check if methods already exist
    if "_create_sources_uses_tab" in content:
        logger.info("✓ M&A tab methods already exist!")
        return True
    
    # The tabs were already added to the list, now we need to add the methods
    logger.info("Finding insertion point for M&A tab methods...")
    
    # Strategy: Insert right after _create_accretion_dilution_tab method ends
    # Find the method and its end
    search_marker = "def _create_accretion_dilution_tab"
    
    if search_marker in content:
        # Find where this method starts
        method_start = content.find(search_marker)
        
        # Find the next method definition after this one
        # Look for the next "def " at the same indentation level (4 spaces)
        next_method_pos = content.find("\n    def ", method_start + 100)
        
        if next_method_pos > 0:
            insert_pos = next_method_pos
            logger.info(f"✓ Found insertion point at position {insert_pos}")
        else:
            logger.error("Could not find next method")
            return False
    else:
        logger.error("Could not find _create_accretion_dilution_tab method")
        return False
    
    # Methods to insert
    new_methods = '''
    def _create_sources_uses_tab(self, wb: Workbook, state: DiligenceState):
        """Create Sources & Uses tab"""
        ws = self._create_sheet_safe(wb, "Sources & Uses")
        ws['A1'] = "SOURCES & USES OF FUNDS - TRANSACTION FINANCING"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells('A1:F1')
        
        agent_output = next((o for o in state.get('agent_outputs', []) 
                            if o.get('agent_name') == 'sources_uses'), None)
        if not agent_output or 'data' not in agent_output:
            ws['A2'] = "Sources & Uses analysis requires deal value"
            return
        
        su_data = agent_output['data']
        uses = su_data.get('uses_of_funds', {})
        sources = su_data.get('sources_of_funds', {})
        
        row = 3
        ws[f'A{row}'] = "USES OF FUNDS"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="FFFFFF")
        ws[f'A{row}'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells(f'A{row}:F{row}')
        row += 1
        
        uses_items = [
            ("Purchase Price", 'equity_purchase_price'),
            ("Debt Refinance", 'refinance_target_debt'),
            ("Transaction Fees", 'transaction_fees'),
        ]
        
        for label, key in uses_items:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = uses.get(key, 0)
            ws[f'B{row}'].number_format = '$#,##0'
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
        
        row += 1
        ws[f'A{row}'] = "SOURCES OF FUNDS"
        ws[f'A{row}'].font = Font(bold=True, size=12, color="FFFFFF")
        ws[f'A{row}'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells(f'A{row}:F{row}')
        row += 1
        
        sources_items = [
            ("Cash", 'acquirer_cash'),
            ("New Debt", 'new_debt'),
            ("New Equity", 'new_equity'),
        ]
        
        for label, key in sources_items:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = sources.get(key, 0)
            ws[f'B{row}'].number_format = '$#,##0'
            ws[f'A{row}'].font = Font(bold=True)
            row += 1
        
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 20

    def _create_deal_structure_tab(self, wb: Workbook, state: DiligenceState):
        """Create Deal Structure tab"""
        ws = self._create_sheet_safe(wb, "Deal Structure")
        ws['A1'] = "DEAL STRUCTURE ANALYSIS - STOCK VS CASH"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells('A1:F1')
        
        agent_output = next((o for o in state.get('agent_outputs', []) 
                            if o.get('agent_name') == 'deal_structuring'), None)
        if not agent_output or 'data' not in agent_output:
            ws['A2'] = "Deal structuring analysis in progress"
            return
        
        ds_data = agent_output['data']
        consideration = ds_data.get('consideration_structure', {})
        
        row = 3
        ws[f'A{row}'] = "CONSIDERATION OPTIONS"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        ws[f'A{row}'] = "Structure"
        ws[f'B{row}'] = "Cash Component"
        ws[f'C{row}'] = "Stock Component"
        for col in ['A', 'B', 'C']:
            ws[f'{col}{row}'].font = Font(bold=True)
        row += 1
        
        structures = [
            ("All Cash", consideration.get('all_cash', {})),
            ("All Stock", consideration.get('all_stock', {})),
            ("Mixed (50/50)", consideration.get('mixed_structure', {})),
        ]
        
        for struct_name, struct_data in structures:
            if struct_data:
                ws[f'A{row}'] = struct_name
                ws[f'B{row}'] = struct_data.get('cash_component', 0)
                ws[f'B{row}'].number_format = '$#,##0'
                ws[f'C{row}'] = struct_data.get('stock_component', 0)
                ws[f'C{row}'].number_format = '$#,##0'
                row += 1
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 20

    def _create_contribution_analysis_tab(self, wb: Workbook, state: DiligenceState):
        """Create Contribution Analysis tab"""
        ws = self._create_sheet_safe(wb, "Contribution Analysis")
        ws['A1'] = "CONTRIBUTION ANALYSIS"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells('A1:F1')
        
        agent_output = next((o for o in state.get('agent_outputs', []) 
                            if o.get('agent_name') == 'contribution_analysis'), None)
        if not agent_output or 'data' not in agent_output:
            ws['A2'] = "Contribution analysis requires acquirer and target data"
            return
        
        ca_data = agent_output['data']
        financial = ca_data.get('financial_contribution', {})
        ownership = ca_data.get('ownership_split', {})
        
        row = 3
        ws[f'A{row}'] = "FINANCIAL CONTRIBUTION"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        ws[f'A{row}'] = "Metric"
        ws[f'B{row}'] = "Acquirer %"
        ws[f'C{row}'] = "Target %"
        for col in ['A', 'B', 'C']:
            ws[f'{col}{row}'].font = Font(bold=True)
        row += 1
        
        metrics = [
            ("Revenue", 'revenue'),
            ("EBITDA", 'ebitda'),
            ("Net Income", 'net_income'),
        ]
        
        for label, key in metrics:
            contrib = financial.get(key, {})
            ws[f'A{row}'] = label
            ws[f'B{row}'] = contrib.get('acquirer_pct', 0)
            ws[f'B{row}'].number_format = '0.0%'
            ws[f'C{row}'] = contrib.get('target_pct', 0)
            ws[f'C{row}'].number_format = '0.0%'
            row += 1
        
        row += 1
        ws[f'A{row}'] = "OWNERSHIP SPLIT"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        ws[f'A{row}'] = "Acquirer Ownership:"
        ws[f'B{row}'] = ownership.get('acquirer_pct', 0)
        ws[f'B{row}'].number_format = '0.0%'
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 15

    def _create_exchange_ratio_tab(self, wb: Workbook, state: DiligenceState):
        """Create Exchange Ratio tab"""
        ws = self._create_sheet_safe(wb, "Exchange Ratio")
        ws['A1'] = "EXCHANGE RATIO ANALYSIS"
        ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
        ws['A1'].fill = PatternFill(start_color=self.colors["header"], fill_type="solid")
        ws.merge_cells('A1:F1')
        
        agent_output = next((o for o in state.get('agent_outputs', []) 
                            if o.get('agent_name') == 'exchange_ratio_analysis'), None)
        if not agent_output or 'data' not in agent_output:
            ws['A2'] = "Exchange ratio analysis requires stock deal structure"
            return
        
        er_data = agent_output['data']
        proposed = er_data.get('proposed_ratio', {})
        premium = er_data.get('premium_analysis', {})
        
        row = 3
        ws[f'A{row}'] = "PROPOSED EXCHANGE RATIO"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        ws[f'A{row}'] = "Exchange Ratio:"
        ws[f'B{row}'] = proposed.get('exchange_ratio', 0)
        ws[f'B{row}'].number_format = '0.0000'
        row += 1
        ws[f'A{row}'] = "Implied Price:"
        ws[f'B{row}'] = proposed.get('implied_price', 0)
        ws[f'B{row}'].number_format = '$0.00'
        row += 2
        
        ws[f'A{row}'] = "PREMIUM ANALYSIS"
        ws[f'A{row}'].font = Font(bold=True, size=12)
        row += 1
        
        premiums = [
            ("1-Day Premium", 'premium_1day'),
            ("1-Week Premium", 'premium_1week'),
            ("1-Month Premium", 'premium_1month'),
        ]
        
        for label, key in premiums:
            ws[f'A{row}'] = label
            ws[f'B{row}'] = premium.get(key, 0)
            ws[f'B{row}'].number_format = '0.0%'
            row += 1
        
        ws.column_dimensions['A'].width = 25
        ws.column_dimensions['B'].width = 20

'''
    
    # Insert the methods
    content = content[:insert_pos] + new_methods + content[insert_pos:]
    logger.info(f"✓ Inserted 4 M&A tab methods")
    
    # Write back
    excel_file.write_text(content, encoding='utf-8')
    logger.info(f"✓ Successfully updated {excel_file}")
    
    return True

if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("COMPLETING M&A TABS ADDITION")
    logger.info("=" * 80)
    
    success = main()
    
    if success:
        logger.info("\n" + "=" * 80)
        logger.info("✓ SUCCESS - 4 M&A tab methods added!")
        logger.info("=" * 80)
        logger.info("\nExcel generator now has all 4 M&A tabs integrated")
        logger.info("Test with: python demo_revolutionary_system.py")
    else:
        logger.error("\n⚠️ Failed to complete - check logs")
