import requests
import tkinter as tk
from tkinter import ttk

currency_names = {
    "USD": "United States Dollar",
    "AUD": "Australian Dollar",
    "BRL": "Brazilian Real",
    "CAD": "Canadian Dollar",
    "CHF": "Swiss Franc",
    "CNY": "Chinese Yuan",
    "CZK": "Czech Koruna",
    "DKK": "Danish Krone",
    "EUR": "Euro",
    "GBP": "British Pound",
    "HKD": "Hong Kong Dollar",
    "HUF": "Hungarian Forint",
    "IDR": "Indonesian Rupiah",
    "ILS": "Israeli Shekel",
    "INR": "Indian Rupee",
    "ISK": "Icelandic Krona",
    "JPY": "Japanese Yen",
    "KRW": "South Korean Won",
    "MXN": "Mexican Peso",
    "MYR": "Malaysian Ringgit",
    "NOK": "Norwegian Krone",
    "NZD": "New Zealand Dollar",
    "PHP": "Philippine Peso",
    "PLN": "Polish Zloty",
    "RON": "Romanian Leu",
    "SEK": "Swedish Krona",
    "SGD": "Singapore Dollar",
    "THB": "Thai Baht",
    "TRY": "Turkish Lira",
    "ZAR": "South African Rand",
}

res = requests.get("https://api.frankfurter.dev/v1/latest", params={"base": "USD"}, timeout = 10)
data = res.json()


#Primary rate return function
def return_rate(input, output, value):

    try:
        value = float(value)
    except:
         num_error()
         return
    input = input[:3]
    output = output[:3]
    
    if (input == "USD") and (output == "USD"):
        result_var.set(value)
        return
    if input == 'USD':
        result_var.set(round(value * data["rates"][output], 2))
        return
    if output == 'USD':
        result_var.set(round(value / data["rates"][input], 2))
        return
    
    value_in_usd = value / data["rates"][input]
    result_var.set(round(value_in_usd * data["rates"][output], 2))
    return


def num_error():
    numwindow = tk.Toplevel(window)
    numwindow.title("Error")
    numwindow.geometry("200x75+850+320")


    errlabel = tk.Label(numwindow, text=f"Bad Number input", font=24)
    errlabel.pack(pady=10)

    backButton = tk.Button(numwindow, text="Close", command=numwindow.destroy)
    backButton.pack()



#GUI:
window = tk.Tk()
window.geometry("400x220+780+320")

window.title("Exchange Rate Calculator")

selected_input_currency = tk.StringVar(window)
selected_output_currency = tk.StringVar(window)
dropdown_items = [f"{code} - {currency_names.get(code, code)}" for code in data['rates'].keys()]
dropdown_items.insert(0, "USD - United States Dollar")

tk.Label(window, text="From:").grid(row=0, column=0, sticky="e", padx=10, pady=8)
input_dropdown = ttk.Combobox(window, textvariable=selected_input_currency, values=dropdown_items, state="readonly", width=30)
input_dropdown.current(0)
input_dropdown.grid(row=0, column=1, padx=10, pady=8)

tk.Label(window, text="To:").grid(row=1, column=0, sticky="e", padx=10, pady=8)
output_dropdown = ttk.Combobox(window, textvariable=selected_output_currency, values=dropdown_items, state="readonly", width=30)
output_dropdown.current(0)
output_dropdown.grid(row=1, column=1, padx=10, pady=8)

tk.Label(window, text="Value:").grid(row=2, column=0, sticky="e", padx=10, pady=8)
amount = tk.StringVar(window)
user_value_input = tk.Entry(window, textvariable=amount, font=("Arial", 14))
user_value_input.grid(row=2, column=1, padx=10, pady=8, sticky="w")

go_button = tk.Button(window, text="Calculate", font=("Arial", 14), command=lambda: return_rate(selected_input_currency.get(), selected_output_currency.get(), amount.get()))
go_button.grid(row=3, column=0, columnspan=2, pady=10)

tk.Label(window, text="Result:").grid(row=4, column=0, sticky="e", padx=10, pady=8)
result_var = tk.StringVar(window)
result_label = tk.Label(window, textvariable=result_var, font=("Arial", 14), borderwidth=2, relief="raised", width=20)
result_label.grid(row=4, column=1, padx=10, pady=8, sticky="w")



window.mainloop()
