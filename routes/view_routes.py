from flask import render_template, redirect, url_for
from utils.decorators import safe_operation

def register_view_routes(app, web_instance):
    @app.route('/')
    def home():
        return redirect(url_for('editor_interface'))

    @app.route('/editor')
    @safe_operation()
    def editor_interface():
        content = web_instance.file_manager.read_file("production")
        suivi_content = web_instance.file_manager.read_file("suivi")
        return render_template('editor.html',
                             content=content or "",
                             suivi_content=suivi_content or "")

    @app.route('/agents')
    def agents_page():
        return render_template('agents.html')

    @app.route('/clean')
    @safe_operation()
    def clean_interface():
        mission = web_instance.mission_service.get_current_mission()
        if not mission:
            return "No mission selected.", 404
            
        content = web_instance.file_manager.read_file("production")
        suivi_content = web_instance.file_manager.read_file("suivi")
        demande_content = web_instance.file_manager.read_file("demande")
        
        return render_template('clean.html',
                             content=content or "",
                             suivi_content=suivi_content or "",
                             demande_content=demande_content or "")
