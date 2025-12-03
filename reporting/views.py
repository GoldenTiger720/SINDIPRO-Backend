from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image, KeepTogether
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor

from building_mgmt.models import Building, Unit
from equipment_mgmt.models import Equipment, MaintenanceRecord
from financials.models import Expense, Revenue, FinancialMainAccount, ExpenseEntry, RevenueAccount, AccountBalance
from consumptions.models import ConsumptionReading, ConsumptionRegister, ConsumptionAccount
from legal_docs.models import LegalObligation, LegalTemplate, LegalObligationCompletion
from field_mgmt.models import FieldRequest, FieldMgmtTechnical


class NumberedCanvas(canvas.Canvas):
    """Canvas for adding page numbers and header/footer"""
    def __init__(self, *args, **kwargs):
        canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.grey)
        self.drawRightString(
            letter[0] - 0.75 * inch,
            0.5 * inch,
            f"Page {self._pageNumber} of {page_count}"
        )


def create_chart(chart_type, data, title, xlabel, ylabel, figsize=(6, 4), colors_list=None):
    """Create matplotlib charts and return as Image"""
    # Lazy import matplotlib to avoid loading on module import
    import matplotlib
    matplotlib.use('Agg')  # Use non-GUI backend

    # Prevent font fallback and use DejaVu Sans (default font present on server)
    matplotlib.rcParams['font.family'] = 'DejaVu Sans'
    matplotlib.rcParams['axes.unicode_minus'] = False
    # Optimize for speed
    matplotlib.rcParams['figure.max_open_warning'] = 0

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=figsize, dpi=100)  # Lower DPI for faster generation

    if chart_type == 'bar':
        x_labels = [str(item[0])[:15] for item in data]  # Truncate long labels
        y_values = [float(item[1]) for item in data]
        bars = ax.bar(x_labels, y_values, color=colors_list or ['#17a2b8', '#28a745', '#ffc107', '#dc3545'])
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        plt.xticks(rotation=45, ha='right')

    elif chart_type == 'line':
        x_values = [str(item[0]) for item in data]
        y_values = [float(item[1]) for item in data]
        ax.plot(range(len(x_values)), y_values, marker='o', linewidth=2, markersize=6, color='#17a2b8')
        ax.set_xticks(range(len(x_values)))
        ax.set_xticklabels(x_values, rotation=45, ha='right')
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)

    elif chart_type == 'pie':
        labels = [str(item[0])[:20] for item in data]  # Truncate long labels
        values = [float(item[1]) for item in data]
        colors_pie = colors_list or ['#17a2b8', '#28a745', '#ffc107', '#dc3545', '#6610f2', '#e83e8c']
        ax.pie(values, labels=labels, autopct='%1.1f%%', colors=colors_pie, startangle=90)
        ax.axis('equal')

    ax.set_title(title, fontsize=12, fontweight='bold', pad=15)
    plt.tight_layout()

    # Save to BytesIO with optimized DPI for faster generation
    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
    img_buffer.seek(0)

    # Mandatory graph clearing to prevent memory leaks
    plt.close(fig)

    return Image(img_buffer, width=4.5*inch, height=3*inch)


def create_section_header(text, color='#17a2b8'):
    """Create a styled section header"""
    header_style = ParagraphStyle(
        'SectionHeader',
        parent=getSampleStyleSheet()['Heading1'],
        fontSize=16,
        textColor=HexColor(color),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold',
        leftIndent=0,
        borderPadding=8,
        borderColor=HexColor(color),
        borderWidth=0,
        borderRadius=0,
    )
    return Paragraph(text, header_style)


def create_subsection_header(text):
    """Create a styled subsection header"""
    style = ParagraphStyle(
        'SubsectionHeader',
        parent=getSampleStyleSheet()['Heading2'],
        fontSize=13,
        textColor=HexColor('#2c3e50'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold',
    )
    return Paragraph(text, style)


def create_normal_paragraph(text, alignment=TA_JUSTIFY):
    """Create a styled normal paragraph"""
    style = ParagraphStyle(
        'NormalText',
        parent=getSampleStyleSheet()['Normal'],
        fontSize=10,
        textColor=HexColor('#2c3e50'),
        spaceAfter=8,
        spaceBefore=4,
        alignment=alignment,
        leading=14,
    )
    return Paragraph(text, style)


def create_info_table(data, col_widths=None):
    """Create a styled information table"""
    table = Table(data, colWidths=col_widths or [2.5*inch, 4*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), HexColor('#f8f9fa')),
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    return table


def create_data_table(data, has_header=True):
    """Create a styled data table with header"""
    table = Table(data)
    style_commands = [
        ('TEXTCOLOR', (0, 0), (-1, -1), HexColor('#2c3e50')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#dee2e6')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]

    if has_header:
        style_commands.extend([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#17a2b8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
        ])

    table.setStyle(TableStyle(style_commands))
    return table


def generate_building_section(building, start_date, end_date):
    """Generate comprehensive building information section with all details"""
    from building_mgmt.models import Tower, TowerUnitDistribution

    elements = []
    elements.append(create_section_header('Building Information', '#17a2b8'))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(create_normal_paragraph(
        f"Complete building information for {building.building_name}, including basic details, "
        f"tower information, and comprehensive unit listings with all relevant data."
    ))
    elements.append(Spacer(1, 0.15*inch))

    # Basic building info
    info_data = [
        ['Building Name:', building.building_name],
        ['CNPJ:', building.cnpj],
        ['Building Type:', building.get_building_type_display()],
        ['Manager:', building.manager_name],
        ['Manager Phone:', building.manager_phone],
        ['Manager Phone Type:', building.get_manager_phone_type_display()],
    ]

    if building.address:
        info_data.extend([
            ['Street:', building.address.street],
            ['Number:', building.address.number],
            ['Neighborhood:', building.address.neighborhood],
            ['City:', building.address.city],
            ['State:', building.address.state],
            ['CEP:', building.address.cep],
        ])

    if building.use_separate_address and building.alternative_address:
        info_data.append(['Alternative Address:', 'Yes'])
        info_data.extend([
            ['Alt. Street:', building.alternative_address.street],
            ['Alt. Number:', building.alternative_address.number],
            ['Alt. Neighborhood:', building.alternative_address.neighborhood],
            ['Alt. City:', building.alternative_address.city],
            ['Alt. State:', building.alternative_address.state],
        ])

    info_data.append(['Number of Towers:', str(building.number_of_towers)])

    if building.apartments_per_tower:
        info_data.append(['Apartments per Tower:', str(building.apartments_per_tower)])
    if building.residential_units:
        info_data.append(['Residential Units:', str(building.residential_units)])
    if building.commercial_units:
        info_data.append(['Commercial Units:', str(building.commercial_units)])
    if building.non_residential_units:
        info_data.append(['Non-Residential Units:', str(building.non_residential_units)])
    if building.studio_units:
        info_data.append(['Studio Units:', str(building.studio_units)])
    if building.wave_units:
        info_data.append(['Wave Units:', str(building.wave_units)])

    elements.append(create_info_table(info_data))
    elements.append(Spacer(1, 0.3*inch))

    # Tower Information
    towers = Tower.objects.filter(building=building).prefetch_related('unit_distribution')
    if towers.exists():
        elements.append(create_subsection_header('Tower Information'))

        tower_data = [['Tower Name', 'Units per Tower', 'Residential', 'Commercial', 'Non-Residential', 'Studio', 'Wave']]
        for tower in towers:
            dist = getattr(tower, 'unit_distribution', None)
            tower_data.append([
                tower.name,
                str(tower.units_per_tower),
                str(dist.residential if dist else 0),
                str(dist.commercial if dist else 0),
                str(dist.non_residential if dist else 0),
                str(dist.studio if dist else 0),
                str(dist.wave if dist else 0),
            ])

        elements.append(create_data_table(tower_data))
        elements.append(Spacer(1, 0.3*inch))

    # Unit statistics
    elements.append(create_subsection_header('Unit Statistics Summary'))
    units = Unit.objects.filter(building=building).select_related('tower')
    total_units = units.count()
    occupied_units = units.filter(status='occupied').count()
    vacant_units = units.filter(status='vacant').count()
    total_area = units.aggregate(Sum('area'))['area__sum'] or 0
    total_parking = units.aggregate(Sum('parking_spaces'))['parking_spaces__sum'] or 0

    stats_data = [
        ['Total Units:', str(total_units)],
        ['Occupied Units:', f"{occupied_units} ({(occupied_units/total_units*100) if total_units > 0 else 0:.1f}%)"],
        ['Vacant Units:', f"{vacant_units} ({(vacant_units/total_units*100) if total_units > 0 else 0:.1f}%)"],
        ['Total Area:', f"{total_area:.2f} m\u00b2"],
        ['Total Parking Spaces:', str(total_parking)],
        ['Average Unit Area:', f"{(total_area/total_units) if total_units > 0 else 0:.2f} m\u00b2"],
    ]
    elements.append(create_info_table(stats_data))
    elements.append(Spacer(1, 0.2*inch))

    # Unit occupancy chart
    if total_units > 0:
        chart_data = [
            ('Occupied', occupied_units),
            ('Vacant', vacant_units),
        ]
        chart = create_chart('pie', chart_data, 'Unit Occupancy Distribution', '', '', colors_list=['#28a745', '#ffc107'])
        elements.append(chart)
        elements.append(Spacer(1, 0.3*inch))

    # Complete Unit Listing
    if units.exists():
        elements.append(PageBreak())
        elements.append(create_subsection_header('Complete Unit Listing'))
        elements.append(create_normal_paragraph(
            f"Detailed listing of all {total_units} units in {building.building_name} with complete information."
        ))
        elements.append(Spacer(1, 0.15*inch))

        # Create unit table with all fields
        unit_data = [['Unit#', 'Tower', 'Floor', 'Area (m²)', 'Ideal Fraction', 'Type', 'Status', 'Owner', 'Phone', 'Parking']]

        for unit in units.order_by('tower__name', 'floor', 'number'):
            unit_data.append([
                str(unit.number),
                unit.tower.name if unit.tower else 'N/A',
                str(unit.floor),
                f"{unit.area:.2f}",
                f"{unit.ideal_fraction:.6f}",
                unit.identification[:10],
                unit.status.capitalize(),
                unit.owner[:20] if unit.owner else 'N/A',
                unit.owner_phone[:15] if unit.owner_phone else 'N/A',
                str(unit.parking_spaces),
            ])

        # Create table with appropriate column widths
        elements.append(create_data_table(unit_data))
        elements.append(Spacer(1, 0.2*inch))

        # Additional unit details in a second table if needed
        elements.append(create_subsection_header('Unit Additional Details'))
        unit_details_data = [['Unit#', 'Deposit Location', 'Key Delivery', 'Created Date']]

        for unit in units.order_by('tower__name', 'floor', 'number'):
            unit_details_data.append([
                str(unit.number),
                unit.deposit_location[:30] if unit.deposit_location else 'N/A',
                unit.key_delivery if unit.key_delivery else 'N/A',
                unit.created_at.strftime('%Y-%m-%d') if unit.created_at else 'N/A',
            ])

        elements.append(create_data_table(unit_details_data))

    return elements


def generate_equipment_section(building, start_date, end_date):
    """Generate comprehensive equipment section with complete details"""
    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Equipment Management', '#28a745'))
    elements.append(Spacer(1, 0.15*inch))

    equipment_list = Equipment.objects.filter(building_id=str(building.id)).order_by('name')
    total_equipment = equipment_list.count()

    elements.append(create_normal_paragraph(
        f"This section provides a comprehensive overview of all equipment registered for {building.building_name}. "
        f"Total equipment count: <b>{total_equipment}</b>."
    ))
    elements.append(Spacer(1, 0.15*inch))

    if total_equipment == 0:
        elements.append(create_normal_paragraph("No equipment registered for this building during the selected period."))
        return elements

    # Complete Equipment Listing Table
    elements.append(create_subsection_header('Complete Equipment Listing'))
    equipment_data = [['Name', 'Type', 'Location', 'Purchase Date', 'Status', 'Maintenance', 'Company', 'Contact']]

    for eq in equipment_list:
        equipment_data.append([
            str(eq.name)[:25],
            str(eq.type)[:15],
            str(eq.location)[:20],
            eq.purchase_date.strftime('%Y-%m-%d'),
            eq.get_status_display()[:15],
            eq.get_maintenance_frequency_display()[:12],
            str(eq.company_name)[:20] if eq.company_name else 'N/A',
            str(eq.contact_person_name)[:18] if eq.contact_person_name else 'N/A',
        ])

    # Create equipment table with adjusted column widths
    equipment_table = Table(equipment_data, colWidths=[1.2*inch, 0.9*inch, 1.0*inch, 0.9*inch, 0.9*inch, 0.8*inch, 1.1*inch, 1.0*inch])
    equipment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(equipment_table)
    elements.append(Spacer(1, 0.2*inch))

    # Additional Equipment Details Table (Company Phone)
    elements.append(create_subsection_header('Equipment Company Contact Details'))
    contact_data = [['Equipment Name', 'Company Name', 'Company Phone', 'Contact Person']]

    for eq in equipment_list:
        contact_data.append([
            str(eq.name)[:30],
            str(eq.company_name)[:25] if eq.company_name else 'N/A',
            str(eq.company_phone)[:20] if eq.company_phone else 'N/A',
            str(eq.contact_person_name)[:25] if eq.contact_person_name else 'N/A',
        ])

    contact_table = Table(contact_data, colWidths=[2.0*inch, 2.0*inch, 1.5*inch, 2.0*inch])
    contact_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(contact_table)
    elements.append(Spacer(1, 0.2*inch))

    # Equipment by status
    status_counts = {}
    for eq in equipment_list:
        status_counts[eq.get_status_display()] = status_counts.get(eq.get_status_display(), 0) + 1

    elements.append(create_subsection_header('Equipment Status Overview'))
    status_data = [['Status', 'Count', 'Percentage']]
    for status, count in status_counts.items():
        percentage = (count / total_equipment * 100) if total_equipment > 0 else 0
        status_data.append([status, str(count), f"{percentage:.1f}%"])
    elements.append(create_data_table(status_data))
    elements.append(Spacer(1, 0.2*inch))

    # Status chart
    chart_data = [(status, count) for status, count in status_counts.items()]
    chart = create_chart('bar', chart_data, 'Equipment by Status', 'Status', 'Count')
    elements.append(chart)
    elements.append(Spacer(1, 0.2*inch))

    # Maintenance records in date range
    maintenance_records = MaintenanceRecord.objects.filter(
        equipment__in=equipment_list,
        date__range=[start_date, end_date]
    ).order_by('-date')

    maintenance_count = maintenance_records.count()
    total_maintenance_cost = maintenance_records.aggregate(Sum('cost'))['cost__sum'] or 0

    elements.append(create_subsection_header('Maintenance Activity'))
    maintenance_summary = [
        ['Total Maintenance Records:', str(maintenance_count)],
        ['Total Maintenance Cost:', f"R$ {total_maintenance_cost:,.2f}"],
    ]

    if maintenance_count > 0:
        avg_cost = maintenance_records.aggregate(Avg('cost'))['cost__avg'] or 0
        maintenance_summary.append(['Average Maintenance Cost:', f"R$ {avg_cost:,.2f}"])

    elements.append(create_info_table(maintenance_summary))
    elements.append(Spacer(1, 0.2*inch))

    # Detailed Maintenance Records Table
    if maintenance_count > 0:
        elements.append(create_subsection_header('Maintenance Records Detail'))
        maint_data = [['Date', 'Equipment', 'Type', 'Cost', 'Technician', 'Phone']]

        for record in maintenance_records[:20]:  # Limit to 20 most recent
            maint_data.append([
                record.date.strftime('%Y-%m-%d'),
                str(record.equipment.name)[:20],
                str(record.type)[:18],
                f"R$ {record.cost:,.2f}",
                str(record.technician)[:18],
                str(record.technician_phone)[:15] if record.technician_phone else 'N/A',
            ])

        maint_table = Table(maint_data, colWidths=[0.9*inch, 1.5*inch, 1.3*inch, 1.0*inch, 1.3*inch, 1.2*inch])
        maint_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(maint_table)
        elements.append(Spacer(1, 0.2*inch))

        if maintenance_count > 20:
            elements.append(create_normal_paragraph(f"Note: Showing 20 most recent maintenance records out of {maintenance_count} total records."))
            elements.append(Spacer(1, 0.2*inch))

    # Maintenance by equipment type
    if maintenance_count > 0:
        type_costs = {}
        for record in maintenance_records:
            eq_type = record.equipment.type
            type_costs[eq_type] = type_costs.get(eq_type, 0) + float(record.cost)

        if type_costs:
            chart_data = [(eq_type, cost) for eq_type, cost in sorted(type_costs.items(), key=lambda x: x[1], reverse=True)[:8]]
            chart = create_chart('bar', chart_data, 'Maintenance Costs by Equipment Type', 'Equipment Type', 'Cost (R$)')
            elements.append(chart)

    return elements


def generate_financial_section(building, start_date, end_date):
    """
    Generate COMPREHENSIVE financial section covering ALL 7 tabs from frontend:
    Tab 1: Account Management (Chart of Accounts)
    Tab 2: Account Balances (Monthly Balance History)
    Tab 3: Expense Tracking (Monthly Expense Execution)
    Tab 4: Financial Reports (General & By Account Reports)
    Tab 5: Budget Management (Monthly Evolution)
    Tab 6: Fee Calculator (Unit Fee Distribution)
    Tab 7: Market Values (Market Analysis & Comparison)
    """
    from financials.models import (
        FinancialMainAccount, FinancialAccountTransaction, AccountBalance,
        ExpenseEntry, RevenueAccount, AdditionalCharge, MarketValueSetting
    )
    from building_mgmt.models import Unit
    from dateutil.relativedelta import relativedelta
    from collections import defaultdict
    from datetime import datetime
    from decimal import Decimal

    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Financial Management - Complete Analysis', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(create_normal_paragraph(
        f"Comprehensive financial analysis for {building.building_name} covering all aspects of financial management "
        f"including account structure, balances, expense tracking, budgets, fee calculations, and market comparisons."
    ))
    elements.append(Spacer(1, 0.2*inch))

    ###########################################
    # TAB 1: ACCOUNT MANAGEMENT - CHART OF ACCOUNTS
    ###########################################
    elements.append(create_section_header('Tab 1: Account Management - Chart of Accounts', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # Get all accounts for this building
    accounts = FinancialMainAccount.objects.filter(building=building).order_by('code')
    total_accounts = accounts.count()

    # Calculate totals
    total_monthly_expected = accounts.aggregate(Sum('expected_amount'))['expected_amount__sum'] or 0

    summary_data = [
        ['Total Accounts:', str(total_accounts)],
        ['Total Monthly Budget:', f"R$ {total_monthly_expected:,.2f}"],
    ]
    elements.append(create_info_table(summary_data))
    elements.append(Spacer(1, 0.2*inch))

    if accounts.exists():
        elements.append(create_subsection_header('Complete Chart of Accounts'))

        # Create hierarchical account table
        account_data = [['Code', 'Account Name', 'Type', 'Balance Type', 'Monthly Amount', 'Assembly Period', 'Fiscal Year']]

        for account in accounts:
            # Calculate months in assembly period
            if account.assembly_start_date and account.assembly_end_date:
                months_diff = ((account.assembly_end_date.year - account.assembly_start_date.year) * 12 +
                             (account.assembly_end_date.month - account.assembly_start_date.month) + 1)
                period_text = f"{account.assembly_start_date.strftime('%Y-%m')} to {account.assembly_end_date.strftime('%Y-%m')} ({months_diff}m)"
            else:
                period_text = 'N/A'

            account_data.append([
                str(account.code)[:15],
                str(account.name)[:35],
                account.get_type_display()[:8],
                account.get_balance_type_display()[:15],
                f"R$ {account.expected_amount:,.2f}",
                period_text[:22],
                str(account.fiscal_year) if account.fiscal_year else 'N/A',
            ])

        account_table = Table(account_data, colWidths=[1.0*inch, 2.2*inch, 0.7*inch, 1.1*inch, 1.1*inch, 1.5*inch, 0.7*inch])
        account_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(account_table)
        elements.append(Spacer(1, 0.2*inch))

        # Accounts by type distribution
        type_counts = {}
        for account in accounts:
            acc_type = account.get_type_display()
            type_counts[acc_type] = type_counts.get(acc_type, 0) + 1

        # Balance type distribution
        balance_counts = {'Ordinary': 0, 'Extraordinary': 0}
        for account in accounts:
            balance_type = account.get_balance_type_display()
            balance_counts[balance_type] = balance_counts.get(balance_type, 0) + 1

        # Display table and chart side by side
        if type_counts:
            elements.append(create_subsection_header('Account Distribution by Type & Balance Type'))

            # Create the type distribution table
            type_data = [['Account Type', 'Count', 'Percentage']]
            for acc_type, count in type_counts.items():
                percentage = (count / total_accounts * 100) if total_accounts > 0 else 0
                type_data.append([acc_type, str(count), f"{percentage:.1f}%"])

            type_table = create_data_table(type_data)

            # Create the balance type pie chart
            chart_data = [(bal_type, count) for bal_type, count in balance_counts.items() if count > 0]
            chart = None
            if chart_data:
                chart = create_chart('pie', chart_data, 'Accounts by Balance Type', '', '',
                                   colors_list=['#28a745', '#dc3545'])

            # Place table and chart side by side using a layout table
            if chart:
                layout_data = [[type_table, chart]]
                layout_table = Table(layout_data, colWidths=[3.5*inch, 3.5*inch])
                layout_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                elements.append(layout_table)
            else:
                elements.append(type_table)

    ###########################################
    # TAB 2: ACCOUNT BALANCES - MONTHLY BALANCE HISTORY
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 2: Account Balances - Monthly Balance History', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # Get all balances in date range - filter using reference_month field
    start_month = start_date.strftime('%Y-%m')
    end_month = end_date.strftime('%Y-%m')

    balances = AccountBalance.objects.filter(
        building=building,
        reference_month__gte=start_month,
        reference_month__lte=end_month
    ).order_by('-reference_month', 'account_name')

    if balances.exists():
        elements.append(create_subsection_header('Monthly Balance Snapshots'))
        elements.append(create_normal_paragraph(
            f"Complete balance history from {start_month} to {end_month}. "
            f"Total balance records: {balances.count()}."
        ))
        elements.append(Spacer(1, 0.15*inch))

        # Balance history table
        balance_data = [['Reference Month', 'Account Name', 'Balance', 'Delinquency', 'Balance Type']]

        for balance in balances[:40]:  # Limit to 40 most recent
            balance_data.append([
                balance.reference_month,
                str(balance.account_name)[:30],
                f"R$ {balance.balance:,.2f}",
                f"R$ {balance.delinquency:,.2f}",
                balance.get_balance_type_display()[:15],
            ])

        balance_table = Table(balance_data, colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        balance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(balance_table)
        elements.append(Spacer(1, 0.2*inch))

        if balances.count() > 40:
            elements.append(create_normal_paragraph(f"Note: Showing 40 most recent balance records out of {balances.count()} total."))
            elements.append(Spacer(1, 0.2*inch))

        # Balance evolution chart - Group by month
        monthly_totals = defaultdict(float)
        for balance in balances:
            monthly_totals[balance.reference_month] += float(balance.balance)

        if len(monthly_totals) > 1:
            sorted_months = sorted(monthly_totals.keys())
            chart_data = [(month, monthly_totals[month]) for month in sorted_months]
            chart = create_chart('line', chart_data, 'Total Balance Evolution Over Time', 'Month', 'Balance (R$)')
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(create_normal_paragraph("No balance records found for the selected period."))
        elements.append(Spacer(1, 0.2*inch))

    ###########################################
    # TAB 3: EXPENSE TRACKING - MONTHLY EXPENSE EXECUTION
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 3: Expense Tracking - Monthly Execution Analysis', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # Get transactions in date range - filter by reference_month
    transactions = FinancialAccountTransaction.objects.filter(
        building=building,
        reference_month__gte=start_month,
        reference_month__lte=end_month
    ).select_related('account').order_by('-reference_month', '-created_at')

    # Calculate expected vs actual by account and month
    account_execution = defaultdict(lambda: {'expected': 0, 'actual': 0, 'transactions': []})

    for account in accounts:
        if account.assembly_start_date and account.assembly_end_date:
            # Only include accounts within their assembly period
            account_start = account.assembly_start_date.strftime('%Y-%m')
            account_end = account.assembly_end_date.strftime('%Y-%m')

            if account_start <= end_month and account_end >= start_month:
                key = f"{account.code} - {account.name}"
                account_execution[key]['expected'] += float(account.expected_amount)
                account_execution[key]['account_type'] = account.get_balance_type_display()

    for trans in transactions:
        if trans.account:
            key = f"{trans.account.code} - {trans.account.name}"
            account_execution[key]['actual'] += float(trans.amount)
            account_execution[key]['transactions'].append(trans)

    if account_execution:
        elements.append(create_subsection_header('Budget Execution Summary'))

        total_expected = sum(data['expected'] for data in account_execution.values())
        total_actual = sum(data['actual'] for data in account_execution.values())
        total_balance = total_expected - total_actual

        exec_summary = [
            ['Total Expected:', f"R$ {total_expected:,.2f}"],
            ['Total Actual:', f"R$ {total_actual:,.2f}"],
            ['Balance:', f"R$ {total_balance:,.2f}"],
            ['Execution Rate:', f"{(total_actual/total_expected*100) if total_expected > 0 else 0:.1f}%"],
        ]
        elements.append(create_info_table(exec_summary))
        elements.append(Spacer(1, 0.2*inch))

        # Detailed execution table by account
        elements.append(create_subsection_header('Detailed Execution by Account'))
        exec_data = [['Account', 'Type', 'Expected', 'Actual', 'Balance', 'Status']]

        for account_key, data in sorted(account_execution.items()):
            expected = data['expected']
            actual = data['actual']
            balance = expected - actual
            over_budget = actual > expected
            status = 'Over Budget!' if over_budget else 'On Track'

            exec_data.append([
                account_key[:35],
                data.get('account_type', 'N/A')[:12],
                f"R$ {expected:,.2f}",
                f"R$ {actual:,.2f}",
                f"R$ {balance:,.2f}",
                status,
            ])

        exec_table = Table(exec_data, colWidths=[2.5*inch, 1.0*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.1*inch])
        exec_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(exec_table)
        elements.append(Spacer(1, 0.2*inch))

    # Transaction detail table
    if transactions.exists():
        elements.append(create_subsection_header('Transaction Details'))
        trans_data = [['Date', 'Reference Month', 'Account', 'Amount', 'Description']]

        for trans in transactions[:50]:  # Limit to 50 most recent
            trans_data.append([
                trans.created_at.strftime('%Y-%m-%d'),
                trans.reference_month,
                f"{trans.account.code} - {trans.account.name}"[:30] if trans.account else 'N/A',
                f"R$ {trans.amount:,.2f}",
                str(trans.description)[:30] if trans.description else 'N/A',
            ])

        trans_table = Table(trans_data, colWidths=[1.0*inch, 1.0*inch, 2.2*inch, 1.2*inch, 2.8*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(trans_table)
        elements.append(Spacer(1, 0.2*inch))

        if transactions.count() > 50:
            elements.append(create_normal_paragraph(f"Note: Showing 50 most recent transactions out of {transactions.count()} total."))
            elements.append(Spacer(1, 0.2*inch))

    ###########################################
    # TAB 4: FINANCIAL REPORTS - GENERAL & BY ACCOUNT
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 4: Financial Reports - Comprehensive Analysis', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # General Report Section
    elements.append(create_subsection_header('General Financial Report'))

    if account_execution:
        # Revenue vs Expenses comparison
        chart_data = [
            ('Expected Budget', total_expected),
            ('Actual Expenses', total_actual),
        ]
        chart = create_chart('bar', chart_data, 'Expected Budget vs Actual Expenses', '', 'Amount (R$)',
                           colors_list=['#28a745', '#dc3545'])
        elements.append(chart)
        elements.append(Spacer(1, 0.2*inch))

        # Spending projection alert
        if total_expected > 0:
            execution_rate = (total_actual / total_expected) * 100
            months_passed = len(set(trans.reference_month for trans in transactions))

            # Estimate total months in period
            start_dt = datetime.strptime(start_month, '%Y-%m')
            end_dt = datetime.strptime(end_month, '%Y-%m')
            total_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month) + 1

            if months_passed > 0 and total_months > months_passed:
                projected_total = (total_actual / months_passed) * total_months
                projected_variance = ((projected_total - total_expected) / total_expected) * 100 if total_expected > 0 else 0

                alert_data = [
                    ['Months Analyzed:', f"{months_passed} of {total_months}"],
                    ['Current Execution Rate:', f"{execution_rate:.1f}%"],
                    ['Projected Annual Total:', f"R$ {projected_total:,.2f}"],
                    ['Projected Variance:', f"{projected_variance:+.1f}%"],
                    ['Alert Status:', 'Warning!' if abs(projected_variance) > 10 else 'On Track'],
                ]
                elements.append(create_info_table(alert_data))
                elements.append(Spacer(1, 0.2*inch))

    # By Account Report Section
    elements.append(Spacer(1, 0.3*inch))
    elements.append(create_subsection_header('Financial Report by Account'))
    elements.append(create_normal_paragraph(
        "Detailed monthly evolution showing expected vs actual amounts for each account."
    ))
    elements.append(Spacer(1, 0.2*inch))

    # Group transactions by account and month
    for account_key, data in sorted(account_execution.items())[:10]:  # Top 10 accounts
        elements.append(Paragraph(f"<b>{account_key}</b>", ParagraphStyle(
            'AccountHeader',
            fontSize=10,
            textColor=colors.HexColor('#ffc107'),
            spaceAfter=6
        )))

        # Monthly breakdown for this account
        monthly_data_acc = defaultdict(lambda: {'expected': 0, 'actual': 0})

        for trans in data['transactions']:
            monthly_data_acc[trans.reference_month]['actual'] += float(trans.amount)

        # Add expected amounts for each month
        expected_monthly = data['expected'] / len(monthly_data_acc) if monthly_data_acc else data['expected']
        for month in monthly_data_acc.keys():
            monthly_data_acc[month]['expected'] = expected_monthly

        if monthly_data_acc:
            sorted_months_acc = sorted(monthly_data_acc.keys())
            month_table = [['Month', 'Expected', 'Actual', 'Variance']]

            for month in sorted_months_acc:
                expected = monthly_data_acc[month]['expected']
                actual = monthly_data_acc[month]['actual']
                variance = actual - expected

                month_table.append([
                    month,
                    f"R$ {expected:,.2f}",
                    f"R$ {actual:,.2f}",
                    f"R$ {variance:+,.2f}",
                ])

            acc_table = Table(month_table, colWidths=[1.5*inch, 1.8*inch, 1.8*inch, 1.8*inch])
            acc_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 1), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            elements.append(acc_table)
            elements.append(Spacer(1, 0.15*inch))

    ###########################################
    # TAB 5: BUDGET MANAGEMENT - MONTHLY EVOLUTION
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 5: Budget Management - Monthly Evolution', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # This section shows monthly expected vs actual evolution
    # Group all data by month
    monthly_evolution = defaultdict(lambda: {'expected': 0, 'actual': 0})

    # Get all months in range
    current_month = start_date.replace(day=1)
    end_month_date = end_date.replace(day=1)
    all_period_months = []

    while current_month <= end_month_date:
        month_key = current_month.strftime('%Y-%m')
        all_period_months.append(month_key)
        current_month += relativedelta(months=1)

    # Calculate expected amounts per month from accounts
    for account in accounts:
        if account.assembly_start_date and account.assembly_end_date:
            account_start = account.assembly_start_date.strftime('%Y-%m')
            account_end = account.assembly_end_date.strftime('%Y-%m')

            for month in all_period_months:
                if account_start <= month <= account_end:
                    monthly_evolution[month]['expected'] += float(account.expected_amount)

    # Calculate actual amounts per month from transactions
    for trans in transactions:
        monthly_evolution[trans.reference_month]['actual'] += float(trans.amount)

    if monthly_evolution:
        elements.append(create_subsection_header('Monthly Budget Evolution Summary'))

        cumulative_expected = 0
        cumulative_actual = 0

        evolution_data = [['Month', 'Expected', 'Actual', 'Variance', 'Cum. Expected', 'Cum. Actual', 'Exec. Rate']]

        for month in sorted(monthly_evolution.keys()):
            expected = monthly_evolution[month]['expected']
            actual = monthly_evolution[month]['actual']
            variance = actual - expected

            cumulative_expected += expected
            cumulative_actual += actual

            exec_rate = (actual / expected * 100) if expected > 0 else 0

            evolution_data.append([
                month,
                f"R$ {expected:,.2f}",
                f"R$ {actual:,.2f}",
                f"R$ {variance:+,.2f}",
                f"R$ {cumulative_expected:,.2f}",
                f"R$ {cumulative_actual:,.2f}",
                f"{exec_rate:.1f}%",
            ])

        evo_table = Table(evolution_data, colWidths=[0.9*inch, 1.2*inch, 1.2*inch, 1.1*inch, 1.2*inch, 1.2*inch, 0.9*inch])
        evo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (6, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(evo_table)
        elements.append(Spacer(1, 0.2*inch))

        # Monthly evolution line chart
        sorted_months_evo = sorted(monthly_evolution.keys())
        if len(sorted_months_evo) > 1:
            # Create two-line chart data (Expected vs Actual)
            chart_data_expected = [(month, monthly_evolution[month]['expected']) for month in sorted_months_evo]
            chart = create_chart('line', chart_data_expected, 'Monthly Expected Budget', 'Month', 'Amount (R$)')
            elements.append(chart)
            elements.append(Spacer(1, 0.15*inch))

            chart_data_actual = [(month, monthly_evolution[month]['actual']) for month in sorted_months_evo]
            chart = create_chart('line', chart_data_actual, 'Monthly Actual Expenses', 'Month', 'Amount (R$)')
            elements.append(chart)
            elements.append(Spacer(1, 0.2*inch))

    ###########################################
    # TAB 6: FEE CALCULATOR - UNIT FEE DISTRIBUTION
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 6: Fee Calculator - Unit Fee Distribution', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # Get all units for this building
    units = Unit.objects.filter(building=building).order_by('number')

    if units.exists() and accounts.exists():
        elements.append(create_subsection_header('Condominium Fee Calculation'))

        # Calculate regular budget (ordinary accounts)
        ordinary_accounts = accounts.filter(balance_type='ordinary')
        total_ordinary_budget = ordinary_accounts.aggregate(Sum('expected_amount'))['expected_amount__sum'] or 0

        # Calculate additional charges (extraordinary accounts)
        extraordinary_accounts = accounts.filter(balance_type='extraordinary')
        total_extraordinary_budget = extraordinary_accounts.aggregate(Sum('expected_amount'))['expected_amount__sum'] or 0

        total_collection = total_ordinary_budget + total_extraordinary_budget

        fee_summary = [
            ['Total Regular Budget (Ordinary):', f"R$ {total_ordinary_budget:,.2f}"],
            ['Total Additional Charges (Extraordinary):', f"R$ {total_extraordinary_budget:,.2f}"],
            ['Total Monthly Collection:', f"R$ {total_collection:,.2f}"],
            ['Total Units:', str(units.count())],
        ]
        elements.append(create_info_table(fee_summary))
        elements.append(Spacer(1, 0.2*inch))

        # Validate ideal fractions sum to 100%
        total_ideal_fraction = float(units.aggregate(Sum('ideal_fraction'))['ideal_fraction__sum'] or 0)
        validation_status = "Valid (100%)" if abs(total_ideal_fraction - 1.0) < 0.0001 else f"Invalid ({total_ideal_fraction*100:.2f}%)"

        elements.append(create_normal_paragraph(
            f"<b>Ideal Fraction Validation:</b> {validation_status}"
        ))
        elements.append(Spacer(1, 0.15*inch))

        # Calculate and display fees per unit
        elements.append(create_subsection_header('Unit Fee Distribution Table'))

        fee_data = [['Unit', 'Owner', 'Area (m²)', 'Ideal Fraction', 'Regular Fee', 'Additional Fee', 'Total Fee', 'Fee per m²']]

        for unit in units:
            # Calculate fees based on ideal fraction
            regular_fee = float(total_ordinary_budget) * float(unit.ideal_fraction)
            additional_fee = float(total_extraordinary_budget) * float(unit.ideal_fraction)
            total_fee = regular_fee + additional_fee

            # Calculate fee per m²
            fee_per_sqm = (total_fee / float(unit.area)) if unit.area > 0 else 0

            fee_data.append([
                str(unit.number)[:10],
                str(unit.owner)[:15] if unit.owner else 'N/A',
                f"{unit.area:.2f}",
                f"{unit.ideal_fraction:.6f}",
                f"R$ {regular_fee:,.2f}",
                f"R$ {additional_fee:,.2f}",
                f"R$ {total_fee:,.2f}",
                f"R$ {fee_per_sqm:,.2f}",
            ])

        fee_table = Table(fee_data, colWidths=[0.7*inch, 1.0*inch, 0.8*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.9*inch])
        fee_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (7, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 6),
            ('FONTSIZE', (0, 1), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(fee_table)
        elements.append(Spacer(1, 0.2*inch))

        # Average fee analysis
        avg_fee = float(total_collection) / units.count() if units.count() > 0 else 0
        total_area = float(units.aggregate(Sum('area'))['area__sum'] or 0)
        avg_fee_per_sqm = float(total_collection) / total_area if total_area > 0 else 0

        avg_data = [
            ['Average Fee per Unit:', f"R$ {avg_fee:,.2f}"],
            ['Total Building Area:', f"{total_area:.2f} m²"],
            ['Average Fee per m²:', f"R$ {avg_fee_per_sqm:,.2f}"],
        ]
        elements.append(create_info_table(avg_data))
        elements.append(Spacer(1, 0.2*inch))
    else:
        elements.append(create_normal_paragraph("Unable to calculate fees: No units or accounts found for this building."))
        elements.append(Spacer(1, 0.2*inch))

    ###########################################
    # TAB 7: MARKET VALUES - MARKET ANALYSIS & COMPARISON
    ###########################################
    elements.append(PageBreak())
    elements.append(create_section_header('Tab 7: Market Values - Market Analysis & Comparison', '#ffc107'))
    elements.append(Spacer(1, 0.15*inch))

    # Get market value settings
    try:
        market_settings = MarketValueSetting.objects.get(building=building)

        elements.append(create_subsection_header('Market Value Ranges (per m²)'))

        market_ranges = [
            ['Sale Price Range:', f"R$ {market_settings.sale_min:,.2f} - R$ {market_settings.sale_max:,.2f}"],
            ['Rental Price Range:', f"R$ {market_settings.rental_min:,.2f} - R$ {market_settings.rental_max:,.2f}"],
            ['Condominium Fee Range:', f"R$ {market_settings.condominium_min:,.2f} - R$ {market_settings.condominium_max:,.2f}"],
        ]
        elements.append(create_info_table(market_ranges))
        elements.append(Spacer(1, 0.2*inch))

        if units.exists():
            # Calculate market values for each unit
            elements.append(create_subsection_header('Detailed Unit Market Analysis'))

            market_data = [['Unit', 'Owner', 'Area', 'Sale Min', 'Sale Max', 'Rental Min', 'Rental Max', 'Condo Fee']]

            total_sale_min = 0
            total_sale_max = 0
            total_rental_min = 0
            total_rental_max = 0

            for unit in units[:30]:  # Limit to 30 units for space
                area = float(unit.area)

                # Calculate market values
                sale_min_val = area * float(market_settings.sale_min)
                sale_max_val = area * float(market_settings.sale_max)
                rental_min_val = area * float(market_settings.rental_min)
                rental_max_val = area * float(market_settings.rental_max)

                # Calculate actual condo fee for this unit (from Tab 6 calculation)
                unit_condo_fee = float(total_collection) * float(unit.ideal_fraction) if total_collection > 0 else 0

                total_sale_min += sale_min_val
                total_sale_max += sale_max_val
                total_rental_min += rental_min_val
                total_rental_max += rental_max_val

                market_data.append([
                    str(unit.number)[:8],
                    str(unit.owner)[:12] if unit.owner else 'N/A',
                    f"{area:.1f}",
                    f"R$ {sale_min_val:,.0f}",
                    f"R$ {sale_max_val:,.0f}",
                    f"R$ {rental_min_val:,.0f}",
                    f"R$ {rental_max_val:,.0f}",
                    f"R$ {unit_condo_fee:,.2f}",
                ])

            market_table = Table(market_data, colWidths=[0.6*inch, 1.0*inch, 0.6*inch, 1.0*inch, 1.0*inch, 1.0*inch, 1.0*inch, 0.9*inch])
            market_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 1), (7, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 6),
                ('FONTSIZE', (0, 1), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('TOPPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ]))
            elements.append(market_table)
            elements.append(Spacer(1, 0.2*inch))

            if units.count() > 30:
                elements.append(create_normal_paragraph(f"Note: Showing 30 units out of {units.count()} total."))
                elements.append(Spacer(1, 0.2*inch))

            # Market value summary
            elements.append(create_subsection_header('Market Value Summary'))

            summary_market = [
                ['Total Sale Value Range:', f"R$ {total_sale_min:,.2f} - R$ {total_sale_max:,.2f}"],
                ['Total Rental Value Range:', f"R$ {total_rental_min:,.2f} - R$ {total_rental_max:,.2f}"],
                ['Total Monthly Collection:', f"R$ {total_collection:,.2f}"],
                ['Average Condo Fee per m²:', f"R$ {avg_fee_per_sqm:,.2f}"],
            ]
            elements.append(create_info_table(summary_market))
            elements.append(Spacer(1, 0.2*inch))

            # Market comparison note
            avg_market_condo = (float(market_settings.condominium_min) + float(market_settings.condominium_max)) / 2
            variance_from_market = ((avg_fee_per_sqm - avg_market_condo) / avg_market_condo * 100) if avg_market_condo > 0 else 0

            elements.append(create_normal_paragraph(
                f"<b>Market Comparison:</b> Building's average condo fee (R$ {avg_fee_per_sqm:.2f}/m²) is "
                f"{variance_from_market:+.1f}% compared to market average (R$ {avg_market_condo:.2f}/m²)."
            ))
            elements.append(Spacer(1, 0.2*inch))

    except MarketValueSetting.DoesNotExist:
        elements.append(create_normal_paragraph("Market value settings have not been configured for this building."))
        elements.append(Spacer(1, 0.2*inch))

    return elements
def generate_consumption_section(building, start_date, end_date):
    """Generate comprehensive consumption section with detailed readings"""
    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Consumption Analysis', '#17a2b8'))
    elements.append(Spacer(1, 0.15*inch))

    # Get consumption readings in date range
    readings = ConsumptionReading.objects.filter(
        building=building,
        reading_date__range=[start_date, end_date]
    ).select_related('consumption_type').order_by('-reading_date')

    if not readings.exists():
        elements.append(create_normal_paragraph("No consumption data available for the selected period."))
        return elements

    elements.append(create_normal_paragraph(
        f"Consumption analysis covering water, electricity, and gas usage for the period from "
        f"{start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}."
    ))
    elements.append(Spacer(1, 0.15*inch))

    # Detailed Consumption Readings Table
    elements.append(create_subsection_header('Consumption Readings Detail'))
    readings_data = [['Date', 'Type', 'Period', 'Consumption', 'Cost', 'Prev. Month', '% Change']]

    for reading in readings[:40]:  # Limit to 40 most recent
        readings_data.append([
            reading.reading_date.strftime('%Y-%m-%d'),
            reading.consumption_type.get_name_display()[:12],
            reading.get_period_display()[:10],
            f"{reading.consumption_value:,.2f} {reading.consumption_type.unit}",
            f"R$ {reading.cost:,.2f}" if reading.cost else 'N/A',
            f"{reading.previous_month_consumption:,.2f}" if reading.previous_month_consumption else 'N/A',
            f"{reading.percentage_change:+.1f}%" if reading.percentage_change is not None else 'N/A',
        ])

    readings_table = Table(readings_data, colWidths=[0.95*inch, 1.0*inch, 0.9*inch, 1.3*inch, 1.0*inch, 1.0*inch, 0.95*inch])
    readings_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (3, 1), (5, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(readings_table)
    elements.append(Spacer(1, 0.2*inch))

    if readings.count() > 40:
        elements.append(create_normal_paragraph(f"Note: Showing 40 most recent consumption readings out of {readings.count()} total records."))
        elements.append(Spacer(1, 0.2*inch))

    # Consumption by type
    consumption_by_type = {}
    cost_by_type = {}

    for reading in readings:
        type_name = reading.consumption_type.get_name_display()
        consumption_by_type[type_name] = consumption_by_type.get(type_name, 0) + float(reading.consumption_value)
        if reading.cost:
            cost_by_type[type_name] = cost_by_type.get(type_name, 0) + float(reading.cost)

    # Summary table
    elements.append(create_subsection_header('Consumption Summary by Type'))
    summary_data = [['Type', 'Total Consumption', 'Total Cost', 'Average Cost per Unit']]
    for type_name in consumption_by_type.keys():
        consumption = consumption_by_type.get(type_name, 0)
        cost = cost_by_type.get(type_name, 0)
        avg_cost = (cost / consumption) if consumption > 0 else 0
        summary_data.append([
            type_name,
            f"{consumption:,.2f}",
            f"R$ {cost:,.2f}" if cost > 0 else "N/A",
            f"R$ {avg_cost:,.2f}" if cost > 0 else "N/A"
        ])

    elements.append(create_data_table(summary_data))
    elements.append(Spacer(1, 0.2*inch))

    # Consumption distribution chart
    chart_data = [(type_name, consumption) for type_name, consumption in consumption_by_type.items()]
    chart = create_chart('bar', chart_data, 'Total Consumption by Type', 'Type', 'Consumption')
    elements.append(chart)
    elements.append(Spacer(1, 0.2*inch))

    # Cost distribution chart
    if any(cost > 0 for cost in cost_by_type.values()):
        chart_data = [(type_name, cost) for type_name, cost in cost_by_type.items() if cost > 0]
        chart = create_chart('pie', chart_data, 'Cost Distribution by Type', '', '')
        elements.append(chart)
        elements.append(Spacer(1, 0.2*inch))

    # Monthly consumption trend
    from collections import defaultdict
    from dateutil.relativedelta import relativedelta

    monthly_consumption = defaultdict(lambda: defaultdict(float))
    monthly_cost = defaultdict(lambda: defaultdict(float))

    for reading in readings:
        month_key = reading.reading_date.strftime('%Y-%m')
        type_name = reading.consumption_type.get_name_display()
        monthly_consumption[month_key][type_name] += float(reading.consumption_value)
        if reading.cost:
            monthly_cost[month_key][type_name] += float(reading.cost)

    if len(monthly_consumption) > 1:
        elements.append(create_subsection_header('Monthly Consumption Trends'))

        # Get all months in range
        current = start_date.replace(day=1)
        end = end_date.replace(day=1)
        all_months = []
        while current <= end:
            all_months.append(current.strftime('%Y-%m'))
            current += relativedelta(months=1)

        # Monthly detail table
        trend_data = [['Month'] + list(consumption_by_type.keys()) + ['Total Cost']]
        for month in all_months:
            row = [month]
            for type_name in consumption_by_type.keys():
                value = monthly_consumption[month].get(type_name, 0)
                row.append(f"{value:,.1f}")
            month_total_cost = sum(monthly_cost[month].values())
            row.append(f"R$ {month_total_cost:,.2f}")
            trend_data.append(row)

        elements.append(create_data_table(trend_data))
        elements.append(Spacer(1, 0.2*inch))

        # Create trend chart for each type
        for type_name in consumption_by_type.keys():
            chart_data = [(month, monthly_consumption[month].get(type_name, 0)) for month in all_months]
            chart = create_chart('line', chart_data, f'{type_name} Monthly Trend', 'Month', 'Consumption')
            elements.append(chart)
            elements.append(Spacer(1, 0.15*inch))

    return elements


def generate_legal_obligations_section(building, start_date, end_date):
    """Generate comprehensive legal obligations section with complete details"""
    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Legal Obligations', '#dc3545'))
    elements.append(Spacer(1, 0.15*inch))

    # Get obligations
    obligations = LegalObligation.objects.filter(
        building=building,
        due_date__range=[start_date, end_date]
    ).order_by('-due_date')

    # Get templates
    templates = LegalTemplate.objects.filter(
        building=building,
        active=True
    ).order_by('name')

    # Get completions in date range
    completions = LegalObligationCompletion.objects.filter(
        template__building=building,
        completion_date__range=[start_date, end_date]
    ).select_related('template').order_by('-completion_date')

    elements.append(create_normal_paragraph(
        f"Legal obligations and compliance tracking for {building.building_name}. "
        f"This section includes pending obligations, completed tasks, and compliance status."
    ))
    elements.append(Spacer(1, 0.15*inch))

    # Summary
    total_obligations = obligations.count()
    completed_obligations = obligations.filter(status='completed').count()
    overdue_obligations = obligations.filter(status='overdue').count()
    pending_obligations = obligations.filter(status='pending').count()

    summary_data = [
        ['Total Obligations:', str(total_obligations)],
        ['Completed:', f"{completed_obligations} ({(completed_obligations/total_obligations*100) if total_obligations > 0 else 0:.1f}%)"],
        ['Pending:', str(pending_obligations)],
        ['Overdue:', str(overdue_obligations)],
        ['Active Templates:', str(templates.count())],
        ['Completions in Period:', str(completions.count())],
    ]
    elements.append(create_info_table(summary_data))
    elements.append(Spacer(1, 0.2*inch))

    # Detailed Obligations Table
    if total_obligations > 0:
        elements.append(create_subsection_header('Legal Obligations Detail'))
        obligations_data = [['Type', 'Title', 'Due Date', 'Status', 'Responsible', 'Est. Cost', 'Act. Cost']]

        for obligation in obligations[:30]:  # Limit to 30 most recent
            obligations_data.append([
                obligation.get_obligation_type_display()[:18],
                str(obligation.title)[:25],
                obligation.due_date.strftime('%Y-%m-%d'),
                obligation.get_status_display()[:12],
                str(obligation.responsible_party)[:15],
                f"R$ {obligation.estimated_cost:,.0f}" if obligation.estimated_cost else 'N/A',
                f"R$ {obligation.actual_cost:,.0f}" if obligation.actual_cost else 'N/A',
            ])

        obligations_table = Table(obligations_data, colWidths=[1.2*inch, 1.8*inch, 0.9*inch, 0.9*inch, 1.1*inch, 0.9*inch, 0.9*inch])
        obligations_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (5, 1), (6, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(obligations_table)
        elements.append(Spacer(1, 0.2*inch))

        if total_obligations > 30:
            elements.append(create_normal_paragraph(f"Note: Showing 30 most recent obligations out of {total_obligations} total records."))
            elements.append(Spacer(1, 0.2*inch))

    # Active Templates Table
    if templates.count() > 0:
        elements.append(create_subsection_header('Active Legal Obligation Templates'))
        templates_data = [['Name', 'Frequency', 'Due Date', 'Status', 'Notice Days', 'Quote Required']]

        for template in templates[:20]:
            templates_data.append([
                str(template.name)[:30],
                str(template.frequency).replace('_', ' ').title()[:15],
                template.due_month.strftime('%Y-%m-%d') if template.due_month else 'N/A',
                template.get_status_display()[:12],
                str(template.notice_period),
                'Yes' if template.requires_quote else 'No',
            ])

        templates_table = Table(templates_data, colWidths=[2.2*inch, 1.2*inch, 1.0*inch, 1.0*inch, 0.9*inch, 1.0*inch])
        templates_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(templates_table)
        elements.append(Spacer(1, 0.2*inch))

    # Completions Table
    if completions.count() > 0:
        elements.append(create_subsection_header('Completed Obligations in Period'))
        completions_data = [['Template Name', 'Completion Date', 'Prev. Due', 'New Due', 'Cost']]

        for completion in completions[:20]:
            completions_data.append([
                str(completion.template.name)[:35],
                completion.completion_date.strftime('%Y-%m-%d'),
                completion.previous_due_date.strftime('%Y-%m-%d') if completion.previous_due_date else 'N/A',
                completion.new_due_date.strftime('%Y-%m-%d') if completion.new_due_date else 'N/A',
                f"R$ {completion.actual_cost:,.2f}" if completion.actual_cost else 'N/A',
            ])

        completions_table = Table(completions_data, colWidths=[2.5*inch, 1.2*inch, 1.0*inch, 1.0*inch, 1.0*inch])
        completions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dc3545')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(completions_table)
        elements.append(Spacer(1, 0.2*inch))

    # Status distribution chart
    if total_obligations > 0:
        status_data = [
            ('Completed', completed_obligations),
            ('Pending', pending_obligations),
            ('Overdue', overdue_obligations),
        ]
        chart = create_chart('pie', status_data, 'Obligations Status Distribution', '', '',
                           colors_list=['#28a745', '#ffc107', '#dc3545'])
        elements.append(chart)
        elements.append(Spacer(1, 0.2*inch))

    # Obligations by type
    if total_obligations > 0:
        elements.append(create_subsection_header('Obligations by Type'))

        type_counts = {}
        for obligation in obligations:
            type_display = obligation.get_obligation_type_display()
            type_counts[type_display] = type_counts.get(type_display, 0) + 1

        type_data = [['Type', 'Count']]
        for obligation_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
            type_data.append([obligation_type, str(count)])

        elements.append(create_data_table(type_data))
        elements.append(Spacer(1, 0.2*inch))

        chart_data = [(otype, count) for otype, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)[:6]]
        chart = create_chart('bar', chart_data, 'Obligations by Type', 'Type', 'Count')
        elements.append(chart)

    # Cost analysis
    total_estimated_cost = obligations.aggregate(Sum('estimated_cost'))['estimated_cost__sum'] or 0
    total_actual_cost = obligations.filter(status='completed').aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0
    completion_costs = completions.aggregate(Sum('actual_cost'))['actual_cost__sum'] or 0

    if total_estimated_cost > 0 or total_actual_cost > 0:
        elements.append(create_subsection_header('Cost Analysis'))
        cost_data = [
            ['Estimated Cost (All):', f"R$ {total_estimated_cost:,.2f}"],
            ['Actual Cost (Completed):', f"R$ {total_actual_cost:,.2f}"],
            ['Costs in Period:', f"R$ {completion_costs:,.2f}"],
        ]
        elements.append(create_info_table(cost_data))

    return elements


def generate_field_management_section(building, start_date, end_date):
    """Generate comprehensive field management section with complete details"""
    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Field Management', '#6610f2'))
    elements.append(Spacer(1, 0.15*inch))

    # Material requests
    # Convert dates to timezone-aware datetime for DateTimeField comparison
    start_datetime = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    material_requests = FieldRequest.objects.filter(
        building=building,
        created_at__range=[start_datetime, end_datetime]
    ).prefetch_related('photos', 'comments').order_by('-created_at')

    # Technical calls
    technical_calls = FieldMgmtTechnical.objects.filter(
        created_at__range=[start_datetime, end_datetime]
    ).prefetch_related('images').order_by('-created_at')

    elements.append(create_normal_paragraph(
        f"Field management activities including material requests and technical service calls "
        f"for the period from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}."
    ))
    elements.append(Spacer(1, 0.15*inch))

    # Summary
    summary_data = [
        ['Material Requests:', str(material_requests.count())],
        ['Technical Calls:', str(technical_calls.count())],
        ['Total Field Activities:', str(material_requests.count() + technical_calls.count())],
    ]
    elements.append(create_info_table(summary_data))
    elements.append(Spacer(1, 0.2*inch))

    # Detailed Material Requests Table
    if material_requests.exists():
        elements.append(create_subsection_header('Material Requests Detail'))
        total_items = sum(len(req.items) for req in material_requests)

        requests_data = [['Title', 'Caretaker', 'Date', 'Items Count', 'Photos', 'Comments']]
        for req in material_requests[:25]:  # Top 25 recent
            requests_data.append([
                str(req.title)[:30],
                str(req.caretaker)[:20] if req.caretaker else 'N/A',
                req.created_at.strftime('%Y-%m-%d'),
                str(len(req.items)),
                str(req.photos.count()),
                str(req.comments.count()),
            ])

        requests_table = Table(requests_data, colWidths=[2.2*inch, 1.5*inch, 1.0*inch, 0.9*inch, 0.8*inch, 0.9*inch])
        requests_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6610f2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (3, 1), (5, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(requests_table)
        elements.append(Spacer(1, 0.2*inch))

        if material_requests.count() > 25:
            elements.append(create_normal_paragraph(f"Note: Showing 25 most recent material requests out of {material_requests.count()} total records."))
            elements.append(Spacer(1, 0.2*inch))

        # Material Items Breakdown
        elements.append(create_subsection_header('Material Items Requested'))
        items_data = [['Request Title', 'Product Type', 'Quantity', 'Observations']]

        for req in material_requests[:15]:
            for item in req.items[:3]:  # Show up to 3 items per request
                items_data.append([
                    str(req.title)[:25],
                    str(item.get('productType', 'N/A'))[:20],
                    str(item.get('quantity', 'N/A'))[:10],
                    str(item.get('observations', 'N/A'))[:30],
                ])

        items_table = Table(items_data, colWidths=[1.8*inch, 1.5*inch, 1.0*inch, 3.2*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6610f2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(items_table)
        elements.append(Spacer(1, 0.2*inch))

        elements.append(create_normal_paragraph(f"Total Material Items: {total_items}"))
        elements.append(Spacer(1, 0.2*inch))

    # Detailed Technical Calls Table
    if technical_calls.exists():
        elements.append(create_subsection_header('Technical Service Calls Detail'))

        calls_data = [['Code', 'Title', 'Location', 'Priority', 'Date', 'Company Email', 'Images']]
        for call in technical_calls[:25]:  # Top 25 recent
            calls_data.append([
                str(call.code)[:8],
                str(call.title)[:22],
                str(call.location)[:18],
                call.get_priority_display()[:10],
                call.created_at.strftime('%Y-%m-%d'),
                str(call.company_email)[:22],
                str(call.images.count()),
            ])

        calls_table = Table(calls_data, colWidths=[0.7*inch, 1.5*inch, 1.3*inch, 0.8*inch, 0.9*inch, 1.6*inch, 0.7*inch])
        calls_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6610f2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (6, 1), (6, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('FONTSIZE', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(calls_table)
        elements.append(Spacer(1, 0.2*inch))

        if technical_calls.count() > 25:
            elements.append(create_normal_paragraph(f"Note: Showing 25 most recent technical calls out of {technical_calls.count()} total records."))
            elements.append(Spacer(1, 0.2*inch))

        # Technical Calls Descriptions Table
        elements.append(create_subsection_header('Technical Calls Descriptions'))
        desc_data = [['Code', 'Title', 'Description']]

        for call in technical_calls[:15]:
            desc_data.append([
                str(call.code)[:8],
                str(call.title)[:25],
                str(call.description)[:65],
            ])

        desc_table = Table(desc_data, colWidths=[0.8*inch, 2.0*inch, 4.7*inch])
        desc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6610f2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(desc_table)
        elements.append(Spacer(1, 0.2*inch))

        # Priority distribution
        priority_counts = {}
        for call in technical_calls:
            priority = call.get_priority_display()
            priority_counts[priority] = priority_counts.get(priority, 0) + 1

        elements.append(create_subsection_header('Technical Calls Priority Distribution'))
        priority_data = [['Priority', 'Count', 'Percentage']]
        total_calls = technical_calls.count()
        for priority, count in sorted(priority_counts.items()):
            percentage = (count / total_calls * 100) if total_calls > 0 else 0
            priority_data.append([priority, str(count), f"{percentage:.1f}%"])

        elements.append(create_data_table(priority_data))
        elements.append(Spacer(1, 0.2*inch))

        # Priority chart
        chart_data = [(priority, count) for priority, count in priority_counts.items()]
        chart = create_chart('pie', chart_data, 'Technical Calls by Priority', '', '',
                           colors_list=['#28a745', '#17a2b8', '#ffc107', '#dc3545'])
        elements.append(chart)

    return elements


def generate_calendar_section(building, start_date, end_date):
    """Generate calendar/schedule section"""
    elements = []
    elements.append(PageBreak())
    elements.append(create_section_header('Calendar & Schedule', '#e83e8c'))
    elements.append(Spacer(1, 0.15*inch))

    elements.append(create_normal_paragraph(
        f"Calendar overview showing important dates, scheduled activities, and upcoming events "
        f"for {building.building_name} from {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}."
    ))
    elements.append(Spacer(1, 0.15*inch))

    # Collect all date-based events
    events = []

    # Legal obligations with due dates
    legal_obligations = LegalObligation.objects.filter(
        building=building,
        due_date__range=[start_date, end_date]
    )
    for obligation in legal_obligations:
        events.append({
            'date': obligation.due_date,
            'type': 'Legal Obligation',
            'description': obligation.title,
            'status': obligation.get_status_display()
        })

    # Maintenance schedules
    maintenance_records = MaintenanceRecord.objects.filter(
        equipment__building_id=str(building.id),
        date__range=[start_date, end_date]
    )
    for record in maintenance_records:
        events.append({
            'date': record.date,
            'type': 'Maintenance',
            'description': f"{record.equipment.name} - {record.type}",
            'status': 'Scheduled'
        })

    # Sort events by date
    events.sort(key=lambda x: x['date'])

    if events:
        elements.append(create_subsection_header('Scheduled Events'))

        events_data = [['Date', 'Type', 'Description', 'Status']]
        for event in events[:20]:  # Show up to 20 events
            events_data.append([
                event['date'].strftime('%Y-%m-%d'),
                event['type'],
                event['description'][:40] + '...' if len(event['description']) > 40 else event['description'],
                event['status']
            ])

        elements.append(create_data_table(events_data))
        elements.append(Spacer(1, 0.2*inch))

        # Event type distribution
        type_counts = {}
        for event in events:
            type_counts[event['type']] = type_counts.get(event['type'], 0) + 1

        chart_data = [(etype, count) for etype, count in type_counts.items()]
        chart = create_chart('pie', chart_data, 'Events by Type', '', '')
        elements.append(chart)
    else:
        elements.append(create_normal_paragraph("No scheduled events found for the selected period."))

    # Monthly event distribution
    from collections import defaultdict
    from dateutil.relativedelta import relativedelta

    monthly_events = defaultdict(int)
    for event in events:
        month_key = event['date'].strftime('%Y-%m')
        monthly_events[month_key] += 1

    if len(monthly_events) > 1:
        elements.append(Spacer(1, 0.2*inch))
        elements.append(create_subsection_header('Monthly Event Distribution'))

        # Get all months
        current = start_date.replace(day=1)
        end = end_date.replace(day=1)
        all_months = []
        while current <= end:
            all_months.append(current.strftime('%Y-%m'))
            current += relativedelta(months=1)

        chart_data = [(month, monthly_events.get(month, 0)) for month in all_months]
        chart = create_chart('bar', chart_data, 'Events per Month', 'Month', 'Number of Events')
        elements.append(chart)

    return elements


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_report(request):
    """Generate comprehensive PDF report"""
    try:
        # Extract data from request
        building_id = request.data.get('building_id')
        start_date_str = request.data.get('start_date')
        end_date_str = request.data.get('end_date')
        sections = request.data.get('sections', {})
        conclusions = request.data.get('conclusions', {})

        # Validate required fields
        if not all([building_id, start_date_str, end_date_str]):
            return Response(
                {'error': 'building_id, start_date, and end_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse dates
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Invalid date format. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get building
        try:
            building = Building.objects.get(id=building_id)
        except Building.DoesNotExist:
            return Response(
                {'error': 'Building not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create PDF buffer
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.65*inch,
            bottomMargin=0.65*inch,
        )

        # Build document content
        story = []

        # Title page
        title_style = ParagraphStyle(
            'Title',
            parent=getSampleStyleSheet()['Title'],
            fontSize=24,
            textColor=HexColor('#17a2b8'),
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        )

        subtitle_style = ParagraphStyle(
            'Subtitle',
            parent=getSampleStyleSheet()['Normal'],
            fontSize=14,
            textColor=HexColor('#2c3e50'),
            spaceAfter=6,
            alignment=TA_CENTER,
            fontName='Helvetica',
        )

        story.append(Spacer(1, 2*inch))
        story.append(Paragraph('COMPREHENSIVE BUILDING REPORT', title_style))
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(building.building_name, subtitle_style))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"Report Period: {start_date.strftime('%B %d, %Y')} to {end_date.strftime('%B %d, %Y')}",
            subtitle_style
        ))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(
            f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
            subtitle_style
        ))
        story.append(PageBreak())

        # Helper function to add section-specific justifications
        def add_section_justifications(section_name, conclusion_text):
            """Add justification paragraphs for a section if provided"""
            if conclusion_text and conclusion_text.strip():
                story.append(Spacer(1, 0.3*inch))
                story.append(create_subsection_header(f'{section_name} - Justifications'))
                story.append(Spacer(1, 0.1*inch))

                conclusion_paragraphs = conclusion_text.strip().split('\n')
                for para in conclusion_paragraphs:
                    if para.strip():
                        story.append(create_normal_paragraph(para.strip()))
                        story.append(Spacer(1, 0.1*inch))

        # NEW VISUAL REPORT STRUCTURE - CHARTS ONLY, 6 SECTIONS
        # Removed tables, focus on visual chart-based presentation

        # Import new visual functions
        from reporting.new_visual_sections import (
            generate_financial_charts,
            generate_consumption_charts,
            generate_legal_visual,
            generate_unit_overview,
            generate_service_requests_visual,
            generate_calendar_visual
        )

        # 1. BUILDING INFORMATION / UNIT OVERVIEW (Numbers, area, rental/sale/fee with min/max limits)
        if sections.get('building_info'):
            story.extend(generate_unit_overview(building))
            add_section_justifications('Building Information', conclusions.get('building_info', ''))

        # 2. EQUIPMENT (placeholder for equipment section)
        if sections.get('equipment'):
            story.append(create_section_header('Equipment Information'))
            story.append(Spacer(1, 0.2*inch))
            story.append(create_normal_paragraph('Equipment section implementation pending.'))
            story.append(Spacer(1, 0.2*inch))
            add_section_justifications('Equipment', conclusions.get('equipment', ''))
            story.append(PageBreak())

        # 3. FINANCIAL CHARTS (Overall performance, by account, market comparison)
        if sections.get('financial'):
            story.extend(generate_financial_charts(building, start_date, end_date))
            add_section_justifications('Financial Analysis', conclusions.get('financial', ''))

        # 4. CONSUMPTION CHARTS (Consumption vs Payments indicators)
        if sections.get('consumption'):
            story.extend(generate_consumption_charts(building, start_date, end_date))
            add_section_justifications('Consumption Analysis', conclusions.get('consumption', ''))

        # 5. LEGAL OBLIGATIONS (Visual, modern, colorful)
        if sections.get('legal_obligations'):
            story.extend(generate_legal_visual(building, start_date, end_date))
            add_section_justifications('Legal Obligations', conclusions.get('legal_obligations', ''))

        # 6. OPEN SERVICE REQUESTS (Consolidated, readable format)
        if sections.get('field_management'):
            story.extend(generate_service_requests_visual(building, start_date, end_date))
            add_section_justifications('Service Requests', conclusions.get('field_management', ''))

        # 7. MEETINGS AND SCHEDULED COMMITMENTS (Integrated format)
        if sections.get('calendar'):
            story.extend(generate_calendar_visual(building, start_date, end_date))
            add_section_justifications('Calendar', conclusions.get('calendar', ''))

        # Build PDF
        doc.build(story, canvasmaker=NumberedCanvas)

        # Prepare response
        buffer.seek(0)
        response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
        filename = f"Report_{building.building_name.replace(' ', '_')}_{start_date}_{end_date}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        import traceback
        traceback.print_exc()
        return Response(
            {'error': f'Error generating report: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )



# ============================================
# Report Justification API Endpoints
# ============================================

from .models import ReportJustification
from .serializers import ReportJustificationSerializer, ReportJustificationUpdateSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_report_justifications(request, building_id):
    """
    Get report justifications for a specific building.
    Creates a new record if one doesn't exist.
    """
    try:
        building = Building.objects.get(id=building_id)
    except Building.DoesNotExist:
        return Response(
            {'error': 'Building not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get or create justification record for this building
    justification, created = ReportJustification.objects.get_or_create(
        building=building,
        defaults={'updated_by': request.user}
    )

    serializer = ReportJustificationSerializer(justification)
    return Response(serializer.data)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_report_justifications(request, building_id):
    """
    Update report justifications for a specific building.
    Creates a new record if one doesn't exist, then updates it.
    """
    try:
        building = Building.objects.get(id=building_id)
    except Building.DoesNotExist:
        return Response(
            {'error': 'Building not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Get or create justification record for this building
    justification, created = ReportJustification.objects.get_or_create(
        building=building,
        defaults={'updated_by': request.user}
    )

    # Use partial update for PATCH, full update for PUT
    partial = request.method == 'PATCH'
    serializer = ReportJustificationUpdateSerializer(
        justification,
        data=request.data,
        partial=partial
    )

    if serializer.is_valid():
        serializer.save()
        # Update the updated_by field
        justification.updated_by = request.user
        justification.save(update_fields=['updated_by', 'updated_at'])

        # Return the full data
        full_serializer = ReportJustificationSerializer(justification)
        return Response(full_serializer.data)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Mapping of page numbers to their justification field names
PAGE_JUSTIFICATION_FIELDS = {
    3: ['page3_financial_justification'],
    4: ['page4_income_justification', 'page4_expenses_justification', 'page4_balance_justification'],
    5: ['page5_section1_justification', 'page5_section2_justification', 'page5_section3_justification'],
    # Page 6 has no justification
    7: ['page7_legal_justification'],
    8: ['page8_water_justification', 'page8_electricity_justification', 'page8_gas_justification'],
    9: ['page9_requests_justification'],
    10: ['page10_calendar_justification'],
}


@api_view(['PATCH', 'OPTIONS'])
@permission_classes([IsAuthenticated])
def update_page_justification(request, building_id, page_number):
    """
    Update justification fields for a specific page.
    Only updates the fields relevant to the specified page number.
    """
    try:
        building = Building.objects.get(id=building_id)
    except Building.DoesNotExist:
        return Response(
            {'error': 'Building not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Check if this page has justification fields
    if page_number not in PAGE_JUSTIFICATION_FIELDS:
        return Response(
            {'error': f'Page {page_number} does not have justification fields'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Get or create justification record for this building
    justification, created = ReportJustification.objects.get_or_create(
        building=building,
        defaults={'updated_by': request.user}
    )

    # Filter request data to only include fields for this page
    allowed_fields = PAGE_JUSTIFICATION_FIELDS[page_number]
    filtered_data = {k: v for k, v in request.data.items() if k in allowed_fields}

    if not filtered_data:
        return Response(
            {'error': f'No valid justification fields provided for page {page_number}. Expected: {allowed_fields}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Update only the specified fields
    for field, value in filtered_data.items():
        setattr(justification, field, value)

    justification.updated_by = request.user
    justification.save()

    # Return the updated data for this page's fields
    response_data = {
        'page': page_number,
        'building_id': building_id,
        **{field: getattr(justification, field) for field in allowed_fields}
    }

    return Response(response_data)
