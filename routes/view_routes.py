from flask import render_template, redirect, url_for

def register_view_routes(app, web_instance):
    @app.route('/')
    def home():
        return redirect(url_for('editor_interface'))

    @app.route('/editor')
    def editor_interface():
        return web_instance.editor_interface()

    @app.route('/agents')
    def agents_page():
        return render_template('agents.html')

    @app.route('/clean')
    def clean_interface():
        return web_instance.clean_interface()
