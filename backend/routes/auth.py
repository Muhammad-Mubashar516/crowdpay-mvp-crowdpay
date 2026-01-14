from flask import Blueprint, request, jsonify
import logging
from services import get_supabase_client
from . import auth_bp
from pydantic import BaseModel, EmailStr, validator

logger = logging.getLogger(__name__)
supabase = get_supabase_client()


class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters')
        return v


class SignInRequest(BaseModel):
    email: EmailStr
    password: str


def session_to_dict(session):
    """Convert Supabase Session object to JSON-serializable dict"""
    if session is None:
        return None
    return {
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
        "expires_at": getattr(session, "expires_at", None),
        "token_type": getattr(session, "token_type", None)
    }


@auth_bp.route('/signup', methods=['POST'])
def signup():
    """Register a new user using Supabase Auth with duplicate check"""
    try:
        data = request.get_json()
        signup_data = SignUpRequest(**data)

        # Check if user already exists in users table
        existing_user = supabase.table("users").select("*").eq("email", signup_data.email).execute()
        if existing_user.data:
            return jsonify({'error': 'User already exists'}), 409

        # Create user in Supabase Auth
        res = supabase.auth.sign_up({
            "email": signup_data.email,
            "password": signup_data.password
        })

        if res.user is None:
            return jsonify({'error': 'Registration failed'}), 400

        # Save extra user info in your users table
        user_data = {
            "id": res.user.id,
            "email": signup_data.email,
            "full_name": signup_data.full_name
        }
        supabase.table("users").insert(user_data).execute()

        return jsonify({
            "message": "User registered successfully",
            "user": user_data,
            "session": session_to_dict(res.session)
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500


@auth_bp.route('/signin', methods=['POST'])
def signin():
    """Sign in an existing user using Supabase Auth"""
    try:
        data = request.get_json()
        signin_data = SignInRequest(**data)

        res = supabase.auth.sign_in_with_password({
            "email": signin_data.email,
            "password": signin_data.password
        })

        if res.user is None:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Fetch extra user info from users table
        user_resp = supabase.table("users").select("*").eq("id", res.user.id).single().execute()
        user_data = user_resp.data if user_resp.data else {"id": res.user.id, "email": res.user.email}

        return jsonify({
            "message": "Signed in successfully",
            "user": user_data,
            "session": session_to_dict(res.session)
        }), 200

    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        return jsonify({'error': 'Invalid credentials'}), 401


@auth_bp.route('/signout', methods=['POST'])
def signout():
    """Sign out user"""
    try:
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            supabase.auth.sign_out(token)

        return jsonify({'message': 'Signed out successfully'}), 200

    except Exception as e:
        logger.error(f"Signout error: {str(e)}")
        return jsonify({'message': 'Signed out'}), 200


@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current user info"""
    try:
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'No authorization token'}), 401

        token = auth_header.split(' ')[1]
        user_resp = supabase.auth.get_user(token)

        if not user_resp or not user_resp.user:
            return jsonify({'error': 'Invalid token'}), 401

        # Fetch extra user info from users table
        user_data_resp = supabase.table("users").select("*").eq("id", user_resp.user.id).single().execute()
        user_data = user_data_resp.data if user_data_resp.data else {"id": user_resp.user.id, "email": user_resp.user.email}

        return jsonify({'user': user_data}), 200

    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({'error': 'Failed to get user'}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """Refresh access token"""
    try:
        data = request.get_json()
        refresh_token = data.get('refresh_token')

        if not refresh_token:
            return jsonify({'error': 'Refresh token required'}), 400

        result = supabase.auth.refresh_session(refresh_token)

        return jsonify({
            'message': 'Token refreshed',
            'session': session_to_dict(result.session) if result else None
        }), 200

    except Exception as e:
        logger.error(f"Refresh error: {str(e)}")
        return jsonify({'error': 'Failed to refresh token'}), 401
