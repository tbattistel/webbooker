from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException
from datetime import datetime
import keyring


def connect():
    driver = webdriver.Chrome()
    driver.get('https://seguro.casandra.com.mx/Login.aspx')
    return driver

def login(driver, uname, pword):
    textfield = driver.find_element(by=By.ID, value='ctl00_Contenido_UID')
    textfield.send_keys(uname)
    textfield = driver.find_element(by=By.ID, value='ctl00_Contenido_PWD')
    textfield.send_keys(pword)
    login_button = driver.find_element(by=By.ID, value='ctl00_Contenido_BLogin')
    login_button.click()

def goto_court2_calendar(driver):
    services_btn = driver.find_element(by=By.CSS_SELECTOR, 
        value='.mm-dropdown:nth-child(6) > a > .mm-text')
    services_btn.click()
    reso_btn = driver.find_element(by=By.CSS_SELECTOR, 
        value='.open li:nth-child(1) .mm-text')
    reso_btn.click()
    court2_btn = driver.find_element(by=By.ID, 
        value='ctl00_Contenido_REPACS_ctl09_BSel')
    court2_btn.click()
    accept_popup_btn = driver.find_element(by=By.CSS_SELECTOR,
        value='button.btn-success')
    accept_popup_btn.click()
    return driver

def goto_date(driver, date):
    try:
        datetime.strptime(date, '%Y-%m-%d')
    except Exception as e:
        print("Date must be provided in format 'YYYY-MM-DD'")
        raise e
    date_btn = driver.find_element(by=By.XPATH, value='//a[@href="#'+date+'"]')
    date_btn.click()
    return driver

def book_time_slot(driver, times):

    # Get position of desired time slots on the single-day calendar view
    times_dec_hrs = []
    try:
        for t in times:
            tdec = datetime.strptime(t, '%H:%M').time()
            times_dec_hrs.append(tdec.hour + tdec.minute/60)
    except Exception as e:
        raise e
    times_rows = [int((t*2)+1) for t in times_dec_hrs]
    times_xpaths = [f'//*[@id="ctl00_Contenido_CalRsv"]/div[1]/div[2]/table/tbody/tr/td[2]/div/table/tbody/tr[{r}]/td' for r in times_rows]
    tslots = dict(zip(times, times_xpaths))
    
    # Loop through time slots until one is successfully booked
    response_map = {
        'ctl00_Contenido_CalRsv_Form_RsvIns_TraslapeHorario' : 
            'Selected time slot overlaps with an existing booking',
        'ctl00_Contenido_CalRsv_Form_RsvIns_ValidaOnlyRsvAfterlast' :
            'Selected time slot is too soon (must book further in advance)',
        'ctl00_Contenido_CalRsv_Form_RsvIns_ValidaFechas' :
            'Selected time slot is not valid',
    }
    tslots_status = []
    for time, xpath in tslots.items():
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        toggle24h_xpath = '//*[@id="ctl00_Contenido_CalRsv"]/div[1]/div[3]/a'
        toggle24h_btn = WebDriverWait(driver, 10).until(   # Wait for element
            EC.presence_of_element_located((By.XPATH, toggle24h_xpath)))
        if '24' in toggle24h_btn.text:
            try:
                toggle24h_btn.click()
            except: #StaleElementReferenceException
                toggle24h_btn = driver.find_element(by=By.XPATH, value=toggle24h_xpath)
                toggle24h_btn.click()
        tslot_btn = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        actionChains = ActionChains(driver) # Need action chain to dbl click
        actionChains.double_click(tslot_btn).perform()
        save_btn_id = 'ctl00_Contenido_CalRsv_Form_RsvIns_UpdateButton'
        cancel_btn_id = 'ctl00_Contenido_CalRsv_Form_RsvIns_CancelButton'
        save_btn = WebDriverWait(driver, 10).until(     # Wait for element
            EC.presence_of_element_located((By.ID, save_btn_id)))
        save_btn.click()
        response = check_success(driver, response_map)
        tslots_status.append('\n'.join(response))
        if 'Succeeded' in response:
            return tslots_status
        cancel_btn = WebDriverWait(driver, 10).until(   # Wait for element
            EC.presence_of_element_located((By.ID, cancel_btn_id)))
        cancel_btn.click()
        if times.index(time) == len(times)-1:
            return tslots_status

def check_success(driver, response_map):
    responses = []
    for code, desc in response_map.items():
        elems = driver.find_elements(by=By.ID, value=code)
        if len(elems) == 0:
            continue
        responses.append(f'RESPONSE:\n{desc}.\nFULL TEXT:\n{elems[0].text}')
    if len(responses) == 0:
        responses = ['DID NOT RECOGNIZE RESPONSE MESSAGE FROM SITE']
    return responses

def disconnect(driver):
    driver.quit()


if __name__ == '__main__':
    uname = 'Parota101'
    pword = keyring.get_password('Punta Esmeralda Casandra', uname)
    driver = connect()
    status = login(driver)
    driver = goto_court2_calendar(driver)
    driver = goto_date(driver, '2024-01-23')
    times = ['09:00', '12:00']
    responses = book_time_slot(driver, times)
    disconnect(driver)
    x=1
