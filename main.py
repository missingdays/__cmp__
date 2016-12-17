
# -*- coding: utf-8 -*-

from tkinter import *
from tkinter.filedialog import *
import pandas as pd
import xlrd

root = Tk()

scrollbar = Scrollbar(root)
txt = Text(root,width=100,height=30,font="12", wrap=WORD, yscrollcommand=scrollbar.set)

notFoundScrollbar = Scrollbar(root)
notFoundText = Text(root, width=30, height=30, font="12", wrap=WORD, yscrollcommand=notFoundScrollbar.set)

shopFile = None
onlineFile = None

class ShopProduct:

    def __init__(self, id, name, price):
        self.id = id
        self.name = name
        self.price = price

        self.vars = []

    def __str__(self):
        return repr(self.id) + ":" + repr(self.name) + ":" + repr(self.price) + ":" + repr(self.vars)

def log(*args, to=txt):
    to.insert(END, ' '.join(map(str, args)))
    to.insert(END, '\n')

def openShopFile():
    global shopFile
    op = askopenfilename()

    shopFileLabel.configure(text=op)

    rb = xlrd.open_workbook(op, formatting_info=True)
    shopFile = rb.sheet_by_index(0)

def openOnlineFile():
    global onlineFile
    op = askopenfilename()

    onlineFileLabel.configure(text=op)

    onlineFile = pd.read_csv(op)

def getOnlineProducts():
    return onlineFile

def processID(id):
    if type(id) != str:
        id = repr(int(id))

    special = (u"бут_п_1")

    if id in special:
        return id

    num_id = []

    for c in id:
        if '0' <= c <= '9':
            num_id.append(c)

    return ''.join(num_id)

def processWeight(weight):
    num_weight = []

    for c in weight:
        if '0' <= c <= '9' or c == '.':
            num_weight.append(c)
        else:
            break

    return ''.join(num_weight)

def getShopProducts():
    shopProducts = []

    for rownum in range(11, shopFile.nrows):
        row = shopFile.row_values(rownum)

        if row[2] == '':
            continue

        row[2] = processID(row[2])

        nextRow = shopFile.row_values(rownum+1)

        shopProduct = ShopProduct(id=row[2], name=row[1], price=row[5])

        if nextRow[1] != '':
            i = rownum + 1

            try:
                while shopFile.row_values(i)[2] == '' and i < rownum + 5:
                    shopProduct.vars.append(shopFile.row_values(i))
                    i += 1
            except Exception:
                break

        shopProducts.append(shopProduct)

    return shopProducts

def getShopProductByID(shopProducts, id):
    def _find(_id):
        for i in range(len(shopProducts)):
            shopProduct = shopProducts[i]

            if shopProduct.id == _id:
                return i

    res = _find(id)

    return res if res else _find("0" + id)

def clearLogs():
    notFoundText.delete(1.0, END)
    txt.delete(1.0, END)

def roundShopPrice(a):
    return round(a*1.18)

def filterByName(name):
    def _filter(x):
        return str(x).find(name) != -1
    return _filter

def findOnlineVars(name, onlineProducts):
    mask = onlineProducts['Product Name'].apply(filterByName(name))
    vars = onlineProducts[mask]

    return vars

def comparePrices(onlineProduct, product, vars=None):
    if vars is None:
        onlinePrice = onlineProduct.iloc[0]["Price"]
        shopPrice = roundShopPrice(int(product.price) * float(processWeight(product.vars[0][1])))

        if onlinePrice != shopPrice:
            log("NOT OK", product.id)
            log("Online price is ", onlinePrice, "while real price is: ", shopPrice)
    else:
        prices = []
        shopPrices = []

        for i in range(len(vars)-1):
            prices.append(vars.iloc[i]["Price"])

        prices.sort()

        for i in range(len(product.vars)):
            var = product.vars[i]

            weight = float(processWeight(var[1]))
            try:
                shopPrices.append((roundShopPrice(weight*var[5]), var[1], i))
            except Exception:
                print("There is wierd row {}", str(var))

        shopPrices.sort(key=lambda x: x[0])

        for price, name, index in shopPrices:
            if prices[index] != price:
                log("NOT OK", product.id, name)
                log("Online price is ", prices[index], "while real price is: ", price)

def runComparrison():

    clearLogs()

    productSKU = None
    onlineProducts = None
    shopProducts = None

    try:
        productSKU = 'Product SKU'

        onlineProducts = getOnlineProducts()
        onlineProductsID = onlineProducts[productSKU]

        shopProducts = getShopProducts()
    except Exception:
        productSKU = u'\ufeff"Product SKU"'

        onlineProducts = getOnlineProducts()
        onlineProductsID = onlineProducts[productSKU]

        shopProducts = getShopProducts()

    for id in onlineProductsID:

        if pd.isnull(id):
            continue

        id = str(int(id))

        shopProduct = getShopProductByID(shopProducts, id)

        if shopProduct == None:
            log(id, "Not found", to=notFoundText)
            continue

        if len(shopProducts[shopProduct].vars) == 0:
            onlineProduct = onlineProducts.loc[onlineProducts[productSKU] == float(id)]

            onlinePrice = int(onlineProduct.iloc[0]['Price'])
            shopPrice = int(shopProducts[shopProduct].price)

            shopPrice = roundShopPrice(shopPrice)

            if onlinePrice != shopPrice:
                log("NOT OK", id)
                log("Online price is ", onlinePrice, "while real price is: ", shopPrice)
        else:
            product = shopProducts[shopProduct]
            onlineProduct = onlineProducts.loc[onlineProducts[productSKU] == float(id)]
            onlineName = onlineProduct.iloc[0]['Product Name']

            onlineVars = findOnlineVars(onlineName, onlineProducts)

            if len(product.vars) == 1:
                comparePrices(onlineProduct, product)
                continue

            if len(onlineVars)-1 != len(product.vars):
                log("ERROR", id)
                log("Online package number is", len(onlineVars)-1, "but real package number is ", len(product.vars))
                continue

            comparePrices(onlineProduct, product, vars=onlineVars)
shopFileButton = Button(root,
                        text="Open true prices (excel)",
                        command=openShopFile)

onlineFileButton = Button(root,
                          text="Open current prices (csv)",
                          command=openOnlineFile)
shopFileLabel = Label(root)
onlineFileLabel = Label(root)

runButton = Button(root, text="Run comparison", command=runComparrison)

txt.pack(side=LEFT, fill=Y)
scrollbar.pack(side=LEFT, fill=Y)

scrollbar.config(command=txt.yview)

notFoundText.pack(side=RIGHT, fill=Y)

notFoundScrollbar.pack(side=RIGHT, fill=Y)
notFoundScrollbar.config(command=notFoundText.yview)

shopFileButton.pack(side=TOP)
shopFileLabel.pack(side=TOP)

onlineFileButton.pack(side=TOP)
onlineFileLabel.pack(side=TOP)

runButton.pack(side=TOP)

#root.state('zoomed')
root.mainloop()
