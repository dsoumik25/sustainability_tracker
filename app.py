
from flask import Flask, render_template, request, send_file
import matplotlib.pyplot as plt
import csv
import uuid
import os
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)

# Environmental impact values
water_footprint_per_liter = 0.002  # kg CO₂e
fuel_emissions_per_km = 0.15       # kg CO₂e
electricity_footprint_per_kwh = 0.5  # kg CO₂e
plastic_footprint_per_kg = 2.5     # kg CO₂e
global_avg_footprint = 6600        # kg CO₂e per year

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form['name']
    daily_water_usage = float(request.form['water'])
    car_km = float(request.form['car'])
    bike_km = float(request.form['bike'])
    public_km = float(request.form['public'])
    electricity = float(request.form['electricity'])
    plastic = float(request.form['plastic'])

    total_footprint = (
        daily_water_usage * water_footprint_per_liter * 365 +
        (car_km * fuel_emissions_per_km +
         public_km * fuel_emissions_per_km * 0.5 +
         bike_km * fuel_emissions_per_km * 0.1) * 365 +
        electricity * electricity_footprint_per_kwh * 12 +
        plastic * plastic_footprint_per_kg * 52
    )

    with open('footprint_history.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([name, total_footprint, daily_water_usage,
                         car_km, public_km, bike_km, electricity, plastic])

    chart_id = str(uuid.uuid4())
    chart_filename = f'{chart_id}.png'
    chart_path = f'static/{chart_filename}'

    plt.figure()
    plt.bar(["Your Footprint", "Global Avg"],
            [total_footprint, global_avg_footprint],
            color=["#00e676", "#9e9e9e"])
    plt.ylabel("kg CO₂e / year")
    plt.title("Environmental Footprint Comparison")
    plt.tight_layout()
    plt.savefig(chart_path)
    plt.close()

    tips = []
    if daily_water_usage > 150:
        tips.append(f"Reduce water use by 20% to save {daily_water_usage * 0.2 * 365:.0f} liters/year.")
    if car_km > 10:
        tips.append("Use public transport or bike more often to cut emissions.")
    if electricity > 300:
        tips.append("Switch to energy-efficient appliances.")
    if plastic > 2:
        tips.append("Try reusable products to reduce plastic waste.")

    with open(f'static/{chart_id}_report.txt', 'w', encoding='utf-8') as report:
        report.write(f"Name: {name}\n")
        report.write(f"Annual Footprint: {total_footprint:.2f} kg CO₂e\n")
        for tip in tips:
            report.write(f"- {tip}\n")

    return render_template("results.html",
                           name=name,
                           footprint=total_footprint,
                           chart=chart_filename,
                           tips=tips,
                           chart_id=chart_id)

@app.route('/download/<chart_id>')
def download_pdf(chart_id):
    txt_path = f'static/{chart_id}_report.txt'
    img_path = f'static/{chart_id}.png'
    pdf_path = f'static/{chart_id}.pdf'

    c = canvas.Canvas(pdf_path, pagesize=letter)
    width, height = letter
    y = height - 50

    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                c.drawString(50, y, line.strip())
                y -= 20

    if os.path.exists(img_path):
        c.drawImage(img_path, 50, y - 280, width=500, height=250)

    c.save()
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
