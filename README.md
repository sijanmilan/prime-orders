# Prime Now Orders

The aim of this tool is to help creation of (repeated) orders on (Amazon) Prime Now.

The main premise is that households have more or less the same shopping list that they buy periodically.

Prime Now interface does not allow users to 'bulk import / copy' shopping list and add / remove items. It forces users
to search for every single item and add them to the cart.

This (CLI) tools uses your "Order History" and allows you to copy (all items from) multiple previous orders into your cart.

From there using Prime Now app you are able to adjust quantities and checkout.
Tool also allows you to empty your cart


Notes:
- Prime Now allows maximum 50 unique items in your cart
- Orders that are currently out of stock will not be added to your cart when you run the script


## How to use this script

- Install Python 3 (you  have done that by now probably)  
- Install [Chrome Webdriver](https://chromedriver.chromium.org/downloads) 
- Add chromedriver installation directory to your `PATH`. This is optional, alternatively you can pass chromedriver
as command line argument (`--driverpath`)
- Install requirements obviously (`pip install -r requirements`)
### Execute script

If you have set chromedriver in your `PATH`, run the script using
```
python prime_order.py USER PASS 
```
or, if you need to specify path to chromedriver
```
python prime_order.py USER PASS --driverpath /path/to/chromedriver
```
where `USER` and `PASS` are your Prime Now credentials.

Example (linux): 
```
python prime_order.py my@email.com myPass --driverpath /usr/lib/chromium-browser/chromedriver
```


## COLLABORATION, LICENSE, WARRANTY 

* Feel free to do whatever you like with this.
* If you like this and would like to see more features added let me know
* if you would like to collaborate or have any suggestions I'd love to hear from you: sijanmilan at gmail
* Use at your own risk




