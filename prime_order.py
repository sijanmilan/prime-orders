import sys
import argparse
from time import sleep

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

url_base = "https://primenow.amazon.com"
url_account_address = "https://primenow.amazon.com/account/address"
url_404 = "https://primenow.amazon.com/404"
url_signout = "https://primenow.amazon.com/signout?ref_=pn_gw_nav_account_signout&returnUrl=https%3A%2F%2Fprimenow.amazon.com%2Fsignin"
url_cart = 'https://primenow.amazon.com/cart?ref_=pn_gw_nav_cart'
url_past_purchased_items = "https://primenow.amazon.com/shop-past-purchases?ref_=pn_gw_nav_account_spp"
url_your_orders = "https://primenow.amazon.com/yourOrders?ref_=pn_spp_nav_account_order"

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
# headless works if we are using execute_script to 'click'
options.add_argument('--headless')
options.add_argument('--user-data-dir=/home/milan/.config/google-chrome/Default')
driver = webdriver.Chrome('/usr/lib/chromium-browser/chromedriver', options=options)


def sign_out_in(user_name, password):
    """Attempts to sing in use with passed credentials
    :return True is user signed in successfully """

    driver.get(url_signout)
    driver.find_element_by_id("ap_email").send_keys(user_name)
    driver.find_element_by_id("ap_password").send_keys(password)
    sign_in_button = driver.find_element_by_id("signInSubmit")
    driver.execute_script("arguments[0].click()", sign_in_button)
    sleep(1)
    # check successful sign in by checking if `url_account_address` is reachable
    driver.get(url_account_address)
    sleep(1)
    if driver.current_url == url_account_address:
        print(f"User {user_name} signed in successfully!")
        return True
    else:
        print(f"User sign in failed. Check credentials and try again")
        return False


def get_orders_list():
    """ :returns list of Completed Orders from 'Your Order' screen"""
    driver.get(url_your_orders)
    sleep(1)
    orders_dict = dict()

    try:
        completed_orders = driver.find_element_by_xpath('//*[@id="completed-orders"]')
        orders = completed_orders.find_elements_by_xpath("./table")
    except NoSuchElementException:
        print("No Completed orders found. You need at least one Completed order in order to copy last one")
    else:
        for x in range(len(orders)):
            try:
                order_date = orders[x].find_element_by_xpath("./tbody/tr/td[1]/span[1]").text
                order_url = orders[x].find_element_by_xpath("./tbody/tr/td[2]/span[1]/span/a").get_attribute('href')
                orders_dict.update({x+1: {"date" : order_date, "url": order_url}})
            except NoSuchElementException:
                print(f"Can not process order {x+1} from your order history")
        return orders_dict


def copy_order_to_cart(order_url):
    """Traverse through "Items Purchased" on the passed order's screen
    and add to shopping cart everything that was on the list and is available
    """

    print(f"Fetching order details from {order_url} and copying items to your cart")
    driver.get(order_url)
    sleep(5)

    ordered_items_divs = driver.find_elements_by_xpath("//div[@class='a-box-group' and "
                                                  ".//span[contains(text(),'Items Purchased')]]"
                                                  "/div[@class='a-box']")
    added_to_cart_cnt = 0
    for x in range(len(ordered_items_divs)):
        ordered_item_div = ordered_items_divs[x]
        try:
            item_on_stock = ordered_item_div.find_element_by_xpath("./div/div/div/div[1]")
            item_text = item_on_stock.find_element_by_xpath("./a/div").text
            item_button = item_on_stock.find_element_by_xpath(".//button[contains(@id,'add-to-cart')]")
            item_button_location_y = item_on_stock.location['y']

            # Button may not be in the viewport - so it can not be clicked => scroll to button loction
            driver.execute_script(f"window.scrollTo(0, {item_button_location_y});")
            sleep(0.5)
            print(f"{x+1:4} - {item_text}")
            driver.execute_script("arguments[0].click();", item_button)
            added_to_cart_cnt += 1
            sleep(0.5)
        except:
            # item doesn't have Add button -> not on stock?
            item_not_on_stock = ordered_item_div.find_element_by_xpath("./div/a/div/div/div[2]/div[1]")
            item_text = item_not_on_stock.text
            print(f"{x+1:4} - {item_text} - NOT AVAILABLE")

    print(f"\nTOTAL: {added_to_cart_cnt} items added to the cart")


def get_yes_no_input(question_text):
    """ :return True/False as answer to the passed yes-no question"""
    confirm = ""
    while confirm.lower() not in ["y", "n"]:
        confirm = input(f"{question_text} [y/n]: ")
    return confirm.lower() == 'y'


def clear_cart(cart_url):
    """ Empty user's Shopping Cart"""
    # Logic:
    # 1. find different merchant carts (wholefoods, amazon...)
    #   - these are in a div[@id='cart-merchant-thumbnail-container']
    #   - all anchor tags contain links to merchant's cart content (div.id = a.data-merchantid)
    #   - find merchant cart divs and show them so that all cart items are visible on the page regardless of merchant
    # 2.  find all 'Remove' buttons <a> and click them xpath: //div[@class = 'cart-item-remove-container'
    driver.get(cart_url)
    try:
        merchant_carts_div = driver.find_element_by_id('cart-merchant-thumbnail-container')
        print("Found multiple merchant's carts")
        merchant_carts_anchors = merchant_carts_div.find_elements_by_xpath('./span/a')
        for a in merchant_carts_anchors:
            merchant_id = a.get_attribute("data-merchantid")
            merchant_cart_div = driver.find_element_by_id(merchant_id)
            merchant_cart_div_class_show = merchant_cart_div.get_attribute("class").replace("cart-hide", "show")
            driver.execute_script(f"document.getElementById('{merchant_id}').setAttribute('class','{merchant_cart_div_class_show}')")
            print(f"Merchant ID {merchant_id} found and div made visible | class = '{merchant_cart_div_class_show}")
    except NoSuchElementException as e:
        # in case there is only one merchant's cart
        # `driver.find_element_by_id('cart-merchant-thumbnail-container') will throw `NoSuchElementException`
        print("Seems like there in only one merchant cart")
        pass
    cart_items_links = driver.find_elements_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
    print(f"Removing {len(cart_items_links)} items from the cart...")
    while len(cart_items_links):
        # need to loop several times until all items are removed
        for item in cart_items_links:
            driver.execute_script('arguments[0].click()', item)
            sleep(0.5)
        # seems like event handler is not fired for all elements.
        # wait a bit an check if any `cart-item-remove-link` is left
        sleep(2)
        cart_items_links = driver.find_elements_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
        if cart_items_links:
            print("Still removing...")

    print(f"Done - {len(cart_items_links)} items left in the cart")


def is_cart_empty(cart_url):
    """:returns True if there are no items n the cart"""
    driver.get(cart_url)
    try:
        # if there is at least one item in the cart there will be "Remove" link associated with it
        driver.find_element_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
        return False
    except NoSuchElementException:
        return True


def main():
    parser = argparse.ArgumentParser(description="Copy items from Past Orders on Amazon Prime now to your cart")
    parser.add_argument('user',  help='Username for Prime Now account')
    parser.add_argument('password', help='Password for Prime Now account')
    args = parser.parse_args()

    try:
        sign_out_in(args.user, args.password)
        print("Checking the state of your cart...")
        if not is_cart_empty(url_cart):
            if get_yes_no_input("There are items in your cart. Would you like to empty your cart first?"):
                clear_cart(url_cart)
        else:
            print("Cart is empty")

        print("\nFetching your past order to copy to your cart...")
        past_orders = get_orders_list()
        print("Your past (10) orders:")
        for order_key in past_orders.keys():
            print(f" {order_key} - {past_orders[order_key]['date']}")

        selected_orders_no = input(f"---\n Select numbers (comma separated) of your past orders you want copied to your cart [1..{len(past_orders)}]: ")
        for no in selected_orders_no.split(sep=','):
            selected_order = past_orders.get(int(no))
            if not selected_order:
                print(f"Order #{no} not in the list. Skipping")
                continue
            if get_yes_no_input(f"You are about to copy your order from {selected_order['date']}. Do you want to continue?"):
                copy_order_to_cart(selected_order["url"])
    finally:
        print("Finished. Exiting")
        driver.quit()


if __name__ == "__main__":
    main()
