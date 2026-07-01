"""
Main Application API Routes
Core application routes (index, simple dashboard)
"""

import logging
from flask import Blueprint, jsonify

main_api_bp = Blueprint('main_api', __name__)
logger = logging.getLogger(__name__)


@main_api_bp.route('/health', methods=['GET'])
def health_check():
    try:
        stats = 'OK'
        return jsonify({
            'status': 'success',
            'data': f'{str(stats)}'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get health stats: {str(e)}'
        }), 500


@main_api_bp.route('/data/storage/stats', methods=['GET'])
def get_storage_stats():
    """Get storage statistics for all data directories"""
    try:
        stats = 'good'
        return jsonify({
            'status': 'success',
            'data': f'{str(stats)}'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'Failed to get storage stats: {str(e)}'
        }), 500
