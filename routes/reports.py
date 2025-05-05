from flask import Blueprint, render_template, redirect, url_for, session, flash
from models import db, Greenhouse, Issue # Import necessary models
from datetime import datetime

reports_bp = Blueprint('reports', __name__, template_folder='../templates')

@reports_bp.route('/reports')
def show_reports(): # Renamed function
    if 'user_id' not in session:
        flash('Please log in to access this page.', 'warning')
        return redirect(url_for('auth.login'))
    
    # Calculate various report statistics
    total_greenhouses = Greenhouse.query.count()
    current_issues = Issue.query.filter(Issue.status != 'resolved').count()
    
    # Issues by type
    issue_types = db.session.query(Issue.issue_type, db.func.count(Issue.id)).\
        group_by(Issue.issue_type).all()
    issue_types_dict = {t[0]: t[1] for t in issue_types}
    
    # Issues by status
    issue_statuses = db.session.query(Issue.status, db.func.count(Issue.id)).\
        group_by(Issue.status).all()
    issue_statuses_dict = {s[0]: s[1] for s in issue_statuses}
    
    # Average resolution time
    resolved_issues = Issue.query.filter(Issue.status == 'resolved', Issue.resolved_at != None).all()
    
    avg_resolution_time = 0
    if resolved_issues:
        total_resolution_time_seconds = sum([(issue.resolved_at - issue.created_at).total_seconds() for issue in resolved_issues])
        avg_resolution_time = total_resolution_time_seconds / len(resolved_issues) / 3600  # in hours
    
    # Recent issues (last 10)
    recent_issues = Issue.query.order_by(Issue.created_at.desc()).limit(10).all()
    
    return render_template('reports.html', 
                          total_greenhouses=total_greenhouses,
                          current_issues=current_issues,
                          issue_types=issue_types_dict,
                          issue_statuses=issue_statuses_dict,
                          avg_resolution_time=round(avg_resolution_time, 2),
                          recent_issues=recent_issues)
