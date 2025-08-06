"""Make into package and house helper functions"""

def register_routes(app):
    """
    CENTRAL CONTROLLER
    Imports and registers all the blueprint routes for the application.
    This is the single entry point for all route registration.
    """

    # Register the OLD, non-Blueprint routes
    from .legacy_routes import register_legacy_routes # pylint: disable=import-outside-toplevel
    register_legacy_routes(app)

    # Register the NEW, Bluerprint-based routes
    from .auth_routes import auth_bp # pylint: disable=import-outside-toplevel
    app.register_blueprint(auth_bp)
