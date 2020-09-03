#!/bin/env python3

#todo:
#clean up code tagged: '#HACK'
#improve performance for large budgetfile
#change chart size dynamically
#change .format to fstrings
#chart coloring: what happens when amount tags > amount colors?
#use classes the way they were intended ;)
#add ability to show arbitrary month


#libraries
from ast import literal_eval
from datetime import date, timedelta
from os.path import expanduser
from random import choice, sample
from urllib.request import Request, urlopen
from traceback import print_exc

try:
    import readline
except ImportError:
    pass

class color:
    colors = {"red": "\33[31m", 
              "green": "\33[32m",
              "orange": "\33[33m",
              "blue": "\33[34m",
              "purple": "\33[35m",
              "cyan": "\33[36m",
              "gray": "\33[37m",
              "yellow": "\33[93m",
              "pink": "\33[95m"} 

    def text(col, string):
        end = "\33[0m"

        if col == "random":
            col = choice(list(color.colors.keys()))
        colored_string = f"{color.colors[col]}{string}{end}"

        return colored_string

class dateinfo:
    def today():
        date_today = date.today()
        year = date_today.strftime("%Y")
        month = date_today.strftime("%m")
        day = date_today.strftime("%d")

        return (year, month, day)

    def last_month():
        date_last_month = date.today().replace(day=1) - timedelta(days=1)
        year = date_last_month.strftime("%Y")
        month = date_last_month.strftime("%m")

        return (year, month)

    def to_string(year, month, day):
        date_str = "{}-{}-{}".format(year, month, day)

        return date_str

class currency:
    rates_available = False
    base_currency = "EUR"
    api_url = "https://api.ratesapi.io/api/latest?base=" + base_currency

    rates = {}

    def update_rates():
        try:
            rates_api_request = Request(currency.api_url, headers={"User-Agent": "Mozilla/5.0"})
            rates_api_data = urlopen(rates_api_request).read().decode("utf-8")
            currency.rates = literal_eval(rates_api_data)
            currency.rates_available = True
        except:
            print("Could not retrieve currency rates.")

    def convert(input_currency, amount):
        if currency.rates_available == True:
            if input_currency in currency.rates["rates"]:
                amount = float(amount)
                base_to_input_rate = currency.rates["rates"][input_currency]
                base_to_input_rate = float(base_to_input_rate)
                base_amount = amount / base_to_input_rate

                return base_amount
            else:
                raise Exception("Requested currency (" + input_currency
                                                   + ") not available.")
        else:
            raise Exception("Currency conversion not available.")

    def go_online():
        userin = input("Retrieve currency rates? [y,N] ")
        if userin in ["y", "Y", "yes"]:
            currency.update_rates()

class budgets:
    path = expanduser("~/budget_file")
    backup_path = path + ".edit"
    budget = []
    entry_dict = {"year": 0, "month": 1, "day": 2,
                  "amount": 3, "purpose": 4, "tag": 5}

    entry_format = "{year};{month};{day};{amount};{purpose};{tag}\n"

    def format_entry(year, month, day, amount, purpose, tag):
        amount = round(float(amount), 2)
        entry = (year, month, day, amount, purpose, tag)

        return entry

    def read_entry(entry, item):
        bd = budgets.entry_dict

        if item == "date":
            year = entry[bd["year"]]
            month = entry[bd["month"]]
            day = entry[bd["day"]]
            item_value = dateinfo.to_string(year, month, day)
        else:
            item_value = entry[budgets.entry_dict[item]]

        return item_value

    #HACK (from stackoverflow)
    def translate_entry(entry):
        temp_tuple_list = list(zip(budgets.entry_dict, entry))
        entry_as_dict = {k: v for k,v in temp_tuple_list}

        return entry_as_dict

class filter:
    def by_month(budget, year, month):
        filtered_budget = []

        for entry in budget:
            entry_year = budgets.read_entry(entry, "year")
            entry_month = budgets.read_entry(entry, "month")

            if entry_month == month and entry_month == month:
                filtered_budget.extend([entry])

        return filtered_budget

    def by_tag(budget, tag):
        filtered_budget = []

        for entry in budget:
            entry_tag = budgets.read_entry(entry, "tag")

            if entry_tag == tag:
                filtered_budget.extend([entry])

        return filtered_budget

class budgetfile:
    def read(path):
        budget = []

        try:
            with open(path, "r") as budgetfile:
                for line in budgetfile:
                    line = line.strip("\n")
                    line = line.split(";")
                    bd = budgets.entry_dict

                    year = line[bd["year"]]
                    month = line[bd["month"]]
                    day = line[bd["day"]]
                    amount = float(line[bd["amount"]])
                    purpose = line[bd["purpose"]]
                    tag = line[bd["tag"]]

                    entry = budgets.format_entry(year, month, day,
                                                 amount, purpose, tag)

                    budget.extend([entry])

        except FileNotFoundError:
            print("READ: " + path + " not found.")
        except PermissionError:
            print("READ: Permission denied: "+ path)

        return budget

    def write(path, budget):
        entry_format = budgets.entry_format

        try:
            with open(path, "w") as budgetfile:
                for entry in budget:
                    entry_as_dict = budgets.translate_entry(entry)
                    entry_formatted = entry_format.format(**entry_as_dict)

                    budgetfile.write(entry_formatted)

        except PermissionError:
            print("WRITE: Permission denied: "+ path)

class transaction:
    def new(amount, purpose, tag="notag"):
        date = dateinfo.today()
        year = date[0]
        month = date[1]
        day = date[2]

        transaction = budgets.format_entry(year, month, day,
                                           amount, purpose, tag)

        return transaction

    def add(budget, transaction):
        budget = budget.extend([transaction])

        return budget

class calculate:
    def budget(budget):
        saldo = 0
        income = 0
        expenses = 0

        for entry in budget:
            amount = budgets.read_entry(entry, "amount")
            saldo += amount

            if amount > 0:
                income += amount
            else:
                expenses += amount

        saldo = round(saldo, 2)
        income = round(income, 2)
        expenses = round(expenses, 2)

        calculation = {"saldo": saldo, "income": income,
                       "expenses": expenses}

        return calculation

    def tags(budget):
        income = {}
        expenses = {}
        tags = {}
        i = 0
        e = 0

        for entry in budget:
            amount = budgets.read_entry(entry, "amount")
            tag = budgets.read_entry(entry, "tag")

            if amount > 0:
                if tag in income:
                    income[tag] = income[tag] + amount
                else:
                    income[tag] = amount
                i += amount
            else:
                if tag in expenses:
                    expenses[tag] = expenses[tag] + amount
                else:
                    expenses[tag] = amount
                e += amount

        calculation = {"income": income, "expenses": expenses, 
                       "totals": {"income": i, "expenses": e}}
        
        return calculation

class visualize:
    def entry(entry):
        entry_vis_format = "{} {} {} [{}]"
        br = budgets.read_entry
        date = br(entry, "date")
        amount = br(entry, "amount")
        purpose = br(entry, "purpose")
        purpose = "{:-<20}".format(purpose + " ")
        tag = br(entry, "tag")

        if amount <= 0:
            col = "red"
        else:
            col = "green"

        amount = "{:+10.2f}".format(amount)
        amount = color.text(col, amount)
        entry_vis = entry_vis_format.format(amount, date, purpose, tag)

        return entry_vis

    def summary(budget_calculation):
        bc = budget_calculation
        saldo = str(bc["saldo"])
        income = color.text("green", str(bc["income"]))
        expenses = color.text("red", str(bc["expenses"]))
        vis_saldo = "Saldo: {} Income: {} Expenses: {}"
        vis_saldo = vis_saldo.format(saldo, income, expenses)

        return vis_saldo

    def list(budget, entries=10):
        for entry in budget[-entries:]:
            print(visualize.entry(entry))

    def chart(budget_calculation):
        bc = budget_calculation

        #TODO what if there are too many tags?
        tags = set(bc["income"]).union(set(bc["expenses"]))
        tag_colors = sample(set(color.colors), len(tags))
        tag_colors = dict(zip(tags, tag_colors)) 

        tag_char = chr(9608) # box character
        max_value = max(bc["totals"]["income"], abs(bc["totals"]["expenses"]))

        if max_value == 0:
            print("No transactions this month")
        else:
            for s in ("income", "expenses"):
                value = bc["totals"][s]
                chart_str = "Income:   " if s == "income" else "Expenses: "
                bar_len = 80 - len(chart_str) - len(str(value)) - 4
                bar_len = bar_len * (abs(value) / max_value)
                
                for tag in bc[s]:
                    tag_bar_len = int(bar_len * (abs(bc[s][tag]) / abs(value)))
                    tag_str = color.text(tag_colors[tag], tag_char)

                    chart_str += tag_str * tag_bar_len
                chart_str = f"{chart_str} {value:+.2f}"
                print(chart_str)
            label_str = "Legend:   "
            for tag in tag_colors:
                label_str += f"{color.text(tag_colors[tag], tag_char)} {tag} "
            print(label_str)

class commands:
    def total(tag=None):
        if tag:
            tag = tag[0]
            budget_filtered = filter.by_tag(budgets.budget, tag)
        else:
            budget_filtered = budgets.budget

        budget_calc = calculate.budget(budget_filtered)
        budget_vis = visualize.summary(budget_calc)

        print(budget_vis)

    def month(tag=None):
        year = dateinfo.today()[0]
        month = dateinfo.today()[1]

        budget_monthly = filter.by_month(budgets.budget, year, month)
        if tag:
            tag = tag[0]
            budget_filtered = filter.by_tag(budget_monthly, tag)
        else:
            budget_filtered = budget_monthly

        budget_calc = calculate.budget(budget_filtered)
        budget_vis = visualize.summary(budget_calc)

        print(budget_vis)

    def chart(arg=None):
        if arg == ["total"]:
            print("Budget total:")
            budget_filtered = budgets.budget
        else:
            print("Budget this month:")
            year = dateinfo.today()[0]
            month = dateinfo.today()[1]
            budget_filtered = filter.by_month(budgets.budget, year, month)
        
        budget_vis = visualize.chart(calculate.tags(budget_filtered))
    def transaction(args):
        try:
            amount = args[0]
            purpose = args[1]
            currency_tag = amount[-3:]

            if currency_tag.isalpha():
                amount = amount[:-3]
                amount = currency.convert(currency_tag, amount)

            if len(args) >= 3:
                tag = args[2]
                transac = transaction.new(amount, purpose, tag)
            else:
                transac = transaction.new(amount, purpose)

            transaction.add(budgets.budget, transac)
            print(visualize.entry(transac))

        except IndexError:
            raise Exception("Not enough Arguments provided.")
        except ValueError:
            raise Exception("Enter a valid amount.")

    def list(arg=None):
        if arg:
            arg = arg[0]
            if arg.isdigit():
                visualize.list(budgets.budget, int(arg))
            else:
                budget_filtered = filter.by_tag(budgets.budget, arg)
                visualize.list(budget_filtered, 0)
        else:
            visualize.list(budgets.budget)

    def list_tags():
        tags = []
        for entry in budgets.budget:
            tags.extend([budgets.read_entry(entry, "tag")])
        tags = set(tags)
        tags.discard("notag")
        for tag in tags:
            print(tag)

    def raw_list():
        for entry in budgets.budget:
            print(entry)

    def undo():
        budget = budgets.budget
        print(visualize.entry(budget[-1]) + " removed.")
        del budget[-1]
        budgets.budget = budget

    def help():
        print("Available commands:")
        for entry in available_commands.commands:
            print(f"{entry} {available_commands.commands[entry][1]}")

    def exit():
        budgetfile.write(budgets.path, budgets.budget)
        print("All changes have been saved.")
        raise SystemExit

class available_commands:
    commands = {"total": (commands.total, "[tag]"),
                "month": (commands.month, "[tag]"),
                "chart": (commands.chart, "['total']"),
                "t": (commands.transaction, "amount label [tag]"),
                "l": (commands.list, "[number of entries ('0' prints all)]"),
                "raw": (commands.raw_list, ""),
                "tags": (commands.list_tags, ""),
                "undo": (commands.undo, ""),
                "h": (commands.help, ""),
                "q": (commands.exit, "")}

class userinput:
    def split(raw_in):
        in_list = raw_in.split(" ")
        command = in_list[0]
        arguments = in_list[1:]
        cmd_args = {"command": command, "arguments": arguments}

        return cmd_args

    def execute(userin):
        try:
            cmd = userin["command"]
            args = userin["arguments"]

            try:
                exec_func = available_commands.commands[cmd][0]

                if args and '' not in args:
                    exec_func(args)
                else:
                    exec_func()

            except KeyError:
                raise Exception(cmd + " - Command not found. 'h' for help.")

        except Exception:
            print_exc()

if __name__ == "__main__":
    try:
        path = budgets.path
        budgets.budget = budgetfile.read(path)
        budgetfile.write(budgets.backup_path, budgets.budget)

        currency.go_online()

        prompt = "> "

        while True:
            try:
                userin = input(prompt)
                userin_split = userinput.split(userin)
                userinput.execute(userin_split)

            except SystemExit:
                break
            except EOFError:
                print("\nAborted - No changes have been made.")
                break

    except (KeyboardInterrupt, EOFError) as e:
        print("\nAborted - No changes have been made.")
