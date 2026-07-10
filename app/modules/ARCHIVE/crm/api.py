"""
CRM API Routes
RESTful API endpoints for CRM module
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import or_, and_
from app.extensions.core import db
from app.models.crm import (
    Contact, Company, Lead, Deal, Activity, Task, Note,
    ContactStatus, DealStage, ActivityType, TaskStatus
)
from app.utils.security import sanitize_input, validate_email_format

logger = logging.getLogger(__name__)

# Create API blueprint
crm_api_bp = Blueprint('crm_api', __name__, url_prefix='/api/v1/crm')


# ========== CONTACTS API ==========

@crm_api_bp.route('/contacts', methods=['GET'])
@login_required
def contacts_list_api():
    """List contacts API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        status = request.args.get('status', '').strip()
        owner_id = request.args.get('owner_id', '').strip()
        
        query = Contact.query.filter_by(is_deleted=False)
        
        if search:
            query = query.filter(
                or_(
                    Contact.email.ilike(f'%{search}%'),
                    Contact.first_name.ilike(f'%{search}%'),
                    Contact.last_name.ilike(f'%{search}%')
                )
            )
        
        if status:
            query = query.filter_by(status=status)
        
        if owner_id:
            query = query.filter_by(owner_id=owner_id)
        
        query = query.order_by(Contact.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [contact.to_dict() for contact in pagination.items],
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    
    except Exception as e:
        logger.exception('Error in contacts_list_api')
        return jsonify({'error': 'Failed to fetch contacts'}), 500


@crm_api_bp.route('/contacts', methods=['POST'])
@login_required
def contacts_create_api():
    """Create contact API"""
    try:
        data = request.get_json()
        
        email = sanitize_input(data.get('email', '').strip().lower(), 255)
        first_name = sanitize_input(data.get('first_name', '').strip(), 100)
        last_name = sanitize_input(data.get('last_name', '').strip(), 100)
        phone = sanitize_input(data.get('phone', '').strip(), 50)
        company_id = data.get('company_id')
        owner_id = data.get('owner_id') or current_user.id
        status = data.get('status', ContactStatus.ACTIVE.value)
        
        # Validate email
        if not validate_email_format(email):
            return jsonify({'error': 'Invalid email address'}), 400
        
        # Check if email exists
        if Contact.query.filter_by(email=email, is_deleted=False).first():
            return jsonify({'error': 'Contact with this email already exists'}), 400
        
        # Create contact
        contact = Contact(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            company_id=company_id,
            owner_id=owner_id,
            status=status,
            created_by=current_user.id
        )
        
        db.session.add(contact)
        db.session.commit()
        
        return jsonify(contact.to_dict()), 201
    
    except Exception as e:
        logger.exception('Error in contacts_create_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to create contact'}), 500


@crm_api_bp.route('/contacts/<uuid:contact_id>', methods=['GET'])
@login_required
def contacts_get_api(contact_id):
    """Get contact API"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        return jsonify(contact.to_dict())
    
    except Exception as e:
        logger.exception('Error in contacts_get_api')
        return jsonify({'error': 'Contact not found'}), 404


@crm_api_bp.route('/contacts/<uuid:contact_id>', methods=['PATCH'])
@login_required
def contacts_update_api(contact_id):
    """Update contact API"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        data = request.get_json()
        
        # Update fields
        if 'email' in data:
            email = sanitize_input(data['email'].strip().lower(), 255)
            if email != contact.email:
                if not validate_email_format(email):
                    return jsonify({'error': 'Invalid email address'}), 400
                if Contact.query.filter(Contact.email == email, Contact.id != contact.id, Contact.is_deleted == False).first():
                    return jsonify({'error': 'Email already exists'}), 400
                contact.email = email
        
        if 'first_name' in data:
            contact.first_name = sanitize_input(data['first_name'].strip(), 100)
        if 'last_name' in data:
            contact.last_name = sanitize_input(data['last_name'].strip(), 100)
        if 'phone' in data:
            contact.phone = sanitize_input(data['phone'].strip(), 50)
        if 'company_id' in data:
            contact.company_id = data['company_id']
        if 'owner_id' in data:
            contact.owner_id = data['owner_id']
        if 'status' in data:
            contact.status = data['status']
        
        contact.updated_by = current_user.id
        db.session.commit()
        
        return jsonify(contact.to_dict())
    
    except Exception as e:
        logger.exception('Error in contacts_update_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to update contact'}), 500


@crm_api_bp.route('/contacts/<uuid:contact_id>', methods=['DELETE'])
@login_required
def contacts_delete_api(contact_id):
    """Delete contact API (soft delete)"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        contact.soft_delete()
        db.session.commit()
        
        return jsonify({'message': 'Contact deleted successfully'}), 200
    
    except Exception as e:
        logger.exception('Error in contacts_delete_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to delete contact'}), 500


@crm_api_bp.route('/contacts/<uuid:contact_id>/timeline', methods=['GET'])
@login_required
def contacts_timeline_api(contact_id):
    """Get contact activity timeline"""
    try:
        contact = Contact.query.filter_by(id=contact_id, is_deleted=False).first_or_404()
        
        activities = Activity.query.filter_by(contact_id=contact_id).order_by(Activity.created_at.desc()).limit(50).all()
        
        return jsonify({
            'contact_id': str(contact_id),
            'activities': [activity.to_dict() for activity in activities]
        })
    
    except Exception as e:
        logger.exception('Error in contacts_timeline_api')
        return jsonify({'error': 'Failed to fetch timeline'}), 500


# ========== DEALS API ==========

@crm_api_bp.route('/deals', methods=['GET'])
@login_required
def deals_list_api():
    """List deals API"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        stage = request.args.get('stage', '').strip()
        owner_id = request.args.get('owner_id', '').strip()
        
        query = Deal.query.filter_by(is_deleted=False)
        
        if stage:
            query = query.filter_by(stage=stage)
        
        if owner_id:
            query = query.filter_by(owner_id=owner_id)
        
        query = query.order_by(Deal.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'data': [deal.to_dict() for deal in pagination.items],
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages
            }
        })
    
    except Exception as e:
        logger.exception('Error in deals_list_api')
        return jsonify({'error': 'Failed to fetch deals'}), 500


@crm_api_bp.route('/deals', methods=['POST'])
@login_required
def deals_create_api():
    """Create deal API"""
    try:
        data = request.get_json()
        
        name = sanitize_input(data.get('name', '').strip(), 255)
        contact_id = data.get('contact_id')
        company_id = data.get('company_id')
        value = float(data.get('value', 0))
        currency = data.get('currency', 'USD')
        stage = data.get('stage', DealStage.LEAD.value)
        probability = int(data.get('probability', 0))
        owner_id = data.get('owner_id') or current_user.id
        
        if not name:
            return jsonify({'error': 'Deal name is required'}), 400
        
        # Parse expected_close_date if provided
        expected_close_date = None
        if data.get('expected_close_date'):
            from datetime import datetime
            try:
                expected_close_date = datetime.strptime(data['expected_close_date'], '%Y-%m-%d').date()
            except:
                pass
        
        # Create deal
        deal = Deal(
            name=name,
            contact_id=contact_id,
            company_id=company_id,
            value=value,
            currency=currency,
            stage=stage,
            probability=probability,
            expected_close_date=expected_close_date,
            owner_id=owner_id,
            created_by=current_user.id
        )
        
        db.session.add(deal)
        db.session.commit()
        
        return jsonify(deal.to_dict()), 201
    
    except Exception as e:
        logger.exception('Error in deals_create_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to create deal'}), 500


@crm_api_bp.route('/deals/<uuid:deal_id>', methods=['GET'])
@login_required
def deals_get_api(deal_id):
    """Get deal API"""
    try:
        deal = Deal.query.filter_by(id=deal_id, is_deleted=False).first_or_404()
        return jsonify(deal.to_dict())
    
    except Exception as e:
        logger.exception('Error in deals_get_api')
        return jsonify({'error': 'Deal not found'}), 404


@crm_api_bp.route('/deals/<uuid:deal_id>', methods=['PATCH'])
@login_required
def deals_update_api(deal_id):
    """Update deal API"""
    try:
        deal = Deal.query.filter_by(id=deal_id, is_deleted=False).first_or_404()
        data = request.get_json()
        
        # Update fields
        if 'name' in data:
            deal.name = sanitize_input(data['name'].strip(), 255)
        if 'contact_id' in data:
            deal.contact_id = data['contact_id']
        if 'company_id' in data:
            deal.company_id = data['company_id']
        if 'value' in data:
            deal.value = float(data['value'])
        if 'currency' in data:
            deal.currency = data['currency']
        if 'stage' in data:
            deal.stage = data['stage']
        if 'probability' in data:
            deal.probability = int(data['probability'])
        if 'expected_close_date' in data:
            if data['expected_close_date']:
                from datetime import datetime
                try:
                    deal.expected_close_date = datetime.strptime(data['expected_close_date'], '%Y-%m-%d').date()
                except:
                    pass
            else:
                deal.expected_close_date = None
        
        deal.updated_by = current_user.id
        db.session.commit()
        
        return jsonify(deal.to_dict())
    
    except Exception as e:
        logger.exception('Error in deals_update_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to update deal'}), 500


@crm_api_bp.route('/deals/pipeline', methods=['GET'])
@login_required
def deals_pipeline_api():
    """Get pipeline view API"""
    try:
        stages = [DealStage.LEAD.value, DealStage.QUALIFIED.value, DealStage.PROPOSAL.value,
                 DealStage.NEGOTIATION.value, DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value]
        
        pipeline_data = {}
        for stage in stages:
            deals = Deal.query.filter_by(stage=stage, is_deleted=False).order_by(Deal.expected_close_date.asc()).all()
            pipeline_data[stage] = {
                'deals': [deal.to_dict() for deal in deals],
                'count': len(deals),
                'total_value': sum(float(d.value) for d in deals),
                'weighted_value': sum(d.weighted_value for d in deals)
            }
        
        # Calculate summary
        total_value = sum(stage['total_value'] for stage in pipeline_data.values())
        weighted_value = sum(stage['weighted_value'] for stage in pipeline_data.values())
        total_deals = sum(stage['count'] for stage in pipeline_data.values())
        
        return jsonify({
            'stages': pipeline_data,
            'summary': {
                'total_value': total_value,
                'weighted_value': weighted_value,
                'total_deals': total_deals
            }
        })
    
    except Exception as e:
        logger.exception('Error in deals_pipeline_api')
        return jsonify({'error': 'Failed to fetch pipeline'}), 500


@crm_api_bp.route('/deals/<uuid:deal_id>/stage', methods=['PATCH'])
@login_required
def deals_update_stage_api(deal_id):
    """Update deal stage API"""
    try:
        deal = Deal.query.filter_by(id=deal_id, is_deleted=False).first_or_404()
        data = request.get_json()
        
        new_stage = data.get('stage')
        if new_stage not in [s.value for s in DealStage]:
            return jsonify({'error': 'Invalid stage'}), 400
        
        old_stage = deal.stage
        deal.stage = new_stage
        deal.updated_by = current_user.id
        
        # If closing, set actual_close_date
        if new_stage in [DealStage.CLOSED_WON.value, DealStage.CLOSED_LOST.value]:
            from datetime import date
            deal.actual_close_date = date.today()
        
        db.session.commit()
        
        return jsonify(deal.to_dict())
    
    except Exception as e:
        logger.exception('Error in deals_update_stage_api')
        db.session.rollback()
        return jsonify({'error': 'Failed to update deal stage'}), 500
