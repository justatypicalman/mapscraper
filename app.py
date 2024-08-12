from flask import Flask, render_template, request, redirect, url_for, send_file
import os
import pandas as pd
from playwright.sync_api import sync_playwright

app = Flask(__name__)

def scrape_google_maps(place, building_type, total=1000):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)
        search_for = f"{building_type} in {place}"
        page.locator('//input[@id="searchboxinput"]').fill(search_for)
        page.wait_for_timeout(3000)
        page.keyboard.press("Enter")
        page.wait_for_timeout(5000)
        
        results = []
        listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
        for listing in listings:
            listing.click()
            page.wait_for_timeout(3000)
            
            # Locate all potential address elements
            address_elements = page.locator('//button[@data-item-id="address"]//div').all()
            
            # Choose the first element with non-empty text
            address = next((element.text_content() for element in address_elements if element.text_content()), "N/A")
            
            name = listing.get_attribute('aria-label')
            results.append({"name": name, "address": address})
        
        df = pd.DataFrame(results)
        filename = f"{place}_{building_type}.csv"
        file_path = os.path.join('output', filename)
        os.makedirs('output', exist_ok=True)
        df.to_csv(file_path, index=False)
        
        browser.close()
        return filename

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        place = request.form['place']
        building_type = request.form['building_type']
        filename = scrape_google_maps(place, building_type)
        return redirect(url_for('result', filename=filename))
    return render_template('index.html')

@app.route('/result/<filename>')
def result(filename):
    return render_template('result.html', filename=filename)

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join('output', filename)
    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)