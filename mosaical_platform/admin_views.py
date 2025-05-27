
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from .reports import FinancialReports
import csv

@staff_member_required
def financial_dashboard(request):
    """Admin financial dashboard"""
    platform_summary = FinancialReports.generate_platform_summary()
    collection_report = FinancialReports.generate_collection_report()
    
    return render(request, 'admin/financial_dashboard.html', {
        'platform_summary': platform_summary,
        'collection_report': collection_report,
    })

@staff_member_required
def export_financial_report(request):
    """Export financial report to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="financial_report.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Metric', 'Value'])
    
    platform_summary = FinancialReports.generate_platform_summary()
    for key, value in platform_summary.items():
        writer.writerow([key.replace('_', ' ').title(), value])
    
    return response
