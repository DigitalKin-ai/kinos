import os
from flask import render_template, redirect, url_for
from utils.decorators import safe_operation
from utils.error_handler import ErrorHandler
from utils.exceptions import ResourceNotFoundError, ServiceError
from utils.logger import Logger
from utils.path_manager import PathManager

import os
from flask import send_from_directory

def register_view_routes(app, web_instance):
    """Register all view-related routes"""
    logger = Logger()

    @app.route('/favicon.ico')
    def favicon():
        """Serve favicon from static directory"""
        try:
            return send_from_directory(
                os.path.join(PathManager.get_static_path()),
                'favicon.ico', 
                mimetype='image/x-icon'
            )
        except Exception as e:
            logger.log(f"Favicon error: {str(e)}", 'error')
            return '', 404
    @app.route('/', endpoint='home')
    def home():
        return redirect(url_for('editor_interface'))

    @app.route('/editor', endpoint='editor_interface')
    @safe_operation()
    def editor_interface():
        try:
            logger.log("Loading editor interface", "info")
            # Use FileManager which already uses PathManager
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi")
            
            # Use template path from PathManager 
            template_path = os.path.join(PathManager.get_templates_path(), 'editor.html')
            return render_template(template_path,
                                 content=content or "",
                                 suivi_content=suivi_content or "")
        except Exception as e:
            logger.log(f"Error loading editor: {str(e)}", "error")
            return ErrorHandler.handle_error(e)

    @app.route('/agents', endpoint='agents_page')
    def agents_page():
        try:
            # Access currentMission property directly
            current_mission = web_instance.mission_service.currentMission if hasattr(web_instance, 'mission_service') else None
            
            return render_template('agents.html', 
                                   current_mission=current_mission, 
                                   teams=[])  # Pass an empty list of teams as a default
        except Exception as e:
            # Log the error
            logger.log(f"Error rendering agents page: {str(e)}", 'error')
            return render_template('agents.html', teams=[], error=str(e))

    @app.route('/files', endpoint='files_page')
    def files_page():
        """Render the files interface"""
        try:
            logger.log("Loading files interface", "info")
            return render_template('files.html')
        except Exception as e:
            logger.log(f"Error loading files interface: {str(e)}", "error")
            return ErrorHandler.handle_error(e)

    @app.route('/teams', endpoint='teams_page')
    def teams_page():
        """Render the teams management interface"""
        try:
            logger.log("Loading teams interface", "info")
            return render_template('teams.html')
        except Exception as e:
            logger.log(f"Error loading teams interface: {str(e)}", "error")
            return ErrorHandler.handle_error(e)

    @app.route('/clean', endpoint='clean_interface')
    @safe_operation()
    def clean_interface():
        try:
            logger.log("Loading clean interface", "info")
            mission = web_instance.mission_service.get_current_mission()
            
            if not mission:
                logger.log("No mission selected", "warning")
                raise ResourceNotFoundError("No mission selected")
                
            # Use FileManager which already uses PathManager
            content = web_instance.file_manager.read_file("production")
            suivi_content = web_instance.file_manager.read_file("suivi") 
            demande_content = web_instance.file_manager.read_file("demande")

            logger.log("Clean interface loaded successfully", "success")
            # Use template path from PathManager
            template_path = os.path.join(PathManager.get_templates_path(), 'clean.html')
            return render_template(template_path,
                                 content=content or "",
                                 suivi_content=suivi_content or "",
                                 demande_content=demande_content or "")
                                 
        except Exception as e:
            logger.log(f"Error loading clean interface: {str(e)}", "error")
            return ErrorHandler.handle_error(e)
