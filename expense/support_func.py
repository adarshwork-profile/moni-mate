from fpdf import FPDF
from django.http import HttpResponse
import io

class CustomPDF(FPDF):
    def __init__(self, app_name, user_name):
        super().__init__()
        self.app_name = app_name
        self.user_name = user_name

    # Header
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, self.app_name, align='C', ln=1)

    # Footer
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='L')
        self.cell(0, 10, f'User:{self.user_name}', align='R')

def generate_pdf(data, user_name, report_type, month = None,app_name="MoniMate"):
    pdf = CustomPDF(app_name=app_name, user_name=user_name)
    pdf.add_page()

    # Add a heading
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, "Expense Report", align='C', ln=1)

    # Add subtext
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, "A detailed breakdown of your expenses.",align='C', ln=1)

    if report_type == "monthly":
        # Generate table for monthly data
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, f"Expenses - {month}", ln=1)
        generate_table(pdf, data[month], data["summary"])

    elif report_type == "yearly":
        # Generate chapters for each month
        for month, month_data in data.items():
            pdf.set_font('Arial', 'B', 14)
            pdf.cell(0, 10, f"Chapter: {month}", ln=1)
            generate_table(pdf, month_data[0], month_data[-1])
            pdf.add_page()

    # Return PDF as response
    pdf_buffer = io.BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)
    return pdf_buffer

def generate_table(pdf, table_data, summary):
    # Table Header
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(30, 10, "Name", border=1)
    pdf.cell(20, 10, "Category", border=1)
    pdf.cell(30, 10, "Amount", border=1)
    pdf.cell(30, 10, "Date", border=1)
    pdf.cell(40, 10, "Payment Method", border=1)
    pdf.cell(40, 10, "Transaction Mode", border=1)
    pdf.ln()

    # Table Rows
    pdf.set_font('Arial', '', 10)
    for row in table_data:
        pdf.cell(30, 10, row["name"], border=1)
        pdf.cell(20, 10, row["category"], border=1)
        pdf.cell(30, 10, row["amount"], border=1)
        pdf.cell(30, 10, row["date"], border=1)
        pdf.cell(40, 10, row["payment_method"], border=1)
        pdf.cell(40, 10, row["transaction_mode"], border=1)
        pdf.ln()

    # Summary
    pdf.ln()
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Summary", ln=1)
    pdf.set_font('Arial', '', 12)
    for key, value in summary.items():
        pdf.cell(0, 10, f"{key}: {value}", ln=1)

