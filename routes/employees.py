from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import db, Employee, Issue # Import necessary models

employees_bp = Blueprint('employees', __name__, template_folder='../templates')

@employees_bp.route('/employees')
def list_employees(): # Renamed function
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    employees = Employee.query.all()
    employee_data = []
    
    for emp in employees:
        active_issues = Issue.query.filter_by(employee_id=emp.id, status='assigned').count()
        resolved_issues = Issue.query.filter_by(employee_id=emp.id, status='resolved').count()
        
        employee_data.append({
            'id': emp.id,
            'name': emp.name,
            'email': emp.email,
            'phone': emp.phone,
            'status': emp.status,
            'active_issues': active_issues,
            'resolved_issues': resolved_issues
        })
    
    return render_template('employees.html', employees=employee_data)
