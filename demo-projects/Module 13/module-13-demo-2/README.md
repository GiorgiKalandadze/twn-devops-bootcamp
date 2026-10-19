# Module 13: Programming with Python - Automation with Python

## Demo Project

Automation with Python

## Technologies Used

- Python
- IntelliJ IDEA / PyCharm
- Git

## Project Description

- Write an application that reads a spreadsheet file, then processes and manipulates the spreadsheet.

## Implementation Code

```python
import openpyxl

inv_file = openpyxl.load_workbook("inventory.xlsx")
product_list = inv_file["Sheet1"]

products_per_supplier = {}
total_value_per_supplier = {}
products_under_10_inv = {}


for product_row in range(2, product_list.max_row + 1):
    supplier_name = product_list.cell(product_row, 4).value
    inventory = product_list.cell(product_row, 2).value
    price = product_list.cell(product_row, 3).value
    product_num = product_list.cell(product_row, 1).value
    inventory_price = product_list.cell(product_row, 5)

    # calculation number of products per supplier
    if supplier_name in products_per_supplier:
        current_num_products = products_per_supplier.get(supplier_name)
        products_per_supplier[supplier_name] = current_num_products + 1
    else:
        products_per_supplier[supplier_name] = 1

    # calculation total value of inventory per supplier
    if supplier_name in total_value_per_supplier:
        current_total_value = total_value_per_supplier.get(supplier_name)
        total_value_per_supplier[supplier_name] = current_total_value + inventory * price
    else:
        total_value_per_supplier[supplier_name] = inventory * price

    # logic products with inventory less than 10
    if inventory < 10:
        products_under_10_inv[int(product_num)] = int(inventory)

    # add value for total inventory price
    inventory_price.value = inventory * price

print(products_per_supplier)
print(total_value_per_supplier)
print(products_under_10_inv)

inv_file.save("inventory_with_total_value.xlsx")
```

## Expected Spreadsheet Layout

The script assumes `inventory.xlsx` has a sheet named `Sheet1` with the following columns, and a header in row 1:

| Column | Contents |
|--------|----------|
| A (1) | Product number |
| B (2) | Inventory quantity |
| C (3) | Price |
| D (4) | Supplier name |
| E (5) | Total inventory value (written by the script) |

## Step-by-Step Implementation

### Step 1: Set Up the Environment

- Created a Python project in IntelliJ IDEA / PyCharm with a virtual environment.
- Installed the `openpyxl` library to read and write Excel files.
- Initialized a Git repository for version control.

### Step 2: Load the Spreadsheet

- Opened `inventory.xlsx` with `openpyxl.load_workbook()`.
- Selected the `Sheet1` worksheet.

### Step 3: Read and Process Each Row

- Looped from row 2 to the last row, skipping the header.
- Read the product number, inventory, price, and supplier name from each row.

### Step 4: Aggregate Data by Supplier

- Counted the number of products per supplier using a dictionary.
- Calculated the total inventory value per supplier by multiplying inventory by price and summing the results.

### Step 5: Identify Low-Stock Products

- Collected products with fewer than 10 units in stock into a dictionary, keyed by product number.

### Step 6: Write Results Back to the Spreadsheet

- Wrote the total value (inventory × price) for each product into column E.
- Printed the three summary dictionaries to the console.
- Saved the updated workbook as `inventory_with_total_value.xlsx`.
