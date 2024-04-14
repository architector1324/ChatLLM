import json
import ollama
import random
import flet


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


class ChatLLM:
    def __init__(self, page, settings, topics):
        self.page = page

        self.settings = settings
        self.topics = topics

        self.model = None

        self.chat = []

        self._init_sidebar()
        self._init_chat()

        self.page.add(flet.Row(controls=[self.sidebar_frame, self.chat_main_frame], alignment=flet.MainAxisAlignment.START))

    def _init_sidebar(self):
        self.model_box = flet.Dropdown(options=[flet.dropdown.Option(m) for m in Model.get_models()], on_change=self.model_selected)
        self.model_load = flet.ElevatedButton(text='Load', on_click=self.model_load_clicked, disabled=True)

        self.model_row = flet.Row(controls=[self.model_box, self.model_load])
        self.generate_suggesions_check = flet.Switch(label='Generate suggestions')

        tmp = flet.Column(controls=[self.model_row, self.generate_suggesions_check], alignment=flet.alignment.center)

        self.sidebar_frame = flet.Container(content=tmp, alignment=flet.alignment.center, border_radius=flet.border_radius.all(10), bgcolor=flet.colors.GREY_900, height=700)

    def _init_chat(self):
        self.prompt_entry = flet.TextField(value='', width=770, label='prompt', multiline=True, hint_text=random.choice(self.topics[self.settings['lang']])['prompt'], text_align=flet.TextAlign.LEFT)
        self.prompt_go = flet.ElevatedButton(text='Go', on_click=self.prompt_go_clicked, disabled=True)

        self.prompt_frame = flet.Row(controls=[self.prompt_entry, self.prompt_go], alignment=flet.alignment.center)

        self.chat_entries = flet.Column(alignment=flet.alignment.center)
        self.chat_frame = flet.Container(content=self.chat_entries, alignment=flet.alignment.center, border_radius=flet.border_radius.all(10), bgcolor=flet.colors.GREY_900, width=850, height=635)

        self.chat_main_frame = flet.Column(controls=[self.chat_frame, self.prompt_frame], alignment=flet.alignment.center)

    def add_chat_entry(self, e):
        prompt = e['msg']

        entry_text = flet.Markdown(value=prompt, selectable=True, extension_set=flet.MarkdownExtensionSet.GITHUB_WEB, on_tap_link=lambda e: self.page.launch_url(e.data))
        entry_text_container = flet.Container(content=entry_text, alignment=flet.alignment.center, border_radius=flet.border_radius.all(10), bgcolor=flet.colors.GREY_800)
        entry_row = flet.Column(controls=[entry_text_container], alignment=flet.alignment.center, scroll=flet.ScrollMode.ALWAYS)

        self.chat_entries.controls.append(entry_row)
        self.page.update()

    def update_last_chat_entry(self, e):
        msg = e['msg']

        self.chat_entries.controls[-1].controls[0].content.value = msg
        self.page.update()

    def prompt_go_clicked(self, e):
        prompt = self.prompt_entry.value

        self.chat.append({'who': 'user', 'msg': prompt})

        self.add_chat_entry(self.chat[-1])
        self.prompt_entry.value = None
        self.page.update()

        self.chat.append({'who': 'ai', 'msg': 'AI:'})
        self.add_chat_entry(self.chat[-1])

        stream = self.model.prompt_stream(prompt)

        for t in stream:
            # if not self.answering:
            #     stream.close()
            #     break

            self.chat[-1]['msg'] += t['response']
            self.update_last_chat_entry(self.chat[-1])

    def model_selected(self, e):
        self.model_load.disabled = False
        self.page.update()

    def model_load_clicked(self, e):
        self.model = Model(self.model_box.value, self.settings['lang'])
        self.prompt_go.disabled = False
        self.page.update()

        print(f'Loaded model: {self.model.name}')


def main(page: flet.Page):
    page.title = 'ChatLLM'

    # settings
    settings = json.load(open('settings.json', 'r'))
    topics = json.load(open('topics.json', 'r'))

    ChatLLM(page, settings, topics)


flet.app(target=main, name='ChatLLM', view=flet.FLET_APP)
