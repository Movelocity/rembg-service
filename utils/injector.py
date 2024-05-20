import gradio as gr
import os

current_directory = os.path.dirname(os.path.abspath(__file__))

gradioTemplateResponseOriginal = gr.routes.templates.TemplateResponse
def inject_template():
    with open(f'{current_directory}/index.js', 'r', encoding='utf-8') as f:
        js = f'<script type="text/javascript">{f.read()}</script>\n'
    with open(f'{current_directory}/index.css', 'r', encoding='utf-8') as f:
        css = f'<style>{f.read()}</style>'
    def template_response(*args, **kwargs):
        res = gradioTemplateResponseOriginal(*args, **kwargs)
        res.body = res.body.replace(b'</head>', f'{js}</head>'.encode("utf8"))
        res.body = res.body.replace(b'</body>', f'{css}</body>'.encode("utf8"))
        res.init_headers()
        return res
    gr.routes.templates.TemplateResponse = template_response
    print('> load custom js and css')
    