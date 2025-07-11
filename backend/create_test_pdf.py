from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import os

def create_test_pdf():
    """Crea un PDF de prueba con transacciones de ejemplo"""
    
    # Crear el directorio si no existe
    os.makedirs("uploaded_pdfs", exist_ok=True)
    
    # Crear el documento
    doc = SimpleDocTemplate("uploaded_pdfs/test_statement.pdf", pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
        alignment=1  # Centrado
    )
    story.append(Paragraph("BBVA MEXICO", title_style))
    story.append(Paragraph("ESTADO DE CUENTA", title_style))
    story.append(Spacer(1, 20))
    
    # Información del cliente
    story.append(Paragraph("ANA SOFIA MOYA TORRES", styles['Heading2']))
    story.append(Paragraph("RIO TAMESI 126, ROMA", styles['Normal']))
    story.append(Paragraph("64700 MONTERREY, NL", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Tabla de transacciones
    data = [
        ['Fecha Operación', 'Fecha Cargo', 'Descripción', 'Monto'],
        ['04-Jun-2025', '04-Jun-2025', 'SU PAGO GRACIAS SPEI A CTA CLABE XXXXXXXX1179', '+ $9,153.00'],
        ['05-Jun-2025', '05-Jun-2025', 'COMPRA TARJETA OXXO MONTERREY', '- $150.00'],
        ['06-Jun-2025', '06-Jun-2025', 'RETIRO CAJERO AUTOMATICO', '- $500.00'],
        ['07-Jun-2025', '07-Jun-2025', 'UBER TRIP 8005928996', '- $340.00'],
        ['08-Jun-2025', '08-Jun-2025', 'RESTAURANTE PIZZA HUT', '- $280.00'],
        ['09-Jun-2025', '09-Jun-2025', 'DEPOSITO EFECTIVO', '+ $2,000.00'],
    ]
    
    # Crear tabla
    table = Table(data, colWidths=[1.2*inch, 1.2*inch, 3*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (2, -1), 'LEFT'),  # Descripción alineada a la izquierda
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Resumen
    story.append(Paragraph("RESUMEN:", styles['Heading3']))
    story.append(Paragraph("Total Abonos: $11,153.00", styles['Normal']))
    story.append(Paragraph("Total Cargos: $1,270.00", styles['Normal']))
    story.append(Paragraph("Saldo: $9,883.00", styles['Normal']))
    
    # Construir el PDF
    doc.build(story)
    print("PDF de prueba creado: uploaded_pdfs/test_statement.pdf")

if __name__ == "__main__":
    create_test_pdf() 