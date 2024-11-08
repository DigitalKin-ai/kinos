from flask import render_template, redirect, url_for
from utils.decorators import safe_operation
from utils.error_handler import ErrorHandler
from utils.exceptions import ResourceNotFoundError, ServiceError
from utils.logger import Logger

def register_view_routes(app, web_instance):
    """Register all view-related routes"""
    logger = Logger()
    @app.route('/')
    def home():
        return redirect(url_for('editor_interface'))

    @app.route('/editor')
    @safe_operation()
    def editor_interface():
        try:
            logger.log("Loading editor interface", level="info")
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi")
            
            return render_template('editor.html',
                                 content=content or "",
                                 suivi_content=suivi_content or "")
        except Exception as e:
            logger.log(f"Error loading editor: {str(e)}", level="error")
            return ErrorHandler.handle_error(e)

    @app.route('/agents')
    def agents_page():
        return render_template('agents.html')

    @app.route('/clean')
    @safe_operation()
    def clean_interface():
        try:
            logger.log("Loading clean interface", level="info")
            mission = web_instance.mission_service.get_current_mission()
            
            if not mission:
                logger.log("No mission selected", level="warning")
                raise ResourceNotFoundError("No mission selected")
                
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi")
            demande_content = web_instance.file_manager.read_file("demande")
            
            logger.log("Clean interface loaded successfully", level="success")
            return render_template('clean.html',
                                 content=content or "",
                                 suivi_content=suivi_content or "",
                                 demande_content=demande_content or "")
                                 
        except Exception as e:
            logger.log(f"Error loading clean interface: {str(e)}", level="error")
            return ErrorHandler.handle_error(e)
