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
    VISUAL Financial Section - CHARTS ONLY
    1. Overall financial performance chart
    2. Individual account performance charts
    3. Condominium fee vs market comparison chart
    """
    from financials.models import (
        FinancialMainAccount, FinancialAccountTransaction,
        MarketValueSetting
    )
    from building_mgmt.models import Unit
    from datetime import datetime
    from decimal import Decimal

    elements = []

    # Section Header
    from reportlab.lib.units import inch
    elements.append(PageBreak())
    elements.append(create_section_header('1. Financial Performance Analysis', '#ffc107'))
    elements.append(Spacer(1, 0.2*inch))

    # Get financial data
    accounts = FinancialMainAccount.objects.filter(building=building).order_by('code')

    start_month = start_date.strftime('%Y-%m')
    end_month = end_date.strftime('%Y-%m')

    transactions = FinancialAccountTransaction.objects.filter(
        building=building,
        reference_month__gte=start_month,
        reference_month__lte=end_month
    ).select_related('account')

    # Chart 1: Overall Financial Performance (Budget vs Actual)
    if accounts.exists() and transactions.exists():
        total_budget = float(accounts.aggregate(Sum('expected_amount'))['expected_amount__sum'] or 0)
        total_actual = float(transactions.aggregate(Sum('amount'))['amount__sum'] or 0)

        if total_budget > 0 or total_actual > 0:
            elements.append(create_subsection_header('Overall Financial Performance'))
            chart_data = [
                ('Budgeted', total_budget),
                ('Actual Spent', total_actual)
            ]
            chart = create_chart('bar', chart_data,
                               'Budget vs Actual Expenses',
                               'Category', 'Amount (R$)',
                               colors_list=['#28a745', '#dc3545'])
            elements.append(chart)
            elements.append(Spacer(1, 0.3*inch))

            # Variance info
            variance = total_actual - total_budget
            variance_pct = (variance / total_budget * 100) if total_budget > 0 else 0

            status_text = "WITHIN BUDGET" if variance <= 0 else "OVER BUDGET"
            status_color = '#28a745' if variance <= 0 else '#dc3545'

            elements.append(create_normal_paragraph(
                f"<b>Budget Status:</b> <font color='{status_color}'>{status_text}</font> | "
                f"<b>Variance:</b> R$ {abs(variance):,.2f} ({abs(variance_pct):.1f}%)"
            ))
            elements.append(Spacer(1, 0.4*inch))

    # Chart 2: Top 5 Accounts by Spending
    if transactions.exists():
        from collections import defaultdict
        account_totals = defaultdict(float)

        for trans in transactions:
            account_totals[trans.account.name] += float(trans.amount)

        # Get top 5
        top_accounts = sorted(account_totals.items(), key=lambda x: x[1], reverse=True)[:5]

        if top_accounts:
            elements.append(create_subsection_header('Top 5 Expense Categories'))
            chart = create_chart('pie', top_accounts,
                               'Expense Distribution by Account',
                               '', '',
                               colors_list=['#17a2b8', '#28a745', '#ffc107', '#dc3545', '#6610f2'])
            elements.append(chart)
            elements.append(Spacer(1, 0.3*inch))

    # Chart 3: Condominium Fee vs Market Comparison
    units = Unit.objects.filter(building=building)
    if units.exists() and accounts.exists():
        try:
            market_settings = MarketValueSetting.objects.get(building=building)

            # Calculate average condo fee per m²
            ordinary_budget = float(accounts.filter(balance_type='ordinary').aggregate(
                Sum('expected_amount'))['expected_amount__sum'] or 0)
            total_area = float(units.aggregate(Sum('area'))['area__sum'] or 0)

            if total_area > 0:
                avg_fee_per_sqm = ordinary_budget / total_area
                market_min = float(market_settings.condominium_min)
                market_max = float(market_settings.condominium_max)
                market_avg = (market_min + market_max) / 2

                elements.append(PageBreak())
                elements.append(create_subsection_header('Condominium Fee - Market Comparison'))

                chart_data = [
                    ('Building Fee', avg_fee_per_sqm),
                    ('Market Min', market_min),
                    ('Market Average', market_avg),
                    ('Market Max', market_max)
                ]

                chart = create_chart('bar', chart_data,
                                   'Condominium Fee vs Market (R$/m²)',
                                   'Category', 'R$ per m²',
                                   colors_list=['#17a2b8', '#ffc107', '#28a745', '#dc3545'])
                elements.append(chart)
                elements.append(Spacer(1, 0.2*inch))

                # Market position analysis
                if avg_fee_per_sqm < market_min:
                    status = "BELOW MARKET RANGE"
                    color = '#28a745'
                elif avg_fee_per_sqm > market_max:
                    status = "ABOVE MARKET RANGE"
                    color = '#dc3545'
                else:
                    status = "WITHIN MARKET RANGE"
                    color = '#28a745'

                elements.append(create_normal_paragraph(
                    f"<b>Market Position:</b> <font color='{color}'>{status}</font> | "
                    f"<b>Building Fee:</b> R$ {avg_fee_per_sqm:.2f}/m² | "
                    f"<b>Market Range:</b> R$ {market_min:.2f} - R$ {market_max:.2f}/m²"
                ))
        except MarketValueSetting.DoesNotExist:
            pass

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
