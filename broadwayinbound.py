import datetime
import json
import requests
import time
import logging
import os
from lxml import html
from playwright.sync_api import sync_playwright
from playwright. sync_api._generated import Page, BrowserContext

# Configure logging
logging.basicConfig(filename='broadway.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def upload_data(item):
    files = {
        'Groupname': (None, item["Group_FIT"]),
        'showname': (None, item["Show_name"]),
        'showdate': (None, item["Show_date"]),
        'showtime': (None, item["Show_time"]),
        'data': (None, json.dumps(item["data"])),
    }
    response = requests.post('http://nycbroadwayteam.com/broadway/service//broadwayinbound_api.php', files=files)
    retry_count = 1
    while response.status_code != 200:
        if retry_count > 3:
            break
        response = requests.post('http://nycbroadwayteam.com/broadway/service//broadwayinbound_api.php', files=files)
        retry_count += 1
    res_text = json.loads(response.text)
    mess = res_text['message']
    status = res_text['status']
    if mess == 'Successfull' and status == 1:
        print('data inserted successfully.')
        logging.info('data inserted successfully.')
    else:
        print('error while inserting data')
        logging.error(f'error while inserting data:{files}')


def new_checking(page):
    try:
        inactive = page.locator('//button[@id="timeout-keep-signin-btn"]')
    except Exception as e:
        logging.error(f'Error in new_checking: {e}')
        inactive = ''

    try:
        inactive.click()
    except Exception as e:
        logging.error(f'Error clicking in new_checking: {e}')

    return page


def login(context: BrowserContext):
    login_username = ''
    login_password = ''
    current_run_hour = datetime.datetime.now().hour
    script_run_date = datetime.datetime.now().strftime("%d%m%Y")    
    now = datetime.datetime.now()
    current_minute = now.minute
    folder_name = f"broadway_inbound_{script_run_date}_{current_run_hour}_{current_minute}"
    os.makedirs(folder_name, exist_ok=True)
    page: Page = context.new_page()

    page.goto('https://www.broadwayinbound.com', timeout=40000)
    page.wait_for_load_state()
    time.sleep(10)
    try:
        login_button = page.locator(
            '//ul[@class="nav navbar-nav navbar-right bi-utility-nav "]/li[@class="button login"]')
    except Exception as e:
        logging.error(f'login button error: {e}')
        login_button = ''
    time.sleep(4)
    if login_button:
        login_button.click()
        time.sleep(4)
        try:
            username = page.locator('//input[@id="Username"]')
        except Exception as e:
            logging.error(f'username not found: {e}')
            username = ''
        if username:
            username.fill(login_username)
        time.sleep(3)
        try:
            password = page.locator('//input[@id="Password"]')
        except Exception as e:
            logging.error(f'password : {e}')
            password = ''
        if password:
            password.fill(login_password)
        time.sleep(3)
        try:
            page.locator('//button[@id="loginSubmitButton"]').click()
        except Exception as e:
            logging.error(f'login button error: {e}')
    else:
        logging.info('already logged in')
        pass
    time.sleep(3)
    try:
        all_show = page.locator('//a[@class="view-all-shows btn btn-lg btn-pink text-uppercase"]')
    except Exception as e:
        logging.error(f'view show not found: {e}')
        all_show = ''

    if all_show:
        all_show.click()
    time.sleep(3)
    try:
        show_click = page.locator('(//a[@aria-label="Request Tickets"])[1]')
    except Exception as e:
        logging.error(f'Request Tickets button : {e}')
        show_click = ''
    if show_click:
        show_click.click()
    time.sleep(3)
    try:
        ticket_req = page.locator('(//a[@class="btn btn-pink" and contains(text(), "request tickets")])[1]')
    except Exception as e:
        logging.error(f'ticket_req error: {e}')
        ticket_req = ''
    if ticket_req:
        ticket_req.click()
    page.wait_for_load_state()
    time.sleep(40)

    while True:
        ShowName_Input = input("Please Enter the Show Name Here: ")
        if not ShowName_Input:
            break
        logging.info(f'Starting processing for show: {ShowName_Input}')
        print("Input date should be in correct format (Ex.: dd/mm/yyyy 04/01/2024)")
        start = input("Enter start date: ")
        stop = input("Enter end date: ")
        order_type = ''
        while True:
            Group_FIT = input('Enter Group or FIT: ')
            if 'Group' == Group_FIT:
                order_type = 'Group'
                os.makedirs(f'{folder_name}/{order_type}', exist_ok=True)
                try:
                    page.locator('//button[@id="dropdownMenu1"]').click()
                except Exception as e:
                    logging.error(f'dropdown for group/FIT: {e}')

                time.sleep(5)
                try:
                    page.locator('//a/span[contains(text(),"Group Sale")]').click()
                except Exception as e:
                    logging.error(f'Group sale error: {e}')

                break

            elif 'FIT' == Group_FIT:
                order_type = 'FIT'
                os.makedirs(f'{folder_name}/{order_type}', exist_ok=True)
                try:
                    page.locator('//button[@id="dropdownMenu1"]').click()
                except Exception as e:
                    logging.error(f'dropdown for group/FIT: {e}')
                time.sleep(5)
                try:
                    page.locator('//a/span[contains(text(),"FIT Sale")]').click()
                except Exception as e:
                    logging.error(f'FIT error: {e}')
                break

            else:
                print("Please enter a valid value - Group or FIT")
                continue
        try:
            all_show = page.query_selector_all(f'//td[contains(text(),"{ShowName_Input}")]')
        except Exception as e:
            all_show = ''
            logging.error(f'Error getting on show: {e}')
        for show in all_show:
            try:
                a = show.inner_text()
            except:
                a = ''
            if a:
                if a == ShowName_Input:
                    show.click()
                    time.sleep(5)
                    break
                else:
                    continue

        brod = True
        while brod:
            try:
                page = new_checking(page)
            except Exception as e:
                logging.error(f'Error in new_checking while processing show: {e}')

            NextMonth_check = True
            time.sleep(25)
            page.wait_for_load_state()
            date_content = page.content()
            dt = html.fromstring(date_content)

            try:
                dat = "".join(dt.xpath('(//th[@class="datepicker-switch"])[1]/text()')).strip()
            except Exception as e:
                logging.error(f'Error getting date: {e}')
                dat = ''

            try:
                all_date = dt.xpath('//td[@class="active day" or @class="day"]')
            except Exception as e:
                logging.error(f'Error getting all_date: {e}')
                all_date = ''

            try:
                show_name = "".join(dt.xpath('//div[@id="SecondColumnHeadingId"]/text()')).strip()
            except Exception as e:
                logging.error(f'Error getting show_name: {e}')
                show_name = ''

            for date in all_date:
                try:
                    date_ = "".join(date.xpath('.//text()'))
                except Exception as e:
                    logging.error(f'Error getting date: {e}')
                    date_ = ''

                date__ = date_ + ', ' + dat
                date_obj = datetime.datetime.strptime(date__, "%d, %B %Y")
                date_1 = date_obj.strftime("%d/%m/%Y")
                date1 = datetime.datetime.strptime(start, "%d/%m/%Y")
                date2 = datetime.datetime.strptime(stop, "%d/%m/%Y")
                check_date = datetime.datetime.strptime(date_1, "%d/%m/%Y")
                current_year = check_date.year

                if date1 <= check_date <= date2:
                    logging.info(f'Processing date: {check_date}')

                    try:
                        date_b = page.locator(f'(//td[@class="day" and contains(text(),"{date_}")])[1]')
                    except Exception as e:
                        logging.error(f'Error getting date_b: {e}')
                        date_b = ''

                    try:
                        date_b.click()
                    except Exception as e:
                        logging.error(f'Error clicking date_b: {e}')
                        page = new_checking(page)
                        try:
                            date_b.click()
                        except Exception as e:
                            continue

                    time.sleep(25)
                    try:
                        times = page.locator('//input[@type="radio"]').all()
                    except Exception as e:
                        logging.error(f'Error getting times: {e}')
                        page = new_checking(page)
                        try:
                            times = page.locator('//input[@type="radio"]').all()
                        except Exception as e:
                            times = ''

                    if len(times) > 1:
                        for time_ in times:
                            try:
                                time_.click()
                            except Exception as e:
                                logging.error(f'Error clicking time_: {e}')
                                page = new_checking(page)
                                try:
                                    time_.click()
                                except Exception as e:
                                    logging.error(f'time click error: {e}')
                                    continue

                            time.sleep(25)
                            page_content = page.content()
                            sds = html.fromstring(page_content)

                            try:
                                show_date = page.locator('//div[@class="pull-left oe-product-date"]').inner_text()
                            except Exception as e:
                                logging.error(f'Error getting show_date: {e}')
                                show_date = ''

                            try:
                                show_date_text = show_date.split(', ')[1]
                                logging.info(f'Show_date_text_{show_date_text}')
                            except Exception as e:
                                logging.error(f'Error getting show_date_text: {e}')
                                show_date_text = ''
                            show_date_text = show_date_text.split()
                            current_year = str(current_year)
                            show_date_text.insert(2, current_year)
                            show_date_text = " ".join(show_date_text)
                            dt = datetime.datetime.strptime(show_date_text, "%B %d %Y %I:%M %p")
                            formatted_time = dt.strftime(f"%m-%d-%Y-%I-%M-%p")
                            show_date_info = formatted_time.split('-')[:3]
                            show_date_info_ = "-".join(show_date_info)
                            show_time_ = formatted_time.split('-')[3:]
                            show_time = "-".join(show_time_)
                            file_name = f'broad-{order_type}-{show_name}-{formatted_time}.json'
                            save_path = os.path.join(f'{folder_name}/{order_type}', file_name)
                            item = {'Show_name': show_name,
                                    'Show_date': show_date_info_,
                                    'Show_time': show_time.replace("-PM", " PM").replace("-AM", " AM").replace("-",
                                                                                                               ":").strip(),
                                    'Group_FIT': Group_FIT}
                            if os.path.exists(save_path):
                                logging.info(f'file already exists. {save_path}')
                                continue
                            time_data = []
                            try:
                                all_tr = sds.xpath(
                                    '//div[@id="sectionPricingGrid_wrapper"]/div[2]/div[2]/table/tbody/tr')
                            except Exception as e:
                                logging.error(f'Error getting all_tr: {e}')
                                all_tr = ''

                            for tr in all_tr:
                                avail = "".join(tr.xpath('.//td[1]/text()')).strip()
                                section = "".join(tr.xpath('.//td[2]/text()')).strip()
                                Your_price = "".join(tr.xpath('.//td[3]/text()')).strip()
                                Reg_price = "".join(tr.xpath('.//td[4]/text()')).strip()
                                data = {
                                    'avail': avail,
                                    'section': section,
                                    'Your_price': Your_price,
                                    'Reg_price': Reg_price
                                }

                                time_data.append(data)
                                print(data)
                            item["data"] = time_data
                            if time_data:
                                upload_data(item)
                                with open(save_path, 'w') as f:
                                    json.dump(time_data, f)
                                logging.info(f'file_saved_successfully_{save_path}')

                    else:
                        page_content = page.content()
                        sds = html.fromstring(page_content)

                        try:
                            show_date = page.locator('//div[@class="pull-left oe-product-date"]').inner_text()
                        except Exception as e:
                            logging.error(f'Error getting show_date: {e}')
                            show_date = ''

                        try:
                            show_date_text = show_date.split(', ')[1]
                        except Exception as e:
                            logging.error(f'Error getting show_date_text: {e}')
                            show_date_text = ''
                        show_date_text = show_date_text.split()
                        current_year = str(current_year)
                        show_date_text.insert(2, current_year)
                        show_date_text = " ".join(show_date_text)
                        dt = datetime.datetime.strptime(show_date_text, "%B %d %Y %I:%M %p")
                        formatted_time = dt.strftime(f"%m-%d-%Y-%I-%M-%p")
                        show_date_info = formatted_time.split('-')[:3]
                        show_date_info_ = "-".join(show_date_info)
                        show_time_ = formatted_time.split('-')[3:]
                        show_time = "-".join(show_time_)
                        file_name = f'broad-{order_type}-{show_name}-{formatted_time}.json'
                        save_path = os.path.join(f'{folder_name}/{order_type}', file_name)
                        if os.path.exists(save_path):
                            logging.info(f'file already exists. {save_path}')
                            continue

                        try:
                            all_tr = sds.xpath('//div[@id="sectionPricingGrid_wrapper"]/div[2]/div[2]/table/tbody/tr')
                        except Exception as e:
                            logging.error(f'Error getting all_tr: {e}')
                            all_tr = ''
                        item = {
                            'Show_name': show_name,
                            'Show_date': show_date_info_,
                            'Show_time': show_time.replace("-PM", " PM").replace("-AM", " AM").replace("-",
                                                                                                       ":").strip(),
                            'Group_FIT': Group_FIT}

                        time_data = []
                        for tr in all_tr:
                            avail = "".join(tr.xpath('.//td[1]/text()')).strip()
                            section = "".join(tr.xpath('.//td[2]/text()')).strip()
                            Your_price = "".join(tr.xpath('.//td[3]/text()')).strip()
                            Reg_price = "".join(tr.xpath('.//td[4]/text()')).strip()
                            data = {
                                'avail': avail,
                                'section': section,
                                'Your_price': Your_price,
                                'Reg_price': Reg_price
                            }

                            time_data.append(data)
                            print(data)

                        item["data"] = time_data
                        if time_data:
                            upload_data(item)
                            with open(save_path, 'w') as f:
                                json.dump(time_data, f)
                            logging.info(f'file_saved_successfully_{save_path}')

                elif check_date > date2:
                    brod = False
                    NextMonth_check = False
                    break
                else:
                    pass

            if NextMonth_check:
                try:
                    next_month = page.locator('(//th[@class="next"])[1]')
                except Exception as e:
                    logging.error(f'Error getting next_month: {e}')
                    next_month = ''

                if next_month:
                    try:
                        next_month.click()
                    except Exception as e:
                        logging.error(f'error: {e}')
                        break
                else:
                    return


if __name__ == '__main__':
    def open_playwright_session(headless):
        playwright_instance = sync_playwright().start()
        browser = playwright_instance.chromium.launch(headless=headless)
        context = browser.new_context()
        return context


    contex = open_playwright_session(headless=False)
    login(contex)
