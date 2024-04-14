import json
import ollama
import random
import customtkinter as gui


def str_chunks(s, w):
    lines = []

    tmp = ''

    for c in s:
        if c == '\n':
            tmp += ' ' * (w - len(tmp))
        else:
            tmp += c

        if len(tmp) >= w or c == '\n':
            lines.append(tmp)
            tmp = ''

    if tmp:
        lines.append(tmp)
        tmp = ''
    return lines

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


class ChatLLM(gui.CTk):
    def __init__(self, settings, topics):
        super().__init__()

        self.settings = settings
        self.topics = topics

        self.model = None

        self.chat = []
        self.chat_entries = []
        self.answering = False

        self.title('ChatLLM')
        self.geometry('1280x720')
        self.resizable(True, True)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        self._init_side_panel()
        self._init_chat()

    def _init_side_panel(self):
        self.side_panel_frame = gui.CTkFrame(self)
        self.side_panel_frame.grid(row=0, column=0, padx=20, pady=20, sticky='nsw', rowspan=2)

        self.model_box = gui.CTkComboBox(self.side_panel_frame, values=Model.get_models())
        self.model_box.grid(row=0, column=0, padx=20, pady=20)

        self.model_load = gui.CTkButton(self.side_panel_frame, text='load', width=40, command=lambda: self.load_model_cb(self.model_box.get()))
        self.model_load.grid(row=0, column=1, padx=(0, 20), pady=20)

        self.theme_box = gui.CTkOptionMenu(self.side_panel_frame, values=['dark', 'light'], command=self.select_theme_cb)
        self.theme_box.grid(row=1, column=0, padx=20, pady=(0, 20))

        self.generate_suggestions_check = gui.CTkSwitch(self.side_panel_frame, text='generate suggestions', command=self.select_gen_suggestions)
        self.generate_suggestions_check.select()

        if not self.settings['generate suggestions']:
            self.generate_suggestions_check.deselect()

        self.generate_suggestions_check.grid(row=2, column=0, padx=20, pady=(0, 20))

    def _init_chat(self):
        self.chat_main_frame = gui.CTkFrame(self)
        self.chat_main_frame.grid(row=0, column=1, padx=(0, 20), pady=20, stick='nswe')
        self.chat_main_frame.rowconfigure(0, weight=1)
        self.chat_main_frame.columnconfigure(0, weight=1)

        self.prompt_entry = gui.CTkEntry(self.chat_main_frame, corner_radius=20)
        self.prompt_entry.grid(row=1, column=0, padx=(20, 0), pady=20, stick='we')

        self.prompt_go = gui.CTkButton(self.chat_main_frame, text='Go', width=40, command=self.prompt_cb)
        self.prompt_go.grid(row=1, column=1, padx=(10, 20), pady=20)
        self.prompt_go.configure(state='disabled')

        self.chat_frame = gui.CTkScrollableFrame(self.chat_main_frame)
        self.chat_frame.grid(row=0, column=0, padx=20, pady=(20, 0), columnspan=2, stick='nswe')
        self.chat_frame.rowconfigure(0, weight=1)
        self.chat_frame.rowconfigure(1, weight=1)
        self.chat_frame.columnconfigure(0, weight=1)
        self.chat_frame.columnconfigure(1, weight=1)

        self.suggestions_frame = gui.CTkFrame(self.chat_main_frame)
        self.suggestions_frame.grid(row=0, column=0, padx=20, pady=(20, 0), columnspan=2, stick='nswe')
        self.suggestions_frame.rowconfigure(0, weight=1)
        self.suggestions_frame.rowconfigure(1, weight=1)
        self.suggestions_frame.columnconfigure(0, weight=1)
        self.suggestions_frame.columnconfigure(1, weight=1)

    def load_model_cb(self, name):
        print(name)
        self.model = Model(name, settings['lang'])

        self.prompt_go.configure(state='normal')

        if self.chat:
            self.suggestions_frame.grid_remove()
            return

        suggestions = self.model.generate_suggestions() if self.settings['generate suggestions'] else random.sample(self.topics[self.model.lang], 4)

        print(suggestions)

        self.chat_suggestions = []
        for i, s in enumerate(suggestions):
            tmp = gui.CTkButton(self.suggestions_frame, text=s['prompt'], command=lambda i=i: self.select_suggestion(i))
            tmp.grid(row=i%2, column=i//2, padx=20, pady=20, sticky='nswe')
            self.chat_suggestions.append(tmp)

    def select_suggestion(self, i):
        s = self.chat_suggestions[i].cget('text')
        self.prompt_entry.delete(0, 'end')
        self.prompt_entry.insert(0, s)

        for e in self.chat_suggestions:
            e.grid_remove()
            e.destroy()

        self.chat_suggestions.clear()

    def select_theme_cb(self, theme):
        print(theme)
        self.settings['theme'] = theme
        gui.set_appearance_mode(theme)

    def select_gen_suggestions(self):
        self.settings['generate suggestions'] = True if self.generate_suggestions_check.get() else False

    def update_last_chat_entry(self, entry):
        msg = entry['msg']

        self.chat_entries[-1].configure(state='normal')
        self.chat_entries[-1].delete('0.0', 'end')
        self.chat_entries[-1].insert('0.0', msg)
        self.chat_entries[-1].configure(state='disabled')

        height = 28 + 18 * len(str_chunks(msg, 60))

        if self.chat_entries[-1].cget('height') != height:
            self.chat_entries[-1].configure(height=height)

        self.update()

    def add_chat_entry(self, entry):
        self.suggestions_frame.grid_remove()

        height = 28 + 18 * len(str_chunks(entry['msg'], 60))
        tmp = gui.CTkTextbox(self.chat_frame, height=height, corner_radius=15)

        tmp.insert('0.0', entry['msg'])
        tmp.configure(state='disabled')

        tmp.grid(row=len(self.chat_entries), column=1 if entry['who'] == 'user' else 0, padx=10, pady=(10, 0), sticky='wen')

        self.chat_entries.append(tmp)
        self.update()

    def prompt_cb(self):
        prompt = self.prompt_entry.get()

        if not prompt or self.answering:
            print('stop')
            self.prompt_go.configure(text='Go')
            self.prompt_go.configure(fg_color=gui.ThemeManager.theme["CTkButton"]["fg_color"])
            self.prompt_go.configure(hover_color=gui.ThemeManager.theme["CTkButton"]["hover_color"])
            self.answering = False
            return

        print('go')
        self.answering = True

        self.prompt_go.configure(text='Stop')
        self.prompt_go.configure(fg_color='#c42d43')
        self.prompt_go.configure(hover_color='#b71c33')

        self.prompt_entry.delete(0, 'end')

        self.chat.append({'who': 'user', 'msg': prompt})
        self.add_chat_entry(self.chat[-1])

        self.chat.append({'who': 'ai', 'msg': ''})
        self.add_chat_entry(self.chat[-1])

        stream = self.model.prompt_stream(prompt)

        for t in stream:
            if not self.answering:
                stream.close()
                break

            self.chat[-1]['msg'] += t['response']
            self.update_last_chat_entry(self.chat[-1])

        self.answering = False


# settings
settings = json.load(open('settings.json', 'r'))
topics = json.load(open('topics.json', 'r'))

# app
gui.set_appearance_mode(settings['theme'])
gui.set_default_color_theme(settings['color'])

app = ChatLLM(settings, topics)
app.mainloop()
