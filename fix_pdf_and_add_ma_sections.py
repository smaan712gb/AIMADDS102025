"""
Fix PDF Generation Error and Add M&A Sections/Slides
Addresses:
1. PDF 'list'.get() error (if any)
2. Add 4 M&A sections to PDF
3. Add 4 M&A slides to PPT
"""
import re
from pathlib import Path


def add_ma_sections_to_pdf():
    """Add 4 M&A sections to revolutionary_pdf_generator.py"""
    
    pdf_path = Path("src/outputs/revolutionary_pdf_generator.py")
    content = pdf_path.read_text(encoding='utf-8')
    
    # Check if sections already exist
    if "_create_sources_uses_section" in content:
        print("✓ M&A sections already exist in PDF generator")
        return False
    
    # Find the position after _create_tax_structuring_section
    tax_section_end = content.find("return content", content.find("def _create_tax_structuring_section"))
    if tax_section_end == -1:
        print("❌ Could not find tax_structuring_section to insert after")
        return False
    
    # Find the end of that method (next method or class end)
    insert_pos = content.find("\n    def ", tax_section_end + 1)
    if insert_pos == -1:
        insert_pos = len(content) - 1
    
    # Define the 4 new M&A section methods
    new_sections = '''
    
    def _create_sources_uses_section(self, state: DiligenceState) -> List:
        """NEW Section: Sources & Uses of Funds"""
        content = []
        content.append(Paragraph("Sources & Uses of Funds", self.styles['Heading2']))
        
        intro = """Our Deal Structuring Agent analyzed the capital structure and funding sources for this transaction. 
        This investment banking-grade analysis shows exactly how the deal will be financed."""
        content.append(Paragraph(intro, self.styles['Body']))
        content.append(Spacer(1, 0.2*inch))
        
        # Extract Sources & Uses data from agent
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'sources_uses'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            content.append(Paragraph(
                "Sources & uses analysis not available. Deal structuring agent has not completed analysis.",
                self.styles['Body']
            ))
            return content
        
        su_data = agent_output['data']
        sources = su_data.get('sources', {})
        uses = su_data.get('uses', {})
        
        # Sources table
        content.append(Paragraph("Sources of Funds", self.styles['Heading3']))
        sources_data = [
            ['Source', 'Amount', '% of Total']
        ]
        
        total_sources = sources.get('total', 0)
        for source_name, amount in sources.items():
            if source_name != 'total' and amount > 0:
                pct = (amount / total_sources * 100) if total_sources > 0 else 0
                sources_data.append([
                    source_name.replace('_', ' ').title(),
                    f"${amount/1e9:.2f}B" if amount >= 1e9 else f"${amount/1e6:.1f}M",
                    f"{pct:.1f}%"
                ])
        
        sources_data.append(['TOTAL SOURCES', f"${total_sources/1e9:.2f}B", '100.0%'])
        
        sources_table = Table(sources_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        sources_table.setStyle(self._get_standard_table_style())
        content.append(sources_table)
        
        content.append(Spacer(1, 0.2*inch))
        
        # Uses table
        content.append(Paragraph("Uses of Funds", self.styles['Heading3']))
        uses_data = [
            ['Use', 'Amount', '% of Total']
        ]
        
        total_uses = uses.get('total', 0)
        for use_name, amount in uses.items():
            if use_name != 'total' and amount > 0:
                pct = (amount / total_uses * 100) if total_uses > 0 else 0
                uses_data.append([
                    use_name.replace('_', ' ').title(),
                    f"${amount/1e9:.2f}B" if amount >= 1e9 else f"${amount/1e6:.1f}M",
                    f"{pct:.1f}%"
                ])
        
        uses_data.append(['TOTAL USES', f"${total_uses/1e9:.2f}B", '100.0%'])
        
        uses_table = Table(uses_data, colWidths=[3*inch, 2*inch, 1.5*inch])
        uses_table.setStyle(self._get_standard_table_style())
        content.append(uses_table)
        
        content.append(Spacer(1, 0.2*inch))
        
        # Financing recommendation
        recommendation = su_data.get('financing_recommendation', 'Optimal capital structure identified')
        content.append(Paragraph(
            f"<b>Financing Recommendation:</b> {recommendation}",
            self.styles['Body']
        ))
        
        return content
    
    def _create_deal_structure_section(self, state: DiligenceState) -> List:
        """NEW Section: Deal Structure Analysis"""
        content = []
        content.append(Paragraph("Deal Structure Analysis", self.styles['Heading2']))
        
        intro = """Our Deal Structuring Agent evaluated alternative transaction structures to maximize value creation 
        and minimize execution risk."""
        content.append(Paragraph(intro, self.styles['Body']))
        content.append(Spacer(1, 0.2*inch))
        
        # Extract Deal Structure data from agent
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'deal_structuring'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            content.append(Paragraph(
                "Deal structure analysis not available.",
                self.styles['Body']
            ))
            return content
        
        ds_data = agent_output['data']
        
        # Structure comparison table
        content.append(Paragraph("Structure Comparison", self.styles['Heading3']))
        
        structure_comp = ds_data.get('structure_comparison', {})
        comp_data = [
            ['Structure Type', 'Pros', 'Cons', 'Tax Efficiency']
        ]
        
        for struct_name in ['stock_deal', 'cash_deal', 'mixed_consideration']:
            struct = structure_comp.get(struct_name, {})
            if struct:
                comp_data.append([
                    struct.get('name', struct_name.replace('_', ' ').title()),
                    ', '.join(struct.get('pros', [])[:2]),
                    ', '.join(struct.get('cons', [])[:2]),
                    struct.get('tax_efficiency', 'Medium')
                ])
        
        if len(comp_data) > 1:
            comp_table = Table(comp_data, colWidths=[1.5*inch, 2*inch, 2*inch, 1.5*inch])
            comp_table.setStyle(self._get_standard_table_style())
            content.append(comp_table)
        
        content.append(Spacer(1, 0.2*inch))
        
        # Recommended structure
        recommended = ds_data.get('recommended_structure', 'Mixed cash and stock consideration')
        rationale = ds_data.get('rationale', 'Balances risk and return for both parties')
        
        content.append(Paragraph("Recommended Structure:", self.styles['Heading3']))
        content.append(Paragraph(
            f"<b>{recommended}</b>",
            ParagraphStyle('DSRec', parent=self.styles['Body'], fontSize=12, 
                          fontName='Helvetica-Bold', textColor=self.colors["success"])
        ))
        content.append(Spacer(1, 0.1*inch))
        content.append(Paragraph(f"<b>Rationale:</b> {rationale}", self.styles['Body']))
        
        return content
    
    def _create_contribution_analysis_section(self, state: DiligenceState) -> List:
        """NEW Section: Contribution Analysis"""
        content = []
        content.append(Paragraph("Contribution Analysis", self.styles['Heading2']))
        
        intro = """Our Contribution Analysis Agent evaluated what each party brings to the combined entity. 
        This analysis is critical for determining fair exchange ratios and ownership splits."""
        content.append(Paragraph(intro, self.styles['Body']))
        content.append(Spacer(1, 0.2*inch))
        
        # Extract Contribution data from agent
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'contribution_analysis'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            content.append(Paragraph(
                "Contribution analysis not available. Requires both target and acquirer data.",
                self.styles['Body']
            ))
            return content
        
        ca_data = agent_output['data']
        
        # Contribution metrics table
        content.append(Paragraph("Relative Contributions", self.styles['Heading3']))
        
        metrics = ca_data.get('contribution_metrics', {})
        contrib_data = [
            ['Metric', 'Target Contribution', 'Acquirer Contribution']
        ]
        
        contrib_items = [
            ('Revenue', 'revenue'),
            ('EBITDA', 'ebitda'),
            ('Market Cap', 'market_cap'),
            ('Enterprise Value', 'enterprise_value')
        ]
        
        for label, key in contrib_items:
            target_val = metrics.get(f'target_{key}_contribution', 0)
            acquirer_val = metrics.get(f'acquirer_{key}_contribution', 0)
            contrib_data.append([
                label,
                f"{target_val:.1f}%" if target_val > 0 else 'N/A',
                f"{acquirer_val:.1f}%" if acquirer_val > 0 else 'N/A'
            ])
        
        contrib_table = Table(contrib_data, colWidths=[2.5*inch, 2*inch, 2*inch])
        contrib_table.setStyle(self._get_standard_table_style())
        content.append(contrib_table)
        
        content.append(Spacer(1, 0.2*inch))
        
        # Fair value assessment
        fairness = ca_data.get('fairness_assessment', 'Under review')
        ownership_recommendation = ca_data.get('ownership_recommendation', {})
        
        content.append(Paragraph("Fairness Assessment:", self.styles['Heading3']))
        content.append(Paragraph(f"<b>{fairness}</b>", self.styles['Body']))
        
        if ownership_recommendation:
            target_share = ownership_recommendation.get('target_shareholders_pct', 0)
            acquirer_share = ownership_recommendation.get('acquirer_shareholders_pct', 0)
            content.append(Spacer(1, 0.1*inch))
            content.append(Paragraph(
                f"<b>Recommended Ownership Split:</b> Target shareholders {target_share:.1f}%, "
                f"Acquirer shareholders {acquirer_share:.1f}%",
                self.styles['Body']
            ))
        
        return content
    
    def _create_exchange_ratio_section(self, state: DiligenceState) -> List:
        """NEW Section: Exchange Ratio Analysis"""
        content = []
        content.append(Paragraph("Exchange Ratio Analysis", self.styles['Heading2']))
        
        intro = """Our Exchange Ratio Agent calculated the fair share exchange for this all-stock or 
        stock-component transaction. This analysis incorporates multiple valuation methodologies."""
        content.append(Paragraph(intro, self.styles['Body']))
        content.append(Spacer(1, 0.2*inch))
        
        # Extract Exchange Ratio data from agent
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'exchange_ratio_analysis'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            content.append(Paragraph(
                "Exchange ratio analysis not available. Only applicable for stock or mixed-consideration deals.",
                self.styles['Body']
            ))
            return content
        
        er_data = agent_output['data']
        
        # Exchange ratio summary
        content.append(Paragraph("Recommended Exchange Ratio", self.styles['Heading3']))
        
        base_ratio = er_data.get('base_exchange_ratio', 0)
        range_low = er_data.get('exchange_ratio_range', {}).get('low', 0)
        range_high = er_data.get('exchange_ratio_range', {}).get('high', 0)
        
        ratio_data = [
            ['Metric', 'Value'],
            ['Base Exchange Ratio', f"{base_ratio:.4f}" if base_ratio > 0 else 'N/A'],
            ['Exchange Ratio Range', f"{range_low:.4f} - {range_high:.4f}" if range_low > 0 else 'N/A'],
            ['Implied Target Price', f"${er_data.get('implied_target_price', 0):.2f}"],
            ['Premium to Market', f"{er_data.get('premium_to_market_pct', 0):.1f}%"]
        ]
        
        ratio_table = Table(ratio_data, colWidths=[3*inch, 3.5*inch])
        ratio_table.setStyle(self._get_standard_table_style())
        content.append(ratio_table)
        
        content.append(Spacer(1, 0.2*inch))
        
        # Methodology summary
        methods_used = er_data.get('methodologies_used', [])
        if methods_used:
            content.append(Paragraph("Valuation Methodologies Used:", self.styles['Heading3']))
            for method in methods_used[:5]:
                content.append(Paragraph(f"• {method}", self.styles['Bullet']))
        
        content.append(Spacer(1, 0.2*inch))
        
        # Recommendation
        recommendation = er_data.get('recommendation', 'Exchange ratio within fair value range')
        content.append(Paragraph(
            f"<b>Recommendation:</b> {recommendation}",
            self.styles['Body']
        ))
        
        return content
'''
    
    # Insert the new sections
    modified_content = content[:insert_pos] + new_sections + content[insert_pos:]
    
    # Now add calls to these sections in generate_revolutionary_report
    # Find the section after "Section 5B: EPS Accretion/Dilution"
    accretion_section = "# Section 5B: NEW - EPS Accretion/Dilution"
    accretion_pos = modified_content.find(accretion_section)
    
    if accretion_pos == -1:
        print("❌ Could not find accretion section to insert after")
        return False
    
    # Find the PageBreak after it
    pagebreak_pos = modified_content.find("story.append(PageBreak())", accretion_pos)
    if pagebreak_pos == -1:
        print("❌ Could not find PageBreak to insert after")
        return False
    
    # Insert the 4 new M&A sections into the story
    ma_section_calls = '''
        
        # Section 5C: NEW - Sources & Uses
        story.extend(self._create_section_header("5C. SOURCES & USES OF FUNDS"))
        story.extend(self._create_sources_uses_section(state))
        story.append(PageBreak())
        
        # Section 5D: NEW - Deal Structure
        story.extend(self._create_section_header("5D. DEAL STRUCTURE ANALYSIS"))
        story.extend(self._create_deal_structure_section(state))
        story.append(PageBreak())
        
        # Section 5E: NEW - Contribution Analysis
        story.extend(self._create_section_header("5E. CONTRIBUTION ANALYSIS"))
        story.extend(self._create_contribution_analysis_section(state))
        story.append(PageBreak())
        
        # Section 5F: NEW - Exchange Ratio
        story.extend(self._create_section_header("5F. EXCHANGE RATIO ANALYSIS"))
        story.extend(self._create_exchange_ratio_section(state))
        story.append(PageBreak())
'''
    
    # Find the end of the line with PageBreak
    line_end = modified_content.find("\n", pagebreak_pos)
    modified_content = modified_content[:line_end+1] + ma_section_calls + modified_content[line_end+1:]
    
    # Update TOC to include new sections
    toc_section = modified_content.find("def _create_revolutionary_toc")
    if toc_section > 0:
        # Find the list of TOC items
        toc_items_start = modified_content.find("toc_items = [", toc_section)
        # Find the lbo line
        lbo_line = modified_content.find('("5A. LBO Analysis', toc_items_start)
        if lbo_line > 0:
            # Find the end of that line
            line_end = modified_content.find('"),', lbo_line) + 3
            # Insert new TOC entries
            new_toc = '''
            ("5C. Sources & Uses of Funds (NEW)", "20"),
            ("5D. Deal Structure Analysis (NEW)", "21"),
            ("5E. Contribution Analysis (NEW)", "22"),
            ("5F. Exchange Ratio Analysis (NEW)", "23"),'''
            modified_content = modified_content[:line_end] + new_toc + modified_content[line_end:]
    
    # Write back
    pdf_path.write_text(modified_content, encoding='utf-8')
    print("✓ Added 4 M&A sections to PDF generator")
    print("  - Sources & Uses")
    print("  - Deal Structure")
    print("  - Contribution Analysis")
    print("  - Exchange Ratio")
    return True


def add_ma_slides_to_ppt():
    """Add 4 M&A slides to revolutionary_ppt_generator.py"""
    
    ppt_path = Path("src/outputs/revolutionary_ppt_generator.py")
    
    if not ppt_path.exists():
        print("❌ PPT generator not found")
        return False
    
    content = ppt_path.read_text(encoding='utf-8')
    
    # Check if slides already exist
    if "_create_sources_uses_slide" in content:
        print("✓ M&A slides already exist in PPT generator")
        return False
    
    # Find position to insert (after risk slides typically)
    risk_slide_pos = content.rfind("def _create")
    if risk_slide_pos == -1:
        print("❌ Could not find position to insert M&A slides")
        return False
    
    # Find end of last method
    next_method_or_end = content.find("\n\nclass ", risk_slide_pos + 1)
    if next_method_or_end == -1:
        next_method_or_end = len(content) - 1
    
    # Define the 4 new M&A slide methods
    new_slides = '''
    
    def _create_sources_uses_slide(self, state: DiligenceState):
        """NEW Slide: Sources & Uses of Funds"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])  # Blank layout
        
        # Title
        title = slide.shapes.title
        title.text = "Sources & Uses of Funds"
        
        # Extract data
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'sources_uses'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            # Add "not available" message
            textbox = slide.shapes.add_textbox(
                Inches(1), Inches(2), Inches(8), Inches(1)
            )
            textbox.text = "Sources & uses analysis not available"
            return
        
        su_data = agent_output['data']
        sources = su_data.get('sources', {})
        uses = su_data.get('uses', {})
        
        # Create two-column layout for sources and uses
        # Sources table (left)
        left = Inches(0.5)
        top = Inches(1.5)
        width = Inches(4.5)
        height = Inches(4)
        
        sources_table = slide.shapes.add_table(
            len(sources) + 1, 2, left, top, width, height
        ).table
        
        # Headers
        sources_table.cell(0, 0).text = "Sources"
        sources_table.cell(0, 1).text = "Amount"
        
        # Data
        row = 1
        total_sources = sources.get('total', 0)
        for source_name, amount in sources.items():
            if source_name != 'total' and amount > 0:
                sources_table.cell(row, 0).text = source_name.replace('_', ' ').title()
                sources_table.cell(row, 1).text = f"${amount/1e9:.2f}B"
                row += 1
        
        # Uses table (right)
        right = Inches(5.5)
        
        uses_table = slide.shapes.add_table(
            len(uses) + 1, 2, right, top, width, height
        ).table
        
        # Headers
        uses_table.cell(0, 0).text = "Uses"
        uses_table.cell(0, 1).text = "Amount"
        
        # Data
        row = 1
        for use_name, amount in uses.items():
            if use_name != 'total' and amount > 0:
                uses_table.cell(row, 0).text = use_name.replace('_', ' ').title()
                uses_table.cell(row, 1).text = f"${amount/1e9:.2f}B"
                row += 1
    
    def _create_deal_structure_slide(self, state: DiligenceState):
        """NEW Slide: Deal Structure"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])
        
        title = slide.shapes.title
        title.text = "Deal Structure Analysis"
        
        # Extract data
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'deal_structuring'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            textbox = slide.shapes.add_textbox(
                Inches(1), Inches(2), Inches(8), Inches(1)
            )
            textbox.text = "Deal structure analysis not available"
            return
        
        ds_data = agent_output['data']
        
        # Recommended structure box
        left = Inches(1)
        top = Inches(1.5)
        width = Inches(8)
        height = Inches(1.5)
        
        rec_box = slide.shapes.add_textbox(left, top, width, height)
        rec_frame = rec_box.text_frame
        
        recommended = ds_data.get('recommended_structure', 'Mixed consideration')
        rationale = ds_data.get('rationale', 'Optimal risk-return balance')
        
        p = rec_frame.paragraphs[0]
        p.text = f"Recommended Structure: {recommended}"
        p.font.size = Pt(18)
        p.font.bold = True
        
        p = rec_frame.add_paragraph()
        p.text = f"Rationale: {rationale}"
        p.font.size = Pt(14)
        
        # Structure comparison table
        structure_comp = ds_data.get('structure_comparison', {})
        if structure_comp:
            table_top = Inches(3.5)
            table = slide.shapes.add_table(
                4, 3, left, table_top, width, Inches(2.5)
            ).table
            
            # Headers
            table.cell(0, 0).text = "Structure"
            table.cell(0, 1).text = "Key Benefits"
            table.cell(0, 2).text = "Considerations"
            
            # Data
            row = 1
            for struct_name in ['stock_deal', 'cash_deal', 'mixed_consideration']:
                struct = structure_comp.get(struct_name, {})
                if struct and row < 4:
                    table.cell(row, 0).text = struct.get('name', struct_name.replace('_', ' ').title())
                    table.cell(row, 1).text = ', '.join(struct.get('pros', [])[:2])
                    table.cell(row, 2).text = ', '.join(struct.get('cons', [])[:2])
                    row += 1
    
    def _create_contribution_analysis_slide(self, state: DiligenceState):
        """NEW Slide: Contribution Analysis"""
        slide = self.prs.slides.add_slide(self.prs.slide_layouts[5])
        
        title = slide.shapes.title
        title.text = "Contribution Analysis"
        
        # Extract data
        agent_output = next(
            (o for o in state.get('agent_outputs', []) 
             if o.get('agent_name') == 'contribution_analysis'),
            None
        )
        
        if not agent_output or 'data' not in agent_output:
            textbox = slide.shapes.add_textbox(
                Inches(1), Inches(2), Inches(8), Inches(1)
            )
            textbox.text = "Contribution analysis not available"
            return
        
        ca_data = agent_output['data']
        metrics = ca_data.get('contribution_metrics', {})
        
        # Contribution comparison table
        left = Inches(1.5)
        top = Inches(1.5)
        width = Inches(7)
        height = Inches(3)
        
        table = slide.shapes.add_table(5, 3, left, top, width, height).table
        
        # Headers
        table.cell(0, 0).text = "Metric"
        table.cell(0, 1).text = "Target %"
        table.cell(0, 2).text = "Acquirer %"
        
        # Data
        contrib_items = [
            ('Revenue', 'revenue'),
            ('EBITDA', 'ebitda'),
            ('Market Cap', 'market_cap'),
            ('Enterprise Value', 'enterprise_value')
        ]
        
        for idx, (label, key) in enumerate(contrib_items, 1):
            table.cell(idx, 0).text = label
            target_val = metrics.get(f'target_{key}_contribution', 0)
            acquirer_val = metrics.get(f'acquirer_{key}_contribution', 0)
            table.cell(idx, 1).text = f"{target_val:.1f}%" if target_val > 0 else 'N/A'
            table.cell(idx, 2).text = f"{acquirer_val:.1f}%" if acquirer_val > 0 else 'N/A'
        
        # Fairness assessment
        fairness = ca_data.get('fairness_assessment', 'Under review')
        fairness_box = slide.shapes.add_textbox(
            Inches(1
