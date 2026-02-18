#!/usr/bin/env python3
"""Static site generator for Airtable data."""

import os
import requests
import json
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

def format_number(value):
    return "{:,}".format(int(value))

def get_data():
    """
    Fetch data from Airtable API or return mock data if PAT is not available.
    
    Returns:
        list: List of records from Airtable or mock data for local testing.
    """
    airtable_pat = os.environ.get("AIRTABLE_PAT")
    BASE_ID = os.environ.get("AIRTABLE_BASE_ID")
    
    if not airtable_pat:
        print("⚠️  AIRTABLE_PAT not found in environment variables.")
        print("📝 Using mock data for local development...")
        
        # Mock data for local testing - Production KPI data
        return {
            "monthlyDataList": [],
            "totalProductionLoss": 0,
            "totalSoldComponents": 0,
            "totalDevelopmentLoss": 0,
            "totalDevelopmentGates": 0,
            "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }
    
    # Fetch real data from Airtable API
    print("🔑 Found AIRTABLE_PAT, fetching live data from Airtable...")
    
    url = f"https://api.airtable.com/v0/{BASE_ID}/Production"
    print(f"📡 Fetching data from Airtable API: {url}")
    headers = {
        "Authorization": f"Bearer {airtable_pat}",
        "Content-Type": "application/json"
    }
    def getEmptyDict(month):
        return {
            "month": month,
            "production_loss": 0,
            "sold_components": 0,
            "development_gates": 0,
            "development_loss": 0,
            "currentMonthProductionLoss": 0,
            "currentMonthSoldComponents": 0,
            "currentMonthDevelopmentLoss": 0,
            "currentMonthDevelopmentGates": 0,
            "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        }

    monthly_data = {}
    # Define month order for sorting
    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"
        ]
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        currentMonth = datetime.now().month
        print(f"Current month: {month_order[currentMonth-1]}")
        data = response.json()
        print(f"Successfully fetched {len(data.get('records', []))} records from Airtable.")
        # Get all the records and organize data by month
        
        for record in data.get("records", []):
            fields = record.get("fields", {})
            month = fields.get("Month", "Unknown")
            production_loss = fields.get("Production Loss", 0)
            sold_components = fields.get("Sold Components", 0)

            # Some fields may be None, so handle that
            try:
                production_loss = round(float(production_loss)) if production_loss is not None else 0
            except Exception:
                production_loss = 0
            try:
                sold_components = int(sold_components) if sold_components is not None else 0
            except Exception:
                sold_components = 0

            # Store data by month
            if month not in monthly_data:
                monthly_data[month] = getEmptyDict(month)
            
            monthly_data[month]["production_loss"] += production_loss
            monthly_data[month]["sold_components"] += sold_components
            
    else:
        print(f"Error fetching data: {response.status_code} - {response.text}")
    monthlyDataList = []

    urlDevelopment = f"https://api.airtable.com/v0/{BASE_ID}/Development"
    responseDevelopment = requests.get(urlDevelopment, headers=headers)
    if responseDevelopment.status_code == 200:
        dataDevelopment = responseDevelopment.json()
        print(f"Successfully fetched {len(dataDevelopment.get('records', []))} records from Airtable (Development).")
        
        for record in dataDevelopment.get("records", []):
            fields = record.get("fields", {})
            month = fields.get("Month", "Unknown")
            development_loss = fields.get("Development Loss", 0)
            development_gates = fields.get("Finished Development Gates", 0)

            # Some fields may be None, so handle that
            try:
                development_loss = round(float(development_loss)) if development_loss is not None else 0
            except Exception:
                development_loss = 0
            try:
                development_gates = int(development_gates) if development_gates is not None else 0
            except Exception:
                development_gates = 0
            # Store data by month
            if month not in monthly_data:
                monthly_data[month] = getEmptyDict(month)
            
            monthly_data[month]["development_loss"] += development_loss
            monthly_data[month]["development_gates"] += development_gates
    else:
        print(f"Error fetching data: {responseDevelopment.status_code} - {responseDevelopment.text}")

    total_production_loss = 0
    total_sold_components = 0
    total_development_loss = 0
    total_development_gates = 0
    currentMonth = month_order[datetime.now().month - 1]
    currentMonthProductionLoss = 0
    currentMonthSoldComponents = 0
    currentMonthDevelopmentLoss = 0
    currentMonthDevelopmentGates = 0
    for month in month_order:
        # Find all months in monthly_data_list that start with this month name (e.g., "January", "January 2026")
        matching_entries = [entry for key, entry in monthly_data.items() if entry["month"].startswith(month)]
        for entry in matching_entries:
            print(f"  {entry['month']}: Production Loss: {entry['production_loss']}, Sold Components: {entry['sold_components']}, Development Loss: {entry['development_loss']}, Development Gates: {entry['development_gates']}")
            if entry["month"].startswith(currentMonth):
                print(f"    -> Matches current month ({currentMonth}), adding to current month totals")
                currentMonthProductionLoss += entry["production_loss"]
                currentMonthSoldComponents += entry["sold_components"]
                currentMonthDevelopmentLoss += entry["development_loss"]
                currentMonthDevelopmentGates += entry["development_gates"]
            monthlyDataList.append(entry)
            total_production_loss += entry["production_loss"]
            total_sold_components += entry["sold_components"]
            total_development_loss += entry["development_loss"]
            total_development_gates += entry["development_gates"]

    print("\nSummary:")
    print(f"  Total Production Loss: {total_production_loss}")
    print(f"  Total Sold Components: {total_sold_components}")
    print(f"  Total Development Loss: {total_development_loss}")
    print(f"  Total Development Gates: {total_development_gates}")
    # print(monthlyDataList)
    finalData = {
        "monthlyDataList": monthlyDataList,
        "totalProductionLoss": total_production_loss,
        "totalSoldComponents": total_sold_components,
        "totalDevelopmentLoss": total_development_loss,
        "totalDevelopmentGates": total_development_gates,
        'currentMonthProductionLoss':currentMonthProductionLoss,
        'currentMonthSoldComponents': currentMonthSoldComponents,
        'currentMonthDevelopmentLoss': currentMonthDevelopmentLoss,
        'currentMonthDevelopmentGates': currentMonthDevelopmentGates,
        "lastUpdated": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    }
    print(f"Final data prepared for template rendering: {finalData}")
    return finalData


def build_site():
    """
    Build the static site by rendering the Jinja2 template with production KPI data.
    """
    print("🔨 Building static site...")
    
    # Get data from Airtable or mock data
    records = get_data()
        
    # Setup Jinja2 environment
    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(['html', 'xml'])
    )
    env.filters['format_number'] = format_number

    try:
        template = env.get_template("index.html")
        
        # Render the template with production KPI data
        output = template.render(
            monthlyDataList=records["monthlyDataList"],
            totalProductionLoss=records["totalProductionLoss"],
            totalSoldComponents=records["totalSoldComponents"],
            totalDevelopmentLoss=records["totalDevelopmentLoss"],
            totalDevelopmentGates=records["totalDevelopmentGates"],
            currentMonthProductionLoss=records["currentMonthProductionLoss"],
            currentMonthSoldComponents=records["currentMonthSoldComponents"],
            currentMonthDevelopmentLoss=records["currentMonthDevelopmentLoss"],
            currentMonthDevelopmentGates=records["currentMonthDevelopmentGates"],
            lastUpdated=records["lastUpdated"]
        )
        
        # Write to output file
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(output)
            
        print(f"✅ Static site built successfully!")
        print(f"📄 Generated index.html with {len(records['monthlyDataList'])} items")
        print(f"📊 Current Month Production Loss: {records['currentMonthProductionLoss']}, Sold Components: {records['currentMonthSoldComponents']}, Development Loss: {records['currentMonthDevelopmentLoss']}, Development Gates: {records['currentMonthDevelopmentGates']}")
        print(f"🕒 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"🔄 Cache-busting enabled - Page will force refresh on data changes")
        
    except Exception as e:
        print(f"❌ Error building site: {e}")
        raise

if __name__ == "__main__":
    print("🚀 Starting Airtable Static Site Generator...")
    print("=" * 50)
    
    build_site()
    
    print("=" * 50)
    print("🎉 Build process completed!")