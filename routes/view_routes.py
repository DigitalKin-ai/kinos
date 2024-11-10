import os
from flask import render_template, redirect, url_for
from utils.decorators import safe_operation
from utils.error_handler import ErrorHandler
from utils.exceptions import ResourceNotFoundError, ServiceError
from utils.logger import Logger
from utils.path_manager import PathManager

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
            # Use FileManager which already uses PathManager
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi")
            
            # Use template path from PathManager
            template_path = os.path.join(PathManager.get_templates_path(), 'editor.html')
            return render_template(template_path,
                                 content=content or "",
                                 suivi_content=suivi_content or "")
        except Exception as e:
            logger.log(f"Error loading editor: {str(e)}", level="error")
            return ErrorHandler.handle_error(e)

    @app.route('/agents')
    def agents_page():
        return render_template('agents.html')

    @app.route('/files')
    def files_page():
        """Render the files interface"""
        try:
            logger.log("Loading files interface", level="info")
            return render_template('files.html')
        except Exception as e:
            logger.log(f"Error loading files interface: {str(e)}", level="error")
            return ErrorHandler.handle_error(e)

    @app.route('/clean')
    @safe_operation()
    def clean_interface():
        try:
            logger.log("Loading clean interface", level="info")
            mission = web_instance.mission_service.get_current_mission()
            
            if not mission:
                logger.log("No mission selected", level="warning")
                raise ResourceNotFoundError("No mission selected")
                
            # Use FileManager which already uses PathManager
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi") 
            demande_content = web_instance.file_manager.read_file("demande")

            logger.log("Clean interface loaded successfully", level="success")
            # Use template path from PathManager
            template_path = os.path.join(PathManager.get_templates_path(), 'clean.html')
            return render_template(template_path,
                                 content=content or "",
                                 suivi_content=suivi_content or "",
                                 demande_content=demande_content or "")
                                 
        except Exception as e:
            logger.log(f"Error loading clean interface: {str(e)}", level="error")
            return ErrorHandler.handle_error(e)
