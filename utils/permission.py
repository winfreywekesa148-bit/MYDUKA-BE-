from functools import wraps

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt


def role_required(*allowed_roles):
    """
    Restrict access to users with specific roles.

    Example:
        @role_required("merchant")

    Or:
        @role_required("merchant", "admin")
    """

    def decorator(function):

        @wraps(function)
        @jwt_required()
        def wrapper(*args, **kwargs):

            # Get information stored inside the JWT
            claims = get_jwt()

            # Get the user's role
            user_role = claims.get("role")

            # Check whether the user's role is allowed
            if user_role not in allowed_roles:
                return jsonify({
                    "error": "Access denied",
                    "message": "You do not have permission to access this resource."
                }), 403

            # User has permission
            return function(*args, **kwargs)

        return wrapper

    return decorator