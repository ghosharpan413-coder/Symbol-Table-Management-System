import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import re
import csv
import math

KEYWORDS = set('auto break case char const continue default do double else enum extern float for goto if int long register return short signed sizeof static struct switch typedef union unsigned void volatile while inline restrict _Bool _Complex _Imaginary'.split())

class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def validate(self, name, dtype, value):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', name) or name in KEYWORDS:
            raise ValueError('Enter a valid, non-keyword C identifier.')
        if not value:
            return
        try:
            if dtype == 'int':
                if not re.fullmatch(r'[+-]?[0-9]+', value):
                    raise ValueError()
            elif dtype in ('float', 'double'):
                if not math.isfinite(float(value)):
                    raise ValueError()
            elif dtype == 'char' and len(value) != 1:
                raise ValueError()
        except ValueError:
            raise ValueError(f'Invalid value for {dtype}.') from None

    def insert(self, name, dtype, value, scope):
        self.validate(name, dtype, value)
        key = (scope, name)
        if key in self.symbols:
            raise ValueError('Duplicate identifier in the same scope.')
        self.symbols[key] = (dtype, value)

    def search(self, name, scope):
        return self.symbols.get((scope, name))

    def update(self, name, dtype, value, scope):
        self.validate(name, dtype, value)
        if (scope, name) not in self.symbols:
            raise ValueError('Symbol not found.')
        self.symbols[(scope, name)] = (dtype, value)

    def delete(self, name, scope):
        if (scope, name) not in self.symbols:
            raise ValueError('Symbol not found.')
        del self.symbols[(scope, name)]

class Application:
    def __init__(self, root):
        self.root = root
        self.table = SymbolTable()
        root.title('Symbol Table Management System')
        root.geometry('850x620')
        root.minsize(680, 540)
        root.configure(bg='#eef2f7')
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('Treeview', rowheight=30, font=('Segoe UI', 10))
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), background='#dbe5f2')
        style.configure('TButton', padding=7)
        header = tk.Frame(root, bg='#142b49', padx=22, pady=18)
        header.pack(fill='x')
        tk.Label(header, text='Symbol Table Management System', bg='#142b49', fg='white', font=('Segoe UI', 21, 'bold')).pack(anchor='w')
        tk.Label(header, text='Compiler Design | Hashing and Scope Management', bg='#142b49', fg='#c5d7ed', font=('Segoe UI', 11)).pack(anchor='w')
        form = ttk.LabelFrame(root, text='Identifier details', padding=14)
        form.pack(fill='x', padx=20, pady=12)
        self.name = tk.StringVar()
        self.dtype = tk.StringVar(value='int')
        self.value = tk.StringVar()
        self.scope = tk.StringVar(value='Global')
        for i, (label, var, options) in enumerate([
            ('Identifier name', self.name, None), ('Data type', self.dtype, ('int','float','double','char')),
            ('Value (optional)', self.value, None), ('Scope', self.scope, ('Global','Local'))]):
            r, c = divmod(i, 2)
            ttk.Label(form, text=label).grid(row=r*2, column=c, sticky='w', padx=6)
            widget = ttk.Combobox(form, textvariable=var, values=options, state='readonly') if options else ttk.Entry(form, textvariable=var)
            widget.grid(row=r*2+1, column=c, sticky='ew', padx=6, pady=(3,9))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        actions = ttk.Frame(root)
        actions.pack(fill='x', padx=20)
        for label, command in [('Insert',self.insert),('Search',self.search),('Update',self.update),('Delete',self.delete),('Clear Input',self.clear),('Export CSV',self.export)]:
            ttk.Button(actions, text=label, command=command).pack(side='left', expand=True, fill='x', padx=2)
        panel = ttk.Frame(root)
        panel.pack(fill='both', expand=True, padx=20, pady=12)
        self.tree = ttk.Treeview(panel, columns=('name','type','value','scope'), show='headings', selectmode='browse')
        for col, label in [('name','Identifier'),('type','Data Type'),('value','Value'),('scope','Scope')]:
            self.tree.heading(col, text=label)
            self.tree.column(col, width=130, anchor='center')
        scroll = ttk.Scrollbar(panel, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', self.select_row)
        self.status = tk.StringVar(value='Ready')
        self.count = tk.StringVar(value='Total symbols: 0')
        footer = ttk.Frame(root, padding=(20,0,20,12))
        footer.pack(fill='x')
        ttk.Label(footer, textvariable=self.status).pack(side='left')
        ttk.Label(footer, textvariable=self.count).pack(side='right')

    def fields(self):
        return self.name.get().strip(), self.dtype.get(), self.value.get(), self.scope.get()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for (scope, name), (dtype, value) in self.table.symbols.items():
            self.tree.insert('', 'end', values=(name, dtype, value, scope))
        self.count.set(f'Total symbols: {len(self.table.symbols)}')

    def perform(self, operation, message):
        try:
            operation()
            self.refresh()
            self.status.set(message)
        except ValueError as error:
            self.status.set(str(error))
            messagebox.showwarning('Symbol Table', str(error))

    def insert(self):
        self.perform(lambda: self.table.insert(*self.fields()), 'Symbol inserted successfully.')

    def search(self):
        name, _, _, scope = self.fields()
        result = self.table.search(name, scope)
        if result is None:
            self.status.set('Symbol not found in selected scope.')
            messagebox.showinfo('Search', 'Symbol not found in selected scope.')
            return
        self.dtype.set(result[0])
        self.value.set(result[1])
        for item in self.tree.get_children():
            row = self.tree.item(item, 'values')
            if row[0] == name and row[3] == scope:
                self.tree.selection_set(item)
                self.tree.see(item)
                break
        self.status.set('Symbol found.')

    def update(self):
        self.perform(lambda: self.table.update(*self.fields()), 'Symbol updated successfully.')

    def delete(self):
        name, _, _, scope = self.fields()
        if messagebox.askyesno('Confirm deletion', f'Delete {name} from {scope} scope?'):
            self.perform(lambda: self.table.delete(name, scope), 'Symbol deleted successfully.')

    def select_row(self, event=None):
        selected = self.tree.selection()
        if selected:
            name, dtype, value, scope = self.tree.item(selected[0], 'values')
            self.name.set(name)
            self.dtype.set(dtype)
            self.value.set(value)
            self.scope.set(scope)

    def clear(self):
        self.tree.selection_remove(*self.tree.selection())
        self.name.set('')
        self.dtype.set('int')
        self.value.set('')
        self.scope.set('Global')
        self.status.set('Input cleared.')

    def export(self):
        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files','*.csv')])
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as file:
                writer = csv.writer(file)
                writer.writerow(['Identifier','Data Type','Value','Scope'])
                for (scope, name), (dtype, value) in self.table.symbols.items():
                    writer.writerow([name, dtype, value, scope])
            self.status.set('Symbol table exported successfully.')
        except OSError as error:
            messagebox.showerror('Export failed', str(error))

if __name__ == '__main__':
    root = tk.Tk()
    Application(root)
    root.mainloop()
