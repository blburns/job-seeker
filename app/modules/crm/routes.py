"""
CRM Routes
Customer Relationship Management web routes
"""

import logging
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from sqlalchemy import or_, and_, func
from sqlalchemy.orm import joinedload
from app.extensions.core import db
from app.models.auth import User
from app.models.crm import (
    Contact, Company, Lead, Deal, Activity, Task, Note,
    Campaign, Segment, ContactStatus, DealStage, ActivityType, TaskStatus
)
from app.utils.security import sanitize_input, validate_email_format
from . import crm_bp

logger = logging.getLogger(__name__)


@crm_bp.route('/')
@login_required
def index():
    """Redirect to CRM dashboard"""
    return redirect(url_for('crm.dashboard'))


@crm_bp.route('/dashboard')
@login_required
def dashboard():
    """CRM dashboard with overview metrics"""
    try:
        # Get statistics
        total_contacts = Contact.query.filter_by(is_deleted=False).count()
        total_companies = Company.query.filter_by(is_deleted=False).count()
        total_leads = Lead.query.count()
        total_deals = Deal.query.filter_by(is_deleted=False).count()
        
        # Active deals value
        active_deals = Deal.query.filter(
            Deal.stage.in_([DealStage.LEAD.value, DealStage.QUALIFIED.value, 
                           DealStage.PROPOSAL.value, DealStage.NEGOTIATION.value]),
            Deal.is_deleted == False
        ).all()
        total_pipeline_value = sum(float(deal.value) for deal in active_deals)
        weighted_pipeline_value = sum(deal.weighted_value for deal in active_deals)
        
        # Recent activities
        recent_activities = Activity.query.order_by(Activity.created_at.desc()).limit(10).all()
        
        # Upcoming tasks
        from datetime import datetime, timedelta
        upcoming_tasks = Task.query.filter(
            Task.status != TaskStatus.COMPLETED.value,
            Task.due_date >= datetime.utcnow(),
            Task.due_date <= datetime.utcnow() + timedelta(days=7)
        ).order_by(Task.due_date.asc()).limit(10).all()
        
        # Recent deals
        recent_deals = Deal.query.filter_by(is_deleted=False).order_by(Deal.created_at.desc()).limit(5).all()
        
        return render_template('modules/crm/dashboard.html',
                            total_contacts=total_contacts,
                            total_companies=total_companies,
                            total_leads=total_leads,
                            total_deals=total_deals,
                            total_pipeline_value=total_pipeline_value,
                            weighted_pipeline_value=weighted_pipeline_value,
                            recent_activities=recent_activities,
                            upcoming_tasks=upcoming_tasks,
                            recent_deals=recent_deals)
    
    except Exception as e:
        logger.exception('Error in CRM dashboard')
        flash('Error loading CRM dashboard', 'danger')
        return render_template('errors/500.html'), 500


# ========== CONTACTS ==========

@crm_bp.route('/contacts')
@login_required
def contacts_list():
    """List all contacts"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        owner_filter = request.args.get('owner_id', '').strip()
        
        query = Contact.query.filter_by(is_deleted=False)
        
        if search:
            query = query.filter(
                or_(
                    Contact.email.ilike(f'%{search}%'),
                    Contact.first_name.ilike(f'%{search}%'),
                    Contact.last_name.ilike(f'%{search}%')
                )
            )
        
        if status_filter:
            query = query.filter_by(status=status_filter)
        
        if owner_filter:
            query = query.filter_by(owner_id=owner_filter)
        
        query = query.order_by(Contact.created_at.desc())
        contacts = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('modules/crm/contacts/list.html', contacts=contacts, search=search)
    
    except Exception as e:
        logger.exception('Error in contacts_list')
        flash('Error loading contacts', 'danger')
        return render_template('errors/500.html'), 500


@crm_bp.route('/contacts/new', methods=['GET', 'POST'])
@login_required
def contact_new():
    """Create new contact"""
    try:
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email', '').strip().lower(), 255)
            first_name = sanitize_input(request.form.get('first_name', '').strip(), 100)
            last_name = sanitize_input(request.form.get('last_name', '').strip(), 100)
            phone = sanitize_input(request.form.get('phone', '').strip(), 50)
            company_id = request.form.get('company_id', '').strip() or None
            owner_id = request.form.get('owner_id', '').strip() or None
            status = request.form.get('status', ContactStatus.ACTIVE.value).strip()
            
            # Validate email
            if not validate_email_format(email):
                flash('Please enter a valid email address', 'warning')
                return render_template('modules/crm/contacts/new.html')
            
            # Check if email already exists
            if Contact.query.filter_by(email=email, is_deleted=False).first():
                flash('Contact with this email already exists', 'warning')
                return render_template('modules/crm/contacts/new.html')
            
            # Create contact
            contact = Contact(
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                company_id=company_id if company_id else None,
                owner_id=owner_id if owner_id else current_user.id,
                status=status,
                created_by=current_user.id
            )
            
            db.session.add(contact)
            db.session.commit()
            
            flash('Contact created successfully', 'success')
            return redirect(url_for('crm.contact_view', contact_id=contact.id))
        
        # GET request - show form
        companies = Company.query.filter_by(is_deleted=False).order_by(Company.name).all()
        users = User.query.filter_by(is_active=True).order_by(User.display_name).all()
        
        return render_template('modules/crm/contacts/new.html', companies=companies, users=users)
    
    except Exception as e:
        logger.exception('Error in contact_new')
        db.session.rollback()
        flash('An error occurred while creating contact', 'danger')
        return render_template('modules/crm/contacts/new.html'), 500


@crm_bp.route('/contacts/<uuid:contact_id>')
@login_required
def contact_view(contact_id):
    """View contact details"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        
        # Get related data
        activities = Activity.query.filter_by(contact_id=contact_id).order_by(Activity.created_at.desc()).limit(20).all()
        tasks = Task.query.filter_by(contact_id=contact_id).order_by(Task.due_date.asc()).all()
        deals = Deal.query.filter_by(contact_id=contact_id, is_deleted=False).all()
        notes = Note.query.filter_by(contact_id=contact_id, is_deleted=False).order_by(Note.created_at.desc()).all()
        
        return render_template('modules/crm/contacts/view.html',
                            contact=contact,
                            activities=activities,
                            tasks=tasks,
                            deals=deals,
                            notes=notes)
    
    except Exception as e:
        logger.exception('Error in contact_view')
        return render_template('errors/500.html'), 500


@crm_bp.route('/contacts/<uuid:contact_id>/edit', methods=['GET', 'POST'])
@login_required
def contact_edit(contact_id):
    """Edit contact"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email', '').strip().lower(), 255)
            first_name = sanitize_input(request.form.get('first_name', '').strip(), 100)
            last_name = sanitize_input(request.form.get('last_name', '').strip(), 100)
            phone = sanitize_input(request.form.get('phone', '').strip(), 50)
            company_id = request.form.get('company_id', '').strip() or None
            owner_id = request.form.get('owner_id', '').strip() or None
            status = request.form.get('status', ContactStatus.ACTIVE.value).strip()
            
            # Validate email if changed
            if email != contact.email:
                if not validate_email_format(email):
                    flash('Please enter a valid email address', 'warning')
                    return render_template('modules/crm/contacts/edit.html', contact=contact)
                
                if Contact.query.filter(Contact.email == email, Contact.id != contact.id, Contact.is_deleted == False).first():
                    flash('Contact with this email already exists', 'warning')
                    return render_template('modules/crm/contacts/edit.html', contact=contact)
                
                contact.email = email
            
            # Update contact
            contact.first_name = first_name
            contact.last_name = last_name
            contact.phone = phone
            contact.company_id = company_id if company_id else None
            contact.owner_id = owner_id if owner_id else current_user.id
            contact.status = status
            contact.updated_by = current_user.id
            contact.updated_at = db.func.now()
            
            db.session.commit()
            flash('Contact updated successfully', 'success')
            return redirect(url_for('crm.contact_view', contact_id=contact.id))
        
        # GET request
        companies = Company.query.filter_by(is_deleted=False).order_by(Company.name).all()
        users = User.query.filter_by(is_active=True).order_by(User.display_name).all()
        
        return render_template('modules/crm/contacts/edit.html', contact=contact, companies=companies, users=users)
    
    except Exception as e:
        logger.exception('Error in contact_edit')
        db.session.rollback()
        flash('An error occurred while updating contact', 'danger')
        return redirect(url_for('crm.contact_view', contact_id=contact_id)), 500


# ========== COMPANIES ==========

@crm_bp.route('/companies')
@login_required
def companies_list():
    """List all companies"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search = request.args.get('search', '').strip()
        
        query = Company.query.filter_by(is_deleted=False)
        
        if search:
            query = query.filter(Company.name.ilike(f'%{search}%'))
        
        query = query.order_by(Company.name.asc())
        companies = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('modules/crm/companies/list.html', companies=companies, search=search)
    
    except Exception as e:
        logger.exception('Error in companies_list')
        flash('Error loading companies', 'danger')
        return render_template('errors/500.html'), 500


@crm_bp.route('/companies/new', methods=['GET', 'POST'])
@login_required
def company_new():
    """Create new company"""
    try:
        if request.method == 'POST':
            name = sanitize_input(request.form.get('name', '').strip(), 255)
            industry = sanitize_input(request.form.get('industry', '').strip(), 100)
            website = sanitize_input(request.form.get('website', '').strip(), 255)
            phone = sanitize_input(request.form.get('phone', '').strip(), 50)
            owner_id = request.form.get('owner_id', '').strip() or None
            
            if not name:
                flash('Company name is required', 'warning')
                return render_template('modules/crm/companies/new.html')
            
            # Create company
            company = Company(
                name=name,
                industry=industry if industry else None,
                website=website if website else None,
                phone=phone if phone else None,
                owner_id=owner_id if owner_id else current_user.id,
                created_by=current_user.id
            )
            
            db.session.add(company)
            db.session.commit()
            
            flash('Company created successfully', 'success')
            return redirect(url_for('crm.company_view', company_id=company.id))
        
        # GET request
        users = User.query.filter_by(is_active=True).order_by(User.display_name).all()
        return render_template('modules/crm/companies/new.html', users=users)
    
    except Exception as e:
        logger.exception('Error in company_new')
        db.session.rollback()
        flash('An error occurred while creating company', 'danger')
        return render_template('modules/crm/companies/new.html'), 500


@crm_bp.route('/companies/<uuid:company_id>')
@login_required
def company_view(company_id):
    """View company details"""
    try:
        company = Company.query.filter_by(id=company_id, is_deleted=False).first_or_404()
        
        # Get related data
        contacts = Contact.query.filter_by(company_id=company_id, is_deleted=False).all()
        deals = Deal.query.filter_by(company_id=company_id, is_deleted=False).all()
        
        return render_template('modules/crm/companies/view.html',
                            company=company,
                            contacts=contacts,
                            deals=deals)
    
    except Exception as e:
        logger.exception('Error in company_view')
        return render_template('errors/500.html'), 500


# ========== DEALS ==========

@crm_bp.route('/deals')
@login_required
def deals_list():
    """List all deals"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        stage_filter = request.args.get('stage', '').strip()
        
        query = Deal.query.filter_by(is_deleted=False)
        
        if stage_filter:
            query = query.filter_by(stage=stage_filter)
        
        query = query.order_by(Deal.created_at.desc())
        deals = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('modules/crm/deals/list.html', deals=deals, stage_filter=stage_filter)
    
    except Exception as e:
        logger.exception('Error in deals_list')
        flash('Error loading deals', 'danger')
        return render_template('errors/500.html'), 500


@crm_bp.route('/deals/pipeline')
@login_required
def deals_pipeline():
    """Deal pipeline Kanban board"""
    try:
        # Get deals grouped by stage
        stages = [DealStage.LEAD.value, DealStage.QUALIFIED.value, DealStage.PROPOSAL.value,
                 DealStage.NEGOTIATION.value, DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value]
        
        pipeline_data = {}
        for stage in stages:
            deals = Deal.query.filter_by(stage=stage, is_deleted=False).order_by(Deal.expected_close_date.asc()).all()
            pipeline_data[stage] = {
                'deals': deals,
                'count': len(deals),
                'total_value': sum(float(d.value) for d in deals),
                'weighted_value': sum(d.weighted_value for d in deals)
            }
        
        return render_template('modules/crm/deals/pipeline.html', pipeline_data=pipeline_data)
    
    except Exception as e:
        logger.exception('Error in deals_pipeline')
        flash('Error loading pipeline', 'danger')
        return render_template('errors/500.html'), 500


@crm_bp.route('/deals/new', methods=['GET', 'POST'])
@login_required
def deal_new():
    """Create new deal"""
    try:
        if request.method == 'POST':
            name = sanitize_input(request.form.get('name', '').strip(), 255)
            contact_id = request.form.get('contact_id', '').strip() or None
            company_id = request.form.get('company_id', '').strip() or None
            value = request.form.get('value', '0').strip()
            currency = request.form.get('currency', 'USD').strip()
            stage = request.form.get('stage', DealStage.LEAD.value).strip()
            probability = int(request.form.get('probability', 0) or 0)
            expected_close_date = request.form.get('expected_close_date', '').strip() or None
            owner_id = request.form.get('owner_id', '').strip() or None
            
            if not name:
                flash('Deal name is required', 'warning')
                return render_template('modules/crm/deals/new.html')
            
            # Parse date
            from datetime import datetime
            close_date = None
            if expected_close_date:
                try:
                    close_date = datetime.strptime(expected_close_date, '%Y-%m-%d').date()
                except:
                    pass
            
            # Create deal
            deal = Deal(
                name=name,
                contact_id=contact_id if contact_id else None,
                company_id=company_id if company_id else None,
                value=float(value),
                currency=currency,
                stage=stage,
                probability=probability,
                expected_close_date=close_date,
                owner_id=owner_id if owner_id else current_user.id,
                created_by=current_user.id
            )
            
            db.session.add(deal)
            db.session.commit()
            
            flash('Deal created successfully', 'success')
            return redirect(url_for('crm.deal_view', deal_id=deal.id))
        
        # GET request
        contacts = Contact.query.filter_by(is_deleted=False).order_by(Contact.first_name, Contact.last_name).all()
        companies = Company.query.filter_by(is_deleted=False).order_by(Company.name).all()
        users = User.query.filter_by(is_active=True).order_by(User.display_name).all()
        
        return render_template('modules/crm/deals/new.html',
                            contacts=contacts,
                            companies=companies,
                            users=users)
    
    except Exception as e:
        logger.exception('Error in deal_new')
        db.session.rollback()
        flash('An error occurred while creating deal', 'danger')
        return render_template('modules/crm/deals/new.html'), 500


@crm_bp.route('/deals/<uuid:deal_id>')
@login_required
def deal_view(deal_id):
    """View deal details"""
    try:
        deal = Deal.query.filter_by(id=deal_id, is_deleted=False).first_or_404()
        
        # Get related data
        activities = Activity.query.filter_by(deal_id=deal_id).order_by(Activity.created_at.desc()).limit(20).all()
        tasks = Task.query.filter_by(deal_id=deal_id).order_by(Task.due_date.asc()).all()
        notes = Note.query.filter_by(deal_id=deal_id, is_deleted=False).order_by(Note.created_at.desc()).all()
        
        return render_template('modules/crm/deals/view.html',
                            deal=deal,
                            activities=activities,
                            tasks=tasks,
                            notes=notes)
    
    except Exception as e:
        logger.exception('Error in deal_view')
        return render_template('errors/500.html'), 500
