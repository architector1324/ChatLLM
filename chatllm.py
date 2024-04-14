import json
import random

import flet as ft
import ollama


class Model:
    PROMPTS_SUGGESTION = {
        'en': 'generate 2 simple and 2 interesting prompts (about 12 words) to ChatGPT. Use json schema [{"prompt":"string", "topic":"string"}]',
        'ru': 'придумай 2 простых и 2 интересных промпта (не больше 12 слов) для ChatGPT на русском языке. Используй json schema [{"prompt":"string", "topic":"string"}]'
    }

    def get_models():
        return [m['name'] for m in ollama.list()['models']]

    def __init__(self, name, lang='en'):
        self.name = name
        self.lang = lang

    def generate_suggestions(self):
        res = ollama.generate(model=self.name, prompt=Model.PROMPTS_SUGGESTION[self.lang])['response']
        return json.loads(res)

    def prompt(self, prompt):
        return ollama.generate(model=self.name, prompt=prompt)['response']

    def prompt_stream(self, prompt):
        return ollama.generate(model=self.name, prompt=prompt, stream=True)


def main(page: ft.Page):
    # settings
    page.title = 'ChatLLM'

    settings = json.load(open('settings.json', 'r'))
    topics = json.load(open('topics.json', 'r'))

    model = None

    # handlers
    def prompt_go_clicked(_e):
        print(model)
        pass

    def model_selected(_e):
        model_load.disabled = False
        page.update()

    def model_load_clicked(_e):
        nonlocal model
        model = Model(model_box.value, settings['lang'])

        prompt_go.disabled = False
        page.snack_bar = ft.SnackBar(content=ft.Text(model_box.value))
        page.snack_bar.open = True

        page.update()


    # app
    model_box = ft.Dropdown(label='model', options=[ft.dropdown.Option(m) for m in Model.get_models()], on_change=model_selected)
    model_load = ft.ElevatedButton(text='Load', on_click=model_load_clicked, disabled=True)
    gen_suggestions_check = ft.Switch(label='Generate suggestions')

    prompt_entry = ft.TextField(value='', label='prompt', multiline=True, hint_text=random.choice(topics[settings['lang']])['prompt'], expand=True)
    prompt_go = ft.ElevatedButton(text='Go', on_click=prompt_go_clicked, disabled=True)

    chat_entries = ft.ListView(expand=True)

    page.add(
        ft.Row([
            model_box,
            model_load,
            gen_suggestions_check,
            ft.IconButton(ft.icons.ABC),
            ft.Icon(ft.icons.ACCOUNT_BOX)
        ]),
        ft.Container(content=chat_entries, border_radius=ft.border_radius.all(10), bgcolor=ft.colors.GREY_900, expand=True),
        ft.Row([prompt_entry, prompt_go])
    )


app = ft.app(target=main)
