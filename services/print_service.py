"""Print service — thermal receipts and A4 invoices."""

import os
import logging
from datetime import datetime
from typing import Optional

from config import (
    cents_to_display, CURRENCY_SYMBOL, RECEIPT_CHARS_80MM,
    RECEIPT_CHARS_58MM, DATA_DIR, PRINTER_SETTINGS
)

logger = logging.getLogger(__name__)


# ─── Thermal Receipt ───────────────────────────────────────────

def _receipt_line(text: str, width: int = RECEIPT_CHARS_80MM) -> str:
    """Truncate/pad text to fit receipt width."""
    if len(text) > width:
        return text[:width - 1] + "…"
    return text.ljust(width)


def _receipt_center(text: str, width: int = RECEIPT_CHARS_80MM) -> str:
    """Center text within receipt width."""
    if len(text) >= width:
        return text[:width]
    padding = (width - len(text)) // 2
    return " " * padding + text


def _receipt_separator(width: int = RECEIPT_CHARS_80MM) -> str:
    return "-" * width


def generate_thermal_receipt_text(invoice_data: dict, width: int = RECEIPT_CHARS_80MM) -> str:
    """Generate plain text thermal receipt content.

    Args:
        invoice_data: dict with keys:
            invoice_number, date, customer_name, phone, vehicle_reg,
            items: list of {description, qty, unit_price, line_total},
            subtotal, labor_charge, discount, total, paid, due,
            payment_method, business_name, business_address, business_phone
        width: chars per line (48 for 80mm, 32 for 58mm)
    """
    lines = []
    biz_name = invoice_data.get("business_name", "Vehicle Service Center")
    biz_addr = invoice_data.get("business_address", "")
    biz_phone = invoice_data.get("business_phone", "")

    lines.append(_receipt_center(biz_name, width))
    if biz_addr:
        lines.append(_receipt_center(biz_addr, width))
    if biz_phone:
        lines.append(_receipt_center(f"Tel: {biz_phone}", width))
    lines.append("")

    inv_num = invoice_data.get("invoice_number", "")
    date_str = invoice_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
    lines.append(_receipt_line(f"Invoice: {inv_num}", width))
    lines.append(_receipt_line(f"Date: {date_str}", width))

    cust = invoice_data.get("customer_name", "")
    if cust:
        lines.append(_receipt_line(f"Customer: {cust}", width))
    phone = invoice_data.get("phone", "")
    if phone:
        lines.append(_receipt_line(f"Phone: {phone}", width))
    veh = invoice_data.get("vehicle_reg", "")
    if veh:
        lines.append(_receipt_line(f"Vehicle: {veh}", width))
    lines.append(_receipt_separator(width))

    # Items
    items = invoice_data.get("items", [])
    for item in items:
        desc = item.get("description", "")
        qty = item.get("qty", 1)
        price = cents_to_display(item.get("unit_price", 0))
        total = cents_to_display(item.get("line_total", 0))
        lines.append(_receipt_line(desc, width))
        lines.append(_receipt_line(f"  {qty} x {price} = {total}", width))

    lines.append(_receipt_separator(width))

    # Totals
    subtotal = cents_to_display(invoice_data.get("subtotal", 0))
    lines.append(_receipt_line(f"Subtotal: {subtotal}", width))

    labor = invoice_data.get("labor_charge", 0)
    if labor > 0:
        lines.append(_receipt_line(f"Labor: {cents_to_display(labor)}", width))

    discount = invoice_data.get("discount", 0)
    if discount > 0:
        lines.append(_receipt_line(f"Discount: -{cents_to_display(discount)}", width))

    lines.append(_receipt_separator(width))
    total_str = cents_to_display(invoice_data.get("total", 0))
    lines.append(_receipt_line(f"TOTAL: {total_str}", width))

    paid = invoice_data.get("paid", 0)
    if paid > 0:
        lines.append(_receipt_line(f"Paid: {cents_to_display(paid)}", width))
    due = invoice_data.get("due", 0)
    if due > 0:
        lines.append(_receipt_line(f"Due: {cents_to_display(due)}", width))

    method = invoice_data.get("payment_method", "")
    if method:
        lines.append(_receipt_line(f"Payment: {method}", width))

    lines.append("")
    lines.append(_receipt_center("Thank you for your business!", width))
    lines.append("")

    return "\n".join(lines)


def save_thermal_receipt(invoice_data: dict, width: int = RECEIPT_CHARS_80MM) -> str:
    """Save thermal receipt text to file. Returns file path."""
    content = generate_thermal_receipt_text(invoice_data, width)
    inv_num = invoice_data.get("invoice_number", "UNKNOWN")
    filename = f"receipt_{inv_num}.txt"
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info(f"Thermal receipt saved to: {filepath}")
    return filepath


# ─── A4 Invoice (ReportLab) ───────────────────────────────────

def generate_a4_invoice_pdf(invoice_data: dict) -> str:
    """Generate A4 invoice PDF using ReportLab. Returns file path.

    Args:
        invoice_data: same dict as generate_thermal_receipt_text
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm, cm
        from reportlab.lib.colors import HexColor, black, white
        from reportlab.platypus import (
            SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    except ImportError:
        logger.error("ReportLab not installed. Cannot generate PDF.")
        return ""

    inv_num = invoice_data.get("invoice_number", "UNKNOWN")
    filename = f"invoice_{inv_num}.pdf"
    filepath = os.path.join(DATA_DIR, filename)

    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvTitle", parent=styles["Title"],
        fontSize=20, spaceAfter=6, textColor=HexColor("#222222"),
    )
    subtitle_style = ParagraphStyle(
        "InvSubtitle", parent=styles["Normal"],
        fontSize=10, spaceAfter=4, textColor=HexColor("#666666"),
    )
    header_style = ParagraphStyle(
        "InvHeader", parent=styles["Normal"],
        fontSize=10, textColor=white,
    )
    cell_style = ParagraphStyle(
        "InvCell", parent=styles["Normal"],
        fontSize=10, textColor=black,
    )
    total_style = ParagraphStyle(
        "InvTotal", parent=styles["Normal"],
        fontSize=12, textColor=HexColor("#222222"), fontName="Helvetica-Bold",
    )

    elements = []

    # Header
    biz_name = invoice_data.get("business_name", "Vehicle Service Center")
    biz_addr = invoice_data.get("business_address", "")
    biz_phone = invoice_data.get("business_phone", "")
    elements.append(Paragraph(biz_name, title_style))
    if biz_addr:
        elements.append(Paragraph(biz_addr, subtitle_style))
    if biz_phone:
        elements.append(Paragraph(f"Tel: {biz_phone}", subtitle_style))
    elements.append(Spacer(1, 10 * mm))

    # Invoice info
    date_str = invoice_data.get("date", datetime.now().strftime("%Y-%m-%d %H:%M"))
    info_data = [
        [Paragraph(f"<b>Invoice:</b> {inv_num}", cell_style),
         Paragraph(f"<b>Date:</b> {date_str}", cell_style)],
    ]
    cust = invoice_data.get("customer_name", "")
    phone = invoice_data.get("phone", "")
    veh = invoice_data.get("vehicle_reg", "")
    if cust:
        info_data.append([Paragraph(f"<b>Customer:</b> {cust}", cell_style),
                          Paragraph(f"<b>Vehicle:</b> {veh}", cell_style)])
    if phone:
        info_data.append([Paragraph(f"<b>Phone:</b> {phone}", cell_style), ""])

    info_table = Table(info_data, colWidths=[90 * mm, 90 * mm])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 8 * mm))

    # Items table
    accent = HexColor("#2F6FED")
    header_bg = HexColor("#E9ECEF")

    items = invoice_data.get("items", [])
    table_data = [
        [
            Paragraph("<b>#</b>", header_style),
            Paragraph("<b>Description</b>", header_style),
            Paragraph("<b>Qty</b>", header_style),
            Paragraph("<b>Unit Price</b>", header_style),
            Paragraph("<b>Total</b>", header_style),
        ]
    ]
    for i, item in enumerate(items, 1):
        table_data.append([
            Paragraph(str(i), cell_style),
            Paragraph(item.get("description", ""), cell_style),
            Paragraph(str(item.get("qty", 1)), cell_style),
            Paragraph(cents_to_display(item.get("unit_price", 0)), cell_style),
            Paragraph(cents_to_display(item.get("line_total", 0)), cell_style),
        ])

    items_table = Table(
        table_data,
        colWidths=[12 * mm, 80 * mm, 18 * mm, 35 * mm, 35 * mm],
    )
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), accent),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),
        ("ALIGN", (3, 0), (4, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor("#F8F9FA")]),
        ("GRID", (0, 0), (-1, -1), 0.5, HexColor("#DADADA")),
    ]))
    elements.append(items_table)
    elements.append(Spacer(1, 6 * mm))

    # Totals
    subtotal = cents_to_display(invoice_data.get("subtotal", 0))
    labor = invoice_data.get("labor_charge", 0)
    discount = invoice_data.get("discount", 0)
    total = cents_to_display(invoice_data.get("total", 0))
    paid = invoice_data.get("paid", 0)
    due = invoice_data.get("due", 0)

    totals_data = [
        [Paragraph("Subtotal:", cell_style), Paragraph(subtotal, cell_style)],
    ]
    if labor > 0:
        totals_data.append([Paragraph("Labor:", cell_style),
                            Paragraph(cents_to_display(labor), cell_style)])
    if discount > 0:
        totals_data.append([Paragraph("Discount:", cell_style),
                            Paragraph(f"-{cents_to_display(discount)}", cell_style)])
    totals_data.append([
        Paragraph("<b>TOTAL:</b>", total_style),
        Paragraph(f"<b>{total}</b>", total_style),
    ])
    if paid > 0:
        totals_data.append([Paragraph("Paid:", cell_style),
                            Paragraph(cents_to_display(paid), cell_style)])
    if due > 0:
        totals_data.append([Paragraph("Due:", cell_style),
                            Paragraph(cents_to_display(due), cell_style)])

    totals_table = Table(totals_data, colWidths=[130 * mm, 50 * mm])
    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LINEABOVE", (0, -1), (-1, -1), 1.5, accent),
    ]))
    elements.append(totals_table)

    # Payment method
    method = invoice_data.get("payment_method", "")
    if method:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(f"<b>Payment Method:</b> {method}", cell_style))

    # Footer
    elements.append(Spacer(1, 15 * mm))
    elements.append(Paragraph("Thank you for your business!", subtitle_style))

    doc.build(elements)
    logger.info(f"A4 invoice PDF saved to: {filepath}")
    return filepath


def print_thermal(invoice_data: dict, printer_name: str = None, width: int = RECEIPT_CHARS_80MM):
    """Send thermal receipt to printer using ESC/POS commands.

    Falls back to saving as text file if printer not available.
    """
    try:
        filepath = save_thermal_receipt(invoice_data, width)

        # Try ESC/POS printing if a thermal printer is configured
        printer = printer_name or PRINTER_SETTINGS.get("thermal_printer_name", "")
        if printer:
            try:
                import subprocess
                # Try raw printing via OS
                if os.name == "nt":
                    # Windows: use print command
                    subprocess.run(["print", "/D:", printer, filepath], check=True, timeout=10)
                else:
                    # Linux: try lp command
                    subprocess.run(["lp", "-d", printer, "-o", "raw", filepath],
                                   check=True, timeout=10)
                logger.info(f"Thermal receipt sent to printer: {printer}")
            except (subprocess.SubprocessError, FileNotFoundError) as e:
                logger.warning(f"Could not print to {printer}: {e}. Receipt saved as file.")
        return filepath
    except Exception as e:
        logger.error(f"Error generating thermal receipt: {e}")
        return ""


def print_a4_invoice(invoice_data: dict):
    """Generate and optionally print A4 invoice PDF."""
    try:
        filepath = generate_a4_invoice_pdf(invoice_data)
        if not filepath:
            return ""

        # Try to open/print the PDF
        printer = PRINTER_SETTINGS.get("a4_printer_name", "")
        if printer:
            try:
                import subprocess
                if os.name == "nt":
                    os.startfile(filepath, "print")
                else:
                    subprocess.run(["lp", "-d", printer, filepath], check=True, timeout=15)
                logger.info(f"A4 invoice sent to printer: {printer}")
            except Exception as e:
                logger.warning(f"Could not print A4 to {printer}: {e}. PDF saved.")

        return filepath
    except Exception as e:
        logger.error(f"Error generating A4 invoice: {e}")
        return ""
