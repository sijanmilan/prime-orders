import argparse
from time import sleep
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

import constants


class PrimeOrderManager:
    """Handles adding Orders from Order history to the Cart, and emptying the Cart
    Purchase / Checkout needs to be carried out manually"""
    def __init__(self, driver):
        self.driver = driver

    def sign_out_in(self, user_name, password):
        """Attempts to sing in use with passed credentials
        :return True is user signed in successfully """
        print(f"\nSigning in {user_name} to Prime Now...")
        self.driver.get(constants.URL_SIGNOUT)
        self.driver.find_element_by_id("ap_email").send_keys(user_name)
        self.driver.find_element_by_id("ap_password").send_keys(password)
        sign_in_button = self.driver.find_element_by_id("signInSubmit")
        self.driver.execute_script("arguments[0].click()", sign_in_button)
        sleep(1)
        # check successful sign in by checking if `url_account_address` is reachable
        self.driver.get(constants.URL_ACCOUNT_ADDRESS)
        sleep(1)
        if self.driver.current_url == constants.URL_ACCOUNT_ADDRESS:
            print(f"{user_name} signed in successfully!")
            return True
        else:
            print(f"User sign in failed. Check credentials and try again")
            return False

    def get_orders_list(self):
        """ :returns list of Completed Orders from 'Your Order' screen"""
        self.driver.get(constants.URL_YOUR_ORDERS)
        sleep(1)
        orders_dict = dict()

        try:
            completed_orders = self.driver.find_element_by_xpath('//*[@id="completed-orders"]')
            orders = completed_orders.find_elements_by_xpath("./table")
        except NoSuchElementException:
            print("No Completed orders found. You need at least one Completed order in order to copy last one")
        else:
            for x in range(len(orders)):
                try:
                    order_date = orders[x].find_element_by_xpath("./tbody/tr/td[1]/span[1]").text
                    order_url = orders[x].find_element_by_xpath("./tbody/tr/td[2]/span[1]/span/a").get_attribute('href')
                    orders_dict.update({x + 1: {"date": order_date, "url": order_url}})
                except NoSuchElementException:
                    print(f"Can not process order {x + 1} from your order history")
            return orders_dict

    def copy_order_to_cart(self, order_url):
        """Traverse through "Items Purchased" on the passed order's screen
        and add to shopping cart everything that was on the list and is available
        """

        print(f"Fetching order details from {order_url} and copying items to your cart")
        self.driver.get(order_url)
        sleep(5)

        ordered_items_divs = self.driver.find_elements_by_xpath("//div[@class='a-box-group' and "
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
                self.driver.execute_script(f"window.scrollTo(0, {item_button_location_y});")
                sleep(0.5)
                print(f"{x + 1:>4} - {item_text}")
                self.driver.execute_script("arguments[0].click();", item_button)
                added_to_cart_cnt += 1
                sleep(0.5)
            except NoSuchElementException:
                # item doesn't have Add button -> not on stock?
                item_not_on_stock = ordered_item_div.find_element_by_xpath("./div/a/div/div/div[2]/div[1]")
                item_text = item_not_on_stock.text
                print(f"{x + 1:>4} - {item_text} - NOT AVAILABLE")

        print(f"TOTAL: {added_to_cart_cnt} items added to the cart")

    def clear_cart(self, cart_url):
        """ Empty user's Shopping Cart"""
        # Logic:
        # 1. find different merchant carts (wholefoods, amazon...)
        # - these are in a div[@id='cart-merchant-thumbnail-container']
        # - all anchor tags contain links to merchant's cart content (div.id = a.data-merchantid)
        # - find merchant cart divs and show them so that all cart items are visible on the page regardless of merchant
        # 2.  find all 'Remove' buttons <a> and click them xpath: //div[@class = 'cart-item-remove-container'
        self.driver.get(cart_url)
        print(f"\nEmptying user's cart...")
        try:
            merchant_carts_div = self.driver.find_element_by_id('cart-merchant-thumbnail-container')
            print("-found multiple merchant's carts")
            merchant_carts_anchors = merchant_carts_div.find_elements_by_xpath('./span/a')
            for a in merchant_carts_anchors:
                merchant_id = a.get_attribute("data-merchantid")
                merchant_cart_div = self.driver.find_element_by_id(merchant_id)
                merchant_cart_div_class_show = merchant_cart_div.get_attribute("class").replace("cart-hide", "show")
                self.driver.execute_script(
                    f"document.getElementById('{merchant_id}').setAttribute('class','{merchant_cart_div_class_show}')")
        except NoSuchElementException:
            # in case there is only one merchant's cart
            # `driver.find_element_by_id('cart-merchant-thumbnail-container') will throw `NoSuchElementException`
            print("- found one merchant cart")
            pass
        cart_items_links = self.driver.find_elements_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
        print(f"- removing {len(cart_items_links)} items from the cart...")
        while len(cart_items_links):
            # need to loop several times until all items are removed
            for item in cart_items_links:
                self.driver.execute_script('arguments[0].click()', item)
                sleep(0.5)
            # seems like event handler is not fired for all elements.
            # wait a bit an check if any `cart-item-remove-link` is left
            sleep(2)
            cart_items_links = self.driver.find_elements_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
            if cart_items_links:
                print("- still removing...")

        print(f"Done - {len(cart_items_links)} items left in the cart")

    def is_cart_empty(self, cart_url):
        """:returns True if there are no items n the cart"""
        self.driver.get(cart_url)
        try:
            # if there is at least one item in the cart there will be "Remove" link associated with it
            self.driver.find_element_by_xpath("//a[contains(@class, 'cart-item-remove-link')]")
            return False
        except NoSuchElementException:
            return True


def get_yes_no_input(question_text):
    """ :return True/False as answer to the passed yes-no question"""
    confirm = ""
    while confirm.lower() not in ["y", "n"]:
        confirm = input(f"{question_text} [y/n]: ")
    return confirm.lower() == 'y'


def main():
    parser = argparse.ArgumentParser(description="Copy items from Past Orders on Amazon Prime now to your cart")
    parser.add_argument('user', help='Username for Prime Now account')
    parser.add_argument('password', help='Password for Prime Now account')
    parser.add_argument('--driverpath', help='Path to chromedriver, unless already in users PATH')
    args = parser.parse_args()

    user_home_dir = str(Path.home())
    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--headless')
    options.add_argument(f"--user-data-dir={user_home_dir}/.config/google-chrome/prime-order-tool")
    if args.driverpath:
        driver = webdriver.Chrome(args.driverpath, options=options)
    else:
        driver = webdriver.Chrome(options=options)

    try:
        prime_order_manager = PrimeOrderManager(driver)
        if prime_order_manager.sign_out_in(args.user, args.password):
            print("\nChecking the state of your cart...")
            if not prime_order_manager.is_cart_empty(constants.URL_CART):
                if get_yes_no_input("There are items in your cart. Would you like to empty your cart first?"):
                    prime_order_manager.clear_cart(constants.URL_CART)
            else:
                print("Cart is empty")

            print(f"\nFetching your past order to copy to your cart...")
            past_orders = prime_order_manager.get_orders_list()
            print(f"\nYour past (10) orders:")
            for order_key in past_orders.keys():
                print(f"{order_key:>4} - {past_orders[order_key]['date']}")

            selected_orders_no = input(
                f"---\nSelect numbers (comma separated) of your past orders you want "
                f"copied to your cart [1..{len(past_orders)}]: ")
            for no in selected_orders_no.split(sep=','):
                selected_order = past_orders.get(int(no))
                if not selected_order:
                    print(f"Order #{no} not in the list. Skipping")
                    continue
                if get_yes_no_input(
                        f"You are about to copy your order from {selected_order['date']}. Do you want to continue?"):
                    prime_order_manager.copy_order_to_cart(selected_order["url"])
    finally:
        print("Finished. Exiting")
        driver.close()
        driver.quit()


if __name__ == "__main__":
    main()
