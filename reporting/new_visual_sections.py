# NEW VISUAL, CHART-FOCUSED REPORT SECTIONS
# This file contains the redesigned report sections focusing on charts over tables

from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Spacer
from django.db.models import Sum

# Import helper functions from main views
from reporting.views import (
    create_section_header,
    create_subsection_header,
    create_normal_paragraph,
    create_chart
)


def generate_financial_charts(building, start_date, end_date):
    """
    COMPREHENSIVE Financial Section - Mirrors frontend Financial page exactly
    1. General Report Tab: Monthly Evolution chart
    2. By Account Tab: Individual account charts
    3. Market Tab: Market values comparison chart + Detailed unit analysis table
    """
    from financials.models import (
        FinancialMainAccount, FinancialAccountTransaction,
        MarketValueSetting
    )
    from financials.serializers import FinancialReportSerializer
    from building_mgmt.models import Unit
    from datetime import datetime
    from decimal import Decimal
    from collections import defaultdict
    from reportlab.lib.units import inch
    from reportlab.platypus import Table, TableStyle
    from reportlab.lib import colors

    elements = []

    # Section Header
    elements.append(PageBreak())
    elements.append(create_section_header('1. Financial Performance Analysis', '#ffc107'))
    elements.append(Spacer(1, 0.2*inch))

    # Get report data using the same serializer as frontend
    start_month = start_date.strftime('%Y-%m')
    end_month = end_date.strftime('%Y-%m')

    serializer_data = {
        'building_id': building.id,
        'fiscal_year_start': start_month,
        'fiscal_year_end': end_month
    }

    serializer = FinancialReportSerializer(serializer_data)
    report_data = serializer.to_representation(serializer_data)

    # ==================================================================
    # TAB 1: GENERAL REPORT - MONTHLY EVOLUTION
    # ==================================================================
    elements.append(create_subsection_header('General Report - Monthly Evolution'))
    elements.append(Spacer(1, 0.1*inch))

    monthly_data = report_data.get('monthlyData', [])
    total_revenue = report_data.get('totalPlannedRevenue', 0)
    total_expense = sum(float(m.get('totalExpense', 0)) for m in monthly_data)
    balance = total_revenue - total_expense

    if monthly_data:
        # Summary Cards Text
        elements.append(create_normal_paragraph(
            f"<b>Total Revenue:</b> <font color='#28a745'>R$ {total_revenue:,.2f}</font> | "
            f"<b>Total Expenses:</b> <font color='#dc3545'>R$ {total_expense:,.2f}</font> | "
            f"<b>Balance:</b> <font color='{'#17a2b8' if balance >= 0 else '#dc3545'}'>R$ {balance:,.2f}</font>"
        ))
        elements.append(Spacer(1, 0.2*inch))

        # Calculate projection (same logic as frontend)
        completed_months = sum(1 for m in monthly_data if float(m.get('totalExpense', 0)) > 0)
        if completed_months > 0 and total_revenue > 0:
            avg_monthly_spending = total_expense / completed_months
            total_months = len(monthly_data)
            projected_annual = avg_monthly_spending * total_months
            percentage = ((projected_annual / total_revenue) * 100) - 100

            # Determine flag
            if projected_annual <= total_revenue:
                flag = 'green'
                flag_text = '🟢 On Track: Current spending pace is within budget.'
                flag_color = '#28a745'
            elif percentage <= 20:
                flag = 'yellow'
                flag_text = f'🟡 Caution: Projected to exceed budget by {abs(percentage):.1f}%. Monitoring required.'
                flag_color = '#ffc107'
            else:
                flag = 'red'
                flag_text = f'🔴 Warning: Projected to exceed budget by {abs(percentage):.1f}%. Corrective action needed.'
                flag_color = '#dc3545'

            elements.append(create_normal_paragraph(
                f"<font color='{flag_color}'><b>{flag_text}</b></font> (Based on {completed_months} completed months)"
            ))
            elements.append(Spacer(1, 0.2*inch))

        # Total Comparison Bar Chart (frontend shows Total Revenue vs Total Expenses)
        chart_data = [
            ('Total Revenue', total_revenue),
            ('Total Expenses', total_expense)
        ]
        chart = create_chart('bar', chart_data,
                           'Total Comparison',
                           '', 'Amount (R$)',
                           colors_list=['#10b981', '#ef4444'])
        elements.append(chart)
        elements.append(Spacer(1, 0.3*inch))

    # ==================================================================
    # TAB 2: BY ACCOUNT - INDIVIDUAL ACCOUNT CHARTS
    # ==================================================================
    accounts_data = report_data.get('accountsData', [])

    if accounts_data:
        elements.append(PageBreak())
        elements.append(create_subsection_header('By Account - Individual Performance'))
        elements.append(Spacer(1, 0.2*inch))

        for account_data in accounts_data[:10]:  # Limit to first 10 accounts to avoid overly long reports
            account_code = account_data.get('accountCode', '')
            account_name = account_data.get('accountName', '')
            monthly_records = account_data.get('monthlyData', [])

            # Calculate totals
            total_expected = sum(float(m.get('expectedAmount', 0)) for m in monthly_records)
            total_actual = sum(float(m.get('actualAmount', 0)) for m in monthly_records)
            account_balance = total_expected - total_actual

            # Account header
            elements.append(create_normal_paragraph(
                f"<b><font color='#6b7280'>{account_code}</font> {account_name}</b>"
            ))
            elements.append(create_normal_paragraph(
                f"<b>Expected:</b> <font color='#10b981'>R$ {total_expected:,.2f}</font> | "
                f"<b>Actual:</b> <font color='#ef4444'>R$ {total_actual:,.2f}</font> | "
                f"<b>Balance:</b> <font color='{'#17a2b8' if account_balance >= 0 else '#dc3545'}'>R$ {account_balance:+,.2f}</font>"
            ))
            elements.append(Spacer(1, 0.1*inch))

            # Line chart with expected vs actual (frontend uses LineChart)
            if len(monthly_records) > 0:
                # Prepare data: list of (month, expected, actual) tuples
                # matplotlib doesn't support multi-series directly in our create_chart
                # So we'll create two separate series and overlay them

                # For now, create a simple comparison showing months with values
                chart_months = [m.get('month', '')[-5:] for m in monthly_records]  # Get MM-YY format
                expected_values = [float(m.get('expectedAmount', 0)) for m in monthly_records]
                actual_values = [float(m.get('actualAmount', 0)) for m in monthly_records]

                # Create a dual-series line chart manually using matplotlib
                import matplotlib
                matplotlib.use('Agg')
                matplotlib.rcParams['font.family'] = 'DejaVu Sans'
                matplotlib.rcParams['axes.unicode_minus'] = False
                import matplotlib.pyplot as plt
                from io import BytesIO
                from reportlab.platypus import Image

                fig, ax = plt.subplots(figsize=(6, 3), dpi=100)
                ax.plot(chart_months, expected_values, color='#10b981', linewidth=2, marker='o', label='Expected')
                ax.plot(chart_months, actual_values, color='#ef4444', linewidth=2, marker='o', label='Actual')
                ax.set_xlabel('Month')
                ax.set_ylabel('Amount (R$)')
                ax.set_title(f'{account_code} - Monthly Performance')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45, ha='right')
                plt.tight_layout()

                # Convert to image
                img_buffer = BytesIO()
                fig.savefig(img_buffer, format='png', bbox_inches='tight')
                img_buffer.seek(0)
                plt.close(fig)

                img = Image(img_buffer, width=6*inch, height=3*inch)
                elements.append(img)
                elements.append(Spacer(1, 0.3*inch))

    # ==================================================================
    # TAB 3: MARKET - MARKET VALUES COMPARISON CHART
    # ==================================================================
    units = Unit.objects.filter(building=building)
    accounts = FinancialMainAccount.objects.filter(building=building)

    if units.exists() and accounts.exists():
        try:
            market_settings = MarketValueSetting.objects.get(building=building)

            elements.append(PageBreak())
            elements.append(create_subsection_header('Market Values Comparison'))
            elements.append(Spacer(1, 0.2*inch))

            # Calculate average condo fee per m² (same logic as frontend)
            ordinary_budget = float(accounts.filter(balance_type='ordinary').aggregate(
                Sum('expected_amount'))['expected_amount__sum'] or 0)
            total_area = float(units.aggregate(Sum('area'))['area__sum'] or 0)
            total_ideal_fraction = float(units.aggregate(Sum('ideal_fraction'))['ideal_fraction__sum'] or 0)

            # Calculate average condo fee per m² using the frontend formula
            # Frontend: condoFeePerM2 = feeInfo.totalFee / ((totalAreaSum / 100) * idealFraction)
            # Average across all units
            avg_condo_fee_per_m2 = 0
            if total_area > 0:
                # Simplified: ordinary_budget / total_area gives average fee per m²
                # But frontend uses more complex formula with ideal fraction
                # For consistency, let's use the exact frontend logic
                unit_fees = []
                for unit in units:
                    area = float(unit.area)
                    ideal_fraction = float(unit.ideal_fraction)
                    if total_area > 0 and ideal_fraction > 0:
                        # Calculate unit's total fee
                        unit_total_fee = ordinary_budget * (ideal_fraction / 100)
                        # Calculate fee per m² for this unit
                        temp_var = (total_area / 100) * ideal_fraction
                        if temp_var > 0:
                            unit_fee_per_m2 = unit_total_fee / temp_var
                            unit_fees.append(unit_fee_per_m2)

                if unit_fees:
                    avg_condo_fee_per_m2 = sum(unit_fees) / len(unit_fees)

            condominium_min = float(market_settings.condominium_min)
            condominium_max = float(market_settings.condominium_max)

            # Summary stats
            elements.append(create_normal_paragraph(
                f"<b>Total Monthly Collection:</b> R$ {ordinary_budget:,.2f} | "
                f"<b>Total Units:</b> {units.count()} | "
                f"<b>Avg Condo Fee/m²:</b> R$ {avg_condo_fee_per_m2:.2f}"
            ))
            elements.append(Spacer(1, 0.2*inch))

            # Market Values Comparison Chart (Area chart like frontend)
            # Frontend shows 12 months with gray area between min/max and orange line for average
            # Simplified for PDF: show the three values as bars
            elements.append(create_normal_paragraph("<b>Market Values Comparison (R$/m²)</b>"))
            elements.append(Spacer(1, 0.1*inch))

            # Sort values to show range
            values_list = [
                ('Condominium Min', condominium_min),
                ('Average Condo Fee', avg_condo_fee_per_m2),
                ('Condominium Max', condominium_max)
            ]
            values_sorted = sorted(values_list, key=lambda x: x[1])

            chart = create_chart('bar', values_sorted,
                               'Market Values Comparison',
                               '', 'R$/m²',
                               colors_list=['#9ca3af', '#ff7300', '#6b7280'])
            elements.append(chart)
            elements.append(Spacer(1, 0.3*inch))

            # ==================================================================
            # TAB 3: MARKET - DETAILED UNIT ANALYSIS TABLE
            # ==================================================================
            elements.append(PageBreak())
            elements.append(create_subsection_header('Detailed Unit Analysis'))
            elements.append(Spacer(1, 0.2*inch))

            # Prepare table data (same logic as frontend)
            rental_min = float(market_settings.rental_min)
            rental_max = float(market_settings.rental_max)
            sale_min = float(market_settings.sale_min)
            sale_max = float(market_settings.sale_max)

            # Table header
            table_data = [[
                'Unit', 'Owner', 'Area', 'Ideal Fraction',
                'Rental Min', 'Rental Max', 'Sale Min', 'Sale Max'
            ]]

            # Table rows
            totals = {
                'area': 0,
                'ideal_fraction': 0,
                'rental_min': 0,
                'rental_max': 0,
                'sale_min': 0,
                'sale_max': 0
            }

            for unit in units[:50]:  # Limit to 50 units to avoid overly long tables
                area = float(unit.area)
                ideal_frac = float(unit.ideal_fraction)

                # Calculate values (same as frontend logic)
                unit_rental_min = area * rental_min
                unit_rental_max = area * rental_max
                unit_sale_min = area * sale_min
                unit_sale_max = area * sale_max

                table_data.append([
                    unit.number,
                    unit.owner or '-',
                    f'{area:.2f}',
                    f'{ideal_frac:.4f}%',
                    f'R$ {unit_rental_min:,.2f}',
                    f'R$ {unit_rental_max:,.2f}',
                    f'R$ {unit_sale_min:,.2f}',
                    f'R$ {unit_sale_max:,.2f}'
                ])

                # Accumulate totals
                totals['area'] += area
                totals['ideal_fraction'] += ideal_frac
                totals['rental_min'] += unit_rental_min
                totals['rental_max'] += unit_rental_max
                totals['sale_min'] += unit_sale_min
                totals['sale_max'] += unit_sale_max

            # Add totals row
            table_data.append([
                'TOTAL', '',
                f'{totals["area"]:.2f}',
                f'{totals["ideal_fraction"]:.4f}%',
                f'R$ {totals["rental_min"]:,.2f}',
                f'R$ {totals["rental_max"]:,.2f}',
                f'R$ {totals["sale_min"]:,.2f}',
                f'R$ {totals["sale_max"]:,.2f}'
            ])

            # Create table
            table = Table(table_data, colWidths=[0.7*inch, 1.2*inch, 0.7*inch, 0.9*inch, 1*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e5e7eb')),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 0.2*inch))

            if units.count() > 50:
                elements.append(create_normal_paragraph(
                    f"<i>Note: Showing first 50 units of {units.count()} total units.</i>"
                ))

        except MarketValueSetting.DoesNotExist:
            elements.append(create_normal_paragraph(
                "Market value settings not configured for this building."
            ))

    return elements


def generate_consumption_charts(building, start_date, end_date):
    """
    VISUAL Consumption Section - CHARTS ONLY
    Focus: Consumption vs Payments comparison
    """
    from consumptions.models import ConsumptionRegister, ConsumptionAccount
    from datetime import datetime

    elements = []

    # Section Header
    from reportlab.lib.units import inch
    elements.append(PageBreak())
    elements.append(create_section_header('2. Consumption Analysis', '#17a2b8'))
    elements.append(Spacer(1, 0.2*inch))

    start_month = start_date.strftime('%Y-%m')
    end_month = end_date.strftime('%Y-%m')

    # Get consumption and payment data
    registers = ConsumptionRegister.objects.filter(
        building=building,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')

    accounts = ConsumptionAccount.objects.filter(
        month__gte=start_month,
        month__lte=end_month
    ).order_by('month')

    # Chart 1: Consumption vs Payments by Utility Type
    for utility_type in ['water', 'electricity', 'gas']:
        utility_registers = registers.filter(utility_type=utility_type)
        utility_accounts = accounts.filter(utility_type=utility_type)

        if utility_registers.exists() or utility_accounts.exists():
            # Aggregate by month
            from collections import defaultdict
            monthly_consumption = defaultdict(float)
            monthly_payments = defaultdict(float)

            for reg in utility_registers:
                month_key = reg.date.strftime('%Y-%m')
                monthly_consumption[month_key] += float(reg.value)

            for acc in utility_accounts:
                monthly_payments[acc.month] = float(acc.amount)

            # Get all months
            all_months = sorted(set(list(monthly_consumption.keys()) + list(monthly_payments.keys())))

            if all_months:
                utility_label = utility_type.capitalize()
                elements.append(create_subsection_header(f'{utility_label} - Consumption vs Payments'))

                # Create dual-series data for comparison
                # We'll create separate charts for consumption and payment
                if monthly_consumption:
                    consumption_data = [(month, monthly_consumption.get(month, 0)) for month in all_months]
                    chart1 = create_chart('line', consumption_data,
                                        f'{utility_label} Consumption Trend',
                                        'Month', 'Consumption',
                                        colors_list=['#17a2b8'])
                    elements.append(chart1)
                    elements.append(Spacer(1, 0.2*inch))

                if monthly_payments:
                    payment_data = [(month, monthly_payments.get(month, 0)) for month in all_months]
                    chart2 = create_chart('line', payment_data,
                                        f'{utility_label} Payment Trend',
                                        'Month', 'Amount (R$)',
                                        colors_list=['#28a745'])
                    elements.append(chart2)
                    elements.append(Spacer(1, 0.3*inch))

    return elements


def generate_legal_visual(building, start_date, end_date):
    """
    VISUAL Legal Obligations - Modern, colorful layout
    Includes: LegalObligation, LegalTemplate, and LegalObligationCompletion data
    """
    from legal_docs.models import LegalObligation, LegalTemplate, LegalObligationCompletion

    elements = []

    # Section Header
    elements.append(PageBreak())
    elements.append(create_section_header('3. Legal Obligations Status', '#dc3545'))
    elements.append(Spacer(1, 0.2*inch))

    # Query ALL obligations for this building (not filtered by date to show all data)
    obligations = LegalObligation.objects.filter(building=building).order_by('-due_date')

    # Query ALL templates for this building
    templates = LegalTemplate.objects.filter(
        building=building,
        active=True
    ).order_by('name')

    # If no building-specific templates, get general templates
    if not templates.exists():
        templates = LegalTemplate.objects.filter(
            building__isnull=True,
            active=True
        ).order_by('name')

    total_items = obligations.count() + templates.count()

    if total_items == 0:
        elements.append(create_normal_paragraph(
            "No legal obligations or templates found for this building."
        ))
        return elements

    # Chart 1: LegalObligation Status Distribution
    if obligations.exists():
        elements.append(create_subsection_header('Legal Obligations by Status'))

        status_counts = {}
        for obl in obligations:
            status_display = obl.get_status_display()
            status_counts[status_display] = status_counts.get(status_display, 0) + 1

        chart_data = [(status, count) for status, count in status_counts.items()]
        chart = create_chart('pie', chart_data,
                           'Obligation Status Distribution',
                           '', '',
                           colors_list=['#28a745', '#ffc107', '#17a2b8', '#dc3545'])
        elements.append(chart)
        elements.append(Spacer(1, 0.2*inch))

        # Status Summary
        pending = obligations.filter(status='pending').count()
        in_progress = obligations.filter(status='in_progress').count()
        completed = obligations.filter(status='completed').count()
        overdue = obligations.filter(status='overdue').count()

        elements.append(create_normal_paragraph(
            f"<b>Total Obligations:</b> {obligations.count()} | "
            f"<b>Pending:</b> {pending} | "
            f"<b>In Progress:</b> {in_progress} | "
            f"<b>Completed:</b> {completed} | "
            f"<font color='#dc3545'><b>Overdue:</b> {overdue}</font>"
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Alert for overdue
        if overdue > 0:
            elements.append(create_normal_paragraph(
                f"<font color='#dc3545'><b>⚠ ALERT:</b> {overdue} overdue obligation(s) require immediate attention!</font>"
            ))
            elements.append(Spacer(1, 0.2*inch))

    # Chart 2: LegalTemplate Status Distribution
    if templates.exists():
        elements.append(create_subsection_header('Template-Based Obligations'))

        template_status_counts = {}
        for tmpl in templates:
            status_display = tmpl.get_status_display()
            template_status_counts[status_display] = template_status_counts.get(status_display, 0) + 1

        if template_status_counts:
            chart_data = [(status, count) for status, count in template_status_counts.items()]
            chart = create_chart('pie', chart_data,
                               'Template Obligation Status',
                               '', '',
                               colors_list=['#28a745', '#ffc107', '#dc3545'])
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))

            # Template Summary
            pending_templates = templates.filter(status='pending').count()
            completed_templates = templates.filter(status='completed').count()
            overdue_templates = templates.filter(status='overdue').count()

            elements.append(create_normal_paragraph(
                f"<b>Total Templates:</b> {templates.count()} | "
                f"<b>Pending:</b> {pending_templates} | "
                f"<b>Completed:</b> {completed_templates} | "
                f"<font color='#dc3545'><b>Overdue:</b> {overdue_templates}</font>"
            ))
            elements.append(Spacer(1, 0.3*inch))

    # Chart 3: Obligation Types Distribution (from LegalObligation)
    if obligations.exists():
        elements.append(create_subsection_header('Obligations by Type'))

        type_counts = {}
        for obl in obligations:
            type_display = obl.get_obligation_type_display()
            type_counts[type_display] = type_counts.get(type_display, 0) + 1

        if type_counts:
            # Get top 5 types
            top_types = sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            chart = create_chart('bar', top_types,
                               'Top Obligation Types',
                               'Type', 'Count',
                               colors_list=['#17a2b8'])
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))

    # Completion History Summary (from LegalObligationCompletion)
    recent_completions = LegalObligationCompletion.objects.filter(
        template__building=building,
        completion_date__gte=start_date,
        completion_date__lte=end_date
    ).order_by('-completion_date')[:10]

    if recent_completions.exists():
        elements.append(create_subsection_header('Recent Completions (Report Period)'))
        elements.append(create_normal_paragraph(
            f"<b>{recent_completions.count()}</b> obligation(s) completed during the report period."
        ))
        elements.append(Spacer(1, 0.1*inch))

    return elements


def generate_unit_overview(building):
    """
    Unit Overview - Key metrics with min/max limits
    """
    from building_mgmt.models import Unit
    from financials.models import MarketValueSetting

    elements = []

    # Section Header
    from reportlab.lib.units import inch
    elements.append(PageBreak())
    elements.append(create_section_header('4. Unit Overview & Market Position', '#6610f2'))
    elements.append(Spacer(1, 0.2*inch))

    units = Unit.objects.filter(building=building).order_by('number')

    if units.exists():
        total_units = units.count()
        total_area = float(units.aggregate(Sum('area'))['area__sum'] or 0)
        avg_area = total_area / total_units if total_units > 0 else 0

        # Summary info
        elements.append(create_subsection_header('Building Summary'))
        elements.append(create_normal_paragraph(
            f"<b>Total Units:</b> {total_units} | "
            f"<b>Total Area:</b> {total_area:,.2f} m² | "
            f"<b>Average Unit Size:</b> {avg_area:.2f} m²"
        ))
        elements.append(Spacer(1, 0.3*inch))

        # Chart: Units by Floor
        floor_counts = {}
        for unit in units:
            floor_counts[str(unit.floor)] = floor_counts.get(str(unit.floor), 0) + 1

        if floor_counts:
            chart_data = sorted(floor_counts.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
            chart = create_chart('bar', chart_data,
                               'Unit Distribution by Floor',
                               'Floor', 'Number of Units',
                               colors_list=['#6610f2'])
            elements.append(chart)
            elements.append(Spacer(1, 0.3*inch))

        # Market comparison (if available)
        try:
            market_settings = MarketValueSetting.objects.get(building=building)
            elements.append(create_subsection_header('Market Value Reference Ranges'))
            elements.append(create_normal_paragraph(
                f"<b>Sale Price Range:</b> R$ {market_settings.sale_min:.2f} - R$ {market_settings.sale_max:.2f} per m²<br/>"
                f"<b>Rental Price Range:</b> R$ {market_settings.rental_min:.2f} - R$ {market_settings.rental_max:.2f} per m²<br/>"
                f"<b>Condo Fee Range:</b> R$ {market_settings.condominium_min:.2f} - R$ {market_settings.condominium_max:.2f} per m²"
            ))
        except MarketValueSetting.DoesNotExist:
            pass

    return elements


def generate_service_requests_visual(building, start_date, end_date):
    """
    Visual Service Requests - Consolidated format
    Includes: FieldRequest and FieldMgmtTechnical data
    """
    from field_mgmt.models import FieldRequest, FieldMgmtTechnical, FieldMgmtTechnicalImage

    elements = []

    # Section Header
    elements.append(PageBreak())
    elements.append(create_section_header('5. Service Requests Status', '#e83e8c'))
    elements.append(Spacer(1, 0.2*inch))

    # Query FieldRequest (building-specific requests)
    field_requests = FieldRequest.objects.filter(building=building).order_by('-created_at')

    # Query FieldMgmtTechnical (all technical requests - no building filter since it doesn't have building field)
    technical_requests = FieldMgmtTechnical.objects.all().order_by('-created_at')

    # Apply date filter
    field_requests_period = field_requests.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )

    technical_requests_period = technical_requests.filter(
        created_at__gte=start_date,
        created_at__lte=end_date
    )

    total_requests = field_requests.count()
    total_technical = technical_requests.count()
    total_period = field_requests_period.count() + technical_requests_period.count()

    if total_requests == 0 and total_technical == 0:
        elements.append(create_normal_paragraph(
            "No service requests found."
        ))
        return elements

    # Summary Info
    elements.append(create_subsection_header('Service Requests Overview'))
    elements.append(create_normal_paragraph(
        f"<b>Total Field Requests:</b> {total_requests} | "
        f"<b>Total Technical Requests:</b> {total_technical} | "
        f"<b>Requests in Report Period:</b> {total_period}"
    ))
    elements.append(Spacer(1, 0.3*inch))

    # Chart 1: Field Requests Timeline (all time)
    if field_requests.exists():
        elements.append(create_subsection_header('Field Requests by Caretaker'))

        # Group by caretaker
        caretaker_counts = {}
        for req in field_requests[:50]:  # Limit to 50 most recent
            caretaker = req.caretaker if req.caretaker else 'Unassigned'
            caretaker_counts[caretaker] = caretaker_counts.get(caretaker, 0) + 1

        if caretaker_counts:
            # Get top 5 caretakers
            top_caretakers = sorted(caretaker_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            chart = create_chart('bar', top_caretakers,
                               'Top 5 Caretakers by Request Count',
                               'Caretaker', 'Number of Requests',
                               colors_list=['#e83e8c'])
            elements.append(chart)
            elements.append(Spacer(1, 0.3*inch))

    # Chart 2: Technical Requests by Priority
    if technical_requests.exists():
        elements.append(create_subsection_header('Technical Requests by Priority'))

        priority_counts = {}
        for req in technical_requests:
            priority_display = req.get_priority_display()
            priority_counts[priority_display] = priority_counts.get(priority_display, 0) + 1

        if priority_counts:
            chart_data = [(priority, count) for priority, count in priority_counts.items()]
            chart = create_chart('pie', chart_data,
                               'Technical Request Priority Distribution',
                               '', '',
                               colors_list=['#28a745', '#ffc107', '#ff851b', '#dc3545'])
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))

            # Priority breakdown
            urgent = technical_requests.filter(priority='urgent').count()
            high = technical_requests.filter(priority='high').count()
            medium = technical_requests.filter(priority='medium').count()
            low = technical_requests.filter(priority='low').count()

            elements.append(create_normal_paragraph(
                f"<font color='#dc3545'><b>Urgent:</b> {urgent}</font> | "
                f"<font color='#ff851b'><b>High:</b> {high}</font> | "
                f"<b>Medium:</b> {medium} | "
                f"<b>Low:</b> {low}"
            ))
            elements.append(Spacer(1, 0.3*inch))

    # Chart 3: Requests Over Time (monthly breakdown in report period)
    if total_period > 0:
        elements.append(create_subsection_header('Request Volume in Report Period'))

        from collections import defaultdict
        monthly_counts = defaultdict(int)

        # Count field requests by month
        for req in field_requests_period:
            month_key = req.created_at.strftime('%Y-%m')
            monthly_counts[month_key] += 1

        # Count technical requests by month
        for req in technical_requests_period:
            month_key = req.created_at.strftime('%Y-%m')
            monthly_counts[month_key] += 1

        if monthly_counts:
            sorted_months = sorted(monthly_counts.items())
            chart = create_chart('line', sorted_months,
                               'Request Volume by Month',
                               'Month', 'Number of Requests',
                               colors_list=['#e83e8c'])
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))

    # Additional Statistics
    if field_requests.exists():
        # Count items across all field requests
        total_items = sum(len(req.items) if req.items else 0 for req in field_requests)

        elements.append(create_subsection_header('Field Request Details'))
        elements.append(create_normal_paragraph(
            f"<b>Total Items Requested:</b> {total_items} items across {field_requests.count()} requests"
        ))
        elements.append(Spacer(1, 0.2*inch))

    # Technical Request Images
    if technical_requests.exists():
        total_images = FieldMgmtTechnicalImage.objects.filter(
            technical_request__in=technical_requests
        ).count()

        if total_images > 0:
            elements.append(create_subsection_header('Technical Request Documentation'))
            elements.append(create_normal_paragraph(
                f"<b>Total Images Attached:</b> {total_images} images for documentation and reference"
            ))

    return elements


def generate_calendar_visual(building, start_date, end_date):
    """
    Visual Calendar - Meetings and commitments
    """
    elements = []

    # Section Header
    from reportlab.lib.units import inch
    elements.append(PageBreak())
    elements.append(create_section_header('6. Meetings & Scheduled Commitments', '#28a745'))
    elements.append(Spacer(1, 0.2*inch))

    # This would integrate with a calendar/meeting model if available
    # For now, showing placeholder
    elements.append(create_normal_paragraph(
        "Calendar integration displays upcoming and past meetings, scheduled inspections, "
        "and important deadlines in a consolidated timeline view."
    ))

    return elements
