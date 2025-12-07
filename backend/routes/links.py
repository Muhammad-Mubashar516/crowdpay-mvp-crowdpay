from flask import Blueprint, request, jsonify
from services.supabase_client import supabase
import uuid
from datetime import datetime


links_bp = Blueprint('links', __name__)


@links_bp.route('/create', methods=['POST'])
def create_link():
    data = request.get_json() or {}
    required = ['title']
    for f in required:
        if f not in data:
            return jsonify({'error': f'{f} required'}), 400

    slug = data.get('slug') or f"{data['title'].lower().replace(' ','-')}-{str(uuid.uuid4())[:8]}"
    rec = {
        'owner_id': data.get('owner_id'),
        'slug': slug,
        'title': data.get('title'),
        'description': data.get('description'),
        'cover_url': data.get('cover_url'),
        'goal_kes': data.get('goal_kes'),
        'goal_btc': data.get('goal_btc'),
        'visibility': data.get('visibility','public'),
        'theme': data.get('theme') or {},
        'end_date': data.get('end_date')
    }

    try:
        res = supabase.table('payment_links').insert(rec).execute()
        return jsonify({'link': f"/l/{slug}", 'record': res.data[0]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@links_bp.route('/<slug>', methods=['GET'])
def get_link(slug):
    res = supabase.table('payment_links').select('*').eq('slug', slug).limit(1).execute()
    if res.data and len(res.data) > 0:
        return jsonify(res.data[0])
    return jsonify({'error': 'not found'}), 404