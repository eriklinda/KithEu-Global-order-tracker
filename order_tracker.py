
import time
import requests
import time
import csv
import threading
from bs4 import BeautifulSoup
from csv import reader
from termcolor import colored
from threading import Thread, Lock
import sys

order_summary = {}
x = 1


def get_call(order):
    # Adding the orders in the dictionary
    # Making it global so i can access to maniuplate it thru this function
    # Otherwise it wouldnt have been saved
    global order_summary
    global x
    order_summary[x] = order
    x += 1


def write_to_file():
    # Here i am reading from the global variable we just declared in the above function
    # It reads it. loops it thru and writing each order down to a new line!
    with open('order_status.csv', 'w', newline='') as f:
        # create the csv writer
        writer = csv.writer(f)

        # write a row to the csv file
        writer.writerow({'Id', 'Email', 'Status', 'Item'})
        for i in order_summary:
            writer.writerow(order_summary[i].values())


class order_tracker():
    def __init__(self, order):
        # Declaring the instance and creating the variables that we will be using when checking them
        self.session = requests.Session()
        try:
            self.order_id = order['id']
            self.order_email = order['email']
        except Exception as e:
            print(colored(f'Error loading order - {e}', 'red'))
            sys.exit(1)
        self.start()

    def start(self):
        # I choosed to declare this function for easier readability and cleaner codebase
        order_info = self.get_order()
        self.parse_order(order_info)

        # Now we have gathered all the necessary info from the orders we just pasted in!
        get_call(self.order)

    def get_order(self):
        # Using "while True:" to make it loop until it have recived a successfull response from the API
        while True:
            URL = 'https://web.global-e.com/Order/Track/'

            # Setting the correct content-type to ensure the encoding is set correctly
            # This isnt necessary sometime due to the fact that most "request" libs have an auto-detector for this
            # but to avoid the possibility of an error-factor i choosed to set it anyway
            headers = {
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'
            }

            # The payload that will be sent to the API

            data = {
                'OrderID': self.order_id,
                'ShippingEmail': self.order_email,
                'X-Requested-With': 'XMLHttpRequest'
            }

            # Wrapping it around try & except statement that is equalent to JS catch, this will simply just catch
            # the errors that could be cause by this
            # i havent seen to many weird error when testing this endpoint out
            try:
                response = self.session.post(
                    url=URL, data=data, headers=headers)
            except Exception as e:
                # This will raise the exception and sleep for 5s
                # The only thing that can raise this is either server down or rate-limited
                print(colored(f'Error getting order - {e}', 'red'))
                time.sleep(5)

            if response.status_code == 200:
                # Returning the text for parsing when a successful response has been received
                return response.text

    def parse_order(self, text):

        # Declaring the chars that the strings can contain that we wanna filter out
        # There is tons of ways of removing unwanted characters from string
        # but since we know what chars that can appear in the string, we can simply just add them to
        # this list that we just declared
        non_wanted_chars = ['1', '2', '3', '4',
                            '5', '.', ' ', 'order', '\n', '\r']

        # Declaring the html parser that we will be using
        soup = BeautifulSoup(text, 'html.parser')

        is_order_valid = soup.find('span', class_='field-validation-error')
        if is_order_valid != None:
            print(
                colored(f'No order matched {self.order_id} - {self.order_email}', 'red'))
            self.order = {
                'Id': self.order_id,
                'Email': self.order_email,
                'Status': 'No order found',
                'Item': 'No order found'
            }
            return self.order

        # Retreiving the status from the html file
        order_status = soup.find('div', class_='order-status noSplit')
        order_status = order_status.find('span', class_='current active')

        # Retreving the productname from the html file
        order_product = soup.find('span', class_='product-name')

        if order_status != None:
            # If the orderstatus is available, that means its not a ghost order, then it cuts out all the unwanted chars from the string
            status = order_status.text.lower()
            for i in non_wanted_chars:
                status = status.replace(i, '')

        else:
            status = 'Ghost'

        order_item = order_product.text

        # Wrapping all the gathered info in a dictionary that will be sent to the 'get_call' function
        self.order = {
            'Id': self.order_id,
            'Email': self.order_email,
            'Status': status.title(),
            'Item': order_item.strip()
        }

        print(
            colored(f'Successfully got orderstatus from {self.order_id}', 'green'))

        return self.order


def load_orders(file):
    # Parsing all the rows from the csv file and extracting the info
    rows = dict()
    with open(file, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        row_count = 0
        for row in reader:
            rows[row_count] = dict(row)
            row_count += 1

    return rows, row_count


def main():
    input_orders, input_amount = load_orders('orders.csv')
    if input_amount > 0 or input_amount != None:
        # Making sure orders is loaded in the orders.csv to get rid of potential errors
        print(colored(f'Successfully loaded {input_amount} orders', 'green'))
    else:
        # If no orders is loaded, it will close the application
        print(colored(f'No orders loaded, exiting...', 'red'))
        sys.exit()

    taskarna = []
    for tasken in input_orders:
        # Looping thru all tasks and starts a separate thread for each order to speed up the process
        taskarna.append(threading.Thread(
            target=order_tracker, args=[input_orders[tasken]]))
        taskarna[-1].start()

    for t in taskarna:
        t.join()

    # Writing down all the orders to a new csv file
    # Its way easier to get a good overview when looking at a csvfile than in a terminal!
    write_to_file()


if __name__ == '__main__':
    # Executing the "main" function declared above ^
    main()
